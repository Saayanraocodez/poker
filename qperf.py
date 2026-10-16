"""Open problem 2, last part: does QUASI-PERFECTION (van Damme 1984) select c33 = lo + w/3?

Quasi-perfect: sigma is the limit of completely mixed profiles x^n such that, for every player k
and every information set h of k, sigma_k's continuation is a best reply at h against x^n_{-k}
-- the OTHER players tremble, k's own later moves are taken from sigma_k itself (this is the one
difference from extensive-form perfection, where k's own later trembles count too).

In this game's coordinates the condition at k's coordinate v is the D-condition with the
own-reach-stripped gradient evaluated at the MIXED profile (sigma_k, x_{-k}):
    D_v(sigma_k, x_{-k}) = 0 where 0 < sigma_v < 1,   <= 0 where sigma_v = 0,   >= 0 where sigma_v = 1
(local optimality at every own set with own continuation sigma_k is optimality of the
continuation, by backward induction over k's own tree).  So the certificate is refine.perfect_cert
with each row's OWN-player columns removed from the Jacobian:
  1. an inward direction delta (delta_v > 0 where sigma_v = 0, < 0 where sigma_v = 1) along which
     every interior coordinate stays indifferent to first order and every tight pure coordinate
     keeps its sign strictly (or its D is sign-definite on the whole cube) -- an exact LP (exlp);
  2. the indifference rows M -- EVERY interior coordinate whose D, with the owner's own coordinates
     frozen at sigma, is not identically zero (stricter than perfect_cert, which drops rows whose
     gradient vanishes at sigma) -- of full rank, so the implicit function theorem gives the curve
     x(t) = sigma + t delta + O(t^2), completely mixed, along which sigma is a best reply.
The same test with the full Jacobian is the perfection control (it must reproduce Theorem 6.5).

Points: leaf 469, b11 = b21 = 1/8, c11 = 1/4 (Theorem 6.5's slice), every off-path coordinate at
its refined value, c33 swept through the Nash window [1/2, 23/32]; the normal-form proper point
is 55/96.

usage:  python qperf.py      -> log_qperf.txt (stdout), qperf.json
"""
import json
from fractions import Fraction as F
import numpy as np
import sympy as sp
import refine, seqset

L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
NV = 48
owner = lambda i: i // 16


def restrict_own(poly, sig, k):
    """D_v with player k's own coordinates replaced by sigma_k: a polynomial in the others' coordinates."""
    out = {}
    for mon, c in poly.items():
        t = c; m2 = list(mon)
        for w, e in enumerate(mon):
            if e and owner(w) == k:
                t *= sig[w]; m2[w] = 0
                if t == 0: break
        if t:
            key = tuple(m2); out[key] = out.get(key, F(0)) + t
    return {m: c for m, c in out.items() if c}


def cert(sig, quasi):
    D = refine.D_all(); J = refine.jac()
    if quasi:
        J = [{w: d for w, d in J[v].items() if owner(w) != owner(v)} for v in range(NV)]
    st, val, delta = refine.lp_first_order(sig, J)
    if st != "optimal": return False, "no first-order direction (%s)" % st, None
    if val == 0: return False, "no uniform inward direction (s* = 0)", None
    tight = []
    for v in range(NV):
        if sig[v] in (0, 1) and refine.ev(D[v], sig) == 0:
            g = sum(refine.ev(J[v][w], sig) * delta[w] for w in J[v])
            if g == 0:
                cs = list(D[v].values())
                ok = (sig[v] == 0 and all(c <= 0 for c in cs)) or (sig[v] == 1 and all(c >= 0 for c in cs))
                if not ok: tight.append(NAME[v])
            elif (sig[v] == 0 and g > 0) or (sig[v] == 1 and g < 0):
                tight.append(NAME[v] + "(wrong sign)")
    if tight: return False, "first-order tight and not sign-definite at %s" % ",".join(tight), None
    # rows: every interior coordinate whose (own-frozen, if quasi) D is not identically zero
    M = []
    for v in range(NV):
        if 0 < sig[v] < 1:
            Dv = restrict_own(D[v], sig, owner(v)) if quasi else D[v]
            if Dv: M.append(v)
    for v in M:
        assert refine.ev(D[v], sig) == 0
        g = sum(refine.ev(J[v][w], sig) * delta[w] for w in J[v])
        assert g == 0, "indifference not kept at first order: %s" % NAME[v]
    JM = sp.Matrix([[sp.Rational(refine.ev(J[v][w], sig)) if w in J[v] else 0 for w in range(NV)] for v in M])
    rk = JM.rank()
    if rk != len(M): return False, "indifference Jacobian rank %d < %d (rows %s)" % (rk, len(M), [NAME[v] for v in M]), None
    return True, {"s": str(val), "rank": rk, "rows": [NAME[v] for v in M],
                  "delta": {NAME[w]: str(delta[w]) for w in range(NV) if delta[w] != 0}}, delta


