"""Exact rational simplex (dense tableau, Bland's rule, two phases).

    maximize  c . x
    s.t.      A_ub x <= b_ub,   A_eq x = b_eq,   0 <= x <= u   (u_i may be None)

Everything is fractions.Fraction; the answer is exact.  Used by exactbox as
the LP relaxation over monomials: interval contraction cannot see that
{b21 - b11 > 0} and {b11 - b21 >= 0} are jointly infeasible, a one-pivot LP can.

    solve(c, A_ub, b_ub, A_eq, b_eq, u) -> (status, value, x)
    status: "optimal" | "infeasible" | "unbounded"
"""
from fractions import Fraction as F


def solve(c, A_ub, b_ub, A_eq, b_eq, u, maxpiv=5000):
    n = len(c)
    rows = []          # (coeffs, rhs, kind)  kind: "<=" or "="
    for a, b in zip(A_ub, b_ub): rows.append((list(a), F(b), "<="))
    for a, b in zip(A_eq, b_eq): rows.append((list(a), F(b), "="))
    for i, ui in enumerate(u):
        if ui is not None:
            a = [F(0)] * n; a[i] = F(1); rows.append((a, F(ui), "<="))
    m = len(rows)
    # make rhs >= 0
    for k in range(m):
        a, b, kind = rows[k]
        if b < 0:
            rows[k] = ([-x for x in a], -b, {"<=": ">=", "=": "="}[kind])
    # columns: x (n) | slacks (one per <= or >= row) | artificials (one per >= or = row)
    nslack = sum(1 for r in rows if r[2] in ("<=", ">="))
    nart = sum(1 for r in rows if r[2] in (">=", "="))
    N = n + nslack + nart
    T = []; basis = []
    js = n; ja = n + nslack
    art_cols = []
    for a, b, kind in rows:
        row = [F(x) for x in a] + [F(0)] * (nslack + nart)
        if kind == "<=":
            row[js] = F(1); basis.append(js); js += 1
        elif kind == ">=":
            row[js] = F(-1); js += 1
            row[ja] = F(1); basis.append(ja); art_cols.append(ja); ja += 1
        else:
            row[ja] = F(1); basis.append(ja); art_cols.append(ja); ja += 1
        row.append(b)
        T.append(row)

    def pivot(r, s):
        pr = T[r]; p = pr[s]
        if p != 1:
            pr = [x / p for x in pr]; T[r] = pr
        for i in range(len(T)):
            if i != r and T[i][s] != 0:
                f = T[i][s]; ri = T[i]
                T[i] = [ri[j] - f * pr[j] for j in range(N + 1)]
        basis[r] = s

    def run(obj, allowed):
        """maximize obj (list of N coefficients) over the current tableau."""
        for _ in range(maxpiv):
            # reduced costs: obj_j - sum_i obj[basis_i] * T[i][j]
            z = [F(0)] * (N + 1)
            for i, bi in enumerate(basis):
                cb = obj[bi]
                if cb != 0:
                    ri = T[i]
                    for j in range(N + 1):
                        if ri[j] != 0: z[j] += cb * ri[j]
            s = -1
            for j in range(N):                        # Bland: smallest index with positive reduced cost
                if allowed[j] and j not in basis and obj[j] - z[j] > 0:
                    s = j; break
            if s < 0:
                return "optimal", z[N]
            r = -1; best = None
            for i in range(len(T)):
                if T[i][s] > 0:
                    ratio = T[i][N] / T[i][s]
                    if best is None or ratio < best or (ratio == best and basis[i] < basis[r]):
                        best = ratio; r = i
            if r < 0:
                return "unbounded", None
            pivot(r, s)
        return "maxpiv", None

    allowed = [True] * N
    if art_cols:
        obj1 = [F(0)] * N
        for j in art_cols: obj1[j] = F(-1)
        st, v = run(obj1, allowed)
        if st != "optimal" or v < 0:
            return "infeasible", None, None
        # drive artificials out of the basis where possible, then forbid them
        for i, bi in enumerate(basis):
            if bi in art_cols:
                for j in range(n + nslack):
                    if T[i][j] != 0:
                        pivot(i, j); break
        for j in art_cols: allowed[j] = False
    obj = [F(x) for x in c] + [F(0)] * (nslack + nart)
    st, v = run(obj, allowed)
    if st != "optimal":
        return st, None, None
    x = [F(0)] * n
    for i, bi in enumerate(basis):
        if bi < n: x[bi] = T[i][N]
    return "optimal", sum(F(c[j]) * x[j] for j in range(n)), x


