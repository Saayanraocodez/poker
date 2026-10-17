"""Plots from saved results only (no recomputation).  Output: results/plots/*.png

1. pilot_convergence.png      NashConv of the average (and current) strategy vs iterations, all seeds
2. panel_convergence.png      the same for every panel game
3. kuhn_c33_pole.png          positive control: exact D vector and rho of P1's a11 / a41 bets, and
                              P1's exact residual, along Kuhn's c33 window
4. op2_sweep.png              imposed P1 silence: D vector, rho and residuals along theta = P3's
                              KK call at B:1-F, for P1's JJ and AA bets
5. pilot_derivatives.png      raw derivative vectors of every binary direction in the pilot
                              profiles: own effect |D_A| vs largest opponent effect, by class
"""
import csv
import glob
import json
import os
from fractions import Fraction

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.environ.get("HINC_RESULTS", os.path.join(ROOT, "results"))
OUT = os.path.join(RES, "plots")
os.makedirs(OUT, exist_ok=True)


def read_hist(path):
    rows = list(csv.DictReader(open(path)))
    return [int(r["t"]) for r in rows], [float(r["avg_nashconv"]) for r in rows], [float(r["cur_nashconv"]) for r in rows]


def convergence(group, fname, title):
    runs = sorted(glob.glob(os.path.join(RES, group, "*", "*", "history.csv")))
    if not runs:
        return
    games = sorted({r.split(os.sep)[-3] for r in runs})
    fig, axes = plt.subplots(1, len(games), figsize=(4.2 * len(games), 3.4), squeeze=False)
    for ax, gname in zip(axes[0], games):
        for r in runs:
            if r.split(os.sep)[-3] != gname:
                continue
            run = r.split(os.sep)[-2]
            t, a, c = read_hist(r)
            style = "-" if run.startswith("dcfr") else "--"
            col = "C0" if run.startswith("dcfr") else "C1"
            ax.loglog(t, [max(x, 1e-12) for x in a], style, color=col, lw=1.2, alpha=0.9)
            ax.loglog(t, [max(x, 1e-12) for x in c], style, color=col, lw=0.6, alpha=0.3)
        ax.set_title(gname, fontsize=8)
        ax.set_xlabel("iteration")
        ax.grid(alpha=0.3, which="both")
    axes[0][0].set_ylabel("NashConv (bb, conditional root)")
    fig.suptitle(title + "  (blue DCFR, orange CFR+; bold = average strategy, faint = current)", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=130)
    plt.close(fig)


def kuhn_pole():
    p = os.path.join(RES, "positive_control", "kuhn_c33_sweep.csv")
    if not os.path.exists(p):
        return
    rows = list(csv.DictReader(open(p)))
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.4))
    for dev, col in (("a11", "C0"), ("a41", "C3")):
        rr = [r for r in rows if r["dev"] == dev]
        x = [float(Fraction(r["c33"])) for r in rr]
        for i, ls in ((0, "-"), (1, ":"), (2, "--")):
            ax[0].plot(x, [float(Fraction(r["D%d" % (i + 1)])) for r in rr], ls, color=col, label="%s: D%d" % (dev, i + 1))
        rho = [float(Fraction(r["rho_P3"])) if r["rho_P3"] else float("nan") for r in rr]
        ax[1].plot(x, rho, color=col, label="rho(P1->P3), %s" % dev)
    rr = [r for r in rows if r["dev"] == "a11"]
    ax[2].plot([float(Fraction(r["c33"])) for r in rr], [float(Fraction(r["r1"])) for r in rr], "k-")
    for a in ax:
        a.axvline(0.1, color="grey", lw=0.8); a.axvline(29 / 80, color="grey", lw=0.8)
        a.set_xlabel("c33 (P3 calls with K after B-F)")
        a.grid(alpha=0.3)
    ax[0].axhline(0, color="k", lw=0.5); ax[0].legend(fontsize=6); ax[0].set_title("exact derivative vectors", fontsize=9)
    ax[1].set_ylim(-30, 30); ax[1].legend(fontsize=7); ax[1].set_title("incidence: simple poles at the window ends", fontsize=9)
    ax[2].set_title("P1's exact best-response residual r1", fontsize=9)
    fig.suptitle("Positive control (bridge = Kuhn), sub-family B, b32 = 2/5: window [1/10, 29/80]", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "kuhn_c33_pole.png"), dpi=130)
    plt.close(fig)


