"""NASH-SOUND interval branch-and-bound over the FULL cube [0,1]^48, with
contractors and a dependency-directed split.

Why a sixth version.  `bnb5` is sound only modulo leaf-distribution equivalence:
its two "weak" rules move a coordinate whose information set may be unreachable
to its dominant pure value.  That preserves the leaf distribution but NOT the
Nash property -- `offpath.py` exhibits an exact equilibrium with b12 = 9/100
(P2 calls P1's bet with the worst card, off path) that stops being an
equilibrium when b12 is moved to its dominant value 0.  So every result built on
`bnb5`/`bnb2` propagation, and every result on the Table-2 slice, is a result
about equilibria in undominated strategies, not about all Nash equilibria.

`bnb6` keeps exactly bnb5's box semantics,

    LO_i > 0  =>  du_i >= 0        HI_i < 1  =>  du_i <= 0

drops the weak rules, never substitutes Table 2 (Table 2 falls out of
propagation wherever the information set is provably reached), and adds two
things bnb5 does not have:

  CHORD CONTRACTOR.  For an active condition i and a coordinate v it depends
  on, pin x_v = lo_v + w_v t and let U_i(t) be ivl's upper bound on du_i over
  the rest of the box.  U_i is CONVEX in t: through the tree it is built from
  maxima of functions affine in t, products with non-negative reach bounds,
  and sums (control 1 below checks it numerically).  So if U_i(0) < 0 <= U_i(1)
  the chord from (0,U_i(0)) to (1,U_i(1)) lies above U_i, and du_i >= 0 is
  infeasible for every t below the chord's zero  t_c = -U(0)/(U(1)-U(0)).
  Symmetrically L_i(t) is concave and narrows boxes for du_i <= 0.  Two pinned
  ivl calls per coordinate give the contractor for EVERY condition at once.

  SLOPE-DIRECTED SPLIT.  bnb5 splits the widest coordinate, which on the
  betting branches spends the depth budget on coordinates irrelevant to the
  conditions that are close to firing.  Here: take the active condition with
  the least slack (its bound is closest to the wrong side of zero) and split
  the coordinate along which its pinned bound moves the most -- the slopes are
  a by-product of the contractor.

Both are pure necessary-condition reasoning: no equilibrium is ever discarded.
Soundness controls live in control6.py and must pass before any verdict from
this file is quoted.

ROUNDING (2026-09-20).  ivl now rounds every operation outward (nextafter),
so DLO / DHI / DMIN / DMAX and the pinned bounds are true bounds, and the
chord crossing below is computed in the safe direction too.  The tolerance
TOL = 1e-11 in every rule is therefore pure slack, no longer the thing that
absorbs rounding: a box killed by `DHI < -tol` has du_i < 0 at every point.
"""
import numpy as np, ivl
import tree as T

TOL = 1e-11
import kuhn3p as _K
N = _K.NPARAM

# dependency graph from the tree: du_i involves every coordinate on the path to
# i's node and every coordinate in the subtree below it, over the 6 deals.
def _deps():
    par = {}
    for pos in T.INTERNAL:
        par[T.AGGC[pos]] = pos; par[T.PASC[pos]] = pos
    below = {}
    def sub(pos):
        if pos in below: return below[pos]
        s = set()
        if pos in T.INTERNAL:
            s.add(pos); s |= sub(T.AGGC[pos]); s |= sub(T.PASC[pos])
        below[pos] = s
        return s
    D = [set() for _ in range(N)]
    for d in range(T.ND):
        for pos in T.INTERNAL:
            i = T.COORD[d, pos]
            p = pos
            while p in par:
                p = par[p]; D[i].add(T.COORD[d, p])
            for q in sub(pos):
                if q != pos: D[i].add(T.COORD[d, q])
    return [np.array(sorted(s), dtype=np.int64) for s in D]

DEPS = _deps()
DEPM = np.zeros((N, N), bool)          # DEPM[i, v] : du_i depends on x_v
for i, d in enumerate(DEPS): DEPM[i, d] = True
np.fill_diagonal(DEPM, False)          # du_i never depends on x_i itself


def _pinned(LO, HI, v, val):
    L = LO.copy(); H = HI.copy(); L[:, v] = val; H[:, v] = val
    r = ivl.bounds(L, H)
    return r[0], r[1]