# ---------------------------------------------------------------------------
# Fast path: float HiGHS finds the optimum, an exact rational dual certificate
# proves the bound.  Only an INFEASIBILITY verdict ever needs to be trusted, so
# only that direction is certified; "feasible" is never used as a conclusion.
try:
    import numpy as _np
    from scipy.optimize import linprog as _linprog
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False


def bound_certificate(c, A, b, U, target, tries=1):
    """LP  max c.z  s.t.  A z <= b,  0 <= z <= U   (all finite).
    Returns True iff an EXACT dual certificate shows  optimum <= target;
    the float LP point (a list) when the relaxation is feasible above target;
    None when the solver failed.
    Weak duality: for any y, w >= 0 with  A^T y + w >= c  (v = A^T y + w - c >= 0),
    every feasible z has  c.z <= b.y + U.w.  The float solver only proposes
    (y, w); the inequality check and the bound are computed in Fractions."""
    if not HAVE_SCIPY: return None
    n = len(c); m = len(A)
    Af = _np.array([[float(x) for x in row] for row in A]) if m else _np.zeros((0, n))
    bf = _np.array([float(x) for x in b]); cf = _np.array([float(x) for x in c])
    Uf = [float(x) for x in U]
    try:
        res = _linprog(-cf, A_ub=Af if m else None, b_ub=bf if m else None,
                       bounds=[(0.0, ui) for ui in Uf], method="highs")
    except Exception:
        return None
    if res.status != 0:
        return None
    if -res.fun > float(target) + 1e-7:
        return list(res.x)                # relaxation looks feasible: return its point, no certificate wanted
    y = [max(F(0), F(float(v)).limit_denominator(10**12)) for v in (-res.ineqlin.marginals if m else [])]
    w = [max(F(0), F(float(v)).limit_denominator(10**12)) for v in -res.upper.marginals]
    # exact repair: v = A^T y + w - c must be >= 0; bump w where it is not
    for j in range(n):
        vj = sum(A[i][j] * y[i] for i in range(m) if y[i]) + w[j] - F(c[j])
        if vj < 0: w[j] -= vj
    bnd = sum(F(b[i]) * y[i] for i in range(m)) + sum(F(U[j]) * w[j] for j in range(n))
    return bnd <= F(target)


def bound_certificate_sparse(c, A, b, U, target):
    """Same as bound_certificate with A given as sparse rows {col: Fraction}.
    The float matrix is filled by index (no dense Fraction rows), and the
    exact certificate only touches rows with a positive dual."""
    if not HAVE_SCIPY: return None
    n = len(c); m = len(A)
    Af = _np.zeros((m, n))
    for i, r in enumerate(A):
        for k, v in r.items(): Af[i, k] = float(v)
    bf = _np.array([float(x) for x in b]); cf = _np.array([float(x) for x in c])
    Uf = [float(x) for x in U]
    try:
        res = _linprog(-cf, A_ub=Af if m else None, b_ub=bf if m else None,
                       bounds=[(0.0, ui) for ui in Uf], method="highs")
    except Exception:
        return None
    if res.status != 0:
        return None
    if -res.fun > float(target) + 1e-7:
        return list(res.x)
    y = [max(F(0), F(float(v)).limit_denominator(10**12)) for v in (-res.ineqlin.marginals if m else [])]
    w = [max(F(0), F(float(v)).limit_denominator(10**12)) for v in -res.upper.marginals]
    aty = [F(0)] * n
    for i, yi in enumerate(y):
        if yi:
            for k, v in A[i].items(): aty[k] += v * yi
    for j in range(n):
        vj = aty[j] + w[j] - F(c[j])
        if vj < 0: w[j] -= vj
    bnd = sum(F(b[i]) * y[i] for i in range(m) if y[i]) + sum(F(U[j]) * w[j] for j in range(n) if w[j])
    return bnd <= F(target)
