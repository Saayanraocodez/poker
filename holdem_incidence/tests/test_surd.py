"""Q(sqrt(d)) arithmetic (hinc/surd.py) and its use by the exact evaluation / best-response code."""
import os
import random
import unittest
from fractions import Fraction as F
from math import sqrt

import numpy as np

from _paths import config
from hinc.bestresponse import residuals
from hinc.evaluate import utilities
from hinc.game import RiverGame
from hinc.surd import Surd, parse


def rand_profile(g, rng, den=97):
    p = np.full((g.n_isets, g.max_actions), F(0), dtype=object)
    for I in g.isets:
        x = F(rng.randrange(den + 1), den)
        p[I.index, 0], p[I.index, 1] = 1 - x, x
    return p


class TestSurdField(unittest.TestCase):
    def test_ops_match_float(self):
        rng = random.Random(1)
        for _ in range(300):
            d = rng.choice([2, 3, 5, 7, 4937])
            x = Surd(F(rng.randrange(-50, 50), rng.randrange(1, 30)), F(rng.randrange(-50, 50), rng.randrange(1, 30)), d)
            y = Surd(F(rng.randrange(-50, 50), rng.randrange(1, 30)), F(rng.randrange(1, 50), rng.randrange(1, 30)), d)
            q = F(rng.randrange(-9, 9), rng.randrange(1, 9))
            for got, want in ((x + y, float(x) + float(y)), (x - y, float(x) - float(y)), (x * y, float(x) * float(y)),
                              (x / y, float(x) / float(y)), (q - x, float(q) - float(x)), (q / y, float(q) / float(y)),
                              (x * q + 1, float(x) * float(q) + 1)):
                self.assertAlmostEqual(float(got), want, delta=1e-9 * max(1.0, abs(want)))
            self.assertEqual(x < y, float(x) < float(y))
            self.assertEqual((x * y) / y, x)
            self.assertEqual(parse(str(x)), x)

    def test_sign_is_exact_where_float_cannot_tell(self):
        # a + b sqrt(2) with a/b the convergents of -sqrt(2): |value| < 1e-17, so the double is unreliable
        p, q = 1, 1
        for _ in range(25):
            p, q = p + 2 * q, p + q                 # p/q -> sqrt(2), alternating sides
            s = Surd(-p, q, 2)
            want = 1 if 2 * q * q > p * p else -1   # sign of q sqrt(2) - p, decided in integers
            self.assertEqual(s.sign(), want)
            self.assertEqual(s > 0, want > 0)

    def test_mixed_with_fraction(self):
        s = Surd(F(1, 3), F(1, 7), 5)
        self.assertEqual(F(1, 2) + s, s + F(1, 2))
        self.assertEqual(F(1, 2) * s, s * F(1, 2))
        self.assertTrue(F(1, 3) < s)
        self.assertEqual(max([F(1, 3), s, F(0)]), s)
        self.assertEqual(Surd(F(2, 3), 0, 5), F(2, 3))


class TestSurdEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = RiverGame(config("bridge.json"))

    def test_rational_profile_cast_to_surds_is_identical(self):
        rng = random.Random(2)
        for _ in range(3):
            p = rand_profile(self.g, rng)
            s = np.empty(p.shape, dtype=object)
            for i in range(p.shape[0]):
                for a in range(p.shape[1]):
                    s[i, a] = Surd(p[i, a], 0, 5)
            ru, rs = residuals(self.g, p), residuals(self.g, s)
            self.assertEqual(list(utilities(self.g, p)), list(utilities(self.g, s)))
            self.assertEqual(ru["r"], rs["r"])

    def test_surd_profile_matches_float(self):
        rng = random.Random(3)
        p = rand_profile(self.g, rng)
        s = p.copy()
        for I in self.g.isets[::3]:                 # every third row becomes a genuine surd in (0, 1)
            x = Surd(F(1, 2), F(rng.randrange(1, 20), 100), 7) if rng.random() < 0.5 else Surd(F(1, 3), F(-1, 30), 7)
            s[I.index, 0], s[I.index, 1] = 1 - x, x
        f = np.array([[float(v) for v in row] for row in s])
        rs, rf = residuals(self.g, s), residuals(self.g, f)
        for a, b in zip(rs["r"], rf["r"]):
            self.assertAlmostEqual(float(a), b, delta=1e-12)
        for a, b in zip(utilities(self.g, s), utilities(self.g, f)):
            self.assertAlmostEqual(float(a), b, delta=1e-12)
        self.assertEqual(sum(utilities(self.g, s)), 0)          # zero-sum, exactly, in Q(sqrt 7)


@unittest.skipIf(os.environ.get("HINC_FAST"), "HINC_FAST set")
class TestSurdExpanded(unittest.TestCase):
    def test_24_hand_game(self):
        g = RiverGame(config("expanded24.json"))
        rng = random.Random(4)
        s = rand_profile(g, rng, den=13)
        for I in g.isets[::5]:
            x = Surd(F(1, 2), F(1, 9), 3)
            s[I.index, 0], s[I.index, 1] = 1 - x, x
        f = np.array([[float(v) for v in row] for row in s])
        rs, rf = residuals(g, s), residuals(g, f)
        for a, b in zip(rs["r"], rf["r"]):
            self.assertAlmostEqual(float(a), b, delta=1e-11)
        self.assertEqual(sum(rs["utilities"]), 0)


if __name__ == "__main__":
    unittest.main()
