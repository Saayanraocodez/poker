"""Sweeps along every validated class-level pole witness of the lowest-NashConv selected run of each
group/game that has witnesses (selection by residual; ALL its witnesses are swept, none hand-picked).

The profile is the rationalised one used in the exact checks (limit_denominator(10^6), rows
renormalised exactly); exact residuals and the exact root theta* come from analysis.json /
recomputed here; the sweep grid itself is evaluated in float64.
Output: results/witness_sweeps/<game>/<witness>.csv, summary.json, and results/plots/witness_sweeps_<game>.png

usage:  python scripts/witness_sweeps.py [group=panel]
"""
import csv
import glob
import json
import os
import sys
from fractions import Fraction

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from analyze_profiles import RESULTS, find_config, hand_class                # noqa: E402
from hinc.bestresponse import residuals                                       # noqa: E402
from hinc.evaluate import infoset_reach                                       # noqa: E402
from hinc.game import RiverGame                                               # noqa: E402
from hinc.offpath import set_theta, upstream_D, root_analysis                 # noqa: E402
from hinc.strategy import load_profile, to_exact, normalise_exact             # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def groups_of(g, label, history, player):
    return [I.index for I in g.isets if I.player == player - 1 and I.history == history and hand_class(I.hand_label) == label]


def main(group):
    out = {}
    games = {}
    for an in glob.glob(os.path.join(RESULTS, group, "*", "*", "analysis.json")):
        a = json.load(open(an))
        if a.get("selected") and a.get("offpath_class", {}).get("pole_witnesses"):
            games.setdefault(a["game"]["name"], []).append((a["nashconv"], an, a))
    for gname, runs in sorted(games.items()):
        nc, an, a = min(runs)
        d = os.path.dirname(an)
        g = RiverGame(find_config(gname))
        ex = normalise_exact(g, to_exact(load_profile(os.path.join(d, "policy_avg.json"), g), 10 ** 6))
        pf = np.array(ex, dtype=float)
        base = residuals(g, ex)
        rows_all = []
        csvdir = os.path.join(RESULTS, "witness_sweeps", gname)
        os.makedirs(csvdir, exist_ok=True)
        pairs = []
        with open(os.path.join(d, "offpath_pairs_class.csv")) as f:
            for r in csv.DictReader(f):
                if r["pole_witness"] == "True":
                    pairs.append(r)
        pairs.sort(key=lambda r: (r["theta_history"], r["theta"], r["upstream"]))
        for r in pairs:
            th = groups_of(g, r["theta"], r["theta_history"], int(r["theta_owner"]))
            up = groups_of(g, r["upstream"], r["upstream_history"], int(r["upstream_player"]))
            A = int(r["upstream_player"]) - 1
            ra = root_analysis(g, ex, th, 1, up, 1, 0)
            ts = Fraction(ra["theta_star_exact"])
            rr_star = residuals(g, set_theta(g, ex, th, 1, ts))["r"]
            reach0 = infoset_reach(g, ex)["total"]
            grid = sorted(set(list(np.linspace(0, 1, 51)) + [float(ts)]))
            rows = []
            for x in grid:
                q = set_theta(g, pf, th, 1, float(x))
                res = residuals(g, q)
                D = upstream_D(g, q, up, 1, 0)
                rho = [float(-D[X] / D[A]) if abs(D[A]) > 1e-13 else float("nan") for X in range(g.n)]
                rows.append([float(x)] + [float(v) for v in res["r"]] + [float(v) for v in D] + rho)
            tag = "%s@%s_vs_P%d_%s" % (r["theta"], r["theta_history"] or "root", A + 1, r["upstream"])
            with open(os.path.join(csvdir, tag.replace(":", "") + ".csv"), "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["theta", "r1", "r2", "r3", "D1", "D2", "D3", "rho_P1", "rho_P2", "rho_P3"])
                w.writerows(rows)
            theta0 = float(np.mean([pf[i, 1] for i in th]))
            rec = {"witness": tag, "theta_owner": int(r["theta_owner"]), "theta0": theta0,
                   "theta_reach_exact": str(sum(reach0[i] for i in th)), "theta_star": float(ts),
                   "theta_star_exact_digits": len(str(ts.denominator)),
                   "cross_effect": ra["cross_effect"], "D_at_theta_star": ra["D_at_theta_star"],
                   "exact_r_baseline": [str(v) for v in base["r"]], "exact_r_at_theta_star": [str(v) for v in rr_star],
                   "kept_side": "theta <= theta*" if ra["cross_effect"][A] > 0 else "theta >= theta*"}
            rows_all.append((rec, rows))
        out[gname] = {"run": a["run"], "nashconv_float": nc, "exact_nashconv_rationalised": str(base["nashconv"]),
                      "witnesses": [rec for rec, _ in rows_all]}
        # small multiples: D_A, opponent D's, and r_A along every witness
        k = len(rows_all)
        cols = min(4, k)
        nr = (k + cols - 1) // cols
        fig, axes = plt.subplots(nr, cols, figsize=(3.3 * cols, 2.7 * nr), squeeze=False)
        for ax, (rec, rows) in zip(axes.flat, rows_all):
            x = [z[0] for z in rows]
            A = int(rec["witness"].split("_vs_P")[1][0]) - 1
            for i, (c, ls) in enumerate((("C0", "-"), ("C1", ":"), ("C2", "--"))):
                ax.plot(x, [z[4 + i] for z in rows], ls, color=c, lw=1.1, label="D%d" % (i + 1))
            ax.plot(x, [z[1 + A] for z in rows], "k-", lw=0.8, alpha=0.6, label="r%d" % (A + 1))
            ax.axvline(rec["theta_star"], color="r", lw=0.8)
            ax.axvline(rec["theta0"], color="grey", lw=0.8, ls="--")
            ax.axhline(0, color="k", lw=0.4)
            ax.set_title(rec["witness"], fontsize=7)
            ax.tick_params(labelsize=6)
        for ax in list(axes.flat)[k:]:
            ax.axis("off")
        axes.flat[0].legend(fontsize=6)
        fig.suptitle("%s (%s): every validated class-level witness. red = exact theta*, dashed = baseline theta; "
                     "black = deviator's residual" % (gname, a["run"]), fontsize=8)
        fig.tight_layout()
        os.makedirs(os.path.join(RESULTS, "plots"), exist_ok=True)
        fig.savefig(os.path.join(RESULTS, "plots", "witness_sweeps_%s.png" % gname), dpi=130)
        plt.close(fig)
        # incidence along one belief-dependent witness (theta interior at baseline), if any
        interior = [(rec, rows) for rec, rows in rows_all if 0 < rec["theta0"] < 1]
        if interior:
            rec, rows = interior[0]
            A = int(rec["witness"].split("_vs_P")[1][0]) - 1
            fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
            x = [z[0] for z in rows]
            for X in range(3):
                if X != A:
                    ax[0].plot(x, [z[7 + X] for z in rows], label="rho(P%d->P%d)" % (A + 1, X + 1))
            ax[0].set_ylim(-20, 20); ax[0].axvline(rec["theta_star"], color="r", lw=0.8)
            ax[0].axvline(rec["theta0"], color="grey", ls="--", lw=0.8); ax[0].legend(fontsize=7)
            ax[0].set_title("incidence along %s" % rec["witness"], fontsize=8)
            ax[1].plot(x, [z[1 + A] for z in rows], "k-")
            ax[1].axvline(rec["theta_star"], color="r", lw=0.8)
            ax[1].set_title("deviator's full best-response residual r%d" % (A + 1), fontsize=8)
            for z in ax:
                z.set_xlabel("theta (off-path response probability)"); z.grid(alpha=0.3)
            fig.tight_layout()
            fig.savefig(os.path.join(RESULTS, "plots", "witness_incidence_%s.png" % gname), dpi=130)
            plt.close(fig)
    os.makedirs(os.path.join(RESULTS, "witness_sweeps"), exist_ok=True)
    json.dump(out, open(os.path.join(RESULTS, "witness_sweeps", "summary.json"), "w"), indent=1)
    for gname, o in out.items():
        print(gname, o["run"], "exact NashConv", o["exact_nashconv_rationalised"], "witnesses", len(o["witnesses"]))
        for w in o["witnesses"]:
            print("   %-32s theta0 %.3f theta* %.4f  r*(exact) %s  D* %s" % (w["witness"], w["theta0"], w["theta_star"],
                  w["exact_r_at_theta_star"], [round(v, 5) for v in w["D_at_theta_star"]]))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "panel")
