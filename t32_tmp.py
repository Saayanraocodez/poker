import numpy as np, sympy as sp, seqset, refine
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
D, R, X = refine.build_DR(); EPS = seqset.EPS
forms = {}
for k in seqset.FAM:
    lab = L[k]
    out, pin = refine.closure(lab, verbose=False)
    pin2 = dict(pin); pin2.update({v: r[0] for v, r in out.items()})
    sub = {}
    for w, val in pin2.items():
        rw = sp.Symbol("r_" + NAME[w]); sub[X[w]] = EPS * rw if val == 0 else 1 - EPS * rw
    for n in ("b32", "c43", "c13", "c34", "b22", "c23", "c33"):
        v = I[n]
        if v in pin2: continue
        kd, A = refine.leading(sp.expand(D[v].subs(sub)), EPS)
        forms.setdefault(n, {}).setdefault(sp.srepr(sp.expand(A)), []).append(k)
for n, d in forms.items():
    print("%-4s : %d distinct form(s) across %d leaves" % (n, len(d), sum(len(v) for v in d.values())))
    for r_, ks in d.items():
        print("      %-28s leaves %s" % (sp.factor(sp.sympify(r_)), ks))
