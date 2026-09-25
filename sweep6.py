"""Fourth value of n: (6,7) vs (6,8)."""
import json, multiprocessing as mp, time
import numpy as np
import kuhnGen as Q, cfrGen as CG, poletest as PT

CONFIGS = [(6, 8, 250000, 6)]   # the missing N>n+1 control at n=6
MAXOFF = 25

def one(args):
    n, N, iters, seed = args
    g = Q.Kuhn(n, N)
    p = CG.train(g, iters, seed=seed)
    e = float(g.exploitability_bi(p).max())
    q = PT.snap(g, p)
    off = PT.offpath(g, q)
    recs = PT.pole_test(g, q, max_off=MAXOFF, sub_seed=seed)
    own = PT.owners(g); G = g.gradient(p); S = []
    for y in range(g.nparam):
        A = own[y]; d = G[y]
        if abs(d[A]) < 1e-9: continue
        S.append([d[k] / (-d[A]) for k in range(n) if k != A])
    S = np.array(S)
    rank = int(np.linalg.matrix_rank(S - S.mean(0), tol=1e-9)) if len(S) else 0
    return dict(n=n, N=N, seed=seed, expl=e,
                maxopen=max(float(p[g.pidx(0, j, "")]) for j in g.cards),
                top=float(p[g.pidx(0, N, "")]),
                noff=len(off), sampled=min(len(off), MAXOFF), rank=rank,
                npairs=len(recs), natt=sum(r["attainable"] for r in recs),
                npole=sum(r["pole"] for r in recs),
                roots=[r["root"] for r in recs], u=g.utilities(p).tolist())

def main():
    jobs = [(n, N, it, s) for n, N, it, ns in CONFIGS for s in range(ns)]
    t = time.time()
    with mp.Pool(3) as pool:            # (6,8) peaks ~2.2GB per worker
        res = pool.map(one, jobs)
    json.dump(res, open("sweep6.json", "w"))
    print("%d runs in %.0fs   (pole test on a random %d-subset of off-path sets)\n"
          % (len(res), time.time() - t, MAXOFF))
    print("   n  N  N=n+1 seeds expl(med)  P1 max open  P1 top card  off-path  rank  pairs  attain  POLES  seeds w/pole  %inside")
    for n, N, it, ns in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        rt = np.array([x for r in R for x in r["roots"]])
        ins = 100 * ((rt >= 0) & (rt <= 1)).mean() if rt.size else 0.0
        print("   %d  %d  %-5s %-5d %-10.5f %-12.3f %-12.3f %-9.0f %-5s %-6d %-7d %-6d %-13s %.0f%%"
              % (n, N, "YES" if N == n + 1 else "no", len(R),
                 np.median([r["expl"] for r in R]),
                 np.median([r["maxopen"] for r in R]),
                 np.median([r["top"] for r in R]),
                 np.median([r["noff"] for r in R]),
                 ",".join(map(str, sorted({r["rank"] for r in R}))),
                 sum(r["npairs"] for r in R), sum(r["natt"] for r in R),
                 sum(r["npole"] for r in R),
                 "%d/%d" % (sum(1 for r in R if r["npole"] > 0), len(R)), ins))
    print("\n   (rank should be n-2 = 4)")
    for n, N, it, ns in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        U = np.array([r["u"] for r in R]).mean(0)
        print("   n=%d N=%d seats: %s" % (n, N, "  ".join("P%d %+.5f" % (k+1, v) for k, v in enumerate(U))))

if __name__ == "__main__":
    main()
