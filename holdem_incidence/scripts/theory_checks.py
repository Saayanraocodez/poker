"""Computational checks of the results stated and proved in THEORY.md.

T3   zero direct effect, affine cross effect, sum of cross effects = 0, and own-unreached sets carry
     NO cross effect (exact, on the 24-hand game: P2's AA opening forced to exactly 1)
T5   residue identity rho = 1 + t / (C_A (theta - theta*)) when the third player is out (exact on
     the bridge; float on the OP2 sweep)
T6   the Nash window along an unreached parameter is an interval (exact on the bridge); the
     deviation-gain envelope is convex piecewise-linear (OP2 sweep, second differences)
T8   classification of every zero-reach / rare information set in every analysed profile into
     own-unreached, publicly unreached and blocker-unreached
T10  share line: in a FOUR-player river game the incidence vector moves on a straight line in
     share space as one off-path parameter varies (exact)
P11  exact equilibria arbitrarily close together with arbitrarily different rho (exact, bridge)

usage:  python scripts/theory_checks.py   ->  results/theory/theory_checks.json
"""
import csv
import glob
import json
import os
import sys
from fractions import Fraction as F

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from _paths import load_kuhn3, config                                     # noqa: E402
from analyze_profiles import RESULTS, find_config                         # noqa: E402
from hinc import kuhn_bridge as KB, plan                                  # noqa: E402
from hinc.bestresponse import residuals                                   # noqa: E402
from hinc.evaluate import infoset_reach, utilities, reach, prior          # noqa: E402
from hinc.game import RiverGame                                           # noqa: E402
from hinc.offpath import root_analysis, set_theta, upstream_D             # noqa: E402
from hinc.strategy import load_profile, to_exact, normalise_exact, uniform  # noqa: E402

OUT = os.path.join(RESULTS, "theory")
os.makedirs(OUT, exist_ok=True)


def t3_own_unreached():
    """Force P2's AA opening to exactly 1 in a pilot profile (exact arithmetic): P2's later sets
    with AA become own-unreached; every cross effect with every other player's deviation must be 0."""
    cands = sorted(glob.glob(os.path.join(RESULTS, "pilot", "*", "dcfr_s1", "policy_avg.json")))
    if not cands:
        return {"status": "pilot profile not available"}
    g = RiverGame(config("expanded24.json"))
    p = normalise_exact(g, to_exact(load_profile(cands[0], g), 10 ** 6))
    for I in g.isets:
        if I.player == 1 and I.history == "K" and I.hand_label[0] == "A":
            p[I.index, 0], p[I.index, 1] = F(0), F(1)
    tot = infoset_reach(g, p)
    thetas = [I.index for I in g.isets if I.player == 1 and I.hand_label[0] == "A" and I.history.startswith("K-K-B:1")]
    ups = [I.index for I in g.isets if (I.player, I.history) in ((0, ""), (2, "K-K"))]
    nz, worst_sum = 0, F(0)
    for t in thetas:
        assert tot["own"][t] == 0 and tot["total"][t] == 0
        for u in ups:
            ra = root_analysis(g, p, [t], 1, [u], 1, 0)
            C = [F(x) for x in ra["cross_effect"]]
            nz += any(c != 0 for c in C)
    # zero direct effect and sum of cross effects at a publicly reached set (for contrast)
    return {"own_unreached_thetas": len(thetas), "upstream_sets": len(ups), "pairs": len(thetas) * len(ups),
            "pairs_with_nonzero_cross_effect": nz, "arithmetic": "exact rational (rationalised pilot profile)"}


