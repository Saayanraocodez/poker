"""INDEPENDENT CHECKER for the leaf certificates written by certleaf.py
(certbox.py box certificates, nullcert.py cofactor certificates).

Nothing here solves anything.  fractions.Fraction arithmetic on dict-polynomials
{exponent tuple: Fraction}, and for every claimed step a direct re-derivation:

  * a leaf's system of necessary conditions is rebuilt from its labels and
    the own-reach-stripped gradients D_i (D_all.pkl, checked separately by
    checkD.py against the game tree):
        MIX i : D_i = 0          0 : -D_i >= 0        1 : D_i >= 0
        DC  i : x_i D_i >= 0  and  -(1 - x_i) D_i >= 0
        MIX i : 0 < x_i < 1 (open box)      DC : 0 <= x_i <= 1
    Every polynomial a certificate reasons with must be one of these (over the
    certificate's variables), a hypothesis the claim states explicitly (the
    h > 0 side of an identity or range), or a DERIVED polynomial with a
    cofactor certificate  p = sum_k q_k e_k (+ q_0 (1 - t f))  over the
    equalities e_k, verified by exact expansion.
  * a box certificate (certbox.py) is a tree; each node's start box is the
    root bounds or the parent's contracted box cut at the split point; every
    contraction step is re-derived from the named constraint and the current
    box (the claimed bound must be no stronger than the derived one); a node
    closed by the LP is verified by WEAK DUALITY: rows are rebuilt from their
    provenance and validated (constraint / monotone elimination with the
    coefficient sign re-proved / open endpoint present in the box / McCormick
    envelope of the box), then y >= 0 on inequality rows, A^T y + w >= c,
    b.y + U.w <= 1, which bounds eps' = eps + 1 by 1 on the relaxation:
    no point of the system lies in the box.
  * verdicts:  EMPTY  = a box certificate for the leaf system (possibly
    after derived rows replace originals), or 1 = sum q_k e_k, or a MIX
    coordinate forced to 0 / 1 on V(E), or an inequality whose derived form
    is a constant of the wrong sign;  FAMILY = pins by labels + every
    identity h = 0 (1 in <E, 1 - t h>, or box certificates for h > 0 and
    h < 0) + every range h <= 0 (box certificate for h > 0).

usage:  python checkcert.py cert_<tag>.json.gz [enum6_pat_<tag>.npy]
"""
import sys, json, gzip, pickle
from fractions import Fraction as F
import tree as _T          # the game tree (positions, owners, coordinates per deal, leaf payoffs)

MIX, DC, U = 2, 3, 9


class Bad(Exception):
    pass


def need(cond, msg):
    if not cond: raise Bad(msg)


# ---------------------------------------------------------------- polynomials
def fr(s):
    if isinstance(s, str):
        p, q = s.split("/"); return F(int(p), int(q))
    return F(s)


def poly(pl):
    out = {}
    for m, c in pl:
        m = tuple(m); c = fr(c)
        if c: out[m] = out.get(m, F(0)) + c
    return {m: c for m, c in out.items() if c}


def padd(p, q, s=F(1)):
    out = dict(p)
    for m, c in q.items():
        out[m] = out.get(m, F(0)) + s * c
    return {m: c for m, c in out.items() if c}


def pmul(p, q):
    out = {}
    for m1, c1 in p.items():
        for m2, c2 in q.items():
            m = tuple(a + b for a, b in zip(m1, m2))
            out[m] = out.get(m, F(0)) + c1 * c2
    return {m: c for m, c in out.items() if c}


def pscale(p, c): return {m: c * v for m, v in p.items()} if c else {}


def ppow(p, e, nv):
    out = {tuple([0] * nv): F(1)}
    for _ in range(e): out = pmul(out, p)
    return out


def mono_range(m, box):
    """every variable lies in [0, 1], so a monomial is monotone: [prod lo^e, prod hi^e]"""
    lo = F(1); hi = F(1)
    for j, e in enumerate(m):
        if e:
            need(box[j][0] >= 0, "negative lower bound")
            lo *= box[j][0] ** e; hi *= box[j][1] ** e
    return lo, hi


def prange(p, box):
    lo = F(0); hi = F(0)
    for m, c in p.items():
        ml, mh = mono_range(m, box)
        if c > 0: lo += c * ml; hi += c * mh
        else:     lo += c * mh; hi += c * ml
    return lo, hi


