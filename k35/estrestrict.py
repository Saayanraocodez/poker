"""Knuth tree-size estimate for the RESTRICTED game G_c of (3,5)-Kuhn (P1's openings frozen at 0 with
NO condition on them) -- with and without the deterrence CUT.

Why.  A P1-silent profile is a Nash equilibrium iff (a) it is an equilibrium of G_c and (b) some
responses to a bet deter every opening: Ebet(j; y) <= V_j for j = 1..5, where V_j is P1's value of
checking with card j.  `deter35.py` proves exactly that every deterrable V satisfies
    3 V_2 + 8 V_5 >= 16.
So "no P1-silent equilibrium" follows from: every equilibrium of G_c has 3 V_2 + 8 V_5 < 16.  That
search has 40 live coordinates instead of 55 (the 15 responses to a bet are unreached -> DC), and a
node dies as soon as the box's upper bound on 3 V_2 + 8 V_5 is below 16.

Float estimate only (no verdicts from here): treesize6.propagate in nash mode with ivl.bounds
patched so the frozen openings carry no condition, then the cut on the box (per-deal interval
bound of P1's root value -- each coordinate occurs once per deal, so that bound is exact per deal).
usage (k35/):  KUHN_CARDS=5 KUHN_MODE=nash KUHN_ORDER=bet python estrestrict.py <walks> <workers> [cut|nocut]"""
import numpy as np, sys, time, os
import ivl, tree as T, kuhn3p as K, treesize6 as T6

U, MIX, DC = 9, 2, 3
NP = K.NPARAM
OPEN = [K.pidx(0, j, 1) for j in K.CARDS]
_orig = ivl.bounds


def _restricted_bounds(LO, HI):
    r = list(_orig(LO, HI))
    for k in (0, 1, 3, 4):              # DLO, DHI, DMIN, DMAX of the frozen openings: no condition
        r[k] = np.array(r[k], copy=True); r[k][:, OPEN] = 0.0
    return tuple(r)


ivl.bounds = _restricted_bounds
INT = [int(p) for p in T.INTERNAL][::-1]
P1C = np.array([c[0] for c in T.DEALS])
# KUHN_CUT=v25 (default): 3 V_2 + 8 V_5 >= 16 ;  v5: 8 V_5 >= 19 (V_1 = -1 used) -- both from deter35.py
CUT = os.environ.get("KUHN_CUT", "v25")
W = np.zeros(T.ND)
if CUT == "v25": W[P1C == 2] = 3.0; W[P1C == 5] = 8.0; THR = 16.0
else: W[P1C == 5] = 8.0; THR = 19.0
NJ = (P1C == 2).sum()                   # deals per P1 card (12)


def cut_ub(LO, HI):
    """(B,) upper bound on 3 V_2 + 8 V_5 over each box, V_j = mean over the deals with P1 card j"""
    B = LO.shape[0]
    Vhi = {p: np.broadcast_to(T.PAYT[:, p, 0], (B, T.ND)) for p in T.LEAFPOS}
    Vlo = dict(Vhi)
    for p in INT:
        c = T.COORD[:, p]; xl = LO[:, c]; xh = HI[:, c]
        a_l, a_h = Vlo[T.AGGC[p]], Vhi[T.AGGC[p]]; p_l, p_h = Vlo[T.PASC[p]], Vhi[T.PASC[p]]
        dl = a_l - p_l; dh = a_h - p_h
        Vlo[p] = np.minimum(p_l + xl * dl, p_l + xh * dl)
        Vhi[p] = np.maximum(p_h + xl * dh, p_h + xh * dh)
    return (Vhi[0] * W).sum(axis=1) / NJ


G5 = [K.pidx(1, k, 1) for k in range(1, 5)] + [K.pidx(2, l, 1) for l in range(1, 5)] +      [K.pidx(2, l, 2) for l in range(1, 5)] + [K.pidx(1, k, 4) for k in range(1, 5)]
if os.environ.get("KUHN_ORDER2", "") == "g5first":
    T6.ORDER = G5 + [i for i in T6.ORDER if i not in G5]
OFFP = set([K.pidx(1, c, 2) for c in K.CARDS] + [K.pidx(2, c, s) for c in K.CARDS for s in (3, 4)])
CUTDEP = sorted(set(int(T.COORD[d, p]) for d in range(T.ND) if W[d] > 0 for p in T.INTERNAL) - set(OPEN) - OFFP)


