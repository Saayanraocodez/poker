"""Control for pgsolve: can it recover a known equilibrium from a COARSE box?

This is the control that control_boxpats.py failed.  Same nine family points,
same width-0.5 dyadic boxes that bnb5 actually emits, but the solver is given
the box centre and no support hypothesis at all.

Three things are checked, because passing the first two alone would not be
enough:

  1. RECOVERY   from each box centre, does LM reach an exact equilibrium
                (eqtools.expl < 1e-13)?  The residual's own value is not
                evidence -- expl is.
  2. NO FALSE POSITIVES  a converged residual must never be reported as an
                equilibrium when expl says otherwise.  Checked by counting
                disagreements between |F| < 1e-12 and expl < 1e-13.
  3. SANITY AT A NON-EQUILIBRIUM  profile_B(b11, 1/2) is NOT an equilibrium
                (expl 4.2e-03; it is sub-family C's boundary, and using it as a
                control is what made a correct prune look unsound in an earlier
                session).  Started there, the solver must either move away to a
                real equilibrium or fail -- it must not certify the start.
"""
import numpy as np, pgsolve, family as F, eqtools as E, kuhn3p as K

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
    LO = np.where(p < 0.5, 0.0, 0.5)
    HI = LO + 0.5
    for n in T2_ZERO:
        LO[I[n]] = HI[I[n]] = 0.0
    for n in T2_ONE:
        LO[I[n]] = HI[I[n]] = 1.0
    return LO, HI


rng = np.random.default_rng(0)
LO = np.array([slab_box(p)[0] for _, p in tests])
HI = np.array([slab_box(p)[1] for _, p in tests])
cen = 0.5 * (LO + HI)

P, r = pgsolve.solve(cen, rng, iters=80, jac_every=3, tol=1e-13)
ex = np.array([float(np.abs(E.expl(q)).max()) for q in P])

print("1. RECOVERY from the box centre\n")
print("%-18s %-12s %-12s %s" % ("control point", "|F|", "expl", "verdict"))
for (name, p), rr, ee in zip(tests, r, ex):
    print("%-18s %-12.2e %-12.2e %s" % (name, rr, ee, "EQUILIBRIUM" if ee < 1e-13 else "no"))
nrec = int((ex < 1e-13).sum())
print("\n   recovered %d of %d from coarse box centres" % (nrec, len(tests)))

print("\n2. NO FALSE POSITIVES")
claim = r < 1e-12
truth = ex < 1e-13
bad = int((claim & ~truth).sum())
print("   residual says solved but expl disagrees: %d  (must be 0)" % bad)

print("\n3. SANITY AT A NON-EQUILIBRIUM START")
bad2 = F.profile_B(0.125, 0.5)[0]
e0 = float(np.abs(E.expl(bad2)).max())
P2, r2 = pgsolve.solve(bad2[None, :], rng, iters=80, jac_every=3, tol=1e-13)
e1 = float(np.abs(E.expl(P2[0])).max())
moved = float(np.abs(P2[0] - bad2).max())
print("   start expl %.2e (not an equilibrium); after LM expl %.2e, moved %.3f"
      % (e0, e1, moved))
print("   did NOT certify the bad start: %s" % (not (r2[0] < 1e-12 and e1 > 1e-13)))

print("\nCONTROL %s" % ("PASSED" if (nrec == len(tests) and bad == 0) else "FAILED"))
