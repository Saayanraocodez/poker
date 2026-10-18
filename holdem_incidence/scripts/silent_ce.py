"""Is there ANY P1-silent Nash equilibrium of the 24-hand JJ-AA river game above the branch threshold
c*?  A deterrence cut plus a coarse-correlated (Lagrangian) certificate, the method that settled the
(3,5)-Kuhn silence question (MASTER_DATA 16.11.5), checked exactly.

Decomposition.  A profile in which P1 never opens is a Nash equilibrium iff (a) its check part is a
Nash equilibrium of the RESTRICTED game G_c (P1's opening forced to check; nobody else's incentive
sees P1's bet, which is never made) and (b) the 72 combo-level responses y to P1's all-in deter every
P1 combo: Ebet(h; y) <= V_h.

Scope.  The check part is SUIT-SYMMETRIC (every combo of a hand class plays alike; such a profile is a
Nash equilibrium of G_c iff its class-level profile is one of the 4-type class game, because one
combo's deviation gains exactly 1/6 of its class's).  The responses y are ARBITRARY (combo level).

Certificate (lambda >= 0 over P1's four classes, mu >= 0 over class agents' pure plans):
  (1)  B_y = min over all y in [0,1]^72 of  sum_k lambda_k Ebet_k(y)       (Ebet_k = sum over k's 6 combos)
       -- multilinear, so attained at a vertex; exact enumeration of P2's 2^24 vertex choices, P3's
       48 responses separating given P2's.
  (2)  B_s = max over class-level pure profiles s of G_c of
         L(s) = sum_k lambda_k V_k(s) + sum_{a, tau} mu_{a,tau} (u_a(s) - u_a(tau, s_-a)),
       where V_k is P1's class-k value (prior-weighted) and a ranges over the 12 class agents.  At a
       Nash equilibrium every bracket is >= 0, and L is multilinear in the class behaviour, so
       sum_k lambda_k V_k <= B_s at EVERY suit-symmetric Nash equilibrium of G_c.  Exact exhaustion:
       P2 x P3 class plans (5^4 x 4^4 = 160,000), P1's classes then separate.
  (3)  If B_s < B_y: deterrence needs sum_k lambda_k Ebet_k(y) <= sum_k lambda_k V_k <= B_s < B_y,
       impossible.  So no P1-silent Nash equilibrium with a suit-symmetric check part exists.

Proposer: scipy linprog (HiGHS) cutting planes; decides nothing.  Checker: exact integers, payoff
tables from the independent class model of scripts/silent_threshold.py, cross-checked against the
hinc engine's own per-deal payoffs (combo level, 6480 deals) at the same c.

usage:  python scripts/silent_ce.py run <c> [tag]     e.g.  run 1   |   run 1038163/1048576 c_lo
        -> results/silent_ce/<tag>.json
"""
import itertools
import json
import math
import os
import sys
import time
from fractions import Fraction as F

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import silent_threshold as ST                                   # noqa: E402  (the independent class model)

OUT = os.path.join(ROOT, "results", "silent_ce")
CLS = ST.CLS
DEALS = ST.DEALS                                               # class triples with positive weight (60)

# pure plans of the restricted game (P1 has checked)
P1_PLANS = list(itertools.product((0, 1), repeat=3))           # calls at K-K-B:1, K-B:1-F, K-B:1-C
P2_PLANS = [("bet",)] + [("check", a, b) for a, b in itertools.product((0, 1), repeat=2)]  # calls at K-K-B:1-F, -C
P3_PLANS = list(itertools.product((0, 1), repeat=2))           # bet at K-K, call at K-B:1


def play(p1, p2, p3):
    """Terminal history of G_c (P1 checked) under pure plans of the three agents dealt."""
    if p2[0] == "bet":                                         # K-B:1, then P3, then P1
        h = "K-B:1-" + ("C" if p3[1] else "F")
        h += "-" + ("C" if (p1[2] if p3[1] else p1[1]) else "F")
        return h
    if not p3[0]:
        return "K-K-K"
    h = "K-K-B:1-" + ("C" if p1[0] else "F")
    h += "-" + ("C" if (p2[2] if p1[0] else p2[1]) else "F")
    return h


