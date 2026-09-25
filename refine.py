"""REFINEMENTS ON THE COMPLETE NASH SET: which equilibria survive a tremble.

Every information set of this game is BINARY (bet/check, call/fold), and for
binary sets van Damme's extensive-form properness, Selten's extensive-form
perfection and agent-normal-form perfection all reduce to the same condition
(Lemma R1, PAPER_KIT): the inferior action's probability is O(eps) either way.
So one computation decides all three, and the remaining refinement -- Myerson
properness on the NORMAL form, which orders whole pure strategies across
information sets (Theorem 3) -- is the only one that can differ.  That is open
problem 2, and this script measures the gap exactly.

The test.  Write D_v for the own-reach-stripped gradient of coordinate v
(symbet.build_D).  At a COMPLETELY MIXED profile x every information set is
reached, so sign(D_v(x)) is the sign of the value difference at v's set, and
"the action played with positive probability is optimal at x" reads

    D_v(x) = 0   if 0 < sigma_v < 1,    D_v(x) >= 0 if sigma_v = 1,
    D_v(x) <= 0  if sigma_v = 0.

Selten: sigma is (extensive-form) perfect iff it is a limit of completely mixed
x satisfying those conditions -- i.e. iff sigma lies in the CLOSURE of

    F(sigma) = { x in (0,1)^48 : the conditions above }.

Take x(t) = sigma + t*delta.  On the Nash set every off-path D_v vanishes
identically, so D_v(sigma) = 0 there and the FIRST ORDER decides:

    g_v(delta) = grad D_v(sigma) . delta,

with delta pointing inward (delta_v >= 0 where sigma_v = 0, <= 0 where
sigma_v = 1).  The conditions on g_v are linear in delta, so perfection at
sigma is an LP feasibility question, and infeasibility comes with a Farkas
certificate in exact rationals.  Strictness is handled as follows:

  * a coordinate with D_v(sigma) != 0 (strict deterrence) imposes NOTHING at
    first order -- the condition holds for all small t;
  * a coordinate with D_v(sigma) = 0 imposes its sign condition on g_v;
  * delta_v > 0 is required at the trembling coordinates, but the LP is solved
    with delta_v >= 0: if the relaxed LP is INFEASIBLE, sigma is certainly not
    perfect (sound); if it is feasible with every required delta_v > 0 and the
    indifference conditions can be maintained, sigma is perfect (a witness
    curve is built and verified separately).  Feasible only with some
    delta_v = 0 means "decided at higher order", and is reported as such.

usage:  python refine.py                 (self-test on a family witness point)
"""
import pickle, json, gzip, sys
from fractions import Fraction as F
import numpy as np
import kuhn3p as K

NAME = K.PARAM_NAME; I = K.NAME_IDX
U, MIX, DC = 9, 2, 3
NV = 48

_D = None


def D_all():
    global _D
    if _D is None: _D = pickle.load(open("D_all.pkl", "rb"))
    return _D


def deriv(poly, w):
    """d(poly)/dx_w for a MULTILINEAR monomial dict -> monomial dict."""
    out = {}
    for mon, c in poly.items():
        if mon[w]:
            m2 = list(mon); m2[w] = 0
            t = tuple(m2); out[t] = out.get(t, F(0)) + c
    return {m: c for m, c in out.items() if c}


def jac():
    """J[v][w] = dD_v/dx_w, only the nonzero entries."""
    D = D_all(); J = []
    for v in range(NV):
        row = {}
        vars_ = set()
        for mon in D[v]:
            for w, e in enumerate(mon):
                if e: vars_.add(w)
        for w in sorted(vars_):
            d = deriv(D[v], w)
            if d: row[w] = d
        J.append(row)
    return J


def ev(poly, x):
    """exact value of a monomial dict at x (list of Fractions)"""
    s = F(0)
    for mon, c in poly.items():
        t = c
        for w, e in enumerate(mon):
            if e:
                t *= x[w]
                if t == 0: break
        s += t
    return s


def profile_from(lab, vals):
    """full 48-vector of Fractions from a leaf's labels + a witness dict"""
    x = []
    for i in range(NV):
        n = NAME[i]
        if n in vals: x.append(vals[n])
        elif lab[i] == 0: x.append(F(0))
        elif lab[i] == 1: x.append(F(1))
        else: raise KeyError("no value for %s (label %s)" % (n, lab[i]))
    return x


