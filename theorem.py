"""
The general theorem, and the parts of it that are verifiable without knowing an
equilibrium.

  P1 (multilinearity)  u_i is affine in every single coordinate.
  P2 (constant sum)    sum_i u_i is constant on the whole cube, so sum_i du_i = 0.
  P3 (incidence)       s_k(y) = du_k/(-du_A) sums to 1 over k != A, so incidence
                       lives on an (n-2)-dimensional affine simplex.  n=2 -> a
                       point (nothing to ask); n=3 -> one number rho; n>=4 -> a
                       vector.
  T1 (Moebius)         for any other coordinate x, both numerator and denominator
                       are affine in x, so every share is a Moebius transform of x
                       with a pole of order <= 1 at the root x* of the denominator:
                           s_k(x) = N'_k/D' + R_k/(x - x*),   R_k = N_k(x*)/D'.
  T2 (boundary)        if x sits at a zero-reach information set then du_i/dx = 0
                       for every i, so x is unconstrained by payoffs; the only
                       equilibrium conditions on x are the incentive constraints
                       du_A/dy <= 0, each affine in x.  Their intersection is a
                       closed interval, so every pole lies on its boundary.
  T3 (residue)         at x*, du_A/dy = 0, so by P2 the deviation is costless for A
                       and purely redistributive: R is the costless transfer vector
                       divided by D'.  For n = 3 that collapses to a scalar t/D'.

Clauses (i) D' != 0, (ii) x* attainable, (iii) N_k(x*) != 0 are GAME-SPECIFIC
hypotheses -- that is what the experiments test.
"""
import numpy as np

import kuhnGen as Q


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


CASES = [(3, 4), (3, 5), (3, 6), (4, 5), (4, 6), (5, 6)]

hdr("P1 / P2 / P3 -- structural, hold at every profile, any n and N")
print("   n  N  | max |2nd diff| (multilinearity) | max |sum du| | max |sum s -1| | costly dirs")
rng = np.random.default_rng(0)
for n, N in CASES:
    g = Q.Kuhn(n, N)
    m2 = ms = mshare = 0.0
    nc = 0
    for _ in range(6):
        p = rng.random(g.nparam)
        for y in rng.choice(g.nparam, 12, replace=False):
            a, b, c = p.copy(), p.copy(), p.copy()
            a[y], b[y], c[y] = 0.0, 0.5, 1.0
            ua, ub, uc = g.utilities(a), g.utilities(b), g.utilities(c)
            m2 = max(m2, float(np.abs(ua - 2 * ub + uc).max()))
            d = g.dcoord(p, int(y))
            ms = max(ms, abs(float(d.sum())))
            A = None
            for pl in range(n):
                lo = g.offset[pl]
                if lo <= y < lo + g.ncard * g.nsit[pl]:
                    A = pl
            if abs(d[A]) > 1e-6:
                s = [d[k] / (-d[A]) for k in range(n) if k != A]
                mshare = max(mshare, abs(sum(s) - 1.0))
                nc += 1
    print("   %d  %d  | %-32.2e | %-12.2e | %-14.2e | %d"
          % (n, N, m2, ms, mshare, nc))

hdr("P3 -- the incidence simplex has FULL affine dimension n-2")
print("   n  N  | costly dirs | affine rank of the share set | n-2 | saturates?")
for n, N in CASES:
    g = Q.Kuhn(n, N)
    p = rng.random(g.nparam) * 0.6 + 0.2
    S = []
    for y in range(g.nparam):
        A = next(pl for pl in range(n)
                 if g.offset[pl] <= y < g.offset[pl] + g.ncard * g.nsit[pl])
        d = g.dcoord(p, y)
        if abs(d[A]) < 1e-9:
            continue
        S.append([d[k] / (-d[A]) for k in range(n) if k != A])
    S = np.array(S)
    r = int(np.linalg.matrix_rank(S - S.mean(0), tol=1e-9))
    print("   %d  %d  | %-11d | %-28d | %-3d | %s"
          % (n, N, len(S), r, n - 2, "yes" if r == n - 2 else "NO"))

hdr("T1 -- every share is EXACTLY a Moebius transform of any other coordinate")
print("   Fit s(x) = c + R/(x - x*) from three values of x, then predict two more.")
print("   n  N  | samples | max prediction error")
for n, N in CASES:
    g = Q.Kuhn(n, N)
    worst = 0.0
    cnt = 0
    for _ in range(4):
        p = rng.random(g.nparam) * 0.6 + 0.2
        for _ in range(8):
            y, x = rng.choice(g.nparam, 2, replace=False)
            A = next(pl for pl in range(n)
                     if g.offset[pl] <= y < g.offset[pl] + g.ncard * g.nsit[pl])
            k = (A + 1) % n

            def D(v):
                q = p.copy()
                q[x] = v
                return g.dcoord(q, int(y))
            d0, d1 = D(0.0), D(1.0)
            Dp = d1[A] - d0[A]
            if abs(Dp) < 1e-9:
                continue
            xs = -d0[A] / Dp
            Np = -(d1[k] - d0[k])
            const = Np / Dp
            R = -(d0[k] + (d1[k] - d0[k]) * xs) / Dp
            for v in (0.23, 0.77):
                if abs(v - xs) < 1e-6:
                    continue
                dv = D(v)
                if abs(dv[A]) < 1e-12:
                    continue
                pred = const + R / (v - xs)
                worst = max(worst, abs(pred - (-dv[k] / dv[A])))
                cnt += 1
    print("   %d  %d  | %-7d | %.2e" % (n, N, cnt, worst))

hdr("T2 -- zero-reach: first derivatives vanish, mixed second derivatives do NOT")
print("   Force every player to bet their best card, which sends their own later")
print("   sets with that card off-path.  Then test the deviation that RE-OPENS the")
print("   set (the owner lowering that same first-situation probability), not a")
print("   random one -- a random deviation cannot reach it and gives 0 trivially.\n")
print("   n  N  | off-path | max |du_i/dx| | max |d2u/(dy dx)| targeted | random y")
for n, N in CASES:
    g = Q.Kuhn(n, N)
    p = rng.random(g.nparam) * 0.6 + 0.2
    owner = {}
    for pl in range(n):
        for j in g.cards:
            for h in g.sit_hist[pl]:
                owner[g.pidx(pl, j, h)] = (pl, j)
    for pl in range(n):
        p[g.pidx(pl, N, g.sit_hist[pl][0])] = 1.0
    r = g.reach(p)
    off = [i for i in range(g.nparam) if r[i] < 1e-13]
    m1 = max((float(np.abs(g.dcoord(p, i)).max()) for i in off), default=0.0)
    tgt = rnd = 0.0
    for x in off:
        pl, j = owner[x]
        y = g.pidx(pl, j, g.sit_hist[pl][0])
        a, b = p.copy(), p.copy()
        a[x], b[x] = 1.0, 0.0
        tgt = max(tgt, float(np.abs(g.dcoord(a, y) - g.dcoord(b, y)).max()))
        for y2 in rng.choice(g.nparam, 5, replace=False):
            rnd = max(rnd, float(np.abs(g.dcoord(a, int(y2)) - g.dcoord(b, int(y2))).max()))
    print("   %d  %d  | %-8d | %-13.2e | %-25.6f | %.6f"
          % (n, N, len(off), m1, tgt, rnd))
print("\n   First derivatives are exactly 0 -- an off-path coordinate is unconstrained")
print("   by payoffs.  But the TARGETED mixed second derivative is large, while a")
print("   random deviation gives 0: the coordinate steers who pays precisely for the")
print("   deviation that re-opens its information set.  That is the whole mechanism.")