def class_table(c):
    """T[d, i1, i2, i3, player] = weight(d) * payoff, exact (weights are counts out of 6480)."""
    T = {}
    for d in DEALS:
        w = ST.weight(d)
        for i1, p1 in enumerate(P1_PLANS):
            for i2, p2 in enumerate(P2_PLANS):
                for i3, p3 in enumerate(P3_PLANS):
                    pay = ST.payoff(play(p1, p2, p3), d, c)
                    T[(d, i1, i2, i3)] = [w * F(x) for x in pay]
    return T


def engine_table(c):
    """The same table from the hinc engine: follow the pure class plans on each of the 6480 combo
    deals, read the engine's exact payoff, and sum by class triple (independent of the class model)."""
    from hinc.game import RiverGame
    g = RiverGame(ST.config_for(c))
    byh = g.tree.by_history()
    cls_of = [[s.labels[h][0] * 2 for h in range(len(s.hands))] for s in g.seats]
    T = {}
    for dd in range(g.D):
        d = tuple(CLS.index(cls_of[i][g.deals[dd, i]]) for i in range(3))
        for i1, p1 in enumerate(P1_PLANS):
            for i2, p2 in enumerate(P2_PLANS):
                for i3, p3 in enumerate(P3_PLANS):
                    t = byh[play(p1, p2, p3)].id
                    row = g.payoff_x[t][dd]
                    acc = T.setdefault((d, i1, i2, i3), [F(0)] * 3)
                    for i in range(3):
                        acc[i] += row[i]
    return T, g


def ebet_combo(g):
    """For every combo-level deal: P1's payoff after P1 bets, for each (P2 call?, P3 call after F?,
    P3 call after C?) pure response; exact."""
    byh = g.tree.by_history()
    out = np.empty((g.D, 2, 2, 2), dtype=object)
    for dd in range(g.D):
        for y2 in (0, 1):
            for yf in (0, 1):
                for yc in (0, 1):
                    h = "B:1-" + ("C" if y2 else "F") + "-" + ("C" if (yc if y2 else yf) else "F")
                    out[dd, y2, yf, yc] = g.payoff_x[byh[h].id][dd][0]
    return out


# ------------------------------------------------------------------------------------------------
# float proposer
# ------------------------------------------------------------------------------------------------
def build_float(T):
    """Arrays for fast evaluation: per deal index j, T[j, i1, i2, i3, :] (float)."""
    A = np.zeros((len(DEALS), len(P1_PLANS), len(P2_PLANS), len(P3_PLANS), 3))
    for j, d in enumerate(DEALS):
        for i1 in range(8):
            for i2 in range(5):
                for i3 in range(4):
                    A[j, i1, i2, i3] = [float(x) for x in T[(d, i1, i2, i3)]]
    return A


AGENTS = [(0, k) for k in range(4)] + [(1, k) for k in range(4)] + [(2, k) for k in range(4)]
NPLAN = {0: 8, 1: 5, 2: 4}
MODE = os.environ.get("HINC_CE_MODE", "ce")          # "cce": mu[a, tau]; "ce": mu[a, rho, tau] (plan-dependent)
if MODE == "cce":
    MU_INDEX = [(a, None, t) for a in AGENTS for t in range(NPLAN[a[0]])]
else:
    MU_INDEX = [(a, r, t) for a in AGENTS for r in range(NPLAN[a[0]]) for t in range(NPLAN[a[0]]) if r != t]


def L_terms(A, s, deal_ids=None):
    """Coefficient vector of L(s) in the LP variables (lambda_0..3, mu_*) at pure class profile s
    (s[(player, class)] = plan index)."""
    row = np.zeros(4 + len(MU_INDEX))
    for j, d in enumerate(DEALS):
        p = [s[(i, d[i])] for i in range(3)]
        v = A[j, p[0], p[1], p[2]]
        row[d[0]] += v[0]                                         # lambda_k V_k
        for m, (a, r, t) in enumerate(MU_INDEX):
            i, k = a
            if d[i] != k or (r is not None and p[i] != r):
                continue
            q = list(p)
            q[i] = t
            row[4 + m] += v[i] - A[j, q[0], q[1], q[2], i]
    return row


