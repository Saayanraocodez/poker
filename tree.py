"""Explicit 25-position game tree, shared shape across all 24 deals.

Positions (parent index < child index):
 0 P1.s1 root      ->  1(B)   2(K)
 1 P2.s2 (B)       ->  3(C)   4(F)
 2 P2.s1 (K)       ->  5(B)   6(K)
 3 P3.s4 (BC)      ->  7      8
 4 P3.s3 (BF)      ->  9     10
 5 P3.s2 (KB)      -> 11     12
 6 P3.s1 (KK)      -> 13     14(KKK)
11 P1.s4 (KBC)     -> 15     16
12 P1.s3 (KBF)     -> 17     18
13 P1.s2 (KKB)     -> 19     20
19 P2.s4 (KKBC)    -> 21     22
20 P2.s3 (KKBF)    -> 23     24
leaves: 7 8 9 10 14 15 16 17 18 21 22 23 24
"""
import itertools
import numpy as np
import kuhn3p as K

NPOS = 25
AGGC = -np.ones(NPOS, dtype=np.int64)
PASC = -np.ones(NPOS, dtype=np.int64)
for _p, _a, _q in [(0,1,2),(1,3,4),(2,5,6),(3,7,8),(4,9,10),(5,11,12),(6,13,14),
                   (11,15,16),(12,17,18),(13,19,20),(19,21,22),(20,23,24)]:
    AGGC[_p], PASC[_p] = _a, _q
INTERNAL = np.array([p for p in range(NPOS) if AGGC[p] >= 0])
LEAFPOS  = np.array([p for p in range(NPOS) if AGGC[p] < 0])

# (player, situation) owning each internal position
OWNER = {0:(0,1), 1:(1,2), 2:(1,1), 3:(2,4), 4:(2,3), 5:(2,2), 6:(2,1),
         11:(0,4), 12:(0,3), 13:(0,2), 19:(1,4), 20:(1,3)}
# leaf -> (contributions, folded)
LEAF = {7:([2,2,2],[0,0,0]),  8:([2,2,1],[0,0,1]),
        9:([2,1,2],[0,1,0]), 10:([2,1,1],[0,1,1]),
       14:([1,1,1],[0,0,0]),
       15:([2,2,2],[0,0,0]), 16:([1,2,2],[1,0,0]),
       17:([2,2,1],[0,0,1]), 18:([1,2,1],[1,0,1]),
       21:([2,2,2],[0,0,0]), 22:([2,1,2],[0,1,0]),
       23:([1,2,2],[1,0,0]), 24:([1,1,2],[1,1,0])}

DEALS = list(itertools.permutations(K.CARDS, 3))
ND = len(DEALS)                       # 24

COORD = -np.ones((ND, NPOS), dtype=np.int64)
PAYT  = np.zeros((ND, NPOS, 3))
for d, cards in enumerate(DEALS):
    for pos, (pl, sit) in OWNER.items():
        COORD[d, pos] = K.pidx(pl, cards[pl], sit)
    for pos, (contrib, folded) in LEAF.items():
        pot = sum(contrib)
        live = [i for i in range(3) if not folded[i]]
        win = max(live, key=lambda i: cards[i])
        pay = [-contrib[i] for i in range(3)]
        pay[win] += pot
        PAYT[d, pos] = pay
KAP = K.KAPPA

# --------------------------------------------------------------- exact ------
def tree_util(p):
    p = np.asarray(p, float)
    V = np.zeros((ND, NPOS, 3))
    V[:, LEAFPOS] = PAYT[:, LEAFPOS]
    for pos in INTERNAL[::-1]:
        x = p[COORD[:, pos]][:, None]
        V[:, pos] = x * V[:, AGGC[pos]] + (1 - x) * V[:, PASC[pos]]
    return KAP * V[:, 0].sum(axis=0)

def tree_grad(p):
    """(48,3): du_t/dp_i  -- exact, via reach x value-difference."""
    p = np.asarray(p, float)
    V = np.zeros((ND, NPOS, 3))
    V[:, LEAFPOS] = PAYT[:, LEAFPOS]
    for pos in INTERNAL[::-1]:
        x = p[COORD[:, pos]][:, None]
        V[:, pos] = x * V[:, AGGC[pos]] + (1 - x) * V[:, PASC[pos]]
    R = np.zeros((ND, NPOS)); R[:, 0] = 1.0
    for pos in INTERNAL:
        x = p[COORD[:, pos]]
        R[:, AGGC[pos]] = R[:, pos] * x
        R[:, PASC[pos]] = R[:, pos] * (1 - x)
    G = np.zeros((48, 3))
    for pos in INTERNAL:
        dv = (V[:, AGGC[pos]] - V[:, PASC[pos]]) * R[:, pos][:, None]
        np.add.at(G, COORD[:, pos], KAP * dv)
    return G
