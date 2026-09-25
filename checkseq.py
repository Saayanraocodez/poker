"""INDEPENDENT CHECKER for the sequential-equilibrium witnesses (seq_<leaf>.json).

Rebuilds the leading coefficients from the tree, re-reads the stored profile and
belief vector as Fractions, and re-tests every condition:

  * the profile is an exact Nash point of the leaf (every D_v with the right sign,
    the leaf's labels respected)  -- `seqset.verify_point`;
  * for every unreached coordinate, the leading coefficient A_v, reduced to the
    terms of its own lowest tremble class (the stored `tremble_order`), has the sign
    the profile's own value demands -- `<= 0` at 0, `>= 0` at 1, `= 0` interior;
  * every stored ratio is strictly positive and each information set's ratios sum to 1
    (each leading coefficient is homogeneous within one set, so the sets scale separately).

usage:  python checkseq.py [seq_<leaf>.json ...]
"""
import json, sys, glob
import numpy as np, sympy as sp
from fractions import Fraction as F
import seqset, refine

L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I


def check_case(lab, pieces, rec):
    polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = pieces
    s = [F(rec["witness"][NAME[i]]) for i in range(48)]
    bad = seqset.verify_point(lab, s)
    if bad: return "not a Nash point: %s" % bad
    bel = {k: F(v) for k, v in rec["beliefs"].items()}
    if any(v <= 0 for v in bel.values()): return "a stored ratio is not positive"
    grp = {}
    for k_ in bel: grp.setdefault(k_[2] + k_[4], []).append(k_)
    for key, ks in grp.items():
        if sum(bel[k_] for k_ in ks) != 1: return "the %s ratios do not sum to 1" % key
    order = rec.get("tremble_order") or {}
    sub = {syms[i]: sp.Rational(s[i].numerator, s[i].denominator) for i in sorted(syms)}
    bsub = {sp.Symbol(k): sp.Rational(v.numerator, v.denominator) for k, v in bel.items()}
    for v in unreached:
        a = sp.expand(A[v].subs(sub))
        if a == 0: continue
        lv = min([order[n] for n in order if sp.Symbol("r_" + n) in a.free_symbols], default=None)
        if lv is not None:
            a = sp.expand(a.subs({sp.Symbol("r_" + n): 0 for n in order if order[n] > lv}))
        if a == 0: continue
        val = a.subs(bsub)
        if val.free_symbols:                       # a ratio at a higher order: it vanishes
            val = sp.expand(val.subs({g: 0 for g in val.free_symbols}))
        x = s[v]
        if 0 < x < 1:
            if val != 0: return "A_%s = %s, but %s is interior" % (NAME[v], val, NAME[v])
        elif x == 0:
            if val > 0: return "A_%s = %s > 0, but %s = 0" % (NAME[v], val, NAME[v])
        else:
            if val < 0: return "A_%s = %s < 0, but %s = 1" % (NAME[v], val, NAME[v])
    return None


def main(paths):
    ok = bad = 0
    for p in paths:
        d = json.load(open(p)); k = d["leaf"]; lab = L[k]
        pieces = seqset.leaf_pieces(lab)
        for rec in d["cases"]:
            if rec["status"] != "SEQUENTIAL": continue
            why = check_case(lab, pieces, rec)
            if why: bad += 1; print("leaf %d %s: FAILED -- %s" % (k, rec["assign"], why))
            else: ok += 1
        print("%s: %d sequential witnesses checked" % (p, sum(1 for r in d["cases"] if r["status"] == "SEQUENTIAL")), flush=True)
    print("verified %d, failed %d  %s" % (ok, bad, "OK" if bad == 0 else "*** NOT VERIFIED"))
    return bad == 0


if __name__ == "__main__":
    main(sys.argv[1:] or sorted(glob.glob("seq_*.json")))
