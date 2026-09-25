"""
Why does du1/d(open top) flip sign at N = n+1?

Holding the BEST card P1 never loses a showdown and never folds, so P1's payoff
on those deals is exactly the pot minus P1's own contribution -- i.e. exactly
the sum of the OPPONENTS' contributions.  Hence

    du1/d(open top) = (1/N) * sum_j [ P(j puts in a 2nd chip | P1 bets)
                                    - P(j puts in a 2nd chip | P1 checks) ]

so the derivative decomposes exactly, one term per opponent.  Delta_j > 0 means
betting extracts more from j; Delta_j < 0 means checking extracts more from j
(slow-play works on that opponent).
"""
import multiprocessing as mp, time, json
import numpy as np
import kuhnGen as Q, cfrGen as CG

CONFIGS = [(3, 4, 800000), (3, 5, 800000), (4, 5, 400000),
           (4, 6, 400000), (5, 6, 200000), (5, 7, 200000)]
NSEED = 6


def contribs(g, cards, hist):
    n = g.nplayer
    c = [1] * n
    h = ""
    for ch in hist:
        _, actor, _ = g.state(h)
        if ch in "BC":
            c[actor] += 1
        h += ch
    return c


def extra_chips(g, p, top_value):
    """E[extra chips by each player], over deals where P1 holds the best card."""
    q = np.array(p, float)
    q[g.pidx(0, g.ncard, "")] = top_value
    n = g.nplayer
    tot = np.zeros(n)
    mass = 0.0
    for cards in g.deals:
        if cards[0] != g.ncard:
            continue
        mass += g.kappa
        stack = [("", 1.0)]
        while stack:
            h, w = stack.pop()
            term, actor, _ = g.state(h)
            if term:
                c = contribs(g, cards, h)
                tot += g.kappa * w * (np.array(c) - 1)
                continue
            i = g.pidx(actor, cards[actor], h)
            pas, agg = g.actions(h)
            stack.append((h + agg, w * q[i]))
            stack.append((h + pas, w * (1.0 - q[i])))
    return tot, mass


def one(args):
    n, N, iters, seed = args
    g = Q.Kuhn(n, N)
    p = CG.train(g, iters, seed=seed)
    bet, _ = extra_chips(g, p, 1.0)
    chk, _ = extra_chips(g, p, 0.0)
    delta = bet - chk
    engine = float(g.gradient(p)[g.pidx(0, N, "")][0])
    return dict(n=n, N=N, seed=seed, engine=engine,
                identity=float(delta[1:].sum()), delta=delta.tolist(),
                p1_own=float(delta[0]))


def main():
    jobs = [(n, N, it, s) for n, N, it in CONFIGS for s in range(NSEED)]
    t = time.time()
    with mp.Pool(min(18, mp.cpu_count() - 1)) as pool:
        res = pool.map(one, jobs)
    json.dump(res, open("decompose.json", "w"))
    print("%d runs in %.0fs\n" % (len(res), time.time() - t))

    err = max(abs(r["engine"] - r["identity"]) for r in res)
    print("IDENTITY CHECK  du1/d(open top) == sum_j Delta_j over opponents")
    print("   max |engine - decomposition| over %d runs = %.2e\n" % (len(res), err))

    print("   n  N  N=n+1   du1/d(top)   " + "  ".join("Delta P%d" % (k + 2) for k in range(5)))
    for n, N, it in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        d = np.array([r["delta"] for r in R]).mean(0)
        cells = "  ".join("%+9.5f" % d[k] for k in range(1, n))
        print("   %d  %d  %-5s  %+10.5f   %s"
              % (n, N, "YES" if N == n + 1 else "no",
                 np.mean([r["engine"] for r in R]), cells))
    print("\n   Delta_j > 0: betting extracts more from opponent j")
    print("   Delta_j < 0: checking extracts more from j (slow-play works on j)")
    print("\n   split by opponent role:")
    print("   n  N  N=n+1   NEXT player (P2)   ALL LATER players   total")
    for n, N, it in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        d = np.array([r["delta"] for r in R]).mean(0)
        nxt, later = d[1], d[2:n].sum()
        print("   %d  %d  %-5s  %+16.5f   %+17.5f   %+.5f"
              % (n, N, "YES" if N == n + 1 else "no", nxt, later, nxt + later))


if __name__ == "__main__":
    main()
