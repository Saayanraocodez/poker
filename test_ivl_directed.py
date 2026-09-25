"""Check ivl.bounds (directed) against the SAME recursion in exact rationals:
directed bounds must enclose the exact-arithmetic bounds, and the nearest
version, and be within a few ulps of them.  Also exact-zero preservation."""
import numpy as np, time, sys
from fractions import Fraction as F
import ivl, tree as T

ND, NPOS = T.ND, T.NPOS
INT, LEAF, AGGC, PASC, COORD, PAYT = ivl.INT, ivl.LEAF, T.AGGC, T.PASC, T.COORD, T.PAYT

def exact_bounds(lo, hi):
    """one box (48,) -> exact DLO, DHI, RH, DMIN, DMAX as Fractions (lists of 48)"""
    lo = [F(x) for x in lo]; hi = [F(x) for x in hi]
    Vlo = {}; Vhi = {}
    for pos in LEAF:
        Vlo[pos] = [[F(PAYT[d, pos, p]) for p in range(3)] for d in range(ND)]; Vhi[pos] = Vlo[pos]
    for pos in INT[::-1]:
        Vlo[pos] = []; Vhi[pos] = []
        for d in range(ND):
            c = COORD[d, pos]; xl, xh = lo[c], hi[c]
            rl = []; rh = []
            for p in range(3):
                al, ah = Vlo[AGGC[pos]][d][p], Vhi[AGGC[pos]][d][p]
                pl, ph = Vlo[PASC[pos]][d][p], Vhi[PASC[pos]][d][p]
                rl.append(min(xl*al + (1-xl)*pl, xh*al + (1-xh)*pl))
                rh.append(max(xl*ah + (1-xl)*ph, xh*ah + (1-xh)*ph))
            Vlo[pos].append(rl); Vhi[pos].append(rh)
    Rlo = [[F(0)]*NPOS for _ in range(ND)]; Rhi = [[F(0)]*NPOS for _ in range(ND)]
    for d in range(ND): Rlo[d][0] = F(1); Rhi[d][0] = F(1)
    for pos in INT:
        for d in range(ND):
            c = COORD[d, pos]
            Rlo[d][AGGC[pos]] = Rlo[d][pos] * lo[c]; Rhi[d][AGGC[pos]] = Rhi[d][pos] * hi[c]
            Rlo[d][PASC[pos]] = Rlo[d][pos] * (1 - hi[c]); Rhi[d][PASC[pos]] = Rhi[d][pos] * (1 - lo[c])
    DLO = [F(0)]*48; DHI = [F(0)]*48; RH = [F(0)]*48; DMIN = [None]*48; DMAX = [None]*48
    for a, pos in enumerate(INT):
        i = ivl.OWNER_PL[a]
        for d in range(ND):
            Dlo = Vlo[AGGC[pos]][d][i] - Vhi[PASC[pos]][d][i]
            Dhi = Vhi[AGGC[pos]][d][i] - Vlo[PASC[pos]][d][i]
            rl, rh = Rlo[d][pos], Rhi[d][pos]
            dlo = rl*Dlo if Dlo >= 0 else rh*Dlo
            dhi = rh*Dhi if Dhi >= 0 else rl*Dhi
            c = COORD[d, pos]
            DLO[c] += dlo; DHI[c] += dhi; RH[c] += rh
            DMIN[c] = Dlo if DMIN[c] is None else min(DMIN[c], Dlo)
            DMAX[c] = Dhi if DMAX[c] is None else max(DMAX[c], Dhi)
    return [x/24 for x in DLO], [x/24 for x in DHI], RH, DMIN, DMAX

rng = np.random.default_rng(5)
B = 60
LO = rng.random((B, 48)); HI = rng.random((B, 48)); LO, HI = np.minimum(LO, HI), np.maximum(LO, HI)
# exact endpoints and degenerate boxes in the mix
LO[:20] = np.where(rng.random((20, 48)) < 0.4, 0.0, LO[:20]); HI[:20] = np.where(rng.random((20, 48)) < 0.4, 1.0, HI[:20])
LO[20:30] = 0.0; HI[20:30] = 1.0
pin = rng.random((10, 48)); LO[30:40] = pin; HI[30:40] = pin          # points
HI[40:50] = np.where(rng.random((10, 48)) < 0.3, 0.0, HI[40:50]); LO[40:50] = np.minimum(LO[40:50], HI[40:50])
LO[50:60] = np.where(rng.random((10, 48)) < 0.3, 1.0, LO[50:60]); HI[50:60] = np.maximum(LO[50:60], HI[50:60])