def split_lin(p, j):
    a = {}; g = {}
    for m, c in p.items():
        if m[j] == 0: g[m] = c
        elif m[j] == 1:
            mm = list(m); mm[j] = 0; a[tuple(mm)] = c
        else: raise Bad("constraint not affine in x_%d" % j)
    return a, g


def subst(p, j, val):
    out = {}
    for m, c in p.items():
        if m[j]:
            c = c * val ** m[j]; m = tuple(0 if t == j else v for t, v in enumerate(m))
        out[m] = out.get(m, F(0)) + c
    return {m: c for m, c in out.items() if c}


def var(j, nv): return {tuple(1 if t == j else 0 for t in range(nv)): F(1)}
def const(c, nv): return {tuple([0] * nv): F(c)} if c else {}


# ---------------------------------------------------------------- the leaf system
D_ALL = None
def leaf_system(lab):
    """-> (vars (coordinate indices), polys over 48 gens with labels substituted, kinds, open flags)"""
    global D_ALL
    if D_ALL is None: D_ALL = pickle.load(open("D_all.pkl", "rb"))
    def sub(p):
        out = {}
        for m, c in p.items():
            mm = list(m); skip = False
            for j, e in enumerate(m):
                if e and lab[j] == 0: skip = True; break
                if e and lab[j] == 1: mm[j] = 0
            if skip: continue
            mm = tuple(mm); out[mm] = out.get(mm, F(0)) + F(c)
        return {m: c for m, c in out.items() if c}
    D = {i: sub(D_ALL[i]) for i in range(48)}
    S = []
    for i in range(48):
        d = D[i]
        if not d: continue
        if lab[i] == MIX: S.append((d, "="))
        elif lab[i] == 0: S.append((pscale(d, F(-1)), ">="))
        elif lab[i] == 1: S.append((d, ">="))
        elif lab[i] == DC:
            x = var(i, 48)
            S.append((pmul(x, d), ">="))
            S.append((padd(pscale(d, F(-1)), pmul(x, d)), ">="))       # -(1 - x) D = -D + x D
        else: raise Bad("unassigned label")
    return S


def leaf_D(lab):
    """the 48 own-reach-stripped gradients with the leaf's 0/1 labels substituted (over 48 coordinates)"""
    global D_ALL
    if D_ALL is None: D_ALL = pickle.load(open("D_all.pkl", "rb"))
    out = {}
    for i in range(48):
        p = {}
        for m, cc in D_ALL[i].items():
            mm = list(m); skip = False
            for j, e in enumerate(m):
                if e and lab[j] == 0: skip = True; break
                if e and lab[j] == 1: mm[j] = 0
            if skip: continue
            mm = tuple(mm); p[mm] = p.get(mm, F(0)) + F(cc)
        out[i] = {m: cc for m, cc in p.items() if cc}
    return out


def lift(p, gens):
    """cert poly over gens (list of coordinate indices) -> poly over 48 gens"""
    out = {}
    for m, c in p.items():
        mm = [0] * 48
        for k, e in enumerate(m):
            if e: mm[gens[k]] += e
        out[tuple(mm)] = out.get(tuple(mm), F(0)) + c
    return {m: c for m, c in out.items() if c}


def is_member(p48, kind, S):
    for q, k in S:
        if k == kind and q == p48: return True
    return False


# ---------------------------------------------------------------- tree-structured bounds on D
_INT = list(_T.INTERNAL); _LEAF = list(_T.LEAFPOS)
_PAY = [[[F(int(_T.PAYT[d, pos, i])) for i in range(3)] for pos in range(_T.NPOS)] for d in range(_T.ND)]
_OWN = {pos: _T.OWNER[pos][0] for pos in _INT}


