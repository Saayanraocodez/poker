"""Continuation 1 / 4: which equilibrium does a fixed TREMBLE SHAPE select?

Floors eps * m_i on the two actions of every information set (m = the shape).  For each shape the
equilibrium of the perturbed game is found exactly at eps = 0.01 (CFR+ start, active-set Newton) and
followed down to small eps by warm starts; the limit is a perfect equilibrium of the game.

Output per shape: the limit's on-path parameters, the position of c33 in its window, whether the
perturbed equilibrium is isolated (smallest singular value of the indifference Jacobian), and P1 / P3
payoffs -- i.e. whether this tremble shape pins beta, the payoff split.
usage:  python tremble_shapes.py <n random shapes> [seed]
"""
import sys, json
import numpy as np
import g34, perturbed_eq as P

g = g34.Game(1.0); IX = g34.IX; N = g34.NAMES


def follow(mlo, mhi, eps0=0.01, eps_min=1e-5, fac=0.7, seed=0):
    lo = eps0 * mlo; hi = 1 - eps0 * mhi
    best = None
    for s in range(3):
        x0, _, _ = g.cfrplus(3000, lo, hi, seed + s)
        x, M, v, sv = P.solve(g, lo, hi, x0)
        if v < 1e-12: best = (x, M, v, sv); break
    if best is None: return None
    x, M, v, sv = best
    path = [(eps0, x.copy(), list(M), v, sv.min() if len(sv) else 0.0)]
    eps = eps0
    while eps * fac >= eps_min:
        e2 = eps * fac
        lo2 = e2 * mlo; hi2 = 1 - e2 * mhi
        x0 = x.copy()
        for i in range(48):
            if i in M:
                # mixed coordinates that scale with eps (near a floor) are rescaled
                if x[i] < 20 * lo[i]: x0[i] = x[i] * fac
                elif x[i] > 1 - 20 * (1 - hi[i]): x0[i] = 1 - (1 - x[i]) * fac
            else:
                x0[i] = lo2[i] if x[i] < 0.5 else hi2[i]
        # keep the active set: nudge mixed coordinates off the floors
        x0 = np.clip(x0, lo2, hi2)
        for i in M:
            x0[i] = min(max(x0[i], lo2[i] * 1.2 + 1e-12), hi2[i] - 0.2 * (1 - hi2[i]) - 1e-12)
        xs, Ms, vs, svs = solve_keep(lo2, hi2, x0, M)
        if vs > 1e-11:
            xs, Ms, vs, svs = P.solve(g, lo2, hi2, x0)
            if vs > 1e-11: path.append((e2, None, None, vs, None)); break
        x, M, eps, lo, hi = xs, Ms, e2, lo2, hi2
        path.append((eps, x.copy(), list(M), vs, svs.min() if len(svs) else 0.0))
    return path


def solve_keep(lo, hi, x0, M):
    """Newton with the given mixed set first; fall back to the general solver's repairs."""
    x = x0.copy(); M = list(M)
    for it in range(80):
        D = g.DR(x)[0]
        if np.abs(D[M]).max() < 1e-16: break
        J = P.jac(g, x, M, M)
        step = np.linalg.lstsq(J, -D[M], rcond=1e-12)[0]
        t = 1.0; xm = x[M] + step
        while np.any(xm <= lo[M]) or np.any(xm >= hi[M]):
            t *= 0.5; xm = x[M] + t * step
            if t < 1e-8: break
        if t < 1e-8: break
        x[M] = xm
    v = P.violation(g, x, lo, hi)
    sv = np.linalg.svd(P.jac(g, x, M, M), compute_uv=False)
    return x, M, v, sv


def describe(x):
    b11, b21, b23, b32, c11 = (x[IX[n]] for n in ('b11', 'b21', 'b23', 'b32', 'c11'))
    beta = max(b11, b21); w = .75 * (b11 + b21) + beta / 4
    pos = (x[IX['c33']] - (.5 - b32)) / w if w > 1e-6 else float('nan')
    return dict(b11=float(b11), b21=float(b21), b23=float(b23), c11=float(c11), c21=float(x[IX['c21']]), b41=float(x[IX['b41']]), a33=float(x[IX['a33']]),
                beta=float(beta), c33=float(x[IX['c33']]), pos=float(pos), u=[float(v) for v in g.util(x)])


if __name__ == "__main__":
    nshape = int(sys.argv[1]); seed0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    rng = np.random.default_rng(seed0); out = []
    for k in range(nshape + 1):
        if k == 0: mlo = np.ones(48); mhi = np.ones(48); name = "uniform"
        else: mlo = np.exp(rng.uniform(np.log(.2), np.log(5), 48)); mhi = np.exp(rng.uniform(np.log(.2), np.log(5), 48)); name = "random %d" % k
        path = follow(mlo, mhi, seed=10 * k)
        if path is None: print("%-10s no equilibrium found at eps = 0.01" % name, flush=True); continue
        eps, x, M, v, svm = [p for p in path if p[1] is not None][-1]
        d = describe(x)
        okend = path[-1][1] is not None
        print("%-10s eps_end %.1e%s viol %.0e  sv_min %.1e  mixed %s\n           b11 %.4f b21 %.4f b23 %.4f c11 %.4f  b41 %.4f a33 %.4f  beta %.4f  c33 %.4f (position %.3f)  u1 %.5f u3 %.5f"
              % (name, eps, "" if okend else " (lost below)", v, svm, " ".join(N[i] for i in M), d['b11'], d['b21'], d['b23'], d['c11'], d['b41'], d['a33'], d['beta'], d['c33'], d['pos'], d['u'][0], d['u'][2]), flush=True)
        out.append(dict(name=name, mlo=mlo.tolist(), mhi=mhi.tolist(), eps=eps, mixed=[N[i] for i in M], viol=float(v), svmin=float(svm), **d, x=x.tolist(),
                        path=[(float(p[0]), None if p[1] is None else describe(p[1])) for p in path]))
    json.dump(out, open('tremble_shapes_%d.json' % seed0, 'w'))
