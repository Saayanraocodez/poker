"""Contrast sweep on the selected pilot profiles: the Kuhn-analogue parameter theta = P3's call
probability with KK after B:1-F (all six combos), which is ON path in the 24-hand game because
P1 opens AA and JJ.  Varying it changes baseline utilities and P3's own incentive, so it is not
a free off-path coordinate; the sweep shows by how much.  Upstream deviation: P1's JJ bet (all
six combos).  Output: results/pilot/contrast_<run>.csv and contrast_summary.json.

usage:  python scripts/pilot_contrast.py
"""
import csv
import glob
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from analyze_profiles import RESULTS, find_config                          # noqa: E402
from hinc.bestresponse import residuals                                    # noqa: E402
from hinc.evaluate import infoset_reach                                    # noqa: E402
from hinc.game import RiverGame                                            # noqa: E402
from hinc.offpath import set_theta, upstream_D, root_analysis              # noqa: E402
from hinc.strategy import load_profile                                     # noqa: E402


def main():
    out = []
    for an in sorted(glob.glob(os.path.join(RESULTS, "pilot", "*", "*", "analysis.json"))):
        a = json.load(open(an))
        if not a["selected"]:
            continue
        d = os.path.dirname(an)
        g = RiverGame(find_config(a["game"]["name"]))
        p = load_profile(os.path.join(d, "policy_avg.json"), g)
        theta = [I.index for I in g.isets if I.player == 2 and I.history == "B:1-F" and I.hand_label[0] == "K"]
        up = [I.index for I in g.isets if I.player == 0 and I.history == "" and I.hand_label[0] == "J"]
        tot = infoset_reach(g, p)["total"]
        th0 = float(np.mean([p[i, 1] for i in theta]))
        rows = []
        for th in np.linspace(0, 1, 21):
            q = set_theta(g, p, theta, 1, float(th))
            res = residuals(g, q)
            D = upstream_D(g, q, up, 1, 0)
            rows.append([float(th)] + [float(x) for x in res["utilities"]] + [float(x) for x in res["r"]] + [float(x) for x in D])
        ra = root_analysis(g, p, theta, 1, up, 1, 0)
        name = os.path.relpath(d, os.path.join(RESULTS, "pilot")).replace(os.sep, "_")
        with open(os.path.join(RESULTS, "pilot", "contrast_%s.csv" % name), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["theta", "u1", "u2", "u3", "r1", "r2", "r3", "D1", "D2", "D3"])
            w.writerows(rows)
        u = np.array([r[1:4] for r in rows]); r = np.array([r[4:7] for r in rows])
        out.append({"run": name, "theta_baseline": th0, "theta_reach": float(sum(tot[i] for i in theta)),
                    "utility_range_over_theta": (u.max(axis=0) - u.min(axis=0)).tolist(),
                    "max_r_over_theta": r.max(axis=0).tolist(), "baseline_r": a["r"],
                    "root_analysis_P1_JJ_bet": ra})
        print(name, "theta0 %.3f reach %.4f  utility range %s  max r3 %.3e" % (
            th0, out[-1]["theta_reach"], np.round(out[-1]["utility_range_over_theta"], 5), r[:, 2].max()))
    json.dump(out, open(os.path.join(RESULTS, "pilot", "contrast_summary.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
