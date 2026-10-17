"""OP2 (preregistration amendment 1): imposed P1 silence on the 24-hand game.

1. Train DCFR (seeds 1-3, 12,000 iterations) on the RESTRICTED game in which P1's opening is
   forced to check.  P2's and P3's responses to a P1 bet are then genuinely unreached (reach 0
   exactly): CFR leaves them at whatever its initialisation gave, so they are NOT used as found.
2. Choose those 72 responses explicitly: minimise P1's FULL-game best-response value (P1 may now
   open) over the response block by exact coordinate minimisation.  BR_1 is a maximum of affine
   functions of any single response probability, hence convex piecewise-linear in it; each
   coordinate is minimised by golden-section search plus both endpoints.  Five declared starts:
   all fold, all call, all 1/2, uniform-random seeds 1 and 2.  The result is an UPPER BOUND on the
   best achievable deterrence (a local search), not a proof that deterrence is impossible.
3. At the best response block, sweep theta = P3's call probability with KK at B:1-F (all six
   combos together: the c33 analogue) with everything else fixed, and measure the derivative
   vector of P1's JJ bet (the a11 analogue; all six combos together) and of P1's AA bet (the a41
   analogue), the incidence ratios, all three full-game residuals, and the reach of theta's sets
   under the baseline and under the deviation.  The exact affine root is computed on the
   rationalised profile.

usage:  python scripts/silent_p1.py train   ->  results/op2_silent/expanded24/dcfr_s*/
        python scripts/silent_p1.py analyse ->  results/op2_silent/op2_results.json, sweep CSVs
"""
import csv
import json
import os
import sys
from fractions import Fraction
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import run_training as RT                                                  # noqa: E402
from hinc.bestresponse import best_response, residuals                     # noqa: E402
from hinc.evaluate import infoset_reach, utilities                         # noqa: E402
from hinc.game import RiverGame                                            # noqa: E402
from hinc.offpath import root_analysis, set_theta, upstream_D, deviate     # noqa: E402
from hinc.strategy import load_profile, to_exact, normalise_exact          # noqa: E402

GROUP = "op2_silent"
CFG = os.path.join(ROOT, "configs", "expanded24.json")
OUT = os.path.join(RT.RESULTS, GROUP)
GOLD = (np.sqrt(5) - 1) / 2


def cls(label):
    return label[0] + label[2]


def response_block(g):
    return [I.index for I in g.isets if (I.player, I.history) in ((1, "B:1"), (2, "B:1-F"), (2, "B:1-C"))]


def p1_open(g):
    return [I.index for I in g.isets if I.player == 0 and I.history == ""]


def br1(g, probs):
    return float(best_response(g, probs, 0)[0])


def set_row(p, i, y):
    p[i, 1] = y
    p[i, 0] = 1.0 - y


def coord_min(g, probs, i):
    """Minimise BR_1 over the single response probability at infoset i (convex in it)."""
    lo, hi = 0.0, 1.0
    def f(y):
        set_row(probs, i, y)
        return br1(g, probs)
    a, b = lo, hi
    c, d = b - GOLD * (b - a), a + GOLD * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(40):
        if fc <= fd:
            b, d, fd = d, c, fc
            c = b - GOLD * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + GOLD * (b - a)
            fd = f(d)
    cands = [(f(0.0), 0.0), (f(1.0), 1.0), (f((a + b) / 2), (a + b) / 2)]
    v, y = min(cands)
    set_row(probs, i, y)
    return v


def deterrence_search(args):
    seed_dir, start = args
    g = RiverGame(json.load(open(CFG)))
    base = load_profile(os.path.join(seed_dir, "policy_avg.json"), g)
    p = base.copy()
    block = response_block(g)
    if start in ("fold", "call", "half"):
        y0 = {"fold": 0.0, "call": 1.0, "half": 0.5}[start]
        for i in block:
            set_row(p, i, y0)
    else:
        rng = np.random.default_rng(int(start[-1]))
        for i in block:
            set_row(p, i, float(rng.uniform()))
    hist, prev = [], br1(g, p)
    for sweep in range(25):
        for i in block:
            coord_min(g, p, i)
        v = br1(g, p)
        hist.append(v)
        if prev - v < 1e-12:
            break
        prev = v
    u1 = float(utilities(g, p)[0])
    return {"seed_dir": seed_dir, "start": start, "br1": hist[-1], "r1_full": hist[-1] - u1, "sweeps": len(hist),
            "history": hist, "responses": {g.isets[i].id: float(p[i, 1]) for i in block}}


def train():
    jobs = [(GROUP, CFG, "dcfr", s, 12000, "P1_open_check") for s in (1, 2, 3)]
    with Pool(3) as pool:
        for out in pool.imap_unordered(RT.run, jobs):
            print("done", out, flush=True)


