import unittest
from fractions import Fraction as F

import numpy as np

from _paths import config, load_kuhn3
from hinc import kuhn_bridge as KB
from hinc.cfr import CFR
from hinc.game import RiverGame
from hinc.incidence import all_partials, derivative_vector, incidence_record, classify
from hinc.offpath import root_analysis, set_theta, upstream_D
from test_bridge import known_profiles

KUHN3 = load_kuhn3()


@unittest.skipIf(KUHN3 is None, "kuhn3 reference not found")
class TestIncidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = RiverGame(config("bridge.json"))
        cls.types = KB.card_types(cls.g)

    def iset(self, p, j, k):
        return next(I.index for I in self.g.isets if KB.coordinate(self.g, I.index, self.types) == (p, j, k))

    def test_direct_equals_batch(self):
        pr = KB.profile_from_kuhn(self.g, known_profiles(KUHN3)["subB_interior"])
        P = all_partials(self.g, pr)
        for I in self.g.isets:
            d = derivative_vector(self.g, pr, I.index, 1, 0)
            self.assertEqual(tuple(d), tuple(P[I.index, 1] - P[I.index, 0]))
            self.assertEqual(sum(d), 0)                       # constant sum, exactly

    def test_known_exact_shares(self):
        # PAPER_KIT R5: rho_{P2->P1}(+e_b31) = 3/5 on the whole family
        for name, kp in known_profiles(KUHN3).items():
            pr = KB.profile_from_kuhn(self.g, kp)
            rec = incidence_record(self.g, pr, self.iset(1, 3, 1), 1, 0, max_r=0)
            self.assertEqual(rec["class"], "costly", name)
            self.assertAlmostEqual(rec["rho"]["P1"], 0.6, places=14)
            self.assertAlmostEqual(rec["rho_sum"], 1.0, places=14)
        # P2's +e_b11 at a beta=0 point: (+1/12, 0, -1/12), a costless transfer
        pr = KB.profile_from_kuhn(self.g, KUHN3.canonical_profile(F(0)))
        d = derivative_vector(self.g, pr, self.iset(1, 1, 1), 1, 0)
        self.assertEqual(tuple(d), (F(1, 12), F(0), F(-1, 12)))
        self.assertEqual(classify(d, 1, 0, 0), "costless_transfer")

    def test_offpath_pole_reproduced_exactly(self):
        """Kuhn's c33 window: the root of D_P1(a11) in c33 is lo = 1/2 - b32 (PAPER_KIT R7)."""
        kp = KUHN3.equilibrium_profile(KUHN3.FamilyParameters(F(3, 20), F(3, 20), F(0), F(2, 5), F(1, 4), F(1, 5), F(0)))
        pr = KB.profile_from_kuhn(self.g, kp)
        ra = root_analysis(self.g, pr, [self.iset(2, 3, 3)], 1, [self.iset(0, 1, 1)], 1, 0)
        self.assertEqual(ra["theta_star_exact"], str(F(1, 2) - F(2, 5)))
        # numerator nonzero, slope D' = -4 kappa for a11
        self.assertNotEqual(ra["D_at_theta_star"][2], 0)
        self.assertAlmostEqual(ra["cross_effect"][0], -4 / 24, places=14)


class TestTwoPlayerControl(unittest.TestCase):
    def test_share_is_one(self):
        g = RiverGame(config("control_2p.json"))
        c = CFR(g, "cfr+", seed=1)
        c.run(300)
        avg, _ = c.average()
        for I in g.isets:
            d = derivative_vector(g, avg, I.index, 1, 0)
            self.assertLess(abs(d[0] + d[1]), 1e-12)
            if abs(d[I.player]) > 1e-9:
                self.assertAlmostEqual(-d[1 - I.player] / d[I.player], 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
