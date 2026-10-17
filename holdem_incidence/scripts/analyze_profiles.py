"""Analyse every trained profile of a group by the declared plan (hinc/plan.py).

Per run (results/<group>/<game>/<run>/):
  analysis.json        selection, float and exact residuals, reach census, class counts,
                       off-path scan summary, validated pole witnesses (with exact checks)
  infosets.csv         per information set: probabilities, reach (total / own / cf), reach class,
                       averaging weight
  incidence.csv        per binary information set: the feasible aggressive-increase (or decrease)
                       direction, raw D vector, sum, class, rho, tolerances
  offpath_pairs.csv    every (theta, upstream) pair scanned: cross effect, theta*, numerator,
                       criteria (a)-(d)
Group summary: results/<group>/summary.json and summary.csv.

usage:  python scripts/analyze_profiles.py pilot|panel|control [workers]
"""
import csv
import glob
import json
import os
import sys
from fractions import Fraction
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
RESULTS = os.environ.get("HINC_RESULTS", os.path.join(ROOT, "results"))   # scratch runs: point elsewhere
from hinc import plan                                                      # noqa: E402
from hinc.bestresponse import residuals                                    # noqa: E402
from hinc.evaluate import infoset_reach, utilities                         # noqa: E402
from hinc.game import RiverGame                                            # noqa: E402
from hinc.incidence import binary_records                                  # noqa: E402
from hinc.offpath import root_analysis, set_theta, upstream_D              # noqa: E402
from hinc.strategy import load_profile, to_exact, normalise_exact          # noqa: E402


def find_config(name):
    for f in glob.glob(os.path.join(ROOT, "configs", "*.json")) + glob.glob(os.path.join(ROOT, "configs", "panel", "*.json")):
        c = json.load(open(f))
        if c.get("name") == name:
            return c
    raise KeyError(name)


def hand_class(label):
    r1, s1, r2, s2 = label[0], label[1], label[2], label[3]
    if r1 == r2:
        return r1 + r2
    return r1 + r2 + ("s" if s1 == s2 else "o")


def reach_class(x):
    if x == 0.0:
        return "unreached"
    return "rare" if x <= plan.REACH_RARE else "reached"


def family_check(g, probs, theta_isets, up_isets, base_r, ts, D0, C, A):
    """Criterion (d): on the kept side (D_A(theta) <= 0) of theta* within the window, every
    r_i(theta) <= r_i(baseline) + TOL_FAMILY.  Returns (pass, max increase per player, points)."""
    grid = np.linspace(max(0.0, ts - plan.FAMILY_WINDOW), min(1.0, ts + plan.FAMILY_WINDOW), plan.FAMILY_GRID)
    grid = sorted(set([float(x) for x in grid] + [float(ts)]))
    pts, worst = [], [0.0] * g.n
    for th in grid:
        dA = D0[A] + th * C[A]
        if dA > plan.TOL_NUM:
            continue                                     # the deviation pays here: not the kept side
        p = set_theta(g, probs, theta_isets, 1, th)
        r = [float(x) for x in residuals(g, p)["r"]]
        for i in range(g.n):
            worst[i] = max(worst[i], r[i] - base_r[i])
        pts.append({"theta": th, "r": r, "D_A": float(dA)})
    ok = bool(pts) and all(w <= plan.TOL_FAMILY for w in worst)
    return ok, worst, pts


