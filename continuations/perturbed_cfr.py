"""Continuation 4a: which equilibrium does a learning dynamic reach when every action trembles?

CFR+ (full width, alternating) on the PERTURBED game: every action at every information set has
probability at least a floor.  Equilibria of the perturbed game converge, as the floor goes to 0, to
(agent-normal-form) perfect equilibria.  Theorem 6 says the whole interval of c33 is perfect; this
asks which point a GIVEN tremble shape selects.

Prediction (from P3's knife-edge r4 = 2 (r1 + r2) at BF holding the 3):
  floor(a41) < 2 (floor(a11) + floor(a21))  ->  P3 would call; so P1 raises a41 above its floor until
        r4 = 2 (r1 + r2), which needs P1 indifferent on a41:  c33 -> hi, the UPPER end of the window;
  floor(a41) > 2 (floor(a11) + floor(a21))  ->  mirror image: a11 + a21 rise, c33 -> lo, the LOWER end.
Uniform floors are the first case.  Either way the limit is one of the two poles of the incidence ratio.

usage:  python perturbed_cfr.py <iters> <seeds> [k=1 floor multiplier on a41] [eps list]
"""
import sys, json, time
import numpy as np
import g34

iters = int(float(sys.argv[1])); nseed = int(sys.argv[2]); k41 = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
EPS = [float(v) for v in sys.argv[4].split(',')] if len(sys.argv) > 4 else [0.02, 0.01, 0.005]
IX = g34.IX; g = g34.Game(1.0)
out = []
for eps in EPS:
    lo = np.full(48, eps); hi = np.full(48, 1 - eps)
    lo[IX['a41']] = k41 * eps
    for seed in range(nseed):
        t0 = time.time()
        x, R, S = g.cfrplus(iters, lo, hi, seed)
        e = g.expl(x, lo, hi).max()
        b11, b21, b32, c33, c23 = (x[IX[n]] for n in ('b11', 'b21', 'b32', 'c33', 'c23'))
        beta = max(b11, b21); w = .75 * (b11 + b21) + beta / 4; lo33 = .5 - b32
        D, Rr = g.DR(x)
        rec = dict(eps=eps, seed=seed, k41=k41, expl=float(e), beta=float(beta), w=float(w),
                   a=[float(x[IX[n]]) for n in ('a11', 'a21', 'a31', 'a41')],
                   ratio=float(x[IX['a41']] / (x[IX['a11']] + x[IX['a21']])),
                   b32=float(b32), b22=float(x[IX['b22']]), c23=float(c23), c34=float(x[IX['c34']]), c33=float(c33),
                   pos=float((c33 + c23 - lo33) / w) if w > 1e-9 else None,
                   Dopen=[float(24 * D[IX[n]]) for n in ('a11', 'a21', 'a31', 'a41')], x=x.tolist(), secs=time.time() - t0)
        out.append(rec)
        print("eps %.4f seed %d k41 %g  expl %.1e  beta %.3f  a_j1/eps %s  a41/(a11+a21) %.3f  b32 %.4f c34 %.4f  c33 %.4f  position in window %.3f   24*D_open %s"
              % (eps, seed, k41, e, beta, np.round(np.array(rec['a']) / eps, 2), rec['ratio'], b32, rec['c34'], c33, rec['pos'], np.round(rec['Dopen'], 5)), flush=True)
json.dump(out, open('perturbed_cfr_k%g.json' % k41, 'w'))