def tree_D_bounds(lo, hi):
    """[DLO_i, DHI_i] enclosing the own-reach-stripped gradient D_i over the
    48-box: continuation values V = P + x (A - P) (affine in x, monotone in A
    and P), the other players' reach as products of intervals in [0, 1], and
    D_i = (1/24) sum over the six nodes of R_{-k} (V_k(agg) - V_k(pass))."""
    DLO = [F(0)] * 48; DHI = [F(0)] * 48
    for d in range(_T.ND):
        Vlo = {}; Vhi = {}
        for pos in _LEAF: Vlo[pos] = _PAY[d][pos]; Vhi[pos] = _PAY[d][pos]
        for pos in _INT[::-1]:
            cc = _T.COORD[d, pos]; xl, xh = lo[cc], hi[cc]
            A_l, A_h = Vlo[_T.AGGC[pos]], Vhi[_T.AGGC[pos]]; P_l, P_h = Vlo[_T.PASC[pos]], Vhi[_T.PASC[pos]]
            Vlo[pos] = [min(P_l[i] + xl * (A_l[i] - P_l[i]), P_l[i] + xh * (A_l[i] - P_l[i])) for i in range(3)]
            Vhi[pos] = [max(P_h[i] + xl * (A_h[i] - P_h[i]), P_h[i] + xh * (A_h[i] - P_h[i])) for i in range(3)]
        Rlo = {0: [F(1)] * 3}; Rhi = {0: [F(1)] * 3}
        for pos in _INT:
            cc = _T.COORD[d, pos]; xl, xh = lo[cc], hi[cc]; own = _OWN[pos]
            Rlo[_T.AGGC[pos]] = [Rlo[pos][k] if k == own else Rlo[pos][k] * xl for k in range(3)]
            Rhi[_T.AGGC[pos]] = [Rhi[pos][k] if k == own else Rhi[pos][k] * xh for k in range(3)]
            Rlo[_T.PASC[pos]] = [Rlo[pos][k] if k == own else Rlo[pos][k] * (1 - xh) for k in range(3)]
            Rhi[_T.PASC[pos]] = [Rhi[pos][k] if k == own else Rhi[pos][k] * (1 - xl) for k in range(3)]
        for pos in _INT:
            k = _OWN[pos]; cc = _T.COORD[d, pos]
            dl = Vlo[_T.AGGC[pos]][k] - Vhi[_T.PASC[pos]][k]; dh = Vhi[_T.AGGC[pos]][k] - Vlo[_T.PASC[pos]][k]
            rl, rh = Rlo[pos][k], Rhi[pos][k]
            DLO[cc] += rl * dl if dl >= 0 else rh * dl
            DHI[cc] += rh * dh if dh >= 0 else rl * dh
    return [v / 24 for v in DLO], [v / 24 for v in DHI]


def check_tree_step(lab, gens, box, step):
    """('tree', i, rule): the box is dead by the D-condition at coordinate i;
    ('tlo'|'thi', t, value): DC coordinate gens[t] is pinned to 1 / 0 by the sign of D."""
    lo = [F(0)] * 48; hi = [F(1)] * 48
    for i in range(48):
        if lab[i] == 0: hi[i] = F(0)
        elif lab[i] == 1: lo[i] = F(1)
    for t, g in enumerate(gens): lo[g] = box[t][0]; hi[g] = box[t][1]
    need(all(0 <= lo[i] <= hi[i] <= 1 for i in range(48)), "48-box malformed")
    DLO, DHI = tree_D_bounds(lo, hi)
    if step[0] == "tree":
        i, rule = step[1], step[2]; l = lab[i]
        if rule == "mix":   need(l == MIX and (DLO[i] > 0 or DHI[i] < 0), "tree rule mix does not fire")
        elif rule == "one": need(l == 1 and DHI[i] < 0, "tree rule one does not fire")
        elif rule == "zero": need(l == 0 and DLO[i] > 0, "tree rule zero does not fire")
        elif rule == "dc>0": need(l == DC and lo[i] > 0 and DHI[i] < 0, "tree rule dc>0 does not fire")
        elif rule == "dc<1": need(l == DC and hi[i] < 1 and DLO[i] > 0, "tree rule dc<1 does not fire")
        else: raise Bad("unknown tree rule")
        return False
    t = step[1]; v = fr(step[2]); i = gens[t]
    need(lab[i] == DC, "tree pin on a non-DC coordinate")
    if step[0] == "tlo":
        need(v <= 1 and DLO[i] > 0, "tree pin to 1 not justified"); apply_lo(box[t], v, False)
    else:
        need(v >= 0 and DHI[i] < 0, "tree pin to 0 not justified"); apply_hi(box[t], v, False)
    return True


