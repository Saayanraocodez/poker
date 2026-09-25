"""Independent check of nefull's range certificates (Fractions only).

For each entry "<leaf>:<coord>:<sup|inf>": the emptiness certificate proves
{leaf system, x_v > T} (sup) or {x_v < T} (inf) has no point -- verified by
checkcert.check_box_cert with the rows rebuilt from the leaf's labels plus
the side row; the witness, if any, is a rational point of the leaf with
x_v = T, verified by exact evaluation of the leaf system (MIX coordinates
strictly inside (0, 1)).  So T is the sup / inf of x_v over the leaf when
attained, and a certified bound otherwise.

usage:  python checknefull.py
"""
import json, gzip, time, pickle
import numpy as np
from fractions import Fraction as F
import checkcert as C
import kuhn3p as K

NAME = K.PARAM_NAME; I = K.NAME_IDX
MIX, DC = 2, 3


def leaf_rows(lab):
    """the leaf system over 48 coordinates: list of (poly48, kind)"""
    return C.leaf_system(lab)


def evaluate(p48, x):
    tot = F(0)
    for m, c in p48.items():
        v = c
        for j, e in enumerate(m):
            if e: v *= x[j] ** e
        tot += v
    return tot


if __name__ == "__main__":
    t0 = time.time()
    with gzip.open("nefull_certs.json.gz", "rt") as f: certs = json.load(f)
    L = np.load("enum6_pat_silentR.npy")
    ok = bad = wit_ok = wit_bad = 0
    for key, rec in certs.items():
        k, name, word = key.split(":"); k = int(k); lab = [int(v) for v in L[k]]
        T = C.fr(rec["T"]); v = I[name]; sign = rec["sign"]
        cert = rec["cert"]; gens = cert["gens"]; t = gens.index(v)
        side = C.padd(C.var(t, len(gens)), C.const(-T, len(gens))) if sign > 0 else C.padd(C.pscale(C.var(t, len(gens)), F(-1)), C.const(T, len(gens)))
        base = C.rowof_for(lab, gens)
        strict = ">" if rec["attained"] is not False else ">="      # non-attained bounds were certified with the closed side too; the stored cert is the strict one
        def rowof(og, base=base, side=side):
            if og[0] == "side": return side, ">"
            return base(og)
        try:
            C.check_box_cert(cert, rowof, lab); ok += 1
        except C.Bad as ex:
            bad += 1; print("%s: FAILED %s" % (key, ex)); continue
        if rec["witness"]:
            x = [F(0)] * 48
            for i in range(48):
                if lab[i] == 1: x[i] = F(1)
            for nm, q in rec["witness"].items(): x[I[nm]] = C.fr(q)
            # private DC coordinates (absent from the certificate's variables): the pair
            # x D >= 0 >= (1 - x) D is met by x = 1 if D > 0, x = 0 otherwise (D is free of x)
            D48 = C.leaf_D(lab)
            for i in range(48):
                if lab[i] == DC and i not in gens:
                    x[i] = F(1) if evaluate(D48[i], x) > 0 else F(0)
            good = x[v] == T and all(0 < x[i] < 1 for i in range(48) if lab[i] == MIX)
            for p48, kind in leaf_rows(lab):
                # rows of private coordinates are absent from the certificate's variables: skip rows that use a coordinate not in gens or pinned
                val = evaluate(p48, x)
                if kind == "=" and val != 0: good = False
                if kind == ">=" and val < 0: good = False
            if good: wit_ok += 1
            else: wit_bad += 1; print("%s: witness does not satisfy the leaf system" % key)
    print("range certificates: %d verified, %d failed; witnesses: %d verified, %d failed  (%.0fs)" % (ok, bad, wit_ok, wit_bad, time.time() - t0))
