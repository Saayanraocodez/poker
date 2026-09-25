"""The P1-silent branch, both halves together.

pipe2/pipe screened the enumeration in two pieces -- `samp` (the 400,000-pattern
random sample of s15.4) and `rest` (the other 2,645,358).  400,000 + 2,645,358 =
3,045,358 = the complete enumeration of s15.3, so the union is the whole branch
and this is the first time the numbers can be stated for it rather than for a
sample.

Deduplicates by leaf-distribution signature, which is the right equivalence:
two profiles with the same 312-leaf distribution are the same strategic object.
"""
import numpy as np, eqtools as E, classify, kuhn3p as K

A = np.load("certified_eq_samp.npy")
B = np.load("certified_eq_rest.npy")
print("certified profiles: samp %d, rest %d" % (len(A), len(B)))

sig = {}
for src, X in (("samp", A), ("rest", B)):
    for p in X:
        ex = float(np.abs(E.expl(p)).max())
        assert ex < 1e-13, "non-Nash in %s: expl=%.3e" % (src, ex)
        sig.setdefault(classify.signature(p), p)
print("distinct leaf-distributions over the WHOLE branch: %d" % len(sig))

P = np.array(list(sig.values()))
U = np.array([E.util(p) for p in P])
k = 1 / 24
print("u1 [%.12f, %.12f]  family [%.12f, %.12f]" % (U[:,0].min(), U[:,0].max(), -k*.75, -k*.5))
print("u2 [%.12f, %.12f]  family  %.12f" % (U[:,1].min(), U[:,1].max(), -k*.5))
print("u3 [%.12f, %.12f]  family [%.12f, %.12f]" % (U[:,2].min(), U[:,2].max(), k, k*1.25))

fg = np.array([classify.family_gap(p) for p in P])
print("family leaf-distribution gap: max %.3e   OUTSIDE family (>1e-9): %d of %d"
      % (fg.max(), (fg > 1e-9).sum(), len(fg)))

# Table-3 identities across every certified point
I = K.NAME_IDX
g = lambda p, n: float(p[I[n]])
res = {
    "b41 = 2(b11+b21)":      [abs(g(p,'b41') - 2*(g(p,'b11')+g(p,'b21'))) for p in P],
    "c21 = 1/2 - c11":       [abs(g(p,'c21') - (0.5 - g(p,'c11'))) for p in P],
    "b33 = 1/2+(b11+b21)/2+beta/2-b23(1-b21)":
        [abs(g(p,'b33') - (0.5 + (g(p,'b11')+g(p,'b21'))/2
                           + max(g(p,'b11'), g(p,'b21'))/2
                           - g(p,'b23')*(1-g(p,'b21')))) for p in P],
}
for k_, v in res.items():
    print("   %-42s max residual %.2e" % (k_, max(v)))

beta = np.array([max(g(p,'b11'), g(p,'b21')) for p in P])
print("beta = max{b11,b21} over the branch: [%.9f, %.9f]  (family [0, 0.25])"
      % (beta.min(), beta.max()))
np.save("certified_eq_all.npy", P)
print("saved certified_eq_all.npy (%d profiles)" % len(P))
