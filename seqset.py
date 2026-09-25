"""THE SEQUENTIAL-EQUILIBRIUM SET, exactly, on the complete Nash set.

Input: the 12 FAMILY leaves whose D-systems are the whole Nash set (nefull.py,
PAPER_KIT Theorem 5).  A Nash profile is a SEQUENTIAL equilibrium iff there is
a consistent belief system making the action at every UNREACHED information set
optimal.  In this game consistency has an explicit form: perturb the profile by
x_w = eps*r_w where it plays 0 and 1 - eps*r_w where it plays 1 (r >= 0, one
scale eps), so every set is reached, and let eps -> 0.  The value difference at
set v is D_v / R_v (symbet's own-reach-stripped gradient over the set's reach);
at an unreached set both vanish with eps and the limit is

        A_v(s, r) / B_v(s, r)        (leading coefficients in eps),

the belief-weighted difference -- the beliefs are the ratios r, shared by every
set at once, which is exactly Kreps-Wilson consistency here.  Sequential
rationality is then a sign condition on A_v, and SEQUENTIAL EQUILIBRIUM =

   leaf's Nash system  +  for every unreached v:  A_v <= 0 if x_v = 0,
                                                 A_v >= 0 if x_v = 1,
                                                 A_v  = 0 if 0 < x_v < 1
   +  r >= 0, sum r = 1.

r >= 0 (rather than r > 0) is the closure of the belief set: trembles of
different orders are its boundary, so an EMPTINESS proof on this system is
sound for every consistent belief system, while a witness with r > 0 is a
genuine sequential equilibrium.  Every information set here is BINARY, so the
same conditions decide extensive-form properness and (with the indifference of
the reached sets maintained under the tremble) perfection -- see refine.py.

The unreached coordinates are enumerated 0 / 1 / interior, depth first, with
certbox killing a partial assignment as soon as its system is empty.

usage:  python seqset.py [workers] [leaf ...]
"""
import numpy as np, sympy as sp, sys, time, json, gzip, os
from fractions import Fraction as F
import kuhn3p as K, symleaf as SL, certbox, refine

NAME = K.PARAM_NAME; I = K.NAME_IDX
U, MIX, DC = 9, 2, 3
EPS = sp.Symbol("eps", positive=True)
FAM = [18, 62, 70, 72, 77, 97, 99, 196, 198, 211, 440, 469]


def leaf_pieces(lab):
    """-> (nash polys/kinds, free syms, A_v, B_v, r syms, unreached list)"""
    D, R, X = refine.build_DR()
    pin = {w: int(lab[w]) for w in range(48) if lab[w] in (0, 1)}
    sub = {}; rsym = {}
    for w, val in pin.items():
        rw = sp.Symbol("r_" + NAME[w]); rsym[w] = rw
        sub[X[w]] = EPS * rw if val == 0 else 1 - EPS * rw
    A = {}; B = {}; unreached = []
    for v in range(48):
        kd, a = refine.leading(sp.expand(D[v].subs(sub)), EPS)
        kr, b = refine.leading(sp.expand(R[v].subs(sub)), EPS)
        A[v] = a; B[v] = b
        if v in pin: continue
        if kd is None or kd > 0: unreached.append(v)      # D vanishes at the leaf: off path
    XX, syms, G = SL.build(lab)
    mixv = [i for i in range(48) if lab[i] == MIX]; dcv = [i for i in range(48) if lab[i] == DC]
    polys, kinds = SL._sys(lab, G, mixv, XX)
    return polys, kinds, syms, A, B, rsym, unreached, mixv, dcv


def rgroups(rs):
    """Group the tremble ratios by the information set they belong to (P1's
    openings a_j1, P1's check-calls a_j2, P3's c_j2, ...).  Every leading
    coefficient is HOMOGENEOUS within one group, so each group may be scaled on
    its own: normalising group by group (sum = 1) is without loss of generality
    and, unlike one global simplex, it forbids the degenerate solutions in which
    a whole group's ratios vanish -- the case would then be decided at a higher
    order, which is what the ordering enumeration covers."""
    g = {}
    for r in rs:
        n = str(r)[2:]
        g.setdefault(n[0] + n[2], []).append(r)
    return g


