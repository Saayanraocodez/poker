"""PROPOSER (float, decides nothing) of a coarse-correlated-equilibrium certificate for the (3,5) restricted
game G_c (P1 never opens):  multipliers mu_tau >= 0, one per (player, card, pure plan tau), such that
    L(s) = u_1(s | 5) + sum_tau mu_tau * ( u_a(s | c) - u_a(tau, s_-a | c) )        a = (player, card) of tau
stays below 19/8 at every pure profile.  At a Nash equilibrium of G_c every bracket is >= 0 (no profitable
deviation to tau), so u_1(s|5) = V_5 <= L(s) <= max over pure profiles (L is multilinear).
Cutting planes: an LP over mu on a growing set of pure profiles, separation by local search.  The result is
written, rounded to the grid 1e-6, as an exact certificate for k35/ceverify.py and k35/ceverify2.py, which
are the ONLY judges (exact, integer arithmetic, all 2^40 pure profiles).  A tau multiplier is written in the
CE form mu[rho, tau] = mu_tau for every rho != tau of the same agent (u_a(s) = sum_rho P_s(rho) u_a(rho, s_-a)).
Control: at the 7 polished restricted equilibria (silent35b.json) every bracket must be >= 0 (float).
usage (k35/):  KUHN_CARDS=5 python cceprop35.py <out.json> [cap=50] [rounds=300]
2026-10-08: converged in 22 rounds to ~2.3153 (target < 2.375)."""
import os, sys, itertools, time, json
os.environ.setdefault("KUHN_CARDS", "5")
import numpy as np
from fractions import Fraction as F
from scipy.optimize import linprog
import tree as T, kuhn3p as K

NP = K.NPARAM
INT = [int(p) for p in T.INTERNAL][::-1]
DEALS = np.array(T.DEALS)
OPEN = [K.pidx(0, j, 1) for j in K.CARDS]
OFF = [K.pidx(1, c, 2) for c in K.CARDS] + [K.pidx(2, c, s) for c in K.CARDS for s in (3, 4)]
LIVE = [i for i in range(NP) if i not in OPEN and i not in OFF]          # the 40 coordinates of G_c
SITS = {0: (2, 3, 4), 1: (1, 3, 4), 2: (1, 2)}                          # the plan bits, in ceverify's order
PLANS = []                                                              # (player, card, {coord: value})
for pl in range(3):
    for c in K.CARDS:
        cs = [K.pidx(pl, c, s) for s in SITS[pl]]
        for bits in itertools.product((0, 1), repeat=len(cs)):
            PLANS.append((pl, c, dict(zip(cs, bits))))
NT = len(PLANS)
MASK = {(pl, c): (DEALS[:, pl] == c) for pl in range(3) for c in K.CARDS}
AGENTS = {}
for _t, (_pl, _c, _plan) in enumerate(PLANS): AGENTS.setdefault((_pl, _c), []).append(_t)
DEALIDX = {k: np.flatnonzero(MASK[k]) for k in MASK}


def root_vals(X, deals=None):
    """X (B, NP) -> (B, nd, 3) root values over the given deals (default all)"""
    B = X.shape[0]
    dl = np.arange(T.ND) if deals is None else deals
    PAY = T.PAYT[dl]; CO = T.COORD[dl]
    V = {p: np.broadcast_to(PAY[:, p, :], (B, len(dl), 3)) for p in T.LEAFPOS}
    for p in INT:
        x = X[:, CO[:, p]][:, :, None]
        V[p] = x * V[T.AGGC[p]] + (1 - x) * V[T.PASC[p]]
    return V[0]


def terms(X):
    """-> obj (B,) = u_1(.|5), Delta (B, NT); each deviation evaluated on its agent's 12 deals only"""
    B = X.shape[0]
    R = root_vals(X)
    obj = R[:, MASK[0, 5], 0].mean(axis=1)
    D = np.empty((B, NT))
    for (pl, c), ts in AGENTS.items():
        dl = DEALIDX[pl, c]
        base = R[:, dl, pl].mean(axis=1)
        big = np.repeat(X[None], len(ts), 0).reshape(len(ts) * B, NP).copy()
        for n, t in enumerate(ts):
            for i, v in PLANS[t][2].items(): big[n * B:(n + 1) * B, i] = v
        R2 = root_vals(big, dl)[:, :, pl].mean(axis=1)
        for n, t in enumerate(ts):
            D[:, t] = base - R2[n * B:(n + 1) * B]
    return obj, D


