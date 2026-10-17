import unittest
from fractions import Fraction as F

from _paths import ROOT  # noqa: F401  (sets sys.path)
from hinc.betting import BettingRules, build_tree, validate_tree


def rules(**kw):
    d = {"n_players": 3, "prior_contrib": [1, 1, 1], "stacks": [1, 1, 1], "min_bet": 1,
         "bet_sizes": ["allin"], "raise_sizes": [], "max_raises": 0, "allow_open_fold": False}
    d.update(kw)
    return BettingRules.from_dict(d)


class TestBetting(unittest.TestCase):
    def test_allin_tree_is_kuhn_shaped(self):
        t = build_tree(rules())
        c = validate_tree(t)
        self.assertEqual(c, {"decision_nodes": 12, "terminal_nodes": 13})
        hist = {n.history for n in t.terminal_nodes}
        self.assertEqual(len(hist), 13)
        for n in t.decision_nodes:
            self.assertIn(n.actions, (("K", "B:1"), ("F", "C")))
        # nobody can raise: every bet is all-in
        self.assertFalse(any(a.startswith("R:") for n in t.decision_nodes for a in n.actions))

    def test_min_bet_above_stack_means_no_bet(self):
        t = build_tree(rules(min_bet=2))
        self.assertEqual([n.history for n in t.terminal_nodes], ["K-K-K"])

    def test_two_player_tree(self):
        t = build_tree(rules(n_players=2, prior_contrib=[1, 1], stacks=[1, 1]))
        self.assertEqual(sorted(n.history for n in t.terminal_nodes),
                         sorted(["K-K", "K-B:1-F", "K-B:1-C", "B:1-F", "B:1-C"]))

    def test_multi_size_raise_tree_conserves_chips(self):
        r = rules(stacks=[6, 6, 6], bet_sizes=["1/2pot", "1pot", "allin"], raise_sizes=["1pot", "allin"],
                  max_raises=1)
        t = build_tree(r)
        validate_tree(t)
        root = t.nodes[0]
        self.assertEqual(root.actions, ("K", "B:3/2", "B:3", "B:6"))     # pot 3: 1.5, 3, all-in 6
        for n in t.terminal_nodes:
            for i in range(3):
                self.assertLessEqual(n.contrib[i] - 1, 6)
        # after a 1.5 bet a pot raise is to 1.5 + (3 + 1.5 + 1.5) = 7.5 -> capped at 6 (all-in)
        n = t.by_history()["B:3/2"]
        self.assertEqual(n.actions, ("F", "C", "R:6"))
        # max_raises=1: no re-raise anywhere
        for n in t.decision_nodes:
            if sum(1 for lab in n.labels if lab.startswith("R:")) >= 1:
                self.assertFalse(any(a.startswith("R:") for a in n.actions))

    def test_unequal_stacks_rejected(self):
        with self.assertRaises(ValueError):
            rules(stacks=[1, 2, 1])


if __name__ == "__main__":
    unittest.main()
