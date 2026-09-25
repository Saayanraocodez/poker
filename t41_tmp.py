import numpy as np, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); I = refine.I; NAME = refine.NAME
k = 97
lab = L[k]; pieces = seqset.leaf_pieces(lab)
out, pin = refine.closure(lab, verbose=False)
a = {v: r[0] for v, r in out.items()}
for nm, val in (("b32",0), ("c34",0), ("c13",0), ("c43",1)):
    if lab[I[nm]] == 3: a[I[nm]] = val
a[I["b22"]] = 0; a[I["c23"]] = "mix"; a[I["c33"]] = "mix"
P, Kd, gens, bounds, why = seqset.full_case_system(lab, pieces, a)
print("gens:", [str(g) for g in gens], flush=True)
t0 = time.time(); e, c = seqset.empty(P, Kd, gens, bounds, 6000)
print("emptiness at 6000 nodes:", e, "%.0fs" % (time.time()-t0), flush=True)
if not e:
    t0 = time.time(); w = seqset.witness_for(lab, pieces, a) or seqset.witness_guided(lab, pieces, a)
    print("witness:", "found" if w else "none", "%.0fs" % (time.time()-t0))
    if w: print("   ", ", ".join("%s=%s" % (NAME[i], w[0][i]) for i in range(48) if 0 < w[0][i] < 1), "| order", w[2])
