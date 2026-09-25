"""Mechanised part of the forcing chain (MASTER_DATA 16.13): the leading form of
an unreached coordinate is linear in the tremble ratios, so bounding each of its
coefficients over the Nash windows of Table 4 settles the coordinate whenever the
bounds share a sign.  Run on all 12 FAMILY leaves; c43 = 1 and c13 = 0 everywhere.
usage:  python forcecheck.py
"""

import numpy as np, sympy as sp, seqset, refine
from fractions import Fraction as F
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
D, R, X = refine.build_DR(); EPS = seqset.EPS
WIN = {"b22": (F(0), F(5841,10000)), "c34": (F(0), F(1)), "b32": (F(0), F(15,16)),
       "c33": (F(0), F(15,16)), "c13": (F(0), F(5269,10000)), "c23": (F(0), F(7,12)), "c43": (F(0), F(1))}
def coef_bounds(form, rs):
    p = sp.Poly(form, *rs); out = {}
    for mono, c in zip(p.monoms(), p.coeffs()):
        if sum(mono) != 1: return None
        g = rs[mono.index(1)]
        f = sp.expand(c); lo = hi = None
        # multilinear in the remaining profile symbols, each in its window
        vars_ = sorted(f.free_symbols, key=str)
        if not vars_: lo = hi = sp.nsimplify(f)
        else:
            vals = [WIN.get(str(v), (F(0), F(1))) for v in vars_]
            import itertools
            for corner in itertools.product(*[(sp.Rational(a.numerator,a.denominator), sp.Rational(b.numerator,b.denominator)) for a,b in vals]):
                z = f.subs(dict(zip(vars_, corner)))
                lo = z if lo is None else min(lo, z); hi = z if hi is None else max(hi, z)
        out[str(g)] = (lo, hi)
    return out
for k in seqset.FAM:
    lab = L[k]
    out, pin = refine.closure(lab, verbose=False)
    pin2 = dict(pin); pin2.update({v: r[0] for v, r in out.items()}); pin2[I["b32"]] = 0
    sub = {}
    for w, val in pin2.items():
        rw = sp.Symbol("r_" + NAME[w]); sub[X[w]] = EPS * rw if val == 0 else 1 - EPS * rw
    msg = []
    for n in ("c43", "c13"):
        kd, A = refine.leading(sp.expand(D[I[n]].subs(sub)), EPS)
        rs = sorted([s for s in A.free_symbols if str(s).startswith("r_")], key=str)
        cb = coef_bounds(A, rs)
        sgn = "all > 0 -> %s = 1" % n if all(lo > 0 for lo, hi in cb.values()) else ("all < 0 -> %s = 0" % n if all(hi < 0 for lo, hi in cb.values()) else "mixed")
        msg.append("%-4s %s" % (n, sgn))
    print("leaf %4d: %s" % (k, "   |   ".join(msg)), flush=True)