def add_term(Fj, A, a, r, t, w):
    """Fj[j, i1, i2, i3] += w * (u_i(p) - u_i(p with agent a's plan -> t)) on every deal j where
    agent a = (i, k) is dealt, restricted to entries where a plays plan r (r is None: all entries)."""
    i, k = a
    for j, d in enumerate(DEALS):
        if d[i] != k:
            continue
        own = A[j, :, :, :, i]
        sl = [slice(None)] * 3
        sl[i] = slice(t, t + 1)
        dev = np.broadcast_to(A[j][tuple(sl) + (i,)], own.shape)
        diff = own - dev
        if r is None:
            Fj[j] += w * diff
        else:
            sel = [slice(None)] * 3
            sel[i] = r
            Fj[j][tuple(sel)] += w * diff[tuple(sel)]


def argmax_L(A, lam, mu, topk=1):
    """Exact-structure maximiser (float): enumerate P2 x P3 class plans, P1's classes separate.
    Returns (max, maximiser, [the top-k profiles] for extra cutting planes)."""
    # per deal j, per (i1,i2,i3): contribution F_j = lam[d0] T0 + mu-terms
    Fj = np.zeros((len(DEALS), 8, 5, 4))
    for j, d in enumerate(DEALS):
        Fj[j] += lam[d[0]] * A[j, :, :, :, 0]
    for m, (a, r, t) in enumerate(MU_INDEX):
        if mu[m] == 0:
            continue
        add_term(Fj, A, a, r, t, mu[m])
    best, best_s = -np.inf, None
    p2s = list(itertools.product(range(5), repeat=4))
    p3s = list(itertools.product(range(4), repeat=4))
    deals_by_k = [[j for j, d in enumerate(DEALS) if d[0] == k] for k in range(4)]
    # G[k][i1, a2, a3] where a2, a3 index assignments: sum over deals with d0 = k of Fj[j, i1, a2[d1], a3[d2]]
    P2A = np.array(p2s)
    P3A = np.array(p3s)
    total = np.zeros((len(p2s), len(p3s)))
    choice = np.zeros((4, len(p2s), len(p3s)), dtype=np.int64)
    for k in range(4):
        acc = np.zeros((8, len(p2s), len(p3s)))
        for j in deals_by_k[k]:
            d = DEALS[j]
            acc += Fj[j][:, P2A[:, d[1]], :][:, :, P3A[:, d[2]]]
        total += acc.max(axis=0)
        choice[k] = acc.argmax(axis=0)
    order = np.argpartition(total.ravel(), -topk)[-topk:]
    tops = []
    for flat in order[np.argsort(-total.ravel()[order])]:
        a2, a3 = np.unravel_index(int(flat), total.shape)
        s = {}
        for k in range(4):
            s[(0, k)] = int(choice[k, a2, a3])
            s[(1, k)] = int(P2A[a2, k])
            s[(2, k)] = int(P3A[a3, k])
        tops.append(s)
    return float(total.max()), tops[0], tops


def class_ebet(g, EB):
    """Ebet_k(y) at CLASS-level response vertices (12 class responses): float, for the proposer."""
    cls_of = [[s.labels[h][0] * 2 for h in range(len(s.hands))] for s in g.seats]
    out = []
    for bits in itertools.product((0, 1), repeat=12):
        y2, yf, yc = bits[0:4], bits[4:8], bits[8:12]
        e = np.zeros(4)
        for dd in range(g.D):
            k1, k2, k3 = (CLS.index(cls_of[i][g.deals[dd, i]]) for i in range(3))
            e[k1] += float(EB[dd, y2[k2], yf[k3], yc[k3]])
        out.append(e)
    return np.array(out)                                           # [4096, 4] (sums over combos; x 1/6480 omitted)


