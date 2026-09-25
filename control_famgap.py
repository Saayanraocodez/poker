"""Control for the family_gap / violations tolerance fix.

The fix widened two guards so that the family's own corner b11 = b21 = 1/4 stops
being reported as OUTSIDE the family (b41 = 2(b11+b21) is exactly 1 there and
rounds to 1 + 1e-12).  A widened tolerance is only safe if it still rejects
genuine non-members, so this checks both directions:

  1. family members, including the corner, must have gap ~1e-16 and no
     Table-3 violations;
  2. profiles whose Table-3 image is NOT a profile (b11 = b21 = 0.4 gives
     b41 = 1.6) must still be rejected;
  3. a profile perturbed off the family must still show a large gap -- the
     tolerance must not have swallowed real distance.
"""
import numpy as np, classify, family as F, eqtools as E, kuhn3p as K

I = K.NAME_IDX
ok = True

print("1. family members (the corner is the case that was failing)\n")
pts = [("A(1/8,1/4)", F.profile_A(0.125, 0.25)[0]),
       ("A(1/4,1/4) CORNER", F.profile_A(0.25, 0.25)[0]),
       ("B(1/4,0.3) CORNER", F.profile_B(0.25, 0.3)[0]),
       ("C(1/4,0)", F.profile_C(0.25, 0.0)[0]),
       ("B(1/8,0.2)", F.profile_B(0.125, 0.2)[0])]
for nm, p in pts:
    g = classify.family_gap(p)
    v, sub = classify.family_constraints(p)
    ex = float(np.abs(E.expl(p)).max())
    good = g < 1e-9
    ok &= good
    print("   %-20s gap %.2e  expl %.1e  violations %-24s %s"
          % (nm, g, ex, v if v else "none", "ok" if good else "*** FLAGGED"))

print("\n2. a Table-3 image that is not a profile must still be rejected\n")
q = F.make_profile(0.4, 0.4, 0.0, 0.0, 0.0, 0.5, 0.0)
p = np.clip(q, 0, 1)
p[I['b11']] = 0.4; p[I['b21']] = 0.4
g = classify.family_gap(p)
print("   b11=b21=0.4 -> b41 = %.2f (not a probability); gap %.2e   %s"
      % (2 * 0.4 + 2 * 0.4, g, "ok (rejected)" if g >= 1.0 else "*** ACCEPTED"))
ok &= (g >= 1.0)

print("\n3. a profile moved off the family must still show a large gap\n")
base = F.profile_A(0.125, 0.25)[0]
for d in (1e-6, 1e-4, 1e-2):
    p = base.copy(); p[I['b33']] = min(1.0, p[I['b33']] + d)
    g = classify.family_gap(p)
    det = g > 1e-9
    ok &= det
    print("   b33 perturbed by %.0e -> gap %.2e   %s"
          % (d, g, "ok (detected)" if det else "*** MISSED"))

print("\nCONTROL %s" % ("PASSED" if ok else "FAILED"))
