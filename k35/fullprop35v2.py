"""fullprop35.py, faster: profiles are 15 plan indices (one per agent), payoffs come from a precomputed
table PAY[deal, P1 plan, P2 plan, P3 plan] (from tree.py), and the local search moves one agent to
another plan of its face.  Same LP, same certificate format, same judges (fullcheck35 / fullcheck35b);
float, decides nothing.  Agent order: P1 cards 1..5, P2 cards 1..5, P3 cards 1..5.
CE mode (env KUHN_CE=1): the multipliers may depend on the plan the agent actually plays -- terms
  1[agent a plays a plan of class rho] * (u_a(s) - u_a(tau, s_-a)) >= 0 at every NE (every played plan is
  a best response; payoff-equivalent plans share a class, represented by its smallest plan in the face).
usage (k35/):  KUHN_CARDS=5 [KUHN_CE=1] python fullprop35v2.py <region> <out.json> [rounds] [starts]"""
import os, sys, itertools, time, json
os.environ.setdefault("KUHN_CARDS", "5")
import numpy as np
from fractions import Fraction as F
from scipy.optimize import linprog
import tree as T, kuhn3p as K
from fullprop35 import region, BITS, AGENTS, solve_lp

SITS = (1, 2, 3, 4)
ND = T.ND
DEALS = [tuple(int(x) for x in T.DEALS[d]) for d in range(ND)]
AIDX = {a: n for n, a in enumerate(AGENTS)}
DAG = np.array([[AIDX[(0, d[0])], AIDX[(1, d[1])], AIDX[(2, d[2])]] for d in DEALS])     # (60, 3)


def _pay_table():
    P = np.zeros((ND, 16, 16, 16, 3), dtype=np.int8)
    for d in range(ND):
        cards = DEALS[d]
        for r in itertools.product(range(16), repeat=3):
            x = {}
            for pl in range(3):
                for s, b in zip(SITS, BITS[r[pl]]): x[K.pidx(pl, cards[pl], s)] = b
            p = 0
            while int(T.AGGC[p]) >= 0:
                p = int(T.AGGC[p]) if x[int(T.COORD[d, p])] == 1 else int(T.PASC[p])
            P[(d,) + r] = [int(round(v)) for v in T.PAYT[d, p]]
    return P


_cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fullcert", "pay35.npy")
if os.path.exists(_cache):
    PAY = np.load(_cache)
else:
    PAY = _pay_table(); np.save(_cache, PAY)
AG_DEALS = [np.flatnonzero((DAG == n).any(axis=1)) for n in range(15)]
CE = os.environ.get("KUHN_CE", "") == "1"


def classes(faces):
    """per agent: array plan -> representative (smallest payoff-equivalent plan of the face), -1 outside"""
    out = []
    for n, a in enumerate(AGENTS):
        pl = a[0]; ds = AG_DEALS[n]; allowed = faces.get(a, list(range(16)))
        rep = -np.ones(16, int); seen = {}
        for p in sorted(allowed):
            sig = []
            for d in ds:
                sl = [slice(None)] * 3; sl[pl] = p
                sig.append(PAY[(d,) + tuple(sl)].tobytes())
            rep[p] = seen.setdefault(tuple(sig), p)
        out.append(rep)
    return out


def terms_ce(Pl, brs, cls):
    """CE terms: column block (agent, class representative rho, tau); only representatives get columns"""
    D, G = terms(Pl, brs)
    blocks = []
    for n in range(15):
        reps = sorted(set(int(r) for r in cls[n] if r >= 0))
        R = cls[n][Pl[:, n]]
        for rho in reps:
            blocks.append(np.where((R == rho)[:, None], D[:, n * 16:(n + 1) * 16], 0.0))
    return np.hstack(blocks), G


def ce_index(cls):
    idx = []
    for n, a in enumerate(AGENTS):
        for rho in sorted(set(int(r) for r in cls[n] if r >= 0)):
            for t in range(16): idx.append((a, rho, t))
    return idx


