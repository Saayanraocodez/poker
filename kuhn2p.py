"""
TWO-PLAYER Kuhn poker as a CONTROL for the 3-player rho analysis.

3-card deck {1,2,3}, both ante 1, 6 deals at probability 1/6 each.
P1 checks(K) or bets(B).  If P1 bets, P2 folds or calls.  If P1 checks, P2 checks
(showdown) or bets, and then P1 folds or calls.  Highest unfolded card wins the pot.

Parameters (12): x_{j,1} = P1 bets card j at the root; x_{j,2} = P1 calls card j after
K-B; y_{j,1} = P2 bets card j after P1 checks; y_{j,2} = P2 calls card j after P1 bets.

Known equilibrium family, one free parameter alpha in [0, 1/3]:
    x_{1,1}=alpha   x_{2,1}=0          x_{3,1}=3*alpha
    x_{1,2}=0       x_{2,2}=alpha+1/3  x_{3,2}=1
    y_{1,1}=1/3     y_{2,1}=0          y_{3,1}=1
    y_{1,2}=0       y_{2,2}=1/3        y_{3,2}=1
"""
import itertools
from fractions import Fraction as Fr

import numpy as np

CARDS = (1, 2, 3)
NP2 = 12
DUM = NP2
K6 = 1.0 / 6.0


def q(player, card, sit):
    return player * 6 + (card - 1) * 2 + (sit - 1)


NAME = {}
for _pl, _ch in enumerate("xy"):
    for _j in CARDS:
        for _k in (1, 2):
            NAME[q(_pl, _j, _k)] = "%s%d%d" % (_ch, _j, _k)
IDX_OF = {v: k for k, v in NAME.items()}


def _pay(cards, contrib, folded):
    pot = sum(contrib)
    live = [i for i in range(2) if not folded[i]]
    w = max(live, key=lambda i: cards[i])
    p = [-contrib[i] for i in range(2)]
    p[w] += pot
    return tuple(p)


def _leaves(cards):
    c1, c2 = cards
    out = []
    for b1 in (0, 1):                                  # P1 root
        f1 = (q(0, c1, 1), bool(b1))
        if b1:                                         # P1 bet
            for c_ in (0, 1):                          # P2 fold/call
                f2 = (q(1, c2, 2), bool(c_))
                contrib = [2, 2 if c_ else 1]
                out.append(([f1, f2], _pay(cards, contrib, [False, not c_])))
        else:
            for b2 in (0, 1):                          # P2 check/bet
                f2 = (q(1, c2, 1), bool(b2))
                if b2:
                    for c_ in (0, 1):                  # P1 fold/call
                        f3 = (q(0, c1, 2), bool(c_))
                        contrib = [2 if c_ else 1, 2]
                        out.append(([f1, f2, f3],
                                    _pay(cards, contrib, [not c_, False])))
                else:
                    out.append(([f1, f2], _pay(cards, [1, 1], [False, False])))
    return out


DEALS = list(itertools.permutations(CARDS, 2))
_idx, _agg, _pay_, _hold = [], [], [], []
for d in DEALS:
    for fs, p in _leaves(d):
        _idx.append([f[0] for f in fs] + [DUM] * (3 - len(fs)))
        _agg.append([f[1] for f in fs] + [True] * (3 - len(fs)))
        _pay_.append(p)
        _hold.append(d)
IDX = np.array(_idx)
AGG = np.array(_agg)
PAY = np.array(_pay_, float)
HOLD = np.array(_hold)
NLEAF = len(IDX)


def utilities(p):
    v = np.empty(NP2 + 1)
    v[:NP2] = p
    v[DUM] = 1.0
    w = np.where(AGG, v[IDX], 1 - v[IDX]).prod(axis=1)
    return K6 * (w[:, None] * PAY).sum(axis=0)


def utilities_exact(p):
    v = list(p) + [Fr(1)]
    tot = [Fr(0), Fr(0)]
    for r in range(NLEAF):
        w = Fr(1)
        for k in range(3):
            i = int(IDX[r, k])
            w *= v[i] if AGG[r, k] else (1 - v[i])
        for t in (0, 1):
            tot[t] += w * int(PAY[r, t])
    return tuple(Fr(1, 6) * t for t in tot)


def exact_coord_derivative(p, i):
    a, b = p.copy(), p.copy()
    a[i], b[i] = 1.0, 0.0
    return utilities(a) - utilities(b)


def central_diff(p, i, h=1e-5):
    a, b = p.copy(), p.copy()
    a[i] += h
    b[i] -= h
    return (utilities(a) - utilities(b)) / (2 * h)


_MASK = {(pl, j): (HOLD[:, pl] == j) for pl in (0, 1) for j in CARDS}


def best_response_value(p, player):
    v = np.empty(NP2 + 1)
    v[:NP2] = p
    v[DUM] = 1.0
    tot = 0.0
    for j in CARDS:
        m = _MASK[(player, j)]
        si, sa, sp = IDX[m], AGG[m], PAY[m][:, player]
        own = [q(player, j, k) for k in (1, 2)]
        best = None
        for bits in itertools.product((0.0, 1.0), repeat=2):
            vv = v.copy()
            for i, b in zip(own, bits):
                vv[i] = b
            val = K6 * float((np.where(sa, vv[si], 1 - vv[si]).prod(axis=1) * sp).sum())
            best = val if best is None or val > best else best
        tot += best
    return tot


def exploitability(p):
    u = utilities(p)
    return np.array([best_response_value(p, i) - u[i] for i in (0, 1)])


def reach(p):
    """Reach probability of each parameter's information set."""
    v = np.empty(NP2 + 1)
    v[:NP2] = p
    v[DUM] = 1.0
    out = np.zeros(NP2)
    for r in range(NLEAF):
        f = [v[IDX[r, k]] if AGG[r, k] else 1 - v[IDX[r, k]] for k in range(3)]
        for k in range(3):
            i = int(IDX[r, k])
            if i == DUM:
                continue
            pref = 1.0
            for m in range(3):
                if m != k:
                    pref *= f[m]
            out[i] += K6 * pref
    return out / 2.0          # every node has exactly 2 actions


def family(alpha):
    p = np.zeros(NP2)
    p[q(0, 1, 1)] = alpha
    p[q(0, 2, 1)] = 0.0
    p[q(0, 3, 1)] = 3 * alpha
    p[q(0, 1, 2)] = 0.0
    p[q(0, 2, 2)] = alpha + 1.0 / 3.0
    p[q(0, 3, 2)] = 1.0
    p[q(1, 1, 1)] = 1.0 / 3.0
    p[q(1, 2, 1)] = 0.0
    p[q(1, 3, 1)] = 1.0
    p[q(1, 1, 2)] = 0.0
    p[q(1, 2, 2)] = 1.0 / 3.0
    p[q(1, 3, 2)] = 1.0
    return p
