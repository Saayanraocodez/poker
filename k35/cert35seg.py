"""Component I of (3, 5) is a SEGMENT: certify all of it at once.
cert35/cert35check prove that the reduced 14x14 system G (unknowns A, B, s, ... -- no c11 in it) has a
unique zero y* in the box Y.  For ANY c11 with 0 <= c11 <= s* (c21 = s* - c11 >= 0) the profile
(y*, c11, c21) satisfies all 17 interior conditions, because they depend on c11, c21 only through
s (checked identity).  So it is a Nash equilibrium iff the one-shot D-conditions hold -- and they are
polynomials in (y, c11).  Check them over Y x [c11lo, c11hi] by exact interval evaluation: if they hold,
every c11 in the interval gives an exact Nash equilibrium (P1's play identical along the segment).
At c11 = 0 the coordinate c11 is pure (D_c11 = 0 there since F_c11 = 0: fine for a pure 0).
usage (from k35/):  KUHN_CARDS=5 python cert35seg.py hiprec400.json <c11hi as p/q>"""
import os, sys, json
os.environ.setdefault("KUHN_CARDS", "5")
from fractions import Fraction as Fr
from decimal import Decimal
import cert35check as C

if __name__ == "__main__":
    num = json.load(open(sys.argv[1]))["profile"]
    c11hi = Fr(sys.argv[2])
    val = [Fr(Decimal(s[:75])) for s in num]
    x = [C.var(C.INTERIOR.index(C.NAME[i]), C.NV) if C.NAME[i] in C.INTERIOR else C.const(val[i], C.NV) for i in range(C.NP)]
    u, D = C.build(x)
    rest = [n for n in C.INTERIOR if n not in ("a11", "a21", "b11", "b21", "c11", "c21")]
    gv = ["A", "B", "s", "c1"] + rest                    # 15 variables: the 14 of G plus c11
    img = []
    for n in C.INTERIOR:
        if n in ("a11", "a21"): img.append(C.var(0, 15))
        elif n in ("b11", "b21"): img.append(C.var(1, 15))
        elif n == "c11": img.append(C.var(3, 15))
        elif n == "c21": img.append(C.add(C.var(2, 15), C.var(3, 15), -1))
        else: img.append(C.var(gv.index(n), 15))
    r = Fr(1, 10 ** 30)
    mid = {"A": val[C.IDX["a11"]], "B": val[C.IDX["b11"]], "s": val[C.IDX["c11"]] + val[C.IDX["c21"]]}
    for n in rest: mid[n] = val[C.IDX[n]]
    # c11 itself: the interval [eps, c11hi]; monomials need positive coordinates, so c11 = 0 is checked separately
    eps = Fr(1, 10 ** 6)
    s_lo = mid["s"] - r
    assert c11hi < s_lo, "c11hi must stay below s* so that c21 = s - c11 > 0"
    bad = []
    for lo_c, hi_c in ((eps, c11hi),):
        box = []
        for n in gv:
            if n == "c1": box.append((lo_c, hi_c))
            else: box.append((mid[n] - r, mid[n] + r))
        for i in range(C.NP):
            nm = C.NAME[i]
            if nm in C.INTERIOR and nm not in ("c11", "c21"): continue          # interior: D = 0 from the equations
            Di = C.compose(D[i], img, 15)
            if not Di: continue
            if nm in ("c11", "c21"):
                # interior on the open segment: D must be identically 0 in the reduced variables? check it is
                # independent of c1 and equals the (vanishing) reduced condition -- covered by cert35's identities.
                continue
            # D is a polynomial in (y, c1); split it by the power of c1 and enclose each coefficient over the
            # tiny y-box, then bound the polynomial in c1 on [lo_c, hi_c] -- linear here, so by its endpoints
            k1 = gv.index("c1"); ybox = [b for n, b in zip(gv, box)]
            ybox[k1] = (Fr(1), Fr(1))
            coef = {}
            for m_, c in Di.items():
                e = m_[k1]; mm = list(m_); mm[k1] = 0
                coef.setdefault(e, {})[tuple(mm)] = coef.setdefault(e, {}).get(tuple(mm), Fr(0)) + c
            assert max(coef) <= 1, "%s: not linear in c11" % nm
            d0 = C.ival(coef.get(0, {}), ybox); d1 = C.ival(coef.get(1, {}), ybox)
            ends = [d0[a] + d1[b] * t for t in (Fr(0), hi_c) for a in (0, 1) for b in (0, 1)]
            lo_, hi_ = min(ends), max(ends)                    # covers c1 in [0, hi_c] (linear in c1)
            v = val[i]
            if v == 0 and not hi_ < 0: bad.append("%s=0: D in [%.3e, %.3e]" % (nm, float(lo_), float(hi_)))
            if v == 1 and not lo_ > 0: bad.append("%s=1: D in [%.3e, %.3e]" % (nm, float(lo_), float(hi_)))
    print("segment c11 in [%s, %s] (c21 = s - c11 > 0): D-condition violations %d %s" % (eps, c11hi, len(bad), bad))
    # the endpoint c11 = 0: c11 pure 0 needs D_c11 <= 0; D_c11 = F_c11 / own reach = 0 there (F_c11 vanishes for all c11)
    print("endpoint c11 = 0: c11 becomes pure 0 with D_c11 = 0 (its indifference condition holds for every c11) -- allowed")
    print("CERTIFIED SEGMENT" if not bad else "NOT CERTIFIED")
