"""INDEPENDENT CHECKER for Theorem 6's pattern enumeration (seqcert_<leaf>.jsonl.gz).

No sympy, no seqset / refine / certbox: the belief forms are rebuilt from the game tree by
seqforms.py (Fractions), and box certificates are replayed by checkcert.check_box_cert.

For each leaf it checks
  1. the CLOSURE, coordinate by coordinate in the recorded order:
       dominance -- D_v = c R_v as polynomials, c != 0, and the value is 1 iff c > 0;
       robust    -- v's leading form (every 0/1 coordinate trembling) is ROBUSTLY one-signed
                    with the recorded value's sign;
  2. COVERAGE: every 0 / 1 / interior assignment of the decided coordinates extends a
     killed record or equals a witnessed one (records are prefixes in the decide order);
  3. every KILL:
       onesigned -- the named coordinate's form is robustly one-signed against its value;
       cert      -- the certificate replays, its rows rebuilt from their origins and its
                    starting box containing everything the case allows;
       orderings -- for EVERY ordered partition of the group (enumerated here, not read
                    from the file) there is a certificate, and each replays;
  4. every WITNESS as a concrete tremble curve x_w = eps^e_w rho_w (0-coordinates) or
     1 - eps^e_w rho_w (1-coordinates): an exact Nash point, and for every coordinate the
     limit of D_v / R_v along the curve has the sign its value demands.  That is
     Kreps-Wilson consistency with nothing left implicit.

Soundness restrictions (2026-09-26):
  * a belief row may enter a certificate only if its form is MULTI-HOMOGENEOUS in the
    information sets' ratios (every term has the same degree in each set) -- then scaling
    each set's ratios separately (the per-set simplex) cannot change any sign, and a form
    evaluated at the per-set lowest-class ratios is either 0 or the true leading term;
  * "robustly one-signed" means: linear in the ratios of ONE set, all coefficients of one
    sign, and every ratio appearing in a term whose profile factors are strictly interior
    -- so its lowest-class part cannot vanish under any ordering.

usage:  python checkseqcert.py [seqcert_<leaf>.jsonl.gz ...]
"""
import json, gzip, sys, glob, itertools
from fractions import Fraction as F
import numpy as np
import seqforms as SF
import checkcert as C
import kuhn3p as K

NAME = K.PARAM_NAME; I = K.NAME_IDX
MIX, DC = 2, 3
NX = 48


class Bad(Exception): pass
def need(c, msg):
    if not c: raise Bad(msg)


def vidx(name):
    """variable index in seqforms' 96-variable space for a certificate gen name"""
    return NX + I[name[2:]] if name.startswith("r_") else I[name]


def setkey_of(j):
    """information-set key of ratio variable j (48..95): player letter + decision digit"""
    n = NAME[j - NX]
    return n[0] + n[2]


def substitute_values(poly48, vals):
    """a dict-poly over the 48 x's with some coordinates replaced by Fractions -> 48-poly"""
    out = {}
    for m, c in poly48.items():
        cc = c; mm = list(m)
        for w, e in enumerate(m):
            if e and w in vals:
                cc *= vals[w] ** e; mm[w] = 0
                if cc == 0: break
        if cc:
            t = tuple(mm); out[t] = out.get(t, F(0)) + cc
    return {m: c for m, c in out.items() if c}


def lift(poly48):
    """48-variable dict-poly -> 96-variable dict-poly"""
    return {tuple(list(m) + [0] * NX): c for m, c in poly48.items()}


def pneg(p): return {m: -c for m, c in p.items()}