def build_case(lab, pieces, assign, strict_r=False):
    """The system for a partial assignment {v: 0 | 1 | 'mix'} of the unreached
    coordinates: the leaf's Nash conditions, the decided coordinates' values
    and belief conditions, and the tremble ratios on the simplex.
    -> (polys, kinds, gens, bounds, degenerate) ; degenerate lists the
    coordinates whose leading coefficient collapsed under the substitution
    (their condition is then imposed at the next order, handled by the caller)."""
    polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = pieces
    sub = {}
    for v, val in assign.items():
        if val in (0, 1): sub[syms[v]] = sp.Integer(val)
    P = []; Kd = []; deg = []
    for p, k in zip(polys, kinds):
        q = sp.expand(p.subs(sub))
        if q == 0:
            if k == ">": return None, None, None, None, None      # 0 > 0
            continue
        P.append(q); Kd.append(k)
    for v, val in assign.items():
        a = sp.expand(A[v].subs(sub))
        if a == 0: deg.append(v); continue
        if val == 0: P.append(-a); Kd.append(">=")
        elif val == 1: P.append(a); Kd.append(">=")
        else: P.append(a); Kd.append("=")
    rs = sorted(set().union(*[set(s for s in sp.expand(A[v].subs(sub)).free_symbols if str(s).startswith("r_"))
                              for v in unreached] + [set()]), key=str)
    gens = [syms[i] for i in sorted(syms) if syms[i] not in sub] + rs
    for grp in rgroups(rs).values():
        P.append(sum(grp) - 1); Kd.append("=")
    bounds = []
    for g in gens:
        if str(g).startswith("r_"): bounds.append((F(0), F(1), strict_r, False))
        else:
            i = I[str(g)]
            bounds.append((F(0), F(1), lab[i] == MIX or assign.get(i) == "mix", lab[i] == MIX or assign.get(i) == "mix"))
    return P, Kd, gens, bounds, deg


def empty(P, Kd, gens, bounds, maxnodes=300):
    r = certbox.prove_empty_cert(P, Kd, gens, bounds, maxnodes, chord=False, exact_dual=False)
    return (True, r[1]) if r[0] else (False, None)


def propagate(lab, pieces, assign):
    """Cheap forcing at a node: with the decided values substituted, a leading
    coefficient whose coefficients are all of one sign settles its coordinate
    (every variable left -- a probability or a tremble ratio -- is >= 0).
    -> new assignments, or None on a contradiction."""
    polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = pieces
    sub = {syms[v]: sp.Integer(val) for v, val in assign.items() if val in (0, 1)}
    out = {}
    for v in unreached:
        if v in assign: continue
        a = sp.expand(A[v].subs(sub))
        if a == 0: continue
        vs = sorted(a.free_symbols, key=str)
        s = refine.sign_definite(a, vs) if vs else (1 if a > 0 else -1)
        if s == 0: continue
        out[v] = 1 if s > 0 else 0
    return out


def dfs(lab, pieces, order, budget=60, leaf_budget=400, log=None):
    """Depth-first over the unreached coordinates (0 / 1 / interior), pruning
    with an emptiness certificate.  -> (surviving full assignments, stats)"""
    polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = pieces
    alive = []; stats = {"nodes": 0, "killed": 0, "forced": 0, "degenerate": 0}
    stack = [({}, 0)]
    while stack:
        assign, di = stack.pop(); stats["nodes"] += 1
        fo = propagate(lab, pieces, assign)
        if fo:
            bad = any(v in assign and assign[v] != val for v, val in fo.items())
            if bad: stats["killed"] += 1; continue
            assign = dict(assign); assign.update({v: val for v, val in fo.items() if v not in assign})
            stats["forced"] += len(fo)
        rest = [v for v in order if v not in assign]
        P, Kd, gens, bounds, deg = build_case(lab, pieces, assign)
        if P is None: stats["killed"] += 1; continue
        if deg: stats["degenerate"] += 1
        e, cert = empty(P, Kd, gens, bounds, leaf_budget if not rest else budget)
        if e: stats["killed"] += 1; continue
        if not rest:
            alive.append((dict(assign), [str(g) for g in gens], deg))
            if log: log("   ALIVE %s%s" % (fmt_assign(assign), "  (degenerate at %s)" % ",".join(NAME[v] for v in deg) if deg else ""))
            continue
        v = rest[0]
        for val in ("mix", 1, 0):
            a2 = dict(assign); a2[v] = val; stack.append((a2, di + 1))
    return alive, stats


