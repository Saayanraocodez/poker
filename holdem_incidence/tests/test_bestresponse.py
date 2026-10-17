"""The full best response against brute-force enumeration of every pure strategy, known Kuhn
profiles, and a case where only a COORDINATED change of an earlier and a later decision pays."""
import unittest
from fractions import Fraction as F

from _paths import config, load_kuhn3
from hinc import kuhn_bridge as KB
from hinc.bestresponse import best_response, brute_force_best_response, residuals, br_profile
from hinc.evaluate import utilities
from hinc.game import RiverGame
from test_bridge import known_profiles, offpath_witness, random_profile

KUHN3 = load_kuhn3()


def coordinated_case():
    """P1 bets the A, and after a check would fold everything.  P2 always bets after a check, P3
    folds to every bet and never bets.  With the A, betting wins +2; checking and FOLDING loses 1;
    checking and CALLING wins +3.  So no single coordinate helps P1 (the call is own-unreached
    while P1 bets), but the joint change 'check, then call' gains 1 per A deal."""
    z = {(j, k): F(0) for j in range(1, 5) for k in range(1, 5)}
    a = dict(z)
    a[(4, 1)] = F(1)                                # bet the A; a42 = a43 = a44 = 0
    b = dict(z)
    for j in range(1, 5):
        b[(j, 1)] = F(1)                            # P2 always bets after K
    c = dict(z)                                     # P3 never bets, folds to every bet
    return (a, b, c)


@unittest.skipIf(KUHN3 is None, "kuhn3 reference not found")
class TestBestResponse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = RiverGame(config("bridge.json"))

    def _check(self, kp, players=(0, 1, 2), exact=True):
        pr = KB.profile_from_kuhn(self.g, kp, exact=exact)
        u = utilities(self.g, pr)
        for p in players:
            v, choice, _ = best_response(self.g, pr, p)
            bf, _ = brute_force_best_response(self.g, pr, p)
            if exact:
                self.assertEqual(v, bf)
            else:
                self.assertLess(abs(v - bf), 1e-13)
            # the returned pure strategy really attains v
            vv = utilities(self.g, br_profile(self.g, pr, p, choice))[p]
            self.assertLess(abs(vv - v), 1e-13) if not exact else self.assertEqual(vv, v)
            self.assertGreaterEqual(v, u[p] - (0 if exact else 1e-13))

    @unittest.skipIf(__import__("os").environ.get("HINC_FAST"), "HINC_FAST set")
    def test_brute_force_random_profiles(self):
        for s in (0, 1):                       # float enumeration of all 2^16 pure strategies
            self._check(random_profile(s), exact=False)

    @unittest.skipIf(__import__("os").environ.get("HINC_FAST"), "HINC_FAST set")
    def test_brute_force_family_point(self):
        self._check(known_profiles(KUHN3)["subC_b23"], players=(0,))

    def test_family_points_have_zero_residual_exactly(self):
        for name, kp in known_profiles(KUHN3).items():
            r = residuals(self.g, KB.profile_from_kuhn(self.g, kp))["r"]
            self.assertEqual(r, [0, 0, 0], name)

    def test_offpath_witness_and_its_table2_projection(self):
        kp = offpath_witness(KUHN3)
        self.assertEqual(residuals(self.g, KB.profile_from_kuhn(self.g, kp))["r"], [0, 0, 0])
        b = dict(kp[1]); b[(1, 2)] = F(0)
        r = residuals(self.g, KB.profile_from_kuhn(self.g, (kp[0], b, kp[2])))["r"]
        self.assertEqual(r, [F(1, 300), 0, 0])     # MASTER_DATA: P1 gains exactly 1/300

    def test_coordinated_change_is_found(self):
        kp = coordinated_case()
        pr = KB.profile_from_kuhn(self.g, kp)
        # make P1's other cards locally optimal so that the only gain left is the coordinated one
        v, choice, _ = best_response(self.g, pr, 0)
        types = KB.card_types(self.g)
        keep_A = {i: a for i, a in choice.items() if types[0][self.g.isets[i].hand] != 4}
        pr = br_profile(self.g, pr, 0, keep_A)
        kp1 = ({(j, k): F(0) for j in range(1, 5) for k in range(1, 5)}, kp[1], kp[2])
        for I in self.g.isets:
            if I.player == 0:
                p, j, k = KB.coordinate(self.g, I.index, types)
                kp1[0][(j, k)] = pr[I.index, 1]
        # 1. the coordinate-gradient search (kuhn3) sees nothing profitable
        self.assertFalse(KUHN3.best_feasible_coordinate_direction(kp1, 0).profitable)
        # 2. the full best response finds the coordinated change, worth 1 chip on the 6 A deals
        r = residuals(self.g, pr)["r"][0]
        self.assertEqual(r, F(6, 24))
        bf, bfc = brute_force_best_response(self.g, pr, 0)
        self.assertEqual(bf - utilities(self.g, pr)[0], F(6, 24))
        v2, choice2, _ = best_response(self.g, pr, 0)
        A_open = next(I.index for I in self.g.isets if I.player == 0 and types[0][I.hand] == 4 and I.history == "")
        A_call = next(I.index for I in self.g.isets if I.player == 0 and types[0][I.hand] == 4 and I.history == "K-B:1-F")
        self.assertEqual((choice2[A_open], choice2[A_call]), (0, 1))     # check, then call

    def test_float_and_exact_agree(self):
        kp = random_profile(7)
        rx = residuals(self.g, KB.profile_from_kuhn(self.g, kp))["r"]
        rf = residuals(self.g, KB.profile_from_kuhn(self.g, kp, exact=False))["r"]
        for a, b in zip(rx, rf):
            self.assertLess(abs(float(a) - b), 1e-14)


if __name__ == "__main__":
    unittest.main()
