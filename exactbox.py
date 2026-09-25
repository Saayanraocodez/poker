"""Exact interval branch-and-bound over Q with OPEN endpoints, for the small
polynomial systems an enum6 leaf reduces to.

The one thing this does that ivl/bnb5/bnb6 cannot: a MIX coordinate lives in
the OPEN interval (0,1), and the family-adjacent leaves are empty precisely
because a necessary condition pushes such a coordinate to 0 or 1 exactly.  A
closed-interval prover sees [0,0] and survives; this one sees (0,0] and dies.

Variables are the leaf's MIX / DC coordinates, all in [0,1].  Constraints are
polynomials over Q with kind "=" (f = 0), ">=" (f >= 0) or ">" (f > 0), from
    G_i = 0 for MIX i,   G_i <= 0 for label 0,   G_i >= 0 for label 1,
    x_i > 0 and 1 - x_i > 0 for MIX i.
Every constraint is a necessary condition of Nash, so proving the system
infeasible proves the leaf empty.

Engine: HC4-style contraction.  Every constraint is multilinear, hence affine
in each variable:  f = a(x) x_j + g(x).  Bounding a and g over the box (exact
monomial bounds -- every variable is non-negative) gives a bound on x_j
whenever a's range excludes 0, strict when the constraint is strict.  Then
split: the constraint closest to violation, on the variable whose coefficient
times width is largest (the same idea as bnb6's slope-directed split).
All arithmetic is fractions.Fraction -- there is no rounding anywhere.

    prove_empty(polys, kinds, gens, bounds, maxnodes) -> (True, nodes) if the
    system is infeasible; (False, nodes, box) with a surviving box otherwise.
"""
from fractions import Fraction as F
import sympy as sp
import exlp


def to_poly(expr, gens):
    """sympy expression -> {exponent tuple: Fraction} over gens."""
    P = sp.Poly(sp.expand(expr), *gens)
    out = {}
    for mono, c in P.as_dict().items():
        c = sp.Rational(c)
        out[tuple(int(e) for e in mono)] = F(int(c.p), int(c.q))
    return out


def _mono_range(mono, box):
    lo = F(1); hi = F(1)
    for j, e in enumerate(mono):
        if e:
            l, h = box[j][0], box[j][1]
            lo *= l ** e; hi *= h ** e
    return lo, hi


def _range(poly, box):
    lo = F(0); hi = F(0)
    for mono, c in poly.items():
        ml, mh = _mono_range(mono, box)
        if c > 0: lo += c * ml; hi += c * mh
        else:     lo += c * mh; hi += c * ml
    return lo, hi


def _split_lin(poly, j):
    """poly = a(x) x_j + g(x), both free of x_j (every constraint here is
    multilinear, so this always succeeds); returns (a, g) as poly dicts."""
    a = {}; g = {}
    for mono, c in poly.items():
        if mono[j] == 0:
            g[mono] = c
        elif mono[j] == 1:
            m = list(mono); m[j] = 0; a[tuple(m)] = c
        else:
            return None
    if not a: return None
    return a, g


def _empty(b):
    lo, hi, lop, hip = b
    return lo > hi or (lo == hi and (lop or hip))


GRID = 1 << 48

def _floor(v):
    """round DOWN to the dyadic grid 2^-48: a weaker, still sound lower bound.
    Without this the denominators of contracted bounds grow ~5x in bits per
    round (3, 5, 12, 39, 203, 1075 bits measured) and contraction stalls."""
    n = v.numerator * GRID // v.denominator
    return F(n, GRID)