def fmt_assign(assign):
    return " ".join("%s=%s" % (NAME[v], "mix" if val == "mix" else val) for v, val in sorted(assign.items()))


def is_sequential(pieces, sval, lab):
    """At a FIXED Nash point the belief conditions are LINEAR in the tremble
    ratios, so sequentiality is one exact LP:  max m  s.t.  r_i >= m, sum r = 1,
    A_v(s, r) <= 0 / >= 0 / = 0 by the point's own labels.
      m > 0  : sequential, and r is an explicit consistent belief system;
      m = 0  : only with trembles of different orders (boundary case);
      infeasible : NOT sequential, by a Farkas certificate."""
    import exlp
    polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = pieces
    sub = {syms[i]: sp.Rational(sval[i].numerator, sval[i].denominator) for i in sorted(syms)}
    rows = []
    for v in unreached:
        a = sp.expand(A[v].subs(sub))
        if a == 0: continue
        x = sval[v]
        rows.append((a, "=" if 0 < x < 1 else (">=" if x == 1 else "<=")))
    rs = sorted(set().union(*[set(a.free_symbols) for a, _ in rows] + [set()]), key=str)
    if not rs: return "no tremble", None, None
    n = len(rs) + 1                      # r's and m
    A_ub = []; b_ub = []; A_eq = []; b_eq = []
    for a, k in rows:
        p = sp.Poly(a, *rs)
        co = [F(0)] * n
        const = F(0)
        for mono, c in zip(p.monoms(), p.coeffs()):
            cf = F(int(sp.nsimplify(c).p), int(sp.nsimplify(c).q))
            if sum(mono) == 0: const += cf; continue
            if sum(mono) != 1: return "nonlinear", None, None
            co[mono.index(1)] += cf
        if k == "=": A_eq.append(co); b_eq.append(-const)
        elif k == "<=": A_ub.append(co); b_ub.append(-const)
        else: A_ub.append([-c for c in co]); b_ub.append(const)
    for j in range(len(rs)):             # m - r_j <= 0
        co = [F(0)] * n; co[-1] = F(1); co[j] = F(-1); A_ub.append(co); b_ub.append(F(0))
    idx = {g: j for j, g in enumerate(rs)}        # one simplex PER INFORMATION SET
    for grp in rgroups(rs).values():
        co = [F(0)] * n
        for g in grp: co[idx[g]] = F(1)
        A_eq.append(co); b_eq.append(F(1))
    c = [F(0)] * n; c[-1] = F(1)
    st, val, x = exlp.solve(c, A_ub, b_ub, A_eq, b_eq, [F(1)] * n, maxpiv=20000)
    if st != "optimal": return st, None, None
    return ("sequential" if val > 0 else "boundary"), val, {str(g): x[j] for j, g in enumerate(rs)}


def relead(lab, assign, v):
    """Recompute ONE coordinate's leading coefficient with every coordinate the
    assignment puts at 0 or 1 trembling with its own ratio (needed exactly when
    substituting the value collapses the precomputed leading coefficient)."""
    D, R, X = refine.build_DR()
    sub = {}
    for w in range(48):
        val = assign.get(w, int(lab[w]) if lab[w] in (0, 1) else None)
        if val in (0, 1):
            rw = sp.Symbol("r_" + NAME[w]); sub[X[w]] = EPS * rw if val == 0 else 1 - EPS * rw
    kd, a = refine.leading(sp.expand(D[v].subs(sub)), EPS)
    return a


def exact_pieces(lab, assign):
    """Leading coefficients recomputed with EVERY coordinate the assignment
    puts at 0 or 1 trembling with its own ratio (the cheap version substitutes
    the value into a precomputed A, which is right unless that kills the whole
    leading coefficient).  -> (A, B, syms, nash polys/kinds)"""
    D, R, X = refine.build_DR()
    pin = {w: int(lab[w]) for w in range(48) if lab[w] in (0, 1)}
    for v, val in assign.items():
        if val in (0, 1): pin[v] = int(val)
    sub = {}
    for w, val in pin.items():
        sub[X[w]] = EPS * sp.Symbol("r_" + NAME[w]) if val == 0 else 1 - EPS * sp.Symbol("r_" + NAME[w])
    A = {}; B = {}
    for v in range(48):
        kd, a = refine.leading(sp.expand(D[v].subs(sub)), EPS)
        kr, b = refine.leading(sp.expand(R[v].subs(sub)), EPS)
        A[v] = a; B[v] = b
    return A, B, pin


