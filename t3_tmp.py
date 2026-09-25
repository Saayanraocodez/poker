import sympy as sp, numpy as np, time, refine
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
t0 = time.time(); D, R, X = refine.build_DR(); print("tree built %.0fs" % (time.time()-t0))
lab = L[469]; eps = sp.Symbol("eps", positive=True)
sub, r = refine.tremble_subs(lab, X, eps)
for name in ("c34", "c44", "b32", "c33", "b44", "b42"):
    v = I[name]
    kd, A = refine.leading(D[v].subs(sub), eps)
    kr, B = refine.leading(R[v].subs(sub), eps)
    print("\n%-4s (leaf label %s): D ~ eps^%s,  reach ~ eps^%s" % (name, lab[v], kd, kr))
    print("   belief-weighted difference  A/B  with A =", sp.factor(A))
    print("                                    B =", sp.factor(B))
