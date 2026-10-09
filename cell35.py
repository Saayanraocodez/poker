"""(3, 5): is there a Nash equilibrium in a given P1-opening cell?  (float exploration, decides nothing)
silent35.py generalised: P1's openings for the cards in KUHN_FIX are held at 0 (restricted MCCFR, a fixed
information set is played at its fixed probability and gets no regret), Newton + support repair on the
restricted interior support, then the FULL-game exploitability, which shows P1's gain from opening a fixed
card.  A seed with full-game exploitability ~1e-16 is a candidate equilibrium IN the cell (to be certified
exactly, e.g. by k35/cert35gen.py); a positive gain only for the fixed cards means the cell's restricted
equilibrium is not a full one.
usage:  KUHN_FIX=3,4 python cell35.py <iters> <first seed> <last seed+1> <workers>"""
import os, sys, json, time
import numpy as np
import multiprocessing as mp
import kuhnGen as Q, certify as C, poletest as PT
import silent35 as S35

G = Q.Kuhn(3, 5)
FIXCARDS = [int(c) for c in os.environ.get("KUHN_FIX", "3,4").split(",")]
S35.FIXED.clear()
S35.FIXED.update({G.pidx(0, j, ""): 0.0 for j in FIXCARDS})
FIXED = S35.FIXED


def train(a):
    return S35.train(a)


if __name__ == "__main__":
    iters, s0, s1, nw = (int(x) for x in sys.argv[1:5])
    tag = "cell35_fix%s_%d_s%d_%d" % ("".join(map(str, FIXCARDS)), iters, s0, s1)
    t = time.time()
    with mp.Pool(min(nw, s1 - s0)) as pool:
        P = [np.array(x) for x in pool.map(train, [(iters, s) for s in range(s0, s1)])]
    json.dump([x.tolist() for x in P], open(tag + ".json", "w"))
    print("restricted MCCFR (P1 never opens %s): seeds %d..%d x %d iters in %.0fs" % (FIXCARDS, s0, s1 - 1, iters, time.time() - t), flush=True)
    res = []
    for n, p in enumerate(P):
        s = s0 + n
        e0 = G.exploitability_bi(p)
        off, p0s, p1s, inter = C.classify(G, [p])
        inter = [i for i in inter if i not in FIXED]
        q = PT.snap(G, p)
        for i, v in FIXED.items(): q[i] = v
        r, Sup, e, rep = C.certify(G, q, inter)
        for i, v in FIXED.items(): r[i] = v
        ex = G.exploitability_bi(r)
        opn = [round(float(r[G.pidx(0, j, "")]), 4) for j in G.cards]
        print("seed %2d: MCCFR full expl %s | polished: full expl %s |S| %d  P1 opens %s" % (
            s, np.round(e0, 4).tolist(), ["%.1e" % x for x in ex], len(Sup), opn), flush=True)
        res.append({"seed": s, "expl": [float(x) for x in ex], "interior": Sup, "profile": r.tolist(), "p1": opn})
    json.dump(res, open(tag + "_polished.json", "w"))
    full = [x for x in res if max(abs(v) for v in x["expl"]) < 1e-12]
    print("%d of %d seeds give a FULL-game equilibrium in the cell (float)" % (len(full), len(res)), flush=True)
