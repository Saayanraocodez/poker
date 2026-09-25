"""
Why does P1 go silent exactly when N = n+1?

Hypothesis: SLOW-PLAYING.  P1 checks even the best card when somebody else is
very likely to bet behind, because checking and then calling extracts more than
betting into n-1 opponents.  As the deck grows the chance that everyone checks
behind rises, so betting the top card becomes necessary.

Statistic: P(some later player bets | P1 checks) = 1 - prod_j (1 - a_j) over the
all-checks path, averaged over deals.
"""
import multiprocessing as mp, time, json
import numpy as np
import kuhnGen as Q, cfrGen as CG

CONFIGS = [(3, 4, 800000), (3, 5, 800000), (4, 5, 400000),
           (4, 6, 400000), (5, 6, 200000), (5, 7, 200000)]
NSEED = 6


def one(args):
    n, N, iters, seed = args
    g = Q.Kuhn(n, N)
    p = CG.train(g, iters, seed=seed)
    top = float(p[g.pidx(0, N, "")])                 # P1 opens with the BEST card
    mx = max(float(p[g.pidx(0, j, "")]) for j in g.cards)
    # P(everyone after P1 also checks | P1 checked), averaged over deals
    allcheck = 0.0
    for cards in g.deals:
        pr = 1.0
        for j in range(1, n):
            pr *= 1.0 - p[g.pidx(j, cards[j], "K" * j)]
        allcheck += g.kappa * pr
    G = g.gradient(p)
    return dict(n=n, N=N, seed=seed, top=top, maxopen=mx,
                p_someone_bets=1.0 - allcheck,
                du1_dtop=float(G[g.pidx(0, N, "")][0]),
                expl=float(g.exploitability_bi(p).max()))


def main():
    jobs = [(n, N, it, s) for n, N, it in CONFIGS for s in range(NSEED)]
    t = time.time()
    with mp.Pool(max(1, mp.cpu_count() - 1)) as pool:
        res = pool.map(one, jobs)
    print("%d runs in %.0fs\n" % (len(res), time.time() - t))
    json.dump(res, open("mechanism.json", "w"))
    print("   n  N  N=n+1  P1 opens TOP card   P(someone bets|P1 checks)   du1/d(open top)")
    rows = []
    for n, N, it in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        top = np.mean([r["top"] for r in R])
        pb = np.mean([r["p_someone_bets"] for r in R])
        du = np.mean([r["du1_dtop"] for r in R])
        rows.append((n, N, top, pb, du))
        print("   %d  %d  %-5s  %-18.4f  %-25.4f  %+.5f"
              % (n, N, "YES" if N == n + 1 else "no", top, pb, du))
    A = np.array([[r[2], r[3]] for r in rows])
    print("\n   corr(P1 opens top card, P(someone bets)) = %+.4f  over %d configs"
          % (np.corrcoef(A[:, 0], A[:, 1])[0, 1], len(rows)))
    allr = np.array([[r["top"], r["p_someone_bets"]] for r in res])
    print("   corr over all %d individual seeds              = %+.4f"
          % (len(res), np.corrcoef(allr[:, 0], allr[:, 1])[0, 1]))
    print("\n   du1/d(open top) < 0 means P1 strictly prefers to CHECK the best card")
    print("   (slow-play); > 0 means P1 wants to bet it.")


if __name__ == "__main__":
    main()
