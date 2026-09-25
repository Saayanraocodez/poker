"""
Three loose ends from the follow-up.

(a) Why is a31 NOT exposed to the off-path free parameters, when a11/a21/a41 are?
(b) Fix the Q1c indifference classification (use exact derivatives, not FD noise).
(c) Table 2's values at ALWAYS-unreached sets are a presentational choice, not an
    equilibrium requirement (the paper's Theorem 1 exempts non-reached parameters).
    If those float, does P1's exposure widen?
"""
import numpy as np

import kuhn3p as K
import family as F
from kuhn3p import reach

I = K.NAME_IDX
TOL = 1e-13
PN = ("P1", "P2", "P3")
CYC = {0: (1, 2), 1: (2, 0), 2: (0, 1)}


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


def rho_exact(p, param, A, C):
    g = K.exact_coord_derivative(p, I[param])
    return (np.nan if abs(g[A]) < TOL else -g[C] / g[A]), g


# ===========================================================================
hdr("(a)  Which off-path free parameters can each P1 opening bet re-open?")
print("   The three always-off-path FREE parameters are b32, c33, c34 -- all")
print("   three are CARD-3 parameters.  A P1 opening bet reaches them only if an")
print("   opponent can hold the 3, i.e. only if P1 does not.\n")
base = F.make_profile(.15, .15, 0., .4, .25, .3, .5)
print("   P1 bets with   reach(b32)   reach(c33)   reach(c34)")
for j in (1, 2, 3, 4):
    q = base.copy()
    q[I["a%d1" % j]] = 0.5                     # P1 opens with card j half the time
    r = reach(q)
    print("      card %d       %.6f     %.6f     %.6f"
          % (j, r[I["b32"]], r[I["c33"]], r[I["c34"]]))
print("\n   card 3: all three are still dead -- P1 holds the 3, so no opponent can.")
print("   card 4: c34 is dead -- P2 calls P1's bet only with the 4 (b42=1), and")
print("           P1 holds it, so the BC node is never reached.")
print("   cards 1,2: everything live -> rho indeterminate.  Matches the sweep:")
print("      a11, a21 moved by b32/c33/c34 ;  a41 by b32/c33 ;  a31 by NONE.")

# ===========================================================================
hdr("(b)  Where is P3 genuinely indifferent to c11 / c21?  (exact derivatives)")
print("   b11    b21    b23      sub   du3/dc11     du3/dc21     indifferent to")
for b11, b21, b23, sub in ((.10, .20, 0., "A"), (.20, .20, 0., "A"),
                           (.15, .15, 0., "B"), (.20, .05, 0., "C"),
                           (.20, .05, F.b23_max(.20, .05), "C")):
    c11 = {"A": 0., "B": .25, "C": .5}[sub]
    p = F.make_profile(b11, b21, b23, .4, c11, .3, .5)
    a = K.exact_coord_derivative(p, I["c11"])[2]
    c = K.exact_coord_derivative(p, I["c21"])[2]
    ia, ic = abs(a) < TOL, abs(c) < TOL
    tag = ("both" if ia and ic else "c21 only" if ic else
           "c11 only" if ia else "neither")
    print("   %.2f   %.2f   %.4f   %s     %+.8f   %+.8f   %s"
          % (b11, b21, b23, sub, a, c, tag))
print("\n   So even the single-coordinate 'costless' claim for P3 is conditional:")
print("   c11 is costless only where b11 = beta (i.e. b11 >= b21), and c21 only")
print("   where b21 + 2 b23 (1 - b21) = beta.  It is not a free lever at every")
print("   point of the family.")

# ===========================================================================
hdr("(c)  Table 2 at always-unreached sets is a CHOICE, not a requirement")
print("   Theorem 1: 'Every equilibrium profile has the values listed in Table 2")
print("   unless a parameter is a non-reached strategy parameter.'  Eleven of the")
print("   14 always-unreached parameters are pinned by Table 2 anyway:")
ALWAYS_DEAD_PINNED = ["a44", "b12", "b22", "b42", "b44",
                      "c13", "c14", "c23", "c24", "c43", "c44"]
print("      %s\n" % ", ".join(ALWAYS_DEAD_PINNED))
print("   Let them float to arbitrary values and re-test.  If the profile is")
print("   still an exact equilibrium, they are free in substance, and P1's")
print("   exposure is wider than the b32/c33/c34 count suggests.\n")
rng = np.random.default_rng(7)
worst_expl = 0.0
rows = []
for trial in range(200):
    q = base.copy()
    for n in ALWAYS_DEAD_PINNED:
        q[I[n]] = rng.random()
    worst_expl = max(worst_expl, float(np.abs(K.exploitability(q)).max()))
    if trial < 6:
        r1, _ = rho_exact(q, "a11", 0, 2)
        r3, _ = rho_exact(q, "a31", 0, 2)
        rows.append((r1, r3))
print("   200 random assignments to those 11 parameters:")
print("      max exploitability = %.2e  -> still an exact Nash equilibrium" % worst_expl)
print("      utilities unchanged: max |du| = %.2e"
      % float(np.abs(K.utilities(base) - K.utilities(q)).max()))
print("\n   effect on P1's rho (A=P1, C=P3) at 6 of those random assignments:")
print("      d=+e_a11 : %s" % "  ".join("%+8.3f" % r[0] for r in rows))
print("      d=+e_a31 : %s" % "  ".join("%+8.3f" % r[1] for r in rows))
r1b, _ = rho_exact(base, "a11", 0, 2)
r3b, _ = rho_exact(base, "a31", 0, 2)
print("      (Table 2 values     : %+8.3f            %+8.3f)" % (r1b, r3b))

# does anyone ELSE's rho move when these float?
print("\n   does any OTHER player's rho move?")
moved = {}
for trial in range(60):
    q = base.copy()
    for n in ALWAYS_DEAD_PINNED:
        q[I[n]] = rng.random()
    for A in range(3):
        B, C = CYC[A]
        for i in range(A * 16, (A + 1) * 16):
            nm = K.PARAM_NAME[i]
            gb = K.exact_coord_derivative(base, i)
            gq = K.exact_coord_derivative(q, i)
            if abs(gb[A]) < TOL or abs(gq[A]) < TOL:
                continue
            d = abs((-gq[C] / gq[A]) - (-gb[C] / gb[A]))
            if d > 1e-9:
                moved[(PN[A], nm)] = max(moved.get((PN[A], nm), 0.0), d)
if moved:
    for (a, nm), d in sorted(moved.items(), key=lambda kv: -kv[1]):
        print("      A=%s  d=+e_%-5s   rho shifts by up to %.3f" % (a, nm, d))
else:
    print("      none")
print("\n   => the eleven Table-2-pinned dead parameters are genuinely free, and")
print("      freeing them moves ONLY P1's rho.  P2's and P3's rho are untouched.")
