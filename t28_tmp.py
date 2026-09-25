import numpy as np, sympy as sp, seqset, refine
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
D, R, X = refine.build_DR(); EPS = seqset.EPS
for k in (18, 62, 469, 211):
    lab = L[k]
    out, pin = refine.closure(lab, verbose=False)
    pin2 = dict(pin); pin2.update({v: r[0] for v, r in out.items()}); pin2[I["b32"]] = 0
    sub = {}
    for w, val in pin2.items():
        rw = sp.Symbol("r_" + NAME[w]); sub[X[w]] = EPS * rw if val == 0 else 1 - EPS * rw
    print("leaf %d:" % k)
    for n in ("a11", "a21", "a31", "a41", "b22", "c43", "c13", "c34", "c23"):
        v = I[n]
        if pin2.get(v) is not None and lab[v] in (0,1) and n not in ("a11","a21","a31","a41"): pass
        kd, A = refine.leading(sp.expand(D[v].subs(sub)), EPS)
        print("   A_%-4s (order %s) = %s" % (n, kd, sp.factor(A)))
