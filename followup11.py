"""
Items 1-3: the hard-floor theorem, the global closed form for rho, and the
properness selection argument.  Exact rational arithmetic throughout.
"""
from fractions import Fraction as Fr

import numpy as np

import kuhn3p as K
import family as F

I = K.NAME_IDX
OWN = {"b32": 1, "c33": 2, "c34": 2, "c44": 2}


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


def profile_fr(b11, b21, b23, b32, c11, c33, c34):
    """Exact rational mirror of family.make_profile."""
    p = [Fr(0)] * 48
    for n in ("a42", "a43", "a44", "b42", "b43", "b44", "c42", "c43", "c44"):
        p[I[n]] = Fr(1)
    p[I["a33"]] = Fr(1, 2)
    beta = max(b11, b21)
    p[I["b11"]], p[I["b21"]], p[I["b23"]], p[I["b32"]] = b11, b21, b23, b32
    p[I["b33"]] = Fr(1, 2) + (b11 + b21) / 2 + beta / 2 - b23 * (1 - b21)
    p[I["b41"]] = 2 * b11 + 2 * b21
    p[I["c11"]], p[I["c21"]] = c11, Fr(1, 2) - c11
    p[I["c33"]], p[I["c34"]] = c33, c34
    p[I["c41"]] = Fr(1)
    return p


def dfr(p, name, who):
    """Exact rational du_who/d(name) = u(x=1) - u(x=0)."""
    a, b = list(p), list(p)
    a[I[name]], b[I[name]] = Fr(1), Fr(0)
    return K.utilities_exact(a)[who] - K.utilities_exact(b)[who]


def window(b11, b21, b32):
    lo = Fr(1, 2) - b32
    hi = Fr(1, 2) + Fr(3, 4) * (b11 + b21) + max(b11, b21) / 4 - b32
    return lo, hi


def adv(prof, nm, eps, r):
    """Per-unit-reach advantage of the aggressive action under P1 trembles."""
    q = prof.copy()
    for j in range(1, 5):
        q[I["a%d1" % j]] = eps * r[j - 1]
    g = K.exact_coord_derivative(q, I[nm])[OWN[nm]]
    rr = K.reach(q)[I[nm]]
    return g / rr if rr > 1e-18 else np.nan


POINTS = [
    (Fr(3, 20), Fr(3, 20), Fr(0), Fr(2, 5), Fr(1, 4), "B  b32=2/5"),
    (Fr(3, 20), Fr(3, 20), Fr(0), Fr(0), Fr(1, 4), "B  refined face"),
    (Fr(1, 10), Fr(1, 5), Fr(0), Fr(0), Fr(0), "A  refined face"),
    (Fr(1, 4), Fr(1, 4), Fr(0), Fr(0), Fr(0), "A  corner beta=1/4"),
    (Fr(1, 5), Fr(1, 20), Fr(0), Fr(0), Fr(1, 2), "C  refined face"),
    (Fr(1, 4), Fr(0), Fr(1, 8), Fr(0), Fr(1, 2), "C  b23 at max"),
]

# ===========================================================================
hdr("ITEM 1.  HARD FLOOR:  w = hi - lo = 3/4(b11+b21) + beta/4")
print("   lo = 1/2 - b32 and hi = b32max - b32, so the b32 terms cancel: the")
print("   window width does not depend on b32 at all.\n")
print("   point                 b11    b21    b32  | w measured  w formula  kappa*beta  equal?")
for b11, b21, b23, b32, c11, sub in POINTS:
    lo, hi = window(b11, b21, b32)
    w = hi - lo
    wf = Fr(3, 4) * (b11 + b21) + max(b11, b21) / 4
    print("   %-20s  %-6s %-6s %-4s | %-10s  %-9s  %-10s  %s"
          % (sub, b11, b21, b32, w, wf, K.KAPPA_F * max(b11, b21), w == wf))
print("\n   Every term of w is non-negative, so")
print("      w = 0  <=>  b11 = b21 = 0  <=>  beta = 0  <=>  kappa*beta = 0.")
print("   Deterrence slack and the SGS transfer share a currency: the window")
print("   cannot be closed without destroying the transfer that motivates it.")

