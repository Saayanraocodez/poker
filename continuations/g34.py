"""Three-player four-card Kuhn poker with a general ante A (bet = 1), vectorised over the 24 deals.

Shared by the continuation experiments (2026-11-16):
  * util / D, R (own-reach-stripped gradient and the opponents' reach of every information set);
  * full-width CFR+ on a PERTURBED game (every action has probability at least a floor);
  * exact-in-float best responses, also restricted to the floors.
Built from the rules in independent_check/indep.py (not from tree.py); A = 1 is the standard game and
is checked against indep at import.  Coordinates: the 48-vector a11..a44, b11..b44, c11..c44.
"""
import os, sys, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'independent_check'))
import indep as I

NAMES = I.NAMES; IX = {n: i for i, n in enumerate(NAMES)}
DEALS = I.deals(4); ND = len(DEALS)
PLAYER_OF = np.arange(48) // 16

# ---- the tree as arrays: positions = histories
HIST = []
def _rec(h):
    HIST.append(h)
    if I.actor(h) is not None:
        _rec(h + I.aggressive(h)); _rec(h + I.passive(h))
_rec('')
POS = {h: k for k, h in enumerate(HIST)}
NPOS = len(HIST)
INT = [k for k, h in enumerate(HIST) if I.actor(h) is not None]          # parents before children
LEAF = [k for k, h in enumerate(HIST) if I.actor(h) is None]
OWN = np.array([I.actor(h) if I.actor(h) is not None else -1 for h in HIST])
AGG = np.array([POS[h + I.aggressive(h)] if I.actor(h) is not None else -1 for h in HIST])
PAS = np.array([POS[h + I.passive(h)] if I.actor(h) is not None else -1 for h in HIST])
CO = -np.ones((ND, NPOS), dtype=np.int64)
for d, cards in enumerate(DEALS):
    for k in INT:
        pl = OWN[k]; CO[d, k] = IX[I.name_at(pl, cards[pl], HIST[k])]


def payoffs(A=1.0):
    """(ND, NPOS, 3) terminal payoffs with ante A and bet 1."""
    P = np.zeros((ND, NPOS, 3))
    for d, cards in enumerate(DEALS):
        for k in LEAF:
            h = HIST[k]
            contrib = [A, A, A]; folded = [False] * 3
            if 'B' in h:
                ib = h.index('B'); contrib[ib] += 1
                for t, act in enumerate(h[ib + 1:]):
                    pl = (ib + 1 + t) % 3
                    if act == 'C': contrib[pl] += 1
                    else: folded[pl] = True
            w = max((i for i in range(3) if not folded[i]), key=lambda i: cards[i])
            for i in range(3): P[d, k, i] = -contrib[i]
            P[d, k, w] += sum(contrib)
    return P


