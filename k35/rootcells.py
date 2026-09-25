"""Which of the 3^n P1-opening label cells survive treesize6.propagate at the
root, for the (3, n)-card game (KUHN_CARDS).  Honours KUHN_MODE.
usage:  KUHN_CARDS=5 KUHN_MODE=nash python rootcells.py
"""
import itertools, os, sys, time
import numpy as np, treesize6 as T6, kuhn3p as K

I = K.NAME_IDX; NAME = K.PARAM_NAME
U, MIX, DC = T6.U, T6.MIX, T6.DC
mode = "nash" if not T6.WEAK else "seq"
labs = ["0", "1", "MIX"]
opening = ["a%d1" % j for j in K.CARDS]
alive = []; t0 = time.time(); n = 0
for combo in itertools.product(labs, repeat=len(opening)):
    spec = ",".join("%s:%s" % (c, l) for c, l in zip(opening, combo)); n += 1
    lab, LO, HI = T6.root_of(spec)
    lab2, LO2, HI2, al = T6.propagate(lab[None], LO[None], HI[None], T6.WEAK)
    if al[0]:
        alive.append(spec)
        nu = int((lab2[0] == U).sum()); nd = int((lab2[0] == DC).sum())
        print("%-40s ALIVE  unassigned %2d  DC %2d" % (spec, nu, nd), flush=True)
suffix = "" if mode == "seq" else "_nash"
with open("cells_alive%s_%d.txt" % (suffix, K.NCARDS), "w") as f:
    for s in alive: f.write(s + "\n")
print("\n%d of %d cells alive at the root, %d cards, %s mode  (%.0fs)" % (len(alive), n, K.NCARDS, mode, time.time() - t0))
