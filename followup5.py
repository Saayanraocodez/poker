"""
(1) Does the "attainable deterrence boundary => pole of rho" mechanism appear at ROUND-2
    decisions, or is it specific to opening bets?
(2) Exact residue of each pole, not just its existence.
"""
from fractions import Fraction as Fr

import numpy as np

import kuhn3p as K
import family as F
import grids as G

I = K.NAME_IDX
KAP = K.KAPPA
CYC = {0: (1, 2), 1: (2, 0), 2: (0, 1)}
PN = ("P1", "P2", "P3")


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


def dv(p, name):
    return K.exact_coord_derivative(p, I[name])


def root_in(name, var, **kw):
    """du_owner/d(name) is affine in the free parameter `var` -> solve exactly."""
    owner = "abc".index(name[0])

    def g(v):
        kw2 = dict(kw)
        kw2[var] = v
        return dv(F.make_profile(**kw2), name)[owner]
    g0, g1 = g(0.0), g(1.0)
    if abs(g1 - g0) < 1e-15:
        return None
    return -g0 / (g1 - g0)


# ===========================================================================
hdr("1.  ROUND-2 GENERALIZATION: the same closed-form solve, at call decisions")
print("   Situation k=1 is an opening bet (round 1); k=2,3,4 are call/fold")
print("   decisions facing a bet (round 2).\n")

print("   -- POSITIVE CASE 1: a22 (P1 calls P3's bet at KKB holding the 2) --")
print("   Paper Lemma 5: du1/da22 = k(1-a21)(b11 + 2(b11+b21)c11 + 3c11 - 2), affine in c11.")
print("   Predicted root: c11 = (2-b11)/(3+2b11+2b21) = Table 3's UPPER BOUND on c11.\n")
print("      b11    b21    b23   | root(c11)   c11_max     |diff|")
e = 0.0
for b11, b21, b23 in ((.00, .00, 0.), (.10, .20, 0.), (.25, .25, 0.),
                      (.15, .15, 0.), (.20, .05, .09), (.25, .00, .125)):
    r = root_in("a22", "c11", b11=b11, b21=b21, b23=b23, b32=.3, c33=.3, c34=.5)
    cm = (2 - b11) / (3 + 2 * b11 + 2 * b21)
    e = max(e, abs(r - cm))
    print("      %.2f   %.2f   %.3f | %.8f  %.8f  %.1e" % (b11, b21, b23, r, cm, abs(r - cm)))
print("   max |root - c11_max| = %.3e" % e)
print("   ATTAINABLE?  c11 <= min{1/2, c11_max}.  The bound binds exactly when")
print("   c11_max <= 1/2, i.e. b21 <= 1/2 - 2*b11 -- which is precisely Table 3's")
print("   b21 constraint in the c11=1/2 sub-family.  So it is attained there.")
for b11 in (0.20, 0.25):
    b21 = 0.5 - 2 * b11
    p = F.make_profile(b11, b21, 0., .3, .5, .3, .5)
    g = dv(p, "a22")
    print("      b11=%.2f b21=%.2f (sub-family C corner): du1/da22 = %+.3e,"
          " du3/da22 = %+.6f  -> %s"
          % (b11, b21, g[0], g[2], "POLE" if abs(g[2]) > 1e-12 else "0/0"))

print("\n   -- POSITIVE CASE 2: a32 (P1 calls P3's bet at KKB holding the 3) --")
print("   Lemma 5: du1/da32 = k(1-a31)(-1 + 4b21 + 8c11(b11-b21))/2.")
print("   In sub-family A (c11=0) the root is b21 = 1/4, exactly Table 3's cap.\n")
print("      c11    b11   | root(b21)   predicted   |diff|")
e2 = 0.0
for c11, b11 in ((0.0, .10), (0.0, .00), (0.5, .10), (0.5, .20), (0.3, .15)):
    r = root_in("a32", "b21", b11=b11, b23=0., b32=.3, c11=c11, c33=.3, c34=.5)
    pred = (1 - 8 * c11 * b11) / (4 - 8 * c11) if abs(4 - 8 * c11) > 1e-12 else None
    if pred is None:
        print("      %.2f   %.2f  | %s   (c11=1/2: root independent of b21)"
              % (c11, b11, "%.8f" % r if r else "none"))
        continue
    e2 = max(e2, abs(r - pred))
    print("      %.2f   %.2f  | %.8f  %.8f  %.1e" % (c11, b11, r, pred, abs(r - pred)))
