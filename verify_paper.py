"""
Validate the engine + family transcription against everything the paper states
independently:  the closed-form utilities u1/u2/u3 of Table 3, the Appendix
equations (3), (4), (5), the Table 4 non-equilibrium example, and the
equilibrium property itself (exact best-response gap = 0).
"""
from fractions import Fraction

import numpy as np

import kuhn3p as K
import family as F

I = K.NAME_IDX
k = K.KAPPA
rng = np.random.default_rng(20130506)


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


# ===========================================================================
hdr("1. Table 3 utilities:  u1 = -k(1/2+beta),  u2 = -k/2,  u3 = k(1+beta)")
worst = 0.0
rows = []
for name, gen in (
    ("A  c11=0      ", lambda: F.profile_A(*sorted(rng.uniform(0, .25, 2)),
                                           t_b32=rng.random(),
                                           t_c33=rng.random(),
                                           c34=rng.random())),
    ("B  0<c11<1/2  ", lambda: (lambda b11: F.profile_B(
        b11, rng.uniform(1e-6, F.c11_max(b11, b11) - 1e-6),
        t_b32=rng.random(), t_c33=rng.random(), c34=rng.random()))(
            rng.uniform(0, .25))),
    ("C  c11=1/2    ", lambda: (lambda b11: F.profile_C(
        b11, rng.uniform(0, min(b11, .5 - 2 * b11)),
        t_b23=rng.random(), t_b32=rng.random(),
        t_c33=rng.random(), c34=rng.random()))(rng.uniform(0, .25))),
):
    for _ in range(200):
        p, meta = gen()
        v = F.violations(subfamily=meta["subfamily"],
                         **{q: meta[q] for q in
                            ("b11", "b21", "b23", "b32", "c11", "c33", "c34")})
        assert not v, (meta, v)
        u = K.utilities(p)
        pred = F.predicted_utilities(meta["b11"], meta["b21"])
        worst = max(worst, float(np.abs(u - pred).max()))
    rows.append(name)
print("   sub-families tested:", ", ".join(r.strip() for r in rows),
      "(200 random points each)")
print("   max |u_enumerated - u_paper| = %.3e" % worst)
print("   -> engine agrees with the paper's closed-form utilities" if worst < 1e-14
      else "   -> MISMATCH")

# exact rational check at one point
p, meta = F.profile_A(Fraction(1, 8), Fraction(1, 4))
pf = [Fraction(x).limit_denominator(10**6) for x in p]
ue = K.utilities_exact(pf)
beta = Fraction(1, 4)
print("   exact rational check at b11=1/8, b21=1/4 (beta=1/4):")
print("      u =", tuple(str(x) for x in ue))
print("      expected", (str(-K.KAPPA_F * (Fraction(1, 2) + beta)),
                         str(-K.KAPPA_F * Fraction(1, 2)),
                         str(K.KAPPA_F * (1 + beta))))

# ===========================================================================
hdr("2. Appendix eq. (3): u3 with P1,P2 from Table 3 and P3's parameters free")
# u3 = k[4 c11 b21 b23 - c31 b21 b23 - b11 - b21 - 4 c31 + 2 c21 + 2 c11
#        + 2 b23 c41 + 2 b33 c41 - b21 c32 - b11 c32 - b11 c22 - 4 c21 b33
#        - 4 c11 b33 + c31 b23 - 4 c11 b23 + 5 b21 c31 + 2 b11 c21 + 4 b21 c21
#        + 5 b11 c31 + 4 b11 c11 + 2 b21 c11 - 4 b21 c22 - 2 b21 b23 c41]
def eq3(b11, b21, b23, b33, c11, c21, c22, c31, c32, c41):
    return k * (4 * c11 * b21 * b23 - c31 * b21 * b23 - b11 - b21 - 4 * c31
                + 2 * c21 + 2 * c11 + 2 * b23 * c41 + 2 * b33 * c41
                - b21 * c32 - b11 * c32 - b11 * c22 - 4 * c21 * b33
                - 4 * c11 * b33 + c31 * b23 - 4 * c11 * b23 + 5 * b21 * c31
                + 2 * b11 * c21 + 4 * b21 * c21 + 5 * b11 * c31
                + 4 * b11 * c11 + 2 * b21 * c11 - 4 * b21 * c22
                - 2 * b21 * b23 * c41)