def propagate(LO, HI, tol=TOL, rounds=8, contract=True, hyp_ge=None, hyp_le=None, weak=False):
    """-> LO, HI, alive, DLO, DHI, SLOPE, SLACK
    SLOPE[b, i, v] : |U_i(1)-U_i(0)| or |L_i(1)-L_i(0)| of the pinned bound that
                     matters for condition i (0 where not computed);
    SLACK[b, i]    : how far condition i's bound is on the wrong side of 0
                     (0 = decided / satisfied on the whole box)."""
    B = LO.shape[0]
    LO = LO.copy(); HI = HI.copy()
    alive = np.ones(B, bool)
    HG = None if hyp_ge is None else np.broadcast_to(np.asarray(hyp_ge, bool), (B, N))
    HL = None if hyp_le is None else np.broadcast_to(np.asarray(hyp_le, bool), (B, N))
    SLOPE = np.zeros((B, N, N)); SLACK = np.zeros((B, N))
    DLO = DHI = None
    for r in range(rounds):
        DLO, DHI, RH, DMIN, DMAX = ivl.bounds(LO, HI)
        need_ge = LO > 0.0; need_le = HI < 1.0
        if HG is not None: need_ge = need_ge | HG
        if HL is not None: need_le = need_le | HL
        dead = (need_ge & (DHI < -tol)) | (need_le & (DLO > tol))
        alive &= ~dead.any(axis=1)
        f1 = DLO > tol; f0 = DHI < -tol                     # strong rules: sound for every Nash equilibrium
        if weak is not False and weak is not None:
            # bnb5's weak rules: aggressive strictly better at EVERY node of the
            # information set for every profile in the box (or strictly worse).
            # That is one-shot sequential rationality, so these are sound for
            # SEQUENTIAL equilibria (hence perfect / proper), NOT for all Nash --
            # unless restricted (weak = a (B, N) mask) to information sets that
            # are CERTAINLY reached, where the same rule is the plain
            # best-response condition and sound for every Nash equilibrium.
            # treesize6.propagate builds that mask from the labels: a MIX label
            # is strictly interior, so a path of MIX / matching pure labels has
            # positive reach even though its interval lower bound is 0.
            W = np.ones_like(f1) if weak is True else np.broadcast_to(np.asarray(weak, bool), f1.shape)
            f1 = f1 | (W & (DMIN > tol)); f0 = f0 | (W & (DMAX < -tol))
        alive &= ~((f1 & (HI < 1.0)) | (f0 & (LO > 0.0))).any(axis=1)
        nLO = np.where(f1, 1.0, LO); nHI = np.where(f0, 0.0, HI)
        changed = not (np.array_equal(nLO, LO) and np.array_equal(nHI, HI))
        LO, HI = nLO, nHI
        if not alive.any():
            break
        need_ge = LO > 0.0; need_le = HI < 1.0
        if HG is not None: need_ge = need_ge | HG
        if HL is not None: need_le = need_le | HL
        s_ge = np.where(need_ge, np.maximum(0.0, -DLO), 0.0)
        s_le = np.where(need_le, np.maximum(0.0, DHI), 0.0)
        SLACK = np.maximum(s_ge, s_le)
        if not contract:
            if not changed: break
            continue
        # which coordinates are worth pinning: positive width, and in the
        # dependency set of some condition that is active with positive slack
        actm = (SLACK > 0.0) & alive[:, None]                # (B, N) conditions
        want = ((actm.astype(np.int64) @ DEPM.astype(np.int64)) > 0) & (HI - LO > 0.0)   # (B, N) coords
        cols = np.flatnonzero(want.any(axis=0))
        SLOPE[:] = 0.0
        if len(cols) == 0:
            if not changed: break
            continue
        # ONE ivl call for every (box, coordinate, end) pinned variant: ivl's
        # per-call overhead (~0.4 ms) otherwise dominates on the small batches a
        # thin search tree produces.
        rows = []; pv = []; pe = []
        for v in cols:
            idx = np.flatnonzero(want[:, v])
            rows.append(idx); pv.append(np.full(len(idx), v)); pe.append(np.zeros(len(idx), int))
            rows.append(idx); pv.append(np.full(len(idx), v)); pe.append(np.ones(len(idx), int))
        rows = np.concatenate(rows); pv = np.concatenate(pv); pe = np.concatenate(pe)
        PL = LO[rows].copy(); PH = HI[rows].copy()
        val = np.where(pe == 0, LO[rows, pv], HI[rows, pv])
        PL[np.arange(len(rows)), pv] = val; PH[np.arange(len(rows)), pv] = val
        pl, ph = ivl.bounds(PL, PH)[:2]
        half = len(rows) // 2
        # order: for each v: [idx at end 0], [idx at end 1]
        off = 0
        for v in cols:
            idx = np.flatnonzero(want[:, v]); n_ = len(idx)
            l0, u0 = pl[off:off+n_], ph[off:off+n_]; l1, u1 = pl[off+n_:off+2*n_], ph[off+n_:off+2*n_]
            off += 2 * n_
            cond = DEPM[:, v]
            ge = need_ge[idx][:, cond]; le = need_le[idx][:, cond]
            sl = np.where(ge, np.abs(u1 - u0)[:, cond], 0.0)
            sl = np.maximum(sl, np.where(le, np.abs(l1 - l0)[:, cond], 0.0))
            SLOPE[np.ix_(idx, np.flatnonzero(cond), [v])] = sl[:, :, None]
            # The excluded range is where the computed CHORD is below -tol (resp.
            # above +tol) in VALUE space, then a further tol in t.  A margin in t
            # alone is not a value margin when the chord is nearly flat (slope
            # s: a value error e becomes e/s in t), and ivl's rounding error is
            # ~1e-13 in value.  With the value margin, an excluded t has true
            # chord < -tol + 3e < 0, so du_i >= 0 is impossible there (2026-09-16).
            # DIRECTED ROUNDING (2026-09-20): u0, u1, l0, l1 are now true
            # bounds (ivl), so the chord (1-t) u0 + t u1 >= max du_i at t by
            # convexity, exactly.  The crossing t_c is computed rounded in the
            # safe direction (tlo below the crossing: numerator down, denominator
            # up, quotient down; thi above it), so an excluded t has true chord
            # < -tol with no rounding assumption; the extra tol in t is kept.
            tlo = np.zeros(n_); thi = np.ones(n_)
            for i in np.flatnonzero(cond):
                g = need_ge[idx, i]
                a = g & (u0[:, i] < -tol) & (u1[:, i] >= -tol)
                if a.any():
                    tlo[a] = np.maximum(tlo[a], ivl.sub_dn(ivl.div_dn(ivl.sub_dn(-u0[a, i], tol), ivl.sub_up(u1[a, i], u0[a, i])), tol))
                a = g & (u1[:, i] < -tol) & (u0[:, i] >= -tol)
                if a.any():
                    thi[a] = np.minimum(thi[a], ivl.add_up(ivl.div_up(ivl.add_up(u0[a, i], tol), ivl.sub_dn(u0[a, i], u1[a, i])), tol))
                l = need_le[idx, i]
                a = l & (l0[:, i] > tol) & (l1[:, i] <= tol)
                if a.any():
                    tlo[a] = np.maximum(tlo[a], ivl.sub_dn(ivl.div_dn(ivl.sub_dn(l0[a, i], tol), ivl.sub_up(l0[a, i], l1[a, i])), tol))
                a = l & (l1[:, i] > tol) & (l0[:, i] <= tol)
                if a.any():
                    thi[a] = np.minimum(thi[a], ivl.add_up(ivl.div_up(ivl.sub_up(tol, l0[a, i]), ivl.sub_dn(l1[a, i], l0[a, i])), tol))
            tlo = np.clip(tlo, 0.0, 1.0); thi = np.clip(thi, 0.0, 1.0)
            lo_ = LO[idx, v]; hi_ = HI[idx, v]
            # the kept range [lo + w tlo, lo + w thi], rounded outward
            nlo = ivl.add_dn(lo_, ivl.mul_dn(ivl.sub_dn(hi_, lo_), tlo)); nhi = ivl.add_up(lo_, ivl.mul_up(ivl.sub_up(hi_, lo_), thi))
            emp = tlo > thi + tol
            alive[idx[emp]] = False
            upd = (nlo > lo_ + tol) | (nhi < HI[idx, v] - tol)
            if upd.any():
                LO[idx[upd], v] = np.maximum(LO[idx[upd], v], nlo[upd])
                HI[idx[upd], v] = np.minimum(HI[idx[upd], v], nhi[upd])
                if ((nlo[upd] - lo_[upd]) > 1e-4).any() or ((HI[idx[upd], v] - nhi[upd]) < -1e-4).any() or True:
                    changed = True
        if not changed or not alive.any():
            break
    if DLO is None:
        DLO, DHI = ivl.bounds(LO, HI)[:2]
    return LO, HI, alive, DLO, DHI, SLOPE, SLACK


