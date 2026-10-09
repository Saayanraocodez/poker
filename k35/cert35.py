"""EXACT certificate that (3, 5)-Kuhn has a Nash equilibrium in which P1 BETS.

The numerical equilibrium (polish35: 7 of 20 MCCFR seeds; hiprec35 / 420-digit refinement) has 17
interior coordinates whose values are algebraic of degree > 8 -- no closed form.  So the proof is an
interval-Newton (Krawczyk) existence proof in EXACT rational interval arithmetic, no floats:

 1. The game is k35's tree (tree.py over kuhn3p, KUHN_CARDS=5); every condition is built from it as
    an exact polynomial (sympy, rational coefficients) over the 17 interior coordinates, with the 43
    other coordinates at their exact pure values (0 or 1).
 2. Structure, CHECKED as polynomial identities (not assumed): every condition depends on P3's
    c11, c21 only through c11 + c21; and on the subspace a21 = a11, b21 = b11 the conditions of
    a11/a21, b11/b21, c11/c21 coincide.  So with c11 = 3/10 fixed, the unknowns
    y = (A = a11 = a21, B = b11 = b21, s = c11 + c21, and 11 others) satisfy all 17 conditions iff
    they satisfy 14 distinct equations G(y) = 0 -- a square system.
 3. Krawczyk: for a rational box Y around the numerical solution, m = mid(Y), C ~ J(m)^-1 (any
    rational matrix), K(Y) = m - C G(m) + (I - C J(Y))(Y - m) with J(Y) an exact interval enclosure
    of the Jacobian over Y.  K(Y) inside int(Y) proves G has exactly one zero y* in Y.
 4. Nash: D-conditions (own-reach-stripped value difference D_i, i.e. the one-shot condition at
    every own information set) for ALL 60 coordinates at y*: interior ones have du_i = 0 at y*
    (they are the equations) and own reach > 0 on Y, hence D_i = 0; pure ones need D_i <= 0 (at 0)
    or >= 0 (at 1), checked over Y by exact interval evaluation (or D_i identically 0).  D-conditions
    everywhere imply Nash (one-shot deviation principle in each player's own tree).
 5. P1 bets: the opening coordinates A, a31, a51 are > 0 on Y.
usage (from k35/):  KUHN_CARDS=5 python cert35.py hiprec400.json"""
import os, sys, json, time
os.environ.setdefault("KUHN_CARDS", "5")
import sympy as sp
from fractions import Fraction as Fr
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


def log(*a): print(*a, flush=True)


def build(xsym):
    """utilities u_0..u_2 and the 60 D_i as polynomials, for the profile xsym (60 sympy expressions)"""
    u = [0, 0, 0]; D = [0] * NP
    for d in range(ND):
        V = {}
        for pos in LEAF: V[pos] = [sp.Integer(int(T.PAYT[d, pos, k])) for k in range(3)]
        for pos in reversed(INT):
            x = xsym[int(T.COORD[d, pos])]
            V[pos] = [sp.expand((1 - x) * V[PASC[pos]][k] + x * V[AGGC[pos]][k]) for k in range(3)]
        for k in range(3): u[k] += V[0][k]
        for pos in INT:                                   # D_i: other players' reach on the path, own factors -> 1
            i = int(T.COORD[d, pos]); o = OWNER[i]; R = sp.Integer(1); q = pos
            while q in PAR:
                r, agg = PAR[q]; c = int(T.COORD[d, r])
                if OWNER[c] != o: R = R * (xsym[c] if agg else 1 - xsym[c])
                q = r
            D[i] += sp.expand(R * (V[AGGC[pos]][o] - V[PASC[pos]][o]))
    return [sp.expand(v / ND) for v in u], [sp.expand(v / ND) for v in D]


def own_reach(i):
    """own action factors on the path to coordinate i's information set (the same for all its nodes)"""
    for d in range(ND):
        for pos in INT:
            if int(T.COORD[d, pos]) == i:
                o = OWNER[i]; out = []; q = pos
                while q in PAR:
                    r, agg = PAR[q]; c = int(T.COORD[d, r])
                    if OWNER[c] == o: out.append((c, agg))
                    q = r
                return out


