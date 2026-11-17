"""Sharper certified windows for Table 4 (2026-11-16): for a (leaf, coordinate, side) whose certified bound
in nefull_ranges.txt is slack, try to certify emptiness of {leaf system, x_v > T} (or < T) at tighter rational
T with a larger B&B budget (certbox.prove_empty_cert), and verify every certificate found with the
independent checker (checkcert.check_box_cert), exactly as checknefull.py does.
Leaf labels come from independent_check/family_leaves.json, so no ignored data file is needed.

usage:  python makeD.py ; python sharpen_ranges.py <leaf> <coord> <sup|inf> <budget> <T1> [T2 ...]
        (T as fractions, tried in the order given; results appended to ranges_sharpened.txt)
"""
import sys, json, time
from fractions import Fraction as F
import sympy as sp
import kuhn3p as K, symleaf as SL, certbox, nefull, checkcert as C

I = K.NAME_IDX
leaf, name, word, budget = int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4])
Ts = [F(t) for t in sys.argv[5:]]
sign = 1 if word == "sup" else -1
lab = json.load(open("independent_check/family_leaves.json"))[str(leaf)]
X, syms, G, mixv, dcv, priv, gens, polys, kinds, orig = nefull.leaf_system(lab)
gidx = mixv + dcv; t = gidx.index(I[name]); g = gens[t]; bounds = SL._bounds(lab, mixv, dcv)
for T in Ts:
    t0 = time.time()
    Tr = sp.Rational(T.numerator, T.denominator); side = g - Tr if sign > 0 else Tr - g
    r = certbox.prove_empty_cert(polys + [side], kinds + [">"], gens, bounds, budget, origins=orig + [("side",)], lab=[int(v) for v in lab], gidx=gidx)
    if not r[0]:
        line = "%d %s %s T=%s budget %d: no certificate (%.0fs)" % (leaf, name, word, T, budget, time.time() - t0)
    else:
        cert = r[1]; cert["gens"] = gidx
        tt = cert["gens"].index(I[name]); nv = len(cert["gens"])
        sd = C.padd(C.var(tt, nv), C.const(-T, nv)) if sign > 0 else C.padd(C.pscale(C.var(tt, nv), F(-1)), C.const(T, nv))
        base = C.rowof_for(lab, cert["gens"])
        def rowof(og, base=base, sd=sd):
            if og[0] == "side": return sd, ">"
            return base(og)
        try:
            n = C.check_box_cert(cert, rowof, lab); ok = "VERIFIED by checkcert (%d nodes)" % n
            json.dump(cert, open("ranges_sharpened_%d_%s_%s.json" % (leaf, name, word), "w"))
        except C.Bad as ex:
            ok = "CHECKER REJECTED: %s" % ex
        line = "%d %s %s: {x %s %s} is empty on the leaf, T = %s = %.6f, budget %d: %s (%.0fs)" % (leaf, name, word, ">" if sign > 0 else "<", T, T, float(T), budget, ok, time.time() - t0)
    print(line, flush=True)
    open("ranges_sharpened.txt", "a").write(line + "\n")