def propose(A, EBc, rounds=int(os.environ.get("HINC_CE_ROUNDS", "1500")), topk=25, log=print):
    from scipy.optimize import linprog
    nv = 4 + len(MU_INDEX)
    S = []
    s0 = {(i, k): 0 for i in range(3) for k in range(4)}
    S.append(L_terms(A, s0))
    best = None
    for r in range(rounds):
        # variables: lam (4), mu (68), ty, ts ; maximise ty - ts ; sum lam = 1
        nvar = nv + 2
        c = np.zeros(nvar); c[nv] = -1.0; c[nv + 1] = 1.0
        A_ub, b_ub = [], []
        for e in EBc:                                             # ty <= lam . Ebet(y)
            row = np.zeros(nvar); row[:4] = -e / 6480.0; row[nv] = 1.0
            A_ub.append(row); b_ub.append(0.0)
        for Lrow in S:                                            # L(s) <= ts
            row = np.zeros(nvar); row[:nv] = Lrow / 6480.0; row[nv + 1] = -1.0
            A_ub.append(row); b_ub.append(0.0)
        A_eq = np.zeros((1, nvar)); A_eq[0, :4] = 1.0
        bounds = [(0, None)] * nv + [(None, None), (None, None)]
        bounds[4:nv] = [(0, 50.0)] * len(MU_INDEX)
        res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), A_eq=A_eq, b_eq=[1.0], bounds=bounds, method="highs")
        x = res.x
        lam, mu = x[:4], x[4:nv]
        ty, ts = x[nv], x[nv + 1]
        val, s, tops = argmax_L(A, lam, mu, topk=topk)
        val /= 6480.0
        gap = val - ts
        margin = ty - val
        if best is None or margin > best[0]:
            best = (margin, lam.copy(), mu.copy(), ty, val)
        if r % 25 == 0 or gap < 1e-12:
            log("round %d: LP margin %.6e  true max L %.6f  ty %.6f  cut violation %.3e" % (r, ty - ts, val, ty, gap))
        if gap < 1e-11:
            break
        for t in tops:
            S.append(L_terms(A, t))
    return best


# ------------------------------------------------------------------------------------------------
# exact checker
# ------------------------------------------------------------------------------------------------
def exact_max_L(T, lam, mu):
    """max over class-level pure profiles of L (exact, integers after scaling by the common
    denominator); returns (value as Fraction (x 1/6480 applied), maximiser)."""
    den = math.lcm(*[x.denominator for x in list(lam) + list(mu)])
    tden = math.lcm(*[x.denominator for v in T.values() for x in v])
    lamI = [int(x * den) for x in lam]
    muI = [int(x * den) for x in mu]
    Ti = np.zeros((len(DEALS), 8, 5, 4, 3), dtype=object)          # exact Python integers
    for j, d in enumerate(DEALS):
        for i1 in range(8):
            for i2 in range(5):
                for i3 in range(4):
                    Ti[j, i1, i2, i3] = [int(x * tden) for x in T[(d, i1, i2, i3)]]
    Fj = np.zeros((len(DEALS), 8, 5, 4), dtype=object)
    for j, d in enumerate(DEALS):
        Fj[j] += lamI[d[0]] * Ti[j, :, :, :, 0]
    for m, (a, r, t) in enumerate(MU_INDEX):
        if muI[m] == 0:
            continue
        add_term(Fj, Ti, a, r, t, muI[m])
    assert max(abs(int(x)) for x in Fj.flat) * 64 < 2 ** 62, "int64 guard"
    Fj = Fj.astype(np.int64)                                        # exact: every entry fits, sums of <= 60 fit
    P2A = np.array(list(itertools.product(range(5), repeat=4)))
    P3A = np.array(list(itertools.product(range(4), repeat=4)))
    total = np.zeros((len(P2A), len(P3A)), dtype=np.int64)
    for k in range(4):
        acc = np.zeros((8, len(P2A), len(P3A)), dtype=np.int64)
        for j, d in enumerate(DEALS):
            if d[0] == k:
                acc += Fj[j][:, P2A[:, d[1]], :][:, :, P3A[:, d[2]]]
        total += acc.max(axis=0)
    m = int(total.max())
    a2, a3 = np.unravel_index(int(np.argmax(total)), total.shape)
    return F(m, den * tden * 6480), {"P2_class_plans": P2A[a2].tolist(), "P3_class_plans": P3A[a3].tolist()}


