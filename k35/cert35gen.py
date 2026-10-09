"""GENERAL exact certificate for a float equilibrium of (3, 5)-Kuhn whose interior system is SQUARE AND
NONSINGULAR (no free directions): high-precision Newton (mpmath), then exact Krawczyk on the |S|
interior conditions over a box of radius 10^-R, then the one-shot D-condition of all 60 coordinates
over the box (=> Nash), then P1's opening coordinates.  Exact Fractions, own dict polynomials (the same
helpers as cert35check, no sympy).  Refuses if the Jacobian is singular (then a reduction like
cert35's is needed).
usage (from k35/):  KUHN_CARDS=5 python cert35gen.py ../q2_polish35.json <entry index> [digits] [R] [name=p/q ...]
Coordinates given as name=p/q are FIXED at that rational (free, e.g. off-path, directions); they are
then checked like pure ones: D_i must be identically 0 or of the right sign for their value."""
import os, sys, json, time
os.environ.setdefault("KUHN_CARDS", "5")
import mpmath as mp
import numpy as np
from fractions import Fraction as Fr
import cert35check as H                     # dict polynomials, tree build, interval evaluation
import tree as T, kuhn3p as K

NP = K.NPARAM


def kgen_to_k35(pg):
    sys.path.insert(1, "..")
    import kuhnGen as Q
    g = Q.Kuhn(3, K.NCARDS); out = [None] * NP
    for pl in range(3):
        for j in g.cards:
            for h in g.sit_hist[pl]:
                out[K.pidx(pl, j, Q.SGS_SIT[pl][h])] = pg[g.pidx(pl, j, h)]
    return out


def build(x, nv):
    """u[3], D[60] for profile x (dict polys over nv variables)"""
    H.NV = nv
    return H.build(x)