# ---------------------------------------------------------------- first order

def taylor(poly, sig, delta_syms, order=2):
    """D(sigma + t*delta) as [P_0, P_1, ...]: P_k = the coefficient of t^k, a
    polynomial in the delta symbols (sympy), exact."""
    import sympy as sp
    out = [sp.Integer(0)] * (order + 1)
    for mon, c in poly.items():
        idx = [w for w, e in enumerate(mon) if e]
        # product over idx of (sig_w + t*d_w): collect by number of t factors
        terms = [sp.Integer(1)] + [sp.Integer(0)] * order
        for w in idx:
            s = sp.Rational(sig[w].numerator, sig[w].denominator); d = delta_syms[w]
            new = [sp.Integer(0)] * (order + 1)
            for k in range(order + 1):
                if terms[k] == 0: continue
                new[k] += terms[k] * s
                if k + 1 <= order: new[k + 1] += terms[k] * d
            terms = new
        cc = sp.Rational(c.numerator, c.denominator)
        for k in range(order + 1): out[k] += cc * terms[k]
    return [sp.expand(o) for o in out]


def lp_first_order(sig, J, verbose=False, require=None):
    """Selten's test at first order.  Variables: delta_v (sign-constrained by
    sigma), plus s >= 0 measuring how strictly the tremble enters.

        max s  s.t.  g_v(delta) = 0   where 0 < sigma_v < 1
                     g_v(delta) <= 0  where sigma_v = 0 and D_v(sigma) = 0
                     g_v(delta) >= 0  where sigma_v = 1 and D_v(sigma) = 0
                     delta_v >= s (sigma_v = 0),  -delta_v >= s (sigma_v = 1)
                     |delta_v| <= 1,  s <= 1

    -> (status, s, delta).  s > 0: a genuine inward direction exists (perfect
    at first order); s = 0: every direction leaves some coordinate untrembled
    (higher order decides); infeasible: sigma is NOT perfect, and not
    sequential either (no consistent belief supports it).
    `require`: optional {v: 0|1} forcing extra label conditions (used to ask
    what a candidate off-path value would need)."""
    import exlp
    D = D_all()
    Z = [v for v in range(NV) if sig[v] == 0]
    O = [v for v in range(NV) if sig[v] == 1]
    M = [v for v in range(NV) if 0 < sig[v] < 1]
    # columns: p_v (v in Z: delta_v = p_v >= 0) | n_v (v in O: delta_v = -n_v)
    #          | u_v, w_v (v in M: delta_v = u_v - w_v) | s
    col = {}; n = 0
    for v in Z: col[("p", v)] = n; n += 1
    for v in O: col[("n", v)] = n; n += 1
    for v in M: col[("u", v)] = n; n += 1; col[("w", v)] = n; n += 1
    cs = n; n += 1

    def gvec(v):
        """the row of g_v = grad D_v(sigma) . delta in the column space"""
        a = [F(0)] * n
        for w, dpoly in J[v].items():
            g = ev(dpoly, sig)
            if g == 0: continue
            if ("p", w) in col: a[col[("p", w)]] += g
            elif ("n", w) in col: a[col[("n", w)]] -= g
            else: a[col[("u", w)]] += g; a[col[("w", w)]] -= g
        return a

    A_ub = []; b_ub = []; A_eq = []; b_eq = []
    for v in range(NV):
        d0 = ev(D[v], sig)
        want = None
        if 0 < sig[v] < 1: want = "="
        elif sig[v] == 0 and d0 == 0: want = "<="
        elif sig[v] == 1 and d0 == 0: want = ">="
        if require and v in require:
            want = "=" if require[v] == "mix" else ("<=" if require[v] == 0 else ">=")
        if want is None: continue
        a = gvec(v)
        if want == "=": A_eq.append(a); b_eq.append(F(0))
        elif want == "<=": A_ub.append(a); b_ub.append(F(0))
        else: A_ub.append([-x for x in a]); b_ub.append(F(0))
    for v in Z + O:                      # s - delta_v <= 0  (delta_v >= s)
        a = [F(0)] * n; a[cs] = F(1); a[col[("p", v)] if v in Z else col[("n", v)]] = F(-1)
        A_ub.append(a); b_ub.append(F(0))
    c = [F(0)] * n; c[cs] = F(1)
    u = [F(1)] * n
    st, val, x = exlp.solve(c, A_ub, b_ub, A_eq, b_eq, u, maxpiv=20000)
    if st != "optimal": return st, None, None
    delta = [F(0)] * NV
    for (k, v), j in col.items():
        if k == "p": delta[v] += x[j]
        elif k == "n": delta[v] -= x[j]
        elif k == "u": delta[v] += x[j]
        else: delta[v] -= x[j]
    return st, val, delta


