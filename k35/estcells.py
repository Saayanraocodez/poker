"""Knuth tree-size estimate for the (3,5) cells the sweep cannot finish.

`runcells.py` caps each cell at 15 minutes; the cells where P1 bets only with
the best card, and the ones where P1 bluffs card 1, time out.  This says how
big those enumerations actually are, by Knuth's unbiased estimator on the same
label DFS the enumeration walks (treesize6.propagate, nash mode, bet-first
order): follow a random root-to-leaf path, multiplying by the number of live
children at each node.  The 4-card game is the control: under this propagation (nash mode, bet-first
order) its silent branch has 668 support leaves, and the estimator returns
1.85e3 +/- 1.0e3 on 400 walks -- the right order, with the wide interval that
3 % nonzero paths implies.

usage:  KUHN_CARDS=5 KUHN_MODE=nash KUHN_ORDER=bet python estcells.py <walks> <workers> [cell ...]
"""
import numpy as np, sys, time, os
import treesize6 as T6, kuhn3p as K

I = K.NAME_IDX
U, MIX, DC = 9, 2, 3
NP = 12 * K.NCARDS


def walk(a):
    spec, seed = a
    rng = np.random.default_rng(seed)
    lab = np.full(NP, U, np.int8)
    for part in spec.split(","):
        n, v = part.split(":")
        lab[I[n]] = {"0": 0, "1": 1, "MIX": MIX}[v]
    LO = np.where(lab == 1, 1.0, 0.0); HI = np.where(lab == 0, 0.0, 1.0)
    L, A, B, al = T6.propagate(lab[None], LO[None], HI[None], T6.WEAK)
    if not al[0]: return 0.0, 0.0
    lab, LO, HI = L[0], A[0], B[0]
    w = 1.0; nodes = 1.0        # Knuth: the running product also estimates the
    while True:                 # NODE count when summed along the path
        u = [x for x in T6.ORDER if lab[x] == U]
        if not u: return w, nodes
        v = u[0]
        kids = []
        for l in (0, 1, MIX):
            l2 = lab.copy(); a2 = LO.copy(); b2 = HI.copy(); l2[v] = l
            if l == 0: b2[v] = 0.0
            elif l == 1: a2[v] = 1.0
            kids.append((l2, a2, b2))
        L2, A2, B2, al2 = T6.propagate(np.array([k[0] for k in kids]), np.array([k[1] for k in kids]),
                                       np.array([k[2] for k in kids]), T6.WEAK)
        idx = np.flatnonzero(al2)
        if idx.size == 0: return 0.0, nodes
        w *= idx.size; nodes += w
        k = idx[rng.integers(idx.size)]
        lab, LO, HI = L2[k], A2[k], B2[k]


if __name__ == "__main__":
    nwalk = int(sys.argv[1]); nw = int(sys.argv[2])
    cells = sys.argv[3:]
    if not cells:
        cells = [l.split()[0] for l in open("cells_summary_%d.txt" % K.NCARDS) if "TIMEOUT" in l][:6]
    print("%d cards, mode %s, %d walks each" % (K.NCARDS, "seq" if T6.WEAK else "nash", nwalk), flush=True)
    from multiprocessing import Pool
    with Pool(nw) as pool:
        for spec in cells:
            t0 = time.time()
            R = pool.map(walk, [(spec, s) for s in range(nwalk)])
            W = np.array([r[0] for r in R]); N = np.array([r[1] for r in R])
            m = W.mean(); se = W.std(ddof=1) / np.sqrt(len(W)); nz = (W > 0).mean()
            print("%-46s leaves ~ %.3e +/- %.1e   NODES ~ %.3e +/- %.1e   nonzero %.1f%%   %.0fs"
                  % (spec, m, se, N.mean(), N.std(ddof=1) / np.sqrt(len(N)), 100 * nz, time.time() - t0), flush=True)
