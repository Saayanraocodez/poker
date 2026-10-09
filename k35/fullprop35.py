"""PROPOSER (float, decides nothing) of EMPTINESS certificates for regions of the FULL (3,5)-Kuhn game.

A region R is described by
  * faces:  agent (player, card) restricted to a subset of its 16 pure plans -- e.g. "P1 never opens 5"
    restricts agent (P1, 5) to the 8 check plans (a behavioural strategy with a51 = 0 is a mixture of them);
  * BR terms: "agent a plays plan rho with positive probability" => u_a(rho, s_-a) - u_a(tau, s_-a) >= 0
    for every tau (rho is then a best response).  "P1 opens j with positive probability" uses any open
    plan (they are payoff-equivalent).
Every Nash equilibrium in R makes all CCE terms  Delta_tau = u_a(s) - u_a(tau, s_-a)  and all BR terms >= 0.
So if  max over the face of  sum mu_t Delta_t + sum lam_r BR_r  < 0  for some mu, lam >= 0 (not all 0),
R contains no Nash equilibrium.  The function is multilinear: its max is at a pure profile of the face.
Cutting planes: LP over (mu, lam) with mu + lam summing to 1, separation by local search on the face.
The exact judges are fullcheck35.py / fullcheck35b.py.

Plans: bits for situations 1..4 of the player (k35 numbering):
  P1: (open, KKB call, KBF call, KBC call)   P2: (K bet, B call, KKBF call, KKBC call)
  P3: (KK bet, KB call, BF call, BC call)
usage (k35/):  KUHN_CARDS=5 python fullprop35.py <region> <out.json> [rounds]
regions: open4pos | open5one | open5zero | open3zero | open3one | open1zero_open2zero | ..."""
import os, sys, itertools, time, json
os.environ.setdefault("KUHN_CARDS", "5")
import numpy as np
from fractions import Fraction as F
from scipy.optimize import linprog
import tree as T, kuhn3p as K

NP = K.NPARAM
INT = [int(p) for p in T.INTERNAL][::-1]
DEALS = np.array(T.DEALS)
SITS = (1, 2, 3, 4)
BITS = list(itertools.product((0, 1), repeat=4))
AGENTS = [(pl, c) for pl in range(3) for c in K.CARDS]
COORDS = {(pl, c): [K.pidx(pl, c, s) for s in SITS] for (pl, c) in AGENTS}
MASK = {(pl, c): np.flatnonzero(DEALS[:, pl] == c) for (pl, c) in AGENTS}


def root_vals(X, deals=None):
    B = X.shape[0]
    dl = np.arange(T.ND) if deals is None else deals
    PAY = T.PAYT[dl]; CO = T.COORD[dl]
    V = {p: np.broadcast_to(PAY[:, p, :], (B, len(dl), 3)) for p in T.LEAFPOS}
    for p in INT:
        x = X[:, CO[:, p]][:, :, None]
        V[p] = x * V[T.AGGC[p]] + (1 - x) * V[T.PASC[p]]
    return V[0]


def agent_u_all(X, a):
    """(B, 16): u_a(tau, X_-a) for every plan tau of agent a"""
    pl, c = a; B = X.shape[0]; dl = MASK[a]
    big = np.repeat(X[None], 16, 0).reshape(16 * B, NP).copy()
    for t, bits in enumerate(BITS):
        big[t * B:(t + 1) * B][:, COORDS[a]] = bits
    R = root_vals(big, dl)[:, :, pl].mean(axis=1)
    return R.reshape(16, B).T


def region(name):
    """-> faces {agent: allowed plan indices}, brs [(agent, rho)]"""
    faces = {}; brs = []
    openp = [t for t, b in enumerate(BITS) if b[0] == 1]; checkp = [t for t, b in enumerate(BITS) if b[0] == 0]
    for part in name.split("_"):
        if part.startswith("open") and part.endswith("pos"):
            brs.append(((0, int(part[4])), openp[0]))                 # an open plan is a best response
        elif part.startswith("open") and part.endswith("one"):
            faces[(0, int(part[4]))] = openp
        elif part.startswith("open") and part.endswith("zero"):
            faces[(0, int(part[4]))] = checkp
        else:
            raise SystemExit("unknown region part " + part)
    return faces, brs


