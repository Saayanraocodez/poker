"""(k35 port: the coordinate count is NP = 12 * KUHN_CARDS.)
EXACT label-aware propagation for the option-2 prover (enumc7): bnb6.propagate + treesize6.propagate
in rational arithmetic, one box at a time.  No float anywhere.

A box is two lists of NP Fractions (lo, hi).  Every rule is a necessary condition for a Nash
equilibrium in the box whose support labels are the node's (so no equilibrium is ever discarded):
  * interval enclosure of du_i (x24) over the box: the tree recursion with exact interval arithmetic;
  * box semantics: lo_i > 0 (or label MIX) => du_i >= 0;  hi_i < 1 (or MIX) => du_i <= 0;
  * strong rules: du_i > 0 on the whole box => x_i = 1;  du_i < 0 => x_i = 0;
  * weak rules ONLY at information sets the labels prove reached (a path of MIX / matching pure
    labels): the per-node value difference > 0 at all 6 nodes => x_i = 1 (< 0 => 0) -- at a reached
    set this is the best-response condition, sound for every Nash equilibrium;
  * chord contractor: with x_v pinned to t, the upper bound U_i(t) of du_i is convex in t (each
    coordinate occurs at most once on a root-to-leaf path of a deal, so the recursion composes affine
    maps, maxima, subtractions of a concave lower bound, and non-negative reach factors applied by a
    convex increasing map); where the chord through (0, U_i(0)), (1, U_i(1)) is < 0, du_i >= 0 is
    impossible.  Symmetrically for the concave lower bound and du_i <= 0.  New endpoints are rounded
    OUTWARD to the grid 2^-GRID (a weaker bound; keeps the rationals small);
  * after propagation: lo_i >= 1 => label 1, hi_i <= 0 => label 0 (box-implied), and a coordinate
    whose reach upper bound is 0 at all 6 nodes is marked DC (Lemma 2); a MIX coordinate whose box
    collapsed to 0 or 1 is a contradiction (MIX means interior).
The independent checker (xcheck.py) re-implements all of this separately and must agree exactly."""
from fractions import Fraction as F
import tree as T, kuhn3p as _K
NP = _K.NPARAM                     # 12 * cards (NP for 4 cards, 60 for 5)

U, MIX, DC = 9, 2, 3
GRID = 60
ZERO, ONE = F(0), F(1)
ND, NPOS = T.ND, T.NPOS
INT = [int(p) for p in T.INTERNAL]
LEAF = [int(p) for p in T.LEAFPOS]
AGGC = [int(x) for x in T.AGGC]; PASC = [int(x) for x in T.PASC]
COORD = [[int(T.COORD[d, p]) for p in range(NPOS)] for d in range(ND)]
PAY = [[[int(T.PAYT[d, p, k]) for k in range(3)] for p in range(NPOS)] for d in range(ND)]
OWNER = {int(p): T.OWNER[int(p)][0] for p in INT}
NODES = [[] for _ in range(NP)]
for _d in range(ND):
    for _p in INT: NODES[COORD[_d][_p]].append((_d, _p))
_PAR = {}
for _p in INT: _PAR[AGGC[_p]] = (_p, True); _PAR[PASC[_p]] = (_p, False)


def _deps():
    """DEP[v] = the conditions i (i != v) whose du_i depends on x_v: v on the path to one of i's
    nodes, or in the subtree below it, in the same deal"""
    below = {}
    def sub(p):
        if p not in below:
            below[p] = ({p} | sub(AGGC[p]) | sub(PASC[p])) if p in INT else set()
        return below[p]
    dep = [set() for _ in range(NP)]
    for d in range(ND):
        for p in INT:
            i = COORD[d][p]; q = p
            while q in _PAR:
                q = _PAR[q][0]; dep[COORD[d][q]].add(i)
            for r in sub(p):
                if r != p: dep[COORD[d][r]].add(i)
    for v in range(NP): dep[v].discard(v)
    return [sorted(s) for s in dep]
DEP = _deps()
# the edges on the way to each node: (coordinate, aggressive?) -- for "certainly reached"
PATHS = []
for _d in range(ND):
    for _p in INT:
        e = []; q = _p
        while q in _PAR:
            r, agg = _PAR[q]; e.append((COORD[_d][r], agg)); q = r
        PATHS.append((COORD[_d][_p], e))


