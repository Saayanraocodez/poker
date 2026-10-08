"""EXACT check of a Lagrangian (correlated-equilibrium) certificate for the (3,5) restricted game G_c.
No float decides anything: payoffs are integers from tree.py, multipliers are rationals read from JSON,
the maximum is found by exact exhaustion in integers.

Claim checked.  For the multipliers mu >= 0 in the certificate file,
    L(s) = u_1(s | card 5) + sum_{agent a, plans rho != tau} mu[a,rho,tau] * P_s(a plays rho) *
           ( u_a(rho, s_-a) - u_a(tau, s_-a) )
satisfies  max over [0,1]^40  L < 19/8.
Why that proves "every NE of G_c has V_5 < 19/8": at a Nash equilibrium every plan rho that an agent
(player, card) plays with positive probability is a best response, so every bracket multiplied by a
positive P_s(rho) is >= 0, hence u_1(s|5) <= L(s); and V_5 = u_1(s|5) there.  L is multilinear (P_s(rho)
is a product over the agent's own coordinates; the bracket has none of them), so its maximum over the
cube is attained at a pure profile.  At a pure profile, L is a sum over the 60 deals of a term F_d that
depends only on the plans of the three agents dealt in d, which is what the exhaustion uses.

Agents: (player, card).  Plans (bits, in this order):  P1: (KKB call, KBF call, KBC call);
P2: (K bet, KKBF call, KKBC call);  P3: (KK bet, KB call).  P1's openings are 0 (G_c), the responses
to a bet are unreached and irrelevant.
usage (k35/):  KUHN_CARDS=5 python ceverify.py <certificate.json>
certificate.json: {"mu": [[player, card, [rho bits], [tau bits], "p/q"], ...]}"""
import os, sys, json, itertools, time
os.environ.setdefault("KUHN_CARDS", "5")
from fractions import Fraction as F
import tree as T, kuhn3p as K

assert K.NCARDS == 5
SITS = {0: (2, 3, 4), 1: (1, 3, 4), 2: (1, 2)}
PLANS = {pl: list(itertools.product((0, 1), repeat=len(SITS[pl]))) for pl in range(3)}
AGENTS = [(pl, c) for pl in range(3) for c in K.CARDS]


def pure_payoff(d, plans):
    """deal d, plans[pl] = bits for the agent (pl, card of pl in d) -> integer payoffs (3,)"""
    cards = T.DEALS[d]
    x = {}
    for pl in range(3):
        for s, b in zip(SITS[pl], plans[pl]): x[K.pidx(pl, cards[pl], s)] = b
    for j in K.CARDS: x[K.pidx(0, j, 1)] = 0                      # G_c: P1 never opens
    p = 0
    while int(T.AGGC[p]) >= 0:
        c = int(T.COORD[d, p])
        p = int(T.AGGC[p]) if x[c] == 1 else int(T.PASC[p])
    return [int(round(v)) for v in T.PAYT[d, p]]


def build(mu):
    """F[d][(r1, r2, r3)] = 12 * F_d as an exact Fraction"""
    Fd = []
    for d in range(T.ND):
        cards = T.DEALS[d]
        tab = {}
        pay = {}
        for r in itertools.product(range(8), range(8), range(4)):
            pay[r] = pure_payoff(d, [PLANS[0][r[0]], PLANS[1][r[1]], PLANS[2][r[2]]])
        for r in pay:
            v = F(pay[r][0]) if cards[0] == 5 else F(0)
            for pl in range(3):
                a = (pl, cards[pl])
                for t in range(len(PLANS[pl])):
                    m = mu.get((a, r[pl], t))
                    if not m: continue
                    rt = list(r); rt[pl] = t
                    v += m * (pay[r][pl] - pay[tuple(rt)][pl])
            tab[r] = v
        Fd.append(tab)
    return Fd


def maximise(Fd):
    """EXACT max over all 2^40 pure profiles of (1/12) sum_d F_d, by exhaustion with one decoupling:
    for fixed P3 plans (4^5) and P1 plans (8^5), each P2 agent (P2, card k) only meets the deals with P2
    holding k, so its best plan is chosen on its own -- every pure profile is covered.  The tables are
    scaled to integers by one common denominator; numpy int64 sums are exact below the guard 2^62."""
    from math import lcm
    import numpy as np
    den = 1
    for tab in Fd:
        for v in tab.values(): den = lcm(den, v.denominator)
    big = max(abs(int(v * den)) for tab in Fd for v in tab.values())
    assert big * T.ND < 2 ** 62, "int64 guard"
    G = np.zeros((T.ND, 8, 8, 4), dtype=np.int64)
    for d, tab in enumerate(Fd):
        for r, v in tab.items():
            q = v * den; assert q.denominator == 1
            G[d][r] = int(q)
    DI = {tuple(T.DEALS[d]): d for d in range(T.ND)}
    C = list(K.CARDS)
    R1 = np.array(list(itertools.product(range(8), repeat=5)))          # P1 plans for cards 1..5
    best = None
    for c3 in itertools.product(range(4), repeat=5):                   # P3 plans for cards 1..5
        H = {}
        for j in C:
            for k in C:
                if j != k:
                    H[j, k] = sum(G[DI[j, k, l], :, :, c3[l - 1]] for l in C if l not in (j, k))
        tot = np.zeros(len(R1), dtype=np.int64); arg2 = []
        for k in C:
            S = sum(H[j, k][R1[:, j - 1], :] for j in C if j != k)       # (8^5, 8): P1 combo x P2-k plan
            tot += S.max(axis=1); arg2.append(S.argmax(axis=1))
        i = int(tot.argmax()); m = int(tot[i])
        if best is None or m > best[0]:
            best = (m, {"P1": tuple(int(x) for x in R1[i]), "P2": tuple(int(a[i]) for a in arg2), "P3": c3})
    return F(best[0], 12 * den), best[1]


if __name__ == "__main__":
    t0 = time.time()
    cert = json.load(open(sys.argv[1]))
    mu = {}
    for pl, c, rho, tau, q in cert["mu"]:
        q = F(q); assert q >= 0, "negative multiplier"
        mu[((pl, c), PLANS[pl].index(tuple(rho)), PLANS[pl].index(tuple(tau)))] = q
    print("%d multipliers" % len(mu), flush=True)
    Fd = build(mu)
    print("tables built (%.0fs)" % (time.time() - t0), flush=True)
    m, arg = maximise(Fd)
    print("max over all 2^40 pure profiles of L = %s = %.6f  (%.0fs)" % (m, float(m), time.time() - t0))
    print("argmax plans (index per card 1..5):", arg)
    print("CERTIFIED: every Nash equilibrium of G_c has V_5 < 19/8" if m < F(19, 8) else "NOT a certificate (max >= 19/8)")