def check_chord_step(lab, gens, box, step):
    """('chord', t, lo, hi): the chord contractor's new bounds on gens[t], both derived
    from ONE pinned evaluation on the current box (neither may be stronger than
    re-derived here over every active condition); ('cdead', t, i, why): both pinned
    bounds violate a condition, or the two exclusions cross, or the box is empty."""
    lo = [F(0)] * 48; hi = [F(1)] * 48
    for i in range(48):
        if lab[i] == 0: hi[i] = F(0)
        elif lab[i] == 1: lo[i] = F(1)
    for t, g in enumerate(gens): lo[g] = box[t][0]; hi[g] = box[t][1]
    t = step[1]; v = gens[t]; w = hi[v] - lo[v]
    if step[0] == "cdead" and step[3] == "empty":
        need(box[t][0] > box[t][1], "box claimed empty is not"); return False
    need(w > 0, "chord step on a point")
    ge = [False] * 48; le = [False] * 48
    for i in range(48):
        l = lab[i]
        if l == MIX: ge[i] = le[i] = True
        elif l == 1: ge[i] = True
        elif l == 0: le[i] = True
        elif l == DC:
            if lo[i] > 0: ge[i] = True
            if hi[i] < 1: le[i] = True
    h0 = list(hi); h0[v] = lo[v]; L0, U0 = tree_D_bounds(lo, h0)
    l1 = list(lo); l1[v] = hi[v]; L1, U1 = tree_D_bounds(l1, hi)
    tlo = F(0); thi = F(1); dead = None
    for i in range(48):
        if i == v: continue
        if ge[i]:
            if U0[i] < 0 and U1[i] < 0: dead = dead or ("ge", i)
            if U0[i] < 0 <= U1[i]: tlo = max(tlo, -U0[i] / (U1[i] - U0[i]))
            if U1[i] < 0 <= U0[i]: thi = min(thi, U0[i] / (U0[i] - U1[i]))
        if le[i]:
            if L0[i] > 0 and L1[i] > 0: dead = dead or ("le", i)
            if L0[i] > 0 >= L1[i]: tlo = max(tlo, L0[i] / (L0[i] - L1[i]))
            if L1[i] > 0 >= L0[i]: thi = min(thi, -L0[i] / (L1[i] - L0[i]))
    if step[0] == "cdead":
        need(dead is not None or tlo > thi, "chord death not justified"); return False
    need(step[0] == "chord", "unknown chord step")
    nlo = fr(step[2]); nhi = fr(step[3])
    need(nlo <= lo[v] + w * tlo, "chord lower bound stronger than derived")
    need(nhi >= lo[v] + w * thi, "chord upper bound stronger than derived")
    apply_lo(box[t], nlo, False); apply_hi(box[t], nhi, False)
    return True


# ---------------------------------------------------------------- box certificates
def parse_box(b): return [[fr(x[0]), fr(x[1]), bool(x[2]), bool(x[3])] for x in b]


def box_empty(b): return b[0] > b[1] or (b[0] == b[1] and (b[2] or b[3]))


def apply_lo(b, v, strict):
    if v > b[0]: b[0] = v; b[2] = strict
    elif v == b[0] and strict: b[2] = True


def apply_hi(b, v, strict):
    if v < b[1]: b[1] = v; b[3] = strict
    elif v == b[1] and strict: b[3] = True


def check_step(polys, kinds, box, step):
    side, j, v, strict, ci = step; v = fr(v)
    p = polys[ci]; kind = kinds[ci]
    a, g = split_lin(p, j)
    al, ah = prange(a, box); gl, gh = prange(g, box)
    need(not (al <= 0 <= ah), "coefficient range contains 0")
    # implied bounds on x_j: a x_j + g {kind} 0
    derived = {}   # side -> (value, strict)
    if kind in (">=", ">"):
        if al > 0: derived["lo"] = (min(-gh / al, -gh / ah), kind == ">")
        else:      derived["hi"] = (max(-gh / al, -gh / ah), kind == ">")
    else:
        if al > 0:
            derived["lo"] = (min(-gh / al, -gh / ah), False); derived["hi"] = (max(-gl / al, -gl / ah), False)
        else:
            derived["hi"] = (max(-gh / al, -gh / ah), False); derived["lo"] = (min(-gl / al, -gl / ah), False)
    need(side in derived, "no bound of that side follows")
    dv, dst = derived[side]
    if side == "lo":
        need(v <= dv, "claimed lower bound stronger than derived")
        need((not strict) or dst or v < dv, "strictness not implied")
        apply_lo(box[j], v, strict)
    else:
        need(v >= dv, "claimed upper bound stronger than derived")
        need((not strict) or dst or v > dv, "strictness not implied")
        apply_hi(box[j], v, strict)