def full_case_system(lab, pieces, assign, strict_r=None):
    """The exact system of one complete assignment: the leaf's Nash conditions
    with the assignment substituted, every unreached coordinate's belief
    condition at its true leading order, and the ratios on the simplex."""
    polys, kinds, syms, A, B0, rsym, unreached, mixv, dcv = pieces
    pin = {w: int(lab[w]) for w in range(48) if lab[w] in (0, 1)}
    for v, val in assign.items():
        if val in (0, 1): pin[v] = int(val)
    sub = {syms[v]: sp.Integer(val) for v, val in assign.items() if val in (0, 1)}
    P = []; Kd = []; why = []
    for p, k in zip(polys, kinds):
        q = sp.expand(p.subs(sub))
        if q == 0:
            if k == ">": return None
            continue
        P.append(q); Kd.append(k); why.append("nash")
    for v in range(48):
        if v not in pin and v not in assign: continue
        val = assign.get(v, pin.get(v))
        a = sp.expand(A[v].subs(sub))
        if a == 0:
            a = relead(lab, assign, v)             # the substitution collapsed it: next order
            if a == 0: continue
        if val == 0: P.append(-a); Kd.append(">=")
        elif val == 1: P.append(a); Kd.append(">=")
        else: P.append(a); Kd.append("=")
        why.append("belief:" + NAME[v])
    rs = sorted({s for p in P for s in p.free_symbols if str(s).startswith("r_")}, key=str)
    gens = [syms[i] for i in sorted(syms) if syms[i] not in sub] + rs
    for key, grp in sorted(rgroups(rs).items()):
        P.append(sum(grp) - 1); Kd.append("="); why.append("simplex:" + key)
    bounds = []
    for g in gens:
        if str(g).startswith("r_"):
            bounds.append((strict_r if strict_r else F(0), F(1), False, False))
        else:
            i = I[str(g)]; op = lab[i] == MIX or assign.get(i) == "mix"
            bounds.append((F(0), F(1), op, op))
    return P, Kd, gens, bounds, why


def family_point(b11, b21, b23, c11, off):
    """An exact family profile (Table 2 + Table 3) with the off-path
    coordinates given by `off` -- a dict name -> Fraction.  The result is a
    candidate only; every constraint is verified exactly by the caller."""
    beta = max(b11, b21)
    p = {n: F(0) for n in NAME.values()} if isinstance(NAME, dict) else {}
    p = {K.PARAM_NAME[i]: F(0) for i in range(48)}
    p["a33"] = F(1, 2); p["a41"] = F(0)
    p["a42"] = p["a43"] = p["a44"] = F(1)
    p["b11"] = b11; p["b21"] = b21; p["b23"] = b23
    p["b33"] = F(1, 2) + (b11 + b21) / 2 + beta / 2 - b23 * (1 - b21)
    p["b41"] = 2 * (b11 + b21)
    p["b42"] = p["b43"] = p["b44"] = F(1)
    p["c11"] = c11; p["c21"] = F(1, 2) - c11
    p["c41"] = p["c42"] = p["c43"] = p["c44"] = F(1)
    p.update(off)
    return [p[K.PARAM_NAME[i]] for i in range(48)]


def verify_point(lab, sval):
    """Exact check that a 48-profile satisfies the leaf's labels and its Nash
    system (the D-condition everywhere).  -> None if fine, else the failure."""
    D = refine.D_all()
    for i in range(48):
        x = sval[i]
        if lab[i] == 0 and x != 0: return "%s must be 0" % NAME[i]
        if lab[i] == 1 and x != 1: return "%s must be 1" % NAME[i]
        if lab[i] == MIX and not (0 < x < 1): return "%s must be interior" % NAME[i]
        if not (0 <= x <= 1): return "%s out of [0,1]" % NAME[i]
    for i in range(48):
        x = sval[i]
        d = refine.ev(D[i], sval)
        if x == 0 and d > 0: return "D_%s > 0 at 0" % NAME[i]
        if x == 1 and d < 0: return "D_%s < 0 at 1" % NAME[i]
        if 0 < x < 1 and d != 0: return "D_%s != 0 at an interior %s" % (NAME[i], NAME[i])
    return None