def terms(Pl, brs):
    """Pl (B, 15) plan indices -> CCE terms (B, 240), BR terms (B, 16 * len(brs)) in AGENTS order"""
    B = Pl.shape[0]
    D = np.empty((B, 240)); G = []
    for n, a in enumerate(AGENTS):
        pl = a[0]; ds = AG_DEALS[n]
        idx = Pl[:, DAG[ds]]                                     # (B, 12, 3)
        base = PAY[ds[None, :], idx[:, :, 0], idx[:, :, 1], idx[:, :, 2], pl].astype(np.float64).mean(axis=1)
        U = np.empty((B, 16))
        for t in range(16):
            ii = idx.copy(); ii[:, :, pl] = t
            U[:, t] = PAY[ds[None, :], ii[:, :, 0], ii[:, :, 1], ii[:, :, 2], pl].mean(axis=1)
        D[:, n * 16:(n + 1) * 16] = base[:, None] - U
        for (b, rho) in brs:
            if b == a: G.append(U[:, [rho]] - U)
    return D, (np.hstack(G) if G else np.zeros((B, 0)))


def allowed(faces):
    return [faces.get(a, list(range(16))) for a in AGENTS]


def random_face(n, faces, rng):
    al = allowed(faces)
    return np.stack([rng.choice(al[i], n) for i in range(15)], axis=1)


def T_all(Pl, brs, cls):
    return np.hstack(terms_ce(Pl, brs, cls) if CE else terms(Pl, brs))


def local_search(w, brs, faces, rng, starts=48, iters=200, cls=None):
    al = allowed(faces)
    Pl = random_face(starts, faces, rng)
    cur = T_all(Pl, brs, cls) @ w
    moves = [(i, t) for i in range(15) for t in al[i]]
    for _ in range(iters):
        Nb = np.repeat(Pl, len(moves), 0)
        ii = np.tile(np.array([m[0] for m in moves]), starts); tt = np.tile(np.array([m[1] for m in moves]), starts)
        Nb[np.arange(len(Nb)), ii] = tt
        val = (T_all(Nb, brs, cls) @ w).reshape(starts, len(moves))
        best = val.argmax(1); bv = val.max(1)
        imp = bv > cur + 1e-12
        if not imp.any(): break
        for s in np.flatnonzero(imp):
            i, t = moves[best[s]]; Pl[s, i] = t; cur[s] = bv[s]
    return Pl, cur


if __name__ == "__main__":
    name = sys.argv[1]; out = sys.argv[2]
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    starts = int(sys.argv[4]) if len(sys.argv) > 4 else 48
    faces, brs = region(name)
    cls = classes(faces)
    rng = np.random.default_rng(0)
    rows = [T_all(random_face(4000, faces, rng), brs, cls)]
    t0 = time.time()
    for r in range(rounds):
        M = np.vstack(rows)
        w, s = solve_lp(M)
        Pl, cur = local_search(w, brs, faces, rng, starts, cls=cls)
        print("round %3d: LP value %.6f over %d profiles; separation max %.6f; nonzero %d  (%.0fs)" % (
            r, s, len(M), cur.max(), (w > 1e-9).sum(), time.time() - t0), flush=True)
        new = cur > s + 1e-9
        if not new.any():
            print("local search finds nothing above the LP value %.6f (%s)" % (
                s, "candidate emptiness certificate" if s < 0 else "NO certificate: value >= 0"), flush=True)
            break
        rows.append(T_all(Pl[new], brs, cls))
    nD = len(ce_index(cls)) if CE else 240
    cert = {"region": name, "faces": {"%d,%d" % a: v for a, v in faces.items()},
            "brs": [[a[0], a[1], rho] for a, rho in brs], "lp_value": float(s), "proposer": "fullprop35v2.py",
            "mu": [] if CE else [[AGENTS[i // 16][0], AGENTS[i // 16][1], i % 16, str(F(int(round(w[i] * 10 ** 6)), 10 ** 6))]
                   for i in range(nD) if round(w[i] * 10 ** 6) > 0],
            "ce": [] if not CE else [[a[0], a[1], rho, t, str(F(int(round(w[i] * 10 ** 6)), 10 ** 6))]
                   for i, (a, rho, t) in enumerate(ce_index(cls)) if round(w[i] * 10 ** 6) > 0],
            "lam": [[n, str(F(int(round(w[nD + n] * 10 ** 6)), 10 ** 6))] for n in range(len(w) - nD) if round(w[nD + n] * 10 ** 6) > 0]}
    json.dump(cert, open(out, "w"), indent=0)
    print("wrote", out)