def terms(X, brs):
    """-> CCE terms (B, 15*16) and BR terms (B, len(brs)*16)"""
    B = X.shape[0]
    R = root_vals(X)
    D = []; G = []
    for a in AGENTS:
        ua = R[:, MASK[a], a[0]].mean(axis=1)
        U = agent_u_all(X, a)
        D.append(ua[:, None] - U)
        for (b, rho) in brs:
            if b == a: G.append(U[:, [rho]] - U)
    return np.hstack(D), (np.hstack(G) if G else np.zeros((B, 0)))


def random_face(n, faces, rng):
    X = rng.integers(0, 2, (n, NP)).astype(float)
    for a, allowed in faces.items():
        pick = rng.choice(allowed, n)
        X[:, COORDS[a]] = np.array(BITS)[pick]
    return X


def free_coords(faces):
    fixed = set()
    for a, allowed in faces.items():
        arr = np.array([BITS[t] for t in allowed])
        for s in range(4):
            if (arr[:, s] == arr[0, s]).all(): fixed.add(COORDS[a][s])
    return [i for i in range(NP) if i not in fixed]


def in_face(X, faces):
    ok = np.ones(X.shape[0], bool)
    for a, allowed in faces.items():
        bits = X[:, COORDS[a]].round().astype(int)
        idx = bits[:, 0] * 8 + bits[:, 1] * 4 + bits[:, 2] * 2 + bits[:, 3]
        ok &= np.isin(idx, allowed)
    return ok


def Lval(X, w, brs):
    D, G = terms(X, brs)
    return np.hstack([D, G]) @ w


def local_search(w, brs, faces, rng, starts=48, iters=300):
    free = free_coords(faces)
    X = random_face(starts, faces, rng)
    cur = Lval(X, w, brs)
    for _ in range(iters):
        Fl = np.repeat(X, len(free), 0)
        idx = np.tile(np.array(free), starts)
        Fl[np.arange(len(Fl)), idx] = 1 - Fl[np.arange(len(Fl)), idx]
        val = Lval(Fl, w, brs)
        val[~in_face(Fl, faces)] = -np.inf
        val = val.reshape(starts, len(free))
        best = val.argmax(1); bv = val.max(1)
        imp = bv > cur + 1e-12
        if not imp.any(): break
        for s in np.flatnonzero(imp):
            X[s, free[best[s]]] = 1 - X[s, free[best[s]]]; cur[s] = bv[s]
    return X, cur


def solve_lp(M):
    n, m = M.shape
    c = np.zeros(m + 1); c[-1] = 1
    A = np.hstack([M, -np.ones((n, 1))]); b = np.zeros(n)
    Aeq = np.zeros((1, m + 1)); Aeq[0, :m] = 1
    res = linprog(c, A_ub=A, b_ub=b, A_eq=Aeq, b_eq=[1], bounds=[(0, None)] * m + [(None, None)], method="highs")
    return res.x[:m], res.x[-1]


if __name__ == "__main__":
    name = sys.argv[1]; out = sys.argv[2]; rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    faces, brs = region(name)
    rng = np.random.default_rng(0)
    X0 = random_face(3000, faces, rng)
    D, G = terms(X0, brs)
    rows = [np.hstack([D, G])]
    t0 = time.time()
    for r in range(rounds):
        M = np.vstack(rows)
        w, s = solve_lp(M)
        X, cur = local_search(w, brs, faces, rng)
        print("round %3d: LP value %.6f over %d profiles; separation max %.6f; nonzero %d  (%.0fs)" % (
            r, s, len(M), cur.max(), (w > 1e-9).sum(), time.time() - t0), flush=True)
        new = cur > s + 1e-9
        if not new.any():
            print("local search finds nothing above the LP value %.6f (%s)" % (
                s, "candidate emptiness certificate" if s < 0 else "NO certificate: value >= 0"), flush=True)
            break
        D, G = terms(X[new], brs); rows.append(np.hstack([D, G]))
    nD = 15 * 16
    cert = {"region": name, "faces": {"%d,%d" % a: v for a, v in faces.items()},
            "brs": [[a[0], a[1], rho] for a, rho in brs], "lp_value": float(s),
            "mu": [[AGENTS[i // 16][0], AGENTS[i // 16][1], i % 16, str(F(int(round(w[i] * 10 ** 6)), 10 ** 6))]
                   for i in range(nD) if round(w[i] * 10 ** 6) > 0],
            "lam": [[n, str(F(int(round(w[nD + n] * 10 ** 6)), 10 ** 6))] for n in range(len(w) - nD) if round(w[nD + n] * 10 ** 6) > 0]}
    json.dump(cert, open(out, "w"), indent=0)
    print("wrote", out)
