"""Re-polish ONE explore35 seed with a bigger support-search budget (float exploration, decides nothing).
usage: python explore35_one.py <cache json> <index> <seed label> <budget>"""
import sys, json
import numpy as np
import kuhnGen as Q
from explore35 import polish, OPEN, G
P = json.load(open(sys.argv[1])); p = np.array(P[int(sys.argv[2])])
cand = json.load(open("polish35_candidates.json"))[0]
S0 = cand["interior"]; k35 = cand["float_profile_k35"]
cert = np.zeros(G.nparam)
for pl in range(3):
    for j in G.cards:
        for h in G.sit_hist[pl]:
            cert[G.pidx(pl, j, h)] = k35[pl * 20 + (j - 1) * 4 + Q.SGS_SIT[pl][h] - 1]
e, r, S, how = polish(p, cert, S0, int(sys.argv[4]))
print("seed %s: %s  expl %.2e  P1 opens %s  |S| %d" % (sys.argv[3], how, e, np.round([r[i] for i in OPEN], 5).tolist(), len(S)), flush=True)
json.dump({"seed": sys.argv[3], "expl": e, "profile": r.tolist(), "support": [int(i) for i in S]}, open("explore35_seed%s.json" % sys.argv[3], "w"))
