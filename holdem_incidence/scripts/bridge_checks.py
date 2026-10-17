"""Exact reproduction of the Hold'em-Kuhn embedding, and the first exact facts about the 24-hand
expansion.  Everything here is rational arithmetic.  Output: results/bridge/bridge_checks.json.

usage:  python scripts/bridge_checks.py
"""
import json
import os
import sys
import time
from fractions import Fraction as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
from _paths import load_kuhn3, config                                    # noqa: E402
from hinc import kuhn_bridge as KB                                      # noqa: E402
from hinc.bestresponse import residuals, best_response, br_profile      # noqa: E402
from hinc.evaluate import utilities, infoset_reach                      # noqa: E402
from hinc.game import RiverGame                                         # noqa: E402
from hinc.incidence import derivative_vector                            # noqa: E402
from hinc.offpath import root_analysis, set_theta                       # noqa: E402
from test_bridge import known_profiles, offpath_witness, random_profile  # noqa: E402
from test_bestresponse import coordinated_case                          # noqa: E402

OUT = os.path.join(ROOT, "results", "bridge")
os.makedirs(OUT, exist_ok=True)
S = lambda x: str(x)


def main():
    t0 = time.time()
    k3 = load_kuhn3()
    g = RiverGame(config("bridge.json"))
    types = KB.card_types(g)
    rec = {"scope": ("EXACT correspondence between two specified continuation games: the all-in river game "
                     "(board 2c 4d 6h 8s Tc; JsJh QsQh KsKh AsAh; pot 3, stacks 1, min bet 1, no open fold) and "
                     "three-player Kuhn poker.  It transfers every Kuhn fact about THIS river game, off-path "
                     "strategies and deviation derivatives included.  It does NOT show that these ranges arise at "
                     "an equilibrium of unrestricted Hold'em, nor that the continuation equilibrium extends to one "
                     "from the start of a hand."),
           "game": g.record(), "validate": g.validate()}
    c = g.counts()
    assert (c["legal_ordered_deals"], c["terminal_histories_per_deal"], c["terminal_leaves"], c["information_sets"]) == (24, 13, 312, 48)
    rec["expected_counts_match"] = True
    rec["infoset_map"] = {I.id: KB.kuhn_name(*KB.coordinate(g, I.index, types)) for I in g.isets}
    # every leaf payoff against Kuhn
    n_ok = 0
    for t in g.tree.terminal_nodes:
        for d in range(g.D):
            cards = tuple(types[i][g.deals[d, i]] for i in range(3))
            assert tuple(g.payoff_x[t.id][d]) == KB.kuhn_payoff(cards, KB.kuhn_letters(t.history))
            n_ok += 1
    rec["terminal_payoffs_equal_to_kuhn"] = "%d / 312" % n_ok

    profs = dict(known_profiles(k3))
    profs["offpath_witness_MASTER_DATA"] = offpath_witness(k3)
    for s in range(3):
        profs["random_rational_%d" % s] = random_profile(s)
    prow = []
    for name, kp in profs.items():
        pr = KB.profile_from_kuhn(g, kp)
        u = utilities(g, pr)
        uk = k3.expected_utilities(kp)
        res = residuals(g, pr)
        nder = 0
        for I in g.isets:
            p, j, k = KB.coordinate(g, I.index, types)
            assert tuple(derivative_vector(g, pr, I.index, 1, 0)) == tuple(k3.coordinate_derivatives(kp, p, (j, k)))
            nder += 1
        sel = {}
        for cname in ("a11", "a41", "b11", "b31", "c11", "c33"):
            I = next(I for I in g.isets if KB.kuhn_name(*KB.coordinate(g, I.index, types)) == cname)
            sel[cname] = [S(x) for x in derivative_vector(g, pr, I.index, 1, 0)]
        prow.append({"profile": name, "utilities": [S(x) for x in u], "kuhn3_utilities": [S(x) for x in uk],
                     "utilities_equal": tuple(u) == tuple(uk), "residuals_exact": [S(x) for x in res["r"]],
                     "nashconv_exact": S(res["nashconv"]), "derivative_vectors_equal_to_kuhn3": "%d / 48" % nder,
                     "selected_derivatives_U(x=1)-U(x=0)": sel})
    rec["profiles"] = prow

    # known Kuhn facts reproduced through the river game
    kp = offpath_witness(k3)
    b = dict(kp[1]); b[(1, 2)] = F(0)
    r = residuals(g, KB.profile_from_kuhn(g, (kp[0], b, kp[2])))["r"]
    rec["witness_projection_b12_to_0"] = {"r": [S(x) for x in r], "expected_r1": "1/300", "ok": r[0] == F(1, 300)}
    # coordinated deviation
    pr = KB.profile_from_kuhn(g, coordinated_case())
    _, ch, _ = best_response(g, pr, 0)
    pr = br_profile(g, pr, 0, {i: a for i, a in ch.items() if types[0][g.isets[i].hand] != 4})
    kp1 = [{(j, k): F(0) for j in range(1, 5) for k in range(1, 5)}, coordinated_case()[1], coordinated_case()[2]]
    for I in g.isets:
        if I.player == 0:
            _, j, k = KB.coordinate(g, I.index, types)
            kp1[0][(j, k)] = pr[I.index, 1]
    rec["coordinated_deviation_case"] = {
        "description": "P1 bets A and would fold after checking; P2 always bets after K; P3 never bets, folds to bets",
        "kuhn3_coordinate_gradient_search_profitable": k3.best_feasible_coordinate_direction(tuple(kp1), 0).profitable,
        "full_best_response_r1": S(residuals(g, pr)["r"][0]), "expected": "1/4 (6 A deals x 1 chip / 24)"}
    # Kuhn's off-path pole: c33's root for P1's a11 deviation is lo = 1/2 - b32
    kpB = k3.equilibrium_profile(k3.FamilyParameters(F(3, 20), F(3, 20), F(0), F(2, 5), F(1, 4), F(1, 5), F(0)))
    prB = KB.profile_from_kuhn(g, kpB)
    i_c33 = next(I.index for I in g.isets if KB.kuhn_name(*KB.coordinate(g, I.index, types)) == "c33")
    i_a11 = next(I.index for I in g.isets if KB.kuhn_name(*KB.coordinate(g, I.index, types)) == "a11")
    ra = root_analysis(g, prB, [i_c33], 1, [i_a11], 1, 0)
    window = []
    for th in (F(0), F(1, 20), F(1, 10), F(3, 20), F(1, 5), F(29, 80), F(3, 8), F(1, 2), F(1)):
        p2 = set_theta(g, prB, [i_c33], 1, th)
        rr = residuals(g, p2)["r"]
        window.append({"c33": S(th), "r": [S(x) for x in rr], "reach_c33": S(infoset_reach(g, p2)["total"][i_c33])})
    rec["kuhn_offpath_pole"] = {"profile": "sub-family B, b11=b21=3/20, b32=2/5, c11=1/4, c33=1/5", "root_analysis": ra,
                                "expected_root": "1/10 = 1/2 - b32", "window_sweep_exact": window,
                                "expected_window": "[1/10, 29/80] (Table 3: [1/2-b32, 1/2-b32+3/4(b11+b21)+beta/4])"}

    # ---- the 24-hand expansion: counts and the LIFTED Kuhn profiles, exactly
    g24 = RiverGame(config("expanded24.json"))
    c24 = g24.counts()
    assert (c24["legal_ordered_deals"], c24["terminal_leaves"], c24["deals_with_equal_strength_hands"]) == (6480, 84240, 1296)
    rec["expanded24"] = {"game": g24.record(), "validate": g24.validate(), "expected_counts_match": True}
    lift = []
    for name, kp in known_profiles(k3).items():
        pr = KB.profile_from_kuhn(g24, kp)
        res = residuals(g24, pr)
        lift.append({"profile": name, "utilities": [S(x) for x in res["utilities"]],
                     "r_exact": [S(x) for x in res["r"]], "r_float": [float(x) for x in res["r"]],
                     "nashconv_exact": S(res["nashconv"]), "nashconv_float": float(res["nashconv"])})
    rec["expanded24"]["lifted_kuhn_family"] = {
        "meaning": "every combo of a rank plays its Kuhn type's SGS-family strategy; exact residuals in the 24-hand game",
        "rows": lift}
    rec["wall_s"] = round(time.time() - t0, 1)
    json.dump(rec, open(os.path.join(OUT, "bridge_checks.json"), "w"), indent=1)
    print(json.dumps({k: rec[k] for k in ("terminal_payoffs_equal_to_kuhn", "witness_projection_b12_to_0",
                                          "coordinated_deviation_case")}, indent=1))
    print("kuhn pole:", ra["theta_star_exact"], [(w["c33"], w["r"][0]) for w in window])
    for row in lift:
        print("lifted", row["profile"], "r =", row["r_exact"], "~", ["%.3e" % x for x in row["r_float"]])


if __name__ == "__main__":
    main()
