"""50-seed local pole test at N=5, plus a control run at N=4."""
import json, multiprocessing as mp, time
import numpy as np
import kuhnNp as G, cfrNp as C, poletest as PT

ITERS, NSEED = 1500000, 50

def one(args):
    N, seed = args
    g = G.KuhnN(N)
    p = C.train(g, ITERS, seed=seed)
    e0 = float(g.exploitability(p).max())
    q = PT.snap(g, p)
    e1 = float(g.exploitability(q).max())
    off = [g.name(i) for i in PT.offpath(g, q)]
    recs = PT.pole_test(g, q)
    return dict(N=N, seed=seed, expl_raw=e0, expl_snapped=e1, offpath=off, recs=recs)

def main():
    jobs = [(5, s) for s in range(NSEED)] + [(4, s) for s in range(10)]
    t = time.time()
    with mp.Pool(max(1, mp.cpu_count() - 1)) as pool:
        res = pool.map(one, jobs)
    json.dump(res, open("poles_N5.json", "w"))
    print("%d runs in %.0fs\n" % (len(res), time.time() - t))
    for N in (4, 5):
        R = [r for r in res if r["N"] == N]
        print("=" * 74)
        print("N = %d   (%d seeds)" % (N, len(R)))
        print("=" * 74)
        ex = np.array([r["expl_raw"] for r in R])
        exs = np.array([r["expl_snapped"] for r in R])
        print("   exploitability raw     : median %.5f  max %.5f" % (np.median(ex), ex.max()))
        print("   after snapping to pures: median %.5f  max %.5f" % (np.median(exs), exs.max()))
        from collections import Counter
        cnt = Counter(tuple(sorted(r["offpath"])) for r in R)
        print("   off-path sets found:")
        for k, v in cnt.most_common():
            print("      %-40s %d/%d seeds" % (", ".join(k) if k else "NONE", v, len(R)))
        allrec = [x for r in R for x in r["recs"]]
        att = [x for x in allrec if x["attainable"]]
        pol = [x for x in allrec if x["pole"]]
        print("   (off-path x, deviation y) pairs where x moves the incentive: %d" % len(allrec))
        print("      of those, root attainable in [0,1]: %d" % len(att))
        print("      of those, a genuine POLE          : %d" % len(pol))
        if allrec:
            roots = np.array([x["root"] for x in allrec])
            print("      root distribution: min %.4f  median %.4f  max %.4f"
                  % (roots.min(), np.median(roots), roots.max()))
            d = np.minimum(np.abs(roots), np.abs(roots - 1))
            d[(roots >= 0) & (roots <= 1)] = 0.0
            j = int(np.argmin(np.where(d > 0, d, np.inf))) if (d > 0).any() else 0
            print("      closest miss: %s via %s, root %.4f (%.4f outside)"
                  % (allrec[j]["x"], allrec[j]["y"], allrec[j]["root"], d[j]))
        if pol:
            print("      POLES:")
            for x in pol[:10]:
                print("         x=%s y=%s A=P%d root=%.4f numer=%.6f"
                      % (x["x"], x["y"], x["A"] + 1, x["root"], x["numerator"]))

if __name__ == "__main__":
    main()