# ------------------------------------------------------------------ the case's forms
class Case:
    """one leaf with a (closure + case) assignment {coordinate: 0 | 1 | 'mix'}"""
    def __init__(self, lab, assign):
        self.lab = lab; self.assign = assign
        self.val01 = {v: F(x) for v, x in assign.items() if x in (0, 1)}
        self.pin0 = {w for w in range(NX) if lab[w] == 0 or assign.get(w) == 0}
        self.pin1 = {w for w in range(NX) if lab[w] == 1 or assign.get(w) == 1}
        self.openx = {w for w in range(NX) if lab[w] == MIX or assign.get(w) == "mix"}

    def value(self, v):
        if v in self.assign: return self.assign[v]
        if self.lab[v] in (0, 1): return int(self.lab[v])
        if self.lab[v] == MIX: return "mix"
        return None

    def belief(self, v):
        D, R = SF.DR()
        o, f = SF.leading(D[v], self.pin0, self.pin1)
        return f

    def nash_row(self, tag, i):
        """symleaf._sys's row for coordinate i with the leaf's 0/1 labels AND the case's
        0/1 values substituted as values."""
        D, R = SF.DR()
        leafvals = {w: F(int(self.lab[w])) for w in range(NX) if self.lab[w] in (0, 1)}
        G = substitute_values(D[i], leafvals)
        x_i = {tuple(1 if t == i else 0 for t in range(NX)): F(1)}
        if tag == "D": p, k = G, "="
        elif tag == "0": p, k = pneg(G), ">="
        elif tag == "1": p, k = G, ">="
        elif tag == "DCx": p, k = SF.pmul(x_i, G), ">="
        elif tag == "DC1": p, k = pneg(SF.pmul(SF.padd({tuple([0] * NX): F(1)}, x_i, F(-1)), G)), ">="
        else: raise Bad("unknown Nash row tag %r" % tag)
        return lift(substitute_values(p, self.val01)), k


def ratio_vars(p):
    return sorted({j for m in p for j in range(NX, 2 * NX) if m[j]})


def multi_homogeneous(p):
    """every term has the same degree in each information set's ratios"""
    prof = None
    for m in p:
        d = {}
        for j in range(NX, 2 * NX):
            if m[j]: d[setkey_of(j)] = d.get(setkey_of(j), 0) + m[j]
        if prof is None: prof = d
        elif d != prof: return False
    return True


def robust_sign(p, openx):
    """+1/-1 if p is robustly one-signed (see the module docstring), else 0"""
    if not p: return 0
    cs = list(p.values())
    s = 1 if all(c > 0 for c in cs) else (-1 if all(c < 0 for c in cs) else 0)
    if s == 0: return 0
    rv = ratio_vars(p)
    if not rv:
        xs = {j for m in p for j in range(NX) if m[j]}
        return s if xs <= openx else 0
    if len({setkey_of(j) for j in rv}) != 1: return 0
    for m in p:
        if sum(m[NX:]) != 1: return 0              # linear in the ratios
    for j in rv:
        if not any(m[j] and all((not m[w]) or w in openx for w in range(NX)) for m in p): return 0
    return s


# ------------------------------------------------------------------ rows by origin
def build_rowof(case, gens, order=None, group=None):
    """rowof(origin) -> (poly over the certificate's gens, kind), rebuilt independently"""
    gidx = [vidx(g) for g in gens]
    pos = {j: t for t, j in enumerate(gidx)}
    gset = {NX + I[n] for n in group} if group else set()

    def to_gens(p96):
        out = {}
        for m, c in p96.items():
            e = [0] * len(gens)
            for j, k in enumerate(m):
                if k:
                    need(j in pos, "row uses a variable (%s) the certificate does not declare" %
                         (NAME[j] if j < NX else "r_" + NAME[j - NX]))
                    e[pos[j]] = k
            t = tuple(e); out[t] = out.get(t, F(0)) + c
        return {m: c for m, c in out.items() if c}

    def rowof(og):
        og = tuple(og)
        if og[0] == "N":
            p, k = case.nash_row(og[1], int(og[2]))
            return to_gens(p), k
        if og[0] in ("B", "Bo"):
            v = int(og[1]); f = case.belief(v)
            need(f, "belief row for %s has no leading form" % NAME[v])
            need(multi_homogeneous(f), "belief row for %s is not multi-homogeneous in the sets' ratios" % NAME[v])
            if og[0] == "Bo":
                need(order is not None, "reduced row outside an ordering certificate")
                fs = [j for j in ratio_vars(f) if j in gset]
                if fs:
                    lv = min(order[NAME[j - NX]] for j in fs)
                    f = {m: c for m, c in f.items() if all(not m[j] or order[NAME[j - NX]] <= lv for j in fs)}
                need(f, "reduced belief row vanished")
            val = case.value(v)
            if val == 0: return to_gens(pneg(f)), ">="
            if val == 1: return to_gens(f), ">="
            need(val == "mix", "belief row for %s whose value is not fixed" % NAME[v])
            return to_gens(f), "="
        if og[0] == "S":
            members = [j for j in gidx if j >= NX and setkey_of(j) == og[1] and j not in gset]
            need(members, "empty simplex")
            p = {tuple(1 if t == pos[j] else 0 for t in range(len(gens))): F(1) for j in members}
            p[tuple([0] * len(gens))] = F(-1)
            return p, "="
        if og[0] == "Sc":
            members = [j for j in gidx if j in gset and order[NAME[j - NX]] == int(og[1])]
            need(members, "empty class simplex")
            p = {tuple(1 if t == pos[j] else 0 for t in range(len(gens))): F(1) for j in members}
            p[tuple([0] * len(gens))] = F(-1)
            return p, "="
        raise Bad("unknown row origin %r" % (og,))
    return rowof


