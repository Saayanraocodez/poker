"""PROPOSER (float, decides nothing) with INDEPENDENCE PRODUCTS -- a first level of a hierarchy above the
coarse-correlated relaxation of fullprop35v2.py.

At a Nash equilibrium every CCE term Delta_t(s) = u_a(s) - u_a(t, s_-a) and every region BR term is >= 0,
and so is its product with the probability P_s(b plays pi) of any plan pi of any agent b.  The product
stays MULTILINEAR -- so its maximum over the cube is still at a pure profile -- exactly when b's
coordinates do not occur in the term: b never shares a deal with a, i.e. b is the same player holding
another card, or another player holding a's card.  At a pure profile the product is the term times the
indicator [b plays a plan of class pi].  In the relaxation (a distribution over pure profiles) this forces
every agent's incentive constraint to hold separately for each plan of each agent it never meets -- the
correlation a coarse-correlated device uses to fake incentives is cut there.
usage (k35/):  KUHN_CARDS=5 python fullprop35p.py <region> <out.json> [rounds] [starts] [P1only]"""
import os, sys, time, json
os.environ.setdefault("KUHN_CARDS", "5")
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
from fractions import Fraction as F
from fullprop35 import region
from fullprop35v2 import AGENTS, terms, classes, random_face, allowed

P1ONLY = len(sys.argv) > 5 and sys.argv[5] == "P1only"


def noninteracting(n):
    pl, c = AGENTS[n]
    out = [m for m, (q, d) in enumerate(AGENTS) if m != n and (q == pl or d == c)]
    if P1ONLY: out = [m for m in out if AGENTS[m][0] == 0]
    return out


class Rel:
    def __init__(self, faces, brs):
        self.brs = brs
        self.cls = classes(faces)
        # class index per agent: rep plan -> 0..C-1
        self.cid = []; self.C = []
        for n in range(15):
            reps = sorted(set(int(r) for r in self.cls[n] if r >= 0))
            m = -np.ones(16, int)
            for p in range(16):
                if self.cls[n][p] >= 0: m[p] = reps.index(int(self.cls[n][p]))
            self.cid.append(m); self.C.append(len(reps))
        # base columns: 240 CCE + 16 per BR block; owner agent of each base column
        self.owner = [n for n in range(15) for _ in range(16)]
        for a in AGENTS:
            for (b, rho) in brs:
                if b == a: self.owner += [AGENTS.index(a)] * 16
        self.nbase = len(self.owner)
        # product columns: (base column, partner agent b, class of b)
        self.pcols = []; self.pindex = {}
        for col, n in enumerate(self.owner):
            for b in noninteracting(n):
                for c in range(self.C[b]):
                    self.pindex[(col, b, c)] = self.nbase + len(self.pcols); self.pcols.append((col, b, c))
        self.ncol = self.nbase + len(self.pcols)

    def base(self, Pl):
        D, G = terms(Pl, self.brs)
        return np.hstack([D, G])

    def rows(self, Pl):
        """sparse rows: base columns + the active product columns"""
        Bm = self.base(Pl); Bn = len(Pl)
        ci = np.stack([self.cid[n][Pl[:, n]] for n in range(15)], axis=1)        # (B, 15)
        r_, c_, v_ = [], [], []
        for col, n in enumerate(self.owner):
            r_.append(np.arange(Bn)); c_.append(np.full(Bn, col)); v_.append(Bm[:, col])
            for b in noninteracting(n):
                idx = np.array([self.pindex[(col, b, c)] for c in range(self.C[b])])
                r_.append(np.arange(Bn)); c_.append(idx[ci[:, b]]); v_.append(Bm[:, col])
        r = np.concatenate(r_); c = np.concatenate(c_); v = np.concatenate(v_)
        keep = v != 0
        return sp.csr_matrix((v[keep], (r[keep], c[keep])), shape=(Bn, self.ncol))

    def value(self, Pl, w):
        return np.asarray(self.rows(Pl) @ w).ravel()


def solve_lp(M):
    n, m = M.shape
    c = np.zeros(m + 1); c[-1] = 1
    A = sp.hstack([M, -sp.csr_matrix(np.ones((n, 1)))]).tocsr()
    Aeq = sp.csr_matrix(np.hstack([np.ones(m), [0.0]])[None, :])
    res = linprog(c, A_ub=A, b_ub=np.zeros(n), A_eq=Aeq, b_eq=[1], bounds=[(0, None)] * m + [(None, None)], method="highs")
    return res.x[:m], res.x[-1]


def local_search(R, w, faces, rng, starts=32, iters=200):
    al = allowed(faces)
    Pl = random_face(starts, faces, rng)
    cur = R.value(Pl, w)
    moves = [(i, t) for i in range(15) for t in al[i]]
    for _ in range(iters):
        Nb = np.repeat(Pl, len(moves), 0)
        ii = np.tile(np.array([m[0] for m in moves]), starts); tt = np.tile(np.array([m[1] for m in moves]), starts)
        Nb[np.arange(len(Nb)), ii] = tt
        val = R.value(Nb, w).reshape(starts, len(moves))
        best = val.argmax(1); bv = val.max(1)
        imp = bv > cur + 1e-12
        if not imp.any(): break
        for s in np.flatnonzero(imp):
            i, t = moves[best[s]]; Pl[s, i] = t; cur[s] = bv[s]
    return Pl, cur


if __name__ == "__main__":
    name = sys.argv[1]; out = sys.argv[2]
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    starts = int(sys.argv[4]) if len(sys.argv) > 4 else 32
    faces, brs = region(name)
    R = Rel(faces, brs)
    print("region %s: %d base columns, %d product columns%s" % (name, R.nbase, len(R.pcols), " (P1 partners only)" if P1ONLY else ""), flush=True)
    rng = np.random.default_rng(0)
    rows = [R.rows(random_face(3000, faces, rng))]
    t0 = time.time()
    for r in range(rounds):
        M = sp.vstack(rows).tocsr()
        w, s = solve_lp(M)
        Pl, cur = local_search(R, w, faces, rng, starts)
        print("round %3d: LP value %.6f over %d profiles; separation max %.6f; nonzero %d  (%.0fs)" % (
            r, s, M.shape[0], cur.max(), (w > 1e-9).sum(), time.time() - t0), flush=True)
        new = cur > s + 1e-9
        if not new.any():
            print("local search finds nothing above the LP value %.6f (%s)" % (
                s, "candidate emptiness certificate" if s < 0 else "NO certificate: value >= 0"), flush=True)
            break
        rows.append(R.rows(Pl[new]))
    q = lambda x: str(F(int(round(x * 10 ** 6)), 10 ** 6))
    nz = [i for i in range(R.ncol) if round(w[i] * 10 ** 6) > 0]
    cert = {"region": name, "faces": {"%d,%d" % a: v for a, v in faces.items()},
            "brs": [[a[0], a[1], rho] for a, rho in brs], "lp_value": float(s), "proposer": "fullprop35p.py",
            "base": [[i, q(w[i])] for i in nz if i < R.nbase],
            "prod": [[R.pcols[i - R.nbase][0], AGENTS[R.pcols[i - R.nbase][1]][0], AGENTS[R.pcols[i - R.nbase][1]][1],
                      R.pcols[i - R.nbase][2], q(w[i])] for i in nz if i >= R.nbase]}
    json.dump(cert, open(out, "w"), indent=0)
    print("wrote", out)
