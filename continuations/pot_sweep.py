"""Continuation 3: the ante as a parameter.  Three-player four-card Kuhn poker with ante A and bet 1
(pot before betting P = 3A; the standard game is A = 1).  Where does P1 start betting?

For each A: full-width CFR+ from several seeds, then an active-set Newton polish on the D-conditions
(exact to machine precision when it converges); report exploitability, P1's opening frequencies and
payoffs.  Float exploration: it decides nothing, it locates the thresholds for the exact work.
usage:  python pot_sweep.py <A list or lo:hi:n> [iters=6000] [seeds=3]
"""
import sys, json
import numpy as np
import g34, perturbed_eq as P

arg = sys.argv[1]
if ':' in arg:
    lo_, hi_, n_ = arg.split(':'); AS = list(np.exp(np.linspace(np.log(float(lo_)), np.log(float(hi_)), int(n_))))
else: AS = [float(v) for v in arg.split(',')]
iters = int(sys.argv[2]) if len(sys.argv) > 2 else 6000
nseed = int(sys.argv[3]) if len(sys.argv) > 3 else 3
IX = g34.IX; N = g34.NAMES
out = []
for A in AS:
    g = g34.Game(A)
    for seed in range(nseed):
        x, _, _ = g.cfrplus(iters, seed=seed)
        e0 = g.expl(x).max()
        xp, M, v, sv = P.solve(g, np.zeros(48), np.ones(48), x)
        e1 = g.expl(xp).max()
        use = xp if e1 < e0 else x
        e = min(e0, e1)
        op = [use[IX[n]] for n in ('a11', 'a21', 'a31', 'a41')]
        u = g.util(use)
        print("A %.4f seed %d  expl cfr %.1e polished %.1e | P1 opens %s | b_j1 %s | c_j1 %s | u/A %s"
              % (A, seed, e0, e1, np.round(op, 4), np.round([use[IX['b%d1' % j]] for j in range(1, 5)], 3), np.round([use[IX['c%d1' % j]] for j in range(1, 5)], 3), np.round(u / A, 5)), flush=True)
        out.append(dict(A=float(A), seed=seed, expl=float(e), expl_cfr=float(e0), open=[float(v_) for v_ in op], u=[float(v_) for v_ in u], x=use.tolist()))
json.dump(out, open('pot_sweep_%s.json' % arg.replace(':', '_').replace(',', '_')[:40], 'w'))