def expected_box(case, gens, group=None):
    gset = {"r_" + n for n in group} if group else set()
    out = []
    for g in gens:
        if g.startswith("r_"):
            out.append([F(0), F(1), g in gset, False])
        else:
            i = I[g]
            need(case.lab[i] not in (0, 1) and case.assign.get(i) not in (0, 1),
                 "certificate variable %s is fixed by the case" % g)
            op = i in case.openx
            out.append([F(0), F(1), op, op])
    return out


def check_cert(case, cert, order=None, group=None):
    gens = cert["gens"]
    C.check_box_cert(cert, build_rowof(case, gens, order, group), None, expected_box(case, gens, group))


def system(case, full, order=None, group=None):
    """(origins, gens) of a case system -- the PROVER's choice of rows.  The checker never
    trusts this list: it rebuilds every row a certificate names from its origin."""
    rows = []
    for i in range(NX):
        tags = {MIX: ["D"], 0: ["0"], 1: ["1"], DC: ["DCx", "DC1"]}.get(case.lab[i], [])
        for t in tags:
            p, k = case.nash_row(t, i)
            if p: rows.append((("N", t, i), p))
    gset = {NX + I[n] for n in group} if group else set()
    which = [v for v in range(NX) if case.lab[v] in (0, 1) or v in case.assign] if full else list(case.assign)
    for v in which:
        f = case.belief(v)
        if not f or not multi_homogeneous(f): continue          # dropping a row is a relaxation
        if case.value(v) not in (0, 1, "mix"): continue
        if order is not None:
            fs = [j for j in ratio_vars(f) if j in gset]
            if fs:
                lv = min(order[NAME[j - NX]] for j in fs)
                f = {m: c for m, c in f.items() if all(not m[j] or order[NAME[j - NX]] <= lv for j in fs)}
                if not f: continue
                rows.append((("Bo", v), f)); continue
        rows.append((("B", v), f))
    used = set()
    for o, p in rows:
        for m in p:
            for j, e in enumerate(m):
                if e: used.add(j)
    rv = sorted(j for j in used if j >= NX)
    if order is not None:
        for c in sorted({order[NAME[j - NX]] for j in rv if j in gset}):
            rows.append((("Sc", c), None))
    for key in sorted({setkey_of(j) for j in rv if j not in gset}):
        rows.append((("S", key), None))
    gens = [NAME[j] for j in sorted(j for j in used if j < NX)] + ["r_" + NAME[j - NX] for j in rv]
    return [o for o, p in rows], gens


# ------------------------------------------------------------------ ordered partitions
def ordered_partitions(items):
    items = list(items)
    def rec(rest, lvl):
        if not rest: yield {}; return
        for mask in range(1, 1 << len(rest)):
            grp = [rest[i] for i in range(len(rest)) if mask >> i & 1]
            oth = [rest[i] for i in range(len(rest)) if not mask >> i & 1]
            for tail in rec(oth, lvl + 1):
                d = {g: lvl for g in grp}; d.update(tail); yield d
    seen = set()
    for d in rec(items, 0):
        key = tuple(sorted(d.items()))
        if key not in seen: seen.add(key); yield d


