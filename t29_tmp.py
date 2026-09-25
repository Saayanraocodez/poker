import numpy as np, sympy as sp, seqset, refine
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
D, R, X = refine.build_DR(); EPS = seqset.EPS
lab = L[469]
out, pin = refine.closure(lab, verbose=False)
pin2 = dict(pin); pin2.update({v: r[0] for v, r in out.items()})
for n, val in (("b32",0), ("c34",0), ("c13",0), ("c43",1)): pin2[I[n]] = val
sub = {}
for w, val in pin2.items():
    rw = sp.Symbol("r_" + NAME[w]); sub[X[w]] = EPS * rw if val == 0 else 1 - EPS * rw
print("after the chain b32=0, c34=0, c13=0, c43=1 (all forced):")
for n in ("a11", "a21", "a31", "a41", "b22", "c23", "c33"):
    v = I[n]
    kd, A = refine.leading(sp.expand(D[v].subs(sub)), EPS)
    print("   A_%-4s (eps^%s) = %s" % (n, kd, sp.factor(A)))
