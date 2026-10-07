"""EXACT Nash verification for (3, n)-Kuhn profiles, independent of the search (kuhnGen / cfrGen /
certify / polish35): the game is k35's own tree (tree.py over kuhn3p with KUHN_CARDS), and all
arithmetic is in Fractions.

A profile p (NP = 12 n behaviour coordinates, rationals) is a Nash equilibrium iff for every player
i, u_i(p) equals i's best-response value.  Utility is a sum over deals, and a player's coordinates
for own card j only affect the deals in which the player holds j, so the best response decomposes
by own card: for each card, maximise over the 2^4 pure plans of the player's four situations.
EXACT exploitability 0 for all three players = an exact Nash equilibrium.

Before anything else, the coordinate MAPPING from kuhnGen's order (the search) to k35's order (this
file) is checked: kuhnGen's utilities and this file's must agree on random profiles.
usage (from k35/):  KUHN_CARDS=5 python xeq35.py ../polish35_candidates.json"""
import os, sys, json, itertools, random
os.environ.setdefault("KUHN_CARDS", "5")
from fractions import Fraction as F
import tree as T, kuhn3p as K

NP = K.NPARAM; ND = T.ND
INT = [int(x) for x in T.INTERNAL]; AGGC = [int(x) for x in T.AGGC]; PASC = [int(x) for x in T.PASC]
LEAF = [int(x) for x in T.LEAFPOS]


def deal_values(p, d):
    """exact continuation values (3 players) at the root of deal d"""
    V = {}
    for pos in LEAF: V[pos] = [F(int(T.PAYT[d, pos, k])) for k in range(3)]
    for pos in reversed(INT):
        x = p[int(T.COORD[d, pos])]
        V[pos] = [(1 - x) * V[PASC[pos]][k] + x * V[AGGC[pos]][k] for k in range(3)]
    return V[0]


def utilities(p):
    tot = [F(0)] * 3
    for d in range(ND):
        v = deal_values(p, d)
        for k in range(3): tot[k] += v[k]
    return [t / ND for t in tot]


def best_response(p, i):
    total = F(0)
    for j in K.CARDS:
        deals = [d for d in range(ND) if T.DEALS[d][i] == j]
        own = [K.pidx(i, j, s) for s in K.SITUATIONS]
        best = None
        for bits in itertools.product((F(0), F(1)), repeat=len(own)):
            q = list(p)
            for c, b in zip(own, bits): q[c] = b
            v = sum(deal_values(q, d)[i] for d in deals)
            if best is None or v > best: best = v
        total += best
    return total / ND


def exploitability(p):
    u = utilities(p)
    return [best_response(p, i) - u[i] for i in range(3)], u


def mapping_check(trials=20):
    sys.path.insert(1, "..")
    import kuhnGen as Q
    g = Q.Kuhn(3, K.NCARDS)
    rnd = random.Random(1); worst = 0.0
    for _ in range(trials):
        pg = [rnd.random() for _ in range(g.nparam)]
        pk = [None] * NP
        for pl in range(3):
            for j in g.cards:
                for h in g.sit_hist[pl]:
                    pk[K.pidx(pl, j, Q.SGS_SIT[pl][h])] = F(pg[g.pidx(pl, j, h)])
        ug = g.utilities(pg); uk = utilities(pk)
        worst = max(worst, max(abs(float(uk[k]) - ug[k]) for k in range(3)))
    return worst


if __name__ == "__main__":
    w = mapping_check()
    print("mapping kuhnGen -> k35: max utility difference over 20 random profiles %.1e  %s" % (w, "OK" if w < 1e-12 else "*** MAPPING WRONG"), flush=True)
    if w >= 1e-12: sys.exit(1)
    cands = json.load(open(sys.argv[1]))
    for c in cands:
        p = [F(x) for x in c["k35"]]
        assert len(p) == NP and all(0 <= x <= 1 for x in p)
        e, u = exploitability(p)
        opens = [p[K.pidx(0, j, 1)] for j in K.CARDS]
        ok = all(x == 0 for x in e)
        print("seed %2s: exact exploitability %s  -> %s;  P1 opens %s;  u = %s" % (
            c.get("seed"), [str(x) for x in e], "EXACT NASH EQUILIBRIUM" if ok else "not an equilibrium",
            [str(x) for x in opens], [str(x) for x in u]), flush=True)
