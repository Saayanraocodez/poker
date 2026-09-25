"""Controls for bnb6.py.  Every one must pass before a bnb6 verdict is quoted.

 1. CONVEXITY of the pinned bounds -- the chord contractor's whole argument.
    Random boxes, random coordinate v, t on a grid: U_i(t) <= chord, L_i(t) >= chord.
 2. SOUNDNESS on the FULL cube: boxes around certified equilibria -- the 744
    slice equilibria, a sample of the hunt equilibria INCLUDING off-slice ones
    (valid controls here, unlike for a slice prover), and offpath.py's exact
    witness -- are never killed and never contracted past the equilibrium.
 3. The dependency graph agrees with the symbolic one (symbet on all 48 free).
 4. SEARCH controls: (a) the whole cube must not be proven empty; (b) a box
    around a certified equilibrium must not be proven empty; (c) with the weak
    rules gone, how many of the 81 P1-opening label branches still die at the
    root, against bnb5's 34 -- reported, not asserted, because the numbers are
    allowed to differ (bnb6 proves less, and what it proves is about Nash).
"""
import numpy as np, sys, time
import bnb6, ivl, kuhn3p as K, symbet
import sympy as sp

I = K.NAME_IDX; NAME = K.PARAM_NAME
rng = np.random.default_rng(11)
fails = 0

# ---------------------------------------------------------------- 1. convexity
B = 200
LO = rng.random((B, 48)); HI = rng.random((B, 48)); LO, HI = np.minimum(LO, HI), np.maximum(LO, HI)
worst = 0.0
for rep in range(6):
    v = int(rng.integers(48))
    ts = [0.0, 0.2, 0.5, 0.8, 1.0]
    U = []; L = []
    for t in ts:
        l, u = bnb6._pinned(LO, HI, v, LO[:, v] + t * (HI[:, v] - LO[:, v]))
        U.append(u); L.append(l)
    for k, t in enumerate(ts[1:-1], 1):
        chordU = (1 - t) * U[0] + t * U[-1]; chordL = (1 - t) * L[0] + t * L[-1]
        worst = max(worst, float((U[k] - chordU).max()), float((chordL - L[k]).max()))
print("1. CONVEXITY    worst violation of U<=chord / L>=chord: %.2e   %s" % (worst, "OK" if worst < 1e-12 else "*** FAIL"))
fails += worst >= 1e-12

# ---------------------------------------------------------------- 3. deps
X, syms = [sp.Symbol(NAME[i]) for i in range(48)], None
G, U_ = symbet.build(X)
bad = 0
for i in range(48):
    fs = {int(I[str(s)]) for s in sp.expand(G[i]).free_symbols}
    tree = set(bnb6.DEPS[i].tolist()) - {i}
    if not fs <= tree: bad += 1                     # tree deps may be a superset (sound); never a subset
print("3. DEPENDENCIES symbolic deps contained in tree deps for %d of 48 conditions   %s" % (48 - bad, "OK" if bad == 0 else "*** FAIL"))
fails += bad > 0

# ---------------------------------------------------------------- 2. soundness
EQ = np.load("certified_eq_all.npy")
H = np.load("hunt_eq_bet2.npy")
Z = [I[n] for n in symbet.T2_ZERO]; O = [I[n] for n in symbet.T2_ONE]
t2 = np.maximum(np.abs(H[:, Z]).max(1), np.abs(1 - H[:, O]).max(1))
Hoff = H[t2 > 1e-9][rng.choice((t2 > 1e-9).sum(), 400, replace=False)]
Hon = H[t2 <= 1e-9][rng.choice((t2 <= 1e-9).sum(), 200, replace=False)]
W = np.load("offpath_witness.npy")[None, :]
sets = [("slice certified 744", EQ), ("hunt on-slice 200", Hon), ("hunt OFF-slice 400", Hoff), ("exact off-path witness", W)]
bad_total = 0
for label, XE in sets:
    for w in (1e-3, 1e-2, 0.1, 0.3, 1.0):
        LO = np.clip(XE - w * rng.random(XE.shape), 0, 1)
        HI = np.clip(XE + w * rng.random(XE.shape), 0, 1)
        killed = 0; escaped = 0
        for s in range(0, len(XE), 128):
            lo, hi, x = LO[s:s+128], HI[s:s+128], XE[s:s+128]
            nlo, nhi, al, *_ = bnb6.propagate(lo, hi)
            killed += int((~al).sum())
            esc = al & ((x < nlo - 1e-9) | (x > nhi + 1e-9)).any(axis=1)
            escaped += int(esc.sum())
        bad_total += killed + escaped
        if killed or escaped or w in (1e-3, 1.0):
            print("   %-24s width %.3f : killed %d  escaped %d  of %d" % (label, w, killed, escaped, len(XE)))
print("2. SOUNDNESS    %s" % ("OK -- no certified equilibrium (on or off the slice) killed or excluded" if bad_total == 0 else "*** FAIL"))
fails += bad_total > 0

# ---------------------------------------------------------------- 4. search
t0 = time.time()
v, n, rest = bnb6.search(np.zeros(48), np.ones(48), maxnodes=20000)
print("4a. whole cube   verdict %s after %d nodes (%.0fs)   %s" % (v, n, time.time() - t0, "OK" if v is not True else "*** FAIL: cube proven empty"))
fails += v is True
x = W[0]
lo = np.clip(x - 0.05, 0, 1); hi = np.clip(x + 0.05, 0, 1)
t0 = time.time()
v, n, rest = bnb6.search(lo, hi, maxnodes=20000)
print("4b. box around off-path witness   verdict %s after %d nodes (%.0fs)   %s" % (v, n, time.time() - t0, "OK" if v is not True else "*** FAIL"))
fails += v is True
# 4c: label branches at the root
dead = 0; deadw = 0
labs = []
for a in np.ndindex(3, 3, 3, 3):
    LO = np.zeros((1, 48)); HI = np.ones((1, 48))
    for k, n in enumerate(("a11", "a21", "a31", "a41")):
        if a[k] == 0: HI[0, I[n]] = 0.0
        elif a[k] == 1: LO[0, I[n]] = 1.0
        else: LO[0, I[n]] = 0.5           # 'interior' stand-in: bet at least half the time
    _, _, al, *_ = bnb6.propagate(LO, HI)
    dead += int(not al[0])
print("4c. P1-opening label branches dead at the root (a_j1 in {0, 1, >=1/2}): %d of 81   (bnb5 with weak rules: 34 of 81 for {0,1,interior})" % dead)
print("\nALL CONTROLS %s" % ("PASSED" if not fails else "*** SOME FAILED"))
sys.exit(int(bool(fails)))