def choose_split(LO, HI, SLOPE, SLACK, rule="slope"):
    """index of the coordinate to split, per box.
    rule 'slope': maximise SLOPE[i,v] / SLACK[i] over active conditions i --
    the (condition, coordinate) pair a halving is most likely to decide.
    Falls back to the widest coordinate when no slope information exists."""
    W = HI - LO
    j = W.argmax(axis=1)
    if rule == "width":
        return j
    act = SLACK > 0.0                                      # (B, N)
    score = SLOPE / np.where(act, SLACK, np.inf)[:, :, None]   # (B, N, N)
    score = score.max(axis=1) * (W > TOL)                  # (B, N) over coordinates
    has = score.max(axis=1) > 0.0
    j[has] = score[has].argmax(axis=1)
    return j


def search(LO0, HI0, maxnodes=2_000_000, cap=256, rule="slope", hyp_ge=None, hyp_le=None,
           log=None, rounds=6, contract=True, wtol=1e-9, weak=False):
    """DFS.  returns (verdict, nodes, witness_or_leftover)
       verdict True  : box proven empty
               False : a box of width < wtol survived every rule (a candidate point)
               None  : node cap hit; leftover = list of (LO, HI) stacks not yet processed"""
    stack = [(np.atleast_2d(LO0).astype(float), np.atleast_2d(HI0).astype(float))]
    nodes = 0
    while stack:
        # batched DFS: merge stack entries until the batch holds ~cap boxes, so
        # that the ~100 ivl calls of a contracting propagate are amortised
        LO, HI = stack.pop()
        while stack and LO.shape[0] < cap:
            L2, H2 = stack.pop()
            LO = np.concatenate([LO, L2]); HI = np.concatenate([HI, H2])
        if LO.shape[0] > 2 * cap:
            stack.append((LO[2 * cap:], HI[2 * cap:])); LO, HI = LO[:2 * cap], HI[:2 * cap]
        nodes += LO.shape[0]
        LO, HI, al, DLO, DHI, SLOPE, SLACK = propagate(LO, HI, rounds=rounds, contract=contract,
                                                        hyp_ge=hyp_ge, hyp_le=hyp_le, weak=weak)
        LO, HI, SLOPE, SLACK = LO[al], HI[al], SLOPE[al], SLACK[al]
        if LO.shape[0] == 0:
            continue
        W = HI - LO
        fin = W.max(axis=1) < wtol
        if fin.any():
            k = int(np.flatnonzero(fin)[0])
            return False, nodes, (LO[k], HI[k])
        if maxnodes and nodes > maxnodes:
            stack.append((LO, HI))
            return None, nodes, stack
        j = choose_split(LO, HI, SLOPE, SLACK, rule)
        for jj in np.unique(j):
            m = j == jj
            b_, c_ = LO[m], HI[m]
            for s in range(0, b_.shape[0], cap):
                bl, ch = b_[s:s+cap], c_[s:s+cap]
                mid = 0.5 * (bl[:, jj] + ch[:, jj])
                Bl = np.repeat(bl, 2, axis=0); Ch = np.repeat(ch, 2, axis=0)
                Ch[0::2, jj] = mid; Bl[1::2, jj] = mid
                stack.append((Bl, Ch))
        if log and nodes // log != (nodes - LO.shape[0]) // log:
            print("   nodes %d  stack %d" % (nodes, sum(s[0].shape[0] for s in stack)), flush=True)
    return True, nodes, None
