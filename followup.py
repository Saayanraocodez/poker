"""
Two follow-up questions.

Q1  Is c11 a free lever, or is moving it just walking A -> B -> C along Table 3's
    own sub-family index?  Distinguish:
      (i)  the IN-FAMILY c11 direction  (c11 and c21 = 1/2 - c11 move together),
      (ii) the single-coordinate deviation +e_c11 (c21 held) which LEAVES the family,
    and ask, for each, whether utilities move and whether the result is still a
    Nash equilibrium.  Compare against P2's beta lever on both counts.

Q2  Is the "never-reached parameter controls the sign of rho" mechanism unique to
    P1?  Locate every unreached information set in the family, classify its
    parameters as PINNED (Tables 2/3 fix a number) or FREE (Table 3 gives an
    interval), and measure which free parameters actually move which rho.
"""
import numpy as np

import kuhn3p as K
import family as F
from kuhn3p import reach

I = K.NAME_IDX
kap = K.KAPPA
TOL = 1e-12
PN = ("P1", "P2", "P3")


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


def du(p, param, h=1e-5):
    d = np.zeros(K.NPARAM)
    d[I[param]] = 1.0
    return K.central_diff(p, d, h)


# ===========================================================================
hdr("Q1a.  Sweeping c11 INSIDE the family: does anything move?")
print("   Path: b11 = b21 = 0.15, b23 = 0, b32/c33 fixed, and c21 = 1/2 - c11")
print("   as Table 3 requires.  b11 = b21 <= 1/6 keeps every sub-family's")
print("   constraints satisfiable, so c11 can run 0 -> 1/2 without leaving the")
print("   family.  c11 = 0 is sub-family A, 0<c11<1/2 is B, c11 = 1/2 is C.\n")
b = 0.15
print("   c11      sub-family   u1          u2          u3          exploitability")
for c11 in (0.0, 0.05, 0.15, 0.25, 0.35, 0.45, 0.5):
    p = F.make_profile(b, b, 0.0, 0.4, c11, 0.3, 0.5)
    sub = "A" if c11 == 0 else ("C" if c11 == 0.5 else "B")
    u, e = K.utilities(p), K.exploitability(p)
    print("   %.2f     %s            %+.8f  %+.8f  %+.8f   %.1e"
          % (c11, sub, u[0], u[1], u[2], np.abs(e).max()))
p0 = F.make_profile(b, b, 0., 0.4, 0.0, 0.3, 0.5)
p1 = F.make_profile(b, b, 0., 0.4, 0.5, 0.3, 0.5)
print("\n   u(c11=1/2) - u(c11=0) = %s" % np.round(K.utilities(p1) - K.utilities(p0), 15))
print("   The in-family c11 direction (d = +e_c11 - e_c21):")
d = np.zeros(K.NPARAM)
d[I["c11"]], d[I["c21"]] = 1.0, -1.0
pm = F.make_profile(b, b, 0., 0.4, 0.25, 0.3, 0.5)
print("      du/d eps = %s" % np.round(K.central_diff(pm, d, 1e-5), 12))
print("\n   => the in-family c11 lever is NULL, not a transfer.  It changes")
print("      nobody's utility, because Table 3's utilities depend only on beta,")
print("      and beta = max{b11,b21} is made entirely of P2's parameters.")

# ===========================================================================
hdr("Q1b.  The single-coordinate deviations: do they stay equilibria?")
print("   A costless direction is only a *transfer* in the paper's sense if the")
print("   profile you land on is still a Nash equilibrium.  Test at finite eps.\n")
CASES = [
    ("P2  +e_b11  (single coord, leaves family)", 1, "b11",
     lambda e: F.make_profile(.15 + e, .15, 0., .4, .25, .3, .5)),
    ("P2  beta    (IN-family: b11,b21,b33,b41)", 1, None,
     lambda e: F.make_profile(.15 + e, .15 + e, 0., .4, .25, .3, .5)),
    ("P3  +e_c11  (single coord, leaves family)", 2, "c11",
     lambda e: None),
    ("P3  +e_c21  (single coord, leaves family)", 2, "c21",
     lambda e: None),
    ("P3  in-family c11 (c11 and c21 together)", 2, None,
     lambda e: F.make_profile(.15, .15, 0., .4, .25 + e, .3, .5)),
]
base = F.make_profile(.15, .15, 0., .4, .25, .3, .5)
print("   %-42s %-26s %s" % ("direction", "du/d eps", "exploitability at eps"))
print("   %-42s %-26s %s" % ("", "", "0.00     0.02     0.05"))
print("   " + "-" * 74)
for lbl, A, coord, mk in CASES:
    if coord in ("c11", "c21"):
        def mk(e, coord=coord):
            q = base.copy()
            q[I[coord]] += e
            return q
    d0 = (K.utilities(mk(1e-5)) - K.utilities(mk(-1e-5))) / 2e-5
    es = [np.abs(K.exploitability(mk(e))).max() for e in (0.0, 0.02, 0.05)]
    print("   %-42s [%+.4f %+.4f %+.4f]  %.1e  %.1e  %.1e"
          % (lbl, d0[0], d0[1], d0[2], es[0], es[1], es[2]))
