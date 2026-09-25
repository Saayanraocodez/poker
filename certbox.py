"""Certificate-producing exact branch-and-bound: the same algorithm as
exactbox.prove_empty (contraction + rationally certified LP relaxation, split),
but every step is RECORDED so that checkcert.py can verify the emptiness proof
with fractions.Fraction only -- no sympy, no scipy, no LP solving.

A certificate for "the system {polys, kinds} has no point in `bounds`" is a
tree of nodes.  Each node holds
    box0    the box it starts from (the root's bounds, or the parent's
            contracted box with one bound moved to the split point),
    steps   the contraction trace: ('lo'|'hi', j, value, strict, ci) means
            "constraint ci, affine in x_j with a coefficient of determined
            sign on the current box, implies x_j >= / <= value" (the checker
            re-derives the implied bound from the constraint and the current
            box and accepts value if it is no stronger); ('kill', ci) means the
            range of constraint ci on the current box excludes its kind;
            ('empty', j) means box[j] is now empty,
    lp      when the node is closed by the LP relaxation: the rows' provenance
            (constraint / monotone-elimination / open endpoint / McCormick) and
            the dual multipliers y (rows), w (column upper bounds) with
            b.y + U.w <= 1 -- weak duality then bounds the slack variable
            eps' = eps + 1 by 1, i.e. no point with every strict constraint
            satisfied strictly exists in the box,
    split   otherwise (j, mid): the two children follow.
Rows of the LP are exactly exactbox.lp_infeasible's; here they carry their
provenance so the checker can rebuild and validate each one independently.

    prove_empty_cert(polys, kinds, gens, bounds, maxnodes) -> (True, cert) or
    (False, nodes, box).   cert is JSON-serialisable (Fractions as "p/q").
"""
from fractions import Fraction as F
import exactbox as X
import treebound as TB
import numpy as _np
from scipy.optimize import linprog as _linprog


def fstr(v): return "%d/%d" % (v.numerator, v.denominator)
def pstr(p): return [[list(m), fstr(c)] for m, c in p.items()]
def boxstr(box): return [[fstr(b[0]), fstr(b[1]), bool(b[2]), bool(b[3])] for b in box]


def contract_traced(cons, box, rounds=12):
    """exactbox.contract with a trace.  -> (alive, steps)"""
    steps = []
    for _ in range(rounds):
        changed = False
        mr = X._mranges(cons, box)
        for ci, (poly, kind, lin) in enumerate(cons):
            lo, hi = X._rng(poly, mr)
            if (kind == "=" and (lo > 0 or hi < 0)) or (kind == ">=" and hi < 0) or (kind == ">" and hi <= 0):
                steps.append(("kill", ci)); return False, steps
            strict = kind == ">"
            for j, a, g, afac in lin:
                al, ah = X._rng(a, mr)
                if al <= 0 <= ah: continue
                gl, gh = X._rng(g, mr)
                todo = []
                if kind in (">=", ">"):
                    if al > 0:  todo.append(("lo", X._div_lo(-gh, al, ah), strict))
                    else:       todo.append(("hi", X._div_hi(-gh, al, ah), strict))
                else:
                    if al > 0:
                        todo.append(("lo", X._div_lo(-gh, al, ah), False)); todo.append(("hi", X._div_hi(-gl, al, ah), False))
                    else:
                        todo.append(("hi", X._div_hi(-gh, al, ah), False)); todo.append(("lo", X._div_lo(-gl, al, ah), False))
                ch = False
                for side, v, st in todo:
                    if side == "lo":
                        v2 = X._floor(v)
                        if X._tighten_lo(box[j], v, st):
                            ch = True; steps.append(("lo", j, v2, st, ci))
                    else:
                        v2 = X._ceil(v)
                        if X._tighten_hi(box[j], v, st):
                            ch = True; steps.append(("hi", j, v2, st, ci))
                if ch:
                    changed = True
                    if X._empty(box[j]):
                        steps.append(("empty", j)); return False, steps
                    for m in mr:
                        if m[j]: mr[m] = X._mono_range(m, box)
        if not changed: break
    return True, steps


