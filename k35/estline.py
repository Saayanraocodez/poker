"""Knuth size of the two LINE trees of the restricted game G_c (see estrestrict.py).

After P1's check, P2 either bets (the KB line: P3 calls or folds, then P1) or checks (the KK line: P3
bets or checks; after a bet P1, then P2, call or fold).  The lines share no information set; they are
joined only by P2's choice b_k1 (and the payoff comparison behind it).  The joint label DFS walks the
PRODUCT of the two lines' support trees; a decomposed search would walk P2's bets, then each line
separately, and only then pair the surviving partial patterns.  This estimates the two partial trees:
labels on P2's bets b?1 first, then on one line's coordinates; a walk stops when that line is fully
labelled (the other line's coordinates stay unlabelled, boxes [0,1]).  Float, estimate only.
usage (k35/):  KUHN_CARDS=5 KUHN_MODE=nash KUHN_ORDER=bet python estline.py <walks> <workers> KB|KK"""
import numpy as np, sys, time, os
import estrestrict as ER          # patches ivl.bounds: frozen openings carry no condition
import kuhn3p as K, treesize6 as T6

U = ER.U
B1 = [K.pidx(1, k, 1) for k in K.CARDS]
LINE = {"KB": [K.pidx(2, l, 2) for l in K.CARDS] + [K.pidx(0, j, 3) for j in K.CARDS] + [K.pidx(0, j, 4) for j in K.CARDS],
        "KK": [K.pidx(2, l, 1) for l in K.CARDS] + [K.pidx(0, j, 2) for j in K.CARDS] +
              [K.pidx(1, k, 3) for k in K.CARDS] + [K.pidx(1, k, 4) for k in K.CARDS]}


def walk(a):
    seed, line = a
    order = B1 + LINE[line]
    rng = np.random.default_rng(seed)
    lab, LO, HI = T6.root_of("silent")
    L, A, B, al = T6.propagate(lab[None], LO[None], HI[None], T6.WEAK)
    lab, LO, HI = L[0], A[0], B[0]
    w = 1.0; nodes = 1.0
    while True:
        u = [x for x in order if lab[x] == U]
        if not u: return w, nodes
        kids = T6.expand(lab, LO, HI, u[0])
        if not kids: return 0.0, nodes
        L2, A2, B2, al2 = T6.propagate(np.array([k[0] for k in kids]), np.array([k[1] for k in kids]),
                                       np.array([k[2] for k in kids]), T6.WEAK)
        idx = np.flatnonzero(al2)
        if idx.size == 0: return 0.0, nodes
        w *= idx.size; nodes += w
        k = idx[rng.integers(idx.size)]
        lab, LO, HI = L2[k], A2[k], B2[k]


if __name__ == "__main__":
    nwalk = int(sys.argv[1]); nw = int(sys.argv[2]); line = sys.argv[3]
    from multiprocessing import Pool
    t0 = time.time()
    with Pool(nw) as pool:
        R = pool.map(walk, [(s, line) for s in range(nwalk)])
    W = np.array([r[0] for r in R]); N = np.array([r[1] for r in R])
    print("%s line (after b?1): partial leaves ~ %.3e +/- %.1e   NODES ~ %.3e +/- %.1e   nonzero %.1f%%   %.0fs" % (
        line, W.mean(), W.std(ddof=1) / np.sqrt(len(W)), N.mean(), N.std(ddof=1) / np.sqrt(len(N)),
        100 * (W > 0).mean(), time.time() - t0), flush=True)
