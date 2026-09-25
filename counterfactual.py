"""
A controlled counterfactual for the last link.

The earlier test failed because P1's equilibrium betting range differs between
regimes, so calling rates cannot be compared across N.  Fix that by defining
every strategy by CARD RANK rather than card index, so the identical strategy
can be instantiated at any deck size.  Then only N varies.

P1's range is held fixed and polarised -- bet the best card always, bluff the
worst card at a fixed rate -- and we ask a single question:

    facing an IDENTICAL range, does an opponent's best response call MORE or
    LESS as the deck grows?

If calling rises with N under a fixed range, deck size drives it directly.  If
it does not, the effect in the equilibrium data is selection, not the deck.
"""
import numpy as np
import kuhnGen as Q, poletest as PT


def rank_profile(g, bluff=1.0 / 3.0, call_frac=0.5):
    """Rank-defined reference strategy, instantiable at any (n, N)."""
    N = g.ncard
    p = np.zeros(g.nparam)
    for pl in range(g.nplayer):
        for j in g.cards:
            rank = (j - 1) / (N - 1)               # 0 = worst, 1 = best
            for h in g.sit_hist[pl]:
                i = g.pidx(pl, j, h)
                if pl == 0 and h == "":
                    p[i] = 1.0 if j == N else (bluff if j == 1 else 0.0)
                elif h == "":
                    p[i] = 1.0 if j == N else 0.0
                else:
                    p[i] = 1.0 if rank >= 1.0 - call_frac else 0.0
    return p


def br_call_rate(g, p, player):
    """Fraction of this player's cards where CALLING P1's bet is optimal,
    and the rank threshold at which it flips."""
    r = g.reach(p)
    G = g.gradient(p)
    hs = [h for h in g.sit_hist[player] if h.startswith("B")]
    called, tot, thresh = 0.0, 0.0, None
    for j in g.cards:
        adv = w = 0.0
        for h in hs:
            i = g.pidx(player, j, h)
            if r[i] > 1e-12:
                adv += G[i][player]
                w += r[i]
        if w <= 1e-12:
            continue
        tot += 1
        if adv / w > 0:
            called += 1
            if thresh is None:
                thresh = (j - 1) / (g.ncard - 1)
    return (called / tot if tot else np.nan), tot, thresh


print("Rank-defined P1 range held IDENTICAL across deck sizes:")
print("   bet the best card always, bluff the worst at 1/3, check everything else.\n")
print("   n  N   cards with a live decision   BR calls with   rank threshold")
for n in (3, 4):
    for N in range(n + 1, n + 6):
        g = Q.Kuhn(n, N)
        p = rank_profile(g)
        frac, tot, th = br_call_rate(g, p, 1)
        print("   %d  %-3d %-27d %-15s %s"
              % (n, N, tot,
                 "%.4f" % frac if frac == frac else "n/a",
                 "%.3f" % th if th is not None else "never calls"))
    print()
print("   If the BR call fraction is FLAT in N, the deck size does not drive calling")
print("   directly and the equilibrium difference is a selection effect.")
