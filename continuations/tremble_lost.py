"""Diagnose the tremble shapes whose path was lost in tremble_homotopy.py (same RNG stream)."""
import sys, json
import numpy as np
import g34, perturbed_eq as P
from tremble_shapes import follow, describe
from tremble_homotopy import step_to, deform

g = g34.Game(1.0); IX = g34.IX; N = g34.NAMES
n, seed, spread = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
rng = np.random.default_rng(seed)
done = {d['k'] for d in json.load(open('tremble_homotopy_%d.json' % seed))}
EPS = 1e-3
out = []
for k in range(n):
    mlo = np.exp(rng.uniform(-np.log(spread), np.log(spread), 48)); mhi = np.exp(rng.uniform(-np.log(spread), np.log(spread), 48))
    if k in done: continue
    r4 = mlo[IX['a41']] / (2 * (mlo[IX['a11']] + mlo[IX['a21']]))
    lo = EPS * mlo; hi = 1 - EPS * mhi
    sols = []
    for s in range(6):
        x0, _, _ = g.cfrplus(4000, lo, hi, 100 + s)
        x, M, v, sv = P.solve(g, lo, hi, x0)
        if v < 1e-12: sols.append((x, M, sv.min()))
    if not sols:
        print("shape %2d  r4 %.2f : no equilibrium found at eps = 1e-3 from 6 CFR starts" % (k, r4), flush=True); continue
    for x, M, svm in sols[:1]:
        # shrink eps
        e = EPS; lo2, hi2 = lo, hi
        for _ in range(8):
            e2 = e * 0.5
            xs, Ms, vs, svs = step_to(lo2, hi2, x, M, e2 * mlo, 1 - e2 * mhi)
            if vs > 1e-11: break
            x, M, lo2, hi2, e = xs, Ms, e2 * mlo, 1 - e2 * mhi, e2
        d = describe(x)
        print("shape %2d  r4 %.2f  eps %.1e  sv_min %.1e | b11 %.4f b21 %.4f b23 %.4f c11 %.4f c21 %.4f | beta %.4f c33 %.4f pos %.3f | mixed: %s  (%d of 6 starts solved)"
              % (k, r4, e, svm, d['b11'], d['b21'], d['b23'], d['c11'], d['c21'], d['beta'], d['c33'], d['pos'], " ".join(N[i] for i in M), len(sols)), flush=True)
        out.append(dict(k=k, r4=float(r4), eps=e, mixed=[N[i] for i in M], **d))
json.dump(out, open('tremble_lost_%d.json' % seed, 'w'))
