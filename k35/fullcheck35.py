"""EXACT check of an emptiness certificate for a region of the FULL (3,5)-Kuhn game (see fullprop35.py).

Claim checked:  max over the region's face of  Lam(s) = sum_t mu_t Delta_t(s) + sum_r lam_r BR_r(s)  < 0,
where Delta_t = u_a(s) - u_a(t, s_-a) (CCE terms, >= 0 at every Nash equilibrium) and BR_r =
u_b(rho, s_-b) - u_b(tau, s_-b) for the region's "rho is played" agents (>= 0 at every NE in the region).
Then the region holds no Nash equilibrium.  Lam is multilinear, so the max is at a pure profile of the face.
At a pure profile Lam is a sum over the 60 deals of terms depending on the 3 agents dealt.  The max is
found EXACTLY:
  * payoff-equivalent plans of an agent (identical payoffs in all its deals against all opponents) are
    merged -- Lam depends on an agent's plan only through payoffs (CCE form);
  * all P1 plan combinations are enumerated; for each, P2's five agents are assigned level by level and a
    branch is closed as soon as its EXACT upper bound  sum_l max_c sum_{k != l} (H_kl[b_k, c], or
    max_b H_kl[b, c] while b_k is unassigned)  is < 0 (H_kl = the deals' terms with P2 card k, P3 card l;
    each P3 agent only meets its own 12 deals, so it picks its plan on its own).  The claim holds iff
    every branch closes; a complete profile that survives has value >= 0 and refutes the certificate.
Integers only: one common denominator, numpy int64 under a 2^62 guard.  Payoffs from tree.py.
usage (k35/):  KUHN_CARDS=5 python fullcheck35.py <certificate.json>"""
import os, sys, json, itertools, time
os.environ.setdefault("KUHN_CARDS", "5")
import numpy as np
from fractions import Fraction as F
from math import lcm
import tree as T, kuhn3p as K

assert K.NCARDS == 5
SITS = (1, 2, 3, 4)
BITS = list(itertools.product((0, 1), repeat=4))
CARDS = list(K.CARDS)


def pure_payoff(d, plans):
    cards = T.DEALS[d]
    x = {}
    for pl in range(3):
        for s, b in zip(SITS, BITS[plans[pl]]): x[K.pidx(pl, cards[pl], s)] = b
    p = 0
    while int(T.AGGC[p]) >= 0:
        p = int(T.AGGC[p]) if x[int(T.COORD[d, p])] == 1 else int(T.PASC[p])
    return [int(round(v)) for v in T.PAYT[d, p]]


