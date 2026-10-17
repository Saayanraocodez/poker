"""The exact prior contribution c* at which the P1-silent branch of the 24-hand JJ-AA river game stops
being a Nash equilibrium (preregistration amendment 7).  Scope: THIS branch, i.e. the 7-row on-path
support of the pot-sweep certificates at 61/64 <= c <= 253/256, with class-symmetric profiles.  It is
not a proof that no P1-silent equilibrium exists above c*.

derive    1. An independent class-level model of the game, written from the rules (not from hinc/):
             four hand classes J < Q < K < A per seat; class-triple weights 216 (three ranks), 36 (two
             seats share a rank: one combo each way) and 0 (three seats share a rank) out of 6480; the
             13 terminal histories of the all-in-only tree; payoffs affine in c.  The game is invariant
             under the 24 suit permutations, so a class-symmetric profile of the 24-hand game is a
             profile of this 4-type game, and one combo's deviation gains 1/6 of its class's.  Checked
             against the engine exactly (utilities at all 64 certificates and at random profiles).
          2. With c a symbol, the indifference conditions of the 7 mixed rows (identical to the engine's
             equations at every certificate with this support), solved in closed form in
             Q(c, sqrt(DELTA0(c))); the closed form reproduces every stored 7-row certificate.  Over an
             interval of c it is checked exactly (real-root isolation) that the mixed rows stay in [0,1]
             and that no pure plan of any class of any player does better on path.
          3. P1's four class gains from opening: exact bilinear functions of the 12 class responses to
             P1's all-in.  The JJ-bluff and AA-value thresholds in theta (P3's KK call after B:1-F)
             meet at c*, an algebraic number.  A Lagrangian bound shows that the max-min deterrence
             margin over ALL 12 responses is negative for c > c*; the theta window shows it is
             positive for c < c*.
certify   c_lo = floor(c* 2^20)/2^20 and c_hi = c_lo + 2^-20 (configs/threshold/, hashed in amendment 8):
          (a) at c_lo an exact P1-silent class-symmetric Nash equilibrium, by the engine's exact full
          best-response check in Q(sqrt d); (b) at c_hi an exact proof, from the engine's own payoff
          tables and values, that lambda_JJ gain_JJ + lambda_AA gain_AA > 0 at all 4096 vertices of the
          response box (a multilinear function attains its minimum over a box at a vertex), so no
          class-symmetric responses deter P1, while the on-path part is still an exact equilibrium of
          the game with P1's opening fixed to check.

usage:  python scripts/silent_threshold.py derive|configs|certify|all
        -> results/threshold/derivation.json, certificates.json, c_lo/policy_exact.json
"""
import glob
import itertools
import json
import math
import os
import random
import sys
import time
from fractions import Fraction as F

import numpy as np
import sympy as sp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from hinc.surd import Surd, parse                  # noqa: E402

RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(RESULTS, "threshold")
CLS = ["JJ", "QQ", "KK", "AA"]                     # strength = index
CS = sp.Symbol("c", positive=True)

# ------------------------------------------------------------------------------------------------
# 1. the class-level model (independent of hinc/)
# ------------------------------------------------------------------------------------------------
# public history -> (actor, child after the passive action, child after the aggressive action)
NODES = {"": (0, "K", "B:1"), "K": (1, "K-K", "K-B:1"), "K-K": (2, "K-K-K", "K-K-B:1"),
         "K-K-B:1": (0, "K-K-B:1-F", "K-K-B:1-C"), "K-K-B:1-F": (1, "K-K-B:1-F-F", "K-K-B:1-F-C"),
         "K-K-B:1-C": (1, "K-K-B:1-C-F", "K-K-B:1-C-C"), "K-B:1": (2, "K-B:1-F", "K-B:1-C"),
         "K-B:1-F": (0, "K-B:1-F-F", "K-B:1-F-C"), "K-B:1-C": (0, "K-B:1-C-F", "K-B:1-C-C"),
         "B:1": (1, "B:1-F", "B:1-C"), "B:1-F": (2, "B:1-F-F", "B:1-F-C"), "B:1-C": (2, "B:1-C-F", "B:1-C-C")}


def terminal(h):
    """(seats that put the 1 bb all-in in, seats still live) at a terminal history, by replaying it."""
    i, put, live = 0, set(), {0, 1, 2}
    for t in h.split("-"):
        while i % 3 not in live:
            i += 1
        if t in ("B:1", "C"):
            put.add(i % 3)
        elif t == "F":
            live.discard(i % 3)
        i += 1
    return put, live


TERMINALS = sorted({ch for (_, a, b) in NODES.values() for ch in (a, b) if ch not in NODES})
assert len(TERMINALS) == 13


def payoff(h, deal, c):
    """Net chips relative to the start of the hand: -(c + river contribution) + pot share."""
    put, live = terminal(h)
    pot = 3 * c + len(put)
    best = max(deal[i] for i in live)
    win = [i for i in live if deal[i] == best]
    return [-(c + (1 if i in put else 0)) + (pot / len(win) if i in win else 0) for i in range(3)]


def weight(deal):
    """Ordered combo triples behind a class triple (4 suits: a rank has 6 combos; two seats holding
    one rank must use disjoint suits, 1 way; three seats cannot)."""
    k = len(set(deal))
    return 216 if k == 3 else 36 if k == 2 else 0


DEALS = [d for d in itertools.product(range(4), repeat=3) if weight(d)]
assert sum(weight(d) for d in DEALS) == 6480


def node_value(h, deal, prof, c):
    if h not in NODES:
        return payoff(h, deal, c)
    p, a, b = NODES[h]
    x = prof[(p, h, CLS[deal[p]])]
    va, vb = node_value(a, deal, prof, c), node_value(b, deal, prof, c)
    return [(1 - x) * va[i] + x * vb[i] for i in range(3)]


def _w(d, c):
    return sp.Rational(weight(d), 6480) if isinstance(c, sp.Basic) else F(weight(d), 6480)


def utilities(prof, c):
    """Exact expected utilities of a class-level profile {(player, history, class): P(aggressive)}."""
    u = [0, 0, 0]
    for d in DEALS:
        v = node_value("", d, prof, c)
        for i in range(3):
            u[i] = u[i] + _w(d, c) * v[i]
    return [sp.expand(x) for x in u] if isinstance(c, sp.Basic) else u


