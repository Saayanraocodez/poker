"""Knuth tree-size estimate of the SUPPORT enumeration with bnb6's propagation.

`treesize.py` measured the P1-betting branches at 10^9 - 10^10 support patterns
with `bnb.propagate` (weak rules, no contraction), with 100 % of sampled paths
surviving -- the bound never fired.  This repeats the measurement with the
label DFS driven by bnb6.propagate in sequential mode (weak rules + the chord
contractor), where a MIX label imposes du = 0 through hyp_ge/hyp_le and the
contractor narrows every box, including boxes of still-unassigned coordinates
(which then lose label options: LO > 0 rules out label 0, HI < 1 rules out 1).

CONTROLS
  * the P1-silent branch: the old enumeration has 3,045,358 leaves; the new
    tree can only be SMALLER (its pruning is a superset), so the estimate must
    come out <= ~3.0e6 -- and every certified-equilibrium pattern of
    surv_pat_samp.npy must survive the new propagation with its labels fixed.
  * nonzero-path fraction and quantiles are printed as before.

usage:  python treesize6.py <walks> <workers> [spec ...]
"""
import numpy as np, sys, time, os, bnb6, ivl, kuhn3p as K
from multiprocessing import Pool

# KUHN_MODE=seq (default): bnb6's weak rules on -- sound for every equilibrium that
# is sequentially rational at every information set (sequential / perfect / proper).
# KUHN_MODE=nash: strong rules only -- sound for every Nash equilibrium.  Read by
# enum6 / prove6pat too, and inherited by their worker processes.
WEAK = os.environ.get("KUHN_MODE", "seq") != "nash"

I = K.NAME_IDX
U, MIX, DC = 9, 2, 3
ORDER = [I[n] for n in ("c11", "c21", "c31", "c41", "b11", "b21", "b31", "b41",
                        "a22", "a32", "a33", "a34", "a23",
                        "b22", "b23", "b32", "b33", "b34",
                        "c22", "c23", "c32", "c33", "c34",
                        "a12", "a13", "a14", "a24", "b12", "b13", "b14", "b24",
                        "c12", "c13", "c14", "c24", "a42", "a43", "a44",
                        "b42", "b43", "b44", "c42", "c43", "c44",
                        "a11", "a21", "a31", "a41")]
# KUHN_ORDER=bet: assign the responses to P1's BET first (P2's b_k2, P3's
# c_k3 / c_k4), then the check-subtree.  In a betting branch the exact test's
# strongest constraints are P1's bet incentives, which involve exactly those
# coordinates; with the default order they are the last to be assigned and the
# test stays weak for most of the tree (2026-09-19).
if os.environ.get("KUHN_ORDER", "") == "bet":
    _bet = [I[n] for n in ("b12", "b22", "b32", "b42", "c13", "c23", "c33", "c43", "c14", "c24", "c34", "c44")]
    ORDER = _bet + [i for i in ORDER if i not in _bet]
LABV = {"0": 0, "1": 1, "MIX": MIX}


# root-to-node paths: for each (deal, internal position) the coordinates on the
# way down and whether the edge taken is the aggressive one (factor x) or the
# passive one (factor 1 - x)
def _paths():
    import tree as T
    par = {}
    for pos in T.INTERNAL:
        par[T.AGGC[pos]] = (pos, True); par[T.PASC[pos]] = (pos, False)
    out = []
    for d in range(T.ND):
        for pos in T.INTERNAL:
            edges = []; p = pos
            while p in par:
                q, agg = par[p]; edges.append((T.COORD[d, q], agg)); p = q
            out.append((T.COORD[d, pos], edges))
    return out
PATHS = _paths()


def certain_reach(lab):
    """(B, N) mask: information set of coordinate i is reached with POSITIVE
    probability at every point of the label cell -- some node's path uses only
    aggressive edges labelled 1 / MIX and passive edges labelled 0 / MIX."""
    B = lab.shape[0]
    cert = np.zeros((B, 48), bool)
    for i, edges in PATHS:
        ok = np.ones(B, bool)
        for c, agg in edges:
            ok &= (lab[:, c] == MIX) | (lab[:, c] == (1 if agg else 0))
        cert[:, i] |= ok
    return cert


