"""
C: why do later opponents put in less money against a bet when the deck is minimal?

Two refinements of the 5c decomposition:

 1. Split Delta_j into its two halves -- E[extra chips | P1 BETS] and
    E[extra chips | P1 CHECKS] -- to see which side actually moves.

 2. Measure how sharply an opponent's own card determines its RELATIVE rank.
    With N = n+1 almost every card is dealt, so holding card c tells you almost
    exactly whether you are beaten; with spare cards the same holding is
    ambiguous.  Sharpness = mean over (opponent, card) of min(q, 1-q) where
    q = P(this card is the best among the opponents | I hold it, P1 holds the top).
    0 = perfect information about rank, 0.5 = maximal ambiguity.
"""
import itertools, multiprocessing as mp, time
import numpy as np
import kuhnGen as Q, cfrGen as CG, decompose as D

CONFIGS = [(3, 4, 800000), (3, 5, 800000), (4, 5, 400000),
           (4, 6, 400000), (5, 6, 200000), (5, 7, 200000)]
NSEED = 6


def sharpness(n, N):
    """How well does an opponent's own card pin down its rank among opponents?"""
    cards = tuple(range(1, N + 1))
    vals = []
    for j in range(1, n):                          # each opponent seat
        for c in cards[:-1]:                       # P1 holds the top card N
            hit = tot = 0
            for rest in itertools.permutations([x for x in cards if x not in (N, c)],
                                               n - 2):
                tot += 1
                if all(c > y for y in rest):
                    hit += 1
            if tot:
                q = hit / tot
                vals.append(min(q, 1 - q))
    return float(np.mean(vals))


def one(args):
    n, N, iters, seed = args
    g = Q.Kuhn(n, N)
    p = CG.train(g, iters, seed=seed)
    bet, _ = D.extra_chips(g, p, 1.0)
    chk, _ = D.extra_chips(g, p, 0.0)
    later = slice(2, n)                            # opponents after the next one
    return dict(n=n, N=N, seed=seed,
                bet_later=float(bet[later].sum()), chk_later=float(chk[later].sum()),
                bet_next=float(bet[1]), chk_next=float(chk[1]))


def main():
    jobs = [(n, N, it, s) for n, N, it in CONFIGS for s in range(NSEED)]
    t = time.time()
    with mp.Pool(min(18, mp.cpu_count() - 1)) as pool:
        res = pool.map(one, jobs)
    print("%d runs in %.0fs\n" % (len(res), time.time() - t))

    print("Which half of Delta moves?  (later opponents, expected extra chips)")
    print("   n  N  N=n+1   if P1 BETS   if P1 CHECKS   Delta      sharpness")
    rows = []
    for n, N, it in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        b = np.mean([r["bet_later"] for r in R])
        c = np.mean([r["chk_later"] for r in R])
        sh = sharpness(n, N)
        rows.append((n, N, b, c, b - c, sh))
        print("   %d  %d  %-5s  %10.5f   %12.5f   %+9.5f  %.4f"
              % (n, N, "YES" if N == n + 1 else "no", b, c, b - c, sh))
    A = np.array([[r[4], r[5]] for r in rows])
    print("\n   corr(Delta_later, sharpness) = %+.4f" % np.corrcoef(A[:, 0], A[:, 1])[0, 1])
    print("\n   sharpness: 0 = your card tells you your rank exactly,")
    print("              0.5 = it tells you nothing")
    print("\nSame split for the NEXT player:")
    print("   n  N  N=n+1   if P1 BETS   if P1 CHECKS   Delta")
    for n, N, it in CONFIGS:
        R = [r for r in res if r["n"] == n and r["N"] == N]
        b = np.mean([r["bet_next"] for r in R])
        c = np.mean([r["chk_next"] for r in R])
        print("   %d  %d  %-5s  %10.5f   %12.5f   %+9.5f"
              % (n, N, "YES" if N == n + 1 else "no", b, c, b - c))


if __name__ == "__main__":
    main()