# ---- exact rational interval arithmetic for polynomials over a box of POSITIVE coordinates ----
def ival_poly(P, gens, box):
    """enclosure of polynomial P (sympy Poly over gens) on box {g: (lo, hi)}, all lo > 0"""
    lo = Fr(0); hi = Fr(0)
    for mon, coef in P.terms():
        c = Fr(int(coef.p), int(coef.q))
        a = Fr(1); b = Fr(1)
        for g, e in zip(gens, mon):
            if e: a *= box[g][0] ** e; b *= box[g][1] ** e
        if c >= 0: lo += c * a; hi += c * b
        else: lo += c * b; hi += c * a
    return lo, hi


def eval_poly(P, gens, pt):
    v = Fr(0)
    for mon, coef in P.terms():
        t = Fr(int(coef.p), int(coef.q))
        for g, e in zip(gens, mon):
            if e: t *= pt[g] ** e
        v += t
    return v


if __name__ == "__main__":
    t0 = time.time()
    num = json.load(open(sys.argv[1]))
    pnum = [sp.Rational(x[:75]) for x in num["profile"]]          # ~73 digits of the numerical solution
    # ---- 1. the profile with 17 symbols, pure coordinates exact
    sym = {n: sp.Symbol(n) for n in INTERIOR}
    x17 = []
    for i in range(NP):
        if NAME[i] in sym: x17.append(sym[NAME[i]])
        else:
            assert pnum[i] in (0, 1), NAME[i]                    # exact test: pure coordinates are exactly 0 or 1
            x17.append(sp.Integer(pnum[i]))
    log("building exact polynomials from the k35 tree ...")
    u, D = build(x17)
    F = {n: sp.expand(u[OWNER[IDX[n]]].subs(sym[n], 1) - u[OWNER[IDX[n]]].subs(sym[n], 0)) for n in INTERIOR}
    log("  done (%.0fs)" % (time.time() - t0))
    # ---- 2. structure, as identities
    sv, c1 = sp.Symbol("s"), sym["c11"]
    A, B = sp.Symbol("A"), sp.Symbol("B")
    red = {sym["a11"]: A, sym["a21"]: A, sym["b11"]: B, sym["b21"]: B, sym["c21"]: sv - c1}
    Fr_ = {n: sp.expand(F[n].subs(red)) for n in INTERIOR}
    # on the subspace a21 = a11, b21 = b11: every condition depends on c11, c21 only through s = c11 + c21
    dep_ok = all(not f.has(c1) for f in Fr_.values())
    log("on a21 = a11, b21 = b11, every condition depends on c11, c21 only through c11 + c21: %s %s" % (
        dep_ok, "" if dep_ok else [n for n, f in Fr_.items() if f.has(c1)]))
    pairs = [("a11", "a21"), ("b11", "b21"), ("c11", "c21")]
    pair_ok = all(sp.expand(Fr_[a] - Fr_[b]) == 0 for a, b in pairs)
    log("on a21 = a11, b21 = b11 the conditions a11/a21, b11/b21, c11/c21 coincide: %s" % pair_ok)
    if not (dep_ok and pair_ok): sys.exit("structure does not hold -- no square reduction")
    eqs = [n for n in INTERIOR if n not in ("a21", "b21", "c21")]           # 14 equations
    gens = [A, B, sv] + [sym[n] for n in INTERIOR if n not in ("a11", "a21", "b11", "b21", "c11", "c21")]
    assert len(eqs) == len(gens) == 14
    G = [sp.Poly(Fr_[n], *gens) for n in eqs]
    log("square system: %d equations in %d unknowns %s" % (len(G), len(gens), [str(g) for g in gens]))
    # ---- 3. Krawczyk
    c11v = sp.Rational(3, 10)
    G = [sp.Poly(g.as_expr().subs(c1, c11v), *gens) for g in G]
    num_y = {A: pnum[IDX["a11"]], B: pnum[IDX["b11"]], sv: pnum[IDX["c11"]] + pnum[IDX["c21"]]}
    for g in gens[3:]: num_y[g] = pnum[IDX[str(g)]]
    assert abs(float(pnum[IDX["c11"]]) - 0.3) < 1e-60, "the numerical solution has c11 = 3/10"
    m = {g: Fr(int(sp.Rational(num_y[g]).p), int(sp.Rational(num_y[g]).q)) for g in gens}
    r = Fr(1, 10 ** 30)
    Y = {g: (m[g] - r, m[g] + r) for g in gens}
    assert all(lo > 0 and hi < 1 for lo, hi in Y.values())
    Gm = [eval_poly(g, gens, m) for g in G]
    log("max |G(m)| = %.2e" % max(abs(float(v)) for v in Gm))
    Jp = [[sp.Poly(g.as_expr().diff(x), *gens) for x in gens] for g in G]
    Jm = sp.Matrix([[sp.Rational(eval_poly(Jp[a][b], gens, m)) for b in range(14)] for a in range(14)])
    Cinv = Jm.evalf(40).inv()
    C = [[Fr(sp.Rational(str(Cinv[a, b])).p, sp.Rational(str(Cinv[a, b])).q) if Cinv[a, b] != 0 else Fr(0) for b in range(14)] for a in range(14)]
    JY = [[ival_poly(Jp[a][b], gens, Y) for b in range(14)] for a in range(14)]
    ok = True; worst = Fr(0)
    for a in range(14):
        cg = sum(C[a][k] * Gm[k] for k in range(14))
        lo = m[gens[a]] - cg; hi = lo
        for b in range(14):                                # (I - C J(Y))_ab * (Y_b - m_b), Y_b - m_b in [-r, r]
            plo = (1 if a == b else 0); phi = plo
            for k in range(14):
                jl, jh = JY[k][b]; ck = C[a][k]
                if ck >= 0: plo -= ck * jh; phi -= ck * jl
                else: plo -= ck * jl; phi -= ck * jh
            mag = max(abs(plo), abs(phi))
            lo -= mag * r; hi += mag * r
        inside = Y[gens[a]][0] < lo and hi < Y[gens[a]][1]
        ok &= inside; worst = max(worst, (max(hi - m[gens[a]], m[gens[a]] - lo)) / r)
    log("KRAWCZYK: K(Y) inside int(Y): %s   (K's half-width / r: max %.3e)" % (ok, float(worst)))
    if not ok: sys.exit("Krawczyk test failed")
    # ---- 4. D-conditions for all 60 coordinates over Y
    full = {sym["a11"]: A, sym["a21"]: A, sym["b11"]: B, sym["b21"]: B, sym["c11"]: c11v, sym["c21"]: sv - c11v}
    bad = []; zero = 0
    for i in range(NP):
        Di = sp.expand(D[i].subs(full))
        n = NAME[i]
        if n in INTERIOR:
            orr = own_reach(i)
            for c, agg in orr:                              # own reach > 0 on Y: every own factor > 0
                e = sp.expand((x17[c] if agg else 1 - x17[c]).subs(full))
                lo_, hi_ = ival_poly(sp.Poly(e, *gens), gens, Y) if e.free_symbols else (Fr(int(sp.Rational(e).p), int(sp.Rational(e).q)),) * 2
                if not lo_ > 0: bad.append("%s: own reach not positive" % n)
            continue
        if Di == 0: zero += 1; continue
        lo_, hi_ = ival_poly(sp.Poly(Di, *gens), gens, Y)
        val = int(x17[i])
        if val == 0 and not hi_ < 0: bad.append("%s = 0 but D in [%.3e, %.3e]" % (n, float(lo_), float(hi_)))
        if val == 1 and not lo_ > 0: bad.append("%s = 1 but D in [%.3e, %.3e]" % (n, float(lo_), float(hi_)))
    log("D-conditions: %d pure coordinates with D identically 0, %d violations %s" % (zero, len(bad), bad))
    if bad: sys.exit("not certified")
    # ---- 5. P1 bets
    opens = {n: Y[A] if n in ("a11", "a21") else Y[sym[n]] for n in ("a11", "a21", "a31", "a51")}
    log("P1 opening coordinates on Y: %s" % {n: (float(lo), float(hi)) for n, (lo, hi) in opens.items()})
    log("CERTIFIED: an exact Nash equilibrium of (3,5)-Kuhn exists in Y, unique there on this support, with P1 betting "
        "(a11 = a21 in %s, a31 in %s, a51 in %s).  %.0fs" % tuple([str(float(Y[A][0]))] + [str(float(Y[sym[n]][0])) for n in ("a31", "a51")] + [time.time() - t0]))
