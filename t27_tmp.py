import numpy as np, sympy as sp, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
D, R, X = refine.build_DR(); EPS = seqset.EPS
for k in seqset.FAM:
    lab = L[k]
    out, pin = refine.closure(lab, verbose=False)
    # add b32 = 0 (proved: A_b32 is one-signed at every ordering) and re-close
    pin2 = dict(pin); pin2[I["b32"]] = 0
    for v, r_ in out.items(): pin2[v] = r_[0]
    sub = {}
    for w, val in pin2.items():
        rw = sp.Symbol("r_" + NAME[w]); sub[X[w]] = EPS * rw if val == 0 else 1 - EPS * rw
    free = [w for w in range(48) if w not in pin2]
    nonneg = [sp.Symbol("r_" + NAME[w]) for w in pin2] + [X[w] for w in free]
    forced2 = {}
    for v in free:
        if lab[v] == 2: continue
        kd, A = refine.leading(sp.expand(D[v].subs(sub)), EPS)
        if kd is None: continue
        s = refine.sign_definite(A, sorted(nonneg, key=str))
        if s: forced2[NAME[v]] = 1 if s > 0 else 0
    still = [NAME[v] for v in free if lab[v] == 3 and NAME[v] not in forced2]
    print("%4d  after b32=0: also forced %-40s  still open: %s" % (k, forced2, still), flush=True)