def bounds(lo, hi):
    """exact interval bounds over the box -> DLO, DHI (24 * du_i), RH (reach UB summed), DMIN, DMAX"""
    Vlo = {}; Vhi = {}
    for d in range(ND):
        for p in LEAF: Vlo[d, p] = Vhi[d, p] = PAY[d][p]
        for p in reversed(INT):
            c = COORD[d][p]; xl, xh = lo[c], hi[c]
            al, ah = Vlo[d, AGGC[p]], Vhi[d, AGGC[p]]; pl, ph = Vlo[d, PASC[p]], Vhi[d, PASC[p]]
            vl = []; vh = []
            for k in range(3):
                dl = al[k] - pl[k]; dh = ah[k] - ph[k]
                vl.append(min(pl[k] + xl * dl, pl[k] + xh * dl)); vh.append(max(ph[k] + xl * dh, ph[k] + xh * dh))
            Vlo[d, p] = vl; Vhi[d, p] = vh
    Rlo = {}; Rhi = {}
    for d in range(ND):
        Rlo[d, 0] = Rhi[d, 0] = ONE
        for p in INT:
            c = COORD[d][p]; xl, xh = lo[c], hi[c]
            Rlo[d, AGGC[p]] = Rlo[d, p] * xl; Rhi[d, AGGC[p]] = Rhi[d, p] * xh
            Rlo[d, PASC[p]] = Rlo[d, p] * (1 - xh); Rhi[d, PASC[p]] = Rhi[d, p] * (1 - xl)
    DLO = [ZERO] * NP; DHI = [ZERO] * NP; RH = [ZERO] * NP; DMIN = [None] * NP; DMAX = [None] * NP
    for i in range(NP):
        for d, p in NODES[i]:
            o = OWNER[p]
            Dl = Vlo[d, AGGC[p]][o] - Vhi[d, PASC[p]][o]; Dh = Vhi[d, AGGC[p]][o] - Vlo[d, PASC[p]][o]
            rl, rh = Rlo[d, p], Rhi[d, p]
            DLO[i] += rl * Dl if Dl >= 0 else rh * Dl
            DHI[i] += rh * Dh if Dh >= 0 else rl * Dh
            RH[i] += rh
            DMIN[i] = Dl if DMIN[i] is None else min(DMIN[i], Dl)
            DMAX[i] = Dh if DMAX[i] is None else max(DMAX[i], Dh)
    return DLO, DHI, RH, DMIN, DMAX