def op2():
    files = sorted(glob.glob(os.path.join(RES, "op2_silent", "expanded24", "*", "sweep_P1_JJ_bet.csv")))
    if not files:
        return
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.4))
    for k, f in enumerate(files):
        seed = f.split(os.sep)[-2]
        for tag, col in (("JJ", "C0"), ("AA", "C3")):
            rows = list(csv.DictReader(open(f.replace("JJ", tag))))
            x = [float(r["theta"]) for r in rows]
            ax[0].plot(x, [float(r["D1"]) for r in rows], "-", color=col, alpha=0.7, label="P1 %s bet: D1" % tag if k == 0 else None)
            ax[0].plot(x, [float(r["D3"]) for r in rows], "--", color=col, alpha=0.7, label="P1 %s bet: D3" % tag if k == 0 else None)
            ax[1].plot(x, [float(r["rho_P3"]) if r["rho_P3"] not in ("", "None") else float("nan") for r in rows], color=col,
                       alpha=0.7, label="rho(P1->P3), %s bet" % tag if k == 0 else None)
        rows = list(csv.DictReader(open(f)))
        ax[2].plot([float(r["theta"]) for r in rows], [float(r["r1"]) for r in rows], "k-", alpha=0.7, label="r1" if k == 0 else None)
        ax[2].plot([float(r["theta"]) for r in rows], [float(r["r3"]) for r in rows], "g:", alpha=0.7, label="r3" if k == 0 else None)
    for a in ax:
        a.set_xlabel("theta = P3's call prob. with KK after B:1-F")
        a.grid(alpha=0.3)
    ax[0].axhline(0, color="k", lw=0.5); ax[0].legend(fontsize=6); ax[0].set_title("raw derivative vectors", fontsize=9)
    ax[1].legend(fontsize=7); ax[1].set_title("incidence (raw; not at an equilibrium)", fontsize=9)
    ax[2].legend(fontsize=7); ax[2].set_title("full-game residuals along the sweep", fontsize=9)
    fig.suptitle("OP2: 24-hand game with P1's opening forced to check; responses chosen by deterrence search", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "op2_sweep.png"), dpi=130)
    plt.close(fig)


def pilot_derivatives():
    files = sorted(glob.glob(os.path.join(RES, "pilot", "*", "*", "incidence.csv")))
    if not files:
        return
    pts = {}
    for f in files:
        for r in csv.DictReader(open(f)):
            A = int(r["player"]) - 1
            D = [float(r["D%d" % (i + 1)]) for i in range(3)]
            own = abs(D[A])
            opp = max(abs(D[i]) for i in range(3) if i != A)
            pts.setdefault(r["class"], []).append((max(own, 1e-16), max(opp, 1e-16)))
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    for c, v in sorted(pts.items()):
        ax.loglog([a for a, b in v], [b for a, b in v], ".", ms=3, alpha=0.5, label="%s (%d)" % (c, len(v)))
    lim = [1e-16, 1]
    ax.loglog(lim, lim, "k-", lw=0.5)
    ax.set_xlabel("|D_A| (deviator's own first-order effect, bb)")
    ax.set_ylabel("max opponent |D_X| (bb)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3, which="both")
    ax.set_title("Pilot (24-hand), all profiles: raw derivative vectors", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "pilot_derivatives.png"), dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    convergence("pilot", "pilot_convergence.png", "Pilot: 24-hand JJ-AA river game")
    convergence("panel", "panel_convergence.png", "Sensitivity panel")
    convergence("positive_control", "bridge_convergence.png", "Bridge (Kuhn) DCFR")
    kuhn_pole()
    op2()
    pilot_derivatives()
    print("plots in", OUT, sorted(os.listdir(OUT)))
