import numpy as np, sympy as sp, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
lab = L[469]; pieces = seqset.leaf_pieces(lab)
out, pin = refine.closure(lab, verbose=False)
assign0 = {v: r[0] for v, r in out.items()}
print("closure:", seqset.fmt_assign(assign0))
rest = [v for v in pieces[6] if v not in assign0 and lab[v] == 3]
print("to decide:", [NAME[v] for v in rest])
# the all-zero-ish case, the R11 face:  b32=0, c33 interior
for case in ({I["b22"]:0, I["b32"]:0, I["c13"]:0, I["c23"]:0, I["c33"]:"mix", I["c34"]:0, I["c43"]:1},
             {I["b22"]:0, I["b32"]:"mix", I["c13"]:0, I["c23"]:0, I["c33"]:"mix", I["c34"]:0, I["c43"]:1}):
    a = dict(assign0); a.update(case)
    t0 = time.time(); r = seqset.full_case_system(lab, pieces, a)
    P, Kd, gens, bounds, why = r
    print("\ncase %s" % seqset.fmt_assign(case))
    print("   %d constraints, gens %s  (%.0fs)" % (len(P), [str(g) for g in gens], time.time()-t0))
    for p, k, w in zip(P, Kd, why):
        if w.startswith("belief"): print("      %-14s %s %s 0" % (w, sp.factor(p), k))
