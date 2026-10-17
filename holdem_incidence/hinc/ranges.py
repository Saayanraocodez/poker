"""Seat ranges and the joint root prior over card-compatible ordered deals.

Two kinds of root distribution are kept distinct:

* ``product_prior`` -- a DELIBERATELY SPECIFIED prior: independent per-seat weights w_i(h),
  multiplied and conditioned on card compatibility,
      q(h1, h2, h3) = w1(h1) w2(h2) w3(h3) 1[compatible] / Z.
  Blocker relationships are kept exactly, because deals are enumerated at the level of concrete
  two-card hands (never as independent strength ranks).
* ``table_prior`` -- an explicit joint table, e.g. one DERIVED from an upstream strategy's reach
  probabilities.  It may carry dependence a product form cannot represent.  Only the container
  is implemented; no upstream (pre-river) game is solved in this framework.

Weights are kept as exact Fractions so the prior is exact; a float copy is used for training.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Dict, List, Sequence, Tuple

from .cards import expand_class, hand_str, parse_cards


@dataclass
class SeatRange:
    hands: List[Tuple[int, int]]          # concrete hands, higher card first
    weights: List[Fraction]               # exact non-negative weights
    labels: List[str]                     # canonical hand strings
    spec: list                            # the specification it came from (for the record)


def build_seat_range(spec, board: Sequence[int]) -> SeatRange:
    """spec: list of entries, each a hand class / combo string or [string, weight].

    Weight strings like "1/2" are parsed exactly.  A combo listed twice is an error (that would
    silently double its weight).  Combos that use a board card are dropped.
    """
    hands, weights = [], []
    seen = set()
    for entry in spec:
        if isinstance(entry, str):
            cls, w = entry, Fraction(1)
        else:
            cls, w = entry[0], Fraction(str(entry[1]))
        if w < 0:
            raise ValueError("negative weight for %r" % cls)
        if w == 0:
            continue                    # zero weight = outside the support; never an information set
        for h in expand_class(cls, excluded=board):
            if h in seen:
                raise ValueError("hand %s listed twice" % hand_str(h))
            seen.add(h)
            hands.append(h)
            weights.append(w)
    if not hands:
        raise ValueError("empty range after removing board conflicts")
    return SeatRange(hands=hands, weights=weights, labels=[hand_str(h) for h in hands], spec=list(spec))


@dataclass
class RootPrior:
    deals: List[Tuple[int, ...]]          # per deal: index into each seat's hand list
    probs: List[Fraction]                 # exact, sums to 1
    kind: str                             # "product" or "table"
    note: str


def product_prior(seats: Sequence[SeatRange]) -> RootPrior:
    deals, raw = [], []
    for combo in product(*[range(len(s.hands)) for s in seats]):
        cards = [c for s, i in zip(seats, combo) for c in s.hands[i]]
        if len(set(cards)) != len(cards):
            continue
        w = Fraction(1)
        for s, i in zip(seats, combo):
            w *= s.weights[i]
        if w == 0:
            continue
        deals.append(tuple(combo))
        raw.append(w)
    z = sum(raw)
    if z == 0:
        raise ValueError("no compatible deal with positive weight")
    return RootPrior(deals=deals, probs=[w / z for w in raw], kind="product",
                     note="specified prior: product of seat weights conditioned on card compatibility")


def table_prior(seats: Sequence[SeatRange], table: Dict[Tuple[int, ...], Fraction], note: str) -> RootPrior:
    deals, probs = [], []
    for combo, w in sorted(table.items()):
        cards = [c for s, i in zip(seats, combo) for c in s.hands[i]]
        if len(set(cards)) != len(cards):
            raise ValueError("table prior puts mass on an incompatible deal %r" % (combo,))
        if w < 0:
            raise ValueError("negative table weight")
        if w > 0:
            deals.append(tuple(combo))
            probs.append(Fraction(w))
    z = sum(probs)
    return RootPrior(deals=deals, probs=[p / z for p in probs], kind="table", note=note)
