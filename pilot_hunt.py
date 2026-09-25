"""Pilot: does PG-LM converge to a certified equilibrium from random starts?

Every exhaustive route to the betting question is now closed -- the support
enumeration is 10^9-10^10 patterns per branch, the box partition grows ~1.5x per
level and needs ~104 more of them, and the depth-26 boxes are too coarse to seed
anything (control_pg: 0 of 9 recovered from a box centre, because a width-0.5
slab centre is ~0.25 away and the basin is ~0.1).

That leaves multistart search, which is only worth building if it converges at
all.  s10.5's Attempt 1 was "broad random-restart Newton, FAILED, uninformative";
two things are different now -- Table 2's 21 coordinates are rigorously forced
everywhere (including, as this session showed, on the betting region), so they
can be fixed and the search runs in 27 dimensions not 48; and the residual is
the projected gradient, which needs no support hypothesis.

Reports the yield: certified equilibria per 1000 starts, and how many of them
have P1 betting.  A yield near zero means the hunt is not worth days.
"""
import numpy as np, sys, time, pgsolve, eqtools as E, classify, kuhn3p as K

I = K.NAME_IDX
T2_ZERO = ("a12", "a13", "a14", "a24", "b12", "b13", "b14", "b24",
           "c12", "c13", "c14", "c24")
T2_ONE = ("a42", "a43", "a44", "b42", "b43", "b44", "c42", "c43", "c44")
OPEN = [I[n] for n in ("a11", "a21", "a31", "a41")]
Z = [I[n] for n in T2_ZERO]
O = [I[n] for n in T2_ONE]


def starts(n, rng, force_bet=True, lo=0.02):
    X = rng.random((n, 48))
    X[:, Z] = 0.0
    X[:, O] = 1.0
    if force_bet:
        # at least one opening coordinate in [lo, 1]; the others left random
        j = rng.integers(0, 4, n)
        X[np.arange(n), np.array(OPEN)[j]] = lo + (1 - lo) * rng.random(n)
    return X


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2048
    rng = np.random.default_rng(1)
    for label, fb in (("free", False), ("forced to bet", True)):
        X = starts(n, rng, force_bet=fb)
        t0 = time.time()
        P, r = pgsolve.solve(X, rng, iters=60, jac_every=3, tol=1e-13)
        ex = np.array([float(np.abs(E.expl(q)).max()) for q in P])
        eq = ex < 1e-13
        bet = P[:, OPEN].max(axis=1) > 1e-9
        dt = time.time() - t0
        print("%-14s starts %5d   residual<1e-12 %5d   CERTIFIED %5d (%.2f%%)   "
              "certified with P1 betting %d   %.0fs (%.1f ms/start)"
              % (label, n, int((r < 1e-12).sum()), int(eq.sum()),
                 100 * eq.mean(), int((eq & bet).sum()), dt, 1000 * dt / n),
              flush=True)
        if eq.any():
            Q = P[eq]
            fg = np.array([classify.family_gap(q) for q in Q])
            sig = len({classify.signature(q) for q in Q})
            print("     distinct leaf-distributions %d   family gap max %.2e   "
                  "OUTSIDE family (>1e-9): %d" % (sig, fg.max(), int((fg > 1e-9).sum())),
                  flush=True)
