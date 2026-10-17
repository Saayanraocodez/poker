"""Independent re-check of every stored pot-sweep certificate (does not use scripts/potsweep.py).

For each results/potsweep*/<game>/<run>/policy_exact*.json: parse the exact profile from its text
(Fractions, or a + b*sqrt(d) in one real quadratic field), check every row is a probability vector
exactly, recompute the exact full best-response residuals (must be (0,0,0)), check P1's opening is
exactly 0 for all 24 hands and the utilities sum to 0.  Then re-derive the first stored witness from
scratch with hinc.offpath.upstream_D (the per-combo sum, not the polish's joint class move): theta*
from D_A(0) and D_A(1), D_A(theta*) = 0, a nonzero numerator, and exact residuals (0,0,0) at theta*.

usage:  python scripts/verify_potsweep.py [workers]   ->  results/potsweep/verify.json
"""
import glob
import json
import os
import sys
from fractions import Fraction
from multiprocessing import Pool

import numpy as np

HI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HI)
from hinc.bestresponse import residuals              # noqa: E402
from hinc.game import RiverGame                      # noqa: E402
from hinc.offpath import set_theta, upstream_D       # noqa: E402
from hinc.surd import parse                          # noqa: E402

RES = os.environ.get("HINC_RESULTS", os.path.join(HI, "results"))


def config_named(name):
    for f in glob.glob(os.path.join(HI, "configs", "*", "*.json")):
        c = json.load(open(f))
        if c.get("name") == name:
            return c
    raise KeyError(name)


def load_exact(path):
    doc = json.load(open(path))
    g = RiverGame(config_named(doc["game"]["name"]))
    assert doc["game"]["fingerprint"] == g.fingerprint(), "fingerprint mismatch"
    p = np.full((g.n_isets, g.max_actions), Fraction(0), dtype=object)
    for row in doc["infosets"]:
        i = g.iset_by_id[row["id"]]
        assert tuple(row["actions"]) == g.isets[i].actions
        for a, x in enumerate(row["probs"]):
            p[i, a] = parse(x)
    for I in g.isets:
        k = len(I.actions)
        assert sum(p[I.index, a] for a in range(k)) == 1, I.id
        assert all(0 <= p[I.index, a] <= 1 for a in range(k)), I.id
    return g, p, doc


def check(path):
    g, p, doc = load_exact(path)
    res = residuals(g, p)
    out = {"certificate": os.path.relpath(path, RES).replace("\\", "/"), "number_field": doc.get("number_field", "Q"),
           "exact_r": [str(x) for x in res["r"]], "residuals_zero": all(x == 0 for x in res["r"]),
           "utilities_sum_zero": sum(res["utilities"]) == 0,
           "P1_open_zero": all(p[I.index, 1] == 0 for I in g.isets if I.player == 0 and I.history == "")}
    pol = json.load(open(path.replace("policy_exact", "polish")))
    wit = pol.get("witnesses", [])
    out["witnesses_stored"] = len(wit)
    if wit:
        w = wit[0]
        cls = lambda I: I.hand_label[0] * 2
        th = [I.index for I in g.isets if I.player == w["theta_owner"] - 1 and I.history == w["theta_history"] and cls(I) == w["theta"]]
        up = [I.index for I in g.isets if I.player == w["upstream_player"] - 1 and I.history == w["upstream_history"] and cls(I) == w["upstream"]]
        A = w["upstream_player"] - 1
        D0 = upstream_D(g, set_theta(g, p, th, 1, Fraction(0)), up, 1, 0)
        D1 = upstream_D(g, set_theta(g, p, th, 1, Fraction(1)), up, 1, 0)
        C = D1 - D0
        ts = -D0[A] / C[A]
        D = upstream_D(g, set_theta(g, p, th, 1, ts), up, 1, 0)
        r = residuals(g, set_theta(g, p, th, 1, ts))["r"]
        out["witness_rechecked"] = {"theta": "P%d %s %s" % (w["theta_owner"], w["theta_history"], w["theta"]),
                                    "upstream": "P%d %s %s" % (w["upstream_player"], w["upstream_history"] or "(open)", w["upstream"]),
                                    "theta_star": str(ts), "theta_star_matches_stored": str(ts) == w["theta_star"],
                                    "in_unit_interval": 0 <= ts <= 1, "D_A_zero": D[A] == 0,
                                    "numerator_nonzero": any(D[X] != 0 for X in range(g.n) if X != A),
                                    "residuals_zero_at_theta_star": all(x == 0 for x in r)}
    out["ok"] = (out["residuals_zero"] and out["utilities_sum_zero"] and out["P1_open_zero"] and
                 (not wit or all(v for k, v in out["witness_rechecked"].items() if k not in ("theta", "upstream", "theta_star"))))
    return out


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    files = sorted(glob.glob(os.path.join(RES, "potsweep*", "*", "*", "policy_exact*.json")))
    with Pool(min(workers, len(files))) as pool:
        outs = pool.map(check, files)
    json.dump(outs, open(os.path.join(RES, "potsweep", "verify.json"), "w"), indent=1)
    for o in outs:
        print("%-5s %-72s %-24s r=%s witness %s" % ("OK" if o["ok"] else "FAIL", o["certificate"], o["number_field"],
                                                     o["exact_r"], o.get("witness_rechecked", {}).get("theta_star_matches_stored")))
    print("%d certificates, %d OK" % (len(outs), sum(o["ok"] for o in outs)))


if __name__ == "__main__":
    main()
