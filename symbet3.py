"""The next link: does P1 actually want to value-bet card 4?

symbet2 chained a11 > 0  =>  b32 < 1/2  =>  du2/db32 <= 0  =>  2 a41 >= 3(a11+a21)
=> a41 > 0.  So a P1 that bluffs card 1 must also bet card 4, and then P1's own
condition on a41 applies: a41 > 0 needs du1/da41 >= 0.

If du1/da41 < 0 everywhere on the region carved out so far, P1 does not want
the value bet it is forced to make, and a11 = 0 in every equilibrium.

Constraints accumulated (all necessary for a11 > 0, all verified):
   R1  a11 > 0
   R2  c33, b22, c23, b32 < 1/2                      (from du1/da11 >= 0)
   R3  2 a41 >= 3 (a11 + a21)                         (du2/db32 <= 0)
   R4  5 a11 c34 - 3 a11 + 2 a31 + 2 a41 >= 0         (du2/db22 <= 0)
   R5  a31 + a41 (2 - b32) >= 4 a11 (1 - b32)         (du3/dc23 <= 0)
   R6  a41 (2 - b22) >= 4 (a11 + a21) - 4 a11 b22     (du3/dc33 <= 0)
   R7  du1/da11 >= 0 itself
"""
import numpy as np, sympy as sp, time
import symbet, bgrad, kuhn3p as K

I = K.NAME_IDX
NAME = K.PARAM_NAME

X, syms = symbet.table2_only()
G, U = symbet.build(X)
e41 = sp.expand(G[I["a41"]])
print("du1/da41 : %d terms, degree %d" % (len(e41.args), sp.total_degree(e41)))
print("   depends on:", ", ".join(sorted(str(s) for s in e41.free_symbols)))
print("   =", sp.factor(e41), "\n", flush=True)

# sample the accumulated region, look at du1/da41
rng = np.random.default_rng(2)
M = 2000000
Q = rng.random((M, 48))
for nm in symbet.T2_ZERO: Q[:, I[nm]] = 0.0
for nm in symbet.T2_ONE:  Q[:, I[nm]] = 1.0
for n in ("b22", "b32", "c23", "c33"): Q[:, I[n]] = 0.5 * rng.random(M)
Q[:, I["a11"]] = rng.random(M)
g = lambda n: Q[:, I[n]]
R = (g("a11") > 1e-9)
R &= (2*g("a41") >= 3*(g("a11")+g("a21")))
R &= (5*g("a11")*g("c34") - 3*g("a11") + 2*g("a31") + 2*g("a41") >= 0)
R &= (g("a31") + g("a41")*(2-g("b32")) >= 4*g("a11")*(1-g("b32")))
R &= (g("a41")*(2-g("b22")) >= 4*(g("a11")+g("a21")) - 4*g("a11")*g("b22"))
Gq = bgrad.grads_own(Q[R])
d11 = Gq[:, I["a11"]]
R2 = d11 >= 0
S = Q[R][R2]
Gs = Gq[R2]
print("samples %d -> R1-R6 %d -> plus du1/da11>=0: %d" % (M, R.sum(), R2.sum()), flush=True)
d41 = Gs[:, I["a41"]]
print("\ndu1/da41 on the surviving region:  min %+.5f  max %+.5f   fraction >= 0 (P1 content to bet card 4): %.2f%%"
      % (d41.min(), d41.max(), 100*(d41 >= -1e-12).mean()), flush=True)
ok = d41 >= -1e-12
print("survivors after adding du1/da41 >= 0: %d" % ok.sum(), flush=True)
if ok.any():
    # what else do survivors need?  look at every owner condition implied by
    # the survivors' own coordinates being < 1 or > 0
    S2 = S[ok]; G2 = Gs[ok]
    print("\nfor survivors, fraction violating each remaining first-order condition")
    print("(coordinate > 0 needs du >= 0 ; coordinate < 1 needs du <= 0):")
    bad = np.zeros(len(S2), bool)
    rows = []
    for i in range(48):
        x = S2[:, i]; d = G2[:, i]
        v = ((x > 1e-9) & (d < -1e-12)) | ((x < 1-1e-9) & (d > 1e-12))
        if v.mean() > 0:
            rows.append((v.mean(), NAME[i]))
        bad |= v
    for f, n in sorted(rows, reverse=True)[:12]:
        print("   %-5s violated in %5.1f%%" % (n, 100*f))
    print("\nsurvivors satisfying EVERY first-order condition at once: %d of %d" % ((~bad).sum(), len(S2)))
