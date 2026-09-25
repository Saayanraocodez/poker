"""Where does rho change sign for A = P1, and how does it blow up?"""
import numpy as np

import kuhn3p as K
import family as F
import grids as G

np.set_printoptions(precision=5, suppress=True)
P, M = G.full_grid()
GE = K.gradients_batch(P, h=None)
TOL = 1e-12

for name in ("a11", "a21", "a41", "a32"):
    i = K.NAME_IDX[name]
    dA, dC = GE[:, i, 0], GE[:, i, 2]          # A=P1, C=P3
    nz = np.abs(dA) > TOL
    r = np.full(len(P), np.nan)
    r[nz] = -dC[nz] / dA[nz]
    print("\n==== %s ====   defined at %d/%d points" % (name, nz.sum(), len(P)))
    print("   min |du_1| among defined = %.3e   (kappa = %.4f)"
          % (np.abs(dA[nz]).min(), K.KAPPA))
    for lbl, sel in (("rho < 0 ", nz & (r < -1e-9)),
                     ("rho = 0 ", nz & (np.abs(r) <= 1e-9)),
                     ("0<rho<=1", nz & (r > 1e-9) & (r <= 1 + 1e-9)),
                     ("rho > 1 ", nz & (r > 1 + 1e-9))):
        k = int(sel.sum())
        if not k:
            print("   %s : %6d pts" % (lbl, k))
            continue
        print("   %s : %6d pts   beta[%.3f,%.3f] b32[%.3f,%.3f] "
              "c33[%.3f,%.3f] c11[%.3f,%.3f] t_c33[%.2f,%.2f]"
              % (lbl, k, M["beta"][sel].min(), M["beta"][sel].max(),
                 M["b32"][sel].min(), M["b32"][sel].max(),
                 M["c33"][sel].min(), M["c33"][sel].max(),
                 M["c11"][sel].min(), M["c11"][sel].max(),
                 M["t_c33"][sel].min(), M["t_c33"][sel].max()))

# how cheap is the cheapest strictly-costly deviation for each player?
print("\n\n==== cheapest strictly-costly coordinate deviation per player ====")
own = [range(A * 16, (A + 1) * 16) for A in range(3)]
for A in range(3):
    dA = GE[:, :, A]
    feas_up = (P < 1 - 1e-12)
    feas_dn = (P > 1e-12)
    best = np.full(len(P), -np.inf)
    arg = np.full(len(P), -1)
    for i in own[A]:
        for f, s in ((feas_up[:, i], +1.0), (feas_dn[:, i], -1.0)):
            v = s * dA[:, i]
            m = f & (v < -TOL) & (v > best)
            best[m], arg[m] = v[m], i
    names, cnt = np.unique([K.PARAM_NAME[j] for j in arg], return_counts=True)
    print("  A=P%d  least-costly du_A in [%.5f, %.5f]; achieved by: %s"
          % (A + 1, best.min(), best.max(),
             ", ".join("%s x%d" % (n, c) for n, c in zip(names, cnt))))
