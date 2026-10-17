"""Cards and hand evaluation.

Cards are integers 0..51: ``rank_index * 4 + suit_index`` with ranks ``23456789TJQKA`` and suits
``cdhs``.  ``eval7`` ranks any 5- to 7-card set directly from rank and suit counts (it does not
enumerate the 21 five-card subsets); its value is a tuple that compares the way poker hands do:

    (8, high)                      straight flush (wheel: high = 5)
    (7, quad, kicker)              four of a kind
    (6, trips, pair)               full house
    (5, r1, r2, r3, r4, r5)        flush
    (4, high)                      straight
    (3, trips, k1, k2)             three of a kind
    (2, high pair, low pair, k)    two pair
    (1, pair, k1, k2, k3)          one pair
    (0, r1, r2, r3, r4, r5)        high card

Rank values are 2..14.  This tuple convention is the same as the independent best-of-21
implementation in ``holdem_bridge_audit.py``, which ``tests/test_cards.py`` uses as an oracle.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Iterable, Sequence, Tuple

RANKS = "23456789TJQKA"
SUITS = "cdhs"
CATEGORY_NAMES = ("high card", "one pair", "two pair", "three of a kind", "straight", "flush",
                  "full house", "four of a kind", "straight flush")


def parse_card(text: str) -> int:
    text = text.strip()
    if len(text) != 2 or text[0] not in RANKS or text[1] not in SUITS:
        raise ValueError("bad card %r" % text)
    return RANKS.index(text[0]) * 4 + SUITS.index(text[1])


def card_str(card: int) -> str:
    return RANKS[card // 4] + SUITS[card % 4]


def parse_cards(text: str) -> Tuple[int, ...]:
    """'2c 4d 6h' or '2c4d6h' -> (0, 9, ...)."""
    t = text.replace(" ", "").replace(",", "")
    if len(t) % 2:
        raise ValueError("bad card list %r" % text)
    cards = tuple(parse_card(t[i:i + 2]) for i in range(0, len(t), 2))
    if len(set(cards)) != len(cards):
        raise ValueError("duplicate card in %r" % text)
    return cards


def hand_str(cards: Sequence[int]) -> str:
    """Canonical two-card string, higher card first (rank, then suit order)."""
    a, b = sorted(cards, reverse=True)
    return card_str(a) + card_str(b)


def _straight_high(rank_values: Iterable[int]) -> int:
    present = set(rank_values)
    if 14 in present:
        present.add(1)
    for high in range(14, 4, -1):
        if all(high - k in present for k in range(5)):
            return high
    return 0


def eval7(cards: Sequence[int]) -> tuple:
    """Rank 5..7 cards (best five-card hand)."""
    if not 5 <= len(cards) <= 7 or len(set(cards)) != len(cards):
        raise ValueError("eval7 needs 5..7 distinct cards")
    values = [c // 4 + 2 for c in cards]
    suits = [c % 4 for c in cards]
    counts = Counter(values)
    by_suit = Counter(suits)
    flush_suit = next((s for s, n in by_suit.items() if n >= 5), None)
    if flush_suit is not None:
        fvals = sorted((v for v, s in zip(values, suits) if s == flush_suit), reverse=True)
        sf = _straight_high(fvals)
        if sf:
            return (8, sf)
    quads = sorted((v for v, n in counts.items() if n == 4), reverse=True)
    trips = sorted((v for v, n in counts.items() if n == 3), reverse=True)
    pairs = sorted((v for v, n in counts.items() if n == 2), reverse=True)
    if quads:
        q = quads[0]
        kicker = max(v for v in values if v != q)
        return (7, q, kicker)
    if trips and (len(trips) >= 2 or pairs):
        t = trips[0]
        rest = trips[1:] + pairs
        return (6, t, max(rest))
    if flush_suit is not None:
        return (5,) + tuple(fvals[:5])
    st = _straight_high(values)
    if st:
        return (4, st)
    if trips:
        t = trips[0]
        kick = sorted((v for v in values if v != t), reverse=True)[:2]
        return (3, t) + tuple(kick)
    if len(pairs) >= 2:
        p1, p2 = pairs[0], pairs[1]
        kick = max(v for v in values if v != p1 and v != p2)
        return (2, p1, p2, kick)
    if pairs:
        p = pairs[0]
        kick = sorted((v for v in values if v != p), reverse=True)[:3]
        return (1, p) + tuple(kick)
    return (0,) + tuple(sorted(values, reverse=True)[:5])


def category(rank: tuple) -> str:
    return CATEGORY_NAMES[rank[0]]


def all_two_card_hands(excluded: Iterable[int] = ()) -> Tuple[Tuple[int, int], ...]:
    ex = set(excluded)
    deck = [c for c in range(52) if c not in ex]
    return tuple(tuple(sorted(h, reverse=True)) for h in combinations(deck, 2))


def expand_class(spec: str, excluded: Iterable[int] = ()) -> Tuple[Tuple[int, int], ...]:
    """Hand-class notation -> concrete two-card hands (higher card first).

    'JJ' -> 6 combos, 'AKs' -> 4, 'AKo' -> 12, 'AK' -> 16, 'AsAh' -> that combo.
    Combos using an excluded card (the board) are dropped.
    """
    ex = set(excluded)
    s = spec.strip()
    out = []
    if len(s) == 4 and s[1] in SUITS and s[3] in SUITS:
        h = parse_cards(s)
        out = [tuple(sorted(h, reverse=True))]
    else:
        r1, r2 = s[0], s[1]
        kind = s[2] if len(s) == 3 else ""
        if r1 not in RANKS or r2 not in RANKS or kind not in ("", "s", "o"):
            raise ValueError("bad hand class %r" % spec)
        i1, i2 = RANKS.index(r1), RANKS.index(r2)
        for s1 in range(4):
            for s2 in range(4):
                c1, c2 = i1 * 4 + s1, i2 * 4 + s2
                if c1 == c2:
                    continue
                if i1 == i2 and s1 >= s2:
                    continue
                if i1 != i2:
                    if kind == "s" and s1 != s2:
                        continue
                    if kind == "o" and s1 == s2:
                        continue
                out.append(tuple(sorted((c1, c2), reverse=True)))
    return tuple(h for h in out if not (set(h) & ex))