if __name__ == "__main__":
    t0 = time.time()
    entry = json.load(open(sys.argv[1]))[int(sys.argv[2])]
    digits = int(sys.argv[3]) if len(sys.argv) > 3 else 140
    R = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    # name=p/q : an OFF-PATH coordinate fixed at p/q (no equation; D-checked like a pure one)
    # name:=p/q: a FREE PARAMETER fixed at p/q (an interior coordinate: its condition stays an equation)
    fixed = {K.NAME_IDX[a.split("=")[0]]: Fr(a.split("=")[1]) for a in sys.argv[5:] if ":=" not in a}
    params = {K.NAME_IDX[a.split(":=")[0]]: Fr(a.split(":=")[1]) for a in sys.argv[5:] if ":=" in a}
    p = kgen_to_k35(entry["profile"])
    SA = [i for i in range(NP) if 1e-9 < p[i] < 1 - 1e-9 and i not in fixed]            # interior incl. params
    pure = {i: (fixed[i] if i in fixed else (0 if p[i] < 0.5 else 1)) for i in range(NP) if i not in SA}
    S = [i for i in SA if i not in params]                                              # the unknowns
    names = [H.NAME[i] for i in S]
    print("entry seed %s: %d interior coordinates (%d unknowns %s, parameters %s)" % (
        entry.get("seed"), len(SA), len(S), names, {H.NAME[i]: str(v) for i, v in params.items()}), flush=True)
    na = len(SA); nv = len(S)
    xa = [H.var(SA.index(i), na) if i in SA else H.const(pure[i], na) for i in range(NP)]
    u, D = build(xa, na)
    Fa = [H.add(H.subst_const(u[H.OWNER[i]], k, 1), H.subst_const(u[H.OWNER[i]], k, 0), -1) for k, i in enumerate(SA)]
    def red(poly):
        """substitute the parameters and keep only the unknowns' exponents"""
        for i, v in params.items(): poly = H.subst_const(poly, SA.index(i), v)
        ks = [SA.index(i) for i in S]
        return {tuple(m_[k] for k in ks): c for m_, c in poly.items()}
    u = [red(v) for v in u]; D = [red(v) for v in D]
    x = [red(v) for v in xa]
    F = [red(f) for f in Fa]
    names = [H.NAME[i] for i in SA]
    # duplicate / vanishing conditions: an interior coordinate whose condition is IDENTICAL to a kept one,
    # or identically 0, adds no equation (its condition then holds wherever the kept ones do)
    keep = []; dup = {}
    for k in range(na):
        if not F[k]: dup[k] = None; continue
        t = next((j for j in keep if F[j] == F[k]), None)
        if t is not None: dup[k] = t; continue
        keep.append(k)
    if dup: print("conditions dropped: %s" % {names[k]: ("identically 0" if t is None else "= " + names[t]) for k, t in dup.items()}, flush=True)
    if len(keep) != nv: sys.exit("%d independent conditions for %d unknowns -- fix %d more coordinate(s)" % (len(keep), nv, nv - len(keep)))
    F = [F[k] for k in keep]
    J = [[H.diff(f, k) for k in range(nv)] for f in F]
    # ---- high-precision Newton on the exact polynomials
    mp.mp.dps = digits
    def mpeval(poly, pt):
        v = mp.mpf(0)
        for m_, c in poly.items():
            t = mp.mpf(c.numerator) / c.denominator
            for xx, e in zip(pt, m_):
                if e: t *= xx ** e
            v += t
        return v
    y = [mp.mpf(p[i]) for i in S]
    for it in range(60):
        f = [mpeval(g, y) for g in F]; nf = max(abs(v) for v in f)
        if nf < mp.mpf(10) ** -(digits - 10): break
        Jm = mp.matrix([[mpeval(J[a][b], y) for b in range(nv)] for a in range(nv)])
        step = mp.lu_solve(Jm, mp.matrix(f))
        y = [y[k] - step[k] for k in range(nv)]
    sv = mp.svd_r(mp.matrix([[mpeval(J[a][b], y) for b in range(nv)] for a in range(nv)]), compute_uv=False)
    print("Newton: %d iterations, max|F| %s; Jacobian singular values min %s max %s" % (
        it, mp.nstr(nf, 3), mp.nstr(min(sv), 4), mp.nstr(max(sv), 4)), flush=True)
    if min(sv) < mp.mpf(10) ** -20: sys.exit("Jacobian singular: free directions -- needs a reduction")
    if not all(0 < v < 1 for v in y): sys.exit("solution leaves the cube")
    # ---- Krawczyk, exact
    m = [Fr(str(mp.nstr(v, digits - 5))) for v in y]
    r = Fr(1, 10 ** R); Y = [(v - r, v + r) for v in m]
    Gm = [H.evalp(g, m) for g in F]
    Jmid = np.array([[float(H.evalp(J[a][b], m)) for b in range(nv)] for a in range(nv)])
    C = [[Fr(v).limit_denominator(10 ** 30) for v in row] for row in np.linalg.inv(Jmid).tolist()]
    JY = [[H.ival(J[a][b], Y) for b in range(nv)] for a in range(nv)]
    ok = True; worst = Fr(0)
    for a in range(nv):
        lo = hi = m[a] - sum(C[a][k] * Gm[k] for k in range(nv))
        for b in range(nv):
            plo = phi = Fr(1 if a == b else 0)
            for k in range(nv):
                jl, jh = JY[k][b]; c = C[a][k]
                if c >= 0: plo -= c * jh; phi -= c * jl
                else: plo -= c * jl; phi -= c * jh
            mag = max(abs(plo), abs(phi)); lo -= mag * r; hi += mag * r
        ok &= Y[a][0] < lo and hi < Y[a][1]; worst = max(worst, max(hi - m[a], m[a] - lo) / r)
    print("KRAWCZYK: K(Y) inside int(Y): %s  (half-width / r %.2e), max|G(m)| %.1e" % (ok, float(worst), max(abs(float(v)) for v in Gm)), flush=True)
    if not ok: sys.exit("Krawczyk fails")
    # ---- D-conditions, all 60
    bad = []
    for i in range(NP):
        if i in SA:                                       # interior (incl. parameters): own reach > 0 on Y
            d0 = next((d, pos) for d in range(T.ND) for pos in H.INT if int(T.COORD[d, pos]) == i)
            q = d0[1]
            while q in H.PAR:
                rr, agg = H.PAR[q]; c = int(T.COORD[d0[0], rr])
                if H.OWNER[c] == H.OWNER[i]:
                    f = x[c] if agg else H.add(H.const(1, nv), x[c], -1)
                    if not H.ival(f, Y)[0] > 0: bad.append("%s own reach" % H.NAME[i])
                q = rr
            continue
        if not D[i]: continue
        twin = [k for k in SA if H.OWNER[k] == H.OWNER[i] and D[k] == D[i]]
        if twin:                                         # D_i IS D_k as a polynomial, and D_k(y*) = 0 (k interior)
            print("   %s: D identical to interior %s's D, so D = 0 at the solution" % (H.NAME[i], H.NAME[twin[0]]), flush=True)
            continue
        lo_, hi_ = H.ival(D[i], Y)
        if 0 < pure[i] < 1: bad.append("%s fixed at %s but D not identically 0: [%.2e, %.2e]" % (H.NAME[i], pure[i], float(lo_), float(hi_))); continue
        if pure[i] == 0 and not hi_ < 0: bad.append("%s=0: D in [%.2e, %.2e]" % (H.NAME[i], float(lo_), float(hi_)))
        if pure[i] == 1 and not lo_ > 0: bad.append("%s=1: D in [%.2e, %.2e]" % (H.NAME[i], float(lo_), float(hi_)))
    print("D-conditions: %d violations %s" % (len(bad), bad), flush=True)
    opens = {H.NAME[K.pidx(0, j, 1)]: (float(Y[S.index(K.pidx(0, j, 1))][0]) if K.pidx(0, j, 1) in S else
                                        float(params.get(K.pidx(0, j, 1), pure.get(K.pidx(0, j, 1), 0)))) for j in K.CARDS}
    util = [H.ival(u[k], Y) for k in range(3)]
    print("P1 opens (lower bounds / pure): %s ; payoffs %s" % (opens, [round(float(a), 10) for a, b in util]), flush=True)
    verdict = ok and not bad and any(v > 0 for v in opens.values())
    print("%s  (%.0fs)" % ("CERTIFIED: exact Nash equilibrium with P1 betting, unique in the box on this support" if verdict else "NOT CERTIFIED", time.time() - t0))
    if verdict:
        json.dump({"seed": entry.get("seed"), "interior": names, "pure": {H.NAME[i]: str(v) for i, v in pure.items()},
                   "midpoint": [str(v) for v in m], "radius": "1e-%d" % R, "p1_opens": opens},
                  open("cert35gen_seed%s.json" % entry.get("seed"), "w"), indent=1)
