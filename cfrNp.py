"""External-sampling MCCFR for N-card three-player Kuhn poker."""
import numpy as np

import kuhnNp as G


def _sigma(regret, i):
    r0 = regret[i, 0] if regret[i, 0] > 0.0 else 0.0
    r1 = regret[i, 1] if regret[i, 1] > 0.0 else 0.0
    s = r0 + r1
    return (0.5, 0.5) if s <= 0.0 else (r0 / s, r1 / s)


def _es(g, hist, cards, trav, regret, strat, rng):
    if hist in G.TERMINAL:
        return G.payoff(cards, hist)[trav]
    pl, sit = G.NODE[hist]
    i = g.pidx(pl, cards[pl], sit)
    pas, agg = G.actions(hist)
    p0, p1 = _sigma(regret, i)
    if pl == trav:
        v0 = _es(g, hist + pas, cards, trav, regret, strat, rng)
        v1 = _es(g, hist + agg, cards, trav, regret, strat, rng)
        v = p0 * v0 + p1 * v1
        regret[i, 0] += v0 - v
        regret[i, 1] += v1 - v
        return v
    strat[i, 0] += p0
    strat[i, 1] += p1
    a = agg if rng.random() < p1 else pas
    return _es(g, hist + a, cards, trav, regret, strat, rng)


def train(g, iterations=1000000, seed=0):
    """Returns the average strategy as a length-12N vector of P(aggressive)."""
    rng = np.random.default_rng(seed)
    regret = np.zeros((g.nparam, 2))
    strat = np.zeros((g.nparam, 2))
    deals = g.deals
    nd = len(deals)
    for _ in range(iterations):
        cards = deals[rng.integers(nd)]
        for trav in (0, 1, 2):
            _es(g, "", cards, trav, regret, strat, rng)
    tot = strat.sum(axis=1)
    p = np.full(g.nparam, 0.5)
    nz = tot > 0
    p[nz] = strat[nz, 1] / tot[nz]
    return p


def show(g, p, r=None, tol=5e-3):
    """Readable table: rows = cards, cols = situations, per player."""
    if r is None:
        r = g.reach(p)
    lines = []
    for pl, ch in enumerate("abc"):
        lines.append("   %s (P%d)   k=1        k=2        k=3        k=4"
                     % (ch, pl + 1))
        for j in g.cards:
            cells = []
            for k in (1, 2, 3, 4):
                i = g.pidx(pl, j, k)
                v, rr = p[i], r[i]
                mark = "*" if rr < 1e-6 else (" " if rr > 1e-3 else "~")
                if v < tol:
                    s = "0"
                elif v > 1 - tol:
                    s = "1"
                else:
                    s = "%.4f" % v
                cells.append("%-9s%s" % (s, mark))
            lines.append("     card %-2d  %s" % (j, " ".join(cells)))
    lines.append("   (* = unreached, ~ = reach < 1e-3)")
    return "\n".join(lines)