# ------------------------------------------------------------------ witnesses
def check_witness(lab, assign, rec):
    D, R = SF.DR()
    s = [F(rec["witness"][NAME[i]]) for i in range(NX)]
    # the leaf's labels and the recorded pattern
    for i in range(NX):
        if lab[i] == 0: need(s[i] == 0, "%s must be 0" % NAME[i])
        if lab[i] == 1: need(s[i] == 1, "%s must be 1" % NAME[i])
        if lab[i] == MIX: need(0 < s[i] < 1, "%s must be interior" % NAME[i])
        a = assign.get(i)
        if a in (0, 1): need(s[i] == a, "%s must be %s" % (NAME[i], a))
        if a == "mix": need(0 < s[i] < 1, "%s must be interior" % NAME[i])
        need(0 <= s[i] <= 1, "%s outside [0,1]" % NAME[i])
    # an exact Nash point
    vals = {w: s[w] for w in range(NX)}
    for i in range(NX):
        d = SF.evaluate(lift(D[i]), vals)
        if s[i] == 0: need(d <= 0, "D_%s > 0 at 0" % NAME[i])
        elif s[i] == 1: need(d >= 0, "D_%s < 0 at 1" % NAME[i])
        else: need(d == 0, "D_%s != 0 at an interior value" % NAME[i])
    # the concrete tremble curve
    curve = rec["curve"]
    pin0 = [w for w in range(NX) if s[w] == 0]; pin1 = [w for w in range(NX) if s[w] == 1]
    for w in pin0 + pin1:
        need(NAME[w] in curve, "curve does not tremble %s" % NAME[w])
        e, rho = curve[NAME[w]]
        need(int(e) >= 1 and F(rho) > 0, "curve order / ratio for %s must be >= 1 / > 0" % NAME[w])
    interior = {w: s[w] for w in range(NX) if 0 < s[w] < 1}
    for v in range(NX):
        if not D[v]: continue
        od, ld = lead_along(D[v], curve, pin0, pin1, interior)
        orr, lr = lead_along(R[v], curve, pin0, pin1, interior)
        if orr is None: continue                       # the set is never reached
        need(lr > 0, "reach of %s has a nonpositive leading term" % NAME[v])
        if od is None or od > orr: continue            # limit value difference 0: any action optimal
        need(od == orr, "D_%s vanishes more slowly than its reach" % NAME[v])
        if s[v] == 0: need(ld <= 0, "belief-weighted D_%s > 0 but %s = 0" % (NAME[v], NAME[v]))
        elif s[v] == 1: need(ld >= 0, "belief-weighted D_%s < 0 but %s = 1" % (NAME[v], NAME[v]))
        else: need(ld == 0, "belief-weighted D_%s != 0 but %s is interior" % (NAME[v], NAME[v]))


def lead_along(poly48, curve, pin0, pin1, interior):
    """leading (order, coefficient) of poly48 along the concrete curve, exactly"""
    terms = {}
    p0 = set(pin0); p1 = set(pin1)
    for m, c in poly48.items():
        ws = [w for w, e in enumerate(m) if e]
        coef = c; base = 0; ok = True
        for w in ws:
            if w in interior: coef *= interior[w]
        if coef == 0: continue
        z = [w for w in ws if w in p0]; o = [w for w in ws if w in p1]
        for w in z:
            e, rho = curve[NAME[w]]; base += int(e); coef *= F(rho)
        # expand prod over pinned-1 factors of (1 - eps^e rho)
        parts = {base: coef}
        for w in o:
            e, rho = curve[NAME[w]]; e = int(e); rho = F(rho)
            new = {}
            for k, c2 in parts.items():
                new[k] = new.get(k, F(0)) + c2
                new[k + e] = new.get(k + e, F(0)) - c2 * rho
            parts = new
        for k, c2 in parts.items():
            if c2: terms[k] = terms.get(k, F(0)) + c2
    terms = {k: c for k, c in terms.items() if c}
    if not terms: return None, F(0)
    k = min(terms); return k, terms[k]