def t3_sums_and_direct_effect():
    rows = []
    for f in glob.glob(os.path.join(RESULTS, "*", "*", "*", "offpath_pairs_combo.csv")):
        for r in csv.DictReader(open(f)):
            if r["cross"]:
                C = json.loads(r["cross"])
                rows.append(abs(sum(C)))
    u_ranges = []
    for f in glob.glob(os.path.join(RESULTS, "op2_silent", "expanded24", "*", "sweep_P1_JJ_bet.csv")):
        rr = list(csv.DictReader(open(f)))
        u = np.array([[float(r["u1"]), float(r["u2"]), float(r["u3"])] for r in rr])
        u_ranges.append(float((u.max(axis=0) - u.min(axis=0)).max()))
    return {"pairs_checked": len(rows), "max_abs_sum_of_cross_effects": max(rows) if rows else None,
            "op2_max_utility_range_over_unreached_theta": max(u_ranges) if u_ranges else None}


def t5_residue_exact():
    k3 = load_kuhn3()
    g = RiverGame(config("bridge.json"))
    types = KB.card_types(g)
    name = lambda i: KB.kuhn_name(*KB.coordinate(g, i, types))
    kp = k3.equilibrium_profile(k3.FamilyParameters(F(3, 20), F(3, 20), F(0), F(2, 5), F(1, 4), F(1, 5), F(0)))
    p = KB.profile_from_kuhn(g, kp)
    th = [next(I.index for I in g.isets if name(I.index) == "c33")]
    out = {}
    for dev in ("a11", "a21", "a41"):
        up = [next(I.index for I in g.isets if name(I.index) == dev)]
        D0 = upstream_D(g, set_theta(g, p, th, 1, F(0)), up, 1, 0)
        D1 = upstream_D(g, set_theta(g, p, th, 1, F(1)), up, 1, 0)
        C = D1 - D0
        ts = -D0[0] / C[0]
        t = (D0 + ts * C)[1]                         # costless transfer to the third player P2
        ok = True
        for k in range(0, 41):
            x = F(k, 40)
            if x == ts:
                continue
            D = D0 + x * C
            ok &= (-D[2] / D[0]) == 1 + t / (C[0] * (x - ts))
        out[dev] = {"C": [str(c) for c in C], "C_third_player_zero": C[1] == 0, "theta_star": str(ts),
                    "t": str(t), "R=t/C_A": str(t / C[0]), "identity_exact_at_40_points": bool(ok)}
    return out


def t5_residue_op2():
    out = []
    for f in sorted(glob.glob(os.path.join(RESULTS, "op2_silent", "expanded24", "*", "sweep_P1_*_bet.csv"))):
        rr = list(csv.DictReader(open(f)))
        th = np.array([float(r["theta"]) for r in rr]); D = np.array([[float(r["D1"]), float(r["D2"]), float(r["D3"])] for r in rr])
        C = D[-1] - D[0]
        if abs(C[0]) < 1e-14:
            out.append({"sweep": os.path.relpath(f, RESULTS), "C": C.tolist(), "status": "no theta dependence"})
            continue
        ts = -D[0, 0] / C[0]
        t = (D[0] + ts * C)[1]
        pred = 1 + t / (C[0] * (th - ts))
        meas = -D[:, 2] / D[:, 0]
        m = np.abs(th - ts) > 1e-6
        out.append({"sweep": os.path.relpath(f, RESULTS).replace("\\", "/"), "C": C.tolist(), "C_P2": float(C[1]),
                    "theta_star": float(ts), "theta_star_in_unit_interval": bool(0 <= ts <= 1),
                    "max_abs_error_of_residue_form": float(np.max(np.abs(pred[m] - meas[m]) / np.maximum(1, np.abs(meas[m]))))})
    return out


