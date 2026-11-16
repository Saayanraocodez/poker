"""Continuation 4b / 1: the logit agent quantal response equilibrium (AQRE, McKelvey & Palfrey 1998)
of three-player Kuhn poker, followed along its principal branch from lambda = 0 (uniform play).

At every information set i the aggressive action has probability
        x_i = 1 / (1 + exp(-lambda * Delta_i(x))),     Delta_i = D_i / R_i,
the expected gain (in chips) of the aggressive action given that the set is reached.  Limit points of
the branch as lambda -> infinity are sequential equilibria, and the LIMITING LOGIT EQUILIBRIUM is a
single point: a selection from the equilibrium set by a standard model of noisy play / learning.

Prediction for c33 (same algebra as Theorem 3): a tremble at set j has probability ~ exp(-lambda * cost_j),
so P3's knife-edge r4 = 2 (r1 + r2) forces cost(a41) = min(cost(a11), cost(a21)) in the limit, i.e.
c33 = lo + w/3 -- the point normal-form properness selects.

Method: pseudo-arclength continuation in (z, log lambda), z = logit(x); Newton corrector with the exact
Jacobian (D and R are multilinear, so d/dx_j is a difference of two evaluations).
usage:  python qre.py [lambda_max=400] [A=1]
"""
import sys, json
import numpy as np
import g34

LMAX = float(sys.argv[1]) if len(sys.argv) > 1 else 400.0
A = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
g = g34.Game(A); IX = g34.IX


def delta_and_jac(x):
    D, R = g.DR(x)
    JD = np.zeros((48, 48)); JR = np.zeros((48, 48))
    for j in range(48):
        x1 = x.copy(); x1[j] = 1.0; x0 = x.copy(); x0[j] = 0.0
        D1, R1 = g.DR(x1); D0, R0 = g.DR(x0)
        JD[:, j] = D1 - D0; JR[:, j] = R1 - R0
    Dl = D / R
    J = (JD - Dl[:, None] * JR) / R[:, None]
    return Dl, J


def sig(z): return 1.0 / (1.0 + np.exp(-z))


def F(z, ll):
    x = sig(z); Dl, J = delta_and_jac(x)
    lam = np.exp(ll)
    f = z - lam * Dl
    Jz = np.eye(48) - lam * J * (x * (1 - x))[None, :]
    Jl = -lam * Dl
    return f, Jz, Jl


def report(z, ll):
    x = sig(z); lam = np.exp(ll)
    b11, b21, b32 = x[IX['b11']], x[IX['b21']], x[IX['b32']]
    beta = max(b11, b21); w = .75 * (b11 + b21) + beta / 4
    pos = (x[IX['c33']] - (.5 - b32)) / w if w > 1e-12 else float('nan')
    Dl, _ = delta_and_jac(x)
    cost = -Dl[[IX['a11'], IX['a21'], IX['a31'], IX['a41']]]
    e = g.expl(x).max()
    return dict(lam=float(lam), expl=float(e), beta=float(beta), b11=float(b11), b21=float(b21), b23=float(x[IX['b23']]), b41=float(x[IX['b41']]),
                c11=float(x[IX['c11']]), c21=float(x[IX['c21']]), a33=float(x[IX['a33']]), b33=float(x[IX['b33']]),
                b32=float(b32), b22=float(x[IX['b22']]), c23=float(x[IX['c23']]), c34=float(x[IX['c34']]), c33=float(x[IX['c33']]), pos=float(pos),
                cost_open=[float(c) for c in cost], lnopen=[float(z[IX[n]]) for n in ('a11', 'a21', 'a31', 'a41')], u=[float(v) for v in g.util(x)], x=x.tolist())


if __name__ == "__main__":
    z = np.zeros(48); ll = np.log(1e-3)
    for _ in range(30):                                   # start on the branch at tiny lambda
        f, Jz, Jl = F(z, ll); z = z - np.linalg.solve(Jz, f)
    # tangent
    f, Jz, Jl = F(z, ll)
    t = np.append(-np.linalg.solve(Jz, Jl), 1.0); t /= np.linalg.norm(t)
    ds = 0.05; path = []; nxt = 1e-2; steps = 0; fails = 0
    while np.exp(ll) < LMAX and steps < 200000:
        zp = z + ds * t[:48]; lp = ll + ds * t[48]
        ok = False; zc, lc = zp.copy(), lp
        for it in range(12):
            f, Jz, Jl = F(zc, lc)
            Aug = np.zeros((49, 49)); Aug[:48, :48] = Jz; Aug[:48, 48] = Jl; Aug[48] = t
            rhs = np.append(-f, -(t[:48] @ (zc - zp) + t[48] * (lc - lp)))
            try: d = np.linalg.solve(Aug, rhs)
            except np.linalg.LinAlgError: break
            zc = zc + d[:48]; lc = lc + d[48]
            if not np.all(np.isfinite(zc)): break
            if np.abs(d).max() < 1e-10: ok = True; break
        if not ok or np.abs(zc - zp).max() > 2.0:
            ds *= 0.5; fails += 1
            if ds < 1e-9: print("step size collapsed at lambda %.4f" % np.exp(ll)); break
            continue
        # new tangent, oriented along the old one
        f, Jz, Jl = F(zc, lc)
        Aug = np.zeros((49, 49)); Aug[:48, :48] = Jz; Aug[:48, 48] = Jl; Aug[48] = t
        tn = np.linalg.solve(Aug, np.append(np.zeros(48), 1.0)); tn /= np.linalg.norm(tn)
        z, ll, t = zc, lc, tn; steps += 1
        ds = min(ds * (1.3 if it < 5 else 1.0), 0.5)
        if np.exp(ll) >= nxt:
            r = report(z, ll); r['steps'] = steps; r['dlam_sign'] = float(np.sign(t[48])); path.append(r)
            print("lam %9.3f  expl %.2e  beta %.4f (b11 %.4f b21 %.4f b23 %.4f) c11 %.4f  b32 %.2e c34 %.2e b22 %.2e c23 %.2e  c33 %.5f  pos %.4f  costs %s  u %s"
                  % (r['lam'], r['expl'], r['beta'], r['b11'], r['b21'], r['b23'], r['c11'], r['b32'], r['c34'], r['b22'], r['c23'], r['c33'], r['pos'],
                     np.round(r['cost_open'], 4), np.round(r['u'], 5)), flush=True)
            nxt *= 1.25
    json.dump(path, open('qre_path_A%g.json' % A, 'w'))
    print("done: %d steps, %d step halvings, final lambda %.3f" % (steps, fails, np.exp(ll)))
