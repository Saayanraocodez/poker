"""Pot sweep (preregistration amendment 2): the prior contribution c (pot 3c) at which P1's opening
silence, and with it the exact off-path pole witnesses of the pot-1.5 game, give way to P1 opening.

Reads the trained profiles and the declared analysis (scripts/analyze_profiles.py potsweep,
scripts/theory_checks.py t8); recomputes nothing in float.

certify   every profile of results/potsweep/ plus the reused end points (panel pot 1.5 = c 1/2,
          pilot DCFR = c 1, panel pot 6 = c 2): rationalise (limit_denominator 10^6 per entry, rows
          renormalised exactly), exact residuals and utilities, exact P1 opening probabilities and
          P2's bet after P1 checks, the declared classification, and an exact re-check of EVERY
          class-level witness of the declared scan (root, numerator, residuals at theta*)
          -> results/potsweep/certification.json, certification.csv
train     DCFR on named configs (refinement points), or the declared 48,000-iteration continuation
          into a separate group (checkpoints copied, the 12,000-iteration profiles kept)
summary   per contribution: status (SILENT / NON-SILENT / MIXED), the threshold bracket and, if it
          is wider than 1/256, the next refinement points -> results/potsweep/threshold.json
plot      results/plots/potsweep_threshold.png

usage:  python scripts/potsweep.py train <iterations> <group> <config names...>
        python scripts/potsweep.py certify|summary|plot [workers]
"""
import csv
import glob
import json
import os
import sys
from fractions import Fraction as F
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from analyze_profiles import RESULTS, exact_check, find_config, hand_class   # noqa: E402
from hinc.bestresponse import residuals                                     # noqa: E402
from hinc.game import RiverGame                                             # noqa: E402
from hinc.strategy import load_profile, normalise_exact, to_exact           # noqa: E402

OUT = os.path.join(RESULTS, "potsweep")
OPEN_MIN = 1e-3            # declared: OPENING iff some hand class opens with float probability >= 1e-3
REUSED = ["panel/pot_pot1.5_JJAA24/dcfr_s*", "pilot/expanded24/dcfr_s*", "panel/pot_pot6_JJAA24/dcfr_s*"]


def run_dirs():
    ds = sorted(glob.glob(os.path.join(RESULTS, "potsweep", "*", "*", "run.json")))
    ds += sorted(glob.glob(os.path.join(RESULTS, "potsweep_48k", "*", "*", "run.json")))
    for pat in REUSED:
        ds += sorted(glob.glob(os.path.join(RESULTS, pat, "run.json")))
    return [os.path.dirname(d) for d in ds]


def by_class(g, p, player, history, exact=False):
    """Mean aggressive probability per hand class at (player, history)."""
    acc = {}
    for I in g.isets:
        if I.player == player and I.history == history:
            acc.setdefault(hand_class(I.hand_label), []).append(p[I.index, 1])
    if exact:
        return {k: str(sum(v) / len(v)) for k, v in sorted(acc.items())}
    return {k: float(np.mean([float(x) for x in v])) for k, v in sorted(acc.items())}


def certify_one(d):
    a = json.load(open(os.path.join(d, "analysis.json")))
    g = RiverGame(find_config(a["game"]["name"]))
    c = g.rules.prior_contrib[0]
    probs = load_profile(os.path.join(d, "policy_avg.json"), g)
    ex = normalise_exact(g, to_exact(probs, 10 ** 6))
    res = residuals(g, ex)
    p1 = [I.index for I in g.isets if I.player == 0 and I.history == ""]
    p1_exact_zero = all(ex[i, 1] == 0 for i in p1)
    r_zero = all(x == 0 for x in res["r"])
    open_cls = a["P1_open_prob_by_class"]
    if p1_exact_zero and r_zero:
        status = "CERTIFIED SILENT"
    elif a["selected"] and max(open_cls.values()) >= OPEN_MIN:
        status = "OPENING"
    else:
        status = "UNRESOLVED"
    rec = {"run": a["run"], "game": a["game"]["name"], "contribution": str(c), "pot": str(3 * c),
           "pot_float": float(3 * c), "seed": a["seed"], "iterations": a["iterations"],
           "nashconv": a["nashconv"], "r": a["r"], "selected": a["selected"], "utilities": a["utilities"],
           "P1_open_by_class": open_cls, "P2_bet_after_check_by_class": by_class(g, probs, 1, "K"),
           "P3_bet_after_two_checks_by_class": by_class(g, probs, 2, "K-K"),
           "P1_call_vs_P3_bet_by_class": by_class(g, probs, 0, "K-K-B:1"),
           "reach_census": a["reach_census"],
           "rational": {"rule": "limit_denominator(10^6) per entry, last action absorbs rounding",
                        "exact_r": [str(x) for x in res["r"]], "exact_r_float": [float(x) for x in res["r"]],
                        "exact_utilities": [str(x) for x in res["utilities"]],
                        "P1_open_exactly_zero_all_hands": p1_exact_zero,
                        "P1_open_exact_distinct": sorted({str(ex[i, 1]) for i in p1}),
                        "P2_bet_after_check_exact_by_class": by_class(g, ex, 1, "K", exact=True)},
           "status": status,
           "witnesses_class": a.get("offpath_class", {}).get("pole_witnesses"),
           "witnesses_combo": a.get("offpath_combo", {}).get("pole_witnesses"),
           "pairs_class": a.get("offpath_class", {}).get("pairs_scanned")}
    # exact re-check of EVERY class-level witness the declared scan found
    lookup = {}
    for I in g.isets:
        lookup.setdefault((hand_class(I.hand_label), I.history), []).append(I.index)
    wits = []
    f = os.path.join(d, "offpath_pairs_class.csv")
    if os.path.exists(f):
        for row in csv.DictReader(open(f)):
            if row["pole_witness"] != "True":
                continue
            w = {"theta": row["theta"], "theta_owner": int(row["theta_owner"]), "theta_history": row["theta_history"],
                 "upstream": row["upstream"], "upstream_player": int(row["upstream_player"]),
                 "upstream_history": row["upstream_history"], "theta_star": float(row["theta_star"]),
                 "D_at_theta_star": json.loads(row["D_at_theta_star"])}
            e = exact_check(g, probs, w, lookup)
            w["exact_ok"] = bool(all(x == "0" for x in e["exact_r"]) and e.get("denominator_zero_exactly")
                                 and e.get("numerator_nonzero_exactly")
                                 and all(x == "0" for x in e.get("r_at_theta_star_exact", ["?"])))
            w["theta_star_exact"] = e.get("theta_star_exact")
            w["r_at_theta_star_exact"] = e.get("r_at_theta_star_exact")
            wits.append(w)
    rec["witnesses"] = wits
    rec["witnesses_exact"] = sum(w["exact_ok"] for w in wits)
    return rec