def _acc(*pairs):
    """sparse row from (column, coefficient) pairs, ADDING coefficients that land on
    the same column -- a dict literal keeps only the last one, which for a squared
    monomial (prefix = the variable itself, kj == kp) dropped a term and made the
    McCormick row unsound (caught by checkcert on leaf 1791 of b_M_M_0_MNR, 2026-09-21)."""
    d = {}
    for k, v in pairs: d[k] = d.get(k, F(0)) + v
    return d


def lp_rows(cons, box):
    """the LP relaxation of exactbox.lp_infeasible with row provenance.
    -> (monos, rows, kinds, b, U, E) where rows are sparse dicts over LP
    columns (monomial index, E = eps'), kinds '<=' or '=', and prov[i] tells
    the checker what row i is."""
    nv = len(box)
    monos = {}
    def mid(m):
        if m not in monos: monos[m] = len(monos)
        return monos[m]
    for poly, kind, lin in cons:
        for m in poly:
            if any(m): mid(m)
    mono_rows = X.monotone_rows(cons, box)
    for poly, kind in mono_rows:
        for m in poly:
            if any(m): mid(m)
    for j in range(nv): mid(tuple(1 if k == j else 0 for k in range(nv)))
    def prefix(m):
        j = max(t for t in range(nv) if m[t]); p = list(m); p[j] -= 1
        return tuple(p), j
    work = [m for m in monos if sum(m) >= 2]
    while work:
        m = work.pop(); p, j = prefix(m)
        if sum(p) >= 1 and p not in monos:
            mid(p)
            if sum(p) >= 2: work.append(p)
    n = len(monos) + 1; E = n - 1
    lo = [F(0)] * n; hi = [None] * n
    for m, k in monos.items(): lo[k], hi[k] = X._mono_range(m, box)
    lo[E] = F(0); hi[E] = F(2)
    A = []; b = []; kinds = []; prov = []
    def row(coefs, const, kind, pv):
        a = {}; c0 = F(const)
        for k, v in coefs.items():
            a[k] = a.get(k, F(0)) + v; c0 += v * lo[k]
        if kind == "=":
            A.append(a); b.append(-c0); kinds.append("=")
        elif kind == ">=":
            A.append({k: -x for k, x in a.items()}); b.append(c0); kinds.append("<=")
        else:
            a2 = {k: -x for k, x in a.items()}; a2[E] = a2.get(E, F(0)) + 1
            A.append(a2); b.append(c0 + 1); kinds.append("<=")
        prov.append(pv)
    # monotone rows need their provenance: which constraint, variable, end
    mono_prov = []
    mr = X._mranges(cons, box)
    for ci, (poly, kind, lin) in enumerate(cons):
        if kind == "=": continue
        for j, a, g, afac in lin:
            if afac is None:
                al, ah = X._rng(a, mr); sg = 1 if al >= 0 else (-1 if ah <= 0 else 0)
            else:
                sg = X._coef_sign(afac, mr)
            if sg > 0:   mono_prov.append(("mono", ci, j, 1, afac))
            elif sg < 0: mono_prov.append(("mono", ci, j, 0, afac))
    assert len(mono_prov) == len(mono_rows)
    allrows = [(p, k, ("cons", ci)) for ci, (p, k, _) in enumerate(cons)] + [(p, k, pv) for (p, k), pv in zip(mono_rows, mono_prov)]
    for poly, kind, pv in allrows:
        coefs = {}; const = F(0)
        for m, c in poly.items():
            if any(m): coefs[mid(m)] = coefs.get(mid(m), F(0)) + c
            else: const += c
        row(coefs, const, kind, pv)
    for j in range(nv):
        k = monos[tuple(1 if t == j else 0 for t in range(nv))]
        if box[j][2]: row({k: F(1)}, -box[j][0], ">", ("open", j, 0))
        if box[j][3]: row({k: F(-1)}, box[j][1], ">", ("open", j, 1))
    for m, k in list(monos.items()):
        if sum(m) >= 2:
            p, j = prefix(m)
            kp = monos[p]; kj = monos[tuple(1 if t == j else 0 for t in range(nv))]
            xl, xh = lo[kp], hi[kp]; yl, yh = box[j][0], box[j][1]
            row(_acc((k, F(1)), (kj, -xl), (kp, -yl)), xl * yl, ">=", ("mc", m, 0))
            row(_acc((k, F(1)), (kj, -xh), (kp, -yh)), xh * yh, ">=", ("mc", m, 1))
            row(_acc((k, F(-1)), (kj, xh), (kp, yl)), -xh * yl, ">=", ("mc", m, 2))
            row(_acc((k, F(-1)), (kj, xl), (kp, yh)), -xl * yh, ">=", ("mc", m, 3))
    U = [hi[k] - lo[k] for k in range(n)]
    return monos, A, b, kinds, prov, U, E


