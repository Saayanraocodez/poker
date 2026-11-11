"""T3: independent stress test of Theorem 5 / Table 4 (the off-path windows).

For each of the 12 FAMILY leaves (family_leaves.json: label vectors keyed by the leaf ids used in
nefull_ranges.txt / seq_<leaf>.json, re-derived by an independent run of enuml.py), maximise and
minimise every free coordinate over the leaf's system
    { D_i = 0 on MIX, D_i <= 0 on label 0, D_i >= 0 on label 1, the pair on DC }
with SLSQP.  Variables: the on-path family parameters the leaf's pattern allows plus the DC
coordinates; a point counts only if the FULL D-condition of the leaf holds at it (1e-9), with MIX
coordinates strictly interior.  The best value found is compared with the certified bound:
   beyond the bound  -> a counterexample to Table 4 (written to windows_report.json);
   equal             -> the bound is tight;   short of it -> the certified bound may be slack.
Result of 2026-11-11 (4 starts): 459 bounds reached, 63 not reached, 0 beyond.  Largest candidates
for sharpening Table 4: sup b12 = 5/12, sup b22 = 7/12, sup c13 ~ 0.526219, inf b42 = inf c43 ~ 0.775800.
NOTE the leaves are open in their MIX coordinates: b44 (free where b41 = 1) is not covered here,
see check_34.py section 4.

usage: python makeD.py ; python independent_check/windows_test.py [starts]     (1-3 minutes; default 4 starts)
"""
import os, sys, re, json, time
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')    # tiny matrices: threads only hurt
import numpy as np
from fractions import Fraction as F
from scipy.optimize import minimize
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fastd, indep as I

MIX, DC = 2, 3
NAMES = I.NAMES; IX = {n: i for i, n in enumerate(NAMES)}
_LV = json.load(open(os.path.join(HERE, 'family_leaves.json')))
LEAFID = sorted(int(k) for k in _LV)
L = np.array([_LV[str(k)] for k in LEAFID])
NST = int(sys.argv[1]) if len(sys.argv) > 1 else 4
rng = np.random.default_rng(0)

# ---- the twelve on-path patterns, each with representative family points (floats)
def fam(b11, b21, b23, c11, b32=0.0, c33=None, c34=0.0):
    beta = max(b11, b21); w = .75 * (b11 + b21) + beta / 4
    if c33 is None: c33 = min(1.0, max(0.0, .5 - b32 + w / 2))
    p = I.family(F(b11), F(b21), F(b23), F(b32), F(c11), F(c33), F(c34))
    return np.array([float(p[n]) for n in NAMES])

PAT = {
 'A0  b11=b21=0':            lambda: fam(0, 0, 0, 0),
 'A   b11=0<b21':            lambda: fam(0, rng.uniform(.02, .24), 0, 0),
 'A   0<b11<=b21<1/4':       lambda: (lambda b21: fam(rng.uniform(.01, b21), b21, 0, 0))(rng.uniform(.03, .24)),
 'A   b11=b21=1/4':          lambda: fam(.25, .25, 0, 0),
 'B0  b11=b21=0':            lambda: fam(0, 0, 0, rng.uniform(.05, .45)),
 'B   0<b11=b21<1/4':        lambda: (lambda b: fam(b, b, 0, rng.uniform(.05, min(.45, (2 - b) / (3 + 4 * b) - .02))))(rng.uniform(.02, .24)),
 'B   b11=b21=1/4':          lambda: fam(.25, .25, 0, rng.uniform(.05, .43)),
 'C0  b11=b21=0':            lambda: fam(0, 0, 0, .5),
 'C   b11>0,b21=0,b23=0':    lambda: fam(rng.uniform(.02, .25), 0, 0, .5),
 'C   b11>0,b21=0,b23>0':    lambda: (lambda b: fam(b, 0, rng.uniform(.2, 1) * b / 2, .5))(rng.uniform(.02, .25)),
 'C   b11,b21>0,b23=0':      lambda: (lambda b: fam(b, rng.uniform(.2, 1) * min(b, .5 - 2 * b), 0, .5))(rng.uniform(.02, .24)),
 'C   b11,b21>0,b23>0':      lambda: (lambda b: (lambda b21: fam(b, b21, rng.uniform(.2, .9) * (b - b21) / (2 * (1 - b21)), .5))(rng.uniform(.2, .8) * min(b, .5 - 2 * b)))(rng.uniform(.04, .24)),
}

def matches(lab, x):
    for i in range(48):
        if lab[i] == 0 and x[i] != 0: return False
        if lab[i] == 1 and x[i] != 1: return False
        if lab[i] == MIX and not (0 < x[i] < 1): return False
    return True