def check_kill(polys, kinds, box, ci):
    lo, hi = prange(polys[ci], box); k = kinds[ci]
    need((k == "=" and (lo > 0 or hi < 0)) or (k == ">=" and hi < 0) or (k == ">" and hi <= 0), "range does not exclude the constraint")


def coef_sign(a, box, fac, nv):
    """+1 / -1 if a >= 0 / <= 0 on the box: interval range, else the factorisation claimed"""
    al, ah = prange(a, box)
    if al >= 0: return 1
    if ah <= 0: return -1
    if fac is None: return 0
    c0 = fr(fac[0]); prod = const(c0, nv)
    sgn = 1 if c0 > 0 else -1
    for fp, e in fac[1]:
        fp = poly(fp); prod = pmul(prod, ppow(fp, e, nv))
        lo, hi = prange(fp, box)
        if lo >= 0: s_ = 1
        elif hi <= 0: s_ = -1
        elif e % 2 == 0: s_ = 1
        else: return 0
        if e % 2: sgn *= s_
    need(prod == a, "factorisation does not multiply out to the coefficient")
    return sgn


def check_lp(polys, kinds, box, lp, nv):
    """weak duality on the rows the certificate names.  Columns are the
    monomials occurring in those rows (z_m = m - lo_m in [0, hi_m - lo_m]) and
    E (eps' in [0, 2], objective 1).  A column no named row touches has
    reduced cost 0 + w_k - 0 >= 0 with w_k = 0, so it needs no check.
    A row  sum c_m m + c0 {>=, =, >} 0  reads, in the shifted columns,
        -sum c_m z_m + [e]  <=  c0 + sum c_m lo_m + [1]      (>= / >, the [.] for strict)
         sum c_m z_m        =  -(c0 + sum c_m lo_m)          (=)
    and with y >= 0 on the inequality rows, A^T y + w >= c, the objective
    e = c.z is at most b.y + U.w on every point of the relaxation."""
    rows = []
    for pv, yi in lp["rows"]:
        t = pv[0]
        if t == "cons":
            ci = pv[1]; rows.append((polys[ci], kinds[ci], fr(yi)))
        elif t == "mono":
            ci, j, end, fac = pv[1], pv[2], pv[3], pv[4]
            need(kinds[ci] != "=", "monotone row from an equality")
            a, g = split_lin(polys[ci], j)
            sg = coef_sign(a, box, fac, nv)
            need(sg == (1 if end == 1 else -1), "coefficient sign does not justify the substituted end")
            rows.append((subst(polys[ci], j, box[j][end]), kinds[ci], fr(yi)))
        elif t == "open":
            j, side = pv[1], pv[2]
            if side == 0:
                need(box[j][2], "lower endpoint not open"); rows.append((padd(var(j, nv), const(-box[j][0], nv)), ">", fr(yi)))
            else:
                need(box[j][3], "upper endpoint not open"); rows.append((padd(pscale(var(j, nv), F(-1)), const(box[j][1], nv)), ">", fr(yi)))
        elif t == "mc":
            m = tuple(pv[1]); tt = pv[2]
            need(sum(m) >= 2, "McCormick row on a monomial of degree < 2")
            j = max(t_ for t_ in range(nv) if m[t_]); p = list(m); p[j] -= 1; p = tuple(p)
            xl, xh = mono_range(p, box); yl, yh = box[j][0], box[j][1]
            P = {p: F(1)}; Xj = var(j, nv); Mm = {m: F(1)}
            if tt == 0: q = padd(padd(Mm, pscale(Xj, -xl)), padd(pscale(P, -yl), const(xl * yl, nv)))      # (P - xl)(x_j - yl) >= 0
            elif tt == 1: q = padd(padd(Mm, pscale(Xj, -xh)), padd(pscale(P, -yh), const(xh * yh, nv)))    # (P - xh)(x_j - yh) >= 0
            elif tt == 2: q = padd(padd(pscale(Mm, F(-1)), pscale(Xj, xh)), padd(pscale(P, yl), const(-xh * yl, nv)))   # (xh - P)(x_j - yl) >= 0
            else: q = padd(padd(pscale(Mm, F(-1)), pscale(Xj, xl)), padd(pscale(P, yh), const(-xl * yh, nv)))          # (P - xl)(yh - x_j) >= 0
            rows.append((q, ">=", fr(yi)))
        else: raise Bad("unknown row provenance %s" % t)
    cols = set()
    for p, k, yi in rows:
        for m in p:
            if any(m): cols.add(m)
    w = {}
    for key, v in lp["w"]:
        v = fr(v); need(v >= 0, "negative column multiplier")
        if key == "E": w["E"] = v
        else: m = tuple(key); cols.add(m); w[m] = v
    lo = {m: mono_range(m, box)[0] for m in cols}; hi = {m: mono_range(m, box)[1] for m in cols}
    aty = {m: F(0) for m in cols}; atyE = F(0); by = F(0)
    for p, k, yi in rows:
        need(k == "=" or yi >= 0, "negative multiplier on an inequality row")
        c0 = F(0); sgn = 1 if k == "=" else -1
        for m, c in p.items():
            if any(m): aty[m] += sgn * c * yi; c0 += c * lo[m]
            else: c0 += c
        if k == "=": by += yi * (-c0)
        else:
            by += yi * (c0 + (1 if k == ">" else 0))
            if k == ">": atyE += yi
    for m in cols:
        need(aty[m] + w.get(m, F(0)) >= 0, "dual infeasible at a monomial column")
    need(atyE + w.get("E", F(0)) >= 1, "dual infeasible at the eps column")
    bnd = by + sum((hi[m] - lo[m]) * v for m, v in w.items() if m != "E") + 2 * w.get("E", F(0))
    need(bnd <= 1, "dual bound %s exceeds 1" % bnd)