def cut_contract(LO, HI, rounds=4):
    """chord contractor for the cut UB(3 V_2 + 8 V_5) >= 16 on ONE box (1-D arrays): the per-deal
    upper bound of P1's root value is convex in a pinned coordinate t (a max of non-negative
    combinations of the children's bounds, affine at the pinned node), so where the chord through
    the two pins is < 16 the cut fails.  -> LO, HI, alive"""
    LO = LO.copy(); HI = HI.copy()
    for _ in range(rounds):
        cols = [v for v in CUTDEP if HI[v] > LO[v]]
        if not cols: break
        PL = np.repeat(LO[None], 2 * len(cols), 0); PH = np.repeat(HI[None], 2 * len(cols), 0)
        for n, v in enumerate(cols):
            PL[2 * n, v] = PH[2 * n, v] = LO[v]; PL[2 * n + 1, v] = PH[2 * n + 1, v] = HI[v]
        ub = cut_ub(PL, PH) - THR
        ch = False
        for n, v in enumerate(cols):
            u0, u1 = ub[2 * n], ub[2 * n + 1]
            if u0 < -1e-9 and u1 < -1e-9: return LO, HI, False
            w = HI[v] - LO[v]
            if u0 < -1e-9 <= u1:
                t = -u0 / (u1 - u0); nl = LO[v] + w * t
                if nl > LO[v] + 1e-12: LO[v] = nl; ch = True
            elif u1 < -1e-9 <= u0:
                t = u0 / (u0 - u1); nh = LO[v] + w * t
                if nh < HI[v] - 1e-12: HI[v] = nh; ch = True
        if not ch: break
    return LO, HI, True


def with_cut(L, A, B, al, contract):
    """apply the cut (kill, and optionally the contractor + re-propagation) to a batch of children"""
    al = al & (cut_ub(A, B) >= THR - 1e-9)
    if not contract: return L, A, B, al
    L = L.copy(); A = A.copy(); B = B.copy()
    for i in np.flatnonzero(al):
        lab, lo, hi = L[i], A[i], B[i]
        for _ in range(4):
            lo2, hi2, ok = cut_contract(lo, hi)
            if not ok: al[i] = False; break
            if np.array_equal(lo2, lo) and np.array_equal(hi2, hi): break
            l3, a3, b3, ok3 = T6.propagate(lab[None], lo2[None], hi2[None], T6.WEAK)
            if not ok3[0]: al[i] = False; break
            lab, lo, hi = l3[0], a3[0], b3[0]
        L[i], A[i], B[i] = lab, lo, hi
    return L, A, B, al


def walk(a):
    seed, cut = a
    rng = np.random.default_rng(seed)
    lab, LO, HI = T6.root_of("silent")
    L, A, B, al = T6.propagate(lab[None], LO[None], HI[None], T6.WEAK)
    if not al[0]: return 0.0, 1.0, 0
    lab, LO, HI = L[0], A[0], B[0]
    w = 1.0; nodes = 1.0; depth = 0
    while True:
        u = [x for x in T6.ORDER if lab[x] == U]
        if not u: return w, nodes, depth
        v = u[0]
        kids = T6.expand(lab, LO, HI, v)
        if not kids: return 0.0, nodes, depth
        L2, A2, B2, al2 = T6.propagate(np.array([k[0] for k in kids]), np.array([k[1] for k in kids]),
                                       np.array([k[2] for k in kids]), T6.WEAK)
        if cut: L2, A2, B2, al2 = with_cut(L2, A2, B2, al2, cut == "cutc")
        idx = np.flatnonzero(al2)
        if idx.size == 0: return 0.0, nodes, depth
        w *= idx.size; nodes += w; depth += 1
        k = idx[rng.integers(idx.size)]
        lab, LO, HI = L2[k], A2[k], B2[k]


if __name__ == "__main__":
    nwalk = int(sys.argv[1]); nw = int(sys.argv[2]); mode = sys.argv[3] if len(sys.argv) > 3 else "cut"
    cut = mode if mode in ("cut", "cutc") else False
    lab, LO, HI = T6.root_of("silent")
    L, A, B, al = T6.propagate(lab[None], LO[None], HI[None], T6.WEAK)
    print("root: alive %s, U %d, DC %d, cut %s UB at root %.4f (needs >= %s); order %s" % (
        al[0], (L[0] == U).sum(), (L[0] == DC).sum(), CUT, cut_ub(A, B)[0], THR,
        os.environ.get("KUHN_ORDER2", "bet")), flush=True)
    from multiprocessing import Pool
    t0 = time.time()
    with Pool(nw) as pool:
        R = pool.map(walk, [(s, cut) for s in range(nwalk)])
    Wt = np.array([r[0] for r in R]); N = np.array([r[1] for r in R]); D = np.array([r[2] for r in R])
    print("G_c %s: leaves ~ %.3e +/- %.1e   NODES ~ %.3e +/- %.1e   nonzero %.1f%%   depth mean %.1f max %d   %.0fs" % (
        mode, Wt.mean(), Wt.std(ddof=1) / np.sqrt(len(Wt)), N.mean(),
        N.std(ddof=1) / np.sqrt(len(N)), 100 * (Wt > 0).mean(), D.mean(), D.max(), time.time() - t0), flush=True)