# --------------------------------------------------- the tremble system F(M)

def neg(poly): return {m: -c for m, c in poly.items()}


def tremble_system(lab, extra=()):
    """F(M) for a leaf's label vector, as dict-polys over ALL 48 coordinates,
    each of which is required to be strictly inside (0,1) (a completely mixed
    profile).  A coordinate the leaf pins to 0 or 1 keeps its CONDITION -- the
    prescribed action must still be optimal at the perturbed profile -- but not
    its value; a DC coordinate contributes nothing (its value is not fixed by
    the leaf, so no condition on it is imposed: the system is a relaxation and
    an emptiness proof is sound for every point of the leaf).
    `extra`: further (index, side) conditions, side in (0, 1, "mix")."""
    D = D_all()
    polys = []; kinds = []; orig = []
    for w in range(NV):
        if not D[w]: continue
        if lab[w] == MIX: polys.append(D[w]); kinds.append("="); orig.append(("D", w))
        elif lab[w] == 0: polys.append(neg(D[w])); kinds.append(">="); orig.append(("0", w))
        elif lab[w] == 1: polys.append(D[w]); kinds.append(">="); orig.append(("1", w))
    for v, side in extra:
        if not D[v]: continue
        if side == "mix": polys.append(D[v]); kinds.append("="); orig.append(("Dx", v))
        elif side == 1: polys.append(D[v]); kinds.append(">="); orig.append(("1x", v))
        else: polys.append(neg(D[v])); kinds.append(">="); orig.append(("0x", v))
    return polys, kinds, orig


OPEN_BOX = [(F(0), F(1), True, True)] * NV


def tremble_box(lab, eps, win=None):
    """The box of profiles that tremble AROUND the leaf: every coordinate is
    strictly inside (0,1) (completely mixed), a coordinate the leaf pins to 0
    is below eps, one pinned to 1 is above 1-eps, and a MIX / DC coordinate
    keeps its certified window over the leaf (Table 4) if one is given.
    Any perfect equilibrium of the leaf has trembles in this box for every
    eps > 0 and t small enough, so emptiness here is a sound forcing proof."""
    box = []
    for w in range(NV):
        lo, hi = F(0), F(1)
        if lab[w] == 0: hi = eps
        elif lab[w] == 1: lo = 1 - eps
        elif win and w in win:
            lo2, hi2 = win[w]
            lo = max(lo, lo2 - eps); hi = min(hi, hi2 + eps)
        box.append((lo, hi, True, True))
    return box


def forced(lab, v, side, eps=F(1, 10), maxnodes=400, win=None, extra=()):
    """Is the leaf's coordinate v forced to `side` (0 or 1) in every PERFECT
    (equivalently, by Lemma R1, extensive-form proper) equilibrium of the leaf?
    Proof obligation: the tremble system with the OPPOSITE condition on v is
    empty.  -> (True, certificate) or (False, None)."""
    import certbox
    opp = 1 if side == 0 else 0
    polys, kinds, orig = tremble_system(lab, extra=[(v, opp)] + list(extra))
    box = tremble_box(lab, eps, win)
    r = certbox.prove_empty_cert(polys, kinds, None, box, maxnodes,
                                 origins=orig, lab=None, gidx=None, chord=False, exact_dual=False)
    if r[0]:
        c = r[1]; c["origins_"] = [list(o) for o in orig]; c["eps"] = str(eps)
        return True, c
    return False, None


# ------------------------------------------- leading order in the tremble

_DR = None