print("   max |root - (1-8 c11 b11)/(4-8 c11)| = %.3e" % e2)
p = F.make_profile(.25, .25, 0., .3, 0., .3, .5)
g = dv(p, "a32")
print("      at b21 = 1/4 (Table 3 cap, sub-family A): du1/da32 = %+.3e,"
      " du3/da32 = %+.6f -> %s" % (g[0], g[2], "POLE" if abs(g[2]) > 1e-12 else "0/0"))

print("\n   -- NEGATIVE CONTROL 1: b34 (P2 calls at KKBC holding the 3) --")
print("   Lemma 4: du2/db34 = k(-1 + b31)/2.  Root at b31 = 1, but Table 3 pins")
print("   b31 = 0, so the boundary is NOT ATTAINABLE.  Round-2, no pole:")
r = root_in("b34", "b31", b11=.15, b21=.15, b23=0., b32=.3, c11=.25, c33=.3, c34=.5) \
    if False else None
for b11, b21 in ((.00, .00), (.15, .15), (.25, .25)):
    p = F.make_profile(b11, b21, 0., .3, .25, .3, .5)
    g = dv(p, "b34")
    print("      b11=%.2f b21=%.2f: du2/db34 = %+.8f (never 0), rho = %+.4f"
          % (b11, b21, g[1], -g[0] / g[1]))

print("\n   -- NEGATIVE CONTROL 2: c22 (P3 calls P2's bet at KB holding the 2) --")
print("   Lemma 3: du3/dc22 = k(-b11 - 4 b21).  Root at b11 = b21 = 0, which IS")
print("   attainable (the beta=0 corner).  But the NUMERATOR vanishes there too:")
for b11, b21 in ((.10, .10), (.02, .02), (.002, .002), (.0, .0)):
    p = F.make_profile(b11, b21, 0., .3, .25, .3, .5)
    g = dv(p, "c22")
    rho = "undef (0/0)" if abs(g[2]) < 1e-13 else "%+.6f" % (-g[1] / g[2])
    print("      b11=b21=%.4f: du3/dc22 = %+.3e, du2/dc22 = %+.3e, rho = %s"
          % (b11, g[2], g[1], rho))
print("   -> denominator -> 0 but rho stays bounded.  An attainable boundary is")
print("      NECESSARY but NOT SUFFICIENT; the numerator must survive it.")

print("\n   -- FULL CENSUS over grids.full_grid() --")
P, M = G.full_grid()
GE = K.gradients_batch(P, h=None)
print("   param  owner rnd  du_A=0 at   min|du_A|>0   |num| at those pts   pole?")
rows = []
for i in range(48):
    A = i // 16
    B, C = CYC[A]
    nm = K.PARAM_NAME[i]
    rnd = 1 if nm[2] == "1" else 2
    dA, dC = GE[:, i, A], GE[:, i, C]
    zero = np.abs(dA) <= 1e-12
    nz = ~zero
    if zero.sum() and nz.sum():
        numer = np.abs(dC[zero]).max()
        pole = numer > 1e-12
        rows.append((nm, A, rnd, int(zero.sum()), np.abs(dA[nz]).min(), numer, pole))
for nm, A, rnd, nz0, mn, numer, pole in rows:
    print("   %-6s %s    %d   %5d/9072  %.3e     %.6f          %s"
          % (nm, PN[A], rnd, nz0, mn, numer, "YES" if pole else "no (0/0)"))
poles = [r for r in rows if r[6]]
print("\n   POLES FOUND: %s" % ", ".join(
    "%s(%s,round%d)" % (r[0], PN[r[1]], r[2]) for r in poles))
print("   round-1 poles: %s" % ", ".join(r[0] for r in poles if r[2] == 1))
print("   round-2 poles: %s" % ", ".join(r[0] for r in poles if r[2] == 2))
print("   players with poles: %s" % ", ".join(
    sorted({PN[r[1]] for r in poles})))

# ===========================================================================
hdr("2.  EXACT RESIDUES: rho has a pole of order exactly 1")
print("   u_i is multilinear, so along c33 alone BOTH")
print("      D(c33) = du1/da_j1   and   N(c33) = -du3/da_j1")
print("   are AFFINE.  Hence rho = N/D is a Mobius function of c33: a pole of order")
print("   exactly 1 wherever D vanishes and N does not.\n")

base = dict(b11=.15, b21=.15, b23=0., b32=.40, c11=.25, c34=.5)
lo, hi = F.c33_range(base["b11"], base["b21"], base["b32"])


def gN_D(c33, name):
    g = dv(F.make_profile(c33=c33, **base), name)
    return -g[2], g[0]                       # N, D