err = 0.0
for _ in range(400):
    b11, b21, b23, b33 = rng.random(4)
    p = F.table2(np.full(48, np.nan))
    for n in ("a11", "a21", "a22", "a23", "a31", "a32", "a34", "a41"):
        p[I[n]] = 0.0
    p[I["a33"]] = 0.5
    p[I["b11"]], p[I["b21"]], p[I["b23"]], p[I["b33"]] = b11, b21, b23, b33
    p[I["b22"]] = p[I["b31"]] = p[I["b34"]] = 0.0
    p[I["b32"]] = rng.random()                    # non-reached, must not matter
    p[I["b41"]] = 2 * b11 + 2 * b21               # Table 3 value, substituted
    free3 = dict(c11=rng.random(), c21=rng.random(), c22=rng.random(),
                 c23=rng.random(), c31=rng.random(), c32=rng.random(),
                 c33=rng.random(), c34=rng.random(), c41=rng.random())
    for n, v in free3.items():
        p[I[n]] = v
    got = K.utilities(p)[2]
    want = eq3(b11, b21, b23, b33, free3["c11"], free3["c21"], free3["c22"],
               free3["c31"], free3["c32"], free3["c41"])
    err = max(err, abs(got - want))
print("   max |u3_engine - eq(3)| over 400 random points = %.3e" % err)

# ===========================================================================
hdr("3. Appendix eq. (4): u2 with P1,P3 from Table 3 and P2's parameters free")
# u2 = (k/2)[4 b21 b23 + b31 b34 - 1 - 5 b31 - 4 b23 - b34
#            - 8 c11 b21 b23 + 8 c11 b23]
def eq4(b21, b23, b31, b34, c11):
    return (k / 2.0) * (4 * b21 * b23 + b31 * b34 - 1 - 5 * b31 - 4 * b23
                        - b34 - 8 * c11 * b21 * b23 + 8 * c11 * b23)


err = 0.0
for _ in range(400):
    p = F.table2(np.full(48, np.nan))
    for n in ("a11", "a21", "a22", "a23", "a31", "a32", "a34", "a41"):
        p[I[n]] = 0.0
    p[I["a33"]] = 0.5
    free2 = {n: rng.random() for n in ("b11", "b21", "b22", "b23", "b31",
                                       "b32", "b33", "b34", "b41")}
    for n, v in free2.items():
        p[I[n]] = v
    c11 = rng.random() * 0.5
    p[I["c11"]], p[I["c21"]] = c11, 0.5 - c11
    p[I["c22"]] = p[I["c23"]] = p[I["c31"]] = p[I["c32"]] = 0.0
    p[I["c33"]], p[I["c34"]] = rng.random(), rng.random()
    p[I["c41"]] = 1.0
    got = K.utilities(p)[1]
    want = eq4(free2["b21"], free2["b23"], free2["b31"], free2["b34"], c11)
    err = max(err, abs(got - want))
print("   max |u2_engine - eq(4)| over 400 random points = %.3e" % err)

# ===========================================================================
hdr("4. Appendix eq. (5): u1 with P2,P3 from Table 3 and P1's parameters free")
def eq5(a11, a21, a22, a23, a31, a32, a34, a41, b11, b21, b32, c11, c33):
    return (k / 2.0) * (
        -1 - 4 * a31 * b21 * a32 + 8 * b11 * c11 * a32 + 6 * a31 * b11 * c11
        - 2 * a41 + 4 * a11 - 4 * a22 + 4 * a21 + 4 * a41 * b32 - 8 * a11 * b32
        - 8 * a21 * b32 - 6 * a31 * b21 * c11 - 8 * a11 * c33 - 8 * a21 * c33
        + 4 * c11 * b11 * a22 - 2 * b21 * a34 - 2 * b11 * a21 * a22
        + 8 * a21 * b21 * a23 + 4 * a41 * c33 - 2 * b21 - 5 * a31 - a32
        + 2 * b11 * a31 * a34 + 2 * b21 * a31 * a34 - 8 * b21 * a23
        - 3 * b11 * a41 + a31 * a32 + 2 * b11 * a22 + 4 * b21 * a32
        - 4 * b21 * a41 + 6 * c11 * a22 - 6 * c11 * a22 * a21
        + 2 * c11 * b21 * a41 - 2 * b11 * a41 * c11
        - 4 * c11 * b11 * a21 * a22 - 4 * c11 * a21 * b21 * a22
        - 2 * b11 * a34 - 4 * b11 * c11 + 4 * b21 * c11 + 4 * a21 * a22
        - 8 * a31 * b11 * c11 * a32 + 8 * a31 * b21 * c11 * a32
        - 8 * b21 * c11 * a32 + 4 * c11 * b21 * a22 + 3 * a31 * b11
        + 6 * a31 * b21)