def exact_min_y(g, EB, lam):
    """min over ALL combo-level response vertices of sum_k lam_k Ebet_k(y) (exact).  P2's 24 combo
    responses are enumerated (2^24); given them, each P3 combo's two responses separate."""
    den = math.lcm(*[x.denominator for x in lam])
    lamI = [int(x * den) for x in lam]
    eden = math.lcm(*[F(v).denominator for v in EB.flat])
    cls_of = [[s.labels[h][0] * 2 for h in range(len(s.hands))] for s in g.seats]
    H2, H3 = len(g.seats[1].hands), len(g.seats[2].hands)
    # value = sum_{h2,h3} [ (1-y2) * W0[h2,h3,yf] + y2 * W1[h2,h3,yc] ]
    W0 = np.zeros((H2, H3, 2), dtype=np.int64)
    W1 = np.zeros((H2, H3, 2), dtype=np.int64)
    for dd in range(g.D):
        h1, h2, h3 = (int(g.deals[dd, i]) for i in range(3))
        k1 = CLS.index(cls_of[0][h1])
        for yf in (0, 1):
            W0[h2, h3, yf] += lamI[k1] * int(F(EB[dd, 0, yf, 0]) * eden)
        for yc in (0, 1):
            W1[h2, h3, yc] += lamI[k1] * int(F(EB[dd, 1, 0, yc]) * eden)
    # for P3 combo h3, choice (yf, yc): cost(y2) = sum_h2 [W0[h2,h3,yf] + y2[h2] (W1[h2,h3,yc] - W0[h2,h3,yf])]
    base = np.zeros((H3, 4), dtype=np.int64)
    slope = np.zeros((H2, H3, 4), dtype=np.int64)
    for ch, (yf, yc) in enumerate(itertools.product((0, 1), repeat=2)):
        base[:, ch] = W0[:, :, yf].sum(axis=0)
        slope[:, :, ch] = W1[:, :, yc] - W0[:, :, yf]
    assert (np.abs(slope).sum(axis=0).max() + np.abs(base).max()) < 2 ** 62, "int64 guard"
    S2 = slope.reshape(H2, H3 * 4)
    best, best_y2 = None, None
    chunk = 1 << 16
    for start in range(0, 1 << H2, chunk):
        idx = np.arange(start, start + chunk, dtype=np.int64)
        Y = ((idx[:, None] >> np.arange(H2)[None, :]) & 1).astype(np.int64)      # [chunk, 24]
        V = Y @ S2 + base.reshape(1, -1)                                          # [chunk, H3*4]
        tot = V.reshape(chunk, H3, 4).min(axis=2).sum(axis=1)
        j = int(np.argmin(tot))
        if best is None or tot[j] < best:
            best, best_y2 = int(tot[j]), Y[j].tolist()
    return F(best, den * eden * 6480), best_y2