leaf_of = {}
for name, gen in PAT.items():
    hits = set()
    for _ in range(5):
        x = gen()
        hits.add(tuple(k for k in range(len(L)) if matches(L[k], x)))
    assert len(hits) == 1, (name, hits)
    ks = hits.pop()
    assert len(ks) == 1, (name, ks)
    leaf_of[name] = ks[0]
assert len(set(leaf_of.values())) == 12
print("12 on-path patterns <-> the 12 FAMILY leaves:", {n.split()[0] + ':' + str(LEAFID[k]) for n, k in leaf_of.items()})
# every other leaf: no family point (sanity only; their emptiness is the certificates' job)

# ---- certified windows from the repo, keyed by the leaf's MIX set
cert = {}
cur = None
for line in open(os.path.join(ROOT, 'nefull_ranges.txt')):
    t = line.split()
    if len(t) < 6 or not t[0].isdigit(): continue
    cert.setdefault(int(t[0]), {})[t[2]] = (t[3], t[4], t[5])
def num(s): return float(F(s)) if '/' in s else float(s)
def mixset(rows): return frozenset(n for n, (lab, lo, hi) in rows.items() if lab == 'MIX')

# ---- optimisation: variables = on-path family parameters theta (as the pattern allows) + the DC coordinates;
# MIX / pinned coordinates come from Table 3's formulas, so there are no equality constraints.  The result is
# accepted only if the FULL D-condition of the leaf holds at it (violation()), so nothing is assumed.
THETA = {
 'A0  b11=b21=0': [], 'A   b11=0<b21': ['b21'], 'A   0<b11<=b21<1/4': ['b11', 'b21'], 'A   b11=b21=1/4': [],
 'B0  b11=b21=0': ['c11'], 'B   0<b11=b21<1/4': ['b', 'c11'], 'B   b11=b21=1/4': ['c11'],
 'C0  b11=b21=0': [], 'C   b11>0,b21=0,b23=0': ['b11'], 'C   b11>0,b21=0,b23>0': ['b11', 'b23'],
 'C   b11,b21>0,b23=0': ['b11', 'b21'], 'C   b11,b21>0,b23>0': ['b11', 'b21', 'b23'],
}
FIX = {
 'A0  b11=b21=0': dict(b11=0, b21=0, b23=0, c11=0), 'A   b11=0<b21': dict(b11=0, b23=0, c11=0), 'A   0<b11<=b21<1/4': dict(b23=0, c11=0),
 'A   b11=b21=1/4': dict(b11=.25, b21=.25, b23=0, c11=0),
 'B0  b11=b21=0': dict(b11=0, b21=0, b23=0), 'B   0<b11=b21<1/4': dict(b23=0), 'B   b11=b21=1/4': dict(b11=.25, b21=.25, b23=0),
 'C0  b11=b21=0': dict(b11=0, b21=0, b23=0, c11=.5), 'C   b11>0,b21=0,b23=0': dict(b21=0, b23=0, c11=.5), 'C   b11>0,b21=0,b23>0': dict(b21=0, c11=.5),
 'C   b11,b21>0,b23=0': dict(b23=0, c11=.5), 'C   b11,b21>0,b23>0': dict(c11=.5),
}
ONPATH = ['a33', 'b11', 'b21', 'b23', 'b33', 'b41', 'c11', 'c21']

def build(name, lab, dcv, z):
    th = dict(FIX[name]); nt = len(THETA[name])
    for nm, val in zip(THETA[name], z[:nt]):
        if nm == 'b': th['b11'] = th['b21'] = val
        else: th[nm] = val
    b11, b21, b23, c11 = th['b11'], th['b21'], th['b23'], th['c11']
    beta = max(b11, b21)
    x = np.array([1.0 if lab[i] == 1 else 0.0 for i in range(48)])
    vals = dict(a33=.5, b11=b11, b21=b21, b23=b23, b33=.5 + (b11 + b21) / 2 + beta / 2 - b23 * (1 - b21), b41=2 * b11 + 2 * b21, c11=c11, c21=.5 - c11)
    for nm in ONPATH:
        if lab[IX[nm]] == MIX: x[IX[nm]] = vals[nm]
    x[dcv] = z[nt:]
    return x

def theta_of(name, x):
    out = []
    for nm in THETA[name]:
        out.append(x[IX['b11']] if nm == 'b' else x[IX[nm]])
    return out