err = 0.0
for _ in range(400):
    p = F.table2(np.full(48, np.nan))
    free1 = {n: rng.random() for n in ("a11", "a21", "a22", "a23", "a31",
                                       "a32", "a33", "a34", "a41")}
    for n, v in free1.items():
        p[I[n]] = v
    b11, b21, b23 = rng.random(3)
    b32, c33, c34 = rng.random(3)
    c11 = rng.random() * 0.5
    p[I["b11"]], p[I["b21"]], p[I["b23"]] = b11, b21, b23
    p[I["b22"]] = p[I["b31"]] = p[I["b34"]] = 0.0
    p[I["b32"]] = b32
    p[I["b33"]] = F.b33_of(b11, b21, b23)
    p[I["b41"]] = 2 * b11 + 2 * b21
    p[I["c11"]], p[I["c21"]] = c11, 0.5 - c11
    p[I["c22"]] = p[I["c23"]] = p[I["c31"]] = p[I["c32"]] = 0.0
    p[I["c33"]], p[I["c34"]], p[I["c41"]] = c33, c34, 1.0
    got = K.utilities(p)[0]
    want = eq5(free1["a11"], free1["a21"], free1["a22"], free1["a23"],
               free1["a31"], free1["a32"], free1["a34"], free1["a41"],
               b11, b21, b32, c11, c33)
    err = max(err, abs(got - want))
print("   max |u1_engine - eq(5)| over 400 random points = %.3e" % err)
print("   (note eq(5) contains no a33, b23, b33, c34 -> u1 is independent of")
print("    them; the random draws above confirm that too)")

# ===========================================================================
hdr("5. Table 4: the paper's deliberately MIS-MATCHED (non-equilibrium) profile")
p4 = F.make_profile(b11=0.25, b21=0.0, b23=0.125, b32=0.0,
                    c11=0.0, c33=0.25, c34=0.0)
p4[I["b33"]] = 5.0 / 8.0
p4[I["b41"]] = 0.5
u4 = K.utilities(p4)
beta = 0.25
print("   engine   u = ", np.round(u4, 8))
print("   paper    u = ", np.round(np.array([-k * 0.5, -k * (0.5 + beta),
                                             k * (1 + beta)]), 8))
print("   match:", bool(np.allclose(u4, [-k * .5, -k * (.5 + beta),
                                         k * (1 + beta)], atol=1e-15)))
print("   P2 exploitability here = %.8f  (paper says P2 can gain k*beta = %.8f)"
      % (K.exploitability(p4)[1], k * beta))

# ===========================================================================
hdr("6. Equilibrium property: exact best-response gap over the whole family")
mx = np.zeros(3)
n = 0
for _ in range(150):
    for gen in ("A", "B", "C"):
        if gen == "A":
            b21 = rng.uniform(0, .25)
            p, m = F.profile_A(rng.uniform(0, b21), b21, rng.random(),
                               rng.random(), rng.random())
        elif gen == "B":
            b11 = rng.uniform(0, .25)
            p, m = F.profile_B(b11, rng.uniform(1e-9, F.c11_max(b11, b11)),
                               rng.random(), rng.random(), rng.random())
        else:
            b11 = rng.uniform(0, .25)
            p, m = F.profile_C(b11, rng.uniform(0, min(b11, .5 - 2 * b11)),
                               rng.random(), rng.random(), rng.random(),
                               rng.random())
        mx = np.maximum(mx, K.exploitability(p))
        n += 1
print("   %d random family points; max_i (BR_i - u_i) = %s" % (n, mx))
print("   -> every profile in the family is an exact Nash equilibrium"
      if mx.max() < 1e-12 else "   -> NOT an equilibrium somewhere")
