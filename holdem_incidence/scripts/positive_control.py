"""Positive controls for the off-path scan (preregistration amendment 1).

PC1: exact SGS family profiles of the bridge game, written as policies, analysed by the SAME
     scan as every other profile: it must recover Kuhn's poles (a11/a21 at c33 = 1/2 - b32,
     a41 at the upper end of the c33 window).
PC2: DCFR on the bridge game (3 seeds x 30,000 iterations), trained and analysed like the pilot.

usage:  python scripts/positive_control.py train|write        (then analyze_profiles.py positive_control)
"""
import json
import os
import sys
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from _paths import load_kuhn3, config                          # noqa: E402
from hinc import kuhn_bridge as KB                            # noqa: E402
from hinc.game import RiverGame                               # noqa: E402
from hinc.strategy import save_profile                        # noqa: E402
from test_bridge import known_profiles                        # noqa: E402
import run_training as RT                                      # noqa: E402

GROUP = "positive_control"


def write_family():
    k3 = load_kuhn3()
    g = RiverGame(config("bridge.json"))
    profs = dict(known_profiles(k3))
    profs["subB_b32_2_5"] = k3.equilibrium_profile(k3.FamilyParameters(3 / 20, 3 / 20, 0, 2 / 5, 1 / 4, 1 / 5, 0)) \
        if False else k3.equilibrium_profile(k3.FamilyParameters(*[__import__("fractions").Fraction(x) for x in
                                                                   ("3/20", "3/20", "0", "2/5", "1/4", "1/5", "0")]))
    for name, kp in profs.items():
        d = os.path.join(RT.RESULTS, GROUP, "bridge_family", name)
        os.makedirs(d, exist_ok=True)
        pr = KB.profile_from_kuhn(g, kp, exact=False)
        extra = {"which": "exact SGS family point (Kuhn Tables 2-3) written as floats", "variant": "SGS-exact",
                 "seed": 0, "iterations": 0, "averaging": "n/a", "avg_weight": [1.0] * g.n_isets,
                 "zero_weight_infosets": []}
        save_profile(os.path.join(d, "policy_avg.json"), g, pr, extra=extra)
        json.dump({"game": g.record(), "variant": "SGS-exact", "seed": 0, "iterations": 0, "averaging": "n/a",
                   "restriction": None, "dir": "%s/bridge_family/%s" % (GROUP, name)},
                  open(os.path.join(d, "run.json"), "w"), indent=1)
    print("wrote", len(profs), "family profiles")


def train():
    jobs = [(GROUP, os.path.join(ROOT, "configs", "bridge.json"), "dcfr", s, 30000) for s in (1, 2, 3)]
    with Pool(3) as pool:
        for out in pool.imap_unordered(RT.run, jobs):
            print("done", out, flush=True)


def sweep():
    """Exact sweep of Kuhn's c33 window at the sub-family-B point b11=b21=3/20, b32=2/5, c11=1/4:
    the derivative vector of P1's a11 and a41 deviations, rho, and every exact residual."""
    import csv
    from fractions import Fraction as F
    from hinc.bestresponse import residuals
    from hinc.offpath import set_theta, upstream_D
    k3 = load_kuhn3()
    g = RiverGame(config("bridge.json"))
    types = KB.card_types(g)
    kp = k3.equilibrium_profile(k3.FamilyParameters(F(3, 20), F(3, 20), F(0), F(2, 5), F(1, 4), F(1, 5), F(0)))
    pr = KB.profile_from_kuhn(g, kp)
    name = lambda i: KB.kuhn_name(*KB.coordinate(g, i, types))
    i_c33 = next(I.index for I in g.isets if name(I.index) == "c33")
    ups = {"a11": next(I.index for I in g.isets if name(I.index) == "a11"),
           "a41": next(I.index for I in g.isets if name(I.index) == "a41")}
    out = os.path.join(RT.RESULTS, GROUP, "kuhn_c33_sweep.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["c33", "dev", "D1", "D2", "D3", "rho_P2", "rho_P3", "r1", "r2", "r3"])
        for k in range(0, 81):
            th = F(k, 80)
            q = set_theta(g, pr, [i_c33], 1, th)
            r = residuals(g, q)["r"]
            for dev, i in ups.items():
                D = upstream_D(g, q, [i], 1, 0)
                rho = [str(-D[X] / D[0]) if D[0] != 0 else "" for X in (1, 2)]
                w.writerow([str(th), dev] + [str(x) for x in D] + rho + [str(x) for x in r])
    print("wrote", out)


if __name__ == "__main__":
    {"write": write_family, "train": train, "sweep": sweep}[sys.argv[1]]()