print("\n   (base point: sub-family B, b11=b21=0.15, c11=0.25)")

# ===========================================================================
hdr("Q1c.  Where is P3's c11/c21 deviation actually costless?")
print("   Paper's Lemma 3:  du3/dc11 = k(2 b11 - 2 beta)")
print("                     du3/dc21 = k(2 b21 - 2 beta + 4 b23 (1 - b21))\n")
print("   b11    b21    b23     sub   du3/dc11    du3/dc21    costless?")
for b11, b21, b23, sub in ((.10, .20, 0., "A"), (.20, .20, 0., "A"),
                           (.15, .15, 0., "B"), (.20, .05, 0., "C"),
                           (.20, .05, F.b23_max(.20, .05), "C")):
    c11 = {"A": 0., "B": .25, "C": .5}[sub]
    p = F.make_profile(b11, b21, b23, .4, c11, .3, .5)
    a = K.exact_coord_derivative(p, I["c11"])[2]
    c = K.exact_coord_derivative(p, I["c21"])[2]
    tag = ("both" if abs(a) < 1e-13 and abs(c) < 1e-13 else
           "c21 only" if abs(c) < 1e-13 else "c11 only" if abs(a) < 1e-13 else "neither")
    print("   %.2f   %.2f   %.4f  %s     %+.6f   %+.6f   %s"
          % (b11, b21, b23, sub, a, c, tag))

# ===========================================================================
hdr("Q2a.  Which information sets are unreached in the family, and why?")



p = F.make_profile(.15, .15, 0., .4, .25, .3, .5)
r = reach(p)
print("   sanity: reach of P1's root sets (should be 6/24 = 0.25 each): %s"
      % np.round([r[I["a%d1" % j]] for j in (1, 2, 3, 4)], 6))
unreached = [K.PARAM_NAME[i] for i in range(K.NPARAM) if r[i] < 1e-14]
print("\n   UNREACHED at a generic family point (%d of 48):" % len(unreached))
print("      %s" % ", ".join(unreached))
FREE = {"b11", "b21", "b23", "b32", "c11", "c33", "c34"}
print("\n   of those, FREE in Table 3 (an interval, not a fixed number):")
print("      %s" % ", ".join(n for n in unreached if n in FREE))
print("   the rest are PINNED to a number by Table 2 or Table 3.")
print("\n   Every unreached set sits behind P1's opening bet: Table 3 forces")
print("   a11 = a21 = a31 = a41 = 0, so P2 never faces a bet (b_j2 dead) and")
print("   P3 never reaches BF/BC (c_j3, c_j4 dead).  ONLY P1 can unilaterally")
print("   re-open that subtree -- P2 and P3 cannot make P1 bet.")

# ===========================================================================
hdr("Q2b.  Which free parameters actually move which rho?")
CYC = {0: (1, 2), 1: (2, 0), 2: (0, 1)}


def rho_grid(P, A, C, i):
    d = np.zeros(K.NPARAM)
    d[i] = 1.0
    D = (K.utilities_batch(P + 1e-5 * d) - K.utilities_batch(P - 1e-5 * d)) / 2e-5
    dA = D[:, A]
    out = np.where(np.abs(dA) > 1e-10, -D[:, C] / np.where(dA == 0, 1, dA), np.nan)
    return out


# product grid over sub-family C (the one with all six free axes)
AX = dict(b11=np.linspace(.02, .16, 4), s21=np.linspace(0, 1, 3),
          t_b23=np.linspace(0, 1, 3), t_b32=np.linspace(0, 1, 4),
          t_c33=np.linspace(.05, 1, 4), c34=np.linspace(0, 1, 3))
names = list(AX)
shape = tuple(len(AX[n]) for n in names)
pts = []
for b11 in AX["b11"]:
    for s in AX["s21"]:
        b21 = s * min(b11, .5 - 2 * b11)
        for t23 in AX["t_b23"]:
            for t32 in AX["t_b32"]:
                for t33 in AX["t_c33"]:
                    for c34 in AX["c34"]:
                        pts.append(F.profile_C(b11, b21, t23, t32, t33, c34)[0])
