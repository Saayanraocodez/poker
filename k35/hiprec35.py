"""High-precision refinement of the (3, 5) equilibrium found by polish35 (seeds 0, 3, 6, 8, 12, 13, 14),
and integer-relation guesses for its coordinates.  Uses k35's own tree (not kuhnGen).  Nothing here is
a proof: it produces CANDIDATE exact values for an exact verification.
usage (from k35/):  KUHN_CARDS=5 python hiprec35.py ../polish35_candidates.json [digits]"""
import os, sys, json
os.environ.setdefault("KUHN_CARDS", "5")
import mpmath as mp
import tree as T, kuhn3p as K

NP = K.NPARAM; ND = T.ND
INT = [int(x) for x in T.INTERNAL]; AGGC = [int(x) for x in T.AGGC]; PASC = [int(x) for x in T.PASC]
LEAF = [int(x) for x in T.LEAFPOS]
OWNER = [None] * NP
for _pl in range(3):
    for _j in K.CARDS:
        for _s in K.SITUATIONS: OWNER[K.pidx(_pl, _j, _s)] = _pl


def utilities(p):
    tot = [mp.mpf(0)] * 3
    for d in range(ND):
        V = {}
        for pos in LEAF: V[pos] = [mp.mpf(int(T.PAYT[d, pos, k])) for k in range(3)]
        for pos in reversed(INT):
            x = p[int(T.COORD[d, pos])]
            V[pos] = [(1 - x) * V[PASC[pos]][k] + x * V[AGGC[pos]][k] for k in range(3)]
        for k in range(3): tot[k] += V[0][k]
    return [t / ND for t in tot]


def F(p, S):
    """du_owner / dp_i for i in S (exact for a multilinear u: u(x_i = 1) - u(x_i = 0))"""
    out = []
    for i in S:
        a = list(p); b = list(p); a[i] = mp.mpf(1); b[i] = mp.mpf(0)
        out.append(utilities(a)[OWNER[i]] - utilities(b)[OWNER[i]])
    return out


def newton(p, S, iters=40):
    for it in range(iters):
        f = F(p, S); nf = max(abs(x) for x in f)
        print("   newton %2d  max|F| %s" % (it, mp.nstr(nf, 5)), flush=True)
        if nf < mp.mpf(10) ** (-(mp.mp.dps - 8)): break
        J = mp.matrix(len(S), len(S))
        for c, j in enumerate(S):
            a = list(p); b = list(p); a[j] = mp.mpf(1); b[j] = mp.mpf(0)
            fa, fb = F(a, S), F(b, S)
            for r in range(len(S)): J[r, c] = fa[r] - fb[r]
        step = mp.lu_solve(J, mp.matrix(f))
        for c, j in enumerate(S): p[j] = p[j] - step[c]
    return p


if __name__ == "__main__":
    mp.mp.dps = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    c = json.load(open(sys.argv[1]))[0]
    p = [mp.mpf(x) for x in c["float_profile_k35"]]
    S = [k for k in range(NP) if 1e-9 < float(p[k]) < 1 - 1e-9]
    for k in range(NP):                       # pure coordinates exactly 0 / 1; off-path ones as the float profile has them
        if k not in S and (float(p[k]) < 1e-9 or float(p[k]) > 1 - 1e-9): p[k] = mp.mpf(round(float(p[k])))
    print("%d interior coordinates, %d digits" % (len(S), mp.mp.dps), flush=True)
    p = newton(p, S)
    names = {K.pidx(pl, j, s): "%s%d%d" % ("abc"[pl], j, s) for pl in range(3) for j in K.CARDS for s in K.SITUATIONS}
    out = {}
    for k in S:
        guess = None
        for deg in range(1, 9):
            r = mp.findpoly(p[k], deg, maxcoeff=10 ** 12, tol=mp.mpf(10) ** (-(mp.mp.dps - 15)))
            if r: guess = r; break
        out[names[k]] = {"value": mp.nstr(p[k], mp.mp.dps - 5), "minpoly": guess}
        print("%s = %s   minimal polynomial guess (degree %s): %s" % (names[k], mp.nstr(p[k], 30), len(guess) - 1 if guess else "-", guess), flush=True)
    json.dump({"interior": [names[k] for k in S], "coords": out, "profile": [mp.nstr(x, mp.mp.dps - 5) for x in p]},
              open("hiprec35.json", "w"), indent=1)