GRID = [F(0), F(1, 8), F(1, 6), F(1, 5), F(1, 4), F(1, 3), F(1, 2), F(5, 8), F(3, 4), F(7, 8), F(1)]
INNER = [F(1, 8), F(1, 4), F(1, 3), F(1, 2), F(5, 8), F(3, 4), F(7, 8)]


def witness_for(lab, pieces, assign, tries=None):
    """Search for an EXACT sequential equilibrium with this off-path pattern:
    a family point (Table 2 + 3) whose free parameters and interior off-path
    values come from a small rational grid, verified against the leaf's whole
    Nash system, together with a strictly positive belief vector from the exact
    LP.  -> (profile, beliefs) or None."""
    import itertools
    free_par = [n for n in ("b11", "b21", "b23", "c11") if lab[I[n]] not in (0, 1)]
    fixed = {n: F(int(lab[I[n]])) for n in ("b11", "b21", "b23", "c11") if lab[I[n]] in (0, 1)}
    mixed = [v for v, val in assign.items() if val == "mix"]
    if tries is None: tries = 3000 if len(mixed) <= 2 else (600 if len(mixed) <= 4 else 200)
    n = 0
    for pars in itertools.product(GRID, repeat=len(free_par)):
        pv = dict(zip(free_par, pars)); pv.update(fixed)
        for vals in itertools.product(INNER, repeat=len(mixed)):
            n += 1
            if n > tries: return None
            off = {}
            for v, val in assign.items():
                if val in (0, 1): off[NAME[v]] = F(int(val))
            off.update({NAME[v]: x for v, x in zip(mixed, vals)})
            for i in range(48):
                if lab[i] == 0: off.setdefault(NAME[i], F(0))
                elif lab[i] == 1: off.setdefault(NAME[i], F(1))
            for nm in ("b11", "b21", "b23", "c11"): off.pop(nm, None)
            s = family_point(pv["b11"], pv["b21"], pv["b23"], pv["c11"], off)
            if verify_point(lab, s) is not None: continue
            st, m, r = is_sequential(pieces, s, lab)
            if st == "sequential": return s, r, {}
    return None


def leading_at(lab, sval, orders):
    """Leading coefficients when coordinate w trembles at its OWN order:
    x_w = eps^k_w r_w (or 1 - eps^k_w r_w).  Kreps-Wilson consistency allows
    trembles of different orders, and that is exactly what this parametrises --
    orders all 1 is the uniform-scale case."""
    D, R, X = refine.build_DR()
    sub = {}
    for w in range(48):
        x = sval[w]
        if x in (0, 1):
            rw = sp.Symbol("r_" + NAME[w]); k = orders.get(w, 1)
            sub[X[w]] = EPS ** k * rw if x == 0 else 1 - EPS ** k * rw
        else:
            sub[X[w]] = sp.Rational(x.numerator, x.denominator)
    A = {}
    for v in range(48):
        kd, a = refine.leading(sp.expand(D[v].subs(sub)), EPS)
        A[v] = a
    return A


def seq_layered(lab, sval, rounds=4):
    """Sequentiality with trembles of different orders: solve the belief LP at
    uniform scale; if no strictly positive belief exists, the ratios the LP
    pins to zero are pushed to the next order and the pass repeats.
    -> (status, orders, beliefs)"""
    import exlp
    orders = {w: 1 for w in range(48) if sval[w] in (0, 1)}
    for it in range(rounds):
        A = leading_at(lab, sval, orders)
        rows = []
        for v in range(48):
            a = sp.expand(A[v])
            if a == 0: continue
            x = sval[v]
            rows.append((a, "=" if 0 < x < 1 else (">=" if x == 1 else "<=")))
        rs = sorted({s for a, _ in rows for s in a.free_symbols if str(s).startswith("r_")}, key=str)
        if not rs: return "no tremble", orders, None
        st, m, sol, maxr = _lp(rows, rs)
        if st != "optimal": return "not sequential", orders, None
        if m > 0: return "sequential", orders, sol
        zero = [w for w in range(48) if sval[w] in (0, 1) and ("r_" + NAME[w]) in [str(g) for g in rs]
                and maxr.get("r_" + NAME[w], 0) == 0]
        if not zero: return "boundary", orders, None
        for w in zero: orders[w] = orders[w] + 1
    return "boundary", orders, None


