"""(3,5)-Kuhn: the DETERRENCE CUT, exact.  No float anywhere.

Setting.  In a profile where P1 never opens, the 15 responses to a bet (P2's call after B, P3's calls
after BF / BC, per own card) are off the path.  After P1 bets P1 never acts again, so P1's value of
opening with card j is Ebet(j; y), a function of those 15 responses y alone, and opening is no better
than checking iff  Ebet(j; y) <= V_j,  where V_j is P1's (best) value of checking with card j.

Claims.  For every y in [0,1]^15:
    (A)  3 Ebet(1; y) + 8 Ebet(5; y) >= 16,        (B)  3 Ebet(2; y) + 8 Ebet(5; y) >= 16.
In the restricted game P1 never bets, so with card 1 P1 can only reach showdowns, which card 1 always
loses: folding everything gives -1 and every call is worse, so V_1 = -1 exactly.  Hence (A) gives
    every deterrable V has  8 V_5 >= 16 + 3 = 19,  i.e.  V_5 >= 19/8,
a condition on P1's value with the TOP card alone; (B) gives 3 V_2 + 8 V_5 >= 16.  Interpretation of
(A): P1's deviation "open 5 always, open 1 at rate 3/8" gains at least (19 - 8 V_5)/40 against EVERY
response to a bet.

Proof (computed here).  Ebet(j; y) is a sum over the 12 deals of P1's payoff below the bet, a product
along the path of factors y or 1 - y of DISTINCT coordinates (P2's and P3's), so it is affine in each
coordinate separately; so is the weighted sum, whose minimum over the cube is therefore attained at a
vertex.  We evaluate it at all 2^15 = 32768 vertices in exact rationals, from the game tree (tree.py),
and independently from the closed-form payoff table below; both must agree at every vertex.

The weights are LP optima over (lam_1..lam_5) of min_y sum_j lam_j (Ebet(j; y) - V_j) at the
restricted equilibria found numerically (silent35b.json: V = (-1, -1, -0.676, 0.155, 2.194)); they are
only a choice -- the claim above is proved for them exactly, whatever produced them.
usage (k35/):  KUHN_CARDS=5 python deter35.py"""
import os, sys, itertools
os.environ.setdefault("KUHN_CARDS", "5")
from fractions import Fraction as F
import tree as T, kuhn3p as K

assert K.NCARDS == 5
CARDS = list(K.CARDS)
RESP = [K.pidx(1, c, 2) for c in CARDS] + [K.pidx(2, c, 3) for c in CARDS] + [K.pidx(2, c, 4) for c in CARDS]
BET_SUB = [1, 3, 4]                    # internal positions below P1's bet: P2 (B), P3 (BC), P3 (BF)


def ebet_tree(j, x):
    """P1's mean payoff after betting with card j, from the tree; x: dict coordinate -> Fraction"""
    tot = F(0); n = 0
    for d, cards in enumerate(T.DEALS):
        if cards[0] != j: continue
        n += 1
        V = {}
        for p in [int(q) for q in T.LEAFPOS]: V[p] = F(int(T.PAYT[d, p, 0]))
        for p in reversed(BET_SUB):
            c = int(T.COORD[d, p]); assert c in RESP
            V[p] = x[c] * V[int(T.AGGC[p])] + (1 - x[c]) * V[int(T.PASC[p])]
        tot += V[1]
    return tot / n


def ebet_table(j, beta, phi, psi):
    """the same from the payoff table: both fold +2; one caller: +3 / -2; both call: +4 / -2"""
    s = F(0); n = 0
    for k in CARDS:
        for l in CARDS:
            if len({j, k, l}) < 3: continue
            n += 1
            b, f, c = beta[k], phi[l], psi[l]
            s += ((1 - b) * (1 - f) * 2 + (1 - b) * f * (3 if j > l else -2)
                  + b * (1 - c) * (3 if j > k else -2) + b * c * (4 if j > k and j > l else -2))
    return s / n


if __name__ == "__main__":
    CUTS = [{1: F(3), 5: F(8)}, {2: F(3), 5: F(8)}]; BOUND = F(16)
    best = [None] * len(CUTS); argmin = [[] for _ in CUTS]; nv = 0
    for bits in itertools.product((0, 1), repeat=15):
        x = {RESP[i]: F(bits[i]) for i in range(15)}
        beta = {c: x[K.pidx(1, c, 2)] for c in CARDS}
        phi = {c: x[K.pidx(2, c, 3)] for c in CARDS}
        psi = {c: x[K.pidx(2, c, 4)] for c in CARDS}
        e = {}
        for j in CARDS:
            e[j] = ebet_tree(j, x)
            assert e[j] == ebet_table(j, beta, phi, psi), (bits, j)
        nv += 1
        for n, LAM in enumerate(CUTS):
            val = sum(LAM[j] * e[j] for j in LAM)
            if best[n] is None or val < best[n]: best[n] = val; argmin[n] = [bits]
            elif val == best[n]: argmin[n].append(bits)
    print("vertices %d: tree and table agree at every vertex for all 5 cards" % nv)
    for n, LAM in enumerate(CUTS):
        name = " + ".join("%s Ebet(%d)" % (LAM[j], j) for j in LAM)
        print("min over the cube of %s = %s  (attained at %d vertices)  CLAIM %s" % (
            name, best[n], len(argmin[n]), "PROVED" if best[n] >= BOUND else "FAILS"))
    print("=> every deterrable V has V_5 >= (16 + 3)/8 = %s (using V_1 = -1), and 3 V_2 + 8 V_5 >= 16" % ((BOUND + 3) / 8))
    # a non-vertex sanity point: the affine-in-each-coordinate structure (random rationals)
    import random
    rnd = random.Random(1)
    for _ in range(200):
        x = {c: F(rnd.randint(0, 997), 997) for c in RESP}
        for n, LAM in enumerate(CUTS):
            v = sum(LAM[j] * ebet_tree(j, x) for j in LAM)
            assert v >= best[n], "interior point below the vertex minimum"
    print("200 random rational interior points: all >= the vertex minimum")