def check_box_cert(cert, rowof, lab=None):
    """cert: certbox certificate.  rowof(origin) -> (poly over the cert's gens, kind): the
    checker's own construction of the row the certificate names.  -> number of nodes."""
    if "trivial" in cert: return 0
    nv = cert["nvars"]; gens = cert["gens"]
    need(len(gens) == nv, "variable count mismatch")
    kinds = list(cert["kinds"])
    need("origins" in cert and len(cert["origins"]) == len(kinds), "certificate rows must be named by origin")
    polys = []
    for og, k in zip(cert["origins"], kinds):
        p, kk = rowof(tuple(og))
        need(kk == k, "row kind differs from the origin's kind")
        need(bool(p), "row polynomial is zero")
        polys.append(p)
    bounds = parse_box(cert["bounds"])
    nodes = cert["nodes"]
    final = [None] * len(nodes); children = {}; closed = [False] * len(nodes)
    for idx, rec in enumerate(nodes):
        box = parse_box(rec["box0"])
        if rec["parent"] == -1:
            need(box == bounds, "root box differs from the bounds")
        else:
            par = rec["parent"]; need(par < idx and final[par] is not None, "bad parent")
            j, mid, side = rec["split"]; mid = fr(mid)
            pb = [list(b) for b in final[par]]
            need(pb[j][0] <= mid <= pb[j][1], "split point outside the parent box")
            if side == 0: pb[j][1] = mid; pb[j][3] = False
            else: pb[j][0] = mid; pb[j][2] = False
            need(box == pb, "child box is not the parent's box cut at the split")
            children.setdefault(par, set()).add(side)
        alive = True
        for s in rec["steps"]:
            if s[0] == "kill": check_kill(polys, kinds, box, s[1]); alive = False; break
            if s[0] == "empty": need(box_empty(box[s[1]]), "box claimed empty is not"); alive = False; break
            if s[0] in ("tree", "tlo", "thi"):
                need(lab is not None, "tree step without labels")
                if not check_tree_step(lab, gens, box, s): alive = False; break
                continue
            if s[0] in ("chord", "cdead"):
                need(lab is not None, "chord step without labels")
                if not check_chord_step(lab, gens, box, s): alive = False; break
                continue
            check_step(polys, kinds, box, s)
        final[idx] = box
        if not alive: closed[idx] = True; continue
        if "lp" in rec:
            check_lp(polys, kinds, box, rec["lp"], nv); closed[idx] = True
        else:
            need("splitvar" in rec, "open node: neither closed nor split")
    for idx in range(len(nodes)):
        if not closed[idx]:
            need(children.get(idx) == {0, 1}, "split node without both children")
    return len(nodes)


# ---------------------------------------------------------------- cofactor certificates
def check_cofactors(target, gens_polys, q, nv):
    """target == sum_k q_k * gens_polys[k] ?"""
    acc = {}
    for qk, ek in zip(q, gens_polys):
        acc = padd(acc, pmul(qk, ek))
    need(acc == target, "cofactor identity fails")


