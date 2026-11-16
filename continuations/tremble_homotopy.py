"""Tremble shapes, robustly: at a fixed small eps, deform the floors from the uniform shape to a target
shape in small steps, following the perturbed game's equilibrium (active-set Newton with repairs).
Then shrink eps with the target shape.  See tremble_shapes.py for the question.
usage:  python tremble_homotopy.py <n shapes> <seed> [spread=3]
"""
import sys, json
import numpy as np
import g34, perturbed_eq as P
from tremble_shapes import follow, solve_keep, describe

g = g34.Game(1.0); IX = g34.IX; N = g34.NAMES


def step_to(lo, hi, x, M, lo2, hi2):
    """warm start: floor coordinates move with their floors, mixed ones keep their value (rescaled if near a floor)."""
    x0 = x.copy()
    for i in range(48):
        if i in M:
            if x[i] - lo[i] < 5 * lo[i]: x0[i] = lo2[i] + (x[i] - lo[i]) * (lo2[i] / lo[i])
            elif hi[i] - x[i] < 5 * (1 - hi[i]): x0[i] = hi2[i] - (hi[i] - x[i]) * ((1 - hi2[i]) / (1 - hi[i]))
            x0[i] = min(max(x0[i], lo2[i] + 1e-14), hi2[i] - 1e-14)
        else:
            x0[i] = lo2[i] if x[i] < 0.5 else hi2[i]
    xs, Ms, vs, svs = solve_keep(lo2, hi2, x0, M)
    if vs > 1e-12:
        xs, Ms, vs, svs = P.solve(g, lo2, hi2, x0)
    return xs, Ms, vs, svs


def deform(mlo_t, mhi_t, eps, x, M, nsteps=40):
    ones = np.ones(48); t = 0.0; dt = 1.0 / nsteps
    lo = eps * ones; hi = 1 - eps * ones
    while t < 1 - 1e-12:
        t2 = min(1.0, t + dt)
        mlo = np.exp((1 - t2) * 0 + t2 * np.log(mlo_t)); mhi = np.exp(t2 * np.log(mhi_t))
        lo2 = eps * mlo; hi2 = 1 - eps * mhi
        xs, Ms, vs, svs = step_to(lo, hi, x, M, lo2, hi2)
        if vs > 1e-11:
            dt *= 0.5
            if dt < 1e-5: return None
            continue
        x, M, lo, hi, t = xs, Ms, lo2, hi2, t2
        dt = min(dt * 1.5, 1.0 / nsteps)
    return x, M, lo, hi


if __name__ == "__main__":
    n = int(sys.argv[1]); seed = int(sys.argv[2]); spread = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
    rng = np.random.default_rng(seed)
    EPS = 1e-3
    path = follow(np.ones(48), np.ones(48), eps0=0.01, eps_min=EPS, fac=0.7)
    eps_u, xu, Mu = path[-1][0], path[-1][1], path[-1][2]
    lo = EPS * np.ones(48); hi = 1 - lo
    xu, Mu, v, _ = step_to(eps_u * np.ones(48), 1 - eps_u * np.ones(48), xu, Mu, lo, hi)
    assert v < 1e-12
    out = []
    for k in range(n):
        mlo = np.exp(rng.uniform(-np.log(spread), np.log(spread), 48)); mhi = np.exp(rng.uniform(-np.log(spread), np.log(spread), 48))
        r = deform(mlo, mhi, EPS, xu.copy(), list(Mu))
        if r is None: print("shape %2d: path lost during the deformation" % k, flush=True); continue
        x, M, lo2, hi2 = r
        # shrink eps with this shape
        e = EPS; ok = True
        for _ in range(8):
            e2 = e * 0.5
            xs, Ms, vs, svs = step_to(lo2, hi2, x, M, e2 * mlo, 1 - e2 * mhi)
            if vs > 1e-11: ok = False; break
            x, M, lo2, hi2, e = xs, Ms, e2 * mlo, 1 - e2 * mhi, e2
        sv = np.linalg.svd(P.jac(g, x, M, M), compute_uv=False)
        d = describe(x)
        r4 = mlo[IX['a41']] / (2 * (mlo[IX['a11']] + mlo[IX['a21']]))
        print("shape %2d eps %.1e viol %.0e sv_min %.1e | b11 %.4f b21 %.4f b23 %.4f c11 %.4f c21 %.4f | beta %.4f  c33 pos %.3f | floor(a41)/2(floor a11+a21) = %.2f | mixed: %s"
              % (k, e, P.violation(g, x, lo2, hi2), sv.min(), d['b11'], d['b21'], d['b23'], d['c11'], d['c21'], d['beta'], d['pos'], r4, " ".join(N[i] for i in M)), flush=True)
        out.append(dict(k=k, eps=e, mlo=mlo.tolist(), mhi=mhi.tolist(), mixed=[N[i] for i in M], svmin=float(sv.min()), r4=float(r4), **d, x=x.tolist()))
    json.dump(out, open('tremble_homotopy_%d.json' % seed, 'w'))
