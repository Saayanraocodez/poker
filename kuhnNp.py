"""
Three-player Kuhn poker on an N-card deck, exact.

The betting tree does not depend on N -- it always has the same 13 terminal
histories -- so only the deal set and the parameter count grow:

    deals   = N(N-1)(N-2)          leaves = 13 * deals
    params  = 12N                  kappa  = 1 / deals

The parameter index is  player*(4N) + (card-1)*4 + (situation-1),  which at
N = 4 coincides exactly with kuhn3p's 48-vector layout.  `selfcheck()` uses
that to require bit-for-bit agreement with the validated 4-card engine.

Situations (SGS Table 1):
    k=1: P1 root      | P2 after K     | P3 after KK
    k=2: P1 after KKB | P2 after B     | P3 after KB
    k=3: P1 after KBF | P2 after KKBF  | P3 after BF
    k=4: P1 after KBC | P2 after KKBC  | P3 after BC
"""
import itertools
from fractions import Fraction as Fr

import numpy as np

NODE = {
    "": (0, 1), "B": (1, 2), "BF": (2, 3), "BC": (2, 4),
    "K": (1, 1), "KB": (2, 2), "KBF": (0, 3), "KBC": (0, 4),
    "KK": (2, 1), "KKB": (0, 2), "KKBF": (1, 3), "KKBC": (1, 4),
}
OPEN = {"", "K", "KK"}
TERMINAL = {"BFF", "BFC", "BCF", "BCC",
            "KBFF", "KBFC", "KBCF", "KBCC",
            "KKK", "KKBFF", "KKBFC", "KKBCF", "KKBCC"}
MAXF = 5                                    # longest decision path: KKBFF


def actions(hist):
    return ("K", "B") if hist in OPEN else ("F", "C")


def payoff(cards, hist):
    contrib = [1, 1, 1]
    folded = [False, False, False]
    h = ""
    for ch in hist:
        pl, _ = NODE[h]
        if ch in "BC":
            contrib[pl] += 1
        elif ch == "F":
            folded[pl] = True
        h += ch
    pot = sum(contrib)
    live = [i for i in range(3) if not folded[i]]
    w = max(live, key=lambda i: cards[i])
    pay = [-contrib[i] for i in range(3)]
    pay[w] += pot
    return pay