def class_value(prof, c, player, k):
    """Player's utility from the deals in which they hold class k (prior x value, summed)."""
    v = 0
    for d in DEALS:
        if CLS[d[player]] == k:
            v = v + _w(d, c) * node_value("", d, prof, c)[player]
    return sp.expand(v) if isinstance(c, sp.Basic) else v


ROWS = [(p, h, k) for h, (p, _, _) in NODES.items() for k in CLS]
OPEN = [(0, "", k) for k in CLS]
RESP = [(1, "B:1", k) for k in CLS] + [(2, "B:1-F", k) for k in CLS] + [(2, "B:1-C", k) for k in CLS]


def row_name(key):
    return "P%d %s %s" % (key[0] + 1, key[1] or "(open)", key[2])


def name_row(s):
    p, rest = s.split(" ", 1)
    h, k = rest.rsplit(" ", 1)
    return (int(p[1]) - 1, "" if h == "(open)" else h, k)


# ------------------------------------------------------------------------------------------------
# the stored certificates, the support, and the engine
# ------------------------------------------------------------------------------------------------
UNKNOWN = ["P2 K JJ", "P3 K-K JJ", "P3 K-K QQ", "P1 K-K-B:1 QQ", "P2 K-K-B:1-F KK", "P1 K-B:1-F QQ", "P1 K-B:1-F KK"]
SUPPORT_FROM = "potsweep/potsweep_c253-256_JJAA24/dcfr_s1/policy_exact_silent.json"
OWN_UNREACHED = [(1, "K-K-B:1-F", "AA"), (1, "K-K-B:1-C", "AA")]  # P2 bets AA at K always; set to call
X6 = F(183, 233)       # the free direction (only x5 + x6 is pinned): the value in the 253/256 certificates
BASE = (F(61, 64), F(253, 256))          # the certified 7-row interval
WIDE = (F(7, 8), F(2))                   # where the support's validity interval is searched
DYADIC = 2 ** 20


