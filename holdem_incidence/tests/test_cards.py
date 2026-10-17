import os
import random
import unittest
from collections import Counter
from itertools import combinations

from _paths import load_audit
from hinc.cards import eval7, parse_cards, expand_class, card_str, hand_str

AUDIT = load_audit()


class TestEvaluator(unittest.TestCase):
    def test_handmade_cases(self):
        r = lambda s: eval7(parse_cards(s))
        self.assertEqual(r("Ah2c3d4s5h9c9d")[0:2], (4, 5))                  # wheel straight
        self.assertEqual(r("Ah2h3h4h5h9c9d"), (8, 5))                        # steel wheel
        self.assertGreater(r("2h4h6h8hTh As Ks"), r("9c8d7h6s5c 2d 2h"))    # flush > straight
        self.assertEqual(r("AsAhAdKcKd2c3d")[0:3], (6, 14, 13))              # full house
        self.assertEqual(r("AsAhAdKcKdKh2c")[0:3], (6, 14, 13))              # two trips -> FH
        self.assertEqual(r("AsAhAdAc2d3c4d")[0:3], (7, 14, 4))               # quads, best kicker
        self.assertEqual(r("AsAhKdKcQdQc2d")[0:4], (2, 14, 13, 12))          # 3 pairs -> kicker Q
        # board plays: both players have the board's straight -> exact tie
        board = parse_cards("5c6d7h8s9c")
        self.assertEqual(eval7(board + parse_cards("2d3h")), eval7(board + parse_cards("2s3c")))

    def test_five_card_category_counts_exhaustive(self):
        if os.environ.get("HINC_FAST"):
            self.skipTest("HINC_FAST set")
        counts = Counter(eval7(h)[0] for h in combinations(range(52), 5))
        expected = {8: 40, 7: 624, 6: 3744, 5: 5108, 4: 10200, 3: 54912, 2: 123552, 1: 1098240, 0: 1302540}
        self.assertEqual(dict(counts), expected)

    @unittest.skipIf(AUDIT is None, "audit oracle not found")
    def test_against_independent_best_of_21(self):
        rng = random.Random(20261016)
        for _ in range(20000):
            cards = rng.sample(range(52), 7)
            self.assertEqual(eval7(cards), AUDIT.rank7(tuple(card_str(c) for c in cards)))

    def test_hand_classes(self):
        board = parse_cards("2c4d6h8sTc")
        self.assertEqual(len(expand_class("JJ")), 6)
        self.assertEqual(len(expand_class("AKs")), 4)
        self.assertEqual(len(expand_class("AKo")), 12)
        self.assertEqual(len(expand_class("AK")), 16)
        self.assertEqual(len(expand_class("TT", excluded=board)), 3)        # Tc on the board
        self.assertEqual([hand_str(h) for h in expand_class("AsAh")], ["AsAh"])


if __name__ == "__main__":
    unittest.main()