def propagate(lab, LO, HI, weak=True, contract=True):
    """label-aware propagation: returns lab, LO, HI, alive.
    weak=False (nash mode) still applies the dominance rules at information
    sets the labels prove reached: that is sound for every Nash equilibrium.
    contract=False skips bnb6's chord contractor (~100 ivl calls): used by the
    layered enumeration, where the exact test does the pruning."""
    mix = lab == MIX
    wk = weak if weak else certain_reach(lab)
    LO, HI, al, DLO, DHI, SL, SK = bnb6.propagate(LO, HI, weak=wk, hyp_ge=mix, hyp_le=mix, contract=contract)
    lab = lab.copy()
    # labels implied by the boxes
    lab[(lab == U) & (LO >= 1.0)] = 1
    lab[(lab == U) & (HI <= 0.0)] = 0
    # a MIX coordinate whose box collapsed is contradictory (interior means open)
    al &= ~((lab == MIX) & ((LO >= 1.0) | (HI <= 0.0))).any(axis=1)
    RH = ivl.bounds(LO, HI)[2]
    lab[(lab == U) & (RH <= 0.0)] = DC
    return lab, LO, HI, al


def root_of(spec):
    lab = np.full(48, U); LO = np.zeros(48); HI = np.ones(48)
    if spec == "all":
        pass
    elif spec == "silent":
        for n in ("a11", "a21", "a31", "a41"):
            lab[I[n]] = 0; HI[I[n]] = 0.0
    else:
        for part in spec.split(","):
            c, l = part.split(":")
            if l in LABV:
                lab[I[c]] = LABV[l]
                if l == "0": HI[I[c]] = 0.0
                if l == "1": LO[I[c]] = 1.0
            else:                              # numeric lower bound, e.g. a11:0.2
                LO[I[c]] = float(l)
    return lab, LO, HI


def expand(lab, LO, HI, v):
    """children of one state at coordinate v: label 0 / 1 / MIX where consistent."""
    kids = []
    if LO[v] <= 0.0:
        l, a, b = lab.copy(), LO.copy(), HI.copy(); l[v] = 0; b[v] = 0.0; kids.append((l, a, b))
    if HI[v] >= 1.0:
        l, a, b = lab.copy(), LO.copy(), HI.copy(); l[v] = 1; a[v] = 1.0; kids.append((l, a, b))
    if HI[v] > 0.0 and LO[v] < 1.0:          # box meets the open interval (0,1)
        l, a, b = lab.copy(), LO.copy(), HI.copy(); l[v] = MIX; kids.append((l, a, b))
    return kids


def walk(a):
    spec, seed, weak = a
    rng = np.random.default_rng(seed)
    lab, LO, HI = root_of(spec)
    lab, LO, HI, al = propagate(lab[None], LO[None], HI[None], weak)
    if not al[0]: return 0.0
    lab, LO, HI = lab[0], LO[0], HI[0]
    w = 1.0
    while True:
        u = [x for x in ORDER if lab[x] == U]
        if not u: return w
        v = u[0]
        kids = expand(lab, LO, HI, v)
        if not kids: return 0.0
        L = np.array([k[0] for k in kids]); A = np.array([k[1] for k in kids]); B = np.array([k[2] for k in kids])
        L, A, B, al = propagate(L, A, B, weak)
        idx = np.flatnonzero(al)
        if idx.size == 0: return 0.0
        w *= idx.size
        k = idx[rng.integers(idx.size)]
        lab, LO, HI = L[k], A[k], B[k]


if __name__ == "__main__":
    nwalk = int(sys.argv[1]); nw = int(sys.argv[2])
    specs = sys.argv[3:] or ["silent", "a11:MIX"]
    weak = WEAK
    print("mode %s" % ("seq (weak rules)" if weak else "nash (strong rules only)"), flush=True)
    # control: certified-equilibrium patterns survive with their labels fixed
    P = np.load("surv_pat_samp.npy")[:64].astype(np.int8)
    lab = P.copy(); LO = np.where(lab == 1, 1.0, 0.0); HI = np.where(lab == 0, 0.0, 1.0)
    lab2, LO2, HI2, al = propagate(lab, LO, HI, weak)
    print("control: %d of %d certified-equilibrium patterns survive label propagation  %s"
          % (al.sum(), len(P), "OK" if al.all() else "*** FAIL"), flush=True)
    with Pool(nw) as pool:
        for spec in specs:
            t0 = time.time()
            W = np.array(pool.map(walk, [(spec, s, weak) for s in range(nwalk)]))
            m = W.mean(); se = W.std(ddof=1) / np.sqrt(len(W))
            nz = (W > 0).mean()
            q = np.percentile(W[W > 0], [50, 90, 99]) if (W > 0).any() else [0, 0, 0]
            print("%-14s leaves ~ %.3e  +/- %.1e (se)   nonzero paths %.1f%%   median %.2e  p90 %.2e  p99 %.2e   %.0fs"
                  % (spec, m, se, 100 * nz, q[0], q[1], q[2], time.time() - t0), flush=True)