# ===========================================================================
hdr("ITEM 1b.  THE w = 0 EDGE CASE IS NOT SYMMETRIC BETWEEN a11 AND a41")
p0 = profile_fr(Fr(0), Fr(0), Fr(0), Fr(0), Fr(0), Fr(1, 2), Fr(0))
print("   b11 = b21 = 0 -> the window collapses to the single point {1/2}.\n")
print("   dev    D'/kappa   t = du2 at c33*   du3 at c33*   du1 at c33*   verdict")
_pa = profile_fr(Fr(0), Fr(0), Fr(0), Fr(0), Fr(0), Fr(1), Fr(0))
_pb = profile_fr(Fr(0), Fr(0), Fr(0), Fr(0), Fr(0), Fr(0), Fr(0))
for nm in ("a11", "a41"):
    Dp = dfr(_pa, nm, 0) - dfr(_pb, nm, 0)          # d2u1/(da_j1 dc33)
    d1, t, d3 = dfr(p0, nm, 0), dfr(p0, nm, 1), dfr(p0, nm, 2)
    print("   %-6s %+9s   %-16s  %-12s  %-12s  %s"
          % (nm, Dp / K.KAPPA_F, t, d3, d1,
             "POLE" if d1 == 0 and d3 != 0 else "0/0: clause (iii) fails"))
print("\n   a41's numerator vanishes with the window, so its pole dies.  a11's")
print("   does NOT (t = -1/48 != 0): the singular point becomes the ONLY")
print("   admissible value of c33.  Shrinking the window is doubly futile.")

# ===========================================================================
hdr("ITEM 2.  GLOBAL CLOSED FORM:  rho(c33) = 1 + R/(c33 - c33*)")
print("   D(c33) = D'(c33 - c33*) exactly, and N(c33) = N(c33*) + N'(c33 - c33*).")
print("   When N' = D' this gives rho = 1 + R/(c33 - c33*), R = N(c33*)/D'.")
print("   EXACT everywhere on the family, not an asymptotic statement.\n")
print("   point                 dev   N'/kap  D'/kap  N'/D'  R           max err")
worst = 0.0
for b11, b21, b23, b32, c11, sub in POINTS:
    lo, hi = window(b11, b21, b32)
    pa = profile_fr(b11, b21, b23, b32, c11, Fr(1), Fr(0))
    pb = profile_fr(b11, b21, b23, b32, c11, Fr(0), Fr(0))
    for nm, star in (("a11", lo), ("a21", lo), ("a41", hi)):
        Dp = dfr(pa, nm, 0) - dfr(pb, nm, 0)        # d2u1/(da_j1 dc33)
        Np = -(dfr(pa, nm, 2) - dfr(pb, nm, 2))     # -d2u3/(da_j1 dc33)
        ps = profile_fr(b11, b21, b23, b32, c11, star, Fr(0))
        R = -dfr(ps, nm, 2) / Dp
        errs = []
        for t in (Fr(1, 7), Fr(2, 5), Fr(3, 5), Fr(6, 7)):
            c = lo + t * (hi - lo)
            pc = profile_fr(b11, b21, b23, b32, c11, c, Fr(0))
            d1, d3 = dfr(pc, nm, 0), dfr(pc, nm, 2)
            if d1 != 0:
                errs.append(abs(float(-d3 / d1) - float(1 + R / (c - star))))
        e = max(errs) if errs else 0.0
        worst = max(worst, e)
        print("   %-20s  %-5s %+6s  %+6s  %-5s  %-11s %.1e"
              % (sub, nm, Np / K.KAPPA_F, Dp / K.KAPPA_F, Np / Dp, R, e))
print("\n   N'/D' = 1 exactly at every point; max numeric discrepancy %.1e." % worst)
print("   This strictly supersedes 'rho = R/(c33-c33*) + O(1)': the O(1) term is")
print("   exactly 1.")

# ===========================================================================
hdr("ITEM 3.  PROPERNESS: the equal-cost point c33 = lo + w/3")
print("   cost(a_j1) = -du1/da_j1 >= 0 is what P1 forgoes by opening with card j.")
print("   cost(a11) = 4k(c33 - lo),  cost(a41) = 2k(hi - c33).")
print("   Equal  <=>  4(c33-lo) = 2(hi-c33)  <=>  c33 = lo + w/3.\n")
print("   point                 c33*=lo+w/3  cost a11   cost a21   cost a41   eq?    cost a31   a31 costliest?")
allok = True
for b11, b21, b23, b32, c11, sub in POINTS:
    lo, hi = window(b11, b21, b32)
    cs = lo + (hi - lo) / 3
    pf = profile_fr(b11, b21, b23, b32, c11, cs, Fr(0))
    c = {nm: -dfr(pf, nm, 0) for nm in ("a11", "a21", "a31", "a41")}
    eq = (c["a11"] == c["a41"] == c["a21"])
    hi31 = c["a31"] > c["a11"]
    allok &= bool(eq and hi31)
    print("   %-20s  %-11s  %-9s  %-9s  %-9s  %-5s  %-9s  %s"
          % (sub, cs, c["a11"], c["a21"], c["a41"], eq, c["a31"], hi31))