def certify(workers):
    ds = run_dirs()
    with Pool(min(workers, len(ds))) as pool:
        recs = pool.map(certify_one, ds)
    t8 = json.load(open(os.path.join(RESULTS, "theory", "theory_checks.json"))).get("T8_classification", {})
    for r in recs:
        r["rare_set_kinds"] = t8.get(r["run"], {}).get("zero_or_rare")
    recs.sort(key=lambda r: (F(r["contribution"]), r["run"]))
    os.makedirs(OUT, exist_ok=True)
    json.dump(recs, open(os.path.join(OUT, "certification.json"), "w"), indent=1)
    with open(os.path.join(OUT, "certification.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "contribution", "pot", "seed", "iterations", "nashconv", "status", "P1_open_AA", "P1_open_KK",
                    "P1_open_QQ", "P1_open_JJ", "P2_bet_after_check_max", "exact_r", "rare_set_kinds",
                    "witnesses_class", "witnesses_exact", "witnesses_combo"])
        for r in recs:
            o = r["P1_open_by_class"]
            w.writerow([r["run"], r["contribution"], r["pot"], r["seed"], r["iterations"], "%.3e" % r["nashconv"], r["status"],
                        "%.4g" % o["AA"], "%.4g" % o["KK"], "%.4g" % o["QQ"], "%.4g" % o["JJ"],
                        "%.4g" % max(r["P2_bet_after_check_by_class"].values()), "|".join(r["rational"]["exact_r"]),
                        json.dumps(r["rare_set_kinds"]), r["witnesses_class"], r["witnesses_exact"], r["witnesses_combo"]])
    for r in recs:
        o = r["P1_open_by_class"]
        print("c=%-6s %-48s NC %.2e  %-16s P1 open AA %.3g KK %.3g QQ %.3g JJ %.3g | kinds %s | witnesses %s (exact %d)" % (
            r["contribution"], r["run"], r["nashconv"], r["status"], o["AA"], o["KK"], o["QQ"], o["JJ"],
            r["rare_set_kinds"], r["witnesses_class"], r["witnesses_exact"]))


FLOAT_SILENT = 1e-5        # amendment 3 (secondary, float level): every hand class opens with probability < 1e-5


def merged():
    """certification.json (10^6 rationalisation) joined with polish.json (class-symmetric exact polish,
    amendments 3-4) and polish_silent.json (P1-silent variant, amendment 5)."""
    recs = json.load(open(os.path.join(OUT, "certification.json")))
    for r in recs:
        for key, fn in (("polish", "polish.json"), ("polish_silent", "polish_silent.json")):
            f = os.path.join(RESULTS, r["run"], fn)
            r[key] = json.load(open(f)) if os.path.exists(f) else None
        routes = []
        if r["status"] == "CERTIFIED SILENT":
            routes.append(("rationalisation 10^6", r["witnesses_exact"], "Q"))
        for key, name in (("polish", "class-symmetric polish"), ("polish_silent", "P1-silent polish")):
            if r[key] and r[key]["status"] == "CERTIFIED SILENT":
                routes.append((name, r[key]["exact_witnesses"], r[key].get("field", "Q")))
        r["exact_silent"] = bool(routes)
        r["exact_route"] = routes[0][0] if routes else None
        r["exact_field"] = routes[0][2] if routes else None
        r["exact_witnesses_at_certificate"] = routes[0][1] if routes else None
        r["float_silent"] = max(r["P1_open_by_class"].values()) < FLOAT_SILENT
        r["P2_float_silent"] = max(r["P2_bet_after_check_by_class"].values()) < FLOAT_SILENT
    return recs


