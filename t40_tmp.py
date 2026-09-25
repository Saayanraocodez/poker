import numpy as np, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); I = refine.I
for k in (62, 469):
    lab = L[k]; pieces = seqset.leaf_pieces(lab)
    out, pin = refine.closure(lab, verbose=False)
    a = {v: r[0] for v, r in out.items()}
    for nm, val in (("b32",0), ("c34",0), ("c13",0), ("c43",1)):
        if lab[I[nm]] == 3: a[I[nm]] = val
    for c23 in (0, "mix"):
        aa = dict(a); aa[I["b22"]] = "mix"; aa[I["c23"]] = c23; aa[I["c33"]] = "mix"
        P, Kd, gens, bounds, why = seqset.full_case_system(lab, pieces, aa)
        t0 = time.time(); e, cert = seqset.empty(P, Kd, gens, bounds, 3000)
        print("leaf %d  b22=mix c23=%-3s c33=mix : %s (%.0fs)" % (k, c23, "EMPTY" if e else "alive", time.time()-t0), flush=True)
