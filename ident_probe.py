"""Feasibility probe for research question 10 (identifiability from partial observation).

Observation model: an observer sees the public action history and, at a showdown (>= 2 players
still in), the cards of the players still in.  A seated observer also sees their own card.
For the SGS family on path (b11, b21, b23, c11; c21 = 1/2 - c11, b33, b41 from Table 3), compute
in exact arithmetic (sympy rationals):
  * the Jacobian rank of the observation distribution w.r.t. each sub-family's free on-path
    parameters (full rank = locally identifiable);
  * the total-variation distance between the observation distributions of the two exact
    equilibria of mixdemo.py (x_A, x_C: same payoffs);
  * the per-hand Fisher information for beta (planning numbers for question 1).
"""
import sys
sys.path.insert(0, r"C:\Users\raosa\OneDrive\Documents\poker")
from fractions import Fraction as F
import sympy as sp
import kuhn3p as K

b11, b21, b23, c11 = sp.symbols("b11 b21 b23 c11")
I = K.NAME_IDX


def profile(sub, offpath=F(1, 2)):
    beta = b21 if sub == "A" else b11
    p = {}
    for n in ("a12", "a13", "a14", "a24", "b12", "b13", "b14", "b24", "c12", "c13", "c14", "c24"):
        p[n] = 0
    for n in ("a42", "a43", "a44", "b42", "b43", "b44", "c42", "c43", "c44"):
        p[n] = 1
    for n in ("a11", "a21", "a22", "a23", "a31", "a32", "a34", "a41"):
        p[n] = 0
    p["a33"] = sp.Rational(1, 2)
    p.update(b11=b11, b21=b21, b22=0, b23=b23, b31=0, b34=0,
             b33=sp.Rational(1, 2) + (b11 + b21) / 2 + beta / 2 - b23 * (1 - b21),
             b41=2 * b11 + 2 * b21)
    p.update(c11=c11, c21=sp.Rational(1, 2) - c11, c22=0, c23=0, c31=0, c32=0, c41=1)
    # off path (P1 never bets): b32, c33, c34 -- irrelevant to every observation
    p.update(b32=sp.Rational(offpath), c33=sp.Rational(offpath), c34=sp.Rational(offpath))
    return [sp.sympify(p[K.PARAM_NAME[i]]) for i in range(K.NPARAM)]


def obs_dist(prof, observer):
    """observer: 0,1,2 = seated player, None = spectator."""
    dist = {}
    for d, factors, pay in K.ROWS:
        pr = sp.Rational(1, 24)
        hist, folded = [], [False] * 3
        for idx, agg in factors:
            x = prof[idx]
            pr *= x if agg else (1 - x)
            pl, sit = idx // 16, idx % 4 + 1
            hist.append((pl, sit, agg))
            if sit != 1 and not agg:
                folded[pl] = True
        live = [i for i in range(3) if not folded[i]]
        shown = tuple((i, d[i]) for i in live) if len(live) >= 2 else ()
        own = d[observer] if observer is not None else None
        key = (own, tuple(hist), shown)
        dist[key] = dist.get(key, 0) + pr
    return dist


SUBS = {  # sub-family: (free on-path params, interior point)
    "A": ((b11, b21), {b11: sp.Rational(1, 20), b21: sp.Rational(1, 5), b23: 0, c11: 0}),
    "B": ((b11, c11), {b11: sp.Rational(1, 8), b21: sp.Rational(1, 8), b23: 0, c11: sp.Rational(1, 4)}),
    "C": ((b11, b21, b23), {b11: sp.Rational(1, 5), b21: sp.Rational(1, 20), b23: sp.Rational(1, 40),
                            c11: sp.Rational(1, 2)}),
}
OBS = [("P1", 0), ("P2", 1), ("P3", 2), ("spectator", None)]

print("Jacobian rank of the observation distribution w.r.t. free on-path parameters (exact)")
for sub, (free, pt) in SUBS.items():
    prof = profile(sub)
    if sub == "B":   # b21 = b11 on B
        prof = [e.subs(b21, b11) for e in prof]
    for name, ob in OBS:
        dist = obs_dist(prof, ob)
        rows = [[sp.diff(v, t).subs(pt) for t in free] for v in dist.values()]
        r = sp.Matrix(rows).rank()
        print("  sub-family %s  observer %-9s  rank %d of %d   (%d observation classes)"
              % (sub, name, r, len(free), len(dist)))

print("\nmixdemo pair: x_A (b11=1/20,b21=1/5,c11=0) vs x_C (b11=1/5,b21=1/20,c11=1/2), same payoffs")
pA = [sp.sympify(e).subs({b11: sp.Rational(1, 20), b21: sp.Rational(1, 5), b23: 0, c11: 0})
      for e in profile("A")]
pC = [sp.sympify(e).subs({b11: sp.Rational(1, 5), b21: sp.Rational(1, 20), b23: 0, c11: sp.Rational(1, 2)})
      for e in profile("C")]
for name, ob in OBS:
    dA, dC = obs_dist(pA, ob), obs_dist(pC, ob)
    keys = set(dA) | set(dC)
    tv = sum(abs(dA.get(k, 0) - dC.get(k, 0)) for k in keys) / 2
    # per-hand KL (nats) -> hands for a likelihood-ratio test with error ~ e^-3
    kl = sum(float(dA[k]) * float(sp.log(dA[k] / dC[k])) for k in dA if dA[k] != 0 and dC.get(k, 0) != 0)
    inf = any(dA[k] != 0 and dC.get(k, 0) == 0 for k in dA)
    print("  observer %-9s  TV = %s = %.5f   KL(A||C) = %s per hand"
          % (name, tv, float(tv), "inf" if inf else "%.5f" % kl))

print("\nFisher information for beta along sub-family A (b21 = beta, b11 fixed), per hand")
prof = profile("A")
pt = {b11: sp.Rational(1, 20), b21: sp.Rational(1, 5), b23: 0, c11: 0}
for name, ob in OBS:
    dist = obs_dist(prof, ob)
    fi = sum((sp.diff(v, b21).subs(pt)) ** 2 / v.subs(pt) for v in dist.values() if v.subs(pt) != 0)
    n = (1.96 / 0.01) ** 2 / float(fi)
    print("  observer %-9s  I(beta) = %.5f   hands to pin beta to +-0.01 (95%%): ~%.0f"
          % (name, float(fi), n))