def _exact_dual(A2, b2, U, c, n, m2, M):
    """the dual of  max c.z - M s  s.t. A2 z - s <= b2, 0 <= z <= U, 0 <= s <= 10,
    solved EXACTLY by exlp's simplex:  min b2.y + U.w + 10 w_S  s.t.  A2^T y + w >= c,
    -sum y + w_S >= -M,  y, w >= 0.  Always feasible and bounded.  -> (y3, w3) or None"""
    import exlp
    nv = m2 + n + 1
    cd = [-bb for bb in b2] + [-u for u in U] + [F(-10)]
    Ad = []; bd = []
    for k in range(n):
        row = [-A2[i].get(k, F(0)) for i in range(m2)] + [F(0)] * (n + 1); row[m2 + k] = F(-1)
        Ad.append(row); bd.append(-c[k])
    Ad.append([F(1)] * m2 + [F(0)] * n + [F(-1)]); bd.append(M)
    st, val, yw = exlp.solve(cd, Ad, bd, [], [], [None] * nv, maxpiv=6000)
    if st != "optimal": return None
    return yw[:m2], yw[m2:m2 + n]


def lp_certificate(cons, box, exact=True):
    """-> (dead, cert_or_hint).  dead: cert = {'rows': [...], 'w': [...], 'bound': F}
    proving max eps' <= 1 by weak duality (equality rows may carry either sign).
    HiGHS proposes the duals (rounded to rationals, repaired); when that does
    not give a bound <= 1 -- at a family corner the float duals are off by
    ~1e-13 and no rounding fixes it -- the dual LP is solved exactly."""
    monos, A, b, kinds, prov, U, E = lp_rows(cons, box)
    n = len(U); m = len(A)
    # equality rows split into two <= rows for the solver
    A2 = []; b2 = []; src = []
    for i in range(m):
        A2.append(A[i]); b2.append(b[i]); src.append((i, 1))
        if kinds[i] == "=":
            A2.append({k: -v for k, v in A[i].items()}); b2.append(-b[i]); src.append((i, -1))
    S = n; M = F(1000)
    A3 = [{**r, S: F(-1)} for r in A2]
    c = [F(0)] * n + [-M]; c[E] = F(1)
    U3 = U + [F(10)]
    Af = _np.zeros((len(A3), n + 1))
    for i, r in enumerate(A3):
        for k, v in r.items(): Af[i, k] = float(v)
    bf = _np.array([float(x) for x in b2]); cf = _np.array([float(x) for x in c])
    try:
        res = _linprog(-cf, A_ub=Af, b_ub=bf, bounds=[(0.0, float(u)) for u in U3], method="highs")
    except Exception:
        res = None
    if res is None or res.status != 0:
        return _finish_exact(A, A2, b, b2, kinds, prov, U, E, c, src, monos, n, len(A2), M) if exact else (False, None)
    if -res.fun > 1.0 + 1e-7:
        # relaxation point -> branching hint as in exactbox
        lo = [F(0)] * n
        for mm, k in monos.items(): lo[k] = X._mono_range(mm, box)[0]
        val = {mm: float(lo[k]) + res.x[k] for mm, k in monos.items()}
        nv = len(box); best = None
        for mm, k in monos.items():
            if sum(mm) >= 2:
                j = max(t for t in range(nv) if mm[t]); p = list(mm); p[j] -= 1; p = tuple(p)
                gap = abs(val[mm] - val[p] * val[tuple(1 if t == j else 0 for t in range(nv))])
                if best is None or gap > best[0]: best = (gap, mm)
        return False, best
    y3 = [max(F(0), F(float(v)).limit_denominator(10**12)) for v in -res.ineqlin.marginals]
    w3 = [max(F(0), F(float(v)).limit_denominator(10**12)) for v in -res.upper.marginals]
    # fold the split equality rows back: y_i = y+ - y-
    y = {}
    for (i, sg), v in zip(src, y3):
        if v: y[i] = y.get(i, F(0)) + sg * v
    y = {i: v for i, v in y.items() if v != 0}
    w = {k: w3[k] for k in range(n) if w3[k]}
    # dual feasibility on the z columns (repair w upwards where needed), then the bound
    aty = [F(0)] * n
    for i, yi in y.items():
        for k, v in A[i].items(): aty[k] += v * yi
    for k in range(n):
        r = aty[k] + w.get(k, F(0)) - c[k]
        if r < 0: w[k] = w.get(k, F(0)) - r
    bnd = sum(b[i] * yi for i, yi in y.items()) + sum(U[k] * wk for k, wk in w.items())
    if bnd > 1 or any(kinds[i] == "<=" and yi < 0 for i, yi in y.items()):
        return _finish_exact(A, A2, b, b2, kinds, prov, U, E, c, src, monos, n, len(A2), M) if exact else (False, None)
    return True, _pack(A, b, kinds, prov, U, E, monos, y, w, bnd)


