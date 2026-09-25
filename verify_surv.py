import numpy as np, sys, solve2, screen2, eqtools as E, classify, kuhn3p as K, family as F, bnb
I=K.NAME_IDX
pat=np.load(sys.argv[1]); X=np.load(sys.argv[2])
rng=np.random.default_rng(0)
print("LM survivors:", len(X))
# high-precision polish
P,r = solve2.solve(pat.astype(np.int64), rng, iters=60, x0=X, tol=1e-14)
ex = np.array([np.abs(E.expl(p)).max() for p in P])
nash = ex < 1e-13
print("polished to resid<1e-13: %d   TRUE Nash (exploitability<1e-13): %d" % ((r<1e-13).sum(), nash.sum()))
if nash.sum()==0:
    print("none certified"); raise SystemExit
Q=P[nash]
sig={}
for p in Q: sig.setdefault(classify.signature(p), p)
print("distinct leaf-distributions:", len(sig))
U=np.array([E.util(p) for p in sig.values()])
k=1/24
print("u1 range [%.9f, %.9f]  (family [%.9f, %.9f])"%(U[:,0].min(),U[:,0].max(),-k*0.75,-k*0.5))
print("u2 range [%.9f, %.9f]  (family %.9f)"%(U[:,1].min(),U[:,1].max(),-k*0.5))
print("u3 range [%.9f, %.9f]  (family [%.9f, %.9f])"%(U[:,2].min(),U[:,2].max(),k,k*1.25))
fg=np.array([classify.family_gap(p) for p in sig.values()])
print("family leaf-distribution gap: max %.3e ; OUTSIDE family (>1e-9): %d of %d"%(fg.max(),(fg>1e-9).sum(),len(fg)))
out=[p for p,g in zip(sig.values(),fg) if g>1e-9]
for p in out[:10]:
    print("  OUTSIDE:", {K.PARAM_NAME[i]: round(float(p[i]),6) for i in range(48) if 1e-9<p[i]<1-1e-9}, "u=",E.util(p))
np.save("certified_eq.npy", np.array(list(sig.values())))
