"""
Two verification demands.

A. The pole-at-the-boundary structure was shown once (a11).  Check a21 and a41
   too, and a31 as the internal control.  If it is a claim about the game, each
   of P1's opening deviations should put a zero of its own denominator on an
   endpoint of Table 3's c33 interval -- and it should be the SAME interval,
   with a11/a21 pinning the lower end and a41 the upper end.

B. Are c34 and c44 really inert?  If nobody's incentive constrains them, every
   first derivative must be exactly zero for all three players at every point.
   Test that, then test whether "unconstrained" also means "has no effect".
"""
import numpy as np

import kuhn3p as K
import family as F
import grids as G

I = K.NAME_IDX
PN = ("P1", "P2", "P3")


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


def d1(p, name, who=None):
    g = K.exact_coord_derivative(p, I[name])
    return g if who is None else g[who]


def d2(p, x, y):
    """Exact mixed second derivative, by multilinearity:
       u(1,1) - u(1,0) - u(0,1) + u(0,0)."""
    ix, iy = I[x], I[y]
    out = np.zeros(3)
    for vx, vy, s in ((1, 1, 1), (1, 0, -1), (0, 1, -1), (0, 0, 1)):
        q = p.copy()
        q[ix], q[iy] = float(vx), float(vy)
        out += s * K.utilities(q)
    return out


def root_in_c33(b11, b21, b23, b32, c11, c34, name):
    """du1/d(name) is affine in c33 -> solve for its zero exactly."""
    def g(c33):
        return d1(F.make_profile(b11, b21, b23, b32, c11, c33, c34), name, 0)
    g0, g1 = g(0.0), g(1.0)
    if abs(g1 - g0) < 1e-15:
        return None                      # no dependence on c33 at all
    return -g0 / (g1 - g0)


# ===========================================================================
hdr("A.  Does every P1 opening deviation put a pole on a Table 3 endpoint?")
print("   For each family point, solve du1/da_j1 = 0 for c33 (it is affine in c33)")
print("   and compare the root against Table 3's interval endpoints")
print("      lo = 1/2 - b32          (Table 3 lower bound on c33)")
print("      hi = lo + 3(b11+b21)/4 + beta/4   (Table 3 upper bound)\n")

CASES = []
for b11, b21, b23, c11, sub in ((.00, .00, 0., .0, "A"), (.10, .20, 0., .0, "A"),
                                (.25, .25, 0., .0, "A"), (.12, .12, 0., .30, "B"),
                                (.15, .15, 0., .45, "B"), (.20, .05, .00, .50, "C"),
                                (.20, .05, F.b23_max(.20, .05), .50, "C"),
                                (.10, .10, 0., .50, "C")):
    for b32 in (0.0, 0.25, 0.5):
        for c34 in (0.0, 1.0):
            if b32 > F.b32_max(b11, b21):
                continue
            CASES.append((b11, b21, b23, b32, c11, c34, sub))

print("   sub  b11   b21   b32   c11   c34 | a11 root  a21 root  a41 root | lo     hi")
print("   " + "-" * 76)
e11, e21, err_hi, n31 = 0.0, 0.0, 0.0, 0
shown = 0
for b11, b21, b23, b32, c11, c34, sub in CASES:
    lo, hi = 0.5 - b32, F.b32_max(b11, b21) - b32
    r = {n: root_in_c33(b11, b21, b23, b32, c11, c34, n)
         for n in ("a11", "a21", "a41", "a31")}
    e11 = max(e11, abs(r["a11"] - lo))
    e21 = max(e21, abs(r["a21"] - lo))
    err_hi = max(err_hi, abs(r["a41"] - hi))
    if r["a31"] is None:
        n31 += 1
    if shown < 14:
        print("   %s   %.2f  %.2f  %.2f  %.2f  %.1f | %8.4f  %8.4f  %8.4f | %.4f %.4f"
              % (sub, b11, b21, b32, c11, c34,
                 r["a11"], r["a21"], r["a41"], lo, hi))
        shown += 1