def scan(g, probs, base_r, reach, groups):
    """groups: list of (label, [infoset indices]) at the SAME public history and owner (a combo
    or a hand class).  Returns rows for every (theta group, upstream group) pair."""
    rows = []
    by_hist = {}
    for lab, idx in groups:
        I = g.isets[idx[0]]
        by_hist.setdefault((I.player, I.history), []).append((lab, idx))
    theta_groups = [(lab, idx) for lab, idx in groups
                    if len(g.isets[idx[0]].actions) == 2 and sum(reach[i] for i in idx) <= plan.REACH_RARE]
    for tl, tidx in theta_groups:
        T = g.isets[tidx[0]]
        for (p, h), ups in by_hist.items():
            if p == T.player:
                continue
            node = next(nd for nd in g.tree.decision_nodes if nd.history == h)
            agg = node.actions[1]
            pre = (h + "-" + agg) if h else agg
            if not (T.history == pre or T.history.startswith(pre + "-")):
                continue
            for ul, uidx in ups:
                ra = root_analysis(g, probs, tidx, 1, uidx, 1, 0)
                A = p
                C = ra["cross_effect"]
                row = {"theta": tl, "theta_owner": T.player + 1, "theta_history": T.history,
                       "theta_reach": float(sum(reach[i] for i in tidx)),
                       "theta_reach_class": reach_class(float(sum(reach[i] for i in tidx))),
                       "theta_value": float(np.mean([probs[i, 1] for i in tidx])),
                       "upstream": ul, "upstream_player": A + 1, "upstream_history": h,
                       "upstream_prob_aggr": float(np.mean([probs[i, 1] for i in uidx])),
                       "D_at_0": ra["D_at_0"], "D_at_1": ra["D_at_1"], "cross": C,
                       "theta_star": ra.get("theta_star")}
                a = abs(C[A]) > plan.TOL_CROSS
                row["a_cross_effect"] = a
                ts = ra.get("theta_star")
                row["b_root_in_unit_interval"] = bool(a and ts is not None and 0.0 <= ts <= 1.0)
                if row["b_root_in_unit_interval"]:
                    num = ra["D_at_theta_star"]
                    row["D_at_theta_star"] = num
                    row["c_numerator_nonzero"] = any(abs(num[X]) > plan.TOL_NUMERATOR for X in range(g.n) if X != A)
                else:
                    row["c_numerator_nonzero"] = False
                row["d_family_kept"] = None
                if row["c_numerator_nonzero"]:
                    ok, worst, pts = family_check(g, probs, tidx, uidx, base_r, ts, ra["D_at_0"], C, A)
                    row["d_family_kept"] = ok
                    row["family_max_r_increase"] = worst
                    row["family_points"] = len(pts)
                row["pole_witness"] = bool(row["c_numerator_nonzero"] and row["d_family_kept"])
                rows.append(row)
    return rows


def exact_check(g, probs, witness, groups_by_label):
    """Rationalise the profile (limit_denominator 10^6, rows renormalised exactly) and redo the
    witness exactly: residuals, theta*, numerator, slope, and residuals at theta*."""
    ex = normalise_exact(g, to_exact(probs, 10 ** 6))
    res = residuals(g, ex)
    tidx = groups_by_label[(witness["theta"], witness["theta_history"])]
    uidx = groups_by_label[(witness["upstream"], witness["upstream_history"])]
    ra = root_analysis(g, ex, tidx, 1, uidx, 1, 0)
    A = witness["upstream_player"] - 1
    out = {"rational_profile": "limit_denominator(10^6) per entry, last action absorbs rounding",
           "exact_r": [str(x) for x in res["r"]], "exact_r_float": [float(x) for x in res["r"]],
           "exact_nashconv": float(res["nashconv"]), "theta_star_exact": ra.get("theta_star_exact"),
           "slope_exact_nonzero": ra["cross_effect"][A] != 0}
    if ra.get("theta_star") is not None and 0 <= ra["theta_star"] <= 1:
        ts = Fraction(ra["theta_star_exact"])
        p = set_theta(g, ex, tidx, 1, ts)
        D = upstream_D(g, p, uidx, 1, 0)
        rr = residuals(g, p)
        out["D_at_theta_star_exact"] = [str(x) for x in D]
        out["denominator_zero_exactly"] = D[A] == 0
        out["numerator_nonzero_exactly"] = any(D[X] != 0 for X in range(g.n) if X != A)
        out["r_at_theta_star_exact"] = [str(x) for x in rr["r"]]
        out["r_at_theta_star_float"] = [float(x) for x in rr["r"]]
        out["deviator_r_not_above_baseline"] = rr["r"][A] <= res["r"][A]
    return out


