"""Can P1 bet card 1 at all?  The owners' side of the four coordinates.

symbet.py established, with only Table 2 substituted and verified numerically,

    du1/da11 = [ 2(1-c33)(1-b22) + 2(1-c23)(1-b32) - 3 ] / 12

so a11 > 0 in an equilibrium forces  c33 < 1/2,  b22 < 1/2,  c23 < 1/2,
b32 < 1/2.  Those four coordinates belong to P2 (b22, b32) and P3 (c23, c33),
and in an equilibrium each owner is best-responding: a coordinate held BELOW 1
needs its own derivative <= 0.  So the question is whether

    du2/db22 <= 0,  du2/db32 <= 0,  du3/dc23 <= 0,  du3/dc33 <= 0

can all hold on the region a11 > 0, {c33, b22, c23, b32} < 1/2.  If they cannot,
then a11 = 0 in every equilibrium -- a theorem that removes the entire a11-
betting branch (2.3e10 support patterns) by algebra.

Step 1: derive the four derivatives with Table 2 substituted, verify each
against bgrad, and report size and factorisation.
Step 2: sample the region numerically and look at the signs.
"""
import numpy as np, sympy as sp, time
import symbet, bgrad, kuhn3p as K

I = K.NAME_IDX
FOUR = ("b22", "b32", "c23", "c33")

t0 = time.time()
X, syms = symbet.table2_only()
G, U = symbet.build(X)
print("symbolic tree pass: %.0fs\n" % (time.time() - t0), flush=True)

print("=== own-derivatives of the four coordinates that govern a11 ===\n", flush=True)
exprs = {}
for n in FOUR:
    e = sp.expand(G[I[n]])
    exprs[n] = e
    terms = len(e.args) if e.is_Add else 1
    f = sp.factor(e)
    print("du/d%s : %d terms, degree %d" % (n, terms, sp.total_degree(e)), flush=True)
    print("   = %s\n" % f, flush=True)
    free = sorted(str(s) for s in e.free_symbols)
    print("   depends on: %s\n" % ", ".join(free), flush=True)

# numerical verification of each
print("=== verification against bgrad.grads_own ===", flush=True)
rng = np.random.default_rng(1)
P = rng.random((3000, 48))
for nm in symbet.T2_ZERO: P[:, I[nm]] = 0.0
for nm in symbet.T2_ONE:  P[:, I[nm]] = 1.0
Gn = bgrad.grads_own(P)
for n in FOUR:
    fn = sp.lambdify([syms[s] for s in sorted(syms)], exprs[n], "numpy")
    args = [P[:, I[s]] for s in sorted(syms)]
    val = fn(*args)
    print("   du/d%s  max |symbolic - numeric| = %.2e" % (n, np.abs(val - Gn[:, I[n]]).max()), flush=True)

# sign analysis on the a11-betting region
print("\n=== signs on the region a11>0, {c33,b22,c23,b32} < 1/2 ===", flush=True)
M = 200000
Q = rng.random((M, 48))
for nm in symbet.T2_ZERO: Q[:, I[nm]] = 0.0
for nm in symbet.T2_ONE:  Q[:, I[nm]] = 1.0
for n in FOUR: Q[:, I[n]] = 0.5 * rng.random(M)
Q[:, I["a11"]] = 0.02 + 0.98 * rng.random(M)
Gq = bgrad.grads_own(Q)
d11 = Gq[:, I["a11"]]
ok = d11 >= 0                      # P1 actually wants to bet
print("   samples %d ; with du1/da11 >= 0: %d" % (M, ok.sum()), flush=True)
for n in FOUR:
    g = Gq[ok, I[n]]
    print("   du/d%s on those:  min %+.4f  max %+.4f   fraction <= 0 (owner content to hold it low): %.1f%%"
          % (n, g.min(), g.max(), 100 * (g <= 1e-12).mean()), flush=True)
allok = ok.copy()
for n in FOUR: allok &= (Gq[:, I[n]] <= 1e-12)
print("\n   samples satisfying du1/da11 >= 0 AND all four owner conditions: %d of %d" % (allok.sum(), M), flush=True)
if allok.any():
    j = np.flatnonzero(allok)[0]
    print("   example:", {K.PARAM_NAME[i]: round(float(Q[j, i]), 4) for i in range(48) if 0 < Q[j, i] < 1})
