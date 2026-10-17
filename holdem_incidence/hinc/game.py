"""A conditional river continuation game: board + seat ranges + root prior + betting tree.

What a policy may see: its own private hand and the public state (board, betting history; stacks
and contributions follow from the history).  Information sets are therefore
``(player, own hand, public history)``, which keeps perfect recall (a player's own past actions
are in the public history) and never merges two hands, however similar their equity.

What only the evaluator sees: the full deal.

Payoff convention (recorded in every experiment): utility = net chips in big blinds relative to
the start of the HAND, i.e. ``-(prior contribution + river contribution) + pot share``.  This is
the Kuhn convention (the ante counts), so utilities sum to zero at every leaf.  Values are
CONDITIONAL on reaching this river root with the declared prior; they are not per-hand values
from the start of Hold'em.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Sequence, Tuple

import numpy as np

from .betting import BettingRules, BettingTree, build_tree, validate_tree
from .cards import card_str, eval7, parse_cards
from .ranges import RootPrior, SeatRange, build_seat_range, product_prior

PAYOFF_CONVENTION = ("net chips (big blinds) relative to the start of the hand: "
                     "-(prior contribution + river contribution) + pot share; zero-sum at every leaf; "
                     "split pots divided equally among tied best hands")


@dataclass
class InfoSet:
    index: int
    id: str                 # stable identifier "P<k>|<hand>|<public history>"
    player: int
    hand: int               # index into the player's seat range
    hand_label: str
    node: int               # public decision node id
    history: str
    actions: Tuple[str, ...]


class RiverGame:
    def __init__(self, config: dict):
        self.config = config
        self.name = config.get("name", "unnamed")
        self.board = parse_cards(config["board"])
        if len(self.board) != 5:
            raise ValueError("a river game needs a five-card board")
        self.rules = BettingRules.from_dict(config["betting"])
        self.n = self.rules.n_players
        seat_specs = config["seats"] if "seats" in config else [config["range"]] * self.n
        if len(seat_specs) != self.n:
            raise ValueError("one range per seat")
        self.seats: List[SeatRange] = [build_seat_range(s, self.board) for s in seat_specs]
        if config.get("prior", "product") != "product":
            raise ValueError("only the specified product prior is constructed from a config; "
                             "use ranges.table_prior for a derived joint table")
        self.prior: RootPrior = product_prior(self.seats)
        self.tree: BettingTree = build_tree(self.rules)
        self.tree_counts = validate_tree(self.tree)
        self._build_arrays()

    # ------------------------------------------------------------------ construction
    def _build_arrays(self) -> None:
        n = self.n
        self.deals = np.array(self.prior.deals, dtype=np.int64).reshape(-1, n)
        self.D = self.deals.shape[0]
        self.prior_x = list(self.prior.probs)
        self.prior_f = np.array([float(p) for p in self.prior_x])

        # hand strengths: eval7 tuples, ranked globally (higher int = stronger)
        tuples = {}
        for s in self.seats:
            for h in s.hands:
                if h not in tuples:
                    tuples[h] = eval7(self.board + h)
        order = sorted(set(tuples.values()))
        rank_of = {t: i for i, t in enumerate(order)}
        self.hand_rank_tuple = [[tuples[h] for h in s.hands] for s in self.seats]
        self.strength = [np.array([rank_of[tuples[h]] for h in s.hands], dtype=np.int64) for s in self.seats]
        # per deal strengths [D, n]
        self.deal_strength = np.stack([self.strength[i][self.deals[:, i]] for i in range(n)], axis=1)

        # information sets
        self.isets: List[InfoSet] = []
        self.iset_base: Dict[int, int] = {}
        for node in self.tree.decision_nodes:
            p = node.actor
            self.iset_base[node.id] = len(self.isets)
            for h, lab in enumerate(self.seats[p].labels):
                self.isets.append(InfoSet(index=len(self.isets),
                                          id="P%d|%s|%s" % (p + 1, lab, node.history),
                                          player=p, hand=h, hand_label=lab, node=node.id,
                                          history=node.history, actions=node.actions))
        self.n_isets = len(self.isets)
        self.max_actions = max(len(nd.actions) for nd in self.tree.decision_nodes)
        self.legal = np.zeros((self.n_isets, self.max_actions), dtype=bool)
        for I in self.isets:
            self.legal[I.index, :len(I.actions)] = True
        self.iset_by_id = {I.id: I.index for I in self.isets}
        # per decision node: global infoset index of every deal
        self.node_iset = {nid: base + self.deals[:, self.tree.nodes[nid].actor]
                          for nid, base in self.iset_base.items()}
        # one representative deal per (seat, hand) -- own reach is identical across the deals
        # of an information set (perfect recall), so one deal suffices to read it
        self.first_deal = []
        for i in range(n):
            fd = np.full(len(self.seats[i].hands), -1, dtype=np.int64)
            for d in range(self.D - 1, -1, -1):
                fd[self.deals[d, i]] = d
            self.first_deal.append(fd)

        # terminal payoffs, exact and float
        self.payoff_x: Dict[int, list] = {}
        self.payoff_f: Dict[int, np.ndarray] = {}
        for t in self.tree.terminal_nodes:
            rows = []
            pot = sum(t.contrib)
            live = [i for i in range(n) if i not in t.folded]
            for d in range(self.D):
                if t.kind == "fold":
                    winners = live
                else:
                    best = max(self.deal_strength[d, i] for i in live)
                    winners = [i for i in live if self.deal_strength[d, i] == best]
                share = pot / len(winners)
                rows.append(tuple(-t.contrib[i] + (share if i in winners else 0) for i in range(n)))
            self.payoff_x[t.id] = rows
            self.payoff_f[t.id] = np.array([[float(v) for v in r] for r in rows])

    # ------------------------------------------------------------------ records
    def counts(self) -> dict:
        ties = int(sum(len(set(row)) < self.n for row in self.deal_strength.tolist()))
        return {"hands_per_seat": [len(s.hands) for s in self.seats], "legal_ordered_deals": self.D,
                "decision_nodes": self.tree_counts["decision_nodes"],
                "terminal_histories_per_deal": self.tree_counts["terminal_nodes"],
                "terminal_leaves": self.D * self.tree_counts["terminal_nodes"],
                "information_sets": self.n_isets,
                "binary_information_sets": int(sum(len(I.actions) == 2 for I in self.isets)),
                "deals_with_equal_strength_hands": ties}

    def record(self) -> dict:
        """Everything an experiment must state about its root."""
        return {"name": self.name, "board": " ".join(card_str(c) for c in self.board),
                "betting": self.rules.to_dict(), "seats": [s.spec for s in self.seats],
                "root_prior": {"kind": self.prior.kind, "note": self.prior.note},
                "payoff_convention": PAYOFF_CONVENTION,
                "scope": "conditional river continuation game; values are conditional on this root",
                "counts": self.counts(), "fingerprint": self.fingerprint()}

    def fingerprint(self) -> str:
        blob = json.dumps({"board": list(self.board), "betting": self.rules.to_dict(),
                           "hands": [s.labels for s in self.seats],
                           "weights": [[str(w) for w in s.weights] for s in self.seats],
                           "isets": [I.id for I in self.isets]}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def infoset_table(self) -> List[dict]:
        return [{"index": I.index, "id": I.id, "player": I.player + 1, "hand": I.hand_label,
                 "history": I.history, "actions": list(I.actions)} for I in self.isets]

    # ------------------------------------------------------------------ validation
    def validate(self) -> dict:
        n = self.n
        assert sum(self.prior_x) == 1, "prior does not sum to 1 exactly"
        assert all(p > 0 for p in self.prior_x)
        board = set(self.board)
        for d in range(self.D):
            cards = [c for i in range(n) for c in self.seats[i].hands[self.deals[d, i]]]
            assert len(set(cards)) == len(cards), "overlapping private cards in a deal"
            assert not (set(cards) & board), "a private card is on the board"
        for t in self.tree.terminal_nodes:
            for row in self.payoff_x[t.id]:
                assert sum(row) == 0, "chips not conserved at a leaf"
                for i in range(n):
                    assert row[i] >= -t.contrib[i], "a player lost more than they put in"
                    if i in t.folded:
                        assert row[i] == -t.contrib[i], "a folded player received chips"
        for I in self.isets:
            nd = self.tree.nodes[I.node]
            assert nd.actor == I.player and nd.actions == I.actions
        assert len(set(I.id for I in self.isets)) == self.n_isets, "duplicate infoset ids"
        return {"prior_sums_to_one_exactly": True, "card_compatibility": self.D,
                "chip_conservation_leaves": self.D * len(self.tree.terminal_nodes),
                "infoset_ids_unique": self.n_isets}