def _lp(rows, rs, want_max=True):
    """max m s.t. the sign conditions, r >= m, sum r = 1; also the largest each
    r can be on its own (to see which ratios are pinned to zero)."""
    import exlp
    n = len(rs) + 1
    A_ub = []; b_ub = []; A_eq = []; b_eq = []
    for a, k in rows:
        p = sp.Poly(a, *rs); co = [F(0)] * n; const = F(0); ok = True
        for mono, c in zip(p.monoms(), p.coeffs()):
            cf = F(int(sp.nsimplify(c).p), int(sp.nsimplify(c).q))
            if sum(mono) == 0: const += cf
            elif sum(mono) == 1: co[mono.index(1)] += cf
            else: ok = False; break
        if not ok: continue                      # nonlinear in r: drop (a relaxation)
        if k == "=": A_eq.append(co); b_eq.append(-const)
        elif k == "<=": A_ub.append(co); b_ub.append(-const)
        else: A_ub.append([-c for c in co]); b_ub.append(const)
    for j in range(len(rs)):
        co = [F(0)] * n; co[-1] = F(1); co[j] = F(-1); A_ub.append(co); b_ub.append(F(0))
    idx = {g: j for j, g in enumerate(rs)}
    for grp in rgroups(rs).values():
        co = [F(0)] * n
        for g in grp: co[idx[g]] = F(1)
        A_eq.append(co); b_eq.append(F(1))
    c = [F(0)] * n; c[-1] = F(1)
    st, val, x = exlp.solve(c, A_ub, b_ub, A_eq, b_eq, [F(1)] * n, maxpiv=20000)
    if st != "optimal": return st, None, None, {}
    maxr = {}
    for j, g in enumerate(rs if want_max else []):
        cj = [F(0)] * n; cj[j] = F(1)
        s2, v2, x2 = exlp.solve(cj, A_ub, b_ub, A_eq, b_eq, [F(1)] * n, maxpiv=20000)
        maxr[str(g)] = v2 if s2 == "optimal" else F(0)
    return st, val, {str(g): x[j] for j, g in enumerate(rs)}, maxr


def ordered_partitions(items):
    """every way to order `items` into non-empty classes (ties allowed):
    class 0 trembles at the largest scale, class 1 infinitely less, ..."""
    if not items: yield {}; return
    n = len(items)
    def rec(rest, lvl):
        if not rest: yield {}; return
        for mask in range(1, 1 << len(rest)):
            grp = [rest[i] for i in range(len(rest)) if mask >> i & 1]
            oth = [rest[i] for i in range(len(rest)) if not mask >> i & 1]
            for tail in rec(oth, lvl + 1):
                d = {g: lvl for g in grp}; d.update(tail); yield d
    seen = set()
    for d in rec(list(items), 0):
        key = tuple(sorted(d.items()))
        if key in seen: continue
        seen.add(key); yield d


GROUPS = [("a11", "a21", "a31", "a41"), ("b11", "b21", "b31", "b41"),
          ("c11", "c21", "c31", "c41"), ("a12", "a22", "a32", "a42"),
          ("c12", "c22", "c32", "c42")]


def seq_orderings_any(lab, sval, pieces=None, groups=None):
    """seq_orderings over each candidate group in turn: at the corner leaves the
    beliefs come from P2's or P3's trembles, not P1's openings."""
    for g in (groups or GROUPS):
        st, order, sol = seq_orderings(lab, sval, pieces, g)
        if st == "sequential": return st, {("%s" % k): v for k, v in order.items()}, sol
    return "boundary", None, None


