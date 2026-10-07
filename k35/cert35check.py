"""INDEPENDENT re-check of cert35.py, without sympy: polynomials are dicts {exponent tuple: Fraction}
built directly from k35's tree; substitution, differentiation and interval evaluation are written
here.  Re-checks (1) the structural identities, (2) the Krawczyk existence test, (3) the D-conditions
of all 60 coordinates, (4) P1's opening coordinates > 0.
usage (from k35/):  KUHN_CARDS=5 python cert35check.py hiprec400.json"""
import os, sys, json, time
os.environ.setdefault("KUHN_CARDS", "5")
from fractions import Fraction as Fr
from decimal import Decimal
import tree as T, kuhn3p as K

NP = K.NPARAM; ND = T.ND
INT = [int(x) for x in T.INTERNAL]; AGGC = [int(x) for x in T.AGGC]; PASC = [int(x) for x in T.PASC]
LEAF = [int(x) for x in T.LEAFPOS]
PAR = {}
for p_ in INT: PAR[AGGC[p_]] = (p_, True); PAR[PASC[p_]] = (p_, False)
NAME = {K.pidx(pl, j, s): "%s%d%d" % ("abc"[pl], j, s) for pl in range(3) for j in K.CARDS for s in K.SITUATIONS}
IDX = {v: k for k, v in NAME.items()}
OWNER = {i: "abc".index(NAME[i][0]) for i in range(NP)}
INTERIOR = "a11 a21 a31 a32 a43 a44 a51 b11 b21 b33 b42 b44 c11 c21 c32 c33 c41".split()
NV = len(INTERIOR)


# ---- dict polynomials over n variables ----
def const(c, n): return {(0,) * n: Fr(c)} if c else {}
def var(k, n): return {tuple(1 if t == k else 0 for t in range(n)): Fr(1)}
def add(p, q, s=1):
    out = dict(p)
    for m, c in q.items():
        out[m] = out.get(m, Fr(0)) + s * c
    return {m: c for m, c in out.items() if c}
def mul(p, q):
    out = {}
    for m1, c1 in p.items():
        for m2, c2 in q.items():
            m = tuple(a + b for a, b in zip(m1, m2)); out[m] = out.get(m, Fr(0)) + c1 * c2
    return {m: c for m, c in out.items() if c}
def scale(p, c): return {m: v * c for m, v in p.items()} if c else {}
def subst_const(p, k, val):
    out = {}
    for m, c in p.items():
        mm = list(m); e = mm[k]; mm[k] = 0; mm = tuple(mm)
        out[mm] = out.get(mm, Fr(0)) + c * (Fr(val) ** e)
    return {m: c for m, c in out.items() if c}
def compose(p, images, n):
    """substitute variable k by the polynomial images[k] (over n variables)"""
    out = {}
    for m, c in p.items():
        t = const(c, n)
        for k, e in enumerate(m):
            for _ in range(e): t = mul(t, images[k])
        out = add(out, t)
    return out
def diff(p, k):
    out = {}
    for m, c in p.items():
        if m[k]:
            mm = list(m); mm[k] -= 1; out[tuple(mm)] = out.get(tuple(mm), Fr(0)) + c * m[k]
    return {m: c for m, c in out.items() if c}
def evalp(p, pt):
    v = Fr(0)
    for m, c in p.items():
        t = c
        for x, e in zip(pt, m):
            if e: t *= x ** e
        v += t
    return v
def ival(p, box):
    """enclosure on a box of positive coordinates (each monomial is monotone increasing)"""
    lo = hi = Fr(0)
    for m, c in p.items():
        a = b = Fr(1)
        for (l, h), e in zip(box, m):
            if e: a *= l ** e; b *= h ** e
        if c >= 0: lo += c * a; hi += c * b
        else: lo += c * b; hi += c * a
    return lo, hi


def build(x):
    """u[3] and D[60] as dict polys over NV variables, profile x (60 dict polys)"""
    u = [{}, {}, {}]; D = [{} for _ in range(NP)]
    for d in range(ND):
        V = {}
        for pos in LEAF: V[pos] = [const(int(T.PAYT[d, pos, k]), NV) for k in range(3)]
        for pos in reversed(INT):
            xx = x[int(T.COORD[d, pos])]; one = add(const(1, NV), xx, -1)
            V[pos] = [add(mul(one, V[PASC[pos]][k]), mul(xx, V[AGGC[pos]][k])) for k in range(3)]
        for k in range(3): u[k] = add(u[k], V[0][k])
        for pos in INT:
            i = int(T.COORD[d, pos]); o = OWNER[i]; R = const(1, NV); q = pos
            while q in PAR:
                r, agg = PAR[q]; c = int(T.COORD[d, r])
                if OWNER[c] != o: R = mul(R, x[c] if agg else add(const(1, NV), x[c], -1))
                q = r
            D[i] = add(D[i], mul(R, add(V[AGGC[pos]][o], V[PASC[pos]][o], -1)))
    return [scale(v, Fr(1, ND)) for v in u], [scale(v, Fr(1, ND)) for v in D]