def load_cert(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    rows = {}
    for r in doc["infosets"]:
        key = (r["player"] - 1, r["history"], r["hand"][0] * 2)
        v = parse(r["probs"][1])
        assert rows.get(key, v) == v, "not class-symmetric"
        rows[key] = v
    return rows, F(doc["game"]["betting"]["prior_contrib"][0]), doc


def cert_files():
    return sorted(glob.glob(os.path.join(RESULTS, "potsweep*", "*", "dcfr_s*", "policy_exact*.json")))


def rel(path):
    return os.path.relpath(path, RESULTS).replace("\\", "/")


def support():
    """The fixed on-path class rows (all but the 7 unknowns and the 12 responses); P1 never opens."""
    rows = load_cert(os.path.join(RESULTS, SUPPORT_FROM))[0]
    fixed = {}
    for k in ROWS:
        if k[1].startswith("B:1") or row_name(k) in UNKNOWN:
            continue
        fixed[k] = F(1) if k in OWN_UNREACHED else rows[k]
    assert all(fixed[k] == 0 for k in OPEN)
    return fixed


def config_for(cv):
    with open(os.path.join(ROOT, "configs", "potsweep", "potsweep_c253-256_JJAA24.json")) as f:
        cfg = json.load(f)
    cfg["name"] = "threshold_c%d-%d_JJAA24" % (cv.numerator, cv.denominator)
    cfg["description"] = ("Exact threshold of the P1-silent branch (amendments 7-8): dry board, JJ QQ KK AA "
                          "(24 hands), prior contribution %s each (pot %s = %.9f), stack 1 = min bet "
                          "(all-in only by the rules)." % (cv, 3 * cv, float(3 * cv)))
    cfg["betting"]["prior_contrib"] = [str(cv)] * 3
    return cfg


def engine_game(cv):
    from hinc.game import RiverGame
    return RiverGame(config_for(cv))


def engine_profile(g, prof):
    p = np.full((g.n_isets, g.max_actions), F(0), dtype=object)
    for I in g.isets:
        x = prof[(I.player, I.history, I.hand_label[0] * 2)]
        p[I.index, 1] = x
        p[I.index, 0] = 1 - x
    return p


def check_model():
    """The model against the engine, exactly: utilities at every stored certificate, and at random
    rational class-symmetric profiles at three contributions."""
    from hinc.evaluate import utilities as engine_utilities
    out = {"certificates": [], "random_profiles": []}
    for f in cert_files():
        rows, cv, _ = load_cert(f)
        with open(f.replace("policy_exact", "polish")) as fh:
            pol = json.load(fh)
        ok = utilities(rows, cv) == [parse(x) for x in pol["exact_utilities"]]
        out["certificates"].append({"certificate": rel(f), "c": str(cv), "utilities_equal": ok})
    rng = random.Random(20261017)
    for cv in (F(253, 256), F(1, 3), F(7, 5)):
        g = engine_game(cv)
        for _ in range(2):
            prof = {k: F(rng.randint(0, 24), 24) for k in ROWS}
            ok = list(engine_utilities(g, engine_profile(g, prof))) == utilities(prof, cv)
            out["random_profiles"].append({"c": str(cv), "utilities_equal": ok})
    out["all_equal"] = all(r["utilities_equal"] for r in out["certificates"] + out["random_profiles"])
    print("model vs engine: %d certificates, %d random profiles, all exactly equal: %s" % (
        len(out["certificates"]), len(out["random_profiles"]), out["all_equal"]), flush=True)
    assert out["all_equal"]
    return out


# ------------------------------------------------------------------------------------------------
# exact arithmetic in Q(c)(R), R = sqrt(DELTA0(c)) > 0, and exact signs over intervals of c
# ------------------------------------------------------------------------------------------------
KF = sp.QQ.frac_field(CS)


def kf(x):
    if KF.of_type(x):
        return x
    if isinstance(x, F):
        x = sp.Rational(x.numerator, x.denominator)
    return KF.from_sympy(sp.sympify(x))


def rat(x):
    x = sp.Rational(x)
    return F(int(x.p), int(x.q))


class Alg:
    """A + B*R with A, B in Q(c) and R = sqrt(Alg.D) > 0, Alg.D a square-free polynomial in c."""
    D = None
    __slots__ = ("A", "B")

    def __init__(self, A, B=0):
        self.A, self.B = kf(A), kf(B)

    @staticmethod
    def _co(o):
        return o if isinstance(o, Alg) else Alg(o)

    def __add__(self, o):
        o = self._co(o)
        return Alg(self.A + o.A, self.B + o.B)

    __radd__ = __add__

    def __neg__(self):
        return Alg(-self.A, -self.B)

    def __sub__(self, o):
        return self + (-self._co(o))

    def __rsub__(self, o):
        return self._co(o) - self

    def __mul__(self, o):
        o = self._co(o)
        return Alg(self.A * o.A + self.B * o.B * Alg.D, self.A * o.B + self.B * o.A)

    __rmul__ = __mul__

    def norm(self):
        return self.A * self.A - self.B * self.B * Alg.D

    def __truediv__(self, o):
        o = self._co(o)
        n = o.norm()
        return self * Alg(o.A / n, -o.B / n)

    def __rtruediv__(self, o):
        return self._co(o) / self

    def is_zero(self):
        return self.A == 0 and self.B == 0

    def at(self, cv):
        """(a, b, n): the value a + b sqrt(n) at the rational cv, n = DELTA0(cv)."""
        s = sp.Rational(cv.numerator, cv.denominator)
        return (rat(KF.to_sympy(self.A).subs(CS, s)), rat(KF.to_sympy(self.B).subs(CS, s)),
                rat(KF.to_sympy(Alg.D).subs(CS, s)))

    def exact_at(self, cv):
        """The value at the rational cv: a Fraction, or a Surd in Q(sqrt d), d = field_d(cv)."""
        a, b, n = self.at(cv)
        if b == 0:
            return a
        d, m = field_d(cv)
        return Surd(a, b * m, d)

    def sign_at(self, cv):
        a, b, n = self.at(cv)
        return surd_sign(a, b, n)

    def float_at(self, cv):
        a, b, n = self.at(cv)
        return float(a) + float(b) * math.sqrt(float(n))

    def to_json(self):
        return {"A": str(KF.to_sympy(self.A)), "B": str(KF.to_sympy(self.B))}


def surd_sign(a, b, n):
    """Exact sign of a + b sqrt(n), n > 0 rational."""
    sa, sb = (a > 0) - (a < 0), (b > 0) - (b < 0)
    if sb == 0 or sa == sb:
        return sa or sb
    if sa == 0:
        return sb
    t = a * a - b * b * n
    return sa if t > 0 else sb if t < 0 else 0


def field_d(cv):
    """sqrt(DELTA0(cv)) = sqrt(d) / m with d a non-square integer (square factors < 10^5 removed)."""
    n = rat(KF.to_sympy(Alg.D).subs(CS, sp.Rational(cv.numerator, cv.denominator)))
    d, m = n.numerator * n.denominator, F(1, n.denominator)
    p = 2
    while p < 10 ** 5:
        while d % (p * p) == 0:
            d //= p * p
            m *= p
        p += 1 if p == 2 else 2
    assert math.isqrt(d) ** 2 != d, "DELTA0(c) is a rational square"
    return d, m


def poly_c(p):
    """A sympy PolyElement / expression in c -> Poly over QQ."""
    return sp.Poly(p.as_expr() if hasattr(p, "as_expr") else p, CS, domain="QQ")


def irreducible_factors(polys):
    """The distinct irreducible factors (primitive, integer, positive leading coefficient) of polys."""
    out = {}
    for p in polys:
        p = poly_c(p)
        if p.degree() <= 0:
            continue
        for fac, _ in p.factor_list()[1]:
            fac = sp.Poly(fac.as_expr(), CS, domain="ZZ").primitive()[1]
            if fac.LC() < 0:
                fac = -fac
            out[str(fac.as_expr())] = fac
    return list(out.values())


def isolate(factors, lo, hi, eps=F(1, 10 ** 12)):
    """Disjoint rational isolating intervals [a, b] (width < eps) of every real root in [lo, hi] of
    the given irreducible factors, sorted: [(a, b, factor)]."""
    out = []
    for fac in factors:
        for (a, b), _ in fac.intervals(inf=sp.Rational(lo.numerator, lo.denominator),
                                      sup=sp.Rational(hi.numerator, hi.denominator),
                                      eps=sp.Rational(eps.numerator, eps.denominator)):
            out.append((rat(a), rat(b), fac))
    out.sort(key=lambda t: t[0])
    for x, y in zip(out, out[1:]):
        assert x[1] < y[0], "isolating intervals overlap"
    return out


def sign_pattern(E, lo, hi):
    """Exact sign of E = A + B R on [lo, hi]: E changes sign only at real roots of the norm's numerator
    or of the denominators.  Returns (critical intervals, which of them are poles, signs on the gaps
    between them, each decided exactly at a rational sample point)."""
    if E.is_zero():
        return [], [], [0]
    poles = {str(f.as_expr()) for f in irreducible_factors([E.A.denom, E.B.denom])}
    crit = isolate(irreducible_factors([E.norm().numer, E.A.denom, E.B.denom]), lo, hi)
    cuts = [lo] + [x for a, b, _ in crit for x in (a, b)] + [hi]
    samples = [(cuts[2 * i] + cuts[2 * i + 1]) / 2 for i in range(len(crit) + 1)]
    return crit, [str(f.as_expr()) in poles for _, _, f in crit], [E.sign_at(s) for s in samples]


def validity(E, want, base, wide):
    """The maximal interval containing base on which sign(E) is in want, searched inside wide (a pole
    always ends it).  Returns the lower and upper ends, each None (it reaches the end of wide) or the
    critical interval (a, b, factor) at which the condition first fails; or 'identically zero'."""
    crit, pole, signs = sign_pattern(E, *wide)
    if not crit and signs == [0]:
        return {"identically_zero": True, "lower": None, "upper": None}
    ok = [s in want for s in signs]
    gaps = [(wide[0] if i == 0 else crit[i - 1][1], wide[1] if i == len(crit) else crit[i][0])
            for i in range(len(crit) + 1)]
    inside = [i for i, (a, b) in enumerate(gaps) if b > base[0] and a < base[1]]
    assert all(ok[i] for i in inside) and not any(pole[i] for i in inside[:-1]), \
        "condition fails inside the base interval"
    i0, i1 = min(inside), max(inside)
    while i0 > 0 and ok[i0 - 1] and not pole[i0 - 1]:
        i0 -= 1
    while i1 < len(gaps) - 1 and ok[i1 + 1] and not pole[i1]:
        i1 += 1
    return {"identically_zero": False, "lower": crit[i0 - 1] if i0 > 0 else None,
            "upper": crit[i1] if i1 < len(crit) else None,
            "critical_points_inside_base": sum(1 for a, b, _ in crit if b > base[0] and a < base[1])}


def describe(iv):
    """An algebraic number given by an isolating interval of an irreducible factor."""
    if iv is None:
        return None
    a, b, fac = iv
    r = [x for x in sp.Poly(fac.as_expr(), CS).real_roots() if a <= x <= b]
    assert len(r) == 1
    return {"minimal_polynomial": str(fac.as_expr()), "isolating_interval": [str(a), str(b)],
            "decimal": str(sp.N(r[0], 30)), "pot_decimal": str(sp.N(3 * r[0], 30))}


# ------------------------------------------------------------------------------------------------
# 2. the closed form of the on-path part
# ------------------------------------------------------------------------------------------------
XS = sp.symbols("x0:7")
THETA = sp.Symbol("theta")
YS = {k: sp.Symbol("y_%s_%s" % (k[1].replace(":", "").replace("-", ""), k[2])) for k in RESP}


def sym_profile(resp=None, opening=None):
    prof = {k: sp.Rational(v.numerator, v.denominator) for k, v in support().items()}
    for j, n in enumerate(UNKNOWN):
        prof[name_row(n)] = XS[j]
    for k in RESP:
        prof[k] = (resp or {}).get(k, sp.Integer(0))
    for k in OPEN:
        prof[k] = (opening or {}).get(k, sp.Integer(0))
    return prof


def poly_at(expr, vals):
    """A polynomial in XS with coefficients in Q(c), evaluated at Alg values."""
    if not expr.has(*XS):
        return Alg(expr)
    tot = Alg(0)
    for mon, cf in sp.Poly(expr, *XS).terms():
        t = Alg(cf)
        for j, e in enumerate(mon):
            for _ in range(e):
                t = t * vals[j]
        tot = tot + t
    return tot


def horner(P, X):
    acc = Alg(0)
    for cf in P.all_coeffs():
        acc = acc * X + Alg(cf)
    return acc


def same(alg, cv, v):
    """Exact equality of alg at the rational cv with a stored certificate value (Fraction or Surd)."""
    a, b, n = alg.at(cv)
    if not isinstance(v, Surd) or v.b == 0:
        v = v.a if isinstance(v, Surd) else v
        return b == 0 and a == v
    return a == v.a and (b > 0) == (v.b > 0) and b * b * n == v.b * v.b * v.d


def closed_form():
    c = CS
    x0, x1, x2, x3, x4, x5, x6 = XS
    U = utilities(sym_profile(), c)
    eqs = [sp.expand(sp.diff(U[name_row(n)[0]], XS[j])) for j, n in enumerate(UNKNOWN)]
    matched = []
    for f in sorted(glob.glob(os.path.join(RESULTS, "potsweep*", "*", "dcfr_s*", "polish*.json"))):
        with open(f) as fh:
            pol = json.load(fh)
        if pol.get("unknowns") != UNKNOWN or "equations" not in pol:
            continue
        cv = sp.Rational(pol["contribution"])
        loc = {"x%d" % j: XS[j] for j in range(7)}
        ok = all(sp.expand(sp.sympify(s, locals=loc) - e.subs(c, cv)) == 0 for s, e in zip(pol["equations"], eqs))
        matched.append({"polish": rel(f), "c": pol["contribution"], "equations_equal": ok})
    assert matched and all(m["equations_equal"] for m in matched)
    print("equations: identical to the engine's at %d polish records" % len(matched), flush=True)

    X0 = sp.solve(eqs[5], x0)[0]
    assert sp.simplify(X0 - sp.Rational(13) / (24 * c + 8)) == 0 and sp.expand(eqs[6] - eqs[5]) == 0
    S56 = sp.factor(sp.solve(eqs[0], x5)[0] + x6)
    assert not S56.has(x6)
    e = [sp.together(q.subs(x0, X0)) for q in eqs]
    assert sp.Poly(sp.numer(e[1]), x4).degree() == 1
    X4 = sp.solve(e[1], x4)[0]
    qx = sp.Poly(sp.numer(sp.together(e[2].subs(x4, X4))), x3)
    assert qx.degree() == 2
    co = [sp.factor(t) for t in qx.all_coeffs()]
    g = sp.gcd_list(co)
    al, mb, ga = [sp.factor(sp.cancel(t / g)) for t in co]        # al x3^2 + mb x3 + ga = 0
    disc = sp.factor(mb ** 2 - 4 * al * ga)
    cont, facs = sp.factor_list(disc)
    sq, D0 = sp.Integer(1), sp.Integer(1)
    for fac, m in facs:
        sq *= fac ** (m // 2)
        D0 *= fac ** (m % 2)
    cr = sp.sqrt(cont)
    if not cr.is_Rational:
        D0, cr = D0 * cont, sp.Integer(1)
    sq *= cr
    Alg.D = kf(sp.expand(D0))
    s12 = sp.solve([e[3], e[4]], [x1, x2], dict=True)
    assert len(s12) == 1

    def from_x3(expr, X3):
        n, d = sp.fraction(sp.together(expr))
        return horner(sp.Poly(n, x3), X3) / horner(sp.Poly(d, x3), X3)

    cert_rows, cert_c, _ = load_cert(os.path.join(RESULTS, SUPPORT_FROM))
    branch = None
    for sgn in (-1, 1):
        X3 = Alg(-mb / (2 * al), sgn * sq / (2 * al))
        if same(X3, cert_c, cert_rows[name_row(UNKNOWN[3])]):
            branch = sgn
            break
    assert branch is not None
    X3 = Alg(-mb / (2 * al), branch * sq / (2 * al))
    VAL = [Alg(X0), from_x3(s12[0][x1], X3), from_x3(s12[0][x2], X3), X3, from_x3(X4, X3),
           Alg(S56 - sp.Rational(X6.numerator, X6.denominator)), Alg(sp.Rational(X6.numerator, X6.denominator))]
    for q in eqs:
        assert poly_at(q, VAL).is_zero(), "the closed form does not solve the system identically"
    other = validity(Alg(X3.A, -X3.B) - 1, (1,), WIDE, WIDE)      # the other root of the quadratic is > 1
    assert other["lower"] is None and other["upper"] is None
    print("closed form: x0 = %s, x5 + x6 = %s, x3 root of %s = 0, DELTA0 = %s" % (
        sp.factor(X0), S56, sp.expand(al * x3 ** 2 + mb * x3 + ga), sp.factor(D0)), flush=True)

    repro = []
    for f in cert_files():
        with open(f.replace("policy_exact", "polish")) as fh:
            pol = json.load(fh)
        if pol.get("unknowns") != UNKNOWN:
            continue
        rows, cv, _ = load_cert(f)
        ok = [same(VAL[j], cv, rows[name_row(UNKNOWN[j])]) for j in range(5)]
        ok.append(same(VAL[5] + VAL[6], cv, rows[name_row(UNKNOWN[5])] + rows[name_row(UNKNOWN[6])]))
        repro.append({"certificate": rel(f), "c": str(cv), "x0..x4 and x5+x6 equal": all(ok)})
    assert repro and all(r["x0..x4 and x5+x6 equal"] for r in repro)
    print("closed form reproduces %d stored 7-row certificates exactly" % len(repro), flush=True)
    doc = {"equations_vs_engine": matched, "reproduces_certificates": repro,
           "unknowns": UNKNOWN, "equations": [str(sp.factor(q)) for q in eqs],
           "x0_JJ_bluff": str(sp.factor(X0)), "x5_plus_x6": str(S56),
           "free_direction": "x6 = P1 K-B:1-F KK fixed at %s (x5 + x6 is pinned; P1 is indifferent and no other "
                             "player's payoff depends on the split)" % X6,
           "x3_quadratic": str(sp.expand(al * x3 ** 2 + mb * x3 + ga)),
           "x3_branch": "x3 = (%s %s sqrt(DELTA0))/(%s)" % (sp.expand(-mb), "+" if branch > 0 else "-",
                                                             sp.expand(2 * al / sq)),
           "x3_other_root_exceeds_1_on": [str(WIDE[0]), str(WIDE[1])],
           "x4_of_x3": str(sp.factor(X4)), "x1_of_x3": str(sp.factor(s12[0][x1])),
           "x2_of_x3": str(sp.factor(s12[0][x2])), "DELTA0": str(sp.expand(D0)),
           "DELTA0_irreducible": len(sp.factor_list(D0)[1]) == 1}
    return VAL, doc


# ------------------------------------------------------------------------------------------------
# support over an interval: every pure plan of every class, and the mixed rows in [0, 1]
# ------------------------------------------------------------------------------------------------
def plans(player):
    if player == 0:
        return [{"K-K-B:1": a, "K-B:1-F": b, "K-B:1-C": d} for a, b, d in itertools.product((0, 1), repeat=3)]
    if player == 1:
        return [{"K": 1}] + [{"K": 0, "K-K-B:1-F": a, "K-K-B:1-C": b} for a, b in itertools.product((0, 1), repeat=2)]
    return [{"K-K": a, "K-B:1": b} for a, b in itertools.product((0, 1), repeat=2)]


def check_support(VAL):
    """Every on-path condition of the class-symmetric profile as an exact function of c: for every
    player, class and pure plan (P1: after checking; P2, P3: P1 never bets, so the responses to P1's
    bet do not enter their payoffs), plan value - equilibrium value <= 0; and 0 <= x_j <= 1."""
    c = CS
    base = sym_profile()
    conds = []
    for j, n in enumerate(UNKNOWN[:5]):
        conds.append(("%s >= 0" % n, VAL[j], (1,)))
        conds.append(("%s <= 1" % n, 1 - VAL[j], (1,)))
    s56 = VAL[5] + VAL[6]                                  # only the sum is pinned: a split in [0,1]^2 exists
    conds.append(("x5 + x6 >= 0 (P1 K-B:1-F QQ + KK)", s56, (1,)))
    conds.append(("x5 + x6 <= 2", 2 - s56, (1,)))
    info = [("fixed split x6 = %s: P1 K-B:1-F QQ = x5 >= 0" % X6, VAL[5]),
            ("fixed split x6 = %s: P1 K-B:1-F QQ = x5 <= 1" % X6, 1 - VAL[5])]
    for i in range(3):
        for k in CLS:
            eqv = poly_at(class_value(base, c, i, k), VAL)
            for pl in plans(i):
                prof = dict(base)
                for h, a in pl.items():
                    prof[(i, h, k)] = sp.Integer(a)
                diff = poly_at(class_value(prof, c, i, k), VAL) - eqv
                acts = ", ".join("%s %s" % (h, ("K", "B")[a] if h in ("K", "K-K") else ("F", "C")[a])
                                 for h, a in pl.items())
                conds.append(("P%d %s plan (%s): value - equilibrium <= 0" % (i + 1, k, acts), -diff, (1,)))
    out, lo, hi = [], None, None
    for name, E, _ in conds:
        v = validity(E, (0, 1), BASE, WIDE)
        out.append({"condition": name, "identically_zero": v["identically_zero"],
                    "fails_below": describe(v["lower"]), "fails_above": describe(v["upper"]),
                    "_lower": v["lower"], "_upper": v["upper"]})
        if v["lower"] and (lo is None or v["lower"][0] > lo[0][0]):
            lo = (v["lower"], name)
        if v["upper"] and (hi is None or v["upper"][1] < hi[0][1]):
            hi = (v["upper"], name)
    tight = sum(1 for o in out if o["identically_zero"])
    print("support: %d conditions (%d identically tight); valid on (%s, %s) by %s / %s" % (
        len(out), tight, describe(lo[0])["decimal"][:12] if lo else WIDE[0],
        describe(hi[0])["decimal"][:12] if hi else WIDE[1], lo[1] if lo else "-", hi[1] if hi else "-"), flush=True)
    for o in out:
        o.pop("_lower")
        o.pop("_upper")
    split = []
    for name, E in info:
        v = validity(E, (0, 1), BASE, WIDE)
        split.append({"condition": name, "fails_below": describe(v["lower"]), "fails_above": describe(v["upper"])})
    return out, lo, hi, split


# ------------------------------------------------------------------------------------------------
# 3. deterrence: P1's opening gains as bilinear functions of the 12 responses, and c*
# ------------------------------------------------------------------------------------------------
SHAPE = {(1, "B:1", "JJ"): 0, (1, "B:1", "QQ"): 0, (1, "B:1", "KK"): 0, (1, "B:1", "AA"): 1,
         (2, "B:1-F", "JJ"): 0, (2, "B:1-F", "QQ"): 0, (2, "B:1-F", "KK"): THETA, (2, "B:1-F", "AA"): 1,
         (2, "B:1-C", "JJ"): 0, (2, "B:1-C", "QQ"): 0, (2, "B:1-C", "KK"): 0, (2, "B:1-C", "AA"): 0}


def opening_values():
    """V_bet[k](y): P1's class-k value when class k opens, a polynomial in the 12 responses y and c
    (no on-path variable enters: after B:1 only the responses act)."""
    out = {}
    for k in CLS:
        v = class_value(sym_profile(resp=YS, opening={(0, "", k): sp.Integer(1)}), CS, 0, k)
        assert v.free_symbols <= set(YS.values()) | {CS}
        out[k] = v
    return out


def deterrence(VAL):
    c = CS
    base = sym_profile()
    vcheck = {k: poly_at(class_value(base, c, 0, k), VAL) for k in CLS}
    vbet = opening_values()
    shape = {k: sp.expand(vbet[k].subs({YS[r]: v for r, v in SHAPE.items()})) for k in CLS}
    g1 = {k: sp.factor(sp.diff(shape[k], THETA)) for k in CLS}
    g0 = {k: sp.factor(shape[k].subs(THETA, 0)) for k in CLS}
    # thresholds: gain_k(theta) = g0[k] + g1[k] theta - vcheck[k]
    thJ = (vcheck["JJ"] - g0["JJ"]) / Alg(g1["JJ"])
    thA = (vcheck["AA"] - g0["AA"]) / Alg(g1["AA"])
    M = thA - thJ
    lo, hi = F(253, 256), F(127, 128)
    assert M.sign_at(lo) > 0 and M.sign_at(hi) < 0
    crit = isolate(irreducible_factors([M.norm().numer]), lo, hi, eps=F(1, 2 ** 80))
    cands = [iv for iv in crit if M.sign_at(iv[0]) > 0 > M.sign_at(iv[1])]
    assert len(cands) == 1 and M.sign_at(lo) == M.sign_at(cands[0][0]) and M.sign_at(cands[0][1]) == M.sign_at(hi)
    a, b, fac = cands[0]
    assert math.floor(a * DYADIC) == math.floor(b * DYADIC)
    c_lo = F(math.floor(a * DYADIC), DYADIC)
    c_hi = c_lo + F(1, DYADIC)
    cstar = describe(cands[0])
    cstar["degree"] = int(sp.Poly(fac.as_expr(), CS).degree())
    cstar["norm_factorisation"] = [str(f.as_expr()) for f in irreducible_factors([M.norm().numer])]
    print("c* = %s (pot %s), minimal polynomial of degree %d: %s" % (
        cstar["decimal"][:20], cstar["pot_decimal"][:20], cstar["degree"], cstar["minimal_polynomial"]), flush=True)

    # theta window for c below c*: theta_J <= theta_A, both in [0,1], QQ and KK gains < 0 at both ends
    wcond = [("theta_J >= 0", thJ), ("theta_A <= 1", 1 - thA)]
    for k in ("QQ", "KK"):
        for nm, th in (("theta_J", thJ), ("theta_A", thA)):
            wcond.append(("gain_%s(%s) < 0" % (k, nm), -(Alg(g0[k]) + Alg(g1[k]) * th - vcheck[k])))
    window = []
    for nm, E in wcond:
        v = validity(E, (1,), (BASE[0], c_hi), WIDE)
        window.append({"condition": nm, "fails_below": describe(v["lower"]), "fails_above": describe(v["upper"])})
    mpat = validity(M, (1,), (BASE[0], c_lo), WIDE)          # theta_J < theta_A from 61/64 up to c* exactly
    assert mpat["upper"] is not None and mpat["upper"][2] == fac and mpat["upper"][0] < b and a < mpat["upper"][1]
    window.append({"condition": "theta_J < theta_A", "fails_below": describe(mpat["lower"]),
                   "fails_above": describe(mpat["upper"])})
    mneg = validity(M, (-1,), (c_hi, c_hi), WIDE)            # and theta_A < theta_J from c* on: no re-opening
    assert mneg["lower"] is not None and mneg["lower"][2] == fac
    window.append({"condition": "theta_A < theta_J (empty window)", "fails_below": describe(mneg["lower"]),
                   "fails_above": describe(mneg["upper"])})
    assert sp.Poly(fac.as_expr(), CS).count_roots(sp.Rational(c_lo.numerator, c_lo.denominator),
                                                  sp.Rational(c_hi.numerator, c_hi.denominator)) == 1

    # Lagrangian: lambda_J = g1[AA] > 0, lambda_A = -g1[JJ] > 0 cancel theta; L(y) - L(shape) at every vertex
    lamJ, lamA = g1["AA"], -g1["JJ"]
    lam_ok = [validity(Alg(x), (1,), (BASE[0], c_hi), WIDE) for x in (lamJ, lamA)]
    PJ = sp.Poly(vbet["JJ"], *[YS[r] for r in RESP])
    PA = sp.Poly(vbet["AA"], *[YS[r] for r in RESP])
    Lshape = sp.expand(lamJ * shape["JJ"] + lamA * shape["AA"])
    assert not Lshape.has(THETA)

    def at_vertex(P, bits):
        return sum((cf for mon, cf in P.terms() if all(bits[i] or not e for i, e in enumerate(mon))), sp.Integer(0))

    diffs = {}
    for bits in itertools.product((0, 1), repeat=12):
        dv = sp.factor(sp.cancel(lamJ * at_vertex(PJ, bits) + lamA * at_vertex(PA, bits) - Lshape))
        diffs.setdefault(str(dv), (dv, bits))
    lag_lo, lag_hi, lag_tight = None, None, 0
    for s, (dv, bits) in diffs.items():
        v = validity(Alg(dv), (0, 1), (c_lo, c_hi), WIDE)
        lag_tight += v["identically_zero"]
        if v["lower"] and (lag_lo is None or v["lower"][0] > lag_lo[0]):
            lag_lo = v["lower"]
        if v["upper"] and (lag_hi is None or v["upper"][1] < lag_hi[1]):
            lag_hi = v["upper"]
    print("Lagrangian: %d distinct vertex differences, all >= 0 on (%s, %s)" % (
        len(diffs), describe(lag_lo)["decimal"][:12] if lag_lo else WIDE[0],
        describe(lag_hi)["decimal"][:12] if lag_hi else WIDE[1]), flush=True)
    doc = {"P1_check_value_by_class": {k: vcheck[k].to_json() for k in CLS},
           "opening_value_shape": {k: str(shape[k]) for k in CLS},
           "theta_slope": {k: str(g1[k]) for k in CLS},
           "theta_J": thJ.to_json(), "theta_A": thA.to_json(),
           "theta_window_conditions": window,
           "c_star": cstar, "c_lo": str(c_lo), "c_hi": str(c_hi),
           "theta_J_at": {str(x): thJ.float_at(x) for x in (BASE[0], F(31, 32), BASE[1], c_lo, c_hi)},
           "theta_A_at": {str(x): thA.float_at(x) for x in (BASE[0], F(31, 32), BASE[1], c_lo, c_hi)},
           "lagrangian": {"lambda_JJ": str(lamJ), "lambda_AA": str(lamA),
                          "lambda_positive_on": [describe(v["lower"]) or str(WIDE[0]) for v in lam_ok] +
                                                [describe(v["upper"]) or str(WIDE[1]) for v in lam_ok],
                          "vertices": 4096, "distinct_vertex_differences": len(diffs),
                          "identically_zero_differences": lag_tight,
                          "all_vertex_differences_nonnegative_on": [describe(lag_lo) or str(WIDE[0]),
                                                                    describe(lag_hi) or str(WIDE[1])],
                          "L_shape": "lambda_JJ gain_JJ + lambda_AA gain_AA at the shape = g1_AA g1_JJ (theta_A - theta_J): "
                                     "> 0 exactly when c > c*"}}
    return doc, (c_lo, c_hi), (thJ, thA, lamJ, lamA, vcheck)


# ------------------------------------------------------------------------------------------------
# certificates with the engine
# ------------------------------------------------------------------------------------------------
def class_profile_at(VAL, cv, resp):
    prof = dict(support())
    for j, n in enumerate(UNKNOWN):
        prof[name_row(n)] = VAL[j].exact_at(cv)
    for k in OPEN:
        prof[k] = F(0)
    prof.update(resp)
    return prof


def simplest_between(lo, hi):
    """A rational in [min, max] of two exact numbers, with the smallest power-of-two denominator bound."""
    lo, hi = min(lo, hi), max(lo, hi)
    n = 1
    while True:
        th = F((float(lo) + float(hi)) / 2).limit_denominator(n)
        if lo <= th <= hi:
            return th
        n *= 2


def certify_lo(VAL, cv, thJ, thA):
    from hinc.bestresponse import residuals
    from hinc.strategy import save_profile
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from verify_potsweep import load_exact
    tJ, tA = thJ.exact_at(cv), thA.exact_at(cv)
    assert tJ < tA
    th = simplest_between(tJ, tA)
    resp = {k: F(v) if k != (2, "B:1-F", "KK") else th for k, v in SHAPE.items()}
    prof = class_profile_at(VAL, cv, resp)
    g = engine_game(cv)
    p = engine_profile(g, prof)
    t = time.time()
    res = residuals(g, p)
    ok = all(x == 0 for x in res["r"])
    d = field_d(cv)[0]
    os.makedirs(os.path.join(OUT, "c_lo"), exist_ok=True)
    path = os.path.join(OUT, "c_lo", "policy_exact.json")
    save_profile(path, g, p, extra={"which": "P1-silent class-symmetric exact equilibrium just below c* "
                                             "(scripts/silent_threshold.py certify)",
                                    "number_field": "Q(sqrt(%d))" % d, "exact_r": [str(x) for x in res["r"]]})
    g2, p2, _ = load_exact(path)                       # parse back from text, re-check
    res2 = residuals(g2, p2)
    out = {"c": str(cv), "pot": str(3 * cv), "number_field": "Q(sqrt(%d))" % d, "theta": str(th),
           "theta_J": str(tJ), "theta_A": str(tA), "exact_r": [str(x) for x in res["r"]],
           "residuals_zero": ok, "reparsed_residuals_zero": all(x == 0 for x in res2["r"]),
           "P1_open_exactly_zero": all(p[I.index, 1] == 0 for I in g.isets if I.player == 0 and I.history == ""),
           "utilities": [str(x) for x in res["utilities"]], "utilities_float": [float(x) for x in res["utilities"]],
           "profile": {row_name(k): str(v) for k, v in sorted(prof.items())},
           "certificate": rel(path), "seconds": round(time.time() - t, 1)}
    print("c_lo = %s: exact r = %s (%s), theta = %s in [%.9f, %.9f]" % (
        cv, out["exact_r"], out["number_field"], th, float(tJ), float(tA)), flush=True)
    assert ok and out["reparsed_residuals_zero"] and out["P1_open_exactly_zero"]
    return out


def certify_hi(VAL, cv, thJ, thA, lamJ, lamA, vbet_model):
    """No class-symmetric responses deter P1 at cv: from the engine's payoff tables and values."""
    from hinc.bestresponse import residuals
    from hinc.evaluate import values
    g = engine_game(cv)
    tJ, tA = thJ.exact_at(cv), thA.exact_at(cv)
    assert tA < tJ                                     # the window is empty
    th = simplest_between(tA, tJ)
    prof = class_profile_at(VAL, cv, {k: F(v) if k != (2, "B:1-F", "KK") else th for k, v in SHAPE.items()})
    p = engine_profile(g, prof)
    nodes = g.tree.by_history()
    V = values(g, p)
    cls1 = [CLS.index(g.seats[0].labels[h][0] * 2) for h in range(len(g.seats[0].hands))]
    clsd = [[CLS.index(g.seats[i].labels[h][0] * 2) for h in g.deals[:, i]] for i in range(3)]
    vcheck = [F(0)] * 4
    vK = V[nodes["K"].id]
    for dd in range(g.D):
        vcheck[clsd[0][dd]] = vcheck[clsd[0][dd]] + g.prior_x[dd] * vK[dd, 0]
    S = {}
    for t in ("B:1-F-F", "B:1-F-C", "B:1-C-F", "B:1-C-C"):
        arr = np.full((4, 4, 4), F(0), dtype=object)
        for dd, row in enumerate(g.payoff_x[nodes[t].id]):
            arr[clsd[0][dd], clsd[1][dd], clsd[2][dd]] += g.prior_x[dd] * row[0]
        S[t] = arr
    lam = [F(0)] * 4
    lam[0], lam[3] = (rat(sp.sympify(x).subs(CS, sp.Rational(cv.numerator, cv.denominator))) for x in (lamJ, lamA))
    assert lam[0] > 0 and lam[3] > 0

    def gains(y):
        a = [y[(1, "B:1", k)] for k in CLS]
        b = [y[(2, "B:1-F", k)] for k in CLS]
        d = [y[(2, "B:1-C", k)] for k in CLS]
        out = []
        for k1 in range(4):
            v = F(0)
            for k2 in range(4):
                for k3 in range(4):
                    v += ((1 - a[k2]) * ((1 - b[k3]) * S["B:1-F-F"][k1, k2, k3] + b[k3] * S["B:1-F-C"][k1, k2, k3])
                          + a[k2] * ((1 - d[k3]) * S["B:1-C-F"][k1, k2, k3] + d[k3] * S["B:1-C-C"][k1, k2, k3]))
            out.append(v - vcheck[k1])
        return out

    worst, nverts, vb_ok = None, 0, True
    for bits in itertools.product((0, 1), repeat=12):
        y = {r: F(x) for r, x in zip(RESP, bits)}
        gk = gains(y)
        L = lam[0] * gk[0] + lam[3] * gk[3]
        nverts += 1
        if worst is None or L < worst[0]:
            worst = (L, bits, gk)
        if nverts <= 64:                                # the model's opening values agree with the engine's
            s = {YS[r]: x for r, x in zip(RESP, bits)}
            s[CS] = sp.Rational(cv.numerator, cv.denominator)
            vb_ok &= all(rat(vbet_model[k].subs(s)) == gk[i] + vcheck[i] for i, k in enumerate(CLS))
    proof = worst[0] > 0
    forced = {I.index: 0 for I in g.isets if I.player == 0 and I.history == ""}
    rest = residuals(g, p, forced=forced)
    full = residuals(g, p)
    out = {"c": str(cv), "pot": str(3 * cv), "number_field": "Q(sqrt(%d))" % field_d(cv)[0],
           "lambda": {"JJ": str(lam[0]), "AA": str(lam[3])}, "vertices": nverts,
           "min_over_vertices_of_lambda_gain": str(worst[0]), "min_float": float(worst[0]),
           "argmin_vertex": {row_name(r): x for r, x in zip(RESP, worst[1])},
           "gains_at_argmin_float": {k: float(x) for k, x in zip(CLS, worst[2])},
           "no_deterring_responses": proof, "model_opening_values_match_engine_at_64_vertices": vb_ok,
           "on_path_restricted_r_P1_opening_fixed": [str(x) for x in rest["r"]],
           "on_path_restricted_r_zero": all(x == 0 for x in rest["r"]),
           "theta_A": str(tA), "theta_J": str(tJ), "theta_between": str(th),
           "full_r_at_theta_between": [str(x) for x in full["r"]],
           "full_r_at_theta_between_float": [float(x) for x in full["r"]]}
    print("c_hi = %s: min over 4096 vertices of lambda.gain = %.3e > 0: %s; restricted r = %s; full r at "
          "theta %s = %s" % (cv, float(worst[0]), proof, ["%.1e" % float(x) for x in rest["r"]], th,
                             ["%.2e" % float(x) for x in full["r"]]), flush=True)
    assert proof and vb_ok and out["on_path_restricted_r_zero"] and full["r"][0] > 0
    return out


# ------------------------------------------------------------------------------------------------
def derive():
    t = time.time()
    doc = {"amendment": 7, "scope": ("threshold of the P1-silent branch with the 7-row on-path support of the "
                                     "certificates at 61/64..253/256, class-symmetric profiles; not a proof "
                                     "that no P1-silent equilibrium exists above c*")}
    doc["model_check"] = check_model()
    VAL, doc["closed_form"] = closed_form()
    doc["support"], lo, hi, doc["support_fixed_split"] = check_support(VAL)
    doc["support_valid_from"] = describe(lo[0]) if lo else str(WIDE[0])
    doc["support_valid_from_binding"] = lo[1] if lo else None
    doc["support_valid_to"] = describe(hi[0]) if hi else str(WIDE[1])
    doc["support_valid_to_binding"] = hi[1] if hi else None
    doc["deterrence"], (c_lo, c_hi), extra = deterrence(VAL)
    # the branch is a Nash equilibrium on [c_s, c*]: support from c_s, theta window (all its conditions
    # hold below c*), and no deterrence on (c*, 2] (theta_A < theta_J there and the Lagrangian bound)
    cs_lo = lo[0][1] if lo else WIDE[0]
    for w in doc["deterrence"]["theta_window_conditions"][:-2]:
        assert w["fails_below"] is None or F(w["fails_below"]["isolating_interval"][1]) <= cs_lo
    lag = doc["deterrence"]["lagrangian"]["all_vertex_differences_nonnegative_on"]
    assert lag == [str(WIDE[0]), str(WIDE[1])]
    doc["summary"] = {
        "c_star": doc["deterrence"]["c_star"],
        "branch_is_nash_on": [doc["support_valid_from"], "c_star"],
        "fails_below_c_s_by": doc["support_valid_from_binding"],
        "no_class_symmetric_deterrence_on": ["c_star (exclusive)", str(WIDE[1])],
        "on_path_support_ends_at": doc["support_valid_to"], "on_path_support_ends_by": doc["support_valid_to_binding"],
        "c_lo": str(c_lo), "c_hi": str(c_hi)}
    doc["seconds"] = round(time.time() - t, 1)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "derivation.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    return VAL, doc, (c_lo, c_hi), extra


def write_configs(c_lo, c_hi):
    os.makedirs(os.path.join(ROOT, "configs", "threshold"), exist_ok=True)
    for cv in (c_lo, c_hi):
        cfg = config_for(cv)
        with open(os.path.join(ROOT, "configs", "threshold", cfg["name"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=1)
        print("wrote configs/threshold/%s.json" % cfg["name"])


def certify(VAL, c_lo, c_hi, extra):
    thJ, thA, lamJ, lamA, _ = extra
    for cv in (c_lo, c_hi):
        path = os.path.join(ROOT, "configs", "threshold", config_for(cv)["name"] + ".json")
        with open(path) as f:
            assert json.load(f) == config_for(cv), "config missing or changed: " + path
    doc = {"amendment": 8, "c_lo": certify_lo(VAL, c_lo, thJ, thA),
           "c_hi": certify_hi(VAL, c_hi, thJ, thA, lamJ, lamA, opening_values())}
    with open(os.path.join(OUT, "certificates.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    VAL, doc, (c_lo, c_hi), extra = derive()
    print("c_lo = %s, c_hi = %s" % (c_lo, c_hi))
    if cmd == "configs":
        write_configs(c_lo, c_hi)
    elif cmd in ("certify", "all"):
        certify(VAL, c_lo, c_hi, extra)
    elif cmd != "derive":
        raise SystemExit(__doc__)