def _down(q): return F((q.numerator << GRID) // q.denominator, 1 << GRID)
def _up(q): return F(-((-q.numerator << GRID) // q.denominator), 1 << GRID)


def certain_reach(lab):
    out = [False] * NP
    for i, edges in PATHS:
        if not out[i] and all(lab[c] == MIX or lab[c] == (1 if agg else 0) for c, agg in edges): out[i] = True
    return out


def _fs(q):
    return str(q.numerator) if q.denominator == 1 else "%d/%d" % (q.numerator, q.denominator)


def propagate_box(lo, hi, hg, hl, wk, rounds=8, steps=None):
    """exact bnb6.propagate for one box -> (lo, hi, alive, number of bounds() calls).
    steps: a list that receives the CERTIFICATE -- every step that changed the box or closed it,
    each verifiable on its own from the box current at that step (see xcheck.py):
      ["F", [[i, 1|0], ...]]               forces from one bounds() of the current box
      ["C", v, [[side, i, value], ...]]    chord narrowings of x_v from the two pins of v
      ["K", reason, ...]                   the contradiction that closes the box"""
    rec = steps is not None
    lo = list(lo); hi = list(hi); calls = 0
    for _ in range(rounds):
        DLO, DHI, RH, DMIN, DMAX = bounds(lo, hi); calls += 1
        ng = [lo[i] > 0 or hg[i] for i in range(NP)]; nl = [hi[i] < 1 or hl[i] for i in range(NP)]
        for i in range(NP):
            if ng[i] and DHI[i] < 0:
                if rec: steps.append(["K", "ge", i])
                return lo, hi, False, calls
            if nl[i] and DLO[i] > 0:
                if rec: steps.append(["K", "le", i])
                return lo, hi, False, calls
        f1 = [DLO[i] > 0 or (wk[i] and DMIN[i] > 0) for i in range(NP)]
        f0 = [DHI[i] < 0 or (wk[i] and DMAX[i] < 0) for i in range(NP)]
        for i in range(NP):
            if f1[i] and hi[i] < 1:
                if rec: steps.append(["K", "f1", i])
                return lo, hi, False, calls
            if f0[i] and lo[i] > 0:
                if rec: steps.append(["K", "f0", i])
                return lo, hi, False, calls
        nlo = [ONE if f1[i] else lo[i] for i in range(NP)]; nhi = [ZERO if f0[i] else hi[i] for i in range(NP)]
        if rec:
            fs = [[i, 1] for i in range(NP) if nlo[i] != lo[i]] + [[i, 0] for i in range(NP) if nhi[i] != hi[i]]
            if fs: steps.append(["F", fs])
        changed = nlo != lo or nhi != hi
        lo, hi = nlo, nhi
        ng = [lo[i] > 0 or hg[i] for i in range(NP)]; nl = [hi[i] < 1 or hl[i] for i in range(NP)]
        act = [(ng[i] and DLO[i] < 0) or (nl[i] and DHI[i] > 0) for i in range(NP)]
        cols = [v for v in range(NP) if hi[v] > lo[v] and any(act[i] for i in DEP[v])]
        for v in cols:
            pins = []
            for val in (lo[v], hi[v]):
                L = list(lo); H = list(hi); L[v] = H[v] = val
                r = bounds(L, H); calls += 1; pins.append((r[0], r[1]))
            (l0, u0), (l1, u1) = pins
            tlo, thi = ZERO, ONE; ilo = ihi = None
            for i in DEP[v]:
                if ng[i]:
                    if u0[i] < 0 and u1[i] < 0:
                        if rec: steps.append(["K", "cge", v, i])
                        return lo, hi, False, calls
                    if u0[i] < 0 <= u1[i]:
                        t = -u0[i] / (u1[i] - u0[i])
                        if t > tlo: tlo, ilo = t, i
                    if u1[i] < 0 <= u0[i]:
                        t = u0[i] / (u0[i] - u1[i])
                        if t < thi: thi, ihi = t, i
                if nl[i]:
                    if l0[i] > 0 and l1[i] > 0:
                        if rec: steps.append(["K", "cle", v, i])
                        return lo, hi, False, calls
                    if l0[i] > 0 >= l1[i]:
                        t = l0[i] / (l0[i] - l1[i])
                        if t > tlo: tlo, ilo = t, i
                    if l1[i] > 0 >= l0[i]:
                        t = -l0[i] / (l1[i] - l0[i])
                        if t < thi: thi, ihi = t, i
            if tlo > thi:
                if rec: steps.append(["K", "cx", v, ilo, ihi])
                return lo, hi, False, calls
            w = hi[v] - lo[v]
            nl_ = max(_down(lo[v] + w * tlo), lo[v]); nh_ = min(_up(lo[v] + w * thi), hi[v])
            if nl_ > lo[v] or nh_ < hi[v]:
                if rec:
                    ch = []
                    if nl_ > lo[v]: ch.append(["lo", ilo, _fs(nl_)])
                    if nh_ < hi[v]: ch.append(["hi", ihi, _fs(nh_)])
                    steps.append(["C", v, ch])
                lo[v], hi[v] = nl_, nh_; changed = True
        if not changed: break
    return lo, hi, True, calls


def propagate(lab, lo, hi, weak=False, steps=None):
    """label-aware exact propagation (treesize6.propagate semantics, nash mode by default)
    -> (labels, lo, hi, alive).  weak=True would apply the weak rules everywhere (seq mode).
    steps: receives the certificate (propagate_box's steps, plus ["K", "mix", i])."""
    mix = [lab[i] == MIX for i in range(NP)]
    wk = [True] * NP if weak else certain_reach(lab)
    lo, hi, al, _ = propagate_box(lo, hi, mix, mix, wk, steps=steps)
    lab = list(lab)
    if not al: return lab, lo, hi, False
    for i in range(NP):
        if lab[i] == MIX and (lo[i] >= 1 or hi[i] <= 0):
            if steps is not None: steps.append(["K", "mix", i])
            return lab, lo, hi, False
    RH = bounds(lo, hi)[2]
    for i in range(NP):
        if lab[i] == U:
            if lo[i] >= 1: lab[i] = 1
            elif hi[i] <= 0: lab[i] = 0
            elif RH[i] <= 0: lab[i] = DC
    return lab, lo, hi, True


def spec_state(spec):
    """the root's labels and box straight from the branch spec (before propagation)"""
    import kuhn3p as K
    I = K.NAME_IDX
    lab = [U] * NP; lo = [ZERO] * NP; hi = [ONE] * NP
    for part in spec.split(","):
        c, l = part.split(":"); i = I[c]
        if l == "0": lab[i] = 0; hi[i] = ZERO
        elif l == "1": lab[i] = 1; lo[i] = ONE
        elif l == "MIX": lab[i] = MIX
        else: raise ValueError(spec)
    return lab, lo, hi


def root_state(spec, steps=None):
    """the root of a branch: labels from the spec, then propagated"""
    lab, lo, hi = spec_state(spec)
    return propagate(lab, lo, hi, steps=steps)


def child(lab, lo, hi, v, l, steps=None):
    """child of a node at coordinate v with label l -> (labels, lo, hi, alive, reason).
    steps: receives the child's certificate (["X"] alone for a label the parent's box excludes)."""
    if (l == 0 and lo[v] > 0) or (l == 1 and hi[v] < 1) or (l == MIX and not (hi[v] > 0 and lo[v] < 1)):
        if steps is not None: steps.append(["X"])
        return None, None, None, False, "excluded"
    lab2 = list(lab); lab2[v] = l; lo2 = list(lo); hi2 = list(hi)
    if l == 0: hi2[v] = ZERO
    elif l == 1: lo2[v] = ONE
    lab2, lo2, hi2, al = propagate(lab2, lo2, hi2, steps=steps)
    return lab2, lo2, hi2, al, None if al else "propagation"