def build_DR():
    """(D_v, R_v) as sympy expressions over the 48 symbols: the own-reach-
    stripped gradient and the reach of v's information set with the player's
    own earlier choices stripped.  D_v / R_v is the value difference at the
    set under the beliefs the profile induces, so its SIGN is what sequential
    rationality tests -- at an unreached set both vanish and the limit along a
    tremble is the belief-weighted difference."""
    global _DR
    if _DR is not None: return _DR
    import sympy as sp, tree as T
    X = [sp.Symbol(NAME[i]) for i in range(NV)]
    V = [[None] * T.NPOS for _ in range(T.ND)]
    for d in range(T.ND):
        for pos in T.LEAFPOS: V[d][pos] = [sp.Integer(int(T.PAYT[d, pos, i])) for i in range(3)]
        for pos in list(T.INTERNAL)[::-1]:
            x = X[T.COORD[d, pos]]
            V[d][pos] = [sp.expand(x * V[d][T.AGGC[pos]][i] + (1 - x) * V[d][T.PASC[pos]][i]) for i in range(3)]
    R = [[None] * T.NPOS for _ in range(T.ND)]
    for d in range(T.ND):
        R[d][0] = [sp.Integer(1)] * 3
        for pos in T.INTERNAL:
            x = X[T.COORD[d, pos]]; own = T.OWNER[pos][0]
            for c_, f in ((T.AGGC[pos], x), (T.PASC[pos], 1 - x)):
                R[d][c_] = [sp.expand(R[d][pos][i] * (1 if i == own else f)) for i in range(3)]
    D = [sp.Integer(0)] * NV; RE = [sp.Integer(0)] * NV
    for d in range(T.ND):
        for pos in T.INTERNAL:
            i = T.OWNER[pos][0]; v = T.COORD[d, pos]
            D[v] += sp.Rational(1, 24) * R[d][pos][i] * (V[d][T.AGGC[pos]][i] - V[d][T.PASC[pos]][i])
            RE[v] += sp.Rational(1, 24) * R[d][pos][i]
    _DR = ([sp.expand(e) for e in D], [sp.expand(e) for e in RE], X)
    return _DR


def tremble_subs(lab, X, eps):
    """x_w = eps*r_w where the leaf plays 0, 1 - eps*r_w where it plays 1, and
    the leaf's own free symbol elsewhere.  -> (substitution dict, r symbols)"""
    import sympy as sp
    sub = {}; r = {}
    for w in range(NV):
        if lab[w] == 0: r[w] = sp.Symbol("r_" + NAME[w]); sub[X[w]] = eps * r[w]
        elif lab[w] == 1: r[w] = sp.Symbol("r_" + NAME[w]); sub[X[w]] = 1 - eps * r[w]
    return sub, r


def leading(expr, eps):
    """(k, A): expr = eps^k * A + O(eps^(k+1)), A not identically zero."""
    import sympy as sp
    p = sp.Poly(sp.expand(expr), eps)
    cs = p.all_coeffs()[::-1]                     # index = power of eps
    for k, c in enumerate(cs):
        if sp.expand(c) != 0: return k, sp.expand(c)
    return None, sp.Integer(0)


def sign_definite(A, syms_nonneg):
    """A is a polynomial in variables that are all >= 0 on the domain.
    -> -1 if every coefficient is <= 0 (so A <= 0), +1 if all >= 0, else 0."""
    import sympy as sp
    P = sp.Poly(sp.expand(A), *syms_nonneg) if syms_nonneg else None
    if P is None: return 0
    cs = [c for c in P.coeffs()]
    if not cs: return 0
    if all(c <= 0 for c in cs): return -1
    if all(c >= 0 for c in cs): return +1
    return 0