def solve2(name, lab, v, sign, x0, live):
    dcv = [i for i in range(48) if lab[i] == DC]
    nt = len(THETA[name])
    z0 = np.array(theta_of(name, x0) + [x0[i] for i in dcv])
    le = [i for i in range(48) if lab[i] == 0 and live[i]]; ge = [i for i in range(48) if lab[i] == 1 and live[i]]
    dcl = [i for i in dcv if live[i]]
    S = 24.0
    def cons(z):
        x = build(name, lab, dcv, z); d = S * fastd.D(x)
        out = [-d[le], d[ge]]
        if dcl: out += [x[dcl] * d[dcl], -(1 - x[dcl]) * d[dcl]]
        return np.concatenate(out)
    bnds = [((1e-6, 0.5 - 1e-6) if nm == 'c11' else (1e-6, 0.25 - 1e-6)) for nm in THETA[name]] + [(0.0, 1.0)] * len(dcv)
    if v in dcv: jv = nt + dcv.index(v); obj = lambda z: -sign * z[jv]
    else: obj = lambda z: -sign * build(name, lab, dcv, z)[v]
    r = minimize(obj, z0, method='SLSQP', bounds=bnds, constraints=[{'type': 'ineq', 'fun': cons}], options={'maxiter': 400, 'ftol': 1e-14})
    return build(name, lab, dcv, np.clip(r.x, [b[0] for b in bnds], [b[1] for b in bnds]))

def violation(lab, x):
    d = 24 * fastd.D(x); v = 0.0
    for i in range(48):
        if lab[i] == MIX: v = max(v, abs(d[i]), 1e-7 - x[i], x[i] - 1 + 1e-7)
        elif lab[i] == 0: v = max(v, d[i])
        elif lab[i] == 1: v = max(v, -d[i])
        else: v = max(v, -x[i] * d[i], (1 - x[i]) * d[i])
    return v

t0 = time.time()
report = []; worst = None; tot = [0, 0, 0]
detail = {}
for name, k in leaf_of.items():
    lab = L[k]
    free = [i for i in range(48) if lab[i] in (MIX, DC)]
    base = np.array([1.0 if lab[i] == 1 else 0.0 for i in range(48)])
    probe = []
    for _ in range(40):
        x = base.copy(); x[free] = rng.random(len(free)); probe.append(fastd.D(x))
    live = np.abs(np.array(probe)).max(axis=0) > 1e-14
    ref = [LEAFID[k]]
    assert mixset(cert[ref[0]]) == frozenset(NAMES[i] for i in range(48) if lab[i] == MIX), name
    rows = cert[ref[0]]
    starts = [PAT[name]() for _ in range(NST)]
    for s_ in list(starts):
        for rep in range(2):
            x = s_.copy()
            for i in free:
                if lab[i] == DC and rng.random() < .6: x[i] = rng.random()
            starts.append(x)
    nbeyond = ntight = nloose = ncoord = 0
    for cname, (clab, slo, shi) in rows.items():
        v = IX[cname]
        if v not in free: continue
        ncoord += 1
        for sign, bound, bs in ((+1, num(shi), shi), (-1, num(slo), slo)):
            best = None
            for x0 in starts:
                try: x = solve2(name, lab, v, sign, x0, live)
                except Exception as ex: continue
                if violation(lab, x) < 1e-9 and (best is None or sign * x[v] > sign * best[v]): best = x
            if best is None: nloose += 1; continue
            gap = sign * (best[v] - bound)
            tol = 2e-6 if '.' in bs else 1e-7
            detail[(ref[0], cname, 'sup' if sign > 0 else 'inf')] = (float(best[v]), bound)
            if gap > tol: nbeyond += 1; report.append((name, cname, sign, float(best[v]), bound, best.tolist()))
            elif gap > -1e-4: ntight += 1
            else:
                nloose += 1
                if worst is None or -gap > worst[0]: worst = (float(-gap), name, cname, sign, float(best[v]), bound)
    tot[0] += ntight; tot[1] += nloose; tot[2] += nbeyond
    print("%-26s leaf %3d  coords %2d  bounds reached %3d  not reached %2d  BEYOND %d   %.0fs" % (name, ref[0], ncoord, ntight, nloose, nbeyond, time.time() - t0), flush=True)
print("totals: reached %d, not reached %d, beyond %d" % tuple(tot))
print("largest shortfall (search did not reach the certified bound):", worst)
print("not reached:", sorted((k, round(a, 5), b) for k, (a, b) in detail.items() if abs(a - b) > 1e-4))
json.dump(dict(beyond=report, best={'%d %s %s' % k: v for k, v in detail.items()}), open(os.path.join(HERE, 'windows_report.json'), 'w'), indent=0)
