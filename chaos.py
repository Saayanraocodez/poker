"""
Is the learning flow on three-player Kuhn chaotic?

Integrate the replicator flow  dx_i/dt = x_i(1-x_i) g_i(x)  and measure the
largest Lyapunov exponent by the Benettin tangent-space method, using the EXACT
Jacobian rather than a finite-difference twin trajectory.

    lambda = lim (1/T) sum log( |delta(t+h)| / |delta(t)| )

lambda > 0  -> chaos;  lambda ~ 0 -> neutral / cyclic;  lambda < 0 -> convergent.

Two-player Kuhn is the control: two-player zero-sum replicator dynamics are
volume preserving and famously cycle, so lambda should sit at ~0 there.
"""
import numpy as np

import kuhn3p as K
import dynamics as D
import kuhn2p as T

OWN3 = np.arange(48) // 16


def f3(x):
    return x * (1.0 - x) * D.g_vec(x)


def f2(x):
    g = np.array([T.exact_coord_derivative(x, i)[0 if i < 6 else 1] for i in range(12)])
    return x * (1.0 - x) * g


def J2(x, eps=1e-6):
    n = len(x)
    J = np.empty((n, n))
    f0 = f2(x)
    for j in range(n):
        y = x.copy()
        y[j] = min(1 - 1e-12, y[j] + eps)
        J[:, j] = (f2(y) - f0) / (y[j] - x[j])
    return J


def rk4(x, f, h):
    k1 = f(x)
    k2 = f(np.clip(x + h / 2 * k1, 1e-12, 1 - 1e-12))
    k3 = f(np.clip(x + h / 2 * k2, 1e-12, 1 - 1e-12))
    k4 = f(np.clip(x + h * k3, 1e-12, 1 - 1e-12))
    return np.clip(x + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4), 1e-12, 1 - 1e-12)


def lyapunov(x0, f, jac, h=0.02, steps=6000, burn=600):
    """Benettin, with the TANGENT vector integrated by RK4 on the augmented
    system rather than by a first-order Euler step.  The Euler version carries a
    positive bias large enough to swamp the signal -- the two-player control,
    whose true exponent is exactly 0, reads +0.006 under it."""
    x = x0.copy()
    d = np.random.default_rng(0).normal(size=len(x))
    d /= np.linalg.norm(d)
    acc, cnt = 0.0, 0
    for s in range(steps):
        # RK4 on (x, d) together: d' = J(x) d
        J1 = jac(x); k1x = f(x); k1d = J1 @ d
        x2 = np.clip(x + h / 2 * k1x, 1e-12, 1 - 1e-12)
        J2 = jac(x2); k2x = f(x2); k2d = J2 @ (d + h / 2 * k1d)
        x3 = np.clip(x + h / 2 * k2x, 1e-12, 1 - 1e-12)
        J3 = jac(x3); k3x = f(x3); k3d = J3 @ (d + h / 2 * k2d)
        x4 = np.clip(x + h * k3x, 1e-12, 1 - 1e-12)
        J4 = jac(x4); k4x = f(x4); k4d = J4 @ (d + h * k3d)
        x = np.clip(x + h / 6 * (k1x + 2 * k2x + 2 * k3x + k4x), 1e-12, 1 - 1e-12)
        d = d + h / 6 * (k1d + 2 * k2d + 2 * k3d + k4d)
        nrm = np.linalg.norm(d)
        if nrm < 1e-300:
            break
        d /= nrm
        if s >= burn:
            acc += np.log(nrm)
            cnt += 1
    return acc / (cnt * h) if cnt else np.nan, x


if __name__ == "__main__":
    rng = np.random.default_rng(1)
    print("THREE-PLAYER (48 coordinates), replicator flow from random interior starts")
    print("   run   largest Lyapunov exp.   |dx/dt| at end   max |x - nearest pure|")
    lam3 = []
    for r in range(5):
        x0 = rng.uniform(0.15, 0.85, 48)
        lam, xe = lyapunov(x0, f3, D.jacobian, h=0.02, steps=3000, burn=400)
        lam3.append(lam)
        drift = float(np.abs(f3(xe)).max())
        mix = float(np.minimum(xe, 1 - xe).max())
        print("   %-5d %+.6f              %.2e         %.4f" % (r, lam, drift, mix))
    print("   mean lambda = %+.6f" % np.mean(lam3))
    print()
    print("TWO-PLAYER control (12 coordinates) -- conservative, TRUE lambda = 0 exactly")
    lam2 = []
    for r in range(4):
        x0 = rng.uniform(0.15, 0.85, 12)
        lam, xe = lyapunov(x0, f2, J2, h=0.02, steps=3000, burn=400)
        lam2.append(lam)
        print("   %-5d %+.6f              %.2e" % (r, lam, float(np.abs(f2(xe)).max())))
    print("   mean lambda = %+.6f" % np.mean(lam2))
