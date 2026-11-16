"""Exact verification of a NORMAL-FORM correlated equilibrium in which P1 bets (continuation 2).

Input: nfce_lp_<seed>.json (support profiles and float weights from nfce_lp.py).  The LP vertex is
re-solved in Fractions (the tight rows as equalities, sum = 1), then EVERY normal-form incentive
constraint is checked in exact integer arithmetic: for each player, each strategy it is recommended
with positive probability, each card and each alternative plan for that card,
        sum_{s_-i} pi(sigma_i, s_-i) ( u_(i,c)(sigma_i, s_-i) - u_(i,c)(tau, s_-i) ) >= 0.
Payoffs are additive over a player's cards, so single-card deviations are all there is to check.
usage:  python nfce_verify.py [seed=0]
"""
import sys, json
from fractions import Fraction as F
from math import lcm
import numpy as np
import ce_lp as C

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
d = json.load(open('nfce_lp_%d.json' % seed))
S = [tuple(s) for s, w in d['support']]
pi = np.array([w for s, w in d['support']]); pi /= pi.sum()
n = len(S)


def strat_of(s, pl): return tuple(s[C.AIDX[(pl, c)]] for c in range(1, 5))


def u_int(s, a):
    pl, c_ = a; t = 0
    for dd, cards in enumerate(C.DEALS):
        if cards[pl] != c_: continue
        t += int(round(C.UT[dd][s[C.AIDX[(0, cards[0])]], s[C.AIDX[(1, cards[1])]], s[C.AIDX[(2, cards[2])]], pl]))
    return t                                                     # 24 * u


# rows: (pl, sigma, card, tau) -> {j: integer coefficient}
rows = {}
for j, s in enumerate(S):
    for pl in range(3):
        sg = strat_of(s, pl)
        for c_ in range(1, 5):
            a = (pl, c_); k = C.AIDX[a]; base = u_int(s, a)
            for tau in range(C.NPL[pl]):
                if tau == s[k]: continue
                s2 = list(s); s2[k] = tau
                v = base - u_int(tuple(s2), a)
                if v: rows.setdefault((pl, sg, c_, tau), {})[j] = v
keys = list(rows)
val = np.array([sum(v * pi[j] for j, v in rows[k].items()) for k in keys])
print("%d support profiles, %d incentive rows; float min row %.2e; float P(P1 bets) %.8f" % (n, len(keys), val.min(), sum(pi[j] * C.fobj(S[j]) for j in range(n))))
T = [k for k, v in zip(keys, val) if abs(v) < 1e-8]
Mx = [[F(rows[k].get(j, 0)) for j in range(n)] + [F(0)] for k in T] + [[F(1)] * n + [F(1)]]
m = len(Mx); piv = []; r = 0
for cidx in range(n):
    p = next((i for i in range(r, m) if Mx[i][cidx] != 0), None)
    if p is None: continue
    Mx[r], Mx[p] = Mx[p], Mx[r]
    inv = 1 / Mx[r][cidx]; Mx[r] = [v * inv for v in Mx[r]]
    for i in range(m):
        if i != r and Mx[i][cidx] != 0:
            fct = Mx[i][cidx]; Mx[i] = [a_ - fct * b_ for a_, b_ in zip(Mx[i], Mx[r])]
    piv.append(cidx); r += 1
    if r == m: break
if any(all(v == 0 for v in row[:-1]) and row[-1] != 0 for row in Mx): raise SystemExit("tight rows inconsistent in exact arithmetic")
free = [c for c in range(n) if c not in piv]
x = [None] * n
for c in free: x[c] = F(float(pi[c])).limit_denominator(10 ** 9)
for i, c in enumerate(piv): x[c] = Mx[i][-1] - sum(Mx[i][c2] * x[c2] for c2 in free)
print("exact vertex: tight rows %d, rank %d, free variables %d, min weight %.3e" % (len(T), len(piv), len(free), float(min(x))))
assert min(x) > 0, "a weight is not positive"
den = 1
for v in x: den = lcm(den, v.denominator)
w = [int(v * den) for v in x]
worst = min(sum(v * w[j] for j, v in rows[k].items()) for k in keys)
pbet = F(sum(w[j] * int(round(4 * C.fobj(S[j]))) for j in range(n)), 4 * den)
per = [F(sum(w[j] * int(C.OPEN[S[j][C.AIDX[(0, c_)]]]) for j in range(n)), den) for c_ in range(1, 5)]
u = [F(sum(w[j] * sum(u_int(S[j], (pl, c_)) for c_ in range(1, 5)) for j in range(n)), 24 * den) for pl in range(3)]
print("EXACT: minimum of the %d normal-form incentive rows = %s  ->  %s" % (len(keys), worst, "ALL >= 0: a normal-form correlated equilibrium" if worst >= 0 else "VIOLATED"))
print("EXACT: P(P1 bets) = %s = %.8f ; per card %s ; payoffs %s" % (pbet, float(pbet), [round(float(v), 5) for v in per], [round(float(v), 5) for v in u]))
if worst >= 0:
    json.dump(dict(denominator=str(den), support=[[list(map(int, S[j])), str(w[j])] for j in range(n)], p_bet=str(pbet), per_card=[str(v) for v in per],
                   payoffs=[str(v) for v in u], plans=[[list(p) for p in P] for P in C.PL], agents=C.AG), open('nfce_witness.json', 'w'))
    print("-> nfce_witness.json")