def seq_orderings(lab, sval, pieces=None, group=("a11", "a21", "a31", "a41")):
    """SEQUENTIALITY, complete over tremble orders within one group.

    A belief at an unreached set is the limit of the reach ratios, so only the
    RELATIVE order of the trembles that reach it matters: in a linear leading
    form, the terms of the lowest class (the largest trembles) survive and the
    rest vanish.  Enumerating the ordered partitions of the group therefore
    covers every consistent belief system obtainable by varying those orders.
    -> (status, ordering, beliefs)"""
    if pieces is None: pieces = leaf_pieces(lab)
    polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = pieces
    sub = {syms[i]: sp.Rational(sval[i].numerator, sval[i].denominator) for i in sorted(syms)}
    rows = []
    for v in unreached:
        a = sp.expand(A[v].subs(sub))
        if a == 0: continue
        x = sval[v]
        rows.append((v, a, "=" if 0 < x < 1 else (">=" if x == 1 else "<=")))
    gsym = {sp.Symbol("r_" + n): n for n in group}
    best = ("not sequential", None, None)
    for order in ordered_partitions(list(group)):
        rr = []
        for v, a, k in rows:
            p = sp.expand(a)
            lv = min([order[gsym[s]] for s in p.free_symbols if s in gsym], default=None)
            if lv is not None:
                drop = {s: 0 for s in p.free_symbols if s in gsym and order[gsym[s]] > lv}
                p = sp.expand(p.subs(drop))
            if p == 0: continue
            rr.append((p, k))
        rs = sorted({s for p, _ in rr for s in p.free_symbols if str(s).startswith("r_")}, key=str)
        if not rs: continue
        st, m, sol, maxr = _lp(rr, rs, want_max=False)
        if st == "optimal" and m > 0: return "sequential", order, sol
        if st == "optimal" and best[0] == "not sequential": best = ("boundary", order, None)
    return best


def numeric_guess(lab, pieces, assign, tries=3):
    """A float point of the case system (family parameters + the interior
    off-path values), used only to aim the exact search."""
    import numpy as np, scipy.optimize as so
    polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = pieces
    free_par = [n for n in ("b11", "b21", "b23", "c11") if lab[I[n]] not in (0, 1)]
    mixed = [v for v, val in assign.items() if val == "mix"]
    names = free_par + [NAME[v] for v in mixed]
    if not names: return []
    D = refine.D_all()

    def point(z):
        off = {}
        for v, val in assign.items():
            if val in (0, 1): off[NAME[v]] = F(int(val))
        for i in range(48):
            if lab[i] == 0: off.setdefault(NAME[i], F(0))
            elif lab[i] == 1: off.setdefault(NAME[i], F(1))
        pv = {}
        for j, n in enumerate(names):
            q = F(float(min(max(z[j], 0.0), 1.0))).limit_denominator(64)
            if n in free_par: pv[n] = q
            else: off[n] = q
        for n in ("b11", "b21", "b23", "c11"):
            if n not in pv: pv[n] = F(int(lab[I[n]])) if lab[I[n]] in (0, 1) else F(0)
            off.pop(n, None)
        return family_point(pv["b11"], pv["b21"], pv["b23"], pv["c11"], off), pv

    def cost(z):
        s, _ = point(z)
        xf = [float(q) for q in s]
        dd = refine.fev_all(xf); c = 0.0
        for i in range(48):
            d = dd[i]; x = xf[i]
            if x == 0.0: c += max(0.0, d) ** 2
            elif x == 1.0: c += max(0.0, -d) ** 2
            else: c += d * d
        return c
    out = []
    rng = np.random.default_rng(0)
    for t in range(tries):
        z0 = rng.uniform(0.05, 0.6, len(names)) if t else np.full(len(names), 0.2)
        r = so.minimize(cost, z0, method="Nelder-Mead", options={"maxiter": 250, "xatol": 1e-3, "fatol": 1e-9})
        out.append(r.x)
    return out


