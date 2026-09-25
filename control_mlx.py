"""Controls for mlx.py -- run before trusting any verdict built on it.

 1. POINT:        degenerate boxes (LO = HI) reproduce bgrad.grads_own to 1e-13.
 2. CONTAINMENT:  random boxes, random interior points: du inside [DLO, DHI].
 3. SOUNDNESS OF propagate: boxes built AROUND certified equilibria (all 744 of
    certified_eq_all.npy plus a sample of the 23,820 hunt equilibria), at widths
    1e-3 .. 0.5, must NOT be killed, and the equilibrium must remain inside the
    contracted box.  This is the control that matters: a contractor that
    narrows past a genuine equilibrium is unsound and every proof built on it
    is worthless.
 4. STRENGTH:     on random boxes, how often is the exact bound strictly tighter
    than the monomial-wise bound of provea11.py (same boxes, same conditions).
"""
import numpy as np, time, sys
import mlx, bgrad, symbet, provea11, kuhn3p as K

I = K.NAME_IDX
vars_, pos, conds = mlx.build()
cols = [I[v] for v in vars_]
rng = np.random.default_rng(1)

def full(X):
    P = np.zeros((X.shape[0], 48))
    for nm in symbet.T2_ONE: P[:, I[nm]] = 1.0
    P[:, cols] = X
    return P

# 1. point control
X = rng.random((3000, 27))
G = bgrad.grads_own(full(X))[:, cols]
DLO, DHI = mlx.bounds(conds, X, X)
e1 = max(np.abs(DLO - G).max(), np.abs(DHI - G).max())
print("1. POINT        max |bound - du| = %.2e   %s" % (e1, "OK" if e1 < 1e-13 else "*** FAIL"))

# 2. containment
B = 400
LO = rng.random((B, 27)); HI = rng.random((B, 27)); LO, HI = np.minimum(LO, HI), np.maximum(LO, HI)
t0 = time.time(); DLO, DHI = mlx.bounds(conds, LO, HI); dt = time.time() - t0
worst = -np.inf
for rep in range(50):
    X = LO + (HI - LO) * rng.random((B, 27))
    G = bgrad.grads_own(full(X))[:, cols]
    worst = max(worst, float((DLO - G).max()), float((G - DHI).max()))
print("2. CONTAINMENT  worst excess %.2e over %d boxes x 50 points   %s   (bounds: %.1f ms/box)"
      % (worst, B, "OK" if worst < 1e-13 else "*** FAIL", 1000 * dt / B))

# 3. propagate soundness around certified equilibria
EQ = np.load("certified_eq_all.npy")
try:
    H = np.load("hunt_eq_bet2.npy"); H = H[rng.choice(len(H), 2000, replace=False)]
    EQ = np.vstack([EQ, H])
except Exception as e:
    print("   (hunt_eq_bet2.npy not used: %s)" % e)
# certified equilibria must satisfy Table 2 exactly, else the reduction does not apply
t2 = np.maximum(np.abs(EQ[:, [I[n] for n in symbet.T2_ZERO]]).max(1), np.abs(1 - EQ[:, [I[n] for n in symbet.T2_ONE]]).max(1))
# ONLY equilibria on the Table-2 slice are valid controls for a slice prover: an
# equilibrium sustained by an off-path dominated action (b12 > 0 etc., see
# offpath.py) is not a point of the reduced problem at all.
EQ = EQ[t2 < 1e-9]
print("   controls on the Table-2 slice: %d (dropped %d off-slice equilibria)" % (len(EQ), (t2 >= 1e-9).sum()))
XE = EQ[:, cols]
bad_total = 0
for w in (1e-3, 1e-2, 0.1, 0.3, 0.5):
    # box = [x - w u, x + w u'] clipped to [0,1], random asymmetric inflation
    LO = np.clip(XE - w * rng.random(XE.shape), 0, 1)
    HI = np.clip(XE + w * rng.random(XE.shape), 0, 1)
    killed = 0; escaped = 0
    for s in range(0, len(XE), 256):
        lo, hi, x = LO[s:s+256], HI[s:s+256], XE[s:s+256]
        nlo, nhi, al, _, _, _ = mlx.propagate(conds, lo, hi)
        killed += int((~al).sum())
        esc = al & ((x < nlo - 1e-9) | (x > nhi + 1e-9)).any(axis=1)
        escaped += int(esc.sum())
    bad_total += killed + escaped
    print("   width %.3f : killed %d   equilibrium pushed outside its box %d   of %d" % (w, killed, escaped, len(XE)))
print("3. PROPAGATE    %s" % ("OK -- no certified equilibrium killed or excluded" if bad_total == 0 else "*** FAIL"))

# 4. strength vs monomial bound
pv, ppos, pconds, pdeps, _, _ = provea11.build()
assert pv == vars_
B = 400
LO = rng.random((B, 27)); HI = rng.random((B, 27)); LO, HI = np.minimum(LO, HI), np.maximum(LO, HI)
mLO, mHI = provea11.bounds(pconds, LO, HI)
eLO, eHI = mlx.bounds(conds, LO, HI)
wm = mHI - mLO; we = eHI - eLO
print("4. STRENGTH     mean width exact/monomial = %.3f ; exact strictly tighter on %.1f%% of (box,cond); "
      "exact never looser: %s" % ((we / np.maximum(wm, 1e-300)).mean(), 100 * (we < wm - 1e-12).mean(),
                                   bool((we <= wm + 1e-12).all())))
sys.exit(0 if (e1 < 1e-13 and worst < 1e-13 and bad_total == 0) else 1)
