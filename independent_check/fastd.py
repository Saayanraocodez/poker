"""Fast float evaluation of the 48 own-reach-stripped gradients D_i and their Jacobian, from the
polynomial form in ../D_all.pkl (python makeD.py).  On import the polynomials are checked EXACTLY
against the independent engine (indep.D_all) at random rational profiles."""
import os, pickle, random
from fractions import Fraction as F
import numpy as np
import indep as I

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DP = pickle.load(open(os.path.join(ROOT, 'D_all.pkl'), 'rb'))
NV = 48
_rng = random.Random(0)
for _ in range(5):
    _v = [F(_rng.randint(0, 30), 30) for _ in range(NV)]
    _D, _ = I.D_all(I.from_vec(_v))
    for _i, _nm in enumerate(I.NAMES):
        _t = F(0)
        for _m, _c in DP[_i].items():
            _w = F(_c)
            for _j, _e in enumerate(_m):
                if _e: _w *= _v[_j] ** _e
            _t += _w
        assert _t == _D[_nm], "D_all.pkl disagrees with the independent engine at " + _nm
_terms = []          # (row i, coef, [vars])
for i in range(NV):
    for m, c in DP[i].items():
        vs = []
        for j, e in enumerate(m):
            assert e in (0, 1)                      # multilinear
            if e: vs.append(j)
        _terms.append((i, float(c), vs))
MAXD = max(len(t[2]) for t in _terms)
ROW = np.array([t[0] for t in _terms])
COEF = np.array([t[1] for t in _terms])
IDX = np.full((len(_terms), MAXD), NV, dtype=np.int64)      # pad with index NV -> value 1
for k, t in enumerate(_terms):
    IDX[k, :len(t[2])] = t[2]


def D(x):
    q = np.append(x, 1.0)
    vals = COEF * q[IDX].prod(axis=1)
    return np.bincount(ROW, weights=vals, minlength=NV)


def DJ(x):
    """D (48,) and Jacobian dD_i/dx_j (48,48)."""
    q = np.append(x, 1.0)
    f = q[IDX]                                    # (T, MAXD)
    J = np.zeros((NV, NV + 1))
    tot = f.prod(axis=1)
    for k in range(MAXD):
        others = np.ones(len(COEF))
        for kk in range(MAXD):
            if kk != k: others = others * f[:, kk]
        np.add.at(J, (ROW, IDX[:, k]), COEF * others)
    return np.bincount(ROW, weights=COEF * tot, minlength=NV), J[:, :NV]
