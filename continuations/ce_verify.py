"""Exact verification of a type-agent correlated equilibrium in which P1 bets (continuation 2).

Input: ce_lp_<seed>.json (profiles found by ce_lp.py).  Steps:
  1. on those profiles, solve  max t  s.t.  every incentive row with a recommended plan >= t, P(P1 bets) >= p0
     (rows of a plan that is never recommended are 0 >= 0), so the solution has slack where slack is possible;
  2. round the weights to rationals, renormalise, and check EVERY incentive constraint in exact integer
     arithmetic (payoffs are integers; u_a = sum over the agent's 6 deals / 24);
  3. optionally check the stronger NORMAL-FORM constraints (a player sees its whole recommended strategy).
Writes ce_witness.json: the exact distribution, P(P1 bets) as a fraction, and the minimum exact slack.
usage:  python ce_verify.py [seed=0] [p0=0.05]
"""
import sys, json, itertools
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog
import ce_lp as C

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
p0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05
d = json.load(open('ce_lp_%d.json' % seed))
prof = [tuple(s) for s in d.get('profiles', [s for s, w in d['support']])]
print("%d profiles" % len(prof))
cols = {s: C.column(s) for s in prof}
S = list(cols)
# rows that matter: (agent, rho, tau) with rho recommended somewhere in S
rec = {(k, s[k]) for s in S for k in range(12)}
rows = [r for r in C.ROWS if (r[0], r[1]) in rec]
ridx = {r: i for i, r in enumerate(rows)}
A = np.zeros((len(rows), len(S)))
for j, s in enumerate(S):
    for r, v in cols[s].items(): A[ridx[r], j] = v
f = np.array([C.fobj(s) for s in S])
# 0. the plain optimum
res0 = linprog(-f, A_ub=-A, b_ub=np.zeros(len(rows)), A_eq=np.ones((1, len(S))), b_eq=[1.0], bounds=(0, None), method='highs')
print("max P(P1 bets) over correlated equilibria on these profiles: %.10f" % (-res0.fun))
# 1. maximise the common slack t:  A pi - t * w >= 0 with w_r = 1 for rows whose plan is recommended with positive probability...
#    scale-free version: rows normalised by P(rho) is nonlinear; use absolute slack and require pi_j >= 0.
n = len(S)
c = np.zeros(n + 1); c[-1] = -1.0
Aub = np.hstack([-A, np.ones((len(rows), 1))])                     # -A pi + t <= 0
Aub = np.vstack([Aub, np.append(-f, 0.0)[None, :]])                # -f.pi <= -p0
bub = np.append(np.zeros(len(rows)), -p0)
res = linprog(c, A_ub=Aub, b_ub=bub, A_eq=np.append(np.ones(n), 0.0)[None, :], b_eq=[1.0], bounds=[(0, None)] * n + [(None, None)], method='highs')
print("max-slack LP: status %d, t = %.3e" % (res.status, res.x[-1] if res.status == 0 else float('nan')))
pi = res.x[:n] if res.status == 0 and res.x[-1] > 1e-9 else res0.x
# 2. exact solution.  At an LP vertex the tight rows hold with equality; solve those equalities (and sum = 1)
#    over the support in Fractions, the free variables set to rationalised float values.
def exact_vertex(pi):
    J = [j for j in range(n) if pi[j] > 1e-9]
    val = A[:, J] @ pi[J]
    T = [i for i in range(len(rows)) if abs(val[i]) < 1e-9 and np.abs(A[i, J]).max() > 0]
    Mx = [[F(int(round(24 * A[i, j]))) for j in J] + [F(0)] for i in T] + [[F(1)] * len(J) + [F(1)]]
    m = len(Mx); nc = len(J); piv = []; r = 0
    for cidx in range(nc):
        p = next((i for i in range(r, m) if Mx[i][cidx] != 0), None)
        if p is None: continue
        Mx[r], Mx[p] = Mx[p], Mx[r]
        inv = 1 / Mx[r][cidx]; Mx[r] = [v * inv for v in Mx[r]]
        for i in range(m):
            if i != r and Mx[i][cidx] != 0:
                fct = Mx[i][cidx]; Mx[i] = [a - fct * b for a, b in zip(Mx[i], Mx[r])]
        piv.append(cidx); r += 1
        if r == m: break
    if any(all(v == 0 for v in row[:-1]) and row[-1] != 0 for row in Mx): return None
    free = [cidx for cidx in range(nc) if cidx not in piv]
    x = [None] * nc
    for cidx in free: x[cidx] = F(float(pi[J[cidx]])).limit_denominator(10 ** 9)
    for i, cidx in enumerate(piv):
        x[cidx] = Mx[i][-1] - sum(Mx[i][c2] * x[c2] for c2 in free)
    return J, x, len(T), len(free)