def point(c33):
    lab = L[469]
    d = json.load(open("seq_469.json"))
    rec = [r for r in d["cases"] if r["status"] == "SEQUENTIAL" and r["assign"].get("c23") == 0][0]
    assign = {I[n]: (v if v == "mix" else int(v)) for n, v in rec["assign"].items()}
    off = {}
    for v, val in assign.items():
        if val in (0, 1): off[NAME[v]] = F(int(val))
    for i in range(NV):
        if lab[i] == 0: off.setdefault(NAME[i], F(0))
        elif lab[i] == 1: off.setdefault(NAME[i], F(1))
    off["c33"] = c33
    for n in ("b11", "b21", "b23", "c11"): off.pop(n, None)
    s = seqset.family_point(F(1, 8), F(1, 8), F(0), F(1, 4), off)
    return lab, s


def main():
    pts = [F(1, 2), F(33, 64), F(17, 32), F(35, 64), F(9, 16), F(55, 96), F(37, 64), F(19, 32), F(5, 8),
           F(21, 32), F(11, 16), F(45, 64), F(23, 32)]
    out = []
    print("Quasi-perfection vs perfection on Theorem 6.5's slice (leaf 469, b11 = b21 = 1/8, c11 = 1/4)")
    print("Nash window c33 in [1/2, 23/32]; normal-form proper point 55/96\n")
    print("   c33       Nash   perfect (control)                    quasi-perfect")
    for c in pts:
        lab, s = point(c)
        nash = seqset.verify_point(lab, s)
        okp, ip, _ = cert(s, quasi=False)
        okq, iq, _ = cert(s, quasi=True)
        tag = lambda ok, info: ("CERTIFIED  s*=%s rank %d" % (info["s"], info["rank"])) if ok else info
        print("   %-8s  %-5s  %-38s  %s" % (c, "OK" if nash is None else "NO", tag(okp, ip)[:38], tag(okq, iq)))
        out.append(dict(c33=str(c), nash=nash is None, perfect=okp, perfect_info=ip if okp else str(ip),
                        quasi=okq, quasi_info=iq if okq else str(iq),
                        profile={NAME[i]: str(s[i]) for i in range(NV)}))
    json.dump(out, open("qperf.json", "w"), indent=1)
    print("\n[qperf.json written]")


if __name__ == "__main__":
    main()


# ------------------------------------------------ the whole open interval, symbolically in c33
G = sp.Symbol("c33")


def sev(poly, sig):
    """exact value of a monomial dict at a profile whose entries are sympy expressions in c33."""
    tot = sp.Integer(0)
    for mon, c in poly.items():
        t = sp.Rational(c.numerator, c.denominator)
        for w, e in enumerate(mon):
            if e: t = t * sig[w]
        tot += t
    return sp.expand(tot)


def sign_on(poly, lo, hi):
    """+1 / -1 if the univariate polynomial is strictly signed on the open interval (lo, hi), 0 if it is
    identically zero, None if it vanishes somewhere inside (exact: real-root isolation)."""
    p = sp.Poly(poly, G)
    if p.is_zero: return 0
    if p.degree() <= 0: return 1 if p.LC() > 0 else -1
    for r in sp.real_roots(p):
        if lo < r < hi: return None
    mid = (lo + hi) / 2
    return 1 if p.eval(mid) > 0 else -1


