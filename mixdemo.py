"""Why can a CFR average sit OFF the Nash set with tiny exploitability?  Because CFR averages
strategies in SEQUENCE FORM (each player's play weighted by that player's own reach), and the Nash
set of three-player Kuhn poker is not convex: the average of two equilibria from different
sub-families is not an equilibrium, yet it is a good approximation of one.

Exact demonstration: two exact SGS equilibria, x_A (sub-family A) and x_C (sub-family C); their
sequence-form mixture m(lam) for lam in [0, 1]; for each m: exploitability EXACTLY (Fractions, exact
best responses as in reread14b.xnash) and the certified distance to the complete Nash set
(reread14.certify).

usage:  python mixdemo.py   -> log_mixdemo.txt (stdout)
"""
from fractions import Fraction as F
import numpy as np
import kuhn3p as K, seqset, reread14 as R, reread14b as B

I = K.NAME_IDX; NAME = K.PARAM_NAME


def own_reach(x, i):
    """reach of coordinate i's information set by its owner's OWN earlier choices (Fractions)."""
    pl, j, k = i // 16, (i % 16) // 4 + 1, i % 4 + 1
    a = lambda s: x[K.pidx(pl, j, s)]
    if pl == 0:   # P1: 1 root; 2 KKB, 3 KBF, 4 KBC all after own check
        return F(1) if k == 1 else 1 - a(1)
    if pl == 1:   # P2: 1 after K, 2 after B (first move); 3 KKBF, 4 KKBC after own check
        return F(1) if k in (1, 2) else 1 - a(1)
    return F(1)   # P3: every set is a first move (KK, KB, BF, BC)


def mix(xs, ws):
    """sequence-form mixture: behaviour at each set = own-reach-weighted average."""
    out = []
    for i in range(48):
        num = sum(w * own_reach(x, i) * x[i] for x, w in zip(xs, ws))
        den = sum(w * own_reach(x, i) for x, w in zip(xs, ws))
        out.append(num / den if den else xs[0][i])
    return out


def main():
    off = {"b32": F(0), "c33": F(5, 8), "c34": F(0)}
    xA = seqset.family_point(F(1, 20), F(1, 5), F(0), F(0), off)          # A: c11 = 0, b11 <= b21
    xC = seqset.family_point(F(1, 5), F(1, 20), F(0), F(1, 2), off)       # C: c11 = 1/2, b21 <= b11
    L, fam = R.leaves(); IDS = R.identities(); RG = R.ranges()
    boxes = {k: R.leaf_box(k, L[k], RG) for k in fam}
    for nm, x in (("x_A", xA), ("x_C", xC)):
        assert B.xnash(x) == 0, nm
    print("two exact equilibria (verified: exact exploitability 0):")
    for nm, x in (("x_A", xA), ("x_C", xC)):
        print("   %s: b11 = %s, b21 = %s, c11 = %s, c21 = %s, b33 = %s, b41 = %s;  u = %s" % (
            nm, x[I["b11"]], x[I["b21"]], x[I["c11"]], x[I["c21"]], x[I["b33"]], x[I["b41"]],
            tuple(str(v) for v in K.utilities_exact(x))))
    print("\nsequence-form mixture m = (1-lam) x_A + lam x_C (what an average over iterations computes):")
    print("   lam     b11      b21      c11      b33      exploitability (exact)     dist to Nash set (certified)")
    for lam in (F(0), F(1, 10), F(1, 4), F(1, 2), F(3, 4), F(9, 10), F(1)):
        m = mix([xA, xC], [1 - lam, lam])
        e = B.xnash(m)
        d = min(R.certify(np.array([float(v) for v in m]), *boxes[k], IDS[k])[0] for k in fam)
        print("   %-5s  %.4f   %.4f   %.4f   %.4f   %-14s = %.2e      %.4f" % (
            lam, m[I["b11"]], m[I["b21"]], m[I["c11"]], m[I["b33"]], e, float(e), float(d)))


if __name__ == "__main__":
    main()
