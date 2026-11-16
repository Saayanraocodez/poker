"""Continuation 2: can a correlated-equilibrium (Lagrangian) certificate prove that P1 never bets?

Such a certificate bounds P1's betting probability over ALL correlated equilibria of a deviation
class, so it exists only if P1 is silent in every one of them.  This script decides that question
for the TYPE-AGENT correlated equilibria: a mediator draws a pure profile s, tells each (player,
card) agent its own plan, and no agent gains by switching from a recommended plan rho to another tau:
        sum_s pi(s) 1[s_a = rho] ( u_a(s) - u_a(tau, s_-a) ) >= 0      for every agent a, rho != tau.
(Nash equilibria are the product distributions among them.)

LP by column generation:  maximise  P(P1 bets) = sum_s pi(s) * (#cards on which s opens with a bet)/4
over distributions pi on a growing set of pure profiles, subject to ALL the incentive constraints
(plans are reduced: bits at information sets the plan itself never reaches are dropped, so no two
plans are payoff-equivalent).  Any positive value on any column set is already a correlated
equilibrium in which P1 bets -- and then no certificate of this kind can exist.

usage:  python ce_lp.py [rounds=40] [seed=0]
"""
import sys, itertools, json, time
import numpy as np
from scipy.optimize import linprog
import g34

IX = g34.IX; ND = g34.ND; DEALS = g34.DEALS
_main = __name__ == '__main__'
rounds = int(sys.argv[1]) if _main and len(sys.argv) > 1 else 400
seed = int(sys.argv[2]) if _main and len(sys.argv) > 2 else 0
rng = np.random.default_rng(seed)
g = g34.Game(1.0)

# ---- reduced plans per player: tuples of 4 bits (situations 1..4), irrelevant bits fixed to 0
def plans(pl):
    out = []
    for bits in itertools.product((0, 1), repeat=4):
        b = list(bits)
        if pl == 0 and b[0] == 1 and any(b[1:]): continue            # P1 bets at the root: KKB/KBF/KBC never reached
        if pl == 1 and b[0] == 1 and (b[2] or b[3]): continue        # P2 bets after K: KKBF/KKBC never reached
        out.append(tuple(b))
    return out
PL = [plans(0), plans(1), plans(2)]
NPL = [len(p) for p in PL]                                           # 9, 10, 16
AG = [(pl, c) for pl in range(3) for c in range(1, 5)]               # 12 agents
AIDX = {a: k for k, a in enumerate(AG)}

# ---- payoff tables per deal: U[d][i1, i2, i3] -> (3,)
def deal_table(d):
    cards = DEALS[d]
    U = np.zeros((NPL[0], NPL[1], NPL[2], 3))
    x = np.zeros(48)
    for i1, p1 in enumerate(PL[0]):
        for i2, p2 in enumerate(PL[1]):
            for i3, p3 in enumerate(PL[2]):
                h = ''
                while g34.I.actor(h) is not None:
                    pl = g34.I.actor(h); k = g34.I.SIT[pl][h] - 1
                    bit = (p1, p2, p3)[pl][k]
                    h += g34.I.aggressive(h) if bit else g34.I.passive(h)
                U[i1, i2, i3] = g.PAY[d, g34.POS[h]]
    return U
UT = [deal_table(d) for d in range(ND)]
OPEN = np.array([p[0] for p in PL[0]])                               # P1's opening bit per plan


def u_agent(s, a):
    """u_a(s): agent a's payoff (sum over its 6 deals, / 24)."""
    pl, c = a; tot = 0.0
    for d, cards in enumerate(DEALS):
        if cards[pl] != c: continue
        tot += UT[d][s[AIDX[(0, cards[0])]], s[AIDX[(1, cards[1])]], s[AIDX[(2, cards[2])]], pl]
    return tot / ND