def load(path):
    c = json.load(open(path))
    faces = {tuple(int(v) for v in k.split(",")): list(vals) for k, vals in c["faces"].items()}
    brs = [((b[0], b[1]), b[2]) for b in c["brs"]]
    mu = {((pl, cd), t): F(q) for pl, cd, t, q in c["mu"]}
    # lam: index n -> (BR block in AGENTS order, tau)
    order = [(a, rho) for a in [(pl, cd) for pl in range(3) for cd in CARDS] for (b, rho) in brs if b == a]
    lam = {}
    for n, q in c["lam"]:
        a, rho = order[n // 16]; lam[(a, rho, n % 16)] = F(q)
    ce = {((pl, cd), rho, t): F(q) for pl, cd, rho, t, q in c.get("ce", [])}
    for v in list(mu.values()) + list(lam.values()) + list(ce.values()):
        if v < 0: raise SystemExit("negative multiplier")
    return c, faces, mu, lam, ce


def main(path):
    t0 = time.time()
    c, faces, mu, lam, ce = load(path)
    print("region %s: %d CCE, %d CE, %d BR multipliers, faces %s" % (c["region"], len(mu), len(ce), len(lam), faces), flush=True)
    dom = {(pl, cd): faces.get((pl, cd), list(range(16))) for pl in range(3) for cd in CARDS}
    deals = [tuple(T.DEALS[d]) for d in range(T.ND)]
    pay = {}
    for d in range(T.ND):
        j, k, l = deals[d]
        for r in itertools.product(range(16), repeat=3):
            pay[d, r] = pure_payoff(d, r)
    # 12 * term of deal d at plans r
    def term(d, r):
        v = F(0)
        for pl in range(3):
            a = (pl, deals[d][pl])
            for t in range(16):
                m = mu.get((a, t))
                if m:
                    rt = list(r); rt[pl] = t
                    v += m * (pay[d, r][pl] - pay[d, tuple(rt)][pl])
            for (aa, rho, t), m in lam.items():
                if aa == a:
                    r1 = list(r); r1[pl] = rho; r2 = list(r); r2[pl] = t
                    v += m * (pay[d, tuple(r1)][pl] - pay[d, tuple(r2)][pl])
            for t in range(16):                   # CE terms of the class the agent actually plays
                m = ce.get((a, r[pl], t))
                if m:
                    rt = list(r); rt[pl] = t
                    v += m * (pay[d, r][pl] - pay[d, tuple(rt)][pl])
        return v
    # merge payoff-equivalent plans within each agent's domain
    rep = {}
    for (pl, cd), allowed in dom.items():
        ds = [d for d in range(T.ND) if deals[d][pl] == cd]
        sig = {}
        for p in allowed:
            key = []
            for d in ds:
                for r in itertools.product(range(16), repeat=2):
                    rr = list(r); rr.insert(pl, p)
                    key.append(tuple(pay[d, tuple(rr)]))
            sig.setdefault(tuple(key), p)
        rep[(pl, cd)] = sorted(sig.values())
    bad = [k for k in ce if k[1] not in rep[k[0]]]
    if bad: raise SystemExit("CE multiplier on a plan that is not its class representative: %s" % bad[:3])
    print("plan classes per agent:", {"P%d c%d" % (a[0] + 1, a[1]): len(v) for a, v in rep.items()}, "(%.0fs)" % (time.time() - t0), flush=True)
    Fd = {}
    for d in range(T.ND):
        j, k, l = deals[d]
        A, B, C = rep[(0, j)], rep[(1, k)], rep[(2, l)]
        Fd[d] = [[[term(d, (a, b, cc)) for cc in C] for b in B] for a in A]
    den = 1
    for d in Fd:
        for x in Fd[d]:
            for y in x:
                for v in y: den = lcm(den, v.denominator)
    G = {}
    big = 0
    for d in Fd:
        arr = np.array([[[int(v * den) for v in y] for y in x] for x in Fd[d]], dtype=object)
        big = max(big, int(np.max(np.abs(arr))))
        G[d] = arr.astype(np.int64)
    assert big * T.ND < 2 ** 62, "int64 guard"
    print("tables built, denominator %d (%.0fs)" % (den, time.time() - t0), flush=True)
    DI = {deals[d]: d for d in range(T.ND)}
    nB = [len(rep[(1, k)]) for k in CARDS]
    P1 = list(itertools.product(*[range(len(rep[(0, j)])) for j in CARDS]))
    worst = None; closed = [0] * 6; nodes = 0
    for n, a in enumerate(P1):
        H = {}
        for k in CARDS:
            for l in CARDS:
                if k != l:
                    H[k, l] = sum(G[DI[(j, k, l)]][a[j - 1]] for j in CARDS if j not in (k, l))   # (P2-k class, P3-l class)
        Mb = {kl: h.max(axis=0) for kl, h in H.items()}
        # threshold search over P2's agents, level by level.  Bound of a partial assignment:
        #   sum_l  max_c  sum_{k != l} ( H[k,l][b_k, c] if b_k assigned else max_b H[k,l][b, c] )
        # -- exact once all five are assigned (each P3 agent then picks its best plan on its own deals)
        surv = np.zeros((1, 0), dtype=np.int64); lev = 0
        for lev, k in enumerate(CARDS):
            N = len(surv)
            cand = np.hstack([np.repeat(surv, nB[k - 1], 0), np.tile(np.arange(nB[k - 1]), N)[:, None]])
            bound = np.zeros(len(cand), dtype=np.int64)
            for l in CARDS:
                S = np.zeros((len(cand), len(rep[(2, l)])), dtype=np.int64)
                for kk in CARDS:
                    if kk == l: continue
                    S += H[kk, l][cand[:, kk - 1], :] if kk <= k else Mb[kk, l][None, :]
                bound += S.max(axis=1)
            nodes += len(cand)
            surv = cand[bound >= 0]
            if len(surv) == 0: break
        if len(surv) == 0:
            closed[lev] += 1
        else:                                     # complete profiles with exact value >= 0
            i = int(np.argmax(bound)); worst = (int(bound[i]), a, tuple(int(x) for x in cand[i])); break
        if (n + 1) % 5000 == 0:
            print("   %d/%d P1 combinations, closed at P2 level %s, %d nodes (%.0fs)" % (
                n + 1, len(P1), closed[:5], nodes, time.time() - t0), flush=True)
    if worst is None:
        print("every branch closed with an exact bound < 0: max < 0  (%d P1 combinations, closed at P2 level %s, %d nodes, %.0fs)" % (
            len(P1), closed[:5], nodes, time.time() - t0))
        print("CERTIFIED: region %s contains no Nash equilibrium" % c["region"])
        return
    m = F(worst[0], 12 * den)
    print("a pure profile of the face has value %s = %.6g >= 0  (P1 classes %s, P2 classes %s, %.0fs)" % (
        m, float(m), worst[1], worst[2], time.time() - t0))
    print("NOT a certificate (max >= 0)")


if __name__ == "__main__":
    main(sys.argv[1])