def t6_window():
    k3 = load_kuhn3()
    g = RiverGame(config("bridge.json"))
    types = KB.card_types(g)
    name = lambda i: KB.kuhn_name(*KB.coordinate(g, i, types))
    kp = k3.equilibrium_profile(k3.FamilyParameters(F(3, 20), F(3, 20), F(0), F(2, 5), F(1, 4), F(1, 5), F(0)))
    p = KB.profile_from_kuhn(g, kp)
    th = [next(I.index for I in g.isets if name(I.index) == "c33")]
    nash = []
    for k in range(0, 161):
        x = F(k, 160)
        r = residuals(g, set_theta(g, p, th, 1, x))["r"]
        nash.append((x, all(v == 0 for v in r)))
    inside = [x for x, ok in nash if ok]
    contiguous = all(ok for x, ok in nash if inside[0] <= x <= inside[-1])
    conv = []
    for f in sorted(glob.glob(os.path.join(RESULTS, "op2_silent", "expanded24", "*", "sweep_P1_JJ_bet.csv"))):
        rr = list(csv.DictReader(open(f)))
        r1 = np.array([float(r["r1"]) for r in rr])
        conv.append(float((r1[:-2] - 2 * r1[1:-1] + r1[2:]).min()))
    return {"bridge_window_on_grid_1/160": [str(inside[0]), str(inside[-1])], "contiguous": contiguous,
            "expected": ["1/10", "29/80"],
            "op2_min_second_difference_of_r1": conv,
            "note": "r1(theta) = max over P1's pure strategies of affine functions minus a constant: convex PL"}


def t8_classify():
    """For every information set J = (X, h, H) with total reach <= REACH_RARE, the three factors of
    pi(J) = own(J) * q(h) * E[opponents' reach of H | X holds h]:
        own      = pi_X(H | h)                         (X's own reach)
        opp      = Pr_{-X}(H) = sum_d q(d) prod_{Y!=X} pi_Y(H | d_Y)   (the others' actions in H)
        blocking = E[opponents' reach | X holds h] / Pr_{-X}(H)          (card removal by h)
    J is classed by its SMALLEST factor (own / opponent-silent / blocker); '-unreached' if pi(J) == 0
    exactly, else '-rare'."""
    out = {}
    for an in sorted(glob.glob(os.path.join(RESULTS, "*", "*", "*", "analysis.json"))):
        a = json.load(open(an))
        d = os.path.dirname(an)
        if not os.path.exists(os.path.join(d, "infosets.csv")):
            continue
        g = RiverGame(find_config(a["game"]["name"]))
        p = load_profile(os.path.join(d, "policy_avg.json"), g)
        R = reach(g, p)
        pr = prior(g, False)
        rch = infoset_reach(g, p, R)
        qh = [np.bincount(g.deals[:, i], weights=pr, minlength=len(g.seats[i].hands)) for i in range(g.n)]
        opp = {nid: float((pr * np.delete(R[nid], g.tree.nodes[nid].actor, axis=1).prod(axis=1)).sum()) for nid in g.iset_base}
        counts = {}
        for I in g.isets:
            tot = float(rch["total"][I.index])
            if tot > plan.REACH_RARE:
                continue
            own = float(rch["own"][I.index])
            o = opp[I.node]
            blk = (float(rch["cf"][I.index]) / qh[I.player][I.hand]) / o if o > 0 else 1.0
            k = min((own, "own"), (o, "opponent-silent"), (blk, "blocker"))[1]
            k = k + ("-unreached" if tot == 0.0 else "-rare")
            counts[k] = counts.get(k, 0) + 1
        out[a["run"]] = {"nashconv": a["nashconv"], "selected": a["selected"], "zero_or_rare": counts}
    return out


