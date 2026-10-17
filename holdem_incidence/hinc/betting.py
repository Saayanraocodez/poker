"""Public betting tree of one river street, built from explicit rules.

Rules (all amounts in big blinds, exact Fractions):

* ``prior_contrib[i]`` -- chips seat i put in before the river (sunk; part of the pot).
* ``stacks[i]``        -- chips seat i has left at the start of the river.  Stacks must be EQUAL
  (side pots are not implemented, so an under-stacked all-in call cannot arise).
* ``min_bet``          -- minimum opening bet.  An all-in for less is not offered.
* ``bet_sizes``        -- opening sizes: "allin", "<x>pot" (x times the current pot), "<x>bb".
* ``raise_sizes``      -- raise-to sizes: "allin", "<x>pot" (raise to the current bet plus x times
  the pot after calling), "<x>bb" (raise BY x).
* ``max_raises``       -- maximum number of raises after the opening bet (0 = no raise).
* A raise must be a full raise: its increment is at least the previous bet/raise increment and at
  least ``min_bet``; a short all-in raise is NOT offered (documented restriction).
* ``allow_open_fold``  -- whether a player may fold when checking is available (default False).

Seats act in order 0, 1, 2, ...  With no bet outstanding the actor may check or bet; facing a bet,
fold, call, or (if allowed) raise.  The street ends when every live player who can still act has
acted since the last bet or raise; a showdown follows unless only one player is left.

Action labels: ``K`` check, ``F`` fold, ``C`` call, ``B:<to>`` bet to <to>, ``R:<to>`` raise to
<to>, where <to> is the seat's total river contribution after the action.  A node's public
history is its labels joined by "-" (the root is ""), which is the stable public part of every
information-set identifier.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple


def _frac(x) -> Fraction:
    return Fraction(str(x)) if not isinstance(x, Fraction) else x


def _fmt(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else "%d/%d" % (x.numerator, x.denominator)


@dataclass
class BettingRules:
    n_players: int
    prior_contrib: Tuple[Fraction, ...]
    stacks: Tuple[Fraction, ...]
    min_bet: Fraction
    bet_sizes: Tuple[str, ...] = ("allin",)
    raise_sizes: Tuple[str, ...] = ()
    max_raises: int = 0
    allow_open_fold: bool = False

    @staticmethod
    def from_dict(d: dict) -> "BettingRules":
        n = int(d["n_players"])
        r = BettingRules(
            n_players=n,
            prior_contrib=tuple(_frac(x) for x in d["prior_contrib"]),
            stacks=tuple(_frac(x) for x in d["stacks"]),
            min_bet=_frac(d["min_bet"]),
            bet_sizes=tuple(d.get("bet_sizes", ["allin"])),
            raise_sizes=tuple(d.get("raise_sizes", [])),
            max_raises=int(d.get("max_raises", 0)),
            allow_open_fold=bool(d.get("allow_open_fold", False)),
        )
        r.validate()
        return r

    def to_dict(self) -> dict:
        return {"n_players": self.n_players, "prior_contrib": [_fmt(x) for x in self.prior_contrib],
                "stacks": [_fmt(x) for x in self.stacks], "min_bet": _fmt(self.min_bet),
                "bet_sizes": list(self.bet_sizes), "raise_sizes": list(self.raise_sizes),
                "max_raises": self.max_raises, "allow_open_fold": self.allow_open_fold}

    def validate(self) -> None:
        if self.n_players < 2:
            raise ValueError("need at least two players")
        if len(self.prior_contrib) != self.n_players or len(self.stacks) != self.n_players:
            raise ValueError("prior_contrib and stacks need one entry per player")
        if len(set(self.stacks)) != 1:
            raise ValueError("unequal stacks need side pots, which are not implemented")
        if self.stacks[0] <= 0 or self.min_bet <= 0:
            raise ValueError("stacks and min_bet must be positive")
        if self.max_raises > 0 and not self.raise_sizes:
            raise ValueError("max_raises > 0 needs raise_sizes")


@dataclass
class Node:
    id: int
    history: str
    labels: Tuple[str, ...]
    actor: Optional[int]                      # None at a terminal
    actions: Tuple[str, ...] = ()
    children: Tuple[int, ...] = ()
    terminal: bool = False
    kind: Optional[str] = None                # "fold" or "showdown" at a terminal
    contrib: Tuple[Fraction, ...] = ()        # TOTAL contributions (prior + river) at a terminal
    folded: frozenset = frozenset()
    parent: Optional[int] = None
    depth: int = 0


@dataclass
class BettingTree:
    rules: BettingRules
    nodes: List[Node] = field(default_factory=list)

    @property
    def decision_nodes(self) -> List[Node]:
        return [n for n in self.nodes if not n.terminal]

    @property
    def terminal_nodes(self) -> List[Node]:
        return [n for n in self.nodes if n.terminal]

    def by_history(self) -> Dict[str, Node]:
        return {n.history: n for n in self.nodes}


def _size_amount(spec: str, pot: Fraction, level: Fraction, to_call: Fraction, opening: bool) -> Fraction:
    """Return the 'to' amount (seat's total river contribution) a size spec asks for, before
    clamping to the stack.  ``level`` = current highest river contribution."""
    if spec == "allin":
        return Fraction(10 ** 9)
    if spec.endswith("pot"):
        x = Fraction(spec[:-3])
        if opening:
            return x * pot
        return level + x * (pot + to_call)
    if spec.endswith("bb"):
        x = Fraction(spec[:-2])
        return x if opening else level + x
    raise ValueError("bad size spec %r" % spec)


def build_tree(rules: BettingRules) -> BettingTree:
    rules.validate()
    n = rules.n_players
    tree = BettingTree(rules=rules)

    def add(node: Node) -> int:
        node.id = len(tree.nodes)
        tree.nodes.append(node)
        return node.id

    def rec(labels, street, folded, allin, to_act, level, last_inc, n_raises, parent, depth):
        live = [i for i in range(n) if i not in folded]
        history = "-".join(labels)
        if len(live) == 1:
            return add(Node(id=-1, history=history, labels=tuple(labels), actor=None, terminal=True,
                            kind="fold", contrib=tuple(rules.prior_contrib[i] + street[i] for i in range(n)),
                            folded=frozenset(folded), parent=parent, depth=depth))
        pending = [i for i in to_act if i not in folded and i not in allin]
        if not pending:
            return add(Node(id=-1, history=history, labels=tuple(labels), actor=None, terminal=True,
                            kind="showdown", contrib=tuple(rules.prior_contrib[i] + street[i] for i in range(n)),
                            folded=frozenset(folded), parent=parent, depth=depth))
        p = pending[0]
        pot = sum(rules.prior_contrib) + sum(street)
        remaining = rules.stacks[p] - street[p]
        to_call = level - street[p]
        moves = []                      # (label, new state pieces)
        if to_call == 0:
            if rules.allow_open_fold:
                moves.append(("F", "fold", None))
            moves.append(("K", "check", None))
            opening = level == 0
            if opening:
                tos = []
                for spec in rules.bet_sizes:
                    to = min(_size_amount(spec, pot, level, to_call, True), remaining)
                    if to >= rules.min_bet:           # an all-in for less than min_bet is not offered
                        tos.append(to)
                for to in sorted(set(tos)):
                    moves.append(("B:" + _fmt(to), "bet", to))
        else:
            moves.append(("F", "fold", None))
            moves.append(("C", "call", min(to_call, remaining)))
            if n_raises < rules.max_raises and remaining > to_call:
                tos = []
                for spec in rules.raise_sizes:
                    to = min(_size_amount(spec, pot, level, to_call, False), rules.stacks[p])
                    inc = to - level
                    if inc >= max(last_inc, rules.min_bet):
                        tos.append(to)
                for to in sorted(set(tos)):
                    moves.append(("R:" + _fmt(to), "raise", to))
        node = Node(id=-1, history=history, labels=tuple(labels), actor=p,
                    actions=tuple(m[0] for m in moves), parent=parent, depth=depth)
        nid = add(node)
        kids = []
        order_after = [(p + k) % n for k in range(1, n)]
        for label, kind, amt in moves:
            st = list(street)
            fo, al = set(folded), set(allin)
            ta = [i for i in to_act if i != p]
            lv, li, nr = level, last_inc, n_raises
            if kind == "fold":
                fo.add(p)
            elif kind == "check":
                pass
            elif kind == "call":
                st[p] += amt
                if st[p] == rules.stacks[p]:
                    al.add(p)
            else:                                   # bet or raise to amt
                st[p] = amt
                li = amt - level
                if kind == "raise":
                    nr += 1
                lv = amt
                if st[p] == rules.stacks[p]:
                    al.add(p)
                ta = [i for i in order_after if i not in fo and i not in al]
            # keep the action order: seats after p first
            ta = [i for i in order_after if i in ta] + ([p] if p in ta else [])
            kids.append(rec(labels + [label], tuple(st), frozenset(fo), frozenset(al), ta, lv, li, nr, nid, depth + 1))
        node.children = tuple(kids)
        return nid

    rec([], tuple(Fraction(0) for _ in range(n)), frozenset(), frozenset(), list(range(n)),
        Fraction(0), Fraction(0), 0, None, 0)
    # ids were assigned in creation order; the root is node 0
    return tree


def validate_tree(tree: BettingTree) -> dict:
    """Structural checks; raises on failure, returns counts."""
    rules = tree.rules
    for node in tree.nodes:
        if node.terminal:
            assert node.actor is None and not node.actions
            assert all(c >= 0 for c in node.contrib)
            for i in range(rules.n_players):
                assert node.contrib[i] - rules.prior_contrib[i] <= rules.stacks[i], "over-contribution"
            live = [i for i in range(rules.n_players) if i not in node.folded]
            assert len(live) >= 1
            if node.kind == "showdown":
                lv = {node.contrib[i] for i in live}
                assert len(lv) == 1, "live players must have matched at a showdown"
        else:
            assert len(node.actions) == len(node.children) >= 2, "a decision needs two or more actions"
            assert len(set(node.actions)) == len(node.actions)
            if not rules.allow_open_fold:
                assert not ("K" in node.actions and "F" in node.actions), "open fold offered"
            for c in node.children:
                assert tree.nodes[c].parent == node.id
    return {"decision_nodes": len(tree.decision_nodes), "terminal_nodes": len(tree.terminal_nodes)}