def closure(lab, verbose=True):
    """ITERATED FORCING UNDER TREMBLES on one leaf.

    Every information set is reached at a completely mixed profile, so
    sequential rationality applies everywhere; at an unreached set the value
    difference is the limit of D_v / R_v along the tremble, whose leading
    coefficients A_v, B_v are polynomials in the tremble ratios r >= 0 and in
    the leaf's still-free coordinates.  If A_v has one sign on that domain the
    action is settled, the coordinate joins the pinned ones (trembling with
    its own ratio), and the pass repeats.  This is iterated strict dominance
    under trembles; it is sound for sequential, perfect and proper equilibria
    alike, since all three make the same demand at an unreached set.
    -> {coordinate: (value, 'dominance' | 'forced', A/B)}"""
    import sympy as sp
    D, R, X = build_DR()
    eps = sp.Symbol("eps", positive=True)
    pin = {w: int(lab[w]) for w in range(NV) if lab[w] in (0, 1)}
    out = {}; rnd = 0
    while True:
        rnd += 1
        sub = {}; rs = []
        for w, val in pin.items():
            rw = sp.Symbol("r_" + NAME[w]); rs.append(rw)
            sub[X[w]] = eps * rw if val == 0 else 1 - eps * rw
        free = [w for w in range(NV) if w not in pin]
        nonneg = rs + [X[w] for w in free]
        new = {}
        for v in free:
            if not D[v].free_symbols and D[v] == 0: continue
            kd, A = leading(D[v].subs(sub), eps)
            kr, B = leading(R[v].subs(sub), eps)
            if kd is None: continue
            s = sign_definite(A, nonneg)
            if s == 0: continue
            q = sp.cancel(A / B) if B != 0 else None
            why = "dominance" if (q is not None and q.is_number) else "forced"
            new[v] = (1 if s > 0 else 0, why, q)
        if not new: break
        for v, rec in new.items():
            pin[v] = rec[0]; out[v] = rec
            if verbose: print("   round %d: %-4s -> %d   (%s%s)" % (rnd, NAME[v], rec[0], rec[1], "" if rec[2] is None or not rec[2].is_number else ", value difference %s" % rec[2]), flush=True)
    return out, pin


def perfect_cert(sig, J=None):
    """A certificate that sigma is (extensive-form) PERFECT, hence -- every
    information set here being binary -- extensive-form PROPER.

      1. an inward direction delta with delta_v > 0 wherever sigma_v = 0 and
         < 0 wherever sigma_v = 1 (so sigma + t*delta is completely mixed),
      2. the indifference of every interior coordinate preserved to first
         order, and the deterrence of every other one STRICT to first order --
         or the inequality true on the whole cube, which needs no order at all,
      3. the indifference Jacobian of full rank, so the implicit function
         theorem turns the direction into an actual curve of completely mixed
         profiles against which sigma is a best reply at every set.

    -> (True, data) or (False, reason)."""
    import sympy as sp
    D = D_all(); J = J or jac()
    st, val, delta = lp_first_order(sig, J)
    if st != "optimal": return False, "no first-order direction (%s)" % st
    if val == 0: return False, "no uniform inward direction (s* = 0)"
    tight = []
    for v in range(NV):
        d0 = ev(D[v], sig)
        if sig[v] in (0, 1) and d0 == 0:
            g = sum(ev(J[v][w], sig) * delta[w] for w in J[v])
            if g == 0:
                cs = list(D[v].values())
                ok = (sig[v] == 0 and all(c <= 0 for c in cs)) or (sig[v] == 1 and all(c >= 0 for c in cs))
                if not ok: tight.append(NAME[v])
    M = [i for i in range(NV) if 0 < sig[i] < 1 and ev(D[i], sig) == 0 and any(ev(J[i][w], sig) != 0 for w in J[i])]
    JM = sp.Matrix([[sp.Rational(ev(J[v][w], sig)) if w in J[v] else sp.Integer(0) for w in range(NV)] for v in M])
    rk = JM.rank()
    if tight: return False, "first-order tight and not sign-definite at %s" % ",".join(tight)
    if rk != len(M): return False, "indifference Jacobian rank %d < %d" % (rk, len(M))
    return True, {"s": val, "delta": delta, "rank": rk, "equations": [NAME[v] for v in M]}


_FEV = None


def fev_all(x):
    """float values of all 48 gradients at a float 48-vector (for search only;
    every claim is re-checked in Fractions)."""
    global _FEV
    if _FEV is None:
        D = D_all()
        _FEV = [[(float(c), [w for w, e in enumerate(mon) if e]) for mon, c in D[v].items()] for v in range(NV)]
    out = []
    for terms in _FEV:
        s_ = 0.0
        for c, idx in terms:
            t = c
            for w in idx: t *= x[w]
            s_ += t
        out.append(s_)
    return out