t0 = time.time(); D = ivl.bounds(LO, HI); td = time.time() - t0
t0 = time.time(); N = ivl._bounds_nearest(LO, HI); tn = time.time() - t0
worst = 0.0; ulps = 0; nz_bad = 0; bad = 0
for b in range(B):
    E = exact_bounds(LO[b], HI[b])
    for k, (name, sgn) in enumerate([("DLO", -1), ("DHI", 1), ("RH", 1)]):
        for c in range(48):
            e = E[k][c]; d = F(D[k][b, c]); n = F(N[k][b, c])
            if sgn < 0 and d > e: bad += 1; print("VIOLATION", name, b, c, float(d - e))
            if sgn > 0 and d < e: bad += 1; print("VIOLATION", name, b, c, float(e - d))
            worst = max(worst, abs(float(d - e)))
            if e == 0 and d != 0: nz_bad += 1
            if e != 0 and d == 0: nz_bad += 1
    for k, (name, sgn) in enumerate([("DMIN", -1), ("DMAX", 1)], 3):
        for c in range(48):
            e = E[k][c]; d = F(D[k][b, c])
            if sgn < 0 and d > e: bad += 1; print("VIOLATION", name, b, c, float(d - e))
            if sgn > 0 and d < e: bad += 1; print("VIOLATION", name, b, c, float(e - d))
            worst = max(worst, abs(float(d - e)))
print("boxes %d  violations %d  zero-mismatch %d  worst |directed - exact| %.2e   time directed %.3fs nearest %.3fs (x%.1f)"
      % (B, bad, nz_bad, worst, td, tn, td / tn))
# directed encloses nearest
enc = (D[0] <= N[0] + 0).all() and (D[1] >= N[1]).all() and (D[2] >= N[2]).all()
print("directed encloses nearest:", enc, " max gap %.2e" % max((N[0]-D[0]).max(), (D[1]-N[1]).max()))
# big batch timing
LO = rng.random((512, 48)); HI = rng.random((512, 48)); LO, HI = np.minimum(LO, HI), np.maximum(LO, HI)
t0 = time.time()
for _ in range(20): ivl.bounds(LO, HI)
td = (time.time() - t0) / 20
t0 = time.time()
for _ in range(20): ivl._bounds_nearest(LO, HI)
tn = (time.time() - t0) / 20
print("batch 512: directed %.1f ms  nearest %.1f ms  (x%.1f)" % (1e3*td, 1e3*tn, td/tn))

# which quantities have zero mismatches?
rng = np.random.default_rng(5)
B = 60
LO = rng.random((B, 48)); HI = rng.random((B, 48)); LO, HI = np.minimum(LO, HI), np.maximum(LO, HI)
LO[:20] = np.where(rng.random((20, 48)) < 0.4, 0.0, LO[:20]); HI[:20] = np.where(rng.random((20, 48)) < 0.4, 1.0, HI[:20])
LO[20:30] = 0.0; HI[20:30] = 1.0
pin = rng.random((10, 48)); LO[30:40] = pin; HI[30:40] = pin
HI[40:50] = np.where(rng.random((10, 48)) < 0.3, 0.0, HI[40:50]); LO[40:50] = np.minimum(LO[40:50], HI[40:50])
LO[50:60] = np.where(rng.random((10, 48)) < 0.3, 1.0, LO[50:60]); HI[50:60] = np.maximum(LO[50:60], HI[50:60])
D = ivl.bounds(LO, HI)
from collections import Counter
cnt = Counter()
for b in range(B):
    E = exact_bounds(LO[b], HI[b])
    for k, name in enumerate(["DLO", "DHI", "RH", "DMIN", "DMAX"]):
        for c in range(48):
            e = E[k][c]; d = F(D[k][b, c])
            if (e == 0) != (d == 0): cnt[(name, "exact0" if e == 0 else "dir0")] += 1
print("zero mismatches by quantity:", dict(cnt))