def _finish_exact(A, A2, b, b2, kinds, prov, U, E, c, src, monos, n, m2, M):
    r = _exact_dual(A2, b2, U, c, n, m2, M)
    if r is None: return False, None
    y3, w3 = r
    y = {}
    for (i, sg), v in zip(src, y3):
        if v: y[i] = y.get(i, F(0)) + sg * v
    w = {k: w3[k] for k in range(n) if w3[k]}
    aty = [F(0)] * n
    for i, yi in y.items():
        for k, v in A[i].items(): aty[k] += v * yi
    for k in range(n):
        rk = aty[k] + w.get(k, F(0)) - c[k]
        if rk < 0: w[k] = w.get(k, F(0)) - rk
    bnd = sum(b[i] * yi for i, yi in y.items()) + sum(U[k] * wk for k, wk in w.items())
    if bnd > 1 or any(kinds[i] == "<=" and yi < 0 for i, yi in y.items()):
        return False, None
    return True, _pack(A, b, kinds, prov, U, E, monos, y, w, bnd)


def _pack(A, b, kinds, prov, U, E, monos, y, w, bnd):
    # only the rows with a nonzero multiplier matter to weak duality (a column
    # touched by no such row has reduced cost 0 - w_k <= 0 trivially satisfied
    # with w_k = 0); store those rows with their provenance and multiplier
    inv = {k: mm for mm, k in monos.items()}
    rows_out = []
    for i, yi in y.items():
        pv = prov[i]
        if pv[0] == "mono":
            afac = pv[4]
            fac = None if afac is None else [fstr(afac[0]), [[pstr(fp), e] for fp, e in afac[1]]]
            pv_out = ["mono", pv[1], pv[2], pv[3], fac]
        elif pv[0] == "mc": pv_out = ["mc", list(pv[1]), pv[2]]
        else: pv_out = list(pv)
        rows_out.append([pv_out, fstr(yi)])
    w_out = [["E" if k == E else list(inv[k]), fstr(v)] for k, v in w.items() if v]
    return {"rows": rows_out, "w": w_out, "bound": fstr(bnd)}


def ser_step_(s):
    if s[0] in ("kill", "empty"): return [s[0], s[1]]
    if s[0] == "tree": return ["tree", int(s[1]), s[2]]
    if s[0] in ("tlo", "thi"): return [s[0], s[1], fstr(s[2])]
    if s[0] == "chord": return ["chord", s[1], fstr(s[2]), fstr(s[3])]
    if s[0] == "cdead": return ["cdead", s[1], int(s[2]), s[3]]
    return [s[0], s[1], fstr(s[2]), bool(s[3]), s[4]]