def run(cv, tag):
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    log = lambda s: print("[%6.0fs] %s" % (time.time() - t0, s), flush=True)
    T = class_table(cv)
    Te, g = engine_table(cv)
    same = all(T[k] == Te[k] for k in T) and set(T) == set(Te)
    log("class model vs engine payoff table (%d entries): exactly equal: %s" % (len(T), same))
    assert same
    EB = ebet_combo(g)
    A = build_float(T)
    EBc = class_ebet(g, EB)
    best = propose(A, EBc, log=log)
    margin, lam, mu, ty, val = best
    log("proposer: best margin %.6e (lambda %s)" % (margin, np.round(lam, 5)))
    rec = {"c": str(cv), "pot": str(3 * cv), "mode": MODE, "scope": __doc__.split("Scope.")[1].split("Certificate")[0].strip(),
           "table_cross_check_equal": same, "proposer_margin_float": margin,
           "lambda_float": lam.tolist()}
    if margin <= 0:
        rec["verdict"] = "no certificate: the %s relaxation does not separate (proposer margin <= 0)" % (
            "coarse-correlated" if MODE == "cce" else "correlated (plan-dependent)")
        json.dump(rec, open(os.path.join(OUT, "%s.json" % tag), "w"), indent=1)
        log(rec["verdict"])
        return rec
    # rationalise (mu rounded DOWN to a grid keeps mu >= 0; lambda normalised exactly)
    q = 10 ** 6
    lamQ = [F(int(round(x * q)), q) for x in lam]
    muQ = [F(int(x * q), q) for x in mu]
    Bs, smax = exact_max_L(T, lamQ, muQ)
    log("exact max L over class-level pure profiles: %s (%.9f)" % (Bs, float(Bs)))
    By, y2 = exact_min_y(g, EB, lamQ)
    log("exact min over all 2^72 combo response vertices of lambda.Ebet: %s (%.9f)" % (By, float(By)))
    rec.update({"mode": MODE, "lambda": [str(x) for x in lamQ],
                "mu_nonzero": {"P%d %s %s-> %d" % (a[0] + 1, CLS[a[1]], "" if r is None else "%d " % r, t): str(muQ[m])
                               for m, (a, r, t) in enumerate(MU_INDEX) if muQ[m] != 0},
                "B_s_max_L": str(Bs), "B_s_float": float(Bs), "B_s_maximiser": smax,
                "B_y_min_deterrence": str(By), "B_y_float": float(By), "B_y_minimiser_P2_combo_calls": y2,
                "certified": Bs < By, "exact_gap": float(By - Bs)})
    rec["verdict"] = ("CERTIFIED: no P1-silent Nash equilibrium with a suit-symmetric check part exists at c = %s "
                      "(any responses to P1's bet)" % cv) if Bs < By else "no certificate after exact check"
    json.dump(rec, open(os.path.join(OUT, "%s.json" % tag), "w"), indent=1)
    log(rec["verdict"])
    return rec


# ------------------------------------------------------------------------------------------------
# a certificate for a whole interval of c
# ------------------------------------------------------------------------------------------------
def propose_joint(Aa, EBs, rounds=int(os.environ.get("HINC_CE_ROUNDS", "1500")), topk=25, log=print):
    """One (lambda, mu) for several values of c: maximise the smallest margin."""
    from scipy.optimize import linprog
    nv = 4 + len(MU_INDEX)
    E = len(Aa)
    S = [[L_terms(A, {(i, k): 0 for i in range(3) for k in range(4)})] for A in Aa]
    best = None
    for r in range(rounds):
        nvar = nv + 2 * E + 1                                      # lam, mu, (ty_e, ts_e) per end, t
        cvec = np.zeros(nvar); cvec[-1] = -1.0
        A_ub, b_ub = [], []
        for e in range(E):
            ty, ts = nv + 2 * e, nv + 2 * e + 1
            for y in EBs[e]:
                row = np.zeros(nvar); row[:4] = -y / 6480.0; row[ty] = 1.0
                A_ub.append(row); b_ub.append(0.0)
            for Lrow in S[e]:
                row = np.zeros(nvar); row[:nv] = Lrow / 6480.0; row[ts] = -1.0
                A_ub.append(row); b_ub.append(0.0)
            row = np.zeros(nvar); row[-1] = 1.0; row[ty] = -1.0; row[ts] = 1.0          # t <= ty - ts
            A_ub.append(row); b_ub.append(0.0)
        A_eq = np.zeros((1, nvar)); A_eq[0, :4] = 1.0
        bounds = [(0, None)] * 4 + [(0, 50.0)] * len(MU_INDEX) + [(None, None)] * (2 * E + 1)
        res = linprog(cvec, A_ub=np.array(A_ub), b_ub=np.array(b_ub), A_eq=A_eq, b_eq=[1.0], bounds=bounds, method="highs")
        x = res.x
        lam, mu = x[:4], x[4:nv]
        worst, viol = np.inf, 0.0
        for e in range(E):
            val, s0, tops = argmax_L(Aa[e], lam, mu, topk=topk)
            val /= 6480.0
            ty, ts = x[nv + 2 * e], x[nv + 2 * e + 1]
            worst = min(worst, ty - val)
            viol = max(viol, val - ts)
            for t in tops:
                S[e].append(L_terms(Aa[e], t))
        if best is None or worst > best[0]:
            best = (worst, lam.copy(), mu.copy())
        if r % 25 == 0 or viol < 1e-11:
            log("round %d: LP min margin %.6e  true min margin %.6e  cut violation %.3e" % (r, x[-1], worst, viol))
        if viol < 1e-11:
            break
    return best