def _ceil(v):
    n = -((-v.numerator * GRID) // v.denominator)
    return F(n, GRID)


def _tighten_lo(b, v, strict):
    """new lower bound v (open if strict); True if the box changed."""
    v = _floor(v)
    if v > b[0]:
        b[0] = v; b[2] = strict; return True
    if v == b[0] and strict and not b[2]:
        b[2] = True; return True
    return False


def _tighten_hi(b, v, strict):
    v = _ceil(v)
    if v < b[1]:
        b[1] = v; b[3] = strict; return True
    if v == b[1] and strict and not b[3]:
        b[3] = True; return True
    return False


def _div_lo(num, al, ah):
    """min of num / a over a in [al, ah] (0 not in [al, ah])."""
    return min(num / al, num / ah)


def _div_hi(num, al, ah):
    return max(num / al, num / ah)


def _mranges(cons, box):
    """exact range of every monomial that occurs, once per box."""
    mr = {}
    for poly, kind, lin in cons:
        for m in poly:
            if m not in mr: mr[m] = _mono_range(m, box)
        for j, a, g, afac in lin:
            for m in a:
                if m not in mr: mr[m] = _mono_range(m, box)
            if afac is not None:
                for fp, e in afac[1]:
                    for m in fp:
                        if m not in mr: mr[m] = _mono_range(m, box)
    return mr


def _rng(poly, mr):
    lo = F(0); hi = F(0)
    for mono, c in poly.items():
        ml, mh = mr[mono]
        if c > 0: lo += c * ml; hi += c * mh
        else:     lo += c * mh; hi += c * ml
    return lo, hi


def contract(cons, box, rounds=12):
    """cons: list of (poly, kind, lin_cache).  box: list of [lo, hi, lo_open, hi_open].
    returns False if proven empty."""
    for _ in range(rounds):
        changed = False
        mr = _mranges(cons, box)
        for poly, kind, lin in cons:
            lo, hi = _rng(poly, mr)
            if kind == "=" and (lo > 0 or hi < 0): return False
            if kind == ">=" and hi < 0: return False
            if kind == ">" and hi <= 0: return False
            strict = kind == ">"
            for j, a, g, afac in lin:
                al, ah = _rng(a, mr)
                if al <= 0 <= ah: continue            # coefficient may vanish: no division
                gl, gh = _rng(g, mr)
                if kind in (">=", ">"):
                    # a x_j >= -g  >= -gh
                    if al > 0:  ch = _tighten_lo(box[j], _div_lo(-gh, al, ah), strict)
                    else:       ch = _tighten_hi(box[j], _div_hi(-gh, al, ah), strict)
                else:
                    # a x_j = -g  in  [-gh, -gl]
                    if al > 0:
                        ch = _tighten_lo(box[j], _div_lo(-gh, al, ah), False)
                        ch = _tighten_hi(box[j], _div_hi(-gl, al, ah), False) or ch
                    else:
                        ch = _tighten_hi(box[j], _div_hi(-gh, al, ah), False)
                        ch = _tighten_lo(box[j], _div_lo(-gl, al, ah), False) or ch
                if ch:
                    changed = True
                    if _empty(box[j]): return False
                    # refresh the ranges of monomials containing x_j
                    for m in mr:
                        if m[j]: mr[m] = _mono_range(m, box)
        if not changed: break
    return True


def _choose(cons, box):
    """slack-directed split: the constraint closest to violation, and in it the
    variable whose coefficient range times width is largest."""
    best = None
    mr = _mranges(cons, box)
    for poly, kind, lin in cons:
        lo, hi = _rng(poly, mr)
        slack = min(-lo, hi) if kind == "=" else hi
        if best is None or slack < best[0]:
            best = (slack, lin)
    if best is None or not best[1]:
        return max(range(len(box)), key=lambda k: box[k][1] - box[k][0])
    j_best = None; sc = -1
    for j, a, g, afac in best[1]:
        w = box[j][1] - box[j][0]
        if w == 0: continue
        al, ah = _rng(a, mr)
        v = max(abs(al), abs(ah)) * w
        if v > sc: sc = v; j_best = j
    if j_best is None:
        return max(range(len(box)), key=lambda k: box[k][1] - box[k][0])
    return j_best


def _subst(poly, j, val):
    """poly with x_j := val (exact)."""
    out = {}
    for m, c in poly.items():
        e = m[j]
        if e:
            c = c * val ** e
            m = tuple(0 if t == j else v for t, v in enumerate(m))
        if c != 0: out[m] = out.get(m, F(0)) + c
    return {m: c for m, c in out.items() if c != 0}


def monotone_rows(cons, box):
    """Derived constraints by MONOTONE ELIMINATION: a constraint affine in x_j,
    f = a(x) x_j + g(x), whose coefficient has a determined sign over the box
    is weakest at one end of x_j's range; substituting that end gives a valid
    consequence free of x_j.  For a strict constraint the consequence is strict.
    This is what proves SGS's parameter ranges in Nash mode: P1's fold condition
    at KKB carries the off-path b44 with coefficient 10(1-b41)(1-2c21) >= 0, so
    it is weakest at b44 = 1, where it is exactly the Table-3 range -- an
    implication the product relaxation cannot see at the boundary point."""
    mr = _mranges(cons, box)
    out = []
    for poly, kind, lin in cons:
        if kind == "=": continue
        for j, a, g, afac in lin:
            if afac is None:
                al, ah = _rng(a, mr)
                sg = 1 if al >= 0 else (-1 if ah <= 0 else 0)
            else:
                sg = _coef_sign(afac, mr)
            if sg > 0:   out.append((_subst(poly, j, box[j][1]), kind))
            elif sg < 0: out.append((_subst(poly, j, box[j][0]), kind))
    return out


def _acc(*pairs):
    """sparse row from (column, coefficient) pairs, ADDING coefficients that land on
    the same column -- a dict literal keeps only the last one, which for a squared
    monomial (prefix = the variable itself, kj == kp) dropped a term and made the
    McCormick row unsound (caught by checkcert on leaf 1791 of b_M_M_0_MNR, 2026-09-21)."""
    d = {}
    for k, v in pairs: d[k] = d.get(k, F(0)) + v
    return d


def lp_infeasible(cons, box):
    """LP relaxation over monomials: every monomial is a variable with its
    exact range over the box, every product link (monomial = prefix * variable)
    gets its McCormick envelope, and the strict constraints (and open
    endpoints) carry a common slack eps.
    max eps <= 0, or LP infeasible  =>  the system has no point in the box."""
    nv = len(box)
    monos = {}
    def mid(m):
        if m not in monos: monos[m] = len(monos)
        return monos[m]
    for poly, kind, lin in cons:
        for m in poly:
            if any(m): mid(m)
    for poly, kind in monotone_rows(cons, box):
        for m in poly:
            if any(m): mid(m)
    for j in range(nv): mid(tuple(1 if k == j else 0 for k in range(nv)))
    # recursive McCormick: every monomial of degree >= 2 is (prefix) * (one
    # variable); make sure every prefix is an LP variable too, so each product
    # link gets its own envelope (degree-3 monomials are common here)
    def prefix(m):
        j = max(t for t in range(nv) if m[t])
        p = list(m); p[j] -= 1
        return tuple(p), j
    work = [m for m in monos if sum(m) >= 2]
    while work:
        m = work.pop()
        p, j = prefix(m)
        if sum(p) >= 1 and p not in monos:
            mid(p)
            if sum(p) >= 2: work.append(p)
    n = len(monos) + 1                     # + eps' = eps + 1 in [0, 2]
    E = n - 1
    lo = [F(0)] * n; hi = [None] * n
    for m, k in monos.items():
        lo[k], hi[k] = _mono_range(m, box)
    lo[E] = F(0); hi[E] = F(2)
    A_ub = []; b_ub = []; A_eq = []; b_eq = []          # rows are SPARSE dicts {col: Fraction}
    def row(coefs, const, kind):
        """sum coefs[k] y_k + const {kind} 0 with y = x' + lo, eps = e - 1"""
        a = {}; c0 = F(const)
        for k, v in coefs.items():
            a[k] = a.get(k, F(0)) + v; c0 += v * lo[k]
        if kind == "=":
            A_eq.append(a); b_eq.append(-c0)
        elif kind == ">=":
            A_ub.append({k: -x for k, x in a.items()}); b_ub.append(c0)
        else:   # ">":  sum - eps >= 0  ->  -sum + (e - 1) <= 0 ... with y shift folded into c0
            a2 = {k: -x for k, x in a.items()}; a2[E] = a2.get(E, F(0)) + 1
            A_ub.append(a2); b_ub.append(c0 + 1)
    extra = monotone_rows(cons, box)
    for poly, kind in [(p, k) for p, k, _ in cons] + extra:
        coefs = {}; const = F(0)
        for m, c in poly.items():
            if any(m): coefs[mid(m)] = coefs.get(mid(m), F(0)) + c
            else: const += c
        row(coefs, const, kind)
    for j in range(nv):
        k = monos[tuple(1 if t == j else 0 for t in range(nv))]
        if box[j][2]: row({k: F(1)}, -box[j][0], ">")        # x_j - lo > 0  (open endpoint)
        if box[j][3]: row({k: F(-1)}, box[j][1], ">")        # hi - x_j > 0
    # McCormick envelopes for every product link  m = p * x_j
    for m, k in list(monos.items()):
        if sum(m) >= 2:
            p, j = prefix(m)
            kp = monos[p]; kj = monos[tuple(1 if t == j else 0 for t in range(nv))]
            xl, xh = lo[kp], hi[kp]; yl, yh = box[j][0], box[j][1]
            row(_acc((k, F(1)), (kj, -xl), (kp, -yl)), xl * yl, ">=")
            row(_acc((k, F(1)), (kj, -xh), (kp, -yh)), xh * yh, ">=")
            row(_acc((k, F(-1)), (kj, xh), (kp, yl)), -xh * yl, ">=")
            row(_acc((k, F(-1)), (kj, xl), (kp, yh)), -xl * yh, ">=")
    u = [None if hi[k] is None else hi[k] - lo[k] for k in range(n)]
    c = [F(0)] * n; c[E] = F(1)
    # fast path: one soft slack s on every row makes the LP always feasible;
    # maximise eps - M s.  If the system had a point, s = 0 and eps > 0 would
    # give objective > 1 (eps = e - 1), so a certified optimum <= 1 is a proof.
    if exlp.HAVE_SCIPY and all(x is not None for x in u):
        S = n; M = F(1000)
        A2 = [{**r, S: F(-1)} for r in A_ub]; b2 = list(b_ub)
        for r, bb in zip(A_eq, b_eq):
            A2.append({**r, S: F(-1)}); b2.append(bb)
            A2.append({**{k: -x for k, x in r.items()}, S: F(-1)}); b2.append(-bb)
        c2 = c + [-M]; U2 = u + [F(10)]
        cert = exlp.bound_certificate_sparse(c2, A2, b2, U2, F(1))
        if cert is True: return True, None
        if isinstance(cert, list):
            # relaxation point: value of every monomial variable (shifted back)
            val = {m: float(lo[k]) + cert[k] for m, k in monos.items()}
            # largest product-relaxation gap decides the branching variable
            best = None
            for m, k in monos.items():
                if sum(m) >= 2:
                    p, j = prefix(m)
                    gap = abs(val[m] - val[p] * val[tuple(1 if t == j else 0 for t in range(nv))])
                    if best is None or gap > best[0]: best = (gap, m)
            return False, best
        # None: solver trouble -> exact simplex below
    dense = lambda rows: [[r.get(k, F(0)) for k in range(n)] for r in rows]
    st, val, x = exlp.solve(c, dense(A_ub), b_ub, dense(A_eq), b_eq, u)
    if st == "infeasible": return True, None
    if st == "optimal" and val <= 1: return True, None      # eps = e - 1 <= 0
    return False, None


def _factors(a, gens):
    """factor the coefficient polynomial once: [(factor as dict, exponent)],
    plus the constant.  The sign of a product of sign-determined factors is
    known even when the expanded polynomial's interval range straddles 0
    (10 (1 - b41)(1 - 2 c21) expands to a range with lower bound -10)."""
    expr = sum(c * sp.Mul(*[g ** e for g, e in zip(gens, m)]) for m, c in a.items())
    const, fl = sp.factor_list(sp.expand(expr))
    return (F(int(sp.Rational(const).p), int(sp.Rational(const).q)),
            [(to_poly(f, gens), int(e)) for f, e in fl])


def _coef_sign(afac, mr):
    """+1 / -1 if the coefficient is >= 0 / <= 0 on the box, else 0."""
    const, fl = afac
    sgn = 1 if const > 0 else -1
    for fp, e in fl:
        lo, hi = _rng(fp, mr)
        if lo >= 0: s_ = 1
        elif hi <= 0: s_ = -1
        else:
            if e % 2 == 0: s_ = 1
            else: return 0
        if e % 2: sgn *= s_
    return sgn


def prepare(polys, kinds, gens, factor=True):
    """polys: sympy expressions over gens, or dict-polys (then gens may be None
    and the variable count is read off the exponent tuples)."""
    cons = []
    nv = len(gens) if gens is not None else max((len(m) for p in polys if isinstance(p, dict) for m in p), default=0)
    for p, k in zip(polys, kinds):
        P = to_poly(p, gens) if not isinstance(p, dict) else p
        if not P:                       # identically zero
            if k == ">": return None    # 0 > 0 is false: infeasible outright
            continue
        lin = []
        for j in range(nv):
            if any(m[j] for m in P):
                s = _split_lin(P, j)
                if s is not None: lin.append((j, s[0], s[1], _factors(s[0], gens) if factor else None))
        cons.append((P, k, lin))
    return cons


def prove_empty(polys, kinds, gens, bounds, maxnodes=20000, lp_every=1, lab=None, gidx=None):
    """bounds: list of (lo, hi, lo_open, hi_open) per gen.
    -> (True, nodes, None) if infeasible, else (False, nodes, surviving box).
    With lab (the leaf's 48 labels) and gidx (the coordinate index of every
    gen) the search is certbox.prove_empty_cert's (2026-09-21): the same
    contraction + LP, plus the exact tree-structured bounds on D, the chord
    contractor and an exact dual simplex where HiGHS's duals cannot be
    rounded -- the leaves the LP relaxation alone could not close in 20,000
    nodes die at the root.  The certificate it produces is discarded here.
    Each node: exact contraction, then the LP relaxation (root always; every
    lp_every-th depth otherwise).  Branching: the variable of the product
    link with the largest gap in the LP point (spatial B&B), widest-width
    tie-break; interval-slack rule when there is no LP point."""
    if lab is not None:
        import certbox
        r = certbox.prove_empty_cert(polys, kinds, gens, bounds, maxnodes, lab=list(lab), gidx=list(gidx))
        if r[0]: return True, len(r[1].get("nodes", [])) or 1, None
        return False, r[1], r[2]
    cons = prepare(polys, kinds, gens)
    if cons is None: return True, 0, None
    stack = [([list(b) for b in bounds], 0)]
    nodes = 0
    while stack:
        box, depth = stack.pop(); nodes += 1
        if not contract(cons, box):
            continue
        hint = None
        if depth == 0 or (lp_every and depth % lp_every == 0):
            dead, hint = lp_infeasible(cons, box)
            if dead: continue
        if nodes > maxnodes:
            return False, nodes, box
        j = None
        if hint is not None and hint[0] > 1e-9:
            m = hint[1]
            cand = [t for t in range(len(box)) if m[t] and box[t][1] > box[t][0]]
            if cand: j = max(cand, key=lambda t: box[t][1] - box[t][0])
        if j is None:
            j = _choose(cons, box)
        w = box[j][1] - box[j][0]
        if w == 0:
            return False, nodes, box
        mid = (box[j][0] + box[j][1]) / 2
        b1 = [list(b) for b in box]; b2 = [list(b) for b in box]
        b1[j][1] = mid; b1[j][3] = False
        b2[j][0] = mid; b2[j][2] = False
        stack.append((b2, depth + 1)); stack.append((b1, depth + 1))
    return True, nodes, None
