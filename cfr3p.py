"""
External-sampling MCCFR (Lanctot, Waugh, Zinkevich & Bowling, NIPS-22, 2009) for
three-player Kuhn poker.

Written as an INDEPENDENT reimplementation of the game -- its own history parser
and payoff function -- so that agreement with kuhn3p.py is a real cross-check
rather than a shared bug.  The output average strategy is returned in exactly
the kuhn3p 48-vector layout, so every existing tool (utilities, exploitability,
family.violations) applies to it unchanged.

Information sets are (player, card, situation), i.e. precisely kuhn3p.pidx, and
every one has exactly two actions: passive (K or F) and aggressive (B or C).
Regrets and strategy sums are stored as (48, 2) arrays with column 1 =
aggressive, matching the a/b/c parameterization.
"""
import itertools

import numpy as np

CARDS = (1, 2, 3, 4)
DEALS = list(itertools.permutations(CARDS, 3))
NI = 48

# history -> (player, situation).  Situations follow SGS Table 1.
NODE = {
    "": (0, 1), "B": (1, 2), "BF": (2, 3), "BC": (2, 4),
    "K": (1, 1), "KB": (2, 2), "KBF": (0, 3), "KBC": (0, 4),
    "KK": (2, 1), "KKB": (0, 2), "KKBF": (1, 3), "KKBC": (1, 4),
}
# at these histories no bet is outstanding: actions are check / bet
OPEN = {"", "K", "KK"}
TERMINAL = {"BFF", "BFC", "BCF", "BCC",
            "KBFF", "KBFC", "KBCF", "KBCC",
            "KKK", "KKBFF", "KKBFC", "KKBCF", "KKBCC"}


def actions(hist):
    """(passive, aggressive) at this history."""
    return ("K", "B") if hist in OPEN else ("F", "C")


def iset(hist, cards):
    """kuhn3p parameter index of the information set at `hist`."""
    pl, sit = NODE[hist]
    return pl * 16 + (cards[pl] - 1) * 4 + (sit - 1)


def payoff(cards, hist):
    """Chips won/lost by each player at a terminal history."""
    contrib = [1, 1, 1]
    folded = [False, False, False]
    h = ""
    for ch in hist:
        pl, _ = NODE[h]
        if ch in "BC":
            contrib[pl] += 1
        elif ch == "F":
            folded[pl] = True
        h += ch
    pot = sum(contrib)
    live = [i for i in range(3) if not folded[i]]
    w = max(live, key=lambda i: cards[i])
    pay = [-contrib[i] for i in range(3)]
    pay[w] += pot
    return pay


def _sigma(regret, i):
    """Regret matching at information set i -> (p_passive, p_aggressive)."""
    r0 = regret[i, 0] if regret[i, 0] > 0.0 else 0.0
    r1 = regret[i, 1] if regret[i, 1] > 0.0 else 0.0
    s = r0 + r1
    if s <= 0.0:
        return 0.5, 0.5
    return r0 / s, r1 / s


def _es(hist, cards, trav, regret, strat, rng):
    """External sampling: explore all of `trav`'s actions, sample everyone else."""
    if hist in TERMINAL:
        return payoff(cards, hist)[trav]

    i = iset(hist, cards)
    pas, agg = actions(hist)
    p0, p1 = _sigma(regret, i)
    pl, _ = NODE[hist]

    if pl == trav:
        v0 = _es(hist + pas, cards, trav, regret, strat, rng)
        v1 = _es(hist + agg, cards, trav, regret, strat, rng)
        v = p0 * v0 + p1 * v1
        regret[i, 0] += v0 - v
        regret[i, 1] += v1 - v
        return v

    # opponent (or, at the root deal, chance -- handled by the caller)
    strat[i, 0] += p0
    strat[i, 1] += p1
    a = agg if rng.random() < p1 else pas
    return _es(hist + a, cards, trav, regret, strat, rng)


def train(iterations=40000, seed=0, init_regret=0.0):
    """Run ES-MCCFR.  Returns the average strategy as a kuhn3p 48-vector."""
    rng = np.random.default_rng(seed)
    regret = np.zeros((NI, 2))
    strat = np.zeros((NI, 2))
    if init_regret:
        regret += rng.normal(0.0, init_regret, size=(NI, 2))
    nd = len(DEALS)
    for _ in range(iterations):
        cards = DEALS[rng.integers(nd)]
        for trav in (0, 1, 2):
            _es("", cards, trav, regret, strat, rng)
    tot = strat.sum(axis=1)
    p = np.full(NI, 0.5)
    nz = tot > 0
    p[nz] = strat[nz, 1] / tot[nz]          # probability of the AGGRESSIVE action
    return p


def selfcheck():
    """Cross-check the independent payoff logic against kuhn3p."""
    import kuhn3p as K
    rng = np.random.default_rng(0)
    worst = 0.0
    for _ in range(200):
        q = rng.random(48)
        # expected utility by walking this module's own tree, exhaustively
        tot = np.zeros(3)
        for cards in DEALS:
            stack = [("", 1.0)]
            while stack:
                h, pr = stack.pop()
                if h in TERMINAL:
                    tot += pr * np.array(payoff(cards, h), dtype=float)
                    continue
                i = iset(h, cards)
                pas, agg = actions(h)
                stack.append((h + agg, pr * q[i]))
                stack.append((h + pas, pr * (1.0 - q[i])))
        tot /= 24.0
        worst = max(worst, float(np.abs(tot - K.utilities(q)).max()))
    return worst
