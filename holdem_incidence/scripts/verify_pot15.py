"""Independent exact re-check of a pot-1.5 witness (does not use analyze_profiles): the
rationalised profile is an exact Nash equilibrium, P1 never opens, and along P2's JJ call the family
stays exactly Nash up to theta* and leaves the Nash set right after it.

usage:  python scripts/verify_pot15.py
"""
import json, os, sys
from fractions import Fraction as F
HI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HI)
from hinc.game import RiverGame
from hinc.strategy import load_profile, to_exact, normalise_exact
from hinc.bestresponse import residuals
from hinc.evaluate import infoset_reach, utilities
from hinc.offpath import set_theta, upstream_D
g = RiverGame(json.load(open(os.path.join(HI, "configs/panel/pot_pot1.5_JJAA24.json"))))
p = normalise_exact(g, to_exact(load_profile(os.path.join(HI, "results/panel/pot_pot1.5_JJAA24/dcfr_s1/policy_avg.json"), g), 10**6))
res = residuals(g, p)
print("exact r:", [str(x) for x in res["r"]], " utilities:", [str(x) for x in res["utilities"]])
rch = infoset_reach(g, p)
p1open = [I.index for I in g.isets if I.player == 0 and I.history == ""]
print("P1 opening probabilities (exact, distinct values):", sorted({str(p[i, 1]) for i in p1open}))
th = [I.index for I in g.isets if I.player == 1 and I.history == "B:1" and I.hand_label[0] == "J"]
up = [I.index for I in g.isets if I.player == 0 and I.history == "" and I.hand_label[0] == "A"]
print("theta sets reach (exact):", {str(rch["total"][i]) for i in th}, " theta0:", {str(p[i, 1]) for i in th})
D0 = upstream_D(g, set_theta(g, p, th, 1, F(0)), up, 1, 0)
D1 = upstream_D(g, set_theta(g, p, th, 1, F(1)), up, 1, 0)
C = D1 - D0
ts = -D0[0] / C[0]
print("C:", [float(x) for x in C], " theta* =", float(ts), " sum C =", sum(C))
for name, x in (("theta*", ts), ("theta* - 1/1000", ts - F(1, 1000)), ("theta* + 1/1000", ts + F(1, 1000)), ("0", F(0))):
    q = set_theta(g, p, th, 1, x)
    r = residuals(g, q)["r"]
    D = upstream_D(g, q, up, 1, 0)
    print("%-16s r = %s   D = %s" % (name, ["%.3e" % float(v) for v in r], ["%.5f" % float(v) for v in D]),
          " exact zero r:", all(v == 0 for v in r), " D_A exactly 0:", D[0] == 0)
# P2 and P3 betting behaviour (class level)
agg = {}
for I in g.isets:
    agg.setdefault((I.player + 1, I.history, I.hand_label[0] * 2), []).append(float(p[I.index, 1]))
for k in sorted(agg):
    if k[1] in ("K", "K-K", "K-K-B:1", "K-K-B:1-F", "K-K-B:1-C"):
        print(k, round(sum(agg[k]) / len(agg[k]), 4))
