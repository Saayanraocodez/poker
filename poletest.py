"""
The LOCAL pole test -- everything the criterion needs, around a SINGLE profile.

  (i)   x is off-path                  reach(x) == 0
  (ii)  du_A/dy = 0 has a root in x    (affine in x, so solve exactly)
  (iii) the root is attainable         root in [0, 1]
  (iv)  the numerator survives         du_C/dy != 0 at the root

Because every derivative is affine in x, two vectorised gradient evaluations
(at x=0 and x=1) give the whole picture: the value at the root is just the
linear interpolation, so no further game evaluations are needed.  That makes
the test O(off-path count) rather than O(off-path count x parameters).

Engine-agnostic: works on kuhnNp.KuhnN and kuhnGen.Kuhn alike.
"""
import numpy as np


def nplayers(g):
    return getattr(g, "nplayer", 3)


def owners(g):
    """Player index owning each parameter."""
    n = nplayers(g)
    if hasattr(g, "offset") and hasattr(g, "nsit"):
        o = np.empty(g.nparam, int)
        for pl in range(n):
            lo = g.offset[pl]
            o[lo:lo + g.ncard * g.nsit[pl]] = pl
        return o
    per = g.nparam // n
    return np.arange(g.nparam) // per


def grad(g, p):
    if hasattr(g, "gradient"):
        return g.gradient(p)
    return np.array([g.dcoord(p, i) for i in range(g.nparam)])


def snap(g, p, tol=5e-3):
    """Round near-pure probabilities to exactly 0/1 so off-path sets are exact."""
    q = np.array(p, float)
    q[q < tol] = 0.0
    q[q > 1 - tol] = 1.0
    return q


def offpath(g, p, tol=1e-12):
    r = g.reach(p)
    return [i for i in range(g.nparam) if r[i] < tol]


def pole_test(g, p, dtol=1e-12, ntol=1e-9, max_off=None, sub_seed=0):
    n = nplayers(g)
    own = owners(g)
    r = g.reach(p)
    off = [i for i in range(g.nparam) if r[i] < dtol]
    if max_off is not None and len(off) > max_off:
        # random subsample, NOT the first k -- parameter index is ordered by
        # player, so a prefix would over-sample P1 and bias the pole count
        off = list(np.random.default_rng(sub_seed).choice(off, max_off, replace=False))
    live = r > dtol
    ar = np.arange(g.nparam)
    out = []
    for x in off:
        a, b = p.copy(), p.copy()
        a[x], b[x] = 1.0, 0.0
        Ga, Gb = grad(g, a), grad(g, b)
        D0, D1 = Gb[ar, own], Ga[ar, own]          # du_A/dy at x = 0 and 1
        slope = D1 - D0
        cand = np.where(live & (np.abs(slope) > ntol))[0]
        if cand.size == 0:
            continue
        root = -D0[cand] / slope[cand]
        rc = np.clip(root, 0.0, 1.0)[:, None]
        du = Gb[cand] + rc * (Ga[cand] - Gb[cand])  # affine interpolation
        for t, y in enumerate(cand):
            A = own[y]
            others = [du[t, k] for k in range(n) if k != A]
            numer = max(abs(v) for v in others) if others else 0.0
            attain = -1e-9 <= root[t] <= 1 + 1e-9
            out.append(dict(x=g.name(int(x)), y=g.name(int(y)), A=int(A),
                            root=float(root[t]), slope=float(slope[y]),
                            attainable=bool(attain),
                            du_A_at_root=float(du[t, A]),
                            numerator=float(numer),
                            pole=bool(attain and numer > ntol
                                      and abs(du[t, A]) < 1e-7)))
    return out