def summary():
    recs = merged()
    pts = {}
    for r in recs:
        pts.setdefault(r["contribution"], []).append(r)
    rows = []
    for c in sorted(pts, key=F):
        rs = pts[c]
        if any(r["exact_silent"] for r in rs):
            s = "SILENT"
        elif all(r["status"] == "OPENING" for r in rs):
            s = "NON-SILENT"
        else:
            s = "MIXED/UNRESOLVED"
        fs = ("FLOAT-SILENT" if all(r["float_silent"] for r in rs) else
              "OPENING" if all(r["status"] == "OPENING" for r in rs) else "UNRESOLVED")
        rows.append({"contribution": c, "pot": str(3 * F(c)), "status": s, "float_status": fs,
                     "P2_float_silent": all(r["P2_float_silent"] for r in rs),
                     "exact_routes": sorted({r["exact_route"] for r in rs if r["exact_route"]}),
                     "profiles": [{"run": r["run"], "status_10^6": r["status"],
                                   "polish": r["polish"]["status"] if r["polish"] else None,
                                   "polish_silent": r["polish_silent"]["status"] if r["polish_silent"] else None,
                                   "exact_route": r["exact_route"], "exact_field": r["exact_field"],
                                   "P1_open_max": max(r["P1_open_by_class"].values()),
                                   "witnesses_float_scan": r["witnesses_class"],
                                   "exact_witnesses_at_certificate": r["exact_witnesses_at_certificate"]} for r in rs]})
    doc = {"rule": "SILENT: >= 1 profile with an exact certificate that P1 never opens (10^6 rationalisation or "
                   "class-symmetric polish); NON-SILENT: every profile OPENING (selected, some class opens >= 1e-3); "
                   "bracket = (largest SILENT c below the smallest NON-SILENT c, smallest NON-SILENT c). "
                   "FLOAT-SILENT (secondary, never an exactness claim): every class opens < 1e-5 in every profile.",
           "points": rows}
    for key, fld, good, bad in (("bracket", "status", "SILENT", "NON-SILENT"),
                                ("float_bracket", "float_status", "FLOAT-SILENT", "OPENING")):
        hi = min([F(x["contribution"]) for x in rows if x[fld] == bad], default=None)
        lo = max([F(x["contribution"]) for x in rows if x[fld] == good and (hi is None or F(x["contribution"]) < hi)],
                 default=None)
        if hi is not None and lo is not None:
            doc[key] = {"contribution": [str(lo), str(hi)], "pot": [str(3 * lo), str(3 * hi)],
                        "width": str(hi - lo),
                        "between": [x["contribution"] for x in rows if lo < F(x["contribution"]) < hi],
                        "next_refinement_points": ([str(lo + k * (hi - lo) / 4) for k in (1, 2, 3)]
                                                   if hi - lo > F(1, 256) else [])}
    p2 = [x for x in rows if x["P2_float_silent"]]
    p2n = [x for x in rows if not x["P2_float_silent"]]
    if p2 and p2n:
        hi = min(F(x["contribution"]) for x in p2n)
        lo = max([F(x["contribution"]) for x in p2 if F(x["contribution"]) < hi], default=None)
        doc["P2_float_bracket"] = {"contribution": [str(lo), str(hi)], "pot": [str(3 * lo), str(3 * hi)]}
    json.dump(doc, open(os.path.join(OUT, "threshold.json"), "w"), indent=1)
    for x in rows:
        print("c = %-7s pot = %-8s %-17s %-13s P2 silent %-5s %s" % (
            x["contribution"], x["pot"], x["status"], x["float_status"], x["P2_float_silent"],
            [(p["run"].split("/")[0][-3:], p["status_10^6"][:4], p["polish"], p["polish_silent"], "%.1e" % p["P1_open_max"],
              p["witnesses_float_scan"], p["exact_witnesses_at_certificate"]) for p in x["profiles"]]))
    print({k: v for k, v in doc.items() if k not in ("points", "rule")})


def table():
    """Markdown rows for FINDINGS.md, one per contribution, from the merged records (ASCII only)."""
    recs = merged()
    pts, k48 = {}, {}
    for r in recs:
        (k48 if r["run"].startswith("potsweep_48k") else pts).setdefault(F(r["contribution"]), []).append(r)

    def rng(xs, f="%.1e"):
        a, b = f % min(xs), f % max(xs)
        return a if a == b else a + " to " + b

    print("| c | pot | P1 opens (DCFR, max class) | P2 bets AA after check (DCFR) | NashConv | rare sets (T8) | "
          "float-scan witnesses | exact P1-silent certificate | exact witnesses |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in sorted(pts):
        rs = pts[c]
        cert = [r for r in rs + k48.get(c, []) if r["exact_silent"]]
        fields = sorted({r["exact_field"] for r in cert})
        n12 = sum(1 for r in rs if r["exact_silent"])
        cs = "%d/%d seeds" % (n12, len(rs))
        if c in k48:
            cs += "; 48k: %d/%d" % (sum(1 for r in k48[c] if r["exact_silent"]), len(k48[c]))
        if fields:
            cs += " (%s)" % ", ".join(f.replace("Q(sqrt(", "Q(sqrt ").replace("))", ")") for f in fields)
        kinds = sorted({", ".join("%d %s" % (v, k) for k, v in sorted((r["rare_set_kinds"] or {}).items())) for r in rs})
        we = [r["exact_witnesses_at_certificate"] for r in cert]
        print("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            c, 3 * c, rng([max(r["P1_open_by_class"].values()) for r in rs]),
            rng([r["P2_bet_after_check_by_class"]["AA"] for r in rs], "%.2g"), rng([r["nashconv"] for r in rs]),
            "; ".join(kinds) or "-", rng([r["witnesses_class"] or 0 for r in rs], "%d"),
            cs if cert else "none", rng(we, "%d") if we else "-"))