class Game:
    def __init__(self, A=1.0):
        self.A = A; self.PAY = payoffs(A)

    def sweep(self, x):
        Rp = np.ones((ND, NPOS, 3))
        for k in INT:
            s = x[CO[:, k]]; i = OWN[k]
            Rp[:, AGG[k]] = Rp[:, k]; Rp[:, PAS[k]] = Rp[:, k]
            Rp[:, AGG[k], i] *= s; Rp[:, PAS[k], i] *= 1 - s
        V = np.zeros((ND, NPOS, 3)); V[:, LEAF] = self.PAY[:, LEAF]
        for k in INT[::-1]:
            s = x[CO[:, k]][:, None]
            V[:, k] = s * V[:, AGG[k]] + (1 - s) * V[:, PAS[k]]
        return Rp, V

    def util(self, x):
        return self.sweep(x)[1][:, 0].mean(axis=0)

    def DR(self, x):
        """D (48,), R (48,): stripped gradient and opponents' x chance reach of each information set."""
        Rp, V = self.sweep(x)
        D = np.zeros(48); R = np.zeros(48)
        for k in INT:
            i = OWN[k]
            cf = np.prod(np.delete(Rp[:, k], i, axis=1), axis=1) / ND
            np.add.at(D, CO[:, k], cf * (V[:, AGG[k], i] - V[:, PAS[k], i]))
            np.add.at(R, CO[:, k], cf)
        return D, R

    def br(self, x, i, lo=None, hi=None):
        """best-response value of player i against x; with floors, restricted to x_j in {lo_j, hi_j}."""
        lo = np.zeros(48) if lo is None else lo; hi = np.ones(48) if hi is None else hi
        tot = 0.0
        for card in range(1, 5):
            own = [IX['abc'[i] + str(card) + str(s)] for s in range(1, 5)]
            best = -1e18
            dl = np.array([d for d, c in enumerate(DEALS) if c[i] == card])
            for bits in itertools.product((0, 1), repeat=4):
                y = x.copy()
                for j, b in zip(own, bits): y[j] = hi[j] if b else lo[j]
                best = max(best, self._util_deals(y, dl, i))
            tot += best
        return tot

    def _util_deals(self, x, dl, i):
        V = {k: self.PAY[dl, k, i] for k in LEAF}
        for k in INT[::-1]:
            s = x[CO[dl, k]]
            V[k] = s * V[AGG[k]] + (1 - s) * V[PAS[k]]
        return V[0].sum() / ND

    def expl(self, x, lo=None, hi=None):
        u = self.util(x)
        return np.array([self.br(x, i, lo, hi) - u[i] for i in range(3)])

    def cfrplus(self, iters, lo=None, hi=None, seed=0, R0=None, S0=None, t0=0):
        """CFR+ (alternating, RM+, linear averaging) on the game restricted to x in [lo, hi]:
        each information set chooses between the two extreme mixtures lo_j and hi_j."""
        lo = np.zeros(48) if lo is None else lo; hi = np.ones(48) if hi is None else hi
        rng = np.random.default_rng(seed)
        R = np.zeros((48, 2)) if R0 is None else R0.copy(); S = np.zeros((48, 2)) if S0 is None else S0.copy()
        if seed and R0 is None: R += np.abs(rng.normal(0.0, 0.05, size=(48, 2)))
        for t in range(t0 + 1, t0 + iters + 1):
            for i in (0, 1, 2):
                Rpos = np.maximum(R, 0.0); s = Rpos.sum(axis=1)
                sig = np.where(s > 0, Rpos[:, 1] / np.where(s > 0, s, 1), 0.5)
                x = lo + (hi - lo) * sig
                Rp, V = self.sweep(x)
                m = PLAYER_OF == i
                r = np.zeros((48, 2)); ss = np.zeros((48, 2))
                for k in INT:
                    if OWN[k] != i: continue
                    cf = np.prod(np.delete(Rp[:, k], i, axis=1), axis=1) / ND
                    va, vp, v0 = V[:, AGG[k], i], V[:, PAS[k], i], V[:, k, i]
                    c = CO[:, k]
                    vhi = hi[c] * va + (1 - hi[c]) * vp; vlo = lo[c] * va + (1 - lo[c]) * vp
                    np.add.at(r[:, 1], c, cf * (vhi - v0)); np.add.at(r[:, 0], c, cf * (vlo - v0))
                    own = Rp[:, k, i]
                    np.add.at(ss[:, 1], c, own * sig[c]); np.add.at(ss[:, 0], c, own * (1 - sig[c]))
                R[m] = np.maximum(R[m] + r[m], 0.0)
                S[m] += t * ss[m]
        tot = S.sum(axis=1)
        sig = np.where(tot > 0, S[:, 1] / np.where(tot > 0, tot, 1), 0.5)
        return lo + (hi - lo) * sig, R, S


# ---- self-check at A = 1 against the independent exact engine
def _selfcheck():
    from fractions import Fraction as F
    import random
    rnd = random.Random(1); g = Game(1.0)
    for _ in range(3):
        v = [F(rnd.randint(0, 20), 20) for _ in range(48)]
        p = I.from_vec(v); x = np.array([float(t) for t in v])
        assert np.allclose(g.util(x), [float(t) for t in I.utilities(p)], atol=1e-13)
        D, R = I.D_all(p); d, r = g.DR(x)
        assert np.allclose(d, [float(D[n]) for n in NAMES], atol=1e-13) and np.allclose(r, [float(R[n]) for n in NAMES], atol=1e-13)
        assert np.allclose(g.expl(x), [float(t) for t in I.exploitability(p)], atol=1e-12)
_selfcheck()
