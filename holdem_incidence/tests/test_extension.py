"""The research calculations run unchanged on a multi-action tree (deeper stacks, three opening
sizes, one raise), and multi-action mass-transfer derivatives are exact."""
import unittest
from fractions import Fraction as F

import numpy as np

from _paths import config
from hinc.bestresponse import residuals, best_response, brute_force_by_hand
from hinc.cfr import CFR
from hinc.evaluate import utilities
from hinc.game import RiverGame
from hinc.incidence import derivative_vector
from hinc.strategy import uniform, validate_profile


def small_multi():
    """A tiny multi-action game (3 hands per seat, stacks 2, bet 1 bb or all-in, one raise to
    all-in) small enough to brute-force a player's pure strategies."""
    cfg = config("extension_stack6_sizes.json")
    cfg = dict(cfg, range=["QsQh", "KsKh", "AsAh"],
               betting=dict(cfg["betting"], stacks=[2, 2, 2], bet_sizes=["1bb", "allin"], raise_sizes=["allin"]))
    return RiverGame(cfg)


class TestExtension(unittest.TestCase):
    def test_tree_and_game_validate(self):
        g = RiverGame(config("extension_stack6_sizes.json"))
        g.validate()
        self.assertGreater(g.max_actions, 2)
        sizes = {len(I.actions) for I in g.isets}
        self.assertTrue({2, 3}.issubset(sizes) or max(sizes) >= 3)

    def test_mass_transfer_derivative_is_exact(self):
        g = small_multi()
        p = uniform(g, exact=True)
        for I in g.isets:
            k = len(I.actions)
            if k < 3:
                continue
            a, b = k - 1, 0
            D = derivative_vector(g, p, I.index, a, b)
            delta = F(1, 70)                          # move mass delta from action b to action a
            q = p.copy()
            q[I.index, a] += delta
            q[I.index, b] -= delta
            # U is affine in the row, so the change is EXACTLY delta * D (no finite-difference error)
            self.assertEqual(tuple(utilities(g, q) - utilities(g, p)), tuple(delta * D))
            self.assertEqual(sum(D), 0)
            break

    def test_cfr_and_best_response_run(self):
        g = RiverGame(config("extension_stack6_sizes.json"))
        c = CFR(g, "dcfr", seed=1)
        c.run(30)
        avg, _ = c.average()
        validate_profile(g, avg)
        r = residuals(g, avg)
        self.assertTrue(all(x >= -1e-12 for x in r["r"]))

    @unittest.skipIf(__import__('os').environ.get('HINC_FAST'), 'HINC_FAST set')
    def test_best_response_brute_force_multi_action(self):
        g = small_multi()
        rng = np.random.default_rng(0)
        p = uniform(g)
        for I in g.isets:
            k = len(I.actions)
            w = rng.dirichlet(np.ones(k))
            p[I.index, :k] = w
        for player in (0, 2):
            v, _, _ = best_response(g, p, player)
            bf = brute_force_by_hand(g, p, player)
            self.assertLess(abs(v - bf), 1e-12)


if __name__ == "__main__":
    unittest.main()