def analyse(run_dir):
    cached = os.path.join(run_dir, "analysis.json")
    if os.path.exists(cached) and os.path.getmtime(cached) >= os.path.getmtime(os.path.join(run_dir, "policy_avg.json"))             and not os.environ.get("HINC_REANALYSE"):
        return json.load(open(cached))               # already analysed this exact policy
    run = json.load(open(os.path.join(run_dir, "run.json")))
    g = RiverGame(find_config(run["game"]["name"]))
    probs = load_profile(os.path.join(run_dir, "policy_avg.json"), g)
    pol = json.load(open(os.path.join(run_dir, "policy_avg.json")))
    pot = float(sum(g.rules.prior_contrib))
    res = residuals(g, probs)
    r = [float(x) for x in res["r"]]
    nc = float(res["nashconv"])
    selected = nc <= plan.SELECT_NASHCONV_PER_POT * pot
    out = {"run": os.path.relpath(run_dir, RESULTS).replace("\\", "/"), "game": g.record(), "variant": run["variant"],
           "seed": run["seed"], "iterations": run["iterations"], "averaging": run["averaging"],
           "utilities": [float(x) for x in res["utilities"]], "r": r, "max_r": max(r), "nashconv": nc,
           "selection_rule": "NashConv(avg) <= %g x pot = %g bb" % (plan.SELECT_NASHCONV_PER_POT, plan.SELECT_NASHCONV_PER_POT * pot),
           "selected": selected, "zero_weight_infosets": pol.get("zero_weight_infosets", [])}
    rch = infoset_reach(g, probs)
    tot, own, cf = rch["total"], rch["own"], rch["cf"]
    with open(os.path.join(run_dir, "infosets.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "player", "hand", "class", "history", "actions", "probs", "reach_total", "reach_own",
                    "reach_cf", "reach_class", "avg_weight"])
        for I in g.isets:
            w.writerow([I.id, I.player + 1, I.hand_label, hand_class(I.hand_label), I.history, "|".join(I.actions),
                        "|".join("%.10g" % probs[I.index, a] for a in range(len(I.actions))),
                        "%.6e" % tot[I.index], "%.6e" % own[I.index], "%.6e" % cf[I.index],
                        reach_class(float(tot[I.index])), "%.6e" % pol["avg_weight"][I.index]])
    out["reach_census"] = {c: int(sum(reach_class(float(x)) == c for x in tot)) for c in ("unreached", "rare", "reached")}
    # P1's opening behaviour by hand class
    op = {}
    for I in g.isets:
        if I.player == 0 and I.history == "":
            op.setdefault(hand_class(I.hand_label), []).append(float(probs[I.index, 1]))
    out["P1_open_prob_by_class"] = {k: float(np.mean(v)) for k, v in sorted(op.items())}
    if not selected:
        json.dump(out, open(os.path.join(run_dir, "analysis.json"), "w"), indent=1)
        return out
    recs = binary_records(g, probs, max(r))
    with open(os.path.join(run_dir, "incidence.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["infoset", "player", "hand", "history", "move", "prob_from", "feasible"] +
                   ["D%d" % (i + 1) for i in range(g.n)] + ["D_sum", "class"] +
                   ["rho_P%d" % (i + 1) for i in range(g.n)] + ["rho_sum", "tol_num", "tol_eq"])
        for x in recs:
            w.writerow([x["infoset"], x["player"], x["hand"], x["history"], x["move"], x["prob_from"], x["feasible"]] +
                       ["%.12e" % d for d in x["D"]] + ["%.3e" % x["D_sum"], x["class"]] +
                       [("%.10g" % x["rho"]["P%d" % (i + 1)]) if "P%d" % (i + 1) in x["rho"] else "" for i in range(g.n)] +
                       ["" if x["rho_sum"] is None else "%.12f" % x["rho_sum"], x["tol_num"], x["tol_eq"]])
    cls = {}
    for x in recs:
        cls[x["class"]] = cls.get(x["class"], 0) + 1
    out["direction_classes"] = cls
    out["max_abs_D_sum"] = max(abs(x["D_sum"]) for x in recs)
    rs = [x["rho_sum"] for x in recs if x["rho_sum"] is not None]
    out["max_abs_rho_sum_minus_1"] = max((abs(s - 1) for s in rs), default=None)
    if g.n == 2:
        out["control_rho_opponent"] = sorted({round(list(x["rho"].values())[0], 12) for x in recs if x["rho"]})
        out["control_costless_transfers"] = cls.get("costless_transfer", 0)
        json.dump(out, open(os.path.join(run_dir, "analysis.json"), "w"), indent=1)
        return out
    # off-path scan at combo level and at hand-class level
    combo_groups = [(I.hand_label, [I.index]) for I in g.isets]
    cg = {}
    for I in g.isets:
        cg.setdefault((hand_class(I.hand_label), I.player, I.history), []).append(I.index)
    class_groups = [(k[0], v) for k, v in cg.items()]
    lookup = {}
    for lab, idx in combo_groups + class_groups:
        lookup[(lab, g.isets[idx[0]].history)] = idx
    scans = {}
    for level, groups in (("combo", combo_groups), ("class", class_groups)):
        rows = scan(g, probs, r, tot, groups)
        scans[level] = rows
        with open(os.path.join(run_dir, "offpath_pairs_%s.csv" % level), "w", newline="") as f:
            w = csv.writer(f)
            keys = ["theta", "theta_owner", "theta_history", "theta_reach", "theta_reach_class", "theta_value",
                    "upstream", "upstream_player", "upstream_history", "upstream_prob_aggr", "cross",
                    "theta_star", "D_at_theta_star", "a_cross_effect", "b_root_in_unit_interval",
                    "c_numerator_nonzero", "d_family_kept", "family_max_r_increase", "pole_witness"]
            w.writerow(keys)
            for row in rows:
                w.writerow([json.dumps(row.get(k)) if isinstance(row.get(k), list) else row.get(k) for k in keys])
        out["offpath_%s" % level] = {
            "theta_candidates": len({(x["theta"], x["theta_history"]) for x in rows}),
            "pairs_scanned": len(rows),
            "a_cross_effect": sum(x["a_cross_effect"] for x in rows),
            "b_root_in_unit_interval": sum(x["b_root_in_unit_interval"] for x in rows),
            "c_numerator_nonzero": sum(x["c_numerator_nonzero"] for x in rows),
            "pole_witnesses": sum(x["pole_witness"] for x in rows),
            "witness_reach_classes": sorted({x["theta_reach_class"] for x in rows if x["pole_witness"]})}
    # exact verification of the first witnesses in a fixed order (by ids), never by ratio size
    wit = sorted([x for x in scans["class"] if x["pole_witness"]], key=lambda x: (x["theta_history"], x["theta"], x["upstream"]))
    out["witnesses_class_level"] = []
    for x in wit[:6]:
        ex = exact_check(g, probs, x, lookup)
        out["witnesses_class_level"].append({k: x[k] for k in ("theta", "theta_owner", "theta_history", "theta_reach",
                                                               "theta_reach_class", "theta_value", "upstream",
                                                               "upstream_player", "upstream_history", "cross",
                                                               "theta_star", "D_at_theta_star", "family_max_r_increase")}
                                             | {"exact": ex})
    json.dump(out, open(os.path.join(run_dir, "analysis.json"), "w"), indent=1)
    return out


def main(argv):
    group = argv[1]
    workers = int(argv[2]) if len(argv) > 2 else 12
    dirs = sorted(glob.glob(os.path.join(RESULTS, group, "*", "*", "run.json")))
    dirs = [os.path.dirname(d) for d in dirs]
    with Pool(min(workers, len(dirs))) as pool:
        results = pool.map(analyse, dirs)
    keys = ["run", "variant", "seed", "iterations", "nashconv", "max_r", "selected"]
    with open(os.path.join(RESULTS, group, "summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(keys + ["r1", "r2", "r3", "u", "unreached", "rare", "reached", "classes",
                           "combo_pairs", "combo_witnesses", "class_pairs", "class_witnesses", "P1_open"])
        for o in results:
            w.writerow([o[k] for k in keys] + o["r"] + [0] * (3 - len(o["r"])) +
                       [json.dumps([round(x, 6) for x in o["utilities"]]), o["reach_census"]["unreached"],
                        o["reach_census"]["rare"], o["reach_census"]["reached"], json.dumps(o.get("direction_classes")),
                        o.get("offpath_combo", {}).get("pairs_scanned"), o.get("offpath_combo", {}).get("pole_witnesses"),
                        o.get("offpath_class", {}).get("pairs_scanned"), o.get("offpath_class", {}).get("pole_witnesses"),
                        json.dumps({k: round(v, 4) for k, v in o["P1_open_prob_by_class"].items()})])
    json.dump(results, open(os.path.join(RESULTS, group, "summary.json"), "w"), indent=1)
    for o in results:
        print("%-55s NC %.2e sel %s | classes %s | combo witnesses %s / %s | class witnesses %s / %s" % (
            o["run"], o["nashconv"], o["selected"], o.get("direction_classes"),
            o.get("offpath_combo", {}).get("pole_witnesses"), o.get("offpath_combo", {}).get("pairs_scanned"),
            o.get("offpath_class", {}).get("pole_witnesses"), o.get("offpath_class", {}).get("pairs_scanned")))


if __name__ == "__main__":
    main(sys.argv)
