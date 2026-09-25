"""Verify candidate equilibria and classify them against the SGS family."""
import numpy as np, eqtools as E, family as F, kuhn3p as K, bgrad
I = K.NAME_IDX
OOR_TOL = 1e-9      # see family_gap: guards against a non-profile image, not float noise

def family_image(p):
    """the family member with p's own free-parameter values"""
    g = lambda n: float(p[I[n]])
    return F.make_profile(g('b11'), g('b21'), g('b23'), g('b32'),
                          g('c11'), g('c33'), g('c34'))

def family_gap(p):
    """0 iff p induces exactly the leaf distribution of a Table-3 profile with
    p's own (b11,b21,b23,b32,c11,c33,c34)."""
    try:
        q = family_image(p)
    except Exception:
        return 1.0
    # The guard rejects free parameters whose Table-3 image is not a profile at
    # all.  It must NOT reject float noise: at the family's own corner
    # b11 = b21 = 1/4 the identity b41 = 2(b11+b21) is exactly 1, and in
    # floating point it lands at 1 + 1e-12 -- one order past a 1e-12 guard.  A
    # 20M-start hunt hit that corner twice and both were reported as OUTSIDE the
    # family when their leaf-distribution gap after clipping is 2e-16, i.e. they
    # are family members exactly.  Reporting the family's extreme point as a
    # counterexample is the worst possible false positive for this project.
    # 1e-9 is ~1000x the observed noise and still far below any real violation,
    # and the comparison below clips regardless.
    if np.any(q < -OOR_TOL) or np.any(q > 1 + OOR_TOL):
        return 1.0
    return float(np.abs(E.leafw(p) - E.leafw(np.clip(q, 0, 1))).max())

def family_constraints(p):
    g = lambda n: float(p[I[n]])
    b11, b21, b23, b32 = g('b11'), g('b21'), g('b23'), g('b32')
    c11, c33, c34 = g('c11'), g('c33'), g('c34')
    sub = 'A' if c11 <= 1e-9 else ('C' if abs(c11 - .5) <= 1e-9 else 'B')
    return F.violations(b11, b21, b23, b32, c11, c33, c34, sub), sub

def verify(X, expl_tol=1e-12):
    out = []
    for p in np.atleast_2d(X):
        ex = np.abs(E.expl(p)).max()
        u = E.util(p)
        out.append(dict(expl=ex, nash=ex < expl_tol, u=u,
                        fgap=family_gap(p),
                        beta=max(float(p[I['b11']]), float(p[I['b21']]))))
    return out

def signature(p, nd=9):
    return tuple(np.round(E.leafw(p), nd))
