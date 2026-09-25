"""
The remaining causal link: why do later opponents call P1's bet less at N = n+1?

Hypothesis: at N = n+1 P1 is silent, so the "facing P1's bet" information sets
carry ~zero reach.  Their calling frequencies are then not set by anyone's
positive incentive -- they are set by DETERRENCE, and deterring P1 (who holds
the best card when betting) requires calling LESS.  At N > n+1 P1 really does
bet, those sets are on-path, and the frequencies are set by the opponents' own
best response, which calls MORE.

Two predictions:
  1. reach of the bet-response sets ~ 0 at N = n+1, substantial at N > n+1.
  2. at N = n+1 the equilibrium calling frequency sits BELOW the myopic best
     response to P1's actual betting range; at N > n+1 the two agree.
"""
import multiprocessing as mp, time
import numpy as np
import kuhnGen as Q, cfrGen as CG

CONFIGS = [(3, 4, 800000), (3, 5, 800000), (4, 5, 400000),
           (4, 6, 400000), (5, 6, 200000), (5, 7, 200000)]
NSEED = 6


def bet_response_sets(g):
    """Every coordinate where a player is answering a bet made by P1."""
    out = []
    for pl in range(1, g.nplayer):
        for h in g.sit_hist[pl]:
            if h.startswith("B"):
                for j in g.cards:
                    out.append(g.pidx(pl, j, h))
    return out


def one(args):
    n, N, iters, seed = args
    g = Q.Kuhn(n, N)
    p = CG.train(g, iters, seed=seed)
    brs = bet_response_sets(g)
    r = g.reach(p)
    reach_eq = float(r[brs].sum())

    # myopic best response at those sets, against a P1 who DOES bet the top card
    q = p.copy()
    q[g.pidx(0, N, "")] = 1.0
    rq = g.reach(q)
    G = g.gradient(q)
    call_eq = call_br = wt = 0.0
    for i in brs:
        w = rq[i]
        if w < 1e-12:
            continue
        pl = 0
        for k in range(g.nplayer):
            lo = g.offset[k]
            if lo <= i < lo + g.ncard * g.nsit[k]:
                pl = k
        adv = G[i][pl] / w                      # per-unit-reach gain from calling
        call_eq += w * p[i]
        call_br += w * (1.0 if adv > 0 else 0.0)
        wt += w
    return dict(n=n, N=N, seed=seed, reach_eq=reach_eq,
                call_eq=call_eq / wt if wt else np.nan,
                call_br=call_br / wt if wt else np.nan)


def main():
    jobs = [(n, N, it, s) for n, N, it in CONFIGS for s in range(NSEED)]
    t = time.time()
    with mp.Pool(min(18, mp.cpu_count() - 1)) as pool:
        res = pool.map(one, jobs)
    print("%d runs in %.0fs\n" % (len(res), time.time() - t))
    print("   n  N  N=n+1   reach of bet-response sets   equilibrium call rate   myopic BR call rate   gap")
    for n, N, it in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        rc = np.mean([r["reach_eq"] for r in R])
        ce = np.nanmean([r["call_eq"] for r in R])
        cb = np.nanmean([r["call_br"] for r in R])
        print("   %d  %d  %-5s   %-26.6f  %-21.4f  %-19.4f  %+.4f"
              % (n, N, "YES" if N == n + 1 else "no", rc, ce, cb, ce - cb))
    print("\n   Prediction 1: reach ~ 0 at N = n+1, substantial at N > n+1")
    print("   Prediction 2: equilibrium call rate BELOW myopic BR at N = n+1 (negative gap),")
    print("                 and matching at N > n+1 (gap ~ 0)")


if __name__ == "__main__":
    main()
