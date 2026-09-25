"""Which of the 81 P1-opening label branches survive treesize6.propagate at
the root?  Honours KUHN_MODE (seq: bnb6 weak rules; nash: strong rules plus
the certainly-reached dominance rule).  Writes branches_alive<suffix>.txt,
suffix '' for seq and '_nash' for nash, in the format runbet6 reads.

usage:  [KUHN_MODE=nash] [KUHN_SUFFIX=R] python root81.py
"""
import itertools, os, sys, time
import numpy as np, treesize6 as T6, kuhn3p as K

I = K.NAME_IDX; NAME = K.PARAM_NAME
U, MIX, DC = T6.U, T6.MIX, T6.DC
mode = "nash" if not T6.WEAK else "seq"
labs = ["0", "1", "MIX"]
alive = []; t0 = time.time()
for combo in itertools.product(labs, repeat=4):
    spec = ",".join("%s:%s" % (c, l) for c, l in zip(("a11", "a21", "a31", "a41"), combo))
    lab, LO, HI = T6.root_of(spec)
    lab2, LO2, HI2, al = T6.propagate(lab[None], LO[None], HI[None], T6.WEAK)
    if al[0]:
        alive.append(spec)
        nu = int((lab2[0] == U).sum()); nd = int((lab2[0] == DC).sum())
        narrowed = " ".join("%s[%.2f,%.2f]" % (NAME[i], LO2[0, i], HI2[0, i]) for i in range(48)
                            if lab2[0, i] == U and (LO2[0, i] > 0 or HI2[0, i] < 1))
        print("%-32s ALIVE  unassigned %2d  DC %2d  narrowed %s" % (spec, nu, nd, narrowed), flush=True)
    else:
        print("%-32s dead" % spec, flush=True)
suffix = ("" if mode == "seq" else "_nash") + os.environ.get("KUHN_SUFFIX", "")   # KUHN_SUFFIX: separate files for a re-derivation
with open("branches_alive%s.txt" % suffix, "w") as f:
    for s in alive: f.write(s + "\n")
print("\n%d of 81 branches alive at the root in %s mode  (%.0fs)  -> branches_alive%s.txt" % (len(alive), mode, time.time() - t0, suffix))
