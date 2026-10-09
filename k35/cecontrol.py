"""Controls for the (3,5) silent certificate (ceverify.py / ceverify2.py):
  1. the certificate function L agrees between the exact checker's tables and the float proposer
     (cceprop35.terms) at random pure profiles (same multipliers, so to float rounding);
  2. at the 7 polished restricted equilibria (silent35b.json), L(family) lies between V_5 = 2.194111
     and the exact maximum (the family is an NE of G_c, so u_1 <= L there, and L <= max over the cube);
  3. the exact maximiser's plans, printed, and L there recomputed by the proposer.
usage (k35/):  KUHN_CARDS=5 python cecontrol.py <certificate.json> [maximiser json]
(the proposer's per-tau multipliers are recovered from the CCE-form certificate: mu[rho, tau] = mu_tau)"""
import os, sys, json
os.environ.setdefault("KUHN_CARDS", "5")
import numpy as np
from fractions import Fraction as F
import ceverify as A, cceprop35 as P, kuhn3p as K, tree as T

cert = json.load(open(sys.argv[1]))
mu = {}
for pl, c, rho, tau, q in cert["mu"]:
    mu[((pl, c), A.PLANS[pl].index(tuple(rho)), A.PLANS[pl].index(tuple(tau)))] = F(q)
Fd = A.build(mu)
mf = np.zeros(P.NT)                       # per-tau multipliers for the proposer's float L
for t, (pl, c, plan) in enumerate(P.PLANS):
    tb = tuple(plan[K.pidx(pl, c, s)] for s in P.SITS[pl])
    vals = {v for (a, r, tt), v in mu.items() if a == (pl, c) and A.PLANS[pl][tt] == tb}
    assert len(vals) <= 1, "not a CCE-form certificate"
    mf[t] = float(vals.pop()) if vals else 0.0


def exactL(plans):
    tot = F(0)
    for d in range(T.ND):
        cards = T.DEALS[d]
        tot += Fd[d][tuple(plans[(pl, cards[pl])] for pl in range(3))]
    return tot / 12


def to_X(plans):
    X = np.zeros((1, K.NPARAM))
    for (pl, c), r in plans.items():
        for s, b in zip(A.SITS[pl], A.PLANS[pl][r]): X[0, K.pidx(pl, c, s)] = b
    return X


rng = np.random.default_rng(5); worst = 0.0
for _ in range(300):
    plans = {(pl, c): int(rng.integers(0, len(A.PLANS[pl]))) for pl in range(3) for c in K.CARDS}
    worst = max(worst, abs(float(exactL(plans)) - float(P.L(to_X(plans), mf)[0])))
print("1. random pure profiles: max |exact L - proposer's float L| = %.2e" % worst)

sys.path.insert(1, "..")
from cert35gen import kgen_to_k35
for e in json.load(open("../silent35b.json")):
    if max(e["sub_expl"]) < 1e-12:
        p = np.array(kgen_to_k35(e["profile"]), float); p[P.OPEN] = 0.0
        o, D = P.terms(p[None])
        print("2. family seed %2d: V_5 = %.6f <= L = %.6f  (min bracket %.1e)" % (e["seed"], o[0], o[0] + D[0] @ mf, D.min()))

if len(sys.argv) > 2:
    arg = json.loads(sys.argv[2])
    plans = {(pl, c): arg["P%d" % (pl + 1)][c - 1] for pl in range(3) for c in K.CARDS}
    print("3. at the exact maximiser: exact L = %s = %.6f, proposer L = %.6f" % (
        exactL(plans), float(exactL(plans)), float(P.L(to_X(plans), mf)[0])))
    names = {0: ("KKB call", "KBF call", "KBC call"), 1: ("K bet", "KKBF call", "KKBC call"), 2: ("KK bet", "KB call")}
    for pl in range(3):
        print("   P%d" % (pl + 1), "; ".join("card %d: %s" % (c, ",".join(n for n, b in zip(names[pl], A.PLANS[pl][plans[(pl, c)]]) if b) or "-")
                                      for c in K.CARDS))