ev = exact_vertex(pi)
if ev is None: raise SystemExit("tight-row system inconsistent in exact arithmetic")
J, xq, nT, nfree = ev
print("exact vertex: support %d, tight rows %d, free variables %d, min weight %s" % (len(J), nT, nfree, float(min(xq))))
from math import lcm
tot = 1
for v in xq: tot = lcm(tot, v.denominator)
w = [0] * n
for j, v in zip(J, xq): w[j] = int(v * tot)
keep = [j for j in range(n) if w[j] != 0]
assert all(w[j] > 0 for j in keep), "a weight is negative"
def u_agent_int(s, a):
    pl, c_ = a; t = 0
    for dd, cards in enumerate(C.DEALS):
        if cards[pl] != c_: continue
        t += int(round(C.UT[dd][s[C.AIDX[(0, cards[0])]], s[C.AIDX[(1, cards[1])]], s[C.AIDX[(2, cards[2])]], pl]))
    return t                                                         # times 24
worst = None; nrows = 0
for k, a in enumerate(C.AG):
    pl = a[0]
    acc = {}
    for j in keep:
        s = S[j]; rho = s[k]; base = u_agent_int(s, a)
        for tau in range(C.NPL[pl]):
            if tau == rho: continue
            s2 = list(s); s2[k] = tau
            acc[(rho, tau)] = acc.get((rho, tau), 0) + w[j] * (base - u_agent_int(s2, a))
    for key, v in acc.items():
        nrows += 1
        if worst is None or v < worst[0]: worst = (v, k, key)
pbet = F(sum(w[j] * int(round(4 * f[j])) for j in keep), 4 * tot)
print("EXACT: %d support profiles, %d incentive rows, minimum row value %s / (24 * %d) -> %s" % (len(keep), nrows, worst[0], tot, "ALL >= 0: a correlated equilibrium" if worst[0] >= 0 else "VIOLATED at %s" % (worst[1:],)))
print("EXACT: P(P1 bets) = %s = %.8f" % (pbet, float(pbet)))
# P1's betting frequency per card, and payoffs
per = [F(sum(w[j] * int(C.OPEN[S[j][C.AIDX[(0, c_)]]]) for j in keep), tot) for c_ in range(1, 5)]
u = [F(sum(w[j] * sum(u_agent_int(S[j], (pl, c_)) for c_ in range(1, 5)) for j in keep), 24 * tot) for pl in range(3)]
print("   P1 bets with card 1..4 with probability %s ; payoffs %s = %s" % ([str(x) for x in per], [str(x) for x in u], [round(float(x), 5) for x in u]))
# 3. normal-form constraints: condition on the player's whole recommended strategy
viol = 0; worstn = 0
for pl in range(3):
    groups = {}
    for j in keep:
        key = tuple(S[j][C.AIDX[(pl, c_)]] for c_ in range(1, 5)); groups.setdefault(key, []).append(j)
    for key, js in groups.items():
        for c_ in range(1, 5):
            a = (pl, c_); k = C.AIDX[a]
            base = sum(w[j] * u_agent_int(S[j], a) for j in js)
            for tau in range(C.NPL[pl]):
                if tau == key[c_ - 1]: continue
                dev = 0
                for j in js:
                    s2 = list(S[j]); s2[k] = tau; dev += w[j] * u_agent_int(s2, a)
                if dev > base: viol += 1; worstn = max(worstn, dev - base)
print("normal-form (whole-strategy) constraints violated: %d  (largest gain %s / (24 * %d))" % (viol, worstn, tot))
if worst[0] >= 0:
    json.dump(dict(denominator=tot, support=[[list(map(int, S[j])), w[j]] for j in keep], p_bet=str(pbet), per_card=[str(x) for x in per], payoffs=[str(x) for x in u],
                   min_row=str(F(worst[0], 24 * tot)), plans=[[list(p) for p in P] for P in C.PL], agents=C.AG, normal_form_violations=viol), open('ce_witness.json', 'w'))
    print("-> ce_witness.json")