def prove_empty_cert(polys, kinds, gens, bounds, maxnodes=20000, origins=None, lab=None, gidx=None, chord=True, exact_dual=True):
    """exactbox.prove_empty with a certificate.  polys: sympy exprs or dict-polys."""
    cons = X.prepare(polys, kinds, gens, factor=gens is not None)     # dict polys with gens None: no factor certificates
    if cons is None:
        return True, {"trivial": "a constraint is identically 0 with kind '>'"}
    nodes_out = []
    stack = [([list(b) for b in bounds], -1, None)]
    nodes = 0
    while stack:
        box, parent, split = stack.pop(); nodes += 1
        rec = {"parent": parent, "split": None if split is None else [split[0], fstr(split[1]), split[2]], "box0": boxstr(box)}
        idx = len(nodes_out); nodes_out.append(rec)
        alive, steps = contract_traced(cons, box)
        # exact tree-structured bounds on D (treebound): the D-condition of the
        # leaf's labels kills the box or pins a DC coordinate; then contract again
        slopes = None
        # cheap path first: contraction + LP closes most nodes in ~0.3 s; the
        # tree-structured rules and the chord contractor (~1-2 s) only where it does not
        if alive:
            dead, hint = lp_certificate(cons, box, exact=False)
            if dead:
                rec["steps"] = [ser_step_(s) for s in steps]; rec["lp"] = hint; continue
        if alive and lab is not None:
            for _ in range(4):
                r = TB.tree_rules(lab, gidx, box)
                if r is None: break
                if r[0] == "dead":
                    steps.append(("tree", r[1], r[2])); alive = False; break
                for side, t, v in r:
                    if side == "lo": X._tighten_lo(box[t], v, False); steps.append(("tlo", t, v))
                    else:            X._tighten_hi(box[t], v, False); steps.append(("thi", t, v))
                    if X._empty(box[t]):
                        steps.append(("empty", t)); alive = False; break
                if not alive: break
                alive2, steps2 = contract_traced(cons, box); steps.extend(steps2)
                if not alive2: alive = False; break
            # exact chord contractor (treebound.chord_contract), a few rounds
            for _ in range(3 if (alive and chord) else 0):
                cst, slopes = TB.chord_contract(lab, gidx, box, X._floor, X._ceil)
                steps.extend(cst)
                if cst and cst[-1][0] == "cdead": alive = False; break
                if not cst: break
                alive2, steps2 = contract_traced(cons, box); steps.extend(steps2)
                if not alive2: alive = False; break
                r = TB.tree_rules(lab, gidx, box)
                if r is not None and r[0] == "dead":
                    steps.append(("tree", r[1], r[2])); alive = False; break
        rec["steps"] = [ser_step_(s) for s in steps]
        if not alive: continue
        dead, hint = lp_certificate(cons, box, exact=exact_dual)  # exact dual simplex as the last resort
        if dead:
            rec["lp"] = hint; continue
        if nodes > maxnodes:
            return False, nodes, box
        j = None
        if hint is not None and hint[0] > 1e-9:
            m = hint[1]
            cand = [t for t in range(len(box)) if m[t] and box[t][1] > box[t][0]]
            if cand: j = max(cand, key=lambda t: box[t][1] - box[t][0])
        if j is None and slopes is not None:
            # bnb6's idea as the fallback: split where the pinned bound moves the most per unit width
            sc = [(slopes[t] * (box[t][1] - box[t][0]), t) for t in range(len(box)) if box[t][1] > box[t][0]]
            if sc and max(sc)[0] > 0: j = max(sc)[1]
        if j is None: j = X._choose(cons, box)
        w = box[j][1] - box[j][0]
        if w == 0: return False, nodes, box
        mid = (box[j][0] + box[j][1]) / 2
        rec["splitvar"] = j; rec["mid"] = fstr(mid)
        b1 = [list(b) for b in box]; b2 = [list(b) for b in box]
        b1[j][1] = mid; b1[j][3] = False
        b2[j][0] = mid; b2[j][2] = False
        stack.append((b2, idx, (j, mid, 1))); stack.append((b1, idx, (j, mid, 0)))
    cert = {"nvars": len(bounds), "kinds": [k for p, k, _ in cons], "bounds": boxstr(bounds), "nodes": nodes_out}
    if origins is not None:
        # prepare() drops identically-zero polynomials: keep the origins of the rows that survived
        kept = [t for t, (p, k) in enumerate(zip(polys, kinds)) if (X.to_poly(p, gens) if not isinstance(p, dict) else p)]
        assert len(kept) == len(cons)
        cert["origins"] = [list(origins[t]) for t in kept]
    else:
        cert["polys"] = [pstr(p) for p, k, _ in cons]
    return True, cert