def L(X, mu):
    o, D = terms(X)
    return o + D @ mu


def local_search(mu, rng, starts=64, iters=200):
    X = np.zeros((starts, NP)); X[:, LIVE] = rng.integers(0, 2, (starts, len(LIVE)))
    cur = L(X, mu)
    for _ in range(iters):
        Fl = np.repeat(X, len(LIVE), 0)
        idx = np.tile(np.array(LIVE), starts)
        Fl[np.arange(len(Fl)), idx] = 1 - Fl[np.arange(len(Fl)), idx]
        val = L(Fl, mu).reshape(starts, len(LIVE))
        best = val.argmax(1); bv = val.max(1)
        imp = bv > cur + 1e-12
        if not imp.any(): break
        for s in np.flatnonzero(imp):
            X[s, LIVE[best[s]]] = 1 - X[s, LIVE[best[s]]]; cur[s] = bv[s]
    return X, cur


def solve_lp(V_obj, V_D, cap):
    n = len(V_obj)
    c = np.zeros(NT + 1); c[-1] = 1
    A = np.hstack([V_D, -np.ones((n, 1))]); b = -V_obj
    res = linprog(c, A_ub=A, b_ub=b, bounds=[(0, cap)] * NT + [(None, None)], method="highs")
    return res.x[:NT], res.x[-1]


def write_cert(mu, path, den=10 ** 6):
    rows = []
    for t, m in enumerate(mu):
        q = F(int(round(float(m) * den)), den)
        if q <= 0: continue
        pl, c, plan = PLANS[t]
        tb = [plan[K.pidx(pl, c, s)] for s in SITS[pl]]
        for r in AGENTS[pl, c]:
            if r == t: continue
            rp = PLANS[r][2]
            rows.append([pl, c, [rp[K.pidx(pl, c, s)] for s in SITS[pl]], tb, str(q)])
    json.dump({"kind": "cce", "proposer": "cceprop35.py", "mu": rows}, open(path, "w"))
    return len(rows)


if __name__ == "__main__":
    out = sys.argv[1]
    cap = float(sys.argv[2]) if len(sys.argv) > 2 else 50.0
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    sys.path.insert(1, "..")
    from cert35gen import kgen_to_k35
    for e in json.load(open("../silent35b.json")):
        if max(e["sub_expl"]) < 1e-12:
            p = np.array(kgen_to_k35(e["profile"]), float); p[OPEN] = 0.0
            o, D = terms(p[None])
            print("control seed %d: u1(.|5) = %.6f, min bracket = %.2e (an NE of G_c => >= 0)" % (e["seed"], o[0], D.min()), flush=True)
    rng = np.random.default_rng(0)
    X0 = np.zeros((2000, NP)); X0[:, LIVE] = rng.integers(0, 2, (2000, len(LIVE)))
    o, D = terms(X0)
    VO = list(o); VD = list(D)
    t0 = time.time()
    for r in range(rounds):
        mu, s = solve_lp(np.array(VO), np.array(VD), cap)
        X, cur = local_search(mu, rng)
        o, D = terms(X)
        print("round %2d: LP bound %.5f over %d profiles; separation max L %.5f; mu>0: %d  (%.0fs)" % (
            r, s, len(VO), cur.max(), (mu > 1e-9).sum(), time.time() - t0), flush=True)
        new = cur > s + 1e-9
        if not new.any():
            print("local search finds no profile above the LP bound %.5f (target < 19/8 = 2.375)" % s, flush=True)
            break
        VO += list(o[new]); VD += list(D[new])
    np.save(out.replace(".json", "_mu.npy"), mu)
    print("certificate: %d CE-form multipliers -> %s ; now run ceverify.py and ceverify2.py on it" % (write_cert(mu, out), out))
