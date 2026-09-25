"""
B: does the properness selection generalise past n=3, N=4?

At (3,4) properness pinned the surviving free off-path parameter because
exactly TWO of P1's opening deviations competed, and equal-cost gave a unique
point:  d_free = 1, d_cond = 1.

The general question is a dimension count:

  d_free = off-path parameters that still have a non-degenerate DETERRENCE
           WINDOW (an interval of values keeping every incentive <= 0), after
           removing those already pinned by belief-free dominance.
  d_cond = rank of the Jacobian of the cost-DIFFERENCES of the deviating
           player's opening actions with respect to those free parameters --
           i.e. how many independent equal-cost conditions properness supplies.

  d_cond == d_free  -> unique point   (properness pins the split)
  d_cond <  d_free  -> a face survives (properness under-determines it)
  d_cond >  d_free  -> over-determined (no proper equilibrium in the component)

Every derivative is affine in each single coordinate, so the windows and the
Jacobian are computed exactly from two gradient evaluations per parameter.
"""
import numpy as np
import poletest as PT


def windows(g, p, tol=1e-9, wtol=0.02):
    """Deterrence window of every off-path coordinate, computed exactly."""
    own = PT.owners(g)
    r = g.reach(p)
    off = [i for i in range(g.nparam) if r[i] < 1e-12]
    live = r > 1e-12
    ar = np.arange(g.nparam)
    out = {}
    for x in off:
        a, b = p.copy(), p.copy()
        a[x], b[x] = 1.0, 0.0
        Ga, Gb = g.gradient(a), g.gradient(b)
        D0, D1 = Gb[ar, own], Ga[ar, own]
        lo, hi = 0.0, 1.0
        for y in np.where(live)[0]:
            s = D1[y] - D0[y]
            if abs(s) < tol:
                continue                       # x does not move this incentive
            root = -D0[y] / s
            if s > 0:                          # incentive increases in x -> x <= root
                hi = min(hi, root)
            else:                              # decreases -> x >= root
                lo = max(lo, root)
        out[x] = (lo, hi, hi - lo)
    return out, off


def dominance_pinned(g, p, x, eps=1e-3, ratios=((1, 1, 1, 1, 1, 1), (1, 1, 1, 1, 1, 8),
                                                (8, 1, 1, 1, 1, 1), (1, 4, 1, 6, 1, 2))):
    """Owner strictly prefers one action at x under EVERY tremble ratio tested."""
    own = PT.owners(g)
    A = own[x]
    signs = set()
    for rr in ratios:
        q = p.copy()
        for pl in range(g.nplayer):
            for k, j in enumerate(g.cards):
                i = g.pidx(pl, j, g.sit_hist[pl][0])
                if q[i] < 0.5:
                    q[i] = eps * rr[k % len(rr)]
        rch = g.reach(q)[x]
        if rch < 1e-18:
            return None
        v = g.gradient(q)[x][A] / rch
        signs.add(1 if v > 1e-9 else (-1 if v < -1e-9 else 0))
    return len(signs) == 1 and 0 not in signs


def analyse(g, p, wtol=0.02):
    W, off = windows(g, p)
    slack = [x for x, (lo, hi, w) in W.items() if w > wtol]
    status = {x: dominance_pinned(g, p, x) for x in slack}
    inert = [x for x in slack if status[x] is None]     # unreachable even under
    pinned = [x for x in slack if status[x] is True]    # trembles -> cannot matter
    free = [x for x in slack if status[x] is False]
    # costs of the first player's opening actions
    open_idx = [g.pidx(0, j, "") for j in g.cards]
    J = np.zeros((len(open_idx), len(free)))
    for c, x in enumerate(free):
        a, b = p.copy(), p.copy()
        a[x], b[x] = 1.0, 0.0
        Ga, Gb = g.gradient(a), g.gradient(b)
        for rI, y in enumerate(open_idx):
            J[rI, c] = -(Ga[y][0] - Gb[y][0])          # d cost_j / dx
    D = J[1:] - J[0]                                    # cost differences
    d_cond = int(np.linalg.matrix_rank(D, tol=1e-9)) if D.size else 0
    # is the equal-cost system actually SATISFIABLE inside the windows?
    solved = None
    if D.size and d_cond == len(free):
        c0 = np.array([-g.gradient(p)[y][0] for y in open_idx])
        rhs = -(c0[1:] - c0[0])
        sol, *_ = np.linalg.lstsq(D, rhs, rcond=None)
        cur = np.array([p[x] for x in free])
        tgt = cur + sol
        inwin = all(W[x][0] - 1e-6 <= tgt[k] <= W[x][1] + 1e-6
                    for k, x in enumerate(free))
        solved = dict(residual=float(np.linalg.norm(D @ sol - rhs)),
                      in_window=bool(inwin),
                      target=[round(float(v), 4) for v in tgt])
    return dict(off=len(off), slack=len(slack), inert=len(inert),
                pinned=len(pinned),
                d_free=len(free), d_cond=d_cond,
                solved=solved,
                verdict=("at most one point" if d_cond == len(free)
                         else ("face of dim %d survives" % (len(free) - d_cond)
                               if d_cond < len(free) else "over-determined")),
                widths=[round(W[x][2], 4) for x in free][:12])
