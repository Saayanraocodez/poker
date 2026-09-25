"""(a) the residue identity, stated cleanly;  (b) the 2-player slack test, done right."""
from fractions import Fraction as Fr

import numpy as np

import kuhn3p as K
import family as F
import kuhn2p as T

I = K.NAME_IDX
KAP = K.KAPPA


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


hdr("A.  THE RESIDUE IDENTITY")
print("   Along c33 alone, D(c33) = du1/da_j1 and N(c33) = -du3/da_j1 are both AFFINE,")
print("   so rho = N/D is Mobius: a simple pole at the zero c33* of D, with")
print("        rho(c33) = R/(c33 - c33*) + O(1),      R = N(c33*) / D'")
print("   D' = d2u1/(da_j1 dc33) is a constant multiple of kappa = 1/24.")
print("   At c33* the denominator vanishes, so P1's deviation is COSTLESS there and")
print("   zero-sum forces du2 = -du3 = the transfer magnitude t.  Hence N(c33*) = t")
print("   and  R = t / D'  exactly: the residue IS the size of the costless transfer")
print("   available at that boundary, divided by the denominator slope.\n")
print("   dev   D'/kappa   c33*      transfer t at c33*   R = t/D'        check")
ok = True
for base in (dict(b11=.15, b21=.15, b23=0., b32=.40, c11=.25, c34=.5),
             dict(b11=.05, b21=.20, b23=0., b32=.00, c11=.00, c34=.0),
             dict(b11=.25, b21=.00, b23=.125, b32=.30, c11=.50, c34=1.),
             dict(b11=.00, b21=.10, b23=0., b32=.55, c11=.00, c34=.3)):
    sub = "A" if base["c11"] == 0 else ("C" if base["c11"] == .5 else "B")
    v = F.violations(subfamily=sub, c33=max(0., .5 - base["b32"]), **base)
    assert not v, ("OFF-FAMILY TEST POINT", base, v)
    lo, hi = 0.5 - base["b32"], F.b32_max(base["b11"], base["b21"]) - base["b32"]
    for nm, star in (("a11", lo), ("a21", lo), ("a41", hi)):
        if not (0.0 <= star <= 1.0):
            print("   %-4s  %s  %+.4f   pole NOT ATTAINABLE (c33* outside [0,1]"
                  " because b32 > 1/2) -> no pole here" % (nm, " " * 8, star))
            continue
        D0 = K.exact_coord_derivative(F.make_profile(c33=0., **base), I[nm])[0]
        D1 = K.exact_coord_derivative(F.make_profile(c33=1., **base), I[nm])[0]
        Dp = D1 - D0
        g = K.exact_coord_derivative(F.make_profile(c33=star, **base), I[nm])
        t = g[1]                                   # du2 at the boundary (= -du3)
        R = -g[2] / Dp
        # empirical residue from the limit
        eps = 1e-7
        gg = K.exact_coord_derivative(F.make_profile(c33=star + eps, **base), I[nm])
        Remp = (-gg[2] / gg[0]) * eps
        good = abs(g[0]) < 1e-13 and abs(t + g[2]) < 1e-13 and abs(R - t / Dp) < 1e-12
        ok &= good and abs(Remp - R) < 1e-5
        print("   %-4s  %+6.1f     %+.4f   %+.8f          %+.8f = %-8s %s"
              % (nm, Dp / KAP, star, t, R, Fr(R).limit_denominator(10**5),
                 "ok" if good else "MISMATCH"))
    print("   " + "-" * 74)
print("   identity R = t/D' holds at every point tested, and matches the empirical")
print("   limit rho*(c33-c33*) to 1e-5 at offset 1e-7:  %s" % ("PASS" if ok else "FAIL"))

hdr("B.  2-PLAYER: is there any SLACK in the off-path parameters at alpha = 0?")
print("   (previous sweep missed y22 = 1/3 because it is not on a 401-point grid)")
p0 = T.family(0.0)
for nm in ("y12", "y22", "y32"):
    i = T.IDX_OF[nm]
    vs = np.unique(np.concatenate([np.linspace(0, 1, 4001), [p0[i]],
                                   np.linspace(max(0, p0[i] - .01),
                                               min(1, p0[i] + .01), 401)]))
    ex = np.array([T.exploitability(np.where(np.arange(12) == i, v, p0)).max()
                   for v in vs])
    okv = vs[ex < 1e-12]
    w = (okv.max() - okv.min()) if len(okv) else 0.0
    print("   %-4s (family value %.6f): zero-exploitability set = %s, width %.2e -> %s"
          % (nm, p0[i],
             ("[%.6f, %.6f]" % (okv.min(), okv.max())) if len(okv) else "EMPTY",
             w, "INTERVAL (slack)" if w > 1e-9 else "SINGLE POINT (no slack)"))
print("\n   compare 3-player: c33's zero-exploitability set at b11=b21=0.15, b32=0.40")
b11 = b21 = .15
b32 = .40
lo, hi = F.c33_range(b11, b21, b32)
vs = np.linspace(0, 1, 4001)
ex = np.array([np.abs(K.exploitability(
    F.make_profile(b11, b21, 0., b32, .25, v, .5))).max() for v in vs])
okv = vs[ex < 1e-12]
print("      = [%.4f, %.4f], width %.4f -> INTERVAL (slack), matching Table 3 [%.4f, %.4f]"
      % (okv.min(), okv.max(), okv.max() - okv.min(), lo, hi))

hdr("C.  2-PLAYER: what are the null directions, and why")
print("   P1's own free-parameter directions at three alphas (exact derivatives):")
for a in (0.0, 1 / 6, 1 / 3):
    p = T.family(a)
    row = []
    for nm in ("x11", "x31", "x22"):
        du = T.exact_coord_derivative(p, T.IDX_OF[nm])
        row.append("%s=(%+.5f,%+.5f)" % (nm, du[0], du[1]))
    print("      alpha=%.4f : %s" % (a, "  ".join(row)))
print("\n   Every free direction is (0, 0): P1 is indifferent AND so is P2, because")
print("   du2 = -du1.  In 3-player Kuhn the corresponding P2 directions are")
print("   (+1/12, 0, -1/12) -- P2 indifferent, but P1 and P3 emphatically not.")
p3 = F.profile_A(0., 0., .5, .5, 0.)[0]
for nm in ("b11", "b21", "b41"):
    print("      3-player du/d%-4s = %s" % (
        nm, np.round(K.exact_coord_derivative(p3, I[nm]), 8)))