P = np.array(pts)
print("   product grid over sub-family C: %s = %d points" % (shape, len(P)))
print("   (axes: %s)\n" % ", ".join(names))
print("   rho varies along axis ->            b11    b21    b23    b32    c33    c34")
print("   " + "-" * 74)
rows = []
for A in range(3):
    B, C = CYC[A]
    for i in range(A * 16, (A + 1) * 16):
        R = rho_grid(P, A, C, i).reshape(shape)
        if np.all(np.isnan(R)):
            continue
        spans = []
        for k in range(len(names)):
            v = np.nanmax(R, axis=k) - np.nanmin(R, axis=k)
            spans.append(0.0 if np.all(np.isnan(v)) else float(np.nanmax(v)))
        if max(spans) < 1e-9 and not np.any(np.isnan(R)):
            tag = "constant"
        else:
            tag = ""
        rows.append((A, K.PARAM_NAME[i], spans, np.nanmin(R), np.nanmax(R), tag))
        print("   A=%s  d=+e_%-5s  %-12s %s"
              % (PN[A], K.PARAM_NAME[i], "[%+.3f,%+.3f]" % (np.nanmin(R), np.nanmax(R)),
                 "  ".join("%6s" % ("%.3f" % s if s > 1e-9 else ".") for s in spans)))

print("\n   ('.' = rho is exactly invariant to that free parameter)")
offpath = [n for n in ("b32", "c33", "c34")]
idx = [names.index(x) for x in ("t_b32", "t_c33", "c34")]
print("\n   rho values moved by an OFF-PATH free parameter (b32 / c33 / c34):")
any_off = False
for A, nm, spans, lo, hi, tag in rows:
    hit = [o for o, k in zip(offpath, idx) if spans[k] > 1e-9]
    if hit:
        any_off = True
        print("      A=%s  d=+e_%-5s   moved by %s   rho in [%+.3f, %+.3f]"
              % (PN[A], nm, "/".join(hit), lo, hi))
if not any_off:
    print("      (none)")
print("\n   rho values moved ONLY by on-path free parameters (b11/b21/b23/c11):")
for A, nm, spans, lo, hi, tag in rows:
    hit = [o for o, k in zip(offpath, idx) if spans[k] > 1e-9]
    if not hit and max(spans) > 1e-9:
        print("      A=%s  d=+e_%-5s   rho in [%+.3f, %+.3f]" % (PN[A], nm, lo, hi))
print("\n   rho values that are rigid constants of the whole family:")
for A, nm, spans, lo, hi, tag in rows:
    if tag == "constant":
        print("      A=%s  d=+e_%-5s   rho = %+.4f" % (PN[A], nm, lo))

# ===========================================================================
hdr("Q2c.  The control: at beta = 0, P2's bet subtree is off-path too")
print("   At b11 = b21 = b41 = 0 (beta = 0) P2 never bets either, so P3's KB set")
print("   (c_j2) and P1's KBF/KBC sets (a_j3, a_j4) are ALSO unreached.  If the")
print("   mechanism were about off-path-ness alone, P2's deviation into that")
print("   subtree would be indeterminate too.  It is not:\n")
p0 = F.make_profile(0., 0., 0., 0., 0., .5, 0.)
r0 = reach(p0)
dead = [K.PARAM_NAME[i] for i in range(K.NPARAM) if r0[i] < 1e-14]
print("   unreached at beta=0 (%d of 48): %s" % (len(dead), ", ".join(dead)))
print("   of those, FREE in Table 3: %s"
      % (", ".join(n for n in dead if n in FREE) or "(none beyond b32/c33/c34)"))
newly = [n for n in dead if n not in unreached]
print("\n   newly dead relative to a generic point: %s" % ", ".join(newly))
print("   FREE among them: %s" % (", ".join(n for n in newly if n in FREE) or "NONE"))
print("\n   Every parameter in the subtree P2's bet re-opens is PINNED:")
for n in ("c12", "c22", "c32", "c42", "a13", "a23", "a33", "a43"):
    print("      %s = %s" % (n, {0.0: "0", 1.0: "1", 0.5: "1/2"}[float(p0[I[n]])]),
          end="   " if n != "a43" else "\n")
print("   -> rho for P2's bet deviation has no free parameter to depend on,")
print("      which is exactly why rho(b31) = 3/5 is rigid.")
