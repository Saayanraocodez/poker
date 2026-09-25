import numpy as np, time, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); I = refine.I
k = 62
lab = L[k]; pieces = seqset.leaf_pieces(lab)
out, pin = refine.closure(lab, verbose=False)
a = {v: r[0] for v, r in out.items()}
for nm, val in (("b32",0), ("c34",0), ("c13",0), ("c43",1)):
    if lab[I[nm]] == 3: a[I[nm]] = val
a[I["b22"]] = "mix"; a[I["c23"]] = 0; a[I["c33"]] = "mix"
P, Kd, gens, bounds, why = seqset.full_case_system(lab, pieces, a)
print("gens:", [str(g) for g in gens], flush=True)
# what does the system say about b22 alone?  maximise b22 over it
import certbox
from fractions import Fraction as F
j = [str(g) for g in gens].index("b22")
for T in (F(2,5), F(1,3), F(1,4), F(1,8), F(1,100)):
    b2 = [list(b) for b in bounds]; b2[j][0] = T; b2[j][2] = False
    t0 = time.time(); r = certbox.prove_empty_cert(P, Kd, gens, b2, 2000, chord=False, exact_dual=False)
    print("   b22 >= %-6s : %s  (%.0fs)" % (T, "EMPTY" if r[0] else "alive", time.time()-t0), flush=True)