# ------------------------------------------------------------------ one leaf
def check_file(path):
    L = np.load("enum6_pat_silentR.npy")
    D, R = SF.DR()
    stats = {"closure": 0, "onesigned": 0, "cert": 0, "orderings": 0, "witness": 0}
    with gzip.open(path, "rt") as f:
        head = json.loads(f.readline())
        recs = [json.loads(l) for l in f]
    k = head["leaf"]; lab = [int(x) for x in L[k]]
    # 1. closure
    assign0 = {}
    for name, val, why in head["closure"]:
        v = I[name]
        need(lab[v] == DC, "closure forces %s, which the leaf does not leave free" % name)
        if why == "dominance":
            m0 = next(iter(R[v])); c = D[v].get(m0, F(0)) / R[v][m0]
            need(c != 0 and SF.padd(D[v], R[v], -c) == {}, "%s: D is not a constant times R" % name)
            need(val == (1 if c > 0 else 0), "%s: dominance says %d" % (name, 1 if c > 0 else 0))
        else:
            case = Case(lab, dict(assign0))
            s = robust_sign(case.belief(v), case.openx)
            need(s != 0, "%s: leading form not robustly one-signed" % name)
            need(val == (1 if s > 0 else 0), "%s: form sign disagrees with the forced value" % name)
        assign0[v] = val; stats["closure"] += 1
    decide = [I[n] for n in head["decide"]]
    need(sorted(set(decide) | set(assign0)) == sorted(set(decide) | set(assign0)), "")
    # 2. coverage (records are prefixes in the decide order)
    index = {}
    for r in recs:
        a = {I[n]: v for n, v in r["assign"].items()}
        need(set(a) <= set(decide), "record assigns a coordinate outside the decided ones")
        pref = tuple(a.get(v) for v in decide[:len(a)])
        need(all(x is not None for x in pref), "record is not a prefix in the decide order")
        need(pref not in index, "duplicate record")
        index[pref] = r
    def covered(pref):
        if pref in index:
            return index[pref]["kind"] in ("kill", "witness")
        if len(pref) == len(decide): return False
        return all(covered(pref + (x,)) for x in (0, 1, "mix"))
    need(covered(()), "coverage fails: some pattern is neither killed nor witnessed")
    # 3/4. every record
    for pref, r in index.items():
        a = dict(assign0); a.update({decide[t]: pref[t] for t in range(len(pref))})
        case = Case(lab, a)
        if r["kind"] == "witness":
            check_witness(lab, a, r); stats["witness"] += 1; continue
        need(r["kind"] == "kill", "record of kind %r" % r["kind"])
        ev = r["ev"]
        if ev == "onesigned":
            v = I[r["v"]]; s = robust_sign(case.belief(v), case.openx)
            need(s != 0, "%s: not robustly one-signed" % r["v"])
            need(a[v] != (1 if s > 0 else 0), "%s: value agrees with its form -- no contradiction" % r["v"])
            stats["onesigned"] += 1
        elif ev == "cert":
            check_cert(case, r["cert"]); stats["cert"] += 1
        elif ev == "orderings":
            group = r["group"]; certs = r["certs"]
            n = 0
            for order in ordered_partitions(group):
                key = json.dumps(sorted(order.items()))
                need(key in certs, "no certificate for ordering %s" % key)
                check_cert(case, certs[key], order, group); n += 1
            stats["orderings"] += 1
        else:
            raise Bad("unknown evidence %r" % ev)
    return k, stats


if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(glob.glob("seqcert_*.jsonl.gz"))
    bad = 0
    for p in paths:
        try:
            k, st = check_file(p)
            print("%-24s leaf %4d  OK   %s" % (p, k, st), flush=True)
        except (Bad, C.Bad) as e:
            bad += 1; print("%-24s FAILED: %s" % (p, e), flush=True)
    print("%d files, %d failed  %s" % (len(paths), bad, "OK" if bad == 0 else "*** NOT VERIFIED"))
