"""
Port exact certification to (4,5), then answer B on CERTIFIED equilibria.

At (3,4) the ambiguous set was small enough for exhaustive 2^k enumeration.
At (4,5) it will not be, so hypotheses are visited in order of HAMMING DISTANCE
from the CFR reading: the true support is expected to be a few flips away, and
certified supports were ~1% of the space at (3,4), so a distance-ordered walk
finds them long before the space is exhausted.
"""
import itertools, json, os, time
import multiprocessing as mp
import numpy as np
import kuhnGen as Q, cfrGen as CG, certify as C, poletest as PT, properness as PR

N_ITER, NSEED, BUDGET = 4000000, 4, 6000


def _train(a):
    it, s = a
    return CG.train(Q.Kuhn(4, 5), it, seed=s).tolist()


def distance_ordered(k, budget):
    """Masks over k bits, all-ones first, then by Hamming distance from it."""
    seen = 0
    for d in range(k + 1):
        for flip in itertools.combinations(range(k), d):
            m = [1] * k
            for i in flip:
                m[i] = 0
            yield tuple(m)
            seen += 1
            if seen >= budget:
                return


def main():
    g = Q.Kuhn(4, 5)
    cache = "cfr45_%d.json" % N_ITER
    if os.path.exists(cache):
        P = [np.array(x) for x in json.load(open(cache))]
        print("(loaded cached CFR)")
    else:
        t = time.time()
        with mp.Pool(NSEED) as pool:
            P = [np.array(x) for x in pool.map(_train, [(N_ITER, s) for s in range(NSEED)])]
        json.dump([x.tolist() for x in P], open(cache, "w"))
        print("CFR: %d seeds x %d iters in %.0fs" % (NSEED, N_ITER, time.time() - t))
    V = np.array(P)
    expl = [float(np.abs(g.exploitability_bi(q)).max()) for q in P]
    print("   exploitability per seed: %s" % np.round(expl, 5))

    cand = [i for i in range(g.nparam)
            if not (V[:, i].max() < 5e-3 or V[:, i].min() > 1 - 5e-3)]
    print("   %d ambiguous coordinates -> 2^%d = %d hypotheses; visiting %d "
          "nearest the CFR reading" % (len(cand), len(cand), 2 ** len(cand), BUDGET))

    p0 = np.array(P[int(np.argmin(expl))])
    for i in range(g.nparam):
        if i not in cand:
            p0[i] = 1.0 if p0[i] > 0.5 else 0.0

    t = time.time()
    found = []
    for m, mask in enumerate(distance_ordered(len(cand), BUDGET)):
        q = p0.copy()
        S = []
        for c, bit in zip(cand, mask):
            if bit:
                S.append(c)
            else:
                q[c] = 1.0 if p0[c] > 0.5 else 0.0
        r, h = C.newton(g, q, S, iters=25)
        e = float(np.abs(g.exploitability_bi(r)).max())
        if e < 1e-12:
            found.append(dict(expl=e, interior=S, profile=r.copy(),
                              dist=len(cand) - sum(mask)))
        if (m + 1) % 250 == 0:
            print("      %d/%d, %d certified, %.0fs" % (m + 1, BUDGET, len(found), time.time() - t))
            if len(found) >= 12:
                break
    print("\n   CERTIFIED: %d exact equilibria at (4,5)" % len(found))
    if not found:
        print("   none found within the budget")
        return
    json.dump([{"expl": f["expl"], "interior": f["interior"], "dist": f["dist"],
                "profile": f["profile"].tolist()} for f in found],
              open("certified_45.json", "w"))
    print("   best exploitability %.2e | Hamming distance from CFR reading: %s"
          % (min(f["expl"] for f in found), sorted({f["dist"] for f in found})))

    print("\n   B ANSWERED ON CERTIFIED EQUILIBRIA:")
    print("   #   expl        off  slack  inert  pinned  d_free  d_cond  verdict")
    for i, f in enumerate(found[:12]):
        a = PR.analyse(g, f["profile"])
        print("   %-3d %.2e   %-4d %-6d %-6d %-7d %-7d %-7d %s"
              % (i, f["expl"], a["off"], a["slack"], a["inert"], a["pinned"],
                 a["d_free"], a["d_cond"], a["verdict"]))


if __name__ == "__main__":
    main()