def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    recs = [r for r in merged() if r["pot_float"] <= 3]
    thr = json.load(open(os.path.join(OUT, "threshold.json")))
    ink, ink2, blue, orange = "#0b0b0b", "#52514e", "#2a78d6", "#eb6834"      # validated palette, fixed order
    FLOOR = 1e-9
    fig, ax = plt.subplots(2, 1, figsize=(7.6, 6.4), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    xs = sorted({r["pot_float"] for r in recs})
    for key, col, lab in (("P1_open_by_class", blue, "P1 opens (max over hand classes)"),
                          ("P2_bet_after_check_by_class", orange, "P2 bets after P1 checks (max over classes)")):
        y = [max(max(r[key].values()), FLOOR) for r in recs]
        ax[0].semilogy([r["pot_float"] for r in recs], y, "o", ms=4, color=col, alpha=0.55, mec="white", mew=0.5)
        med = [float(np.median([max(max(r[key].values()), FLOOR) for r in recs if r["pot_float"] == x])) for x in xs]
        ax[0].semilogy(xs, med, "-", lw=1.8, color=col, label=lab)
    cert = sorted({r["pot_float"] for r in recs if r["exact_silent"]})
    ax[0].plot(cert, [2 * FLOOR] * len(cert), "v", ms=7, color=ink, label="exact certificate: P1 never opens")
    ax[0].axhline(FLOAT_SILENT, color=ink2, lw=0.8, ls=":")
    ax[0].text(1.47, FLOAT_SILENT * 1.6, "float-silent level 1e-5", fontsize=7, color=ink2)
    ax[0].set_ylim(FLOOR, 3)
    ax[0].set_ylabel("probability (DCFR average strategy)")
    ax[0].legend(fontsize=7, loc="upper left")
    ax[1].plot([r["pot_float"] for r in recs], [r["witnesses_class"] or 0 for r in recs], "o", ms=6, mfc="none",
               color=ink2, label="witnesses found by the declared float scan (per profile)")
    ex = [r for r in recs if r["exact_witnesses_at_certificate"] is not None]
    ax[1].plot([r["pot_float"] for r in ex], [r["exact_witnesses_at_certificate"] for r in ex], "o", ms=3.5, color=ink,
               label="exact witnesses at the certified exact equilibrium")
    ax[1].set_ylabel("class-level pole witnesses")
    ax[1].set_xlabel("pot before the river (bb) = 3 x prior contribution;  stack = bet = 1 bb")
    ax[1].legend(fontsize=7, loc="upper right")
    if thr.get("bracket"):
        lo, hi = (float(F(x)) for x in thr["bracket"]["pot"])
        for a in ax:
            a.axvspan(lo, hi, color="#c3c2b7", alpha=0.6, lw=0)
        ax[0].annotate("silent certified at pot %s;\nevery DCFR seed opens at %s" % tuple(thr["bracket"]["pot"]),
                       xy=(lo, 3e-3), xytext=(2.935, 3e-3), fontsize=7, color=ink2, va="center", ha="right",
                       arrowprops={"arrowstyle": "->", "color": ink2, "lw": 0.8})
    dcfr = [q for q in recs if not q["run"].startswith("potsweep_48k")]
    p2_on = min(F(r["contribution"]) for r in dcfr
                if all(q["P2_bet_after_check_by_class"]["AA"] >= OPEN_MIN for q in dcfr if q["contribution"] == r["contribution"]))
    for a in ax:
        a.axvline(float(3 * p2_on), color=orange, lw=0.9, ls="--")
    ax[0].text(float(3 * p2_on) + 0.015, 2e-2, "P2 bets in every\nDCFR seed from\npot %s" % (3 * p2_on), fontsize=7, color=orange, va="top")
    for a in ax:
        a.grid(alpha=0.3)
    ax[1].set_xlim(1.4, 3.1)
    fig.suptitle("24-hand JJ-AA river game: P1's opening silence and the exact off-path poles vs pot\n"
                 "DCFR averages, 3 seeds x 12k and 48k iterations (pot 3: pilot, 6 x 30k)", fontsize=8.5)
    fig.tight_layout()
    os.makedirs(os.path.join(RESULTS, "plots"), exist_ok=True)
    fig.savefig(os.path.join(RESULTS, "plots", "potsweep_threshold.png"), dpi=140)
    plt.close(fig)


# --- class-symmetric polish (amendment 3) -----------------------------------------------------
# The game is invariant under the 24 suit permutations (no flush is possible, no hole card meets the
# board), so a profile in which every combo of a hand class plays alike is a 4-type profile.  The
# construction below is a heuristic; the certificate is the exact full best-response check.
SNAP = 1e-4                # on-path class rows below SNAP (above 1 - SNAP) are snapped to 0 (1)
TOL_LADDER = [F(1, 10 ** e) for e in (3, 4, 5, 6)]   # free directions / off-path rows: simplest rational
                                                     # within tol of DCFR, first tol that certifies
MAX_UNKNOWNS = 12
METHOD_VERSION = 3         # 1: rational solutions, tol 1e-3 only (amendment 3); 2: + Q(sqrt d), ladder (amendment 4);
                           # 3: P1-silent variant chooses the responses to P1's bet by a deterrence search (amendment 6)
DETER_STARTS = 48          # amendment 6: alternating-LP starts (the DCFR averages first, then seeded random points)


def simplest(lo, hi):
    """The simplest rational (smallest denominator) in [lo, hi], 0 <= lo <= hi."""
    fl = lo.numerator // lo.denominator
    if lo == fl:
        return F(fl)
    if fl + 1 <= hi:
        return F(fl + 1)
    return fl + 1 / simplest(1 / (hi - fl), 1 / (lo - fl))


def near(x, tol):
    x = F(x)
    return simplest(max(F(0), x - tol), min(F(1), x + tol))


def class_rows(g):
    rows = {}
    for I in g.isets:
        assert len(I.actions) == 2
        rows.setdefault((I.player, I.history, hand_class(I.hand_label)), []).append(I.index)
    return rows


def build(g, rows, val, exact=True):
    """Profile with every combo of class row k betting/calling with probability val[k]."""
    one = F(1) if exact else 1.0
    p = np.full((g.n_isets, g.max_actions), F(0) if exact else 0.0, dtype=object if exact else float)
    for k, idx in rows.items():
        for i in idx:
            p[i, 1] = val[k]
            p[i, 0] = one - val[k]
    return p


def class_D(g, p, idx):
    """Exact D = U(class row -> aggressive) - U(class row -> passive).  The combos of one class row
    never share a deal, so this equals the sum of the per-combo transfer derivatives."""
    from hinc.evaluate import utilities
    a, b = p.copy(), p.copy()
    for i in idx:
        a[i, 1], a[i, 0] = F(1), F(0)
        b[i, 1], b[i, 0] = F(0), F(1)
    return utilities(g, a) - utilities(g, b)


def solve_unknowns(g, rows, val, unknown):
    """Exact solution set of the indifference conditions of the mixed on-path class rows.  Utilities
    are multilinear in the class variables, so each owner's utility is recovered exactly from its
    values at the 2^m vertices (Moebius transform), and the condition for row j is dU_owner/dx_j = 0.
    Returns sympy's (possibly parametric) solutions."""
    import itertools
    import sympy
    from hinc.evaluate import utilities
    m = len(unknown)
    xs = sympy.symbols("x0:%d" % m)
    verts = list(itertools.product((0, 1), repeat=m))
    U = {}
    for v in verts:
        vv = dict(val)
        for j, k in enumerate(unknown):
            vv[k] = F(v[j])
        U[v] = utilities(g, build(g, rows, vv))
    eqs = []
    for j, k in enumerate(unknown):
        X = k[0]
        coef = {v: U[v][X] for v in verts}                     # Moebius transform -> monomial coefficients
        for b in range(m):
            for v in verts:
                if v[b] == 1:
                    coef[v] = coef[v] - coef[tuple(0 if t == b else v[t] for t in range(m))]
        expr = sympy.Integer(0)
        for v, cf in coef.items():
            if cf != 0 and v[j] == 1:                          # d/dx_j of the multilinear polynomial
                term = sympy.Rational(cf.numerator, cf.denominator)
                for t in range(m):
                    if v[t] and t != j:
                        term *= xs[t]
                expr += term
        eqs.append(sympy.expand(expr))
    sols = sympy.solve([e for e in eqs if e != 0], xs, dict=True)
    return sols, xs, [str(e) for e in eqs]


def to_exact_number(e):
    """A sympy number -> Fraction, or Surd if it lies in a single real quadratic field; else None."""
    import sympy
    from hinc.surd import Surd
    e = sympy.expand(sympy.radsimp(sympy.simplify(e)))
    if e.is_Rational:
        return F(int(e.p), int(e.q))
    roots = {a for a in e.atoms(sympy.Pow) if a.exp == sympy.Rational(1, 2) and a.base.is_Integer}
    if len(roots) != 1 or not e.is_real:
        return None
    r = roots.pop()
    b = e.coeff(r)
    a = sympy.expand(e - b * r)
    if not (a.is_Rational and b.is_Rational):
        return None
    return Surd(F(int(a.p), int(a.q)), F(int(b.p), int(b.q)), int(r.base))


def realise(sols, xs, unknown, start, tol):
    """Pick the solution branch closest to the DCFR class averages, with every free direction fixed at
    the simplest rational within tol of DCFR; values must be exact numbers (Q or one Q(sqrt d)) in [0,1]."""
    import sympy
    best = None
    for s in sols:
        free = {x: sympy.Rational(near(start[unknown[t]], tol).numerator, near(start[unknown[t]], tol).denominator)
                for t, x in enumerate(xs) if x not in s}
        vals, fields = [], set()
        for t, x in enumerate(xs):
            v = to_exact_number(free[x] if x in free else s[x].subs(free))
            if v is None or v < 0 or v > 1:
                vals = None
                break
            if getattr(v, "b", 0) != 0:
                fields.add(v.d)
            vals.append(v)
        if vals is None or len(fields) > 1:
            continue
        dist = max(abs(float(vals[t]) - start[unknown[t]]) for t in range(len(xs)))
        if best is None or dist < best[0]:
            best = (dist, vals, [str(x) for x in free], sorted(fields))
    return best


def exact_scan(g, ex, rows):
    """The declared class-level scan, in exact arithmetic, on an exact profile: every unreached class
    row theta (binary) against every class row of another player whose aggressive action leads into
    theta's history.  Witness iff C_A != 0, theta* in [0,1], D_A(theta*) = 0 with a nonzero
    numerator, and exact residuals (0,0,0) at theta* (with (0,0,0) at the baseline, Theorem 6 makes
    the whole segment Nash, and D_A > 0 beyond theta*, so theta* is the window's endpoint)."""
    from hinc.evaluate import infoset_reach
    from hinc.offpath import set_theta
    rch = infoset_reach(g, ex)["total"]
    creach = {k: sum(rch[i] for i in idx) for k, idx in rows.items()}
    hist_aggr = {nd.history: nd.actions[1] for nd in g.tree.decision_nodes}
    out = []
    for tk, tidx in sorted(rows.items()):
        if creach[tk] != 0:
            continue
        for uk, uidx in sorted(rows.items()):
            if uk[0] == tk[0]:
                continue
            pre = (uk[1] + "-" + hist_aggr[uk[1]]) if uk[1] else hist_aggr[uk[1]]
            if not (tk[1] == pre or tk[1].startswith(pre + "-")):
                continue
            A = uk[0]
            D0 = class_D(g, set_theta(g, ex, tidx, 1, F(0)), uidx)
            D1 = class_D(g, set_theta(g, ex, tidx, 1, F(1)), uidx)
            C = D1 - D0
            rec = {"theta": tk[2], "theta_owner": tk[0] + 1, "theta_history": tk[1], "theta_value": str(ex[tidx[0], 1]),
                   "upstream": uk[2], "upstream_player": A + 1, "upstream_history": uk[1],
                   "cross": [str(x) for x in C], "cross_float": [float(x) for x in C], "witness": False}
            if C[A] != 0:
                ts = -D0[A] / C[A]
                rec["theta_star"] = str(ts)
                rec["theta_star_float"] = float(ts)
                if 0 <= ts <= 1:
                    num = D0 + ts * C
                    rec["D_at_theta_star"] = [str(x) for x in num]
                    rec["D_at_theta_star_float"] = [float(x) for x in num]
                    if any(num[X] != 0 for X in range(g.n) if X != A):
                        r = residuals(g, set_theta(g, ex, tidx, 1, ts))["r"]
                        rec["r_at_theta_star"] = [str(x) for x in r]
                        rec["witness"] = all(x == 0 for x in r)
            out.append(rec)
    return out


def deterrence(g, rows, val, start):
    """Amendment 6.  P1 never opens; the 12 responses to P1's all-in (P2 at B:1, P3 at B:1-F and B:1-C,
    one per hand class) are unreached, so they matter only through P1's gain from opening,
    gain_k(y) = sum over deals with P1 in class k of prior x (V_P1(class k bets) - V_P1(checks)),
    which is bilinear in y (P2's call times P3's call).  Maximise t subject to gain_k(y) <= -t for all
    four classes by alternating LPs (y_P2 fixed: affine in y_P3; y_P3 fixed: affine in y_P2), in
    float -- a search only; whatever it returns is rounded and certified exactly by the caller."""
    from scipy.optimize import linprog
    from hinc.evaluate import values
    P2 = [k for k in sorted(rows) if k[0] == 1 and k[1] == "B:1"]
    P3 = [k for k in sorted(rows) if k[0] == 2 and k[1] in ("B:1-F", "B:1-C")]
    opens = [k for k in sorted(rows) if k[0] == 0 and k[1] == ""]
    cls_of_hand = np.array([["AA", "JJ", "KK", "QQ"].index(hand_class(l)) for l in g.seats[0].labels])
    hand = cls_of_hand[g.deals[:, 0]]
    base = {k: float(v) for k, v in val.items()}
    v0 = values(g, build(g, rows, base, exact=False))[0][:, 0]

    def gain(y):
        vv = dict(base)
        vv.update(y)
        for k in opens:
            vv[k] = 1.0
        v1 = values(g, build(g, rows, vv, exact=False))[0][:, 0]
        return np.bincount(hand, weights=g.prior_f * (v1 - v0), minlength=4)

    def lp(free, fixed):
        """max t s.t. gain(fixed + free) <= -t, gain affine in the free block."""
        y0 = dict(fixed)
        y0.update({k: 0.0 for k in free})
        g0 = gain(y0)
        A = []
        for k in free:
            y1 = dict(y0)
            y1[k] = 1.0
            A.append(gain(y1) - g0)
        A = np.array(A).T                                    # 4 x len(free)
        # variables (y_free..., t): minimise -t;  A y + t <= -g0
        res = linprog(np.r_[np.zeros(len(free)), -1.0], A_ub=np.c_[A, np.ones(4)], b_ub=-g0,
                      bounds=[(0, 1)] * len(free) + [(None, None)], method="highs")
        return {k: float(x) for k, x in zip(free, res.x[:-1])}, float(res.x[-1])

    rng = np.random.default_rng(20261017)
    best = None
    for s_ in range(DETER_STARTS):
        y = {k: (start[k] if s_ == 0 else float(rng.random())) for k in P2 + P3}
        t_old = -np.inf
        for _ in range(30):
            y3, t = lp(P3, {k: y[k] for k in P2})
            y.update(y3)
            y2, t = lp(P2, {k: y[k] for k in P3})
            y.update(y2)
            if t - t_old < 1e-13:
                break
            t_old = t
        if best is None or t > best[0]:
            best = (t, dict(y))
    return best


def class_averages(d):
    """DCFR class averages of a run, keyed (player, history, class) -- the same keys at every c."""
    run = json.load(open(os.path.join(d, "run.json")))
    g = RiverGame(find_config(run["game"]["name"]))
    probs = load_profile(os.path.join(d, "policy_avg.json"), g)
    return {k: float(np.mean([probs[i, 1] for i in idx])) for k, idx in class_rows(g).items()}


def polish_one(d, source=None, silent=False):
    """Version-2 polish of run d.  With silent=True (amendment 5) P1's opening class rows are set to
    exactly 0 whatever DCFR did, and the class averages are taken from the run ``source`` (the same
    seed at a lower contribution on the silent branch) instead of d.  Output polish[_silent].json."""
    from hinc.evaluate import infoset_reach
    from hinc.strategy import save_profile
    tag = "_silent" if silent else ""
    cached = os.path.join(d, "polish%s.json" % tag)
    src = source or d
    if os.path.exists(cached) and os.path.getmtime(cached) >= os.path.getmtime(os.path.join(src, "policy_avg.json")):
        c = json.load(open(cached))
        if c.get("method_version") == METHOD_VERSION or c["status"].startswith("CERTIFIED"):
            return c                                 # a version-1 certificate is the ladder's first rung
    run = json.load(open(os.path.join(d, "run.json")))
    g = RiverGame(find_config(run["game"]["name"]))
    rows = class_rows(g)
    avg = class_averages(src)
    if silent:
        for k in rows:
            if k[0] == 0 and k[1] == "":
                avg[k] = 0.0
    pf = build(g, rows, avg, exact=False)
    nc_sym = float(residuals(g, pf)["nashconv"])
    rch = infoset_reach(g, pf)["total"]
    from hinc import plan
    val, unknown, off = {}, [], []
    for k, idx in rows.items():
        on_path = float(sum(rch[i] for i in idx)) > plan.REACH_RARE
        if on_path and avg[k] < SNAP:
            val[k] = F(0)
        elif on_path and avg[k] > 1 - SNAP:
            val[k] = F(1)
        elif on_path:
            unknown.append(k)
        else:
            off.append(k)
            val[k] = near(avg[k], TOL_LADDER[0])
    rec = {"run": os.path.relpath(d, RESULTS).replace("\\", "/"), "contribution": str(g.rules.prior_contrib[0]),
           "method_version": METHOD_VERSION, "variant": "P1-silent (amendment 5)" if silent else "default",
           "source": os.path.relpath(src, RESULTS).replace("\\", "/"),
           "dcfr_nashconv": run["final"]["avg"]["nashconv"], "symmetrised_float_nashconv": nc_sym,
           "unknowns": ["P%d %s %s" % (k[0] + 1, k[1] or "(open)", k[2]) for k in unknown],
           "rule": "class average; on-path rows snapped at %g; mixed on-path rows solved exactly (Q or one Q(sqrt d)); "
                   "free directions and off-path rows: simplest rational within tol of the DCFR class average, "
                   "tol = 1e-3, 1e-4, 1e-5, 1e-6 until certified" % SNAP}
    if len(unknown) > MAX_UNKNOWNS:
        rec["status"] = "too many unknowns"
        json.dump(rec, open(cached, "w"), indent=1)
        return rec
    sols, xs, eqs = solve_unknowns(g, rows, val, unknown)
    rec["equations"] = eqs
    rec["attempts"] = []
    ex, det = None, None
    for tol in TOL_LADDER:
        best = realise(sols, xs, unknown, avg, tol)
        if best is None:
            rec["attempts"].append({"tol": str(tol), "status": "no exact solution in [0,1]"})
            continue
        dist, vals, free, fields = best
        for k in off:
            val[k] = near(avg[k], tol)
        for k, v in zip(unknown, vals):
            val[k] = v
        if silent:                                   # amendment 6: choose the responses to P1's bet
            if det is None:
                det = deterrence(g, rows, val, avg)
                rec["deterrence"] = {"float_margin_bb": det[0],
                                     "responses": {"P%d %s %s" % (k[0] + 1, k[1], k[2]): x for k, x in det[1].items()},
                                     "rule": "max min_k (-gain_k) over the 12 responses to P1's bet; alternating "
                                             "LPs from %d starts (float search, exact certificate)" % DETER_STARTS}
            for k, x in det[1].items():
                val[k] = near(x, tol)
        ex = build(g, rows, val)
        res = residuals(g, ex)
        cert = all(x == 0 for x in res["r"])
        rec["attempts"].append({"tol": str(tol), "status": "certified" if cert else "not certified",
                                "exact_r_float": [float(x) for x in res["r"]]})
        if cert:
            break
    if ex is None:
        rec["status"] = "no exact solution in [0,1]"
        json.dump(rec, open(cached, "w"), indent=1)
        return rec
    rec["tol"] = rec["attempts"][-1]["tol"]
    rec["field"] = "Q" if not fields else "Q(sqrt(%d))" % fields[0]
    rec["solution"] = {"P%d %s %s" % (k[0] + 1, k[1] or "(open)", k[2]): str(v) for k, v in zip(unknown, vals)}
    rec["solution_float"] = {"P%d %s %s" % (k[0] + 1, k[1] or "(open)", k[2]): float(v) for k, v in zip(unknown, vals)}
    rec["free_fixed"] = free
    rec["max_shift_from_dcfr"] = dist
    p1_zero = all(val[k] == 0 for k in rows if k[0] == 0 and k[1] == "")
    rec.update({"exact_r": [str(x) for x in res["r"]], "exact_r_float": [float(x) for x in res["r"]],
                "exact_utilities": [str(x) for x in res["utilities"]], "P1_open_exactly_zero": p1_zero,
                "P2_bet_after_check": {k[2]: str(val[k]) for k in sorted(rows) if k[0] == 1 and k[1] == "K"},
                "P3_bet_after_two_checks": {k[2]: str(val[k]) for k in sorted(rows) if k[0] == 2 and k[1] == "K-K"}})
    rec["status"] = ("CERTIFIED SILENT" if p1_zero else "CERTIFIED, P1 OPENS") if cert else "NOT CERTIFIED"
    if cert:
        save_profile(os.path.join(d, "policy_exact%s.json" % tag), g, ex,
                     extra={"which": "class-symmetric exact polish of policy_avg.json (scripts/potsweep.py polish)",
                            "number_field": rec["field"], "exact_r": rec["exact_r"]})
        scan_rows = exact_scan(g, ex, rows)
        rec["exact_scan_pairs"] = len(scan_rows)
        rec["exact_witnesses"] = sum(r["witness"] for r in scan_rows)
        rec["witnesses"] = [r for r in scan_rows if r["witness"]]
        rec["scan"] = scan_rows
    json.dump(rec, open(cached, "w"), indent=1)
    return rec


def silent_source(d):
    """Amendment 5: the same seed's DCFR run at the same c if P1 opens < 1e-2 with every class there,
    else at the nearest lower sweep contribution where it does (a continuation of the silent branch)."""
    seed = os.path.basename(d)
    cands = []
    for rj in glob.glob(os.path.join(RESULTS, "potsweep", "*", seed, "run.json")):
        dd = os.path.dirname(rj)
        a = json.load(open(os.path.join(dd, "analysis.json")))
        cands.append((F(json.load(open(rj))["game"]["betting"]["prior_contrib"][0]), dd,
                      max(a["P1_open_prob_by_class"].values())))
    c0 = F(json.load(open(os.path.join(d, "run.json")))["game"]["betting"]["prior_contrib"][0])
    ok = sorted([(c, dd) for c, dd, m in cands if c <= c0 and m < 1e-2], key=lambda x: x[0])
    return ok[-1][1] if ok else None


def _silent_job(d):
    return polish_one(d, source=silent_source(d), silent=True)


def polish_silent(cmin, workers):
    """Amendment 5: the P1-silent variant on every potsweep run with c >= cmin whose default polish
    did not certify a P1-silent equilibrium."""
    ds = []
    for rj in sorted(glob.glob(os.path.join(RESULTS, "potsweep", "*", "*", "run.json"))):
        d = os.path.dirname(rj)
        c = F(json.load(open(rj))["game"]["betting"]["prior_contrib"][0])
        pj = os.path.join(d, "polish.json")
        done = os.path.exists(pj) and json.load(open(pj))["status"] == "CERTIFIED SILENT"
        if c >= cmin and not done:
            ds.append(d)
    with Pool(min(workers, len(ds))) as pool:
        recs = pool.map(_silent_job, ds)
    recs.sort(key=lambda r: (F(r["contribution"]), r["run"]))
    for r in recs:
        print("c=%-8s %-46s source %-46s %-18s %s exact r %s witnesses %s" % (
            r["contribution"], r["run"], r["source"], r["status"], r.get("field"),
            ["%.1e" % x for x in r.get("exact_r_float", [])], r.get("exact_witnesses")))


def polish(group, workers):
    ds = sorted(os.path.dirname(x) for x in glob.glob(os.path.join(RESULTS, group, "*", "*", "run.json")))
    with Pool(min(workers, len(ds))) as pool:
        recs = pool.map(polish_one, ds)
    recs.sort(key=lambda r: (F(r["contribution"]), r["run"]))
    json.dump([{k: v for k, v in r.items() if k not in ("scan", "equations")} for r in recs],
              open(os.path.join(RESULTS, group, "polish_summary.json"), "w"), indent=1)
    for r in recs:
        print("c=%-6s %-46s %-18s unknowns %d  sym NC %.1e  exact r %s  witnesses %s" % (
            r["contribution"], r["run"], r["status"], len(r["unknowns"]), r["symmetrised_float_nashconv"],
            ["%.1e" % x for x in r.get("exact_r_float", [])], r.get("exact_witnesses")))


def train(argv):
    """train <iterations> <group> <config name> ...   DCFR seeds 1-3 (plan.POTSWEEP) on the named configs.
    A group other than 'potsweep' starting from an existing potsweep run copies its checkpoint first
    (the declared continuation), so the 12,000-iteration profile stays where it was."""
    import shutil
    from run_training import run
    from hinc import plan
    iters, group, names = int(argv[0]), argv[1], argv[2:]
    jobs = []
    for nm in names:
        for s in plan.POTSWEEP["seeds"]:
            src = os.path.join(RESULTS, "potsweep", nm, "dcfr_s%d" % s)
            dst = os.path.join(RESULTS, group, nm, "dcfr_s%d" % s)
            if group != "potsweep" and not os.path.exists(os.path.join(dst, "ckpt.json")):
                os.makedirs(dst, exist_ok=True)
                for f in ("ckpt.json", "ckpt.npz", "log.txt"):
                    shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
            jobs.append((group, os.path.join(ROOT, "configs", "potsweep", nm + ".json"), "dcfr", s, iters))
    with Pool(min(26, len(jobs))) as pool:
        for d, nc, wall in pool.imap_unordered(run, jobs):
            print("done %-50s NashConv(avg) %.3e  %.0fs" % (d, nc, wall), flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "train":
        train(sys.argv[2:])
    elif cmd == "polish_silent":
        polish_silent(F(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 12)
    elif cmd == "polish":
        polish(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 12)
    elif cmd == "certify":
        certify(int(sys.argv[2]) if len(sys.argv) > 2 else 12)
    elif cmd == "summary":
        summary()
    elif cmd == "table":
        table()
    elif cmd == "plot":
        plot()
    else:
        raise SystemExit(__doc__)