def witness_guided(lab, pieces, assign):
    """Exact witness aimed by the numeric guess: snap to small denominators,
    verify every constraint exactly, then solve the belief LP."""
    import itertools
    free_par = [n for n in ("b11", "b21", "b23", "c11") if lab[I[n]] not in (0, 1)]
    mixed = [v for v, val in assign.items() if val == "mix"]
    names = free_par + [NAME[v] for v in mixed]
    for z in numeric_guess(lab, pieces, assign):
        for den in (2, 3, 4, 6, 8, 12, 16, 24, 32):
            off = {}
            for v, val in assign.items():
                if val in (0, 1): off[NAME[v]] = F(int(val))
            for i in range(48):
                if lab[i] == 0: off.setdefault(NAME[i], F(0))
                elif lab[i] == 1: off.setdefault(NAME[i], F(1))
            pv = {}
            ok = True
            for j, n in enumerate(names):
                q = F(int(round(min(max(float(z[j]), 0.0), 1.0) * den)), den)
                if n not in free_par and not (0 < q < 1): ok = False; break
                if n in free_par: pv[n] = q
                else: off[n] = q
            if not ok: continue
            for n in ("b11", "b21", "b23", "c11"):
                if n not in pv: pv[n] = F(int(lab[I[n]])) if lab[I[n]] in (0, 1) else F(0)
                off.pop(n, None)
            s = family_point(pv["b11"], pv["b21"], pv["b23"], pv["c11"], off)
            if verify_point(lab, s) is not None: continue
            st, m, r = is_sequential(pieces, s, lab)
            if st == "sequential": return s, r, {}
            st2, order, sol = seq_orderings_any(lab, s, pieces)
            if st2 == "sequential": return s, sol, order
    return None


def one_signed_conflict(lab, pieces, assign):
    """An ASSIGNED coordinate whose leading form is one-signed in its own ratios
    must take that sign's value (propagate only settles unassigned ones).  With
    every variable left >= 0, all-negative coefficients mean the form is < 0
    whenever any of its ratios survives, at whatever order they live -- so the
    coordinate is 0, never interior or 1.  -> the offending coordinate, or None."""
    polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = pieces
    sub = {syms[v]: sp.Integer(val) for v, val in assign.items() if val in (0, 1)}
    for v, val in assign.items():
        if v not in unreached: continue
        a = sp.expand(A[v].subs(sub))
        if a == 0: continue
        vs = sorted(a.free_symbols, key=str)
        if not vs: continue
        sgn = refine.sign_definite(a, vs)
        if sgn < 0 and val != 0: return v
        if sgn > 0 and val != 1: return v
    return None


def ordering_system(lab, pieces, assign, group, order):
    """The case system under one ordering of a tremble group: every form keeps
    only the terms of ITS OWN lowest class of that group, and the group's ratios
    are normalised class by class (sum = 1 per class), so no class can vanish.
    Other groups are normalised per set as before."""
    built = full_case_system(lab, pieces, assign)
    if built is None: return None
    P, Kd, gens, bounds, why = built
    gsym = {sp.Symbol("r_" + n): n for n in group}
    P2 = []; K2 = []
    for p, k, w in zip(P, Kd, why):
        if w.startswith("simplex"): continue
        fs = [s for s in p.free_symbols if s in gsym]
        if fs:
            lv = min(order[gsym[s]] for s in fs)
            p = sp.expand(p.subs({s: 0 for s in fs if order[gsym[s]] > lv}))
            if p == 0: continue
        P2.append(p); K2.append(k)
    rs = sorted({s for p in P2 for s in p.free_symbols if str(s).startswith("r_")}, key=str)
    classes = {}
    for r in rs:
        if r in gsym: classes.setdefault(("G", order[gsym[r]]), []).append(r)
        else:
            n = str(r)[2:]; classes.setdefault(("S", n[0] + n[2]), []).append(r)
    for grp in classes.values():
        P2.append(sum(grp) - 1); K2.append("=")
    gens2 = [g for g in gens if not str(g).startswith("r_")] + rs
    b2 = []
    for g in gens2:
        # a ratio IN a class of the ordering is the positive coefficient of eps^class:
        # strictly positive (being 0 would mean a higher class, which is another ordering)
        if g in gsym: b2.append((F(0), F(1), True, False))
        elif str(g).startswith("r_"): b2.append((F(0), F(1), False, False))
        else: b2.append(bounds[gens.index(g)])
    return P2, K2, gens2, b2


def kill_by_orderings(lab, pieces, assign, group, budget=400):
    """Sound kill: if under EVERY ordering of `group` the case system is empty,
    no consistent belief system supports the pattern (the group's forms alone
    already fail).  -> (True, n_orderings) or (False, first ordering not killed)."""
    n = 0
    for order in ordered_partitions(list(group)):
        sysd = ordering_system(lab, pieces, assign, group, order)
        n += 1
        if sysd is None: continue
        P, Kd, gens, bounds = sysd
        r = certbox.prove_empty_cert(P, Kd, gens, bounds, budget, chord=False, exact_dual=False)
        if not r[0]: return False, order
    return True, n