print("   affineness check (2nd differences over c33, should be 0):")
for nm in ("a11", "a21", "a41"):
    v = [gN_D(c, nm) for c in (0.1, 0.2, 0.3, 0.4)]
    sN = max(abs(v[k + 2][0] - 2 * v[k + 1][0] + v[k][0]) for k in range(2))
    sD = max(abs(v[k + 2][1] - 2 * v[k + 1][1] + v[k][1]) for k in range(2))
    print("      %s : max |2nd diff N| = %.2e   max |2nd diff D| = %.2e" % (nm, sN, sD))

print("\n   denominator slope D' = dD/dc33, as a multiple of kappa = 1/24:")
slopes = {}
for nm in ("a11", "a21", "a41", "a31"):
    D0, D1 = gN_D(0.0, nm)[1], gN_D(1.0, nm)[1]
    slopes[nm] = D1 - D0
    print("      %s : D' = %+.8f = %+.4f * kappa" % (nm, D1 - D0, (D1 - D0) / KAP))

print("\n   residue R = N(c33*) / D'   at   b11=b21=0.15, b32=0.40, c11=0.25, c34=0.5")
print("   (c33 interval [%.4f, %.4f])" % (lo, hi))
for nm, star in (("a11", lo), ("a21", lo), ("a41", hi)):
    N, D = gN_D(star, nm)
    R = N / slopes[nm]
    print("      %s : pole at c33* = %.4f, N(c33*) = %+.8f, R = %+.8f = %s"
          % (nm, star, N, R, Fr(R).limit_denominator(10000)))

print("\n   rate check:  rho(c33) * (c33 - c33*)  ->  R")
print("   offset      a11: rho*(dc)      rel.err      a41: rho*(dc)      rel.err")
for nm, star, sgn in (("a11", lo, +1), ("a41", hi, -1)):
    pass
for k in range(2, 10):
    off = 10.0 ** (-k)
    line = "   1e-%d " % k
    for nm, star, sgn in (("a11", lo, +1), ("a41", hi, -1)):
        c = star + sgn * off
        N, D = gN_D(c, nm)
        rho = N / D
        R = gN_D(star, nm)[0] / slopes[nm]
        prod = rho * (c - star)
        line += "  %+.10f  %.2e " % (prod, abs(prod - R) / abs(R))
    print(line)

# --- closed form of the residue -------------------------------------------
print("\n   which free parameters does R depend on?  (vary one at a time)")
FREE = ("b11", "b21", "b23", "b32", "c11", "c34")


def resid(name, which, **kw):
    b32 = kw["b32"]
    star = (0.5 - b32) if which == "lo" else (F.b32_max(kw["b11"], kw["b21"]) - b32)
    g = dv(F.make_profile(c33=star, **kw), name)
    D0 = dv(F.make_profile(c33=0.0, **kw), name)[0]
    D1 = dv(F.make_profile(c33=1.0, **kw), name)[0]
    return -g[2] / (D1 - D0)


ref = dict(b11=.15, b21=.15, b23=0., b32=.40, c11=.25, c34=.5)
for v in FREE:
    lohi = []
    for val in (0.05, 0.20):
        kw = dict(ref)
        kw[v] = val
        lohi.append(resid("a11", "lo", **kw))
    print("      d R(a11) / d %-4s : %s" % (
        v, "0 (independent)" if abs(lohi[1] - lohi[0]) < 1e-13
        else "%+.6f over [0.05,0.20]" % (lohi[1] - lohi[0])))

print("\n   fitting R(a11) exactly (multilinear in the variables it uses):")
DEP = [v for v in FREE
       if abs(resid("a11", "lo", **{**ref, v: 0.05})
              - resid("a11", "lo", **{**ref, v: 0.20})) > 1e-13]
print("      depends on: %s" % ", ".join(DEP))


def fit_multilinear(fn, vars_, lo_=0.0, hi_=0.5):
    """Exact multilinear interpolation on the corners of a box."""
    import itertools
    coef = {}
    for mask in itertools.product((0, 1), repeat=len(vars_)):
        pt = {v: (hi_ if m else lo_) for v, m in zip(vars_, mask)}
        coef[mask] = fn(pt)
    return coef


def R_of(pt, name="a11"):
    kw = dict(ref)
    kw.update(pt)
    if kw["b21"] < kw["b11"]:
        pass
    return resid(name, "lo", **kw)


import itertools
corners = {}
for mask in itertools.product((0, 1), repeat=len(DEP)):
    pt = {v: (0.4 if m else 0.0) for v, m in zip(DEP, mask)}
    corners[mask] = R_of(pt)
# multilinear coefficients via inclusion-exclusion on the unit box scaled by 0.4
print("      corner values (each var in {0, 0.4}):")
for mask, val in corners.items():
    print("        %s -> R = %+.10f = %s"
          % ("".join(str(m) for m in mask), val, Fr(val).limit_denominator(100000)))
