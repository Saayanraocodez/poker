"""Multi-seed pole test across (n, N) to test the N = n+1 hypothesis."""
import json, multiprocessing as mp, time
import numpy as np
import kuhnGen as Q, cfrGen as CG, poletest as PT

CONFIGS = [(3, 4, 800000, 20), (3, 5, 800000, 20),
           (4, 5, 400000, 20), (4, 6, 400000, 20),
           (5, 6, 200000, 20), (5, 7, 200000, 8)]

def one(args):
    n, N, iters, seed = args
    g = Q.Kuhn(n, N)
    p = CG.train(g, iters, seed=seed)
    e0 = float(g.exploitability_bi(p).max())
    q = PT.snap(g, p)
    e1 = float(g.exploitability_bi(q).max())
    recs = PT.pole_test(g, q, max_off=60)
    a1 = [float(p[g.pidx(0, j, "")]) for j in g.cards]
    S, own = [], PT.owners(g)
    G = g.gradient(p)
    for y in range(g.nparam):
        A = own[y]
        d = G[y]
        if abs(d[A]) < 1e-9:
            continue
        S.append([d[k] / (-d[A]) for k in range(n) if k != A])
    S = np.array(S)
    rank = int(np.linalg.matrix_rank(S - S.mean(0), tol=1e-9)) if len(S) else 0
    return dict(n=n, N=N, seed=seed, expl=e0, expl_snap=e1, a1max=max(a1),
                noff=len(PT.offpath(g, q)), rank=rank,
                npairs=len(recs),
                natt=sum(r["attainable"] for r in recs),
                npole=sum(r["pole"] for r in recs),
                roots=[r["root"] for r in recs],
                u=g.utilities(p).tolist())

def main():
    jobs = [(n, N, it, s) for n, N, it, ns in CONFIGS for s in range(ns)]
    t = time.time()
    with mp.Pool(max(1, mp.cpu_count() - 1)) as pool:
        res = pool.map(one, jobs)
    json.dump(res, open("sweep_Nn.json", "w"))
    print("%d runs in %.0fs\n" % (len(res), time.time() - t))
    print("   n  N  N=n+1 seeds  expl(med)  P1 max open  off-path  rank  pairs  attain  POLES  seeds w/pole")
    for n, N, it, ns in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        if not R:
            continue
        med = np.median([r["expl"] for r in R])
        a1 = np.median([r["a1max"] for r in R])
        off = np.median([r["noff"] for r in R])
        rk = sorted({r["rank"] for r in R})
        pr = sum(r["npairs"] for r in R)
        at = sum(r["natt"] for r in R)
        po = sum(r["npole"] for r in R)
        sw = sum(1 for r in R if r["npole"] > 0)
        print("   %d  %d  %-5s %-5d  %-9.5f  %-11.3f  %-8.0f  %-5s %-6d %-7d %-6d %d/%d"
              % (n, N, "YES" if N == n + 1 else "no", len(R), med, a1, off,
                 ",".join(map(str, rk)), pr, at, po, sw, len(R)))
    print("\n   (rank should equal n-2:  n=3 -> 1,  n=4 -> 2,  n=5 -> 3)")
    print("\n   root distributions (only configs with pairs):")
    for n, N, it, ns in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        rt = np.array([x for r in R for x in r["roots"]])
        if rt.size == 0:
            continue
        inside = ((rt >= 0) & (rt <= 1)).mean()
        print("      n=%d N=%d: %4d roots | min %8.3f  median %7.3f  max %8.3f | %.0f%% inside [0,1]"
              % (n, N, rt.size, rt.min(), np.median(rt), rt.max(), 100 * inside))
    print("\n   seat utilities (mean over seeds):")
    for n, N, it, ns in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        if not R:
            continue
        U = np.array([r["u"] for r in R]).mean(0)
        print("      n=%d N=%d: %s" % (n, N, "  ".join("P%d %+.5f" % (k + 1, v)
                                                       for k, v in enumerate(U))))

if __name__ == "__main__":
    main()
