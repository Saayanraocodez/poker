"""Replay every sharper range certificate in ranges_sharpened/ with the independent checker (checkcert),
as checknefull.py does for nefull's certificates, and the exact witnesses in ranges_sharpened/witnesses.json
with the independent engine.     usage:  python makeD.py ; python check_sharpened.py
"""
import json, glob, os, sys
from fractions import Fraction as F
import checkcert as C, kuhn3p as K
I = K.NAME_IDX
LV = json.load(open(os.path.join("independent_check", "family_leaves.json")))
ok = bad = 0
for f in sorted(glob.glob(os.path.join("ranges_sharpened", "*_*_*.json"))):
    d = json.load(open(f)); lab = LV[str(d["leaf"])]; T = F(d["T"]); cert = d["cert"]; sign = 1 if d["side"] == "sup" else -1
    t = cert["gens"].index(I[d["coord"]]); nv = len(cert["gens"])
    side = C.padd(C.var(t, nv), C.const(-T, nv)) if sign > 0 else C.padd(C.pscale(C.var(t, nv), F(-1)), C.const(T, nv))
    base = C.rowof_for(lab, cert["gens"])
    def rowof(og, base=base, side=side):
        if og[0] == "side": return side, ">"
        return base(og)
    try: C.check_box_cert(cert, rowof, lab); ok += 1
    except C.Bad as ex: bad += 1; print("%s: FAILED %s" % (f, ex))
wok = wbad = 0
wf = os.path.join("ranges_sharpened", "witnesses.json")
if os.path.exists(wf):
    sys.path.insert(0, "independent_check"); import indep
    for key, prof in json.load(open(wf)).items():
        leaf, coord, side, T = key.split(":")
        p = {n: F(v) for n, v in prof.items()}
        good = indep.exploitability(p) == [0, 0, 0] and p[coord] == F(T)
        wok += good; wbad += not good
print("sharpened range certificates: %d verified, %d failed; exact witnesses: %d verified, %d failed" % (ok, bad, wok, wbad))
sys.exit(1 if bad or wbad else 0)
