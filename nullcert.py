"""Cofactor (Nullstellensatz / ideal-membership) certificates by linear algebra.

    lift(target, gens, nv, dmax) -> [q_1, ..., q_r]  with  sum_k q_k gens[k] == target
    and deg q_k <= d for the smallest d <= dmax that works, or None.

Unknowns are the coefficients of every monomial of degree <= d in every q_k
(a Macaulay system); the linear system is solved exactly over Q by sparse
Gaussian elimination.  Independent of sympy's Groebner machinery: symleaf's
1 in <E> (EMPTY_GB), radical membership 1 in <E, 1 - t f> (EMPTY_MIX and the
FAMILY identities), normal forms modulo the Groebner basis (EMPTY_CONST and
the reduced systems of K1b) all become explicit polynomial identities that
checkcert.py verifies by expansion.

A modular pre-solve (mod a 61-bit prime) finds the smallest degree and the
pivot structure cheaply; the exact solve runs once, at that degree.
"""
from fractions import Fraction as F
import itertools

P61 = (1 << 61) - 1


def monomials(nv, d):
    """all exponent tuples of total degree <= d"""
    out = []
    for total in range(d + 1):
        for c in itertools.combinations_with_replacement(range(nv), total):
            m = [0] * nv
            for j in c: m[j] += 1
            out.append(tuple(m))
    return out


def _system(target, gens, nv, d):
    """sparse rows {col: coef} indexed by product monomial; columns (k, m)"""
    cols = {}
    rows = {}
    for k, e in enumerate(gens):
        for m in monomials(nv, d):
            col = (k, m)
            if col not in cols: cols[col] = len(cols)
            ci = cols[col]
            for m2, c in e.items():
                u = tuple(a + b for a, b in zip(m, m2))
                rows.setdefault(u, {})[ci] = rows.get(u, {}).get(ci, F(0)) + c
    rhs = {}
    for u, c in target.items(): rhs[u] = c
    for u in rhs:
        rows.setdefault(u, {})
    return cols, rows, rhs


def _solve_mod(rows, rhs, ncols, p=P61):
    """Gaussian elimination mod p.  -> dict col -> value (a particular solution) or None"""
    R = []
    for u, r in rows.items():
        rr = {c: int(v.numerator * pow(v.denominator, -1, p)) % p for c, v in r.items()}
        rr = {c: v for c, v in rr.items() if v}
        b = rhs.get(u, F(0)); b = int(b.numerator * pow(b.denominator, -1, p)) % p
        if rr or b: R.append((rr, b))
    pivots = {}          # col -> (row dict, rhs)
    for rr, b in R:
        # reduce by existing pivots
        rr = dict(rr)
        for c in sorted(rr):
            if c in pivots and c in rr:
                f = rr[c]; pr, pb = pivots[c]
                for cc, vv in pr.items():
                    rr[cc] = (rr.get(cc, 0) - f * vv) % p
                b = (b - f * pb) % p
                rr = {cc: vv for cc, vv in rr.items() if vv}
        if not rr:
            if b: return None
            continue
        c = min(rr); inv = pow(rr[c], -1, p)
        rr = {cc: vv * inv % p for cc, vv in rr.items()}; b = b * inv % p
        # eliminate c from other pivot rows
        for pc, (pr, pb) in list(pivots.items()):
            if c in pr:
                f = pr[c]
                for cc, vv in rr.items(): pr[cc] = (pr.get(cc, 0) - f * vv) % p
                pivots[pc] = ({cc: vv for cc, vv in pr.items() if vv}, (pb - f * b) % p)
        pivots[c] = (rr, b)
    sol = {}
    for c, (pr, pb) in pivots.items():
        sol[c] = pb          # free variables = 0
    return sol


def _solve_exact(rows, rhs, cols_used):
    """exact elimination restricted to the columns the modular solve used"""
    keep = set(cols_used)
    R = []
    for u, r in rows.items():
        rr = {c: v for c, v in r.items() if c in keep and v}
        b = rhs.get(u, F(0))
        if rr or b: R.append((rr, b))
    pivots = {}
    for rr, b in R:
        rr = dict(rr)
        for c in sorted(rr):
            if c in pivots and c in rr:
                f = rr[c]; pr, pb = pivots[c]
                for cc, vv in pr.items(): rr[cc] = rr.get(cc, F(0)) - f * vv
                b = b - f * pb
                rr = {cc: vv for cc, vv in rr.items() if vv}
        if not rr:
            if b: return None
            continue
        c = min(rr); inv = 1 / rr[c]
        rr = {cc: vv * inv for cc, vv in rr.items()}; b = b * inv
        for pc, (pr, pb) in list(pivots.items()):
            if c in pr:
                f = pr[c]
                for cc, vv in rr.items(): pr[cc] = pr.get(cc, F(0)) - f * vv
                pivots[pc] = ({cc: vv for cc, vv in pr.items() if vv}, pb - f * b)
        pivots[c] = (rr, b)
    return {c: pb for c, (pr, pb) in pivots.items()}


def lift(target, gens, nv, dmax=6):
    gens = [g for g in gens if g]
    if not gens: return None
    for d in range(dmax + 1):
        cols, rows, rhs = _system(target, gens, nv, d)
        sol = _solve_mod(rows, rhs, len(cols))
        if sol is None: continue
        used = [c for c, v in sol.items() if v] or list(sol)[:1]
        ex = _solve_exact(rows, rhs, used)
        if ex is None:
            # unlucky prime / support: retry with every column
            ex = _solve_exact(rows, rhs, range(len(cols)))
            if ex is None: continue
        inv = {ci: col for col, ci in cols.items()}
        q = [{} for _ in gens]
        for ci, v in ex.items():
            if v:
                k, m = inv[ci]; q[k][m] = v
        # verify
        acc = {}
        for qk, e in zip(q, gens):
            for m1, c1 in qk.items():
                for m2, c2 in e.items():
                    u = tuple(a + b for a, b in zip(m1, m2)); acc[u] = acc.get(u, F(0)) + c1 * c2
        acc = {m: c for m, c in acc.items() if c}
        if acc == {m: c for m, c in target.items() if c}:
            return q
    return None


def radical(E, f, nv, dmax=6):
    """1 = sum q_k e_k + q0 (1 - t f) in nv + 1 variables (t last) -> q list or None"""
    Et = [{m + (0,): c for m, c in e.items()} for e in E]
    tf = {m + (1,): c for m, c in f.items()}
    one = {tuple([0] * (nv + 1)): F(1)}
    rab = dict(one)
    for m, c in tf.items(): rab[m] = rab.get(m, F(0)) - c
    return lift(one, Et + [rab], nv + 1, dmax)
