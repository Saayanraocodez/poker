import unittest
from fractions import Fraction as F

import numpy as np

from _paths import config
from hinc.cfr import CFR
from hinc.game import RiverGame
from hinc.ranges import build_seat_range, product_prior
from hinc.cards import parse_cards
from hinc.strategy import validate_profile, save_profile, load_profile


class TestCFR(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = RiverGame(config("bridge.json"))

    def test_resume_is_bit_identical(self):
        import tempfile, os
        a = CFR(self.g, "cfr+", seed=3); a.run(80)
        b = CFR(self.g, "cfr+", seed=3); b.run(40)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "ck")
            b.save(path)
            c = CFR.load(self.g, path)
        c.run(80)
        self.assertTrue(np.array_equal(a.R, c.R) and np.array_equal(a.S, c.S) and np.array_equal(a.W, c.W))

    def test_seeds_reproducible_and_distinct(self):
        x = CFR(self.g, "dcfr", seed=5); x.run(30)
        y = CFR(self.g, "dcfr", seed=5); y.run(30)
        z = CFR(self.g, "dcfr", seed=6); z.run(30)
        self.assertTrue(np.array_equal(x.average()[0], y.average()[0]))
        self.assertFalse(np.array_equal(x.average()[0], z.average()[0]))

    def test_profiles_valid_and_roundtrip(self):
        import tempfile, os
        c = CFR(self.g, "cfr", seed=1); c.run(50)
        avg, zero = c.average()
        validate_profile(self.g, avg)
        validate_profile(self.g, c.current())
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "p.json")
            save_profile(path, self.g, avg)
            back = load_profile(path, self.g)
        self.assertTrue(np.allclose(back, avg, atol=0, rtol=0))


class TestRanges(unittest.TestCase):
    def test_product_prior_keeps_blockers(self):
        board = parse_cards("2c4d6h8sTc")
        seats = [build_seat_range(["JJ", "QQ", "KK", "AA"], board) for _ in range(3)]
        pr = product_prior(seats)
        self.assertEqual(len(pr.deals), 6480)
        self.assertEqual(sum(pr.probs), 1)
        # P(P2 holds JJ | P1 holds JJ): blockers make it far below the 1/4 of independent ranks
        lab = seats[0].labels
        is_jj = [l[0] == "J" for l in lab]
        num = sum(p for d, p in zip(pr.deals, pr.probs) if is_jj[d[0]] and is_jj[d[1]])
        den = sum(p for d, p in zip(pr.deals, pr.probs) if is_jj[d[0]])
        self.assertLess(num / den, F(1, 10))

    def test_weighted_prior_is_product_conditioned(self):
        board = parse_cards("2c4d6h8sTc")
        s1 = build_seat_range([["JJ", "1"], ["AA", "3"]], board)
        s2 = build_seat_range(["QQ", "AA"], board)
        s3 = build_seat_range(["KK"], board)
        pr = product_prior([s1, s2, s3])
        self.assertEqual(sum(pr.probs), 1)
        w = {d: p for d, p in zip(pr.deals, pr.probs)}
        # brute force the same distribution
        raw = {}
        for i, h1 in enumerate(s1.hands):
            for j, h2 in enumerate(s2.hands):
                for k, h3 in enumerate(s3.hands):
                    cards = h1 + h2 + h3
                    if len(set(cards)) == 6:
                        raw[(i, j, k)] = s1.weights[i] * s2.weights[j] * s3.weights[k]
        z = sum(raw.values())
        self.assertEqual(w, {d: v / z for d, v in raw.items()})


if __name__ == "__main__":
    unittest.main()