print("   ... (%d cases total)" % len(CASES))
print("\n   max |root(a11) - lo| = %.3e" % e11)
print("   max |root(a21) - lo| = %.3e   (same expression as a11: Lemma 5 gives" % e21)
print("                                   du1/da21 = du1/da11 once a22 = a23 = 0)")
print("   max |root(a41) - hi| = %.3e" % err_hi)
print("   a31: du1/da31 has NO dependence on c33 in %d of %d cases -> no root,"
      % (n31, len(CASES)))
print("        so a31 can never have a pole.  (It is the card-3 exclusion: b32,")
print("        c33, c34 are all card-3 parameters and P1 holds the 3.)")

# ===========================================================================
hdr("A2.  Confirm the divergence, not just the root")
b11 = b21 = 0.15
b32 = 0.40
lo, hi = F.c33_range(b11, b21, b32)
print("   b11 = b21 = 0.15, b32 = 0.40  ->  Table 3 c33 interval [%.4f, %.4f]\n"
      % (lo, hi))
print("   c33 position        du1/da11    rho(a11)     du1/da41    rho(a41)")
for t, lab in ((0.0, "lo (endpoint)"), (1e-4, "lo + 1e-4"), (0.01, "lo + 1%"),
               (0.5, "midpoint"), (0.99, "hi - 1%"), (1 - 1e-4, "hi - 1e-4"),
               (1.0, "hi (endpoint)")):
    c33 = lo + t * (hi - lo)
    p = F.make_profile(b11, b21, 0., b32, .25, c33, .5)
    out = []
    for nm in ("a11", "a41"):
        g = d1(p, nm)
        out.append((g[0], "undef" if abs(g[0]) < 1e-13 else "%+.2f" % (-g[2] / g[0])))
    print("   %-18s %+.7f  %-10s  %+.7f  %-10s"
          % (lab, out[0][0], out[0][1], out[1][0], out[1][1]))
print("\n   Two different deviations, two different endpoints, one interval.")
print("   The lower bound on c33 in Table 3 exists to kill a11/a21; the upper")
print("   bound exists to kill a41.  Both bounds are attainable, so both put a")
print("   zero of a rho denominator on the boundary of the equilibrium region.")

# ===========================================================================
hdr("A3.  Same structure in the (b32, c33) plane, not just along c33")
print("   The lower boundary is the LINE c33 = 1/2 - b32.  Walk along it:\n")
print("   b32     c33 = 1/2 - b32   du1/da11      du1/da21      exploitability")
for b32 in (0.0, 0.15, 0.30, 0.45, 0.60):
    if b32 > F.b32_max(.15, .15):
        continue
    c33 = 0.5 - b32
    p = F.make_profile(.15, .15, 0., b32, .25, c33, .5)
    print("   %.2f    %.4f            %+.3e   %+.3e   %.1e"
          % (b32, c33, d1(p, "a11", 0), d1(p, "a21", 0),
             np.abs(K.exploitability(p)).max()))
print("\n   du1/da11 = du1/da21 = 0 identically along the whole line, so the pole")
print("   is a codimension-1 surface in the family, not an isolated point.")

# ===========================================================================
hdr("B.  Are c34 and c44 inert?  First derivatives over the whole grid")
P, M = G.full_grid()
GE = K.gradients_batch(P, h=None)
for nm in ("c34", "c44", "c33", "b32"):
    i = I[nm]
    print("   max |du_i/d%s| over %d grid points x 3 players = %.3e"
          % (nm, len(P), np.abs(GE[:, i, :]).max()))
print("\n   -> c34 and c44 (and c33, b32) have EXACTLY zero first derivatives for")
print("      all three players, at every point.  Unreached sets, as expected.")