def interval_cert(quasi, lo=sp.Rational(1, 2), hi=sp.Rational(23, 32)):
    """The certificate of cert() for EVERY c33 in the open interval (lo, hi) at once: the direction
    delta found at c33 = 9/16 is fixed, and every condition is a polynomial in c33 whose sign is
    decided exactly on the interval."""
    D = refine.D_all(); J = refine.jac()
    if quasi:
        J = [{w: d for w, d in J[v].items() if owner(w) != owner(v)} for v in range(NV)]
    _, s0 = point(F(9, 16))
    ok, info, delta = cert(s0, quasi)
    assert ok
    sig = [sp.Rational(x.numerator, x.denominator) for x in s0]; sig[I["c33"]] = G
    dl = [sp.Rational(x.numerator, x.denominator) for x in delta]
    fails = []
    # (a) Nash: the D-condition at every coordinate, for every c33 in the interval
    for v in range(NV):
        sg = sign_on(sev(D[v], sig), lo, hi)
        x = s0[v] if v != I["c33"] else None
        if v == I["c33"]:
            if sg != 0: fails.append("Nash: D_c33 not identically 0")
        elif x == 0 and sg not in (0, -1): fails.append("Nash: D_%s" % NAME[v])
        elif x == 1 and sg not in (0, 1): fails.append("Nash: D_%s" % NAME[v])
        elif 0 < x < 1 and sg != 0: fails.append("Nash: D_%s != 0 at interior" % NAME[v])
    # (b) first order along the fixed delta
    for v in range(NV):
        g = sp.expand(sum(sev(J[v][w], sig) * dl[w] for w in J[v]))
        d0 = sign_on(sev(D[v], sig), lo, hi)
        mixed = (v == I["c33"]) or (0 < s0[v] < 1)
        if mixed:
            if sign_on(g, lo, hi) != 0: fails.append("first order: %s not kept indifferent" % NAME[v])
        elif d0 == 0:                                     # tight pure coordinate on the whole interval
            sg = sign_on(g, lo, hi)
            if sg == 0:
                cs = list(D[v].values())
                if not ((s0[v] == 0 and all(c <= 0 for c in cs)) or (s0[v] == 1 and all(c >= 0 for c in cs))):
                    fails.append("first order: %s tight, g = 0, not sign-definite" % NAME[v])
            elif sg is None or (s0[v] == 0 and sg > 0) or (s0[v] == 1 and sg < 0):
                fails.append("first order: %s wrong sign" % NAME[v])
        elif d0 is None:
            fails.append("deterrence of %s vanishes inside the interval" % NAME[v])
    # inward and completely mixed: delta_v > 0 where sigma_v = 0, < 0 where sigma_v = 1
    for v in range(NV):
        if v == I["c33"]: continue
        if s0[v] == 0 and not dl[v] > 0: fails.append("delta_%s not inward" % NAME[v])
        if s0[v] == 1 and not dl[v] < 0: fails.append("delta_%s not inward" % NAME[v])
    # (c) rank: an 8 x 8 minor whose determinant has no root in the interval
    M = []
    for v in range(NV):
        if v == I["c33"] or 0 < s0[v] < 1:
            Dv = restrict_own(D[v], s0, owner(v)) if quasi else D[v]
            if v == I["c33"] or Dv: M.append(v)
    JM = sp.Matrix([[sev(J[v][w], sig) if w in J[v] else 0 for w in range(NV)] for v in M])
    cols = [w for w in range(NV) if any(JM[r, w] != 0 for r in range(len(M)))]
    import itertools
    minor = None
    for C in itertools.combinations(cols, len(M)):
        det = sp.expand(JM[:, list(C)].det())
        if det != 0 and sign_on(det, lo, hi) in (1, -1):
            minor = ([NAME[w] for w in C], det); break
    if minor is None: fails.append("no full-rank minor on the whole interval")
    return fails, minor, [NAME[v] for v in M]


if __name__ == "__main__":
    print()
    print("THE WHOLE OPEN INTERVAL c33 in (1/2, 23/32), symbolically (fixed delta from c33 = 9/16):")
    for quasi in (False, True):
        fails, minor, rows = interval_cert(quasi)
        print("   %-14s %s" % ("quasi-perfect" if quasi else "perfect", "CERTIFIED for every c33 in the open interval" if not fails else "FAILED: %s" % fails))
        if minor: print("      rows %s; minor columns %s; det = %s" % (rows, minor[0], minor[1]))