def analyse():
    g = RiverGame(json.load(open(CFG)))
    dirs = [os.path.join(OUT, "expanded24", "dcfr_s%d" % s) for s in (1, 2, 3)]
    forced = {i: 0 for i in p1_open(g)}
    starts = ["fold", "call", "half", "rand1", "rand2"]
    with Pool(15) as pool:
        searches = pool.map(deterrence_search, [(d, s) for d in dirs for s in starts])
    results = {"design": __doc__, "seeds": []}
    for d in dirs:
        base = load_profile(os.path.join(d, "policy_avg.json"), g)
        restricted = residuals(g, base, forced=forced)
        mine = [s for s in searches if s["seed_dir"] == d]
        best = min(mine, key=lambda s: s["br1"])
        p = base.copy()
        for k, y in best["responses"].items():
            set_row(p, g.iset_by_id[k], y)
        full = residuals(g, p)
        rch = infoset_reach(g, p)["total"]
        block = response_block(g)
        # per P1 hand class: bet value minus best check value (positive = P1 wants to open)
        _, choice, _ = best_response(g, p, 0)
        margins = {}
        for i in p1_open(g):
            pb = p.copy(); set_row(pb, i, 1.0)
            pc = p.copy(); set_row(pc, i, 0.0)
            margins.setdefault(cls(g.isets[i].hand_label), []).append(float(utilities(g, pb)[0] - utilities(g, pc)[0]))
        theta = [I.index for I in g.isets if I.player == 2 and I.history == "B:1-F" and cls(I.hand_label) == "KK"]
        upJJ = [I.index for I in g.isets if I.player == 0 and I.history == "" and cls(I.hand_label) == "JJ"]
        upAA = [I.index for I in g.isets if I.player == 0 and I.history == "" and cls(I.hand_label) == "AA"]
        sweeps = {}
        for tag, up in (("P1_JJ_bet", upJJ), ("P1_AA_bet", upAA)):
            rows = []
            for th in np.linspace(0, 1, 41):
                q = set_theta(g, p, theta, 1, float(th))
                res = residuals(g, q)
                D = upstream_D(g, q, up, 1, 0)
                rb = infoset_reach(g, q)["total"]
                rd = infoset_reach(g, deviate(g, q, up, 1))["total"]
                rows.append({"theta": float(th), "u": [float(x) for x in res["utilities"]],
                             "r": [float(x) for x in res["r"]], "D": [float(x) for x in D],
                             "D_sum": float(sum(D)),
                             "rho_P2": float(-D[1] / D[0]) if abs(D[0]) > 1e-12 else None,
                             "rho_P3": float(-D[2] / D[0]) if abs(D[0]) > 1e-12 else None,
                             "theta_reach_baseline": float(sum(rb[i] for i in theta)),
                             "theta_reach_under_deviation": float(sum(rd[i] for i in theta))})
            ex = normalise_exact(g, to_exact(p, 10 ** 6))
            ra = root_analysis(g, ex, theta, 1, up, 1, 0)
            exr = residuals(g, ex)
            sweeps[tag] = {"rows": rows, "root_exact_profile": ra,
                           "exact_profile_r": [str(x) for x in exr["r"]],
                           "exact_profile_r_float": [float(x) for x in exr["r"]]}
            with open(os.path.join(d, "sweep_%s.csv" % tag), "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["theta", "u1", "u2", "u3", "r1", "r2", "r3", "D1", "D2", "D3", "D_sum", "rho_P2", "rho_P3",
                            "theta_reach_baseline", "theta_reach_under_deviation"])
                for r in rows:
                    w.writerow([r["theta"]] + r["u"] + r["r"] + r["D"] + [r["D_sum"], r["rho_P2"], r["rho_P3"],
                                                                        r["theta_reach_baseline"], r["theta_reach_under_deviation"]])
        results["seeds"].append({
            "dir": os.path.relpath(d, RT.RESULTS).replace("\\", "/"),
            "restricted_game_residuals": [float(x) for x in restricted["r"]],
            "restricted_nashconv": float(restricted["nashconv"]),
            "deterrence_search": [{k: s[k] for k in ("start", "br1", "r1_full", "sweeps")} for s in mine],
            "best_start": best["start"], "full_game_residuals_at_best": [float(x) for x in full["r"]],
            "full_nashconv_at_best": float(full["nashconv"]),
            "response_block_reach_max": float(max(rch[i] for i in block)),
            "P1_bet_minus_check_by_class": {k: [min(v), max(v)] for k, v in sorted(margins.items())},
            "best_response_block_by_class": _by_class(g, best["responses"]),
            "sweeps": sweeps})
        print(d, "restricted NC %.2e" % restricted["nashconv"], "| best deterrence r1(full) %.4e (start %s)" % (
            best["r1_full"], best["start"]), "| margins", {k: round(max(v), 4) for k, v in margins.items()})
    json.dump(results, open(os.path.join(OUT, "op2_results.json"), "w"), indent=1)


def _by_class(g, responses):
    out = {}
    for k, y in responses.items():
        I = g.isets[g.iset_by_id[k]]
        out.setdefault("P%d|%s|%s" % (I.player + 1, cls(I.hand_label), I.history), []).append(y)
    return {k: [round(min(v), 4), round(max(v), 4)] for k, v in sorted(out.items())}


if __name__ == "__main__":
    {"train": train, "analyse": analyse}[sys.argv[1]]()