def rowof_for(lab, gens):
    """the checker's own construction of a node's system rows, by origin, for a
    label vector (0/1/MIX/DC only) and the certificate's variables"""
    D48 = leaf_D(lab); nv = len(gens); pos = {g: t for t, g in enumerate(gens)}
    def project(p48):
        out = {}
        for m, cc in p48.items():
            mm = [0] * nv
            for j, e in enumerate(m):
                if e:
                    need(j in pos, "row uses a coordinate outside the certificate's variables")
                    mm[pos[j]] += e
            out[tuple(mm)] = out.get(tuple(mm), F(0)) + cc
        return {m: cc for m, cc in out.items() if cc}
    def rowof(og):
        t = og[0]; i = og[1]
        if t == "D":   need(lab[i] == MIX, "D row on a non-MIX coordinate"); return project(D48[i]), "="
        if t == "0":   need(lab[i] == 0, "label-0 row on another label"); return project(pscale(D48[i], F(-1))), ">="
        if t == "1":   need(lab[i] == 1, "label-1 row on another label"); return project(D48[i]), ">="
        if t == "DCx": need(lab[i] == DC, "DC row on a non-DC coordinate"); return project(pmul(var(i, 48), D48[i])), ">="
        if t == "DC1": need(lab[i] == DC, "DC row on a non-DC coordinate"); return project(padd(pscale(D48[i], F(-1)), pmul(var(i, 48), D48[i]))), ">="
        raise Bad("unknown row origin %s" % (og,))
    return rowof


# ---------------------------------------------------------------- one leaf
def check_leaf(lab, rec):
    """rec: {'verdict': ..., 'gens': [coord indices], 'E': [...], 'derived': [...], ...}
    -> verdict string checked."""
    S = leaf_system(lab)
    gens = rec["gens"]; nv = len(gens)
    # equalities of the leaf over gens
    E = [poly(p) for p in rec.get("E", [])]
    for e in E: need(is_member(lift(e, gens), "=", S), "E contains a non-equality of the leaf")
    derived = []          # (poly, kind) proven consequences
    for d in rec.get("derived", []):
        p = poly(d["poly"]); kind = d.get("kind")
        if d["how"] == "ideal":                # p - r = sum q_k e_k  with r the residual (r is then equivalent to p on V(E))
            q = [poly(x) for x in d["q"]]; r = poly(d["r"])
            check_cofactors(padd(p, r, F(-1)), E, q, nv)
            need(is_member(lift(p, gens), kind, S), "derived from a non-member")
            derived.append((r, kind))
        elif d["how"] == "gb":                 # a Groebner element g = sum q_k e_k : an equality consequence
            q = [poly(x) for x in d["q"]]; g = poly(d["poly"])
            check_cofactors(g, E, q, nv)
            derived.append((g, "="))
        else: raise Bad("unknown derivation")
    D48 = leaf_D(lab)
    def project(p48):
        """poly over 48 coordinates -> over gens (every variable present must be a gen)"""
        pos = {g: t for t, g in enumerate(gens)}
        out = {}
        for m, cc in p48.items():
            mm = [0] * nv
            for j, e in enumerate(m):
                if e:
                    need(j in pos, "row uses a coordinate outside the certificate's variables")
                    mm[pos[j]] += e
            out[tuple(mm)] = out.get(tuple(mm), F(0)) + cc
        return {m: cc for m, cc in out.items() if cc}
    def rowof_base(og, extra=()):
        t = og[0]
        if t == "D":   i = og[1]; need(lab[i] == MIX, "D row on a non-MIX coordinate"); return project(D48[i]), "="
        if t == "0":   i = og[1]; need(lab[i] == 0, "label-0 row on another label"); return project(pscale(D48[i], F(-1))), ">="
        if t == "1":   i = og[1]; need(lab[i] == 1, "label-1 row on another label"); return project(D48[i]), ">="
        if t == "DCx": i = og[1]; need(lab[i] == DC, "DC row on a non-DC coordinate"); return project(pmul(var(i, 48), D48[i])), ">="
        if t == "DC1": i = og[1]; need(lab[i] == DC, "DC row on a non-DC coordinate"); return project(padd(pscale(D48[i], F(-1)), pmul(var(i, 48), D48[i]))), ">="
        if t == "der": d = og[1]; need(d < len(derived), "derived row index"); return derived[d]
        if t == "hyp": u = og[1]; need(u < len(extra) - 1, "hypothesis index"); return extra[u]
        if t == "side": need(len(extra) >= 1, "no side row"); return extra[-1]
        raise Bad("unknown row origin %s" % (og,))
    v = rec["verdict"]
    if v == "EMPTY_BOX":
        check_box_cert(rec["cert"], lambda og: rowof_base(og), lab); return v
    if v == "EMPTY_GB":
        q = [poly(x) for x in rec["q"]]
        check_cofactors(const(1, nv), E, q, nv); return v
    if v == "EMPTY_MIX":
        # 1 = sum q_k e_k + q0 (1 - t f), f = x or 1 - x for a MIX coordinate: f = 0 on V(E)
        j = rec["coord"]; need(lab[gens[j]] == MIX, "not a MIX coordinate")
        f = var(j, nv) if rec["value"] == 0 else padd(const(1, nv), pscale(var(j, nv), F(-1)))
        _check_radical(E, f, rec, nv); return v
    if v == "EMPTY_CONST":
        d = rec["const"]; p = poly(d["poly"]); r = fr(d["r"]); kind = d["kind"]
        need(is_member(lift(p, gens), kind, S), "constant from a non-member")
        q = [poly(x) for x in d["q"]]
        check_cofactors(padd(p, const(r, nv), F(-1)), E, q, nv)
        need(r < 0 or (kind == ">" and r == 0), "residual constant has the right sign")
        return v
    if v == "FAMILY":
        for pin in rec["pins"]:
            i, val = pin; need(lab[i] == val, "pin %d not by label" % i)
        def reduced(item):
            """h, or its stated reduction hred with h - hred = sum q_k e_k verified"""
            h = poly(item["h"])
            if "red" in item:
                hr = poly(item["red"]["hred"]); q = [poly(x) for x in item["red"]["q"]]
                check_cofactors(padd(h, hr, F(-1)), E, q, nv); return hr
            return h
        for idn in rec["identities"]:
            h = reduced(idn); hyp = [(poly(x), k) for x, k in idn.get("hyp", [])]
            if idn["how"] == "zero": need(h == {}, "identity claimed to reduce to 0 does not")
            elif idn["how"] == "radical": _check_radical(E, h, idn, nv)
            elif idn["how"] == "box":
                for side, cert in ((1, idn["pos"]), (-1, idn["neg"])):
                    extra = hyp + [(pscale(h, F(side)), ">")]
                    check_box_cert(cert, lambda og, ex=extra: rowof_base(og, ex), lab)
            else: raise Bad("unknown identity proof")
        for rg in rec["ranges"]:
            h = reduced(rg)
            if rg["how"] == "const":
                r = fr(rg["r"]); need(h == const(r, nv), "range reduction is not the stated constant"); need(r <= 0, "range constant positive")
            elif rg["how"] == "box":
                check_box_cert(rg["cert"], lambda og, ex=[(h, ">")]: rowof_base(og, ex), lab)
            else: raise Bad("unknown range proof")
        return v
    raise Bad("verdict %s carries no certificate" % v)


