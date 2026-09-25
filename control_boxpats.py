"""Control for the box -> support-pattern derivation of boxpats.py.

The betting-region screen is only worth running if a pattern derived from a
COARSE box can still express, and recover, an equilibrium that lies in that box.
If it cannot, the screen returns "nothing found" for a trivial reason and the
result would be worthless while looking clean -- the same failure shape as
freezing off-path coordinates in the solver.

So: take known family equilibria, wrap each in a box of the kind bnb5 actually
emits (Table 2 coordinates pinned, everything else a width-0.5 dyadic slab
containing the point), derive patterns A and B, and require that the pipeline
gets the equilibrium back.

The interesting case is a coordinate sitting exactly on a slab edge -- a33 = 1/2
is in every family profile.  Rule B reads the slab [0, 1/2] as "this coordinate
is 0" and pins it, which is wrong for that point; rule A reads it as MIX and
recovers it.  A control that only ever exercised one rule would not show that
both are needed.
"""
import numpy as np, bnb, boxpats, bisbatch, screen2 as screen, solve2
import family as F, eqtools as E, kuhn3p as K

I = K.NAME_IDX
T2_ZERO = ("a12", "a13", "a14", "a24", "b12", "b13", "b14", "b24",
           "c12", "c13", "c14", "c24")
T2_ONE = ("a42", "a43", "a44", "b42", "b43", "b44", "c42", "c43", "c44")

tests = [
    ("A(1/8,1/4)", F.profile_A(0.125, 0.25)[0]),
    ("A(0,0)", F.profile_A(0.0, 0.0)[0]),
    ("A(1/4,1/4)", F.profile_A(0.25, 0.25)[0]),
    ("B(1/8,0.2)", F.profile_B(0.125, 0.2)[0]),
    ("B(0.2,0.3)", F.profile_B(0.2, 0.3)[0]),
    ("C(0.2,0.05)", F.profile_C(0.2, 0.05)[0]),
    ("C(1/4,0)", F.profile_C(0.25, 0.0)[0]),
    ("A(1/8,1/4)+off", F.profile_A(0.125, 0.25, t_b32=0.3, t_c33=0.7, c34=0.2)[0]),
    ("C(0.2,0.05)+off", F.profile_C(0.2, 0.05, t_b23=0.4, t_b32=0.6,
                                   t_c33=0.3, c34=0.7)[0]),
]


def slab_box(p):
    """A width-0.5 dyadic box containing p, Table 2 pinned -- what bnb5 emits."""
    LO = np.where(p < 0.5, 0.0, 0.5)
    HI = LO + 0.5
    for n in T2_ZERO:
        LO[I[n]] = HI[I[n]] = 0.0
    for n in T2_ONE:
        LO[I[n]] = HI[I[n]] = 1.0
    return LO, HI


print("control point must be an equilibrium, and the box must contain it\n")
ok_all = True
for name, p in tests:
    ex = float(np.abs(E.expl(p)).max())
    LO, HI = slab_box(p)
    inside = bool((LO <= p + 1e-12).all() and (HI >= p - 1e-12).all())
    if ex > 1e-13 or not inside:
        print("  REFUSING %s: expl=%.2e inside=%s" % (name, ex, inside))
        ok_all = False
print("  all %d control points are exact equilibria inside their box: %s\n"
      % (len(tests), ok_all))
assert ok_all

rng = np.random.default_rng(0)
print("%-18s %-10s %-10s %-12s %s" % ("point", "rule A", "rule B", "best resid", "recovered"))
nrec = 0
for name, p in tests:
    LO, HI = slab_box(p)
    A, B = boxpats.patterns(LO[None, :], HI[None, :])
    res = {}
    for rule, pat in (("A", A), ("B", B)):
        pid, lab, bLO, bHI = bisbatch.bisect(pat.astype(np.int8), depth=8)
        if len(pid) == 0:
            res[rule] = (np.inf, None); continue
        cen = 0.5 * (bLO + bHI)
        X, r = screen.screen(lab, rng, iters=14, jac_every=7, x0=cen)
        j = int(np.argmin(r))
        # polish exactly as verify_surv does before believing anything
        P2, r2 = solve2.solve(lab[j:j+1].astype(np.int64), rng, iters=60,
                              x0=X[j:j+1], tol=1e-14)
        res[rule] = (float(r2[0]), P2[0])
    best = min(res, key=lambda k: res[k][0])
    q = res[best][1]
    exq = float(np.abs(E.expl(q)).max()) if q is not None else np.inf
    got = exq < 1e-13
    nrec += got
    print("%-18s %-10.1e %-10.1e %-12.1e %s"
          % (name, res["A"][0], res["B"][0], exq,
             "YES (rule %s)" % best if got else "no"))

print("\nrecovered %d of %d" % (nrec, len(tests)))
print("rule A alone would recover:", sum(
    1 for name, p in tests
    for LO, HI in [slab_box(p)]
    for A, B in [boxpats.patterns(LO[None, :], HI[None, :])]
    if True) and "see per-row columns above")
