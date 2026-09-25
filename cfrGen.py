"""External-sampling MCCFR for the general n-player Kuhn engine."""
import numpy as np


def _sigma(regret, i):
    r0 = regret[i, 0] if regret[i, 0] > 0.0 else 0.0
    r1 = regret[i, 1] if regret[i, 1] > 0.0 else 0.0
    s = r0 + r1
    return (0.5, 0.5) if s <= 0.0 else (r0 / s, r1 / s)


def _es(g, hist, cards, trav, regret, strat, rng):
    term, actor, _ = g.state(hist)
    if term:
        return g.payoff(cards, hist)[trav]
    i = g.pidx(actor, cards[actor], hist)
    pas, agg = g.actions(hist)
    p0, p1 = _sigma(regret, i)
    if actor == trav:
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
    rng = np.random.default_rng(seed)
    regret = np.zeros((g.nparam, 2))
    strat = np.zeros((g.nparam, 2))
    deals, nd = g.deals, len(g.deals)
    players = tuple(range(g.nplayer))
    for _ in range(iterations):
        cards = deals[rng.integers(nd)]
        for trav in players:
            _es(g, "", cards, trav, regret, strat, rng)
    tot = strat.sum(axis=1)
    p = np.full(g.nparam, 0.5)
    nz = tot > 0
    p[nz] = strat[nz, 1] / tot[nz]
    return p