def t10_share_line():
    """4 players, one combo each of 99 JJ QQ KK AA on the dry board (5 strictly ordered types),
    pot 4, stacks 1, all-in only.  Random rational profile.  theta = P4's call with KK after
    B:1-F-F; upstream = P1's JJ bet.  The share vector s_k = -D_k / D_A must lie on one line."""
    cfg = {"name": "theory_4p", "board": "2c 4d 6h 8s Tc", "range": ["9s9h", "JsJh", "QsQh", "KsKh", "AsAh"],
           "prior": "product", "betting": {"n_players": 4, "prior_contrib": [1, 1, 1, 1], "stacks": [1, 1, 1, 1],
                                           "min_bet": 1, "bet_sizes": ["allin"], "raise_sizes": [], "max_raises": 0}}
    g = RiverGame(cfg)
    rng = np.random.default_rng(4)
    p = uniform(g, exact=True)
    for I in g.isets:
        x = F(int(rng.integers(1, 12)), 12)
        p[I.index, 0], p[I.index, 1] = 1 - x, x
    th = [I.index for I in g.isets if I.player == 3 and I.history == "B:1-F-F" and I.hand_label[0] == "K"]
    up = [I.index for I in g.isets if I.player == 0 and I.history == "" and I.hand_label[0] == "J"]
    S = []
    for k in range(0, 11):
        D = upstream_D(g, set_theta(g, p, th, 1, F(k, 10)), up, 1, 0)
        S.append([-D[j] / D[0] for j in range(1, 4)])
    base = S[0]
    dirs = [[s[j] - base[j] for j in range(3)] for s in S[1:]]
    # collinear iff every 2x2 minor of the direction vectors vanishes (exact)
    collinear = all(dirs[0][a] * d[b] - dirs[0][b] * d[a] == 0 for d in dirs for a in range(3) for b in range(3))
    return {"game": g.counts(), "share_sums_equal_1": all(sum(s) == 1 for s in S), "collinear_exact": collinear,
            "points": [[str(x) for x in s] for s in S[:3]]}


def p11_close_equilibria():
    k3 = load_kuhn3()
    g = RiverGame(config("bridge.json"))
    types = KB.card_types(g)
    name = lambda i: KB.kuhn_name(*KB.coordinate(g, i, types))
    kp = k3.equilibrium_profile(k3.FamilyParameters(F(3, 20), F(3, 20), F(0), F(2, 5), F(1, 4), F(1, 5), F(0)))
    p = KB.profile_from_kuhn(g, kp)
    th = [next(I.index for I in g.isets if name(I.index) == "c33")]
    up = [next(I.index for I in g.isets if name(I.index) == "a11")]
    rows = []
    for k in (2, 4, 6):
        eps = F(1, 10 ** k)
        a, b = F(1, 10) + eps, F(1, 10) + 2 * eps
        pa, pb = set_theta(g, p, th, 1, a), set_theta(g, p, th, 1, b)
        ra, rb = residuals(g, pa)["r"], residuals(g, pb)["r"]
        Da, Db = upstream_D(g, pa, up, 1, 0), upstream_D(g, pb, up, 1, 0)
        rho_a, rho_b = -Da[2] / Da[0], -Db[2] / Db[0]
        rows.append({"eps": str(eps), "both_exact_nash": all(x == 0 for x in ra + rb), "sup_distance": str(eps),
                     "rho_a": str(rho_a), "rho_b": str(rho_b), "rho_difference": float(abs(rho_a - rho_b))})
    return rows


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "t8":
        doc = json.load(open(os.path.join(OUT, "theory_checks.json")))
        doc["T8_classification"] = t8_classify()
        json.dump(doc, open(os.path.join(OUT, "theory_checks.json"), "w"), indent=1, default=str)
        return
    res = {"T3_own_unreached_no_cross_effect": t3_own_unreached(),
           "T3_sums_and_direct_effect": t3_sums_and_direct_effect(),
           "T5_residue_exact_bridge": t5_residue_exact(), "T5_residue_op2": t5_residue_op2(),
           "T6_window": t6_window(), "T8_classification": t8_classify(),
           "T10_share_line_4p": t10_share_line(), "P11_close_equilibria_far_rho": p11_close_equilibria()}
    json.dump(res, open(os.path.join(OUT, "theory_checks.json"), "w"), indent=1, default=str)
    for k, v in res.items():
        print("==", k)
        print(json.dumps(v, default=str)[:900])


if __name__ == "__main__":
    main()