if __name__ == "__main__":
    t0 = time.time()
    num = json.load(open(sys.argv[1]))["profile"]
    val = [Fr(Decimal(s[:75])) for s in num]
    x = []
    for i in range(NP):
        if NAME[i] in INTERIOR: x.append(var(INTERIOR.index(NAME[i]), NV))
        else:
            assert val[i] in (0, 1), NAME[i]; x.append(const(val[i], NV))
    u, D = build(x)
    F = {n: add(subst_const(u[OWNER[IDX[n]]], INTERIOR.index(n), 1), subst_const(u[OWNER[IDX[n]]], INTERIOR.index(n), 0), -1) for n in INTERIOR}
    # reduced variables: A, B, s, c1, then the 11 others
    rest = [n for n in INTERIOR if n not in ("a11", "a21", "b11", "b21", "c11", "c21")]
    RV = ["A", "B", "s", "c1"] + rest; nr = len(RV)
    img = []
    for n in INTERIOR:
        if n in ("a11", "a21"): img.append(var(0, nr))
        elif n in ("b11", "b21"): img.append(var(1, nr))
        elif n == "c11": img.append(var(3, nr))
        elif n == "c21": img.append(add(var(2, nr), var(3, nr), -1))
        else: img.append(var(RV.index(n), nr))
    Fr_ = {n: compose(F[n], img, nr) for n in INTERIOR}
    dep_ok = all(all(m[3] == 0 for m in f) for f in Fr_.values())
    pair_ok = all(Fr_[a] == Fr_[b] for a, b in (("a11", "a21"), ("b11", "b21"), ("c11", "c21")))
    print("identities (dict polys, no sympy): sum-only dependence %s, pairs coincide %s" % (dep_ok, pair_ok), flush=True)
    if not (dep_ok and pair_ok): sys.exit("structure fails")
    # drop the c1 variable (absent) -> 14 variables
    keep = [k for k in range(nr) if k != 3]
    def shrink(p): return {tuple(m[k] for k in keep): c for m, c in p.items()}
    eqs = ["a11", "b11", "c11"] + rest
    G = [shrink(Fr_[n]) for n in eqs]
    gv = [RV[k] for k in keep]
    m = [val[IDX["a11"]], val[IDX["b11"]], val[IDX["c11"]] + val[IDX["c21"]]] + [val[IDX[n]] for n in rest]
    assert val[IDX["c11"]] == Fr(3, 10)
    r = Fr(1, 10 ** 30); Y = [(v - r, v + r) for v in m]
    assert all(lo > 0 and hi < 1 for lo, hi in Y)
    Gm = [evalp(g, m) for g in G]
    J = [[diff(g, k) for k in range(14)] for g in G]
    Jm = [[float(evalp(J[a][b], m)) for b in range(14)] for a in range(14)]
    import numpy as np
    C = [[Fr(v).limit_denominator(10 ** 30) for v in row] for row in np.linalg.inv(np.array(Jm)).tolist()]
    JY = [[ival(J[a][b], Y) for b in range(14)] for a in range(14)]
    ok = True
    for a in range(14):
        lo = hi = m[a] - sum(C[a][k] * Gm[k] for k in range(14))
        for b in range(14):
            plo = phi = Fr(1 if a == b else 0)
            for k in range(14):
                jl, jh = JY[k][b]; c = C[a][k]
                if c >= 0: plo -= c * jh; phi -= c * jl
                else: plo -= c * jl; phi -= c * jh
            mag = max(abs(plo), abs(phi)); lo -= mag * r; hi += mag * r
        ok &= Y[a][0] < lo and hi < Y[a][1]
    print("Krawczyk (independent): K(Y) inside int(Y): %s   max|G(m)| %.1e" % (ok, max(abs(float(v)) for v in Gm)), flush=True)
    if not ok: sys.exit("Krawczyk fails")
    img14 = []
    for n in INTERIOR:                                   # the full profile in the 14 reduced variables, c11 = 3/10
        if n in ("a11", "a21"): img14.append(var(0, 14))
        elif n in ("b11", "b21"): img14.append(var(1, 14))
        elif n == "c11": img14.append(const(Fr(3, 10), 14))
        elif n == "c21": img14.append(add(var(2, 14), const(Fr(3, 10), 14), -1))
        else: img14.append(var(gv.index(n), 14))
    bad = []
    for i in range(NP):
        n = NAME[i]
        if n in INTERIOR:                                # own reach > 0 on Y
            d0 = next((d, pos) for d in range(ND) for pos in INT if int(T.COORD[d, pos]) == i)
            q = d0[1]; o = OWNER[i]
            while q in PAR:
                rr, agg = PAR[q]; c = int(T.COORD[d0[0], rr])
                if OWNER[c] == o:
                    f = compose(x[c] if agg else add(const(1, NV), x[c], -1), img14, 14)
                    lo_, hi_ = ival(f, Y)
                    if not lo_ > 0: bad.append("%s: own reach" % n)
                q = rr
            continue
        Di = compose(D[i], img14, 14)
        if not Di: continue
        lo_, hi_ = ival(Di, Y)
        if val[i] == 0 and not hi_ < 0: bad.append(n)
        if val[i] == 1 and not lo_ > 0: bad.append(n)
    print("D-conditions (independent): %d violations %s" % (len(bad), bad), flush=True)
    p1 = [Y[0], Y[gv.index("a31")], Y[gv.index("a51")]]
    print("P1 opening (a11 = a21, a31, a51) lower bounds: %s" % [float(lo) for lo, hi in p1], flush=True)
    print("%s  (%.0fs)" % ("INDEPENDENTLY CONFIRMED" if not bad and all(lo > 0 for lo, hi in p1) else "NOT CONFIRMED", time.time() - t0))
