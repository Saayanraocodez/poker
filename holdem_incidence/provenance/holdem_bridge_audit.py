"""Audit a three-player Kuhn embedding in a prescribed-range Hold'em river game.

Run with Python 3.10+: python holdem_bridge_audit.py
No dependencies. This verifies a game mapping, not a solve of full Hold'em.
"""

from collections import Counter
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path

BOARD = ("2c", "4d", "6h", "8s", "Tc")
RANGE = (("Js", "Jh"), ("Qs", "Qh"), ("Ks", "Kh"), ("As", "Ah"))
RANKS = "23456789TJQKA"


def rank5(cards):
    """Lexicographically increasing standard five-card high-poker rank."""
    values = [RANKS.index(card[0]) + 2 for card in cards]
    counts = Counter(values)
    groups = sorted(((n, r) for r, n in counts.items()), reverse=True)
    unique = sorted(counts)
    straight = 5 if unique == [2, 3, 4, 5, 14] else (
        unique[-1] if len(unique) == 5 and unique[-1] - unique[0] == 4 else 0
    )
    flush = len({card[1] for card in cards}) == 1
    descending = sorted(values, reverse=True)
    if straight and flush:
        return (8, straight)
    if groups[0][0] == 4:
        return (7, groups[0][1], groups[1][1])
    if [n for n, r in groups] == [3, 2]:
        return (6, groups[0][1], groups[1][1])
    if flush:
        return (5, *descending)
    if straight:
        return (4, straight)
    if groups[0][0] == 3:
        return (3, groups[0][1], *sorted((r for n, r in groups[1:]), reverse=True))
    if [n for n, r in groups[:2]] == [2, 2]:
        return (2, *sorted((groups[0][1], groups[1][1]), reverse=True), groups[2][1])
    if groups[0][0] == 2:
        return (1, groups[0][1], *sorted((r for n, r in groups[1:]), reverse=True))
    return (0, *descending)


def rank7(cards):
    return max(map(rank5, combinations(cards, 5)))


def betting_leaves():
    """One bb left per seat; minimum opening bet is one bb; initial pot 3 bb.

    K=check, B=bet all-in, F=fold, C=call all-in. No raise is possible.
    """
    def walk(history, actor, bet, pending, added, folded):
        if not pending:
            yield history, added, folded
            return
        actions = ("F", "C") if bet else ("K", "B")
        for action in actions:
            next_added = list(added)
            next_folded = set(folded)
            next_bet = bet or action == "B"
            if action in ("B", "C"):
                next_added[actor] = 1
            elif action == "F":
                next_folded.add(actor)
            next_pending = 2 if action == "B" else pending - 1
            yield from walk(history + action, (actor + 1) % 3, next_bet,
                            next_pending, tuple(next_added), next_folded)
    return list(walk("", 0, False, 3, (0, 0, 0), set()))


def payoffs(strengths, added, folded):
    active = [i for i in range(3) if i not in folded]
    best = max(strengths[i] for i in active)
    winners = [i for i in active if strengths[i] == best]
    pot = 3 + sum(added)
    # Each seat has already contributed 1 bb; exact fractions handle ties.
    return tuple(-1 - added[i] + (Fraction(pot, len(winners)) if i in winners else 0)
                 for i in range(3))


def legal_deals(hands):
    for deal in product(range(len(hands)), repeat=3):
        cards = list(BOARD) + [c for index in deal for c in hands[index]]
        if len(set(cards)) == len(cards):
            yield deal


def audit():
    strengths = [rank7(BOARD + hand) for hand in RANGE]
    assert strengths == sorted(strengths) and len(set(strengths)) == 4
    assert all(value[0] == 1 for value in strengths)
    leaves = betting_leaves()
    expected_histories = {"KKK", "BFF", "BFC", "BCF", "BCC", "KBFF", "KBFC",
                          "KBCF", "KBCC", "KKBFF", "KKBFC", "KKBCF", "KKBCC"}
    assert {history for history, _, _ in leaves} == expected_histories
    deals = list(legal_deals(RANGE))
    assert len(deals) == 24
    checked = 0
    for deal in deals:
        for history, added, folded in leaves:
            holdem = payoffs([strengths[i] for i in deal], added, folded)
            kuhn = payoffs([i + 1 for i in deal], added, folded)
            assert holdem == kuhn, (deal, history, holdem, kuhn)
            assert sum(holdem) == 0
            checked += 1

    expanded = tuple(tuple(rank + suit for suit in suits)
                     for rank in "JQKA" for suits in combinations("cdhs", 2))
    expanded_strengths = [rank7(BOARD + hand) for hand in expanded]
    expanded_deals = list(legal_deals(expanded))
    tie_deals = sum(len({expanded_strengths[i] for i in deal}) < 3
                    for deal in expanded_deals)
    return {
        "scope": "Prescribed-range three-player river continuation game, not full Hold'em",
        "board": BOARD,
        "range_per_player": RANGE,
        "initial_pot_bb": 3,
        "prior_contribution_per_player_bb": 1,
        "remaining_stack_per_player_bb": 1,
        "minimum_opening_bet_bb": 1,
        "chance_prior": "Uniform over card-compatible ordered deals",
        "legal_ordered_deals": len(deals),
        "terminal_betting_histories_per_deal": len(leaves),
        "terminal_payoff_comparisons": checked,
        "all_terminal_payoffs_match_kuhn": True,
        "zero_sum_checks_passed": checked,
        "expanded_all_JJ_QQ_KK_AA_combos": {
            "hands_per_player": len(expanded),
            "legal_ordered_deals": len(expanded_deals),
            "deals_with_any_tied_hand_strength": tie_deals,
            "terminal_leaves": len(expanded_deals) * len(leaves),
            "status": "Size and tie audit only; no equilibrium computed"
        }
    }


if __name__ == "__main__":
    result = audit()
    target = Path(__file__).with_name("holdem_bridge_audit.json")
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