def run_interval(c1, c2, tag):
    """If one rational (lambda, mu) gives max_s L < min_y lambda.Ebet at c1 AND at c2, it does for
    every c in [c1, c2]: for fixed multipliers every L(s) and every lambda.Ebet(y) is AFFINE in c
    (payoffs are affine in c; the tree does not depend on c), so max_s L is convex, min_y lambda.Ebet
    is concave, and their difference is concave: positive at both ends implies positive between."""
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    log = lambda s: print("[%6.0fs] %s" % (time.time() - t0, s), flush=True)
    ends = []
    for cv in (c1, c2):
        T = class_table(cv)
        Te, g = engine_table(cv)
        assert all(T[k] == Te[k] for k in T) and set(T) == set(Te)
        EB = ebet_combo(g)
        ends.append((cv, T, g, EB, build_float(T), class_ebet(g, EB)))
    log("tables cross-checked at both ends")
    margin, lam, mu = propose_joint([e[4] for e in ends], [e[5] for e in ends], log=log)
    log("joint proposer: min margin %.6e" % margin)
    rec = {"interval_c": [str(c1), str(c2)], "interval_pot": [str(3 * c1), str(3 * c2)], "mode": MODE,
           "argument": run_interval.__doc__.strip(), "proposer_min_margin_float": margin}
    if margin <= 0:
        rec["verdict"] = "no joint certificate for this interval"
        json.dump(rec, open(os.path.join(OUT, "%s.json" % tag), "w"), indent=1)
        log(rec["verdict"])
        return rec
    q = 10 ** 6
    lamQ = [F(int(round(x * q)), q) for x in lam]
    muQ = [F(int(x * q), q) for x in mu]
    rec["lambda"] = [str(x) for x in lamQ]
    rec["mu_nonzero"] = {"P%d %s %s-> %d" % (a[0] + 1, CLS[a[1]], "" if r is None else "%d " % r, t): str(muQ[m])
                         for m, (a, r, t) in enumerate(MU_INDEX) if muQ[m] != 0}
    rec["ends"] = []
    ok = True
    for cv, T, g, EB, _, _ in ends:
        Bs, smax = exact_max_L(T, lamQ, muQ)
        By, y2 = exact_min_y(g, EB, lamQ)
        log("c = %s: exact max L %.9f  exact min deterrence %.9f  certified %s" % (cv, float(Bs), float(By), Bs < By))
        rec["ends"].append({"c": str(cv), "B_s_max_L": str(Bs), "B_y_min_deterrence": str(By),
                            "exact_gap": float(By - Bs), "certified": Bs < By})
        ok &= Bs < By
    rec["certified"] = ok
    rec["verdict"] = ("CERTIFIED for every c in [%s, %s] (pot [%s, %s]): no P1-silent Nash equilibrium with a "
                      "suit-symmetric check part, for any responses to P1's bet" % (c1, c2, 3 * c1, 3 * c2)) if ok         else "no certificate after exact check"
    json.dump(rec, open(os.path.join(OUT, "%s.json" % tag), "w"), indent=1)
    log(rec["verdict"])
    return rec


if __name__ == "__main__":
    if sys.argv[1] == "interval":
        run_interval(F(sys.argv[2]), F(sys.argv[3]), sys.argv[4])
        sys.exit(0)
    if sys.argv[1] == "run":
        cv = F(sys.argv[2])
        run(cv, sys.argv[3] if len(sys.argv) > 3 else "c%s" % str(cv).replace("/", "-"))
