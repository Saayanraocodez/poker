"""The correspondence between the all-in river game and three-player Kuhn poker.

Kuhn notation (Szafron-Gibson-Sturtevant Table 1): x_jk = probability of the AGGRESSIVE action
(bet in situation 1, call in situations 2-4) holding card j in situation k:

    k   P1 history   P2 history   P3 history
    1   (root)       K            KK
    2   KKB          B            KB
    3   KBF          KKBF         BF
    4   KBC          KKBC         BC

In the river game the bet is "B:1" (all-in), and the aggressive action is action index 1 at every
decision ("K","B:1") or ("F","C").  A private hand maps to the Kuhn card given by its showdown
strength order on the board (1 = weakest of the four types, 4 = strongest).
"""
from __future__ import annotations

from fractions import Fraction
from itertools import permutations
from typing import Dict, Tuple

import numpy as np

SITUATION = {
    0: {"": 1, "K-K-B:1": 2, "K-B:1-F": 3, "K-B:1-C": 4},
    1: {"K": 1, "B:1": 2, "K-K-B:1-F": 3, "K-K-B:1-C": 4},
    2: {"K-K": 1, "K-B:1": 2, "B:1-F": 3, "B:1-C": 4},
}
KUHN_TERMINALS = {"KKK", "BFF", "BFC", "BCF", "BCC", "KBFF", "KBFC", "KBCF", "KBCC",
                  "KKBFF", "KKBFC", "KKBCF", "KKBCC"}


def kuhn_letters(history: str) -> str:
    return "".join("B" if lab.startswith("B:") else lab for lab in history.split("-") if lab)


def card_types(game) -> list:
    """Per seat, per hand: Kuhn card 1..4 from the hand's strength rank among the four types."""
    levels = sorted({int(s) for st in game.strength for s in st})
    if len(levels) != 4:
        raise ValueError("the Kuhn correspondence needs exactly four strength levels, got %d" % len(levels))
    return [[levels.index(int(s)) + 1 for s in st] for st in game.strength]


def coordinate(game, iset_index: int, types=None) -> Tuple[int, int, int]:
    """(player 0..2, Kuhn card 1..4, situation 1..4) of a river information set."""
    types = card_types(game) if types is None else types
    I = game.isets[iset_index]
    return I.player, types[I.player][I.hand], SITUATION[I.player][I.history]


def kuhn_name(player: int, card: int, situation: int) -> str:
    return "abc"[player] + "%d%d" % (card, situation)


def profile_from_kuhn(game, kuhn_profile, exact: bool = True) -> np.ndarray:
    """kuhn_profile = (a, b, c), each {(card, situation): P(aggressive)} (the kuhn3.py format).
    Every hand of a type plays its type's Kuhn probabilities."""
    types = card_types(game)
    if exact:
        probs = np.full((game.n_isets, game.max_actions), Fraction(0), dtype=object)
    else:
        probs = np.zeros((game.n_isets, game.max_actions))
    for I in game.isets:
        p, j, k = coordinate(game, I.index, types)
        x = kuhn_profile[p][(j, k)]
        x = Fraction(x) if exact else float(x)
        probs[I.index, 0] = 1 - x
        probs[I.index, 1] = x
    return probs


def kuhn_payoff(cards: Tuple[int, int, int], history: str) -> Tuple[int, int, int]:
    """Kuhn terminal payoff, written from the rules independently of the river engine:
    ante 1 each, bet/call 1, highest unfolded card wins the whole pot."""
    contrib = [1, 1, 1]
    folded = set()
    order = []
    # rebuild who acted, from the Kuhn betting rule
    actor, bet, pending = 0, False, [0, 1, 2]
    for ch in history:
        p = pending.pop(0)
        if ch == "B":
            contrib[p] += 1
            bet = True
            pending = [(p + 1) % 3, (p + 2) % 3]
        elif ch == "C":
            contrib[p] += 1
        elif ch == "F":
            folded.add(p)
        order.append(p)
    assert not pending, "history %s is not terminal" % history
    live = [i for i in range(3) if i not in folded]
    winner = max(live, key=lambda i: cards[i])
    pot = sum(contrib)
    return tuple(-contrib[i] + (pot if i == winner else 0) for i in range(3))


def kuhn_deals():
    return list(permutations((1, 2, 3, 4), 3))