class KuhnN:
    def __init__(self, N):
        self.N = N
        self.cards = tuple(range(1, N + 1))
        self.deals = list(itertools.permutations(self.cards, 3))
        self.ndeal = len(self.deals)
        self.nparam = 12 * N
        self.dummy = self.nparam
        self.kappa = 1.0 / self.ndeal
        self.kappa_f = Fr(1, self.ndeal)
        self._build()

    # ---- indexing ---------------------------------------------------------
    def pidx(self, player, card, sit):
        return player * (4 * self.N) + (card - 1) * 4 + (sit - 1)

    def name(self, i):
        pl, r = divmod(i, 4 * self.N)
        card, sit = divmod(r, 4)
        return "%s%d_%d" % ("abc"[pl], card + 1, sit + 1)

    # ---- leaf table -------------------------------------------------------
    def _leaves(self, cards):
        out = []

        def rec(h, fac):
            if h in TERMINAL:
                out.append((fac, payoff(cards, h)))
                return
            pl, sit = NODE[h]
            i = self.pidx(pl, cards[pl], sit)
            pas, agg = actions(h)
            rec(h + pas, fac + [(i, False)])
            rec(h + agg, fac + [(i, True)])

        rec("", [])
        return out

    def _build(self):
        idx, agg, pay, hold = [], [], [], []
        for d in self.deals:
            for fac, p in self._leaves(d):
                k = len(fac)
                idx.append([f[0] for f in fac] + [self.dummy] * (MAXF - k))
                agg.append([f[1] for f in fac] + [True] * (MAXF - k))
                pay.append(p)
                hold.append(d)
        self.IDX = np.array(idx)
        self.AGG = np.array(agg)
        self.PAY = np.array(pay, float)
        self.HOLD = np.array(hold)
        self.nleaf = len(idx)
        self._sub = {}
        for pl in range(3):
            for j in self.cards:
                m = self.HOLD[:, pl] == j
                self._sub[(pl, j)] = (self.IDX[m], self.AGG[m], self.PAY[m][:, pl])

    # ---- utilities --------------------------------------------------------
    def utilities(self, p):
        q = np.empty(self.nparam + 1)
        q[:self.nparam] = p
        q[self.dummy] = 1.0
        w = np.where(self.AGG, q[self.IDX], 1.0 - q[self.IDX]).prod(axis=1)
        return self.kappa * (w[:, None] * self.PAY).sum(axis=0)

    def utilities_exact(self, p):
        q = list(p) + [Fr(1)]
        tot = [Fr(0), Fr(0), Fr(0)]
        for r in range(self.nleaf):
            w = Fr(1)
            for k in range(MAXF):
                i = int(self.IDX[r, k])
                w *= q[i] if self.AGG[r, k] else (1 - q[i])
            if w:
                for t in range(3):
                    tot[t] += w * int(self.PAY[r, t])
        return tuple(self.kappa_f * t for t in tot)

    def dcoord(self, p, i):
        """Exact du/dp_i = u(p_i=1) - u(p_i=0); valid because u is multilinear."""
        a, b = np.array(p, float), np.array(p, float)
        a[i], b[i] = 1.0, 0.0
        return self.utilities(a) - self.utilities(b)

    def gradient(self, p):
        """(nparam, 3) exact du_i/dp_y in one pass."""
        q = np.empty(self.nparam + 1)
        q[:self.nparam] = p
        q[self.dummy] = 1.0
        f = np.where(self.AGG, q[self.IDX], 1.0 - q[self.IDX])
        out = np.zeros((self.nparam + 1, 3))
        for k in range(MAXF):
            pref = np.ones(self.nleaf)
            for m in range(MAXF):
                if m != k:
                    pref *= f[:, m]
            sign = np.where(self.AGG[:, k], 1.0, -1.0)
            np.add.at(out, self.IDX[:, k],
                      (self.kappa * sign * pref)[:, None] * self.PAY)
        return out[:self.nparam]


    def dcoord_exact(self, p, i):
        a, b = list(p), list(p)
        a[i], b[i] = Fr(1), Fr(0)
        ua, ub = self.utilities_exact(a), self.utilities_exact(b)
        return tuple(x - y for x, y in zip(ua, ub))

    # ---- best response ----------------------------------------------------
    def best_response(self, p, player):
        q = np.empty(self.nparam + 1)
        q[:self.nparam] = p
        q[self.dummy] = 1.0
        tot = 0.0
        for j in self.cards:
            si, sa, sp = self._sub[(player, j)]
            own = [self.pidx(player, j, k) for k in (1, 2, 3, 4)]
            best = None
            for bits in itertools.product((0.0, 1.0), repeat=4):
                qq = q.copy()
                for i, b in zip(own, bits):
                    qq[i] = b
                v = self.kappa * float(
                    (np.where(sa, qq[si], 1.0 - qq[si]).prod(axis=1) * sp).sum())
                if best is None or v > best:
                    best = v
            tot += best
        return tot

    def exploitability(self, p):
        u = self.utilities(p)
        return np.array([self.best_response(p, i) - u[i] for i in range(3)])

    def reach(self, p):
        """Reach probability of every parameter's information set."""
        q = np.empty(self.nparam + 1)
        q[:self.nparam] = p
        q[self.dummy] = 1.0
        f = np.where(self.AGG, q[self.IDX], 1.0 - q[self.IDX])
        out = np.zeros(self.nparam + 1)
        for k in range(MAXF):
            pref = np.ones(self.nleaf)
            for m in range(MAXF):
                if m != k:
                    pref *= f[:, m]
            np.add.at(out, self.IDX[:, k], self.kappa * pref)
        return out[:self.nparam] / 2.0      # every node has exactly 2 actions


# ===========================================================================
def selfcheck(N=4, trials=100, seed=0):
    """At N=4 the layout matches kuhn3p exactly, so demand identical output."""
    import kuhn3p as K
    g = KuhnN(4)
    rng = np.random.default_rng(seed)
    du = dg = de = dr = 0.0
    for _ in range(trials):
        p = rng.random(48)
        du = max(du, float(np.abs(g.utilities(p) - K.utilities(p)).max()))
        de = max(de, float(np.abs(g.exploitability(p) - K.exploitability(p)).max()))
        dr = max(dr, float(np.abs(g.reach(p) - K.reach(p)).max()))
        i = int(rng.integers(48))
        dg = max(dg, float(np.abs(g.dcoord(p, i)
                                  - K.exact_coord_derivative(p, i)).max()))
    return dict(utilities=du, gradient=dg, exploitability=de, reach=dr,
                nleaf=g.nleaf, kuhn3p_nleaf=312)


def sizes(Ns=(4, 5, 6, 7, 8, 10, 12)):
    return [(N, N * (N - 1) * (N - 2), 13 * N * (N - 1) * (N - 2), 12 * N) for N in Ns]
