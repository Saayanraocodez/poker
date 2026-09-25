"""
Correcting loose end (c).

The guess was: Table 2's values at always-unreached sets are arbitrary, because
Theorem 1 exempts non-reached parameters.  That is FALSE as a statement about the
profile.  Theorem 1 exempts them from *the owner's* incentive constraint, but an
off-path parameter still sits inside somebody ELSE's incentive constraint -- it is
the threat that keeps that other player off the path in the first place.

So: which of the 14 always-unreached parameters are genuinely arbitrary, which are
deterrence-constrained, and whose incentive constrains them?
"""
import numpy as np

import kuhn3p as K
import family as F

I = K.NAME_IDX
PN = ("P1", "P2", "P3")
base = F.make_profile(.15, .15, 0., .4, .25, .3, .5)
DEAD = ["a44", "b12", "b22", "b32", "b42", "b44",
        "c13", "c14", "c23", "c24", "c33", "c34", "c43", "c44"]
FREE_IN_T3 = {"b32", "c33", "c34"}


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


hdr("(c1)  Float each always-unreached parameter alone.  Who objects?")
print("   The set is off-path, so the OWNER is always indifferent.  The question")
print("   is whether some other player now wants to enter that subtree.\n")
print("   param  owner  Table 3 says   max exploitability   who becomes")
print("                                over v in [0,1]      exploitable")
print("   " + "-" * 70)
for n in DEAD:
    owner = PN[I[n] // 16]
    worst, who = 0.0, "-"
    for v in np.linspace(0, 1, 21):
        q = base.copy()
        q[I[n]] = v
        e = K.exploitability(q)
        if np.abs(e).max() > worst:
            worst, who = float(np.abs(e).max()), PN[int(np.argmax(e))]
    says = "free interval" if n in FREE_IN_T3 else "pinned to %g" % base[I[n]]
    verdict = "ARBITRARY" if worst < 1e-12 else who
    print("   %-6s %-6s %-14s %.3e            %s"
          % (n, owner, says, worst, verdict))

hdr("(c2)  So what actually constrains the off-path parameters?")
print("   P1's deterrence conditions, from the paper's Lemma 5:")
print("      du1/da11 = k(2 - 4 b32 - 4 c33)   <= 0   <=>   c33 >= 1/2 - b32")
print("      du1/da41 <= 0                     <=>   c33 <= 1/2 - b32 + 3(b11+b21)/4 + beta/4")
print("   Those two inequalities ARE Table 3's c33 interval.  Check numerically")
print("   by walking c33 across and past both endpoints (b11=b21=0.15, b32=0.4):\n")
b11 = b21 = 0.15
b32 = 0.40
lo, hi = F.c33_range(b11, b21, b32)
print("   Table 3 interval for c33: [%.4f, %.4f]\n" % (lo, hi))
print("     c33      du1/da11    du1/da41    P1 exploitability   in Table 3?")
for c33 in (lo - .10, lo - .02, lo, (lo + hi) / 2, hi, hi + .02, hi + .10):
    if not 0 <= c33 <= 1:
        continue
    q = F.make_profile(b11, b21, 0., b32, .25, min(max(c33, 0), 1), .5)
    g11 = K.exact_coord_derivative(q, I["a11"])[0]
    g41 = K.exact_coord_derivative(q, I["a41"])[0]
    e = K.exploitability(q)[0]
    inside = "yes" if lo - 1e-12 <= c33 <= hi + 1e-12 else "NO"
    print("    %6.3f   %+.6f   %+.6f    %.3e           %s"
          % (c33, g11, g41, e, inside))
print("\n   The interval endpoints are exactly where P1's two deterrence")
print("   derivatives hit zero.  Outside it, P1 strictly gains by opening and")
print("   the profile stops being an equilibrium.")

hdr("(c3)  Why this makes P1 the only player exposed")
print("   rho for P1's opening deviation is")
print("      rho = -(du3/da_j1) / (du1/da_j1)")
print("   and du1/da_j1 is precisely the quantity Table 3 constrains to be <= 0")
print("   in order to keep P1 from opening.  A constraint of the form 'X <= 0'")
print("   with X free to reach its boundary puts a ZERO of the denominator on")
print("   the boundary of the feasible set.  So P1's rho MUST have a pole on the")
print("   edge of its own deterrence condition -- it is structural, not accidental.\n")
print("   P2 and P3 have no analogue because no member of the family leaves their")
print("   opening decision off-path with free parameters behind it:")
print("     - at beta > 0 P2 does open (b11,b21,b41 > 0), so nothing behind P2's")
print("       bet is off-path at all;")
print("     - at beta = 0 P2's bet subtree IS off-path, but every parameter in it")
print("       (c12,c22,c32,c42,a13,a23,a33,a43) is pinned -- by Table 2 dominance")
print("       or by Table 3 -- because those same sets are ON-path whenever")
print("       beta > 0, so the equilibrium conditions already fix them;")
print("     - P3 acts last, so no subtree sits behind a P3 opening bet that is")
print("       off-path for the whole family.")
print("\n   Confirm the middle bullet: are c12,c22,c32,c42,a13,a23,a33,a43 pinned")
print("   by incentives rather than convention?  Float each at beta = 0:\n")
p0 = F.make_profile(0., 0., 0., 0., 0., .5, 0.)
print("   param  value  max exploitability over v in [0,1]   who objects")
for n in ("c12", "c22", "c32", "c42", "a13", "a23", "a33", "a43"):
    worst, who = 0.0, "-"
    for v in np.linspace(0, 1, 21):
        q = p0.copy()
        q[I[n]] = v
        e = K.exploitability(q)
        if np.abs(e).max() > worst:
            worst, who = float(np.abs(e).max()), PN[int(np.argmax(e))]
    print("   %-6s %-6g %.3e                            %s"
          % (n, p0[I[n]], worst, who if worst > 1e-12 else "ARBITRARY"))