def column(s):
    """the incentive rows' coefficients for pure profile s: {(agent k, rho, tau): u_a(s) - u_a(tau, s_-a)} with rho = s_a."""
    col = {}
    for k, a in enumerate(AG):
        pl, c = a; rho = s[k]; base = u_agent(s, a)
        for tau in range(NPL[pl]):
            if tau == rho: continue
            s2 = list(s); s2[k] = tau
            col[(k, rho, tau)] = base - u_agent(s2, a)
    return col


ROWS = [(k, rho, tau) for k, a in enumerate(AG) for rho in range(NPL[a[0]]) for tau in range(NPL[a[0]]) if tau != rho]
RIDX = {r: i for i, r in enumerate(ROWS)}


def fobj(s):
    return sum(OPEN[s[AIDX[(0, c)]]] for c in range(1, 5)) / 4.0


def solve(cols):
    S = list(cols)
    A = np.zeros((len(ROWS), len(S)))
    for j, s in enumerate(S):
        for r, v in cols[s].items(): A[RIDX[r], j] = v
    c = -np.array([fobj(s) for s in S])
    res = linprog(c, A_ub=-A, b_ub=np.zeros(len(ROWS)), A_eq=np.ones((1, len(S))), b_eq=[1.0], bounds=(0, None), method='highs')
    return S, res


def support_profiles(x, cap=4096):
    """the pure profiles in the support of behaviour profile x (as reduced plans)."""
    per_agent = []
    for (pl, c) in AG:
        opts = []
        for i, p in enumerate(PL[pl]):
            w = 1.0
            # probability of the reduced plan under x: relevant bits only
            names = ['abc'[pl] + str(c) + str(k) for k in range(1, 5)]
            rel = [True] * 4
            if pl == 0 and p[0] == 1: rel = [True, False, False, False]
            if pl == 1 and p[0] == 1: rel = [True, True, False, False]
            for k in range(4):
                if rel[k]: w *= x[IX[names[k]]] if p[k] else 1 - x[IX[names[k]]]
            if w > 1e-12: opts.append(i)
        per_agent.append(opts)
    n = np.prod([len(o) for o in per_agent])
    if n > cap: return None
    return [tuple(s) for s in itertools.product(*per_agent)]


def best_response_pricing(mu, starts, sweeps=6):
    """local search for a pure profile maximising  f(s) + sum_a sum_tau mu[a, s_a, tau] (u_a(s) - u_a(tau, s_-a))."""
    def G(s):
        tot = fobj(s)
        for k, a in enumerate(AG):
            pl = a[0]; m = mu[k][s[k]]
            if not m.any(): continue
            base = u_agent(s, a)
            for tau in np.flatnonzero(m):
                s2 = list(s); s2[k] = int(tau); tot += m[tau] * (base - u_agent(s2, a))
        return tot
    found = {}
    for s0 in starts:
        s = list(s0); cur = G(s)
        for _ in range(sweeps):
            improved = False
            for k in rng.permutation(12):
                pl = AG[k][0]; best = (cur, s[k])
                for i in range(NPL[pl]):
                    if i == s[k]: continue
                    t = list(s); t[k] = i; v = G(t)
                    if v > best[0] + 1e-12: best = (v, i)
                if best[1] != s[k]: s[k] = best[1]; cur = best[0]; improved = True
            if not improved: break
        found[tuple(s)] = cur
    return found


def dual_lp(cols, M):
    """min z  s.t.  z >= f(s) + sum_r mu_r col_s[r]  for s in the cut set,  0 <= mu <= M.
    (col_s[r] = u_a(s) - u_a(tau, s_-a) >= 0 in expectation at any correlated equilibrium, so z bounds P(P1 bets).)
    The duals of the cuts are a distribution pi on the cut set: the primal correlated equilibrium."""
    S = list(cols); nr = len(ROWS)
    A = np.zeros((len(S), nr + 1)); b = np.zeros(len(S))
    for j, s_ in enumerate(S):
        for r, v in cols[s_].items(): A[j, RIDX[r]] = v
        A[j, nr] = -1.0; b[j] = -fobj(s_)
    c = np.append(np.full(nr, 1e-7), 1.0)
    res = linprog(c, A_ub=A, b_ub=b, bounds=[(0, M)] * nr + [(None, None)], method='highs')
    return S, res


