"""Second pass over nefull's ranges: for every bound whose attainment is
undecided (no witness at T, {x >= T} not certified empty either), try the
small-denominator rationals between the best known equilibrium value and the
certified bound with a larger B&B budget, and look for an exact witness
there.  Updates nefull_ranges.txt / nefull_certs.json.gz in place.
usage:  python nefull_refine.py [workers]
"""
import numpy as np, sys, time, json, gzip, os
import sympy as sp
from fractions import Fraction as F
import kuhn3p as K, symleaf as SL, certbox, nefull

NAME = K.PARAM_NAME; I = K.NAME_IDX


def refine(a):
    key, rec = a
    k, name, word = key.split(":"); k = int(k); sign = rec["sign"]
    lab, X, syms, G, mixv, dcv, priv, gens, polys, kinds, orig, gidx, mixmask, pts, starts = nefull._leaf(k)
    t = gidx.index(I[name]); g = gens[t]; bounds = SL._bounds(lab, mixv, dcv)
    T = nefull.F(*map(int, rec["T"].split("/")))
    known = float(pts[:, t].max() if sign > 0 else pts[:, t].min()) if len(pts) else float(T)
    xbest = nefull.numeric_extreme(polys, kinds, gens, t, sign, starts)
    if xbest is not None and sign * float(xbest[t]) > sign * known: known = float(xbest[t])
    else: xbest = pts[np.argmax(pts[:, t]) if sign > 0 else np.argmin(pts[:, t])] if len(pts) else xbest
    def empty_beyond(Tq, strict, budget):
        Tr = sp.Rational(Tq.numerator, Tq.denominator); side = g - Tr if sign > 0 else Tr - g
        r = certbox.prove_empty_cert(polys + [side], kinds + [">" if strict else ">="], gens, bounds, budget, origins=orig + [("side",)], lab=[int(v) for v in lab], gidx=gidx)
        if r[0]: r[1]["gens"] = gidx
        return r[1] if r[0] else None
    # candidates between known (inclusive) and T, small denominators first
    cands = set()
    for den in (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 25, 32, 40, 48, 50, 64, 80, 96, 100, 128):
        lo_, hi_ = (known, float(T)) if sign > 0 else (float(T), known)
        for n in range(int(np.floor(lo_ * den)) - 1, int(np.ceil(hi_ * den)) + 2):
            c = F(n, den)
            if lo_ - 1e-9 <= float(c) <= hi_ + 1e-9: cands.add(c)
    cands = sorted(cands, key=lambda c: (-float(c) if sign > 0 else float(c)))     # from T inward
    best = (T, rec["attained"], None, rec.get("witness"))
    for c in cands:
        if (sign > 0 and c > T) or (sign < 0 and c < T): continue
        cert = empty_beyond(c, True, 150)
        if cert is None: break                                    # cannot certify beyond c: stop tightening
        wit = nefull.snap_witness(polys, kinds, gens, xbest if xbest is not None else np.full(len(gens), 0.5), t, c, mixmask)
        if wit is not None:
            best = (c, True, cert, {str(gg): certbox.fstr(q) for gg, q in wit.items()}); break
        c2 = empty_beyond(c, False, 150)
        best = (c, (False if c2 is not None else None), cert, None)
        if c2 is not None: break
    return key, best


if __name__ == "__main__":
    nw = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    with gzip.open("nefull_certs.json.gz", "rt") as f: certs = json.load(f)
    todo = [(key, rec) for key, rec in certs.items() if rec["attained"] is None]
    print("%d undecided bounds" % len(todo), flush=True)
    from multiprocessing import Pool
    t0 = time.time(); changed = 0
    with Pool(nw) as pool:
        for key, (T, att, cert, wit) in pool.imap_unordered(refine, todo, chunksize=1):
            rec = certs[key]
            if cert is not None:
                rec["T"] = certbox.fstr(T); rec["attained"] = att; rec["cert"] = cert; rec["witness"] = wit; changed += 1
            elif att is not None: rec["attained"] = att; changed += 1
            print("   %-14s -> %s attained=%s" % (key, T, att), flush=True)
    with gzip.open("nefull_certs.json.gz", "wt") as f: json.dump(certs, f)
    # rewrite the ranges table from the certs
    L = np.load("enum6_pat_silentR.npy")
    with np.load("symleaf_silentR.npz") as z: vd = z["verdict"]
    fam = [int(k) for k in np.flatnonzero(vd == SL.VC["FAMILY"])]
    fmt = lambda T: "?" if T is None else ("%s" % T if T.denominator <= 100 else "%.6f" % float(T))
    glob = {}
    with open("nefull_ranges.txt", "w") as f:
        f.write("leaf sub  coord label     inf            sup      attained(inf,sup)\n")
        for k in fam:
            lab, X, syms, G, mixv, dcv, priv, gens, polys, kinds, orig, gidx, mixmask, pts, starts = nefull._leaf(k)
            sub = "A" if lab[I["c11"]] == 0 else ("B" if lab[I["c21"]] == 2 else "C")
            for t in range(len(gens)):
                name = NAME[gidx[t]]; lbl = "MIX" if mixmask[t] else "DC"
                ri = certs.get("%d:%s:inf" % (k, name)); rs = certs.get("%d:%s:sup" % (k, name))
                Ti = F(*map(int, ri["T"].split("/"))) if ri else None; Ts = F(*map(int, rs["T"].split("/"))) if rs else None
                f.write("%4d  %s   %-4s %-4s  %12s   %12s      %-5s %-5s\n" % (k, sub, name, lbl, fmt(Ti), fmt(Ts), ri["attained"] if ri else "?", rs["attained"] if rs else "?"))
                if Ti is not None and Ts is not None:
                    g0 = glob.get(name, (Ti, Ts)); glob[name] = (min(g0[0], Ti), max(g0[1], Ts))
        f.write("\n=== union over the 12 leaves (coordinates that are MIX or constrained DC somewhere) ===\n")
        for name in sorted(glob, key=lambda n: I[n]):
            lo_, hi_ = glob[name]; f.write("   %-4s  [%s, %s]\n" % (name, fmt(lo_), fmt(hi_)))
    print("refined %d of %d, %.0fs" % (changed, len(todo), time.time() - t0))
