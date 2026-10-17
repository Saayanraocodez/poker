"""The exact Hold'em-Kuhn bridge: chance, information sets, actions, leaves, payoffs, utilities and
derivatives all correspond, in exact arithmetic."""
import random
import unittest
from fractions import Fraction as F

from _paths import config, load_kuhn3, load_repo_kuhn3p
from hinc import kuhn_bridge as KB
from hinc.evaluate import utilities
from hinc.game import RiverGame
from hinc.incidence import derivative_vector

KUHN3 = load_kuhn3()
REPO = load_repo_kuhn3p()


def known_profiles(k3):
    P = k3.FamilyParameters
    out = {
        "canonical_beta0_corner": k3.canonical_profile(F(0)),
        "canonical_beta1_8": k3.canonical_profile(F(1, 8)),
        "canonical_beta1_4_corner": k3.canonical_profile(F(1, 4)),
        "subA_unequal": k3.equilibrium_profile(P(F(1, 16), F(1, 8), F(0), F(1, 2), F(0), F(0), F(1))),
        "subB_interior": k3.equilibrium_profile(P(F(1, 8), F(1, 8), F(0), F(1, 2), F(1, 4), F(0), F(1, 3))),
        "subC_b23": k3.equilibrium_profile(P(F(1, 8), F(1, 16), F(1, 60), F(1, 2), F(1, 2), F(1, 10), F(2, 3))),
    }
    return out


def offpath_witness(k3):
    """MASTER_DATA's exact off-path witness: C corner with off-path values outside Table 2/3."""
    a, b, c = k3.equilibrium_profile(k3.FamilyParameters(F(1, 4), F(0), F(0), F(0), F(1, 2), F(1, 2), F(0)))
    b = dict(b); c = dict(c)
    b[(3, 2)] = F(23, 100); c[(3, 3)] = F(1, 4); c[(3, 4)] = F(9, 10)
    b[(1, 2)] = F(9, 100); b[(2, 2)] = F(1, 40); c[(2, 3)] = F(1, 25)
    return (dict(a), b, c)


def random_profile(seed):
    rng = random.Random(seed)
    return tuple({(j, k): F(rng.randint(0, 12), 12) for j in range(1, 5) for k in range(1, 5)} for _ in range(3))


@unittest.skipIf(KUHN3 is None, "kuhn3 reference not found")
class TestBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = RiverGame(config("bridge.json"))

    def test_counts(self):
        c = self.g.counts()
        self.assertEqual(c["legal_ordered_deals"], 24)
        self.assertEqual(c["terminal_histories_per_deal"], 13)
        self.assertEqual(c["terminal_leaves"], 312)
        self.assertEqual(c["information_sets"], 48)
        self.assertEqual(c["binary_information_sets"], 48)
        self.assertEqual(c["deals_with_equal_strength_hands"], 0)

    def test_chance_is_uniform_over_the_24_kuhn_deals(self):
        types = KB.card_types(self.g)
        seen = set()
        for d in range(self.g.D):
            self.assertEqual(self.g.prior_x[d], F(1, 24))
            seen.add(tuple(types[i][self.g.deals[d, i]] for i in range(3)))
        self.assertEqual(seen, set(KB.kuhn_deals()))

    def test_infosets_and_actions_biject_onto_kuhn_coordinates(self):
        types = KB.card_types(self.g)
        coords = set()
        for I in self.g.isets:
            p, j, k = KB.coordinate(self.g, I.index, types)
            coords.add((p, j, k))
            self.assertEqual(I.actions, ("K", "B:1") if k == 1 else ("F", "C"))
        self.assertEqual(len(coords), 48)
        self.assertEqual(coords, {(p, j, k) for p in range(3) for j in range(1, 5) for k in range(1, 5)})

    def test_every_terminal_payoff_matches_kuhn(self):
        types = KB.card_types(self.g)
        n = 0
        for t in self.g.tree.terminal_nodes:
            hist = KB.kuhn_letters(t.history)
            self.assertIn(hist, KB.KUHN_TERMINALS)
            for d in range(self.g.D):
                cards = tuple(types[i][self.g.deals[d, i]] for i in range(3))
                mine = self.g.payoff_x[t.id][d]
                self.assertEqual(tuple(mine), KB.kuhn_payoff(cards, hist))
                # and against kuhn3's own terminal rule
                contrib = [int(x) for x in t.contrib]
                self.assertEqual(tuple(mine), tuple(KUHN3._terminal_utility(cards, contrib, set(t.folded))))
                self.assertEqual(sum(mine), 0)
                n += 1
        self.assertEqual(n, 312)

    def test_expected_utilities_match_kuhn3_exactly(self):
        profs = dict(known_profiles(KUHN3))
        profs["offpath_witness"] = offpath_witness(KUHN3)
        for s in range(6):
            profs["random_rational_%d" % s] = random_profile(s)
        for name, kp in profs.items():
            u = utilities(self.g, KB.profile_from_kuhn(self.g, kp))
            self.assertEqual(tuple(u), tuple(KUHN3.expected_utilities(kp)), name)

    def test_all_48_derivative_vectors_match_kuhn3_exactly(self):
        types = KB.card_types(self.g)
        profs = known_profiles(KUHN3)
        profs["offpath_witness"] = offpath_witness(KUHN3)
        profs["random_rational_0"] = random_profile(0)
        for name, kp in profs.items():
            pr = KB.profile_from_kuhn(self.g, kp)
            for I in self.g.isets:
                p, j, k = KB.coordinate(self.g, I.index, types)
                mine = derivative_vector(self.g, pr, I.index, 1, 0)
                ref = KUHN3.coordinate_derivatives(kp, p, (j, k))
                self.assertEqual(tuple(mine), tuple(ref), (name, I.id))

    @unittest.skipIf(REPO is None, "repository engine not found")
    def test_float_utilities_match_repository_engine(self):
        import numpy as np
        for s in range(4):
            kp = random_profile(100 + s)
            vec = np.zeros(48)
            for p in range(3):
                for (j, k), x in kp[p].items():
                    vec[REPO.pidx(p, j, k)] = float(x)
            ref = REPO.utilities(vec)
            mine = utilities(self.g, KB.profile_from_kuhn(self.g, kp, exact=False))
            self.assertLess(max(abs(mine - np.array(ref))), 1e-14)


if __name__ == "__main__":
    unittest.main()
