"""
n-player, N-card Kuhn poker, exact.

Betting rule (the natural generalization of the 3-player game):
  players 0..n-1 act in order; with no bet outstanding an actor checks (K) or
  bets (B).  As soon as somebody bets, every OTHER player -- including those who
  already checked -- answers fold (F) or call (C), in order, wrapping around.
  If all n check, showdown.  One betting round, no raises, bet = call = 1 chip.

  leaves per deal = n * 2^(n-1) + 1        (13 for n=3, 33 for n=4)
  deals           = N!/(N-n)!
  information sets: a player's situation is just the public history at their
  turn, so situations are enumerated per player from the tree itself.

At n = 3 this reproduces SGS's tree exactly; `selfcheck` maps histories onto
their k=1..4 situation labels and demands identical utilities.
"""
import itertools
from fractions import Fraction as Fr

import numpy as np

# n=3 history -> SGS situation index, used only for cross-validation
SGS_SIT = {
    0: {"": 1, "KKB": 2, "KBF": 3, "KBC": 4},
    1: {"K": 1, "B": 2, "KKBF": 3, "KKBC": 4},
    2: {"KK": 1, "KB": 2, "BF": 3, "BC": 4},
}


class Kuhn:
    def __init__(self, nplayer, ncard):
        assert 2 <= nplayer <= ncard
        self.nplayer = nplayer
        self.ncard = ncard
        self.cards = tuple(range(1, ncard + 1))
        self.deals = list(itertools.permutations(self.cards, nplayer))
        self.ndeal = len(self.deals)
        self.maxf = 2 * nplayer - 1
        self.kappa = 1.0 / self.ndeal
        self.kappa_f = Fr(1, self.ndeal)
        self._situations()
        self._build()

    # ---- tree navigation --------------------------------------------------
    def state(self, hist):
        """(terminal?, actor, bet_outstanding?)"""
        n = self.nplayer
        bettor = None
        for k, ch in enumerate(hist):
            if bettor is None:
                if ch == "B":
                    bettor = k
            # actions after the bet are responses; nothing to track but count
        if bettor is None:
            if len(hist) == n:
                return True, None, False
            return False, len(hist), False
        nresp = len(hist) - bettor - 1
        if nresp == n - 1:
            return True, None, True
        return False, (bettor + 1 + nresp) % n, True

    def actions(self, hist):
        _, _, bet = self.state(hist)
        return ("F", "C") if bet else ("K", "B")

    def _histories(self):
        out = []
        stack = [""]
        while stack:
            h = stack.pop()
            term, actor, _ = self.state(h)
            if term:
                out.append((h, None))
                continue
            out.append((h, actor))
            pas, agg = self.actions(h)
            stack.append(h + pas)
            stack.append(h + agg)
        return out

    def _situations(self):
        self.sit = {}                      # (player, hist) -> situation index
        self.sit_hist = {}                 # player -> [hist, ...]
        hs = [(h, a) for h, a in self._histories() if a is not None]
        for pl in range(self.nplayer):
            mine = sorted({h for h, a in hs if a == pl}, key=lambda s: (len(s), s))
            self.sit_hist[pl] = mine
            for k, h in enumerate(mine):
                self.sit[(pl, h)] = k
        self.nsit = {pl: len(v) for pl, v in self.sit_hist.items()}
        self.offset = {}
        off = 0
        for pl in range(self.nplayer):
            self.offset[pl] = off
            off += self.ncard * self.nsit[pl]
        self.nparam = off
        self.dummy = self.nparam

    def pidx(self, player, card, hist):
        return (self.offset[player] + (card - 1) * self.nsit[player]
                + self.sit[(player, hist)])

    def name(self, i):
        for pl in range(self.nplayer):
            lo = self.offset[pl]
            hi = lo + self.ncard * self.nsit[pl]
            if lo <= i < hi:
                r = i - lo
                card, s = divmod(r, self.nsit[pl])
                h = self.sit_hist[pl][s]
                return "%s%d[%s]" % ("abcdefgh"[pl], card + 1, h if h else "-")
        return "?"

    # ---- payoffs ----------------------------------------------------------
    def payoff(self, cards, hist):
        n = self.nplayer
        contrib = [1] * n
        folded = [False] * n
        h = ""
        for ch in hist:
            _, actor, _ = self.state(h)
            if ch in "BC":
                contrib[actor] += 1
            elif ch == "F":
                folded[actor] = True
            h += ch
        pot = sum(contrib)
        live = [i for i in range(n) if not folded[i]]
        w = max(live, key=lambda i: cards[i])
        pay = [-contrib[i] for i in range(n)]
        pay[w] += pot
        return pay

    def _leaves(self, cards):
        out = []

        def rec(h, fac):
            term, actor, _ = self.state(h)
            if term:
                out.append((fac, self.payoff(cards, h)))
                return
            i = self.pidx(actor, cards[actor], h)
            pas, agg = self.actions(h)
            rec(h + pas, fac + [(i, False)])
            rec(h + agg, fac + [(i, True)])

        rec("", [])
        return out

    def _build(self):
        idx, agg, pay, hold = [], [], [], []
        for d in self.deals:
            for fac, p in self._leaves(d):
                k = len(fac)
                idx.append([f[0] for f in fac] + [self.dummy] * (self.maxf - k))
                agg.append([f[1] for f in fac] + [True] * (self.maxf - k))
                pay.append(p)
                hold.append(d)
        self.IDX = np.array(idx, np.int32)
        self.AGG = np.array(agg, bool)
        self.PAY = np.array(pay, np.int8)
        self.HOLD = np.array(hold, np.int8)
        self.nleaf = len(idx)
        self._subcache = {}

    def sub(self, pl, j):
        """Lazily built per-(player,card) slice; caching all of them at once
        duplicates the entire leaf table once per player."""
        key = (pl, j)
        if key not in self._subcache:
            m = self.HOLD[:, pl] == j
            self._subcache[key] = (self.IDX[m], self.AGG[m],
                                   self.PAY[m][:, pl].astype(np.float64))
        return self._subcache[key]

    # ---- utilities --------------------------------------------------------
    def utilities(self, p):
        q = np.empty(self.nparam + 1)
        q[:self.nparam] = p
        q[self.dummy] = 1.0
        w = np.where(self.AGG, q[self.IDX], 1.0 - q[self.IDX]).prod(axis=1)
        return self.kappa * (w @ self.PAY)      # matvec: no nleaf x n temporary

    def dcoord(self, p, i):
        a, b = np.array(p, float), np.array(p, float)
        a[i], b[i] = 1.0, 0.0
        return self.utilities(a) - self.utilities(b)

    def best_response(self, p, player):
        q = np.empty(self.nparam + 1)
        q[:self.nparam] = p
        q[self.dummy] = 1.0
        ns = self.nsit[player]
        tot = 0.0
        for j in self.cards:
            si, sa, sp = self.sub(player, j)
            own = [self.offset[player] + (j - 1) * ns + s for s in range(ns)]
            best = None
            for bits in itertools.product((0.0, 1.0), repeat=ns):
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
        return np.array([self.best_response(p, i) - u[i]
                         for i in range(self.nplayer)])

    # ---- vectorised gradient ---------------------------------------------
    def _prodskip(self, f):
        """Yield (k, product of all factors except column k) without the
        O(maxf^2) recomputation, and without an nleaf x maxf second buffer."""
        suf = np.empty_like(f)
        suf[:, -1] = 1.0
        for k in range(self.maxf - 2, -1, -1):
            suf[:, k] = suf[:, k + 1] * f[:, k + 1]
        pre = np.ones(self.nleaf)
        for k in range(self.maxf):
            yield k, pre * suf[:, k]
            pre = pre * f[:, k]

    def gradient(self, p):
        """(nparam, nplayer) matrix of exact du_i/dp_y, in one pass."""
        q = np.empty(self.nparam + 1)
        q[:self.nparam] = p
        q[self.dummy] = 1.0
        f = np.where(self.AGG, q[self.IDX], 1.0 - q[self.IDX])
        out = np.zeros((self.nparam + 1, self.nplayer))
        for k, pref in self._prodskip(f):
            coef = (self.kappa * np.where(self.AGG[:, k], 1.0, -1.0)) * pref
            col = self.IDX[:, k]
            for t in range(self.nplayer):
                out[:, t] += np.bincount(col, weights=coef * self.PAY[:, t],
                                         minlength=self.nparam + 1)
        return out[:self.nparam]

    # ---- best response by backward induction ------------------------------
    def best_response_bi(self, p, player):
        """O(tree) best response: aggregate counterfactual values per info set."""
        q = np.empty(self.nparam + 1)
        q[:self.nparam] = p
        q[self.dummy] = 1.0
        nodes = {}
        for d, cards in enumerate(self.deals):
            stack = [("", 1.0)]
            while stack:
                h, w = stack.pop()
                term, actor, _ = self.state(h)
                nodes[(d, h)] = w
                if term:
                    continue
                i = self.pidx(actor, cards[actor], h)
                pas, agg = self.actions(h)
                if actor == player:
                    stack.append((h + pas, w))
                    stack.append((h + agg, w))
                else:
                    stack.append((h + pas, w * (1.0 - q[i])))
                    stack.append((h + agg, w * q[i]))
        V = {}
        byd = {}
        for (d, h) in nodes:
            byd.setdefault(len(h), []).append((d, h))
        for L in sorted(byd, reverse=True):
            iset = {}
            for d, h in byd[L]:
                cards = self.deals[d]
                term, actor, _ = self.state(h)
                if term:
                    V[(d, h)] = self.payoff(cards, h)[player]
                    continue
                i = self.pidx(actor, cards[actor], h)
                pas, agg = self.actions(h)
                if actor == player:
                    iset.setdefault(i, []).append((d, h, pas, agg))
                else:
                    V[(d, h)] = ((1.0 - q[i]) * V[(d, h + pas)]
                                 + q[i] * V[(d, h + agg)])
            for i, mem in iset.items():
                v0 = sum(nodes[(d, h)] * V[(d, h + pas)] for d, h, pas, agg in mem)
                v1 = sum(nodes[(d, h)] * V[(d, h + agg)] for d, h, pas, agg in mem)
                best = agg if v1 >= v0 else pas
                for d, h, pas, agg in mem:
                    V[(d, h)] = V[(d, h + (agg if v1 >= v0 else pas))]
        return self.kappa * sum(V[(d, "")] for d in range(self.ndeal))

    def exploitability_bi(self, p):
        u = self.utilities(p)
        return np.array([self.best_response_bi(p, i) - u[i]
                         for i in range(self.nplayer)])

    def reach(self, p):
        q = np.empty(self.nparam + 1)
        q[:self.nparam] = p
        q[self.dummy] = 1.0
        f = np.where(self.AGG, q[self.IDX], 1.0 - q[self.IDX])
        out = np.zeros(self.nparam + 1)
        for k, pref in self._prodskip(f):
            out += np.bincount(self.IDX[:, k], weights=self.kappa * pref,
                               minlength=self.nparam + 1)
        return out[:self.nparam] / 2.0


# ===========================================================================
def selfcheck(N=5, trials=60, seed=0):
    """n=3 must reproduce kuhnNp exactly, once situations are relabelled."""
    import kuhnNp as G
    g2, g1 = Kuhn(3, N), G.KuhnN(N)
    perm = np.empty(g1.nparam, int)
    for pl in range(3):
        for j in range(1, N + 1):
            for h, k in SGS_SIT[pl].items():
                perm[g1.pidx(pl, j, k)] = g2.pidx(pl, j, h)
    rng = np.random.default_rng(seed)
    du = de = dr = 0.0
    for _ in range(trials):
        p1 = rng.random(g1.nparam)
        p2 = np.empty(g2.nparam)
        p2[perm] = p1
        du = max(du, float(np.abs(g2.utilities(p2) - g1.utilities(p1)).max()))
        de = max(de, float(np.abs(g2.exploitability(p2) - g1.exploitability(p1)).max()))
        dr = max(dr, float(np.abs(g2.reach(p2)[perm] - g1.reach(p1)).max()))
    return dict(utilities=du, exploitability=de, reach=dr,
                nleaf=g2.nleaf, ref_nleaf=g1.nleaf, nparam=g2.nparam)