if __name__ == "__main__":
    import indep as I
    from fractions import Fraction as F
    t0 = time.time(); M = 200.0
    cols = {}
    fams = [I.family(0, 0, 0, 0, 0, F(1, 2), 0), I.family(F(1, 8), F(1, 8), 0, 0, F(1, 4), F(55, 96), 0),
            I.family(0, F(1, 4), 0, 0, 0, F(3, 4), 0), I.family(F(1, 4), 0, 0, 0, F(1, 2), F(3, 4), 0), I.family(F(1, 4), F(1, 4), 0, 0, 0, F(1, 2), 0)]
    for p in fams:
        x = np.array([float(p[n]) for n in g34.NAMES])
        sp = support_profiles(x)
        if sp:
            for s_ in sp: cols.setdefault(s_, None)
    for _ in range(300):
        cols.setdefault(tuple(int(rng.integers(NPL[a[0]])) for a in AG), None)
    for s_ in list(cols): cols[s_] = column(s_)
    print("start: %d cuts, %d multipliers  (%.0fs)" % (len(cols), len(ROWS), time.time() - t0), flush=True)
    hist = []; stall = 0
    for rd in range(rounds):
        if stall >= 3:
            # converged at this cap: report the hard-constrained primal on the same profiles, then raise the cap
            Sp, rp = solve(cols)
            print("   cap %g converged: bound %.8f ; PRIMAL with all incentive constraints exact on these %d profiles: P(P1 bets) = %.10f"
                  % (M, hist[-1], len(Sp), -rp.fun if rp.status == 0 else float('nan')), flush=True)
            if int((mu_vec > M - 1e-6).sum()) == 0 or M >= 1e7: break
            M *= 10; stall = 0
        S, res = dual_lp(cols, M)
        if res.status != 0: print("LP status", res.status, res.message); break
        z = res.x[-1]; mu_vec = res.x[:-1]
        mu = [np.zeros((NPL[a[0]], NPL[a[0]])) for a in AG]
        for (k, rho, tau), i in RIDX.items(): mu[k][rho, tau] = mu_vec[i]
        pi = -res.ineqlin.marginals
        supp = [S[j] for j in np.argsort(-pi)[:30] if pi[j] > 1e-9]
        starts = supp + [tuple(int(rng.integers(NPL[a[0]])) for a in AG) for _ in range(40)]
        for s_ in supp[:15]:
            for c in range(4):
                t = list(s_); t[c] = int(np.flatnonzero(OPEN)[0]); starts.append(tuple(t))
        found = best_response_pricing(mu, starts)
        new = sorted(((v, s_) for s_, v in found.items() if s_ not in cols and v > z + 1e-7), reverse=True)
        for v, s_ in new[:80]: cols[s_] = column(s_)
        hist.append(float(z))
        print("round %3d  cuts %5d  bound z = %.8f   max violation found %.6f  new cuts %d  |mu|_max %.1f  at cap %d   (%.0fs)"
              % (rd, len(S), z, (new[0][0] - z) if new else 0.0, len(new[:80]), mu_vec.max(), int((mu_vec > M - 1e-6).sum()), time.time() - t0), flush=True)
        stall = stall + 1 if not new else 0
    S, res = dual_lp(cols, M)
    z = res.x[-1]; pi = -res.ineqlin.marginals
    supp = [(list(map(int, S[j])), float(pi[j])) for j in np.argsort(-pi) if pi[j] > 1e-10]
    json.dump(dict(bound=float(z), history=hist, mu=res.x[:-1].tolist(), support=supp, profiles=[list(map(int, s_)) for s_ in cols], plans=[[list(p) for p in P] for P in PL], agents=AG, rows=ROWS, M=M),
              open('ce_lp_%d.json' % seed, 'w'))
    print("final bound z = %.10f ; primal support %d profiles, P(P1 bets) under it = %.8f" % (z, len(supp), sum(w * fobj(tuple(s_)) for s_, w in supp)))