def _check_radical(E, f, rec, nv):
    """1 = sum q_k e_k + q0 (1 - t f) in nv + 1 variables (t last)"""
    Et = [{m + (0,): c for m, c in e.items()} for e in E]
    ft = {m + (0,): c for m, c in f.items()}
    tf = {m + (1,): c for m, c in f.items()}
    one = {tuple([0] * (nv + 1)): F(1)}
    rab = padd(one, tf, F(-1))
    q = [poly(x) for x in rec["q"]]
    check_cofactors(one, Et + [rab], q, nv + 1)


if __name__ == "__main__":
    import numpy as np, time
    path = sys.argv[1]
    with gzip.open(path, "rt") as f: data = json.load(f)
    L = np.load(sys.argv[2]) if len(sys.argv) > 2 else np.load(data["leaves"])
    t0 = time.time(); ok = 0; bad = 0; cnt = {}
    for rec in data["leaves_cert"]:
        k = rec["leaf"]; lab = [int(x) for x in L[k]]
        try:
            v = check_leaf(lab, rec); ok += 1; cnt[v] = cnt.get(v, 0) + 1
        except Bad as ex:
            bad += 1; print("leaf %d: FAILED %s" % (k, ex))
        except Exception as ex:
            bad += 1; print("leaf %d: ERROR %r" % (k, ex))
    print("checked %d leaves: %d verified %s, %d failed  (%.0fs)" % (ok + bad, ok, cnt, bad, time.time() - t0))