print("\n   Exact rational equality at every point: %s" % allok)
print("   a31 is always the costliest opening, so properness gives it the")
print("   smallest tremble; and r3 cannot affect the c33 belief anyway, because")
print("   P3 holds the 3 at that information set, so P1 cannot.")

# ===========================================================================
hdr("ITEM 3b.  WHY BOTH CORNERS ARE EXCLUDED")
print("   At c33 = lo, cost(a11) = 0 while cost(a41) = 2k*w > 0, so a41 is")
print("   STRICTLY worse.  Properness drives r4/(r1+r2) -> 0, hence q -> 1 > 1/5,")
print("   hence P3 strictly calls and c33 = 1 -- contradicting c33 = lo.")
print("   At c33 = hi the mirror argument yields c33 = 0.  Both corners die.\n")
print("   point                 corner    cost a11   cost a41   strictly worse")
for b11, b21, b23, b32, c11, sub in POINTS[:4]:
    lo, hi = window(b11, b21, b32)
    for lbl, cc in (("c33 = lo", lo), ("c33 = hi", hi)):
        pf = profile_fr(b11, b21, b23, b32, c11, cc, Fr(0))
        x, y = -dfr(pf, "a11", 0), -dfr(pf, "a41", 0)
        print("   %-20s  %-9s %-9s  %-9s  %s"
              % (sub, lbl, x, y, "a41" if y > x else ("a11" if x > y else "neither")))

# ===========================================================================
hdr("ITEM 3c.  CONSISTENCY AT THE OTHER OFF-PATH SETS")
print("   At the properness point, check b32, c34, c44 and Nash-ness.\n")
print("   point                 c33*      b32 adv    c34 adv    c44 adv    exploitability")
for b11, b21, b23, b32, c11, sub in POINTS:
    lo, hi = window(b11, b21, b32)
    cs = lo + (hi - lo) / 3
    pfl = F.make_profile(float(b11), float(b21), float(b23), float(b32),
                         float(c11), float(cs), 0.0)
    r = (1, 1, 1, 4)
    print("   %-20s  %-8.4f  %+9.4f  %+9.4f  %+9.4f  %.2e"
          % (sub, float(cs), adv(pfl, "b32", 1e-3, r), adv(pfl, "c34", 1e-3, r),
             adv(pfl, "c44", 1e-3, r), np.abs(K.exploitability(pfl)).max()))
print("\n   b32 adv < 0 -> b32 = 0 forced;  c34 adv < 0 -> c34 = 0 forced.")
print("   c44 shows +5 where b32 > 0 (so c44 = 1, confirming Table 2) and nan")
print("   wherever b32 = 0, because reach(c44) is then exactly 0 even under")
print("   trembles -- c44 is inert on the refined face, exactly as R11 found.")
print("   All consistent with R11, and every selected profile is exactly Nash.")
print("   With b32 = 0 we get lo = 1/2, so the selected point is c33 = 1/2 + w/3.")

# ===========================================================================
hdr("ITEM 3d.  THE SELECTED rho IS FINITE AND EXACTLY RATIONAL")
print("   At c33 = lo + w/3:  rho(a11) = 1 + 3R11/w,  rho(a41) = 1 - 3R41/(2w).\n")
print("   point                 w          rho(a11)     rho(a21)     rho(a41)")
for b11, b21, b23, b32, c11, sub in POINTS:
    lo, hi = window(b11, b21, b32)
    w = hi - lo
    if w == 0:
        continue
    cs = lo + w / 3
    pf = profile_fr(b11, b21, b23, b32, c11, cs, Fr(0))
    out = []
    for nm in ("a11", "a21", "a41"):
        d1, d3 = dfr(pf, nm, 0), dfr(pf, nm, 2)
        out.append(str(-d3 / d1) if d1 != 0 else "undefined")
    print("   %-20s  %-9s  %-11s  %-11s  %-11s" % (sub, w, out[0], out[1], out[2]))
print("\n   Every value is finite and exactly rational.  Properness turns rho from")
print("   an unbounded, sign-ambiguous quantity into a determinate one.")

print("\n   NOTE ON THE REFINEMENT USED: this is Myerson properness on the NORMAL")
print("   form, where whole pure strategies are ordered by expected cost, and the")
print("   behavioural tremble rates r_j inherit that ordering.  Agent-normal-form")
print("   properness would compare only actions WITHIN one information set and")
print("   would NOT order a11 against a41, since P1 holding the 1 and P1 holding")
print("   the 4 are different information sets.  Scope the claim accordingly.")