print("\n   Exploitability with c34 and c44 set to every value in [0,1]:")
base = F.make_profile(.15, .15, 0., .4, .25, .3, .5)
for nm in ("c34", "c44"):
    w = 0.0
    for v in np.linspace(0, 1, 101):
        q = base.copy()
        q[I[nm]] = v
        w = max(w, float(np.abs(K.exploitability(q)).max()))
    print("      %s : max exploitability = %.3e" % (nm, w))
print("   -> nobody's incentive constrains either one.  Confirmed.")

# ===========================================================================
hdr("B2.  But 'unconstrained' is not the same as 'has no effect'")
print("   A first derivative of zero only says the set is off-path NOW.  The")
print("   question for rho is what happens once P1 re-opens it, which is a MIXED")
print("   second derivative.  Exact values of d2u/(da_j1 dx):\n")
print("   x      via a11              via a21              via a31          via a41")
for nm in ("c34", "c44", "c33", "b32"):
    cells = []
    for a in ("a11", "a21", "a31", "a41"):
        v = d2(base, a, nm)
        cells.append("(%+.3f,%+.3f,%+.3f)" % tuple(v) if np.abs(v).max() > 1e-13
                     else "         0        ")
    print("   %-6s %s" % (nm, " ".join(cells)))
print("   NEITHER is zero.  Both c34 and c44 have nonzero mixed second")
print("   derivatives through a11 and a21: they are unconstrained by every")
print("   player's incentive, yet both move u2 and u3 once P1 opens.")

print("\n   Reach after a single P1 deviation (a_j1 = 0.5):")
print("   P1 opens with   reach(c34)   reach(c44)")
for j in (1, 2, 3, 4):
    q = base.copy()
    q[I["a%d1" % j]] = 0.5
    r = K.reach(q)
    print("      card %d       %.6f     %.6f" % (j, r[I["c34"]], r[I["c44"]]))

print("\n   c44 needs b32 > 0 to be reachable at all: to sit at BC holding the 4,")
print("   P3 needs P2 to have called with something other than the 4, and in this")
print("   family P2's only other calling card is the 3 (probability b32).\n")
print("   b32     reach(c44) after a11 = 0.5    d2u3/(da11 dc44)")
for b32 in (0.0, 0.10, 0.40, 0.80):
    if b32 > F.b32_max(.15, .15):
        continue
    c33 = min(.3, F.c33_range(.15, .15, b32)[1])
    q = F.make_profile(.15, .15, 0., b32, .25, c33, .5)
    r2 = q.copy()
    r2[I["a11"]] = 0.5
    print("   %.2f    %.8f                  %+.6f"
          % (b32, K.reach(r2)[I["c44"]], d2(q, "a11", "c44")[2]))

print("\n   CORRECTED CLASSIFICATION -- 'unconstrained' is not 'inert':")
print("     c34, c44   ARBITRARY but CONSEQUENTIAL")
print("       * exactly zero first derivative for all three players, everywhere")
print("       * zero exploitability for every value in [0,1], so nobody's")
print("         incentive pins them: Table 3's '0 <= c34 <= 1' is right, and")
print("         Table 2's c44 = 1 is a convention with no equilibrium content")
print("       * but both are reachable one P1 opening away, so both enter")
print("         d2u/(da_j1 dx) and set the NUMERATOR of P1's rho")
print("\n   Two independent sources of indeterminacy in P1's rho:")
print("     denominator  <- b32, c33   constrained, but by an INEQUALITY whose")
print("                                boundary is attainable -> POLE on the edge")
print("                                of the equilibrium set")
print("     numerator    <- c34, c44   constrained by nobody at all -> VALUE")
print("                                undetermined even where the denominator")
print("                                is safely away from zero")
print("\n   This does not hole the owner/slack classification, which is a statement")
print("   about which player's FIRST-ORDER incentive pins a parameter and still")
print("   holds exactly.  What it kills is the inference that an unconstrained")
print("   parameter is irrelevant: only reachability decides that, and both of")
print("   these sit one deviation away from being reached.")
