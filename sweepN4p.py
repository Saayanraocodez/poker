"""Multi-seed pole test for the 4-PLAYER game, plus incidence rank."""
import json, multiprocessing as mp, time
import numpy as np
import kuhnGen as Q, cfrGen as CG, poletest as PT

ITERS, NSEED = 400000, 24

def one(seed):
    g = Q.Kuhn(4, 5)
    p = CG.train(g, ITERS, seed=seed)
    e0 = float(g.exploitability(p).max())
    q = PT.snap(g, p)
    e1 = float(g.exploitability(q).max())
    recs = PT.pole_test(g, q)
    per = g.nparam // 4
    S = []
    for y in range(g.nparam):
        A = y // per
        d = g.dcoord(p, y)
        if abs(d[A]) < 1e-6:
            continue
        S.append([d[k] / (-d[A]) for k in range(4) if k != A])
    S = np.array(S)
    rank = int(np.linalg.matrix_rank(S - S.mean(0), tol=1e-8)) if len(S) else 0
    return dict(seed=seed, expl_raw=e0, expl_snap=e1, rank=rank, ncostly=len(S),
                noff=len(PT.offpath(g, q)), recs=recs,
                u=g.utilities(p).tolist())

def main():
    t = time.time()
    with mp.Pool(max(1, mp.cpu_count() - 1)) as pool:
        res = pool.map(one, range(NSEED))
    json.dump(res, open("poles_n4.json", "w"))
    ex = np.array([r["expl_raw"] for r in res])
    print("n = 4, N = 5   %d seeds x %d iters   %.0fs" % (NSEED, ITERS, time.time() - t))
    print("   exploitability: median %.5f  max %.5f" % (np.median(ex), ex.max()))
    U = np.array([r["u"] for r in res])
    print("   utilities by seat (mean +- sd):")
    for k in range(4):
        print("      P%d  %+.5f +- %.5f" % (k + 1, U[:, k].mean(), U[:, k].std()))
    rk = [r["rank"] for r in res]
    print("   affine rank of the incidence-share set: %s  (n-2 = 2)"
          % dict((v, rk.count(v)) for v in sorted(set(rk))))
    print("   off-path sets per seed: median %d" % int(np.median([r["noff"] for r in res])))
    allr = [x for r in res for x in r["recs"]]
    att = [x for x in allr if x["attainable"]]
    pol = [x for x in allr if x["pole"]]
    print("   (off-path x, deviation y) pairs that move an incentive: %d" % len(allr))
    print("      attainable root in [0,1]: %d" % len(att))
    print("      genuine POLES           : %d" % len(pol))
    withp = sum(1 for r in res if any(x["pole"] for x in r["recs"]))
    print("      seeds with at least one pole: %d/%d" % (withp, NSEED))
    if pol:
        rt = np.array([x["root"] for x in pol])
        nm = np.array([x["numerator"] for x in pol])
        print("      pole roots: min %.4f median %.4f max %.4f" % (rt.min(), np.median(rt), rt.max()))
        print("      numerators: min %.6f median %.6f" % (nm.min(), np.median(nm)))
        from collections import Counter
        c = Counter((x["x"], x["y"]) for x in pol)
        print("      most common (x, y) pole pairs:")
        for (a, b), v in c.most_common(6):
            print("         x=%-14s y=%-14s %d seeds" % (a, b, v))

if __name__ == "__main__":
    main()
