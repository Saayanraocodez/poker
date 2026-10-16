"""R14 re-read against Theorems 4-5: how far is each MCCFR output from the COMPLETE Nash set?

R14 (followup10.py, cfr_sweep.json) found 99/150 MCCFR outputs in none of the three SGS
sub-families and called that suggestive evidence of equilibria outside the family.  Theorem 5
now gives the complete Nash set as the union of twelve sets S^_l (one per FAMILY leaf).  This
script certifies, for every output p, an EXACT LOWER BOUND on its max-norm distance to that set,
and reports which coordinates force it.

Superset used for leaf l (every constraint holds on S^_l, so distance to the superset is a valid
lower bound on distance to S^_l):
  * the leaf's 0/1 labels (exact values), MIX and DC coordinates in [0, 1];
  * the leaf's LINEAR identities (Groebner basis in nefull_systems.txt; the one bilinear identity,
    leaf 196, is dropped);
  * the leaf's certified coordinate ranges (nefull_certs.json.gz: {S_l, x_v > T} empty);
  * own-unreached coordinates freed as in Theorem 5 (b43, b44 where b41 = 1: leaves 70, 440).

Certificate: weak duality.  For multipliers y (identities), lam, mu >= 0 (lower / upper bounds) put
g = A^T y + lam - mu; every x in the superset has
      g.(x - p) >= N := y.(b - A p) + lam.(l - p) - mu.(u - p),   and   g.(x - p) <= |g|_1 |x - p|_inf,
so |x - p|_inf >= N / |g|_1.  The multipliers come from a float LP (decides nothing); N and |g|_1
are then evaluated in Fractions with p's float entries taken exactly.  dist(p, NE) >= min_l bound_l.

Off path, the outputs are compared with Table 2's pins and with Table 4's windows.

usage:  python reread14.py            -> log_reread14.txt (stdout), reread14.json
"""
import gzip, json, re
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog
import sympy as sp
import kuhn3p as K, symleaf as SL

I = K.NAME_IDX; NAME = K.PARAM_NAME
MIX, DC = 2, 3


def leaves():
    L = np.load("enum6_pat_silentR.npy")
    with np.load("symleaf_silentR.npz") as z: vd = z["verdict"]
    return L, [int(k) for k in np.flatnonzero(vd == SL.VC["FAMILY"])]


def identities():
    """leaf -> list of (row dict name->Fraction, rhs Fraction) for the LINEAR identities."""
    out, cur = {}, None
    syms = {n: sp.Symbol(n) for n in I}
    for line in open("nefull_systems.txt"):
        m = re.match(r"=== leaf (\d+)", line)
        if m: cur = int(m.group(1)); out[cur] = []; continue
        if line.startswith("identities") and cur is not None:
            for s in re.findall(r"'([^']*)'", line):
                e = sp.expand(sp.sympify(s, locals=syms))
                P = sp.Poly(e, *sorted(e.free_symbols, key=str))
                if P.total_degree() > 1: continue           # leaf 196's bilinear identity: dropped
                row = {str(g): F(str(P.coeff_monomial(g))) for g in P.gens}
                rhs = -F(str(P.coeff_monomial(1)))
                out[cur].append((row, rhs))
    return out


def ranges():
    d = json.load(gzip.open("nefull_certs.json.gz", "rt"))
    R = {}
    for k, v in d.items():
        leaf, name, side = k.split(":")
        R[(int(leaf), name, side)] = F(v["T"])
    return R


FREED = {70: ("b43", "b44"), 440: ("b43", "b44")}


def leaf_box(k, lab, R):
    lo = [F(0)] * 48; hi = [F(1)] * 48
    for i in range(48):
        if int(lab[i]) in (0, 1): lo[i] = hi[i] = F(int(lab[i]))
    for i in range(48):
        n = NAME[i]
        if n in FREED.get(k, ()): lo[i], hi[i] = F(0), F(1); continue
        if (k, n, "inf") in R: lo[i] = max(lo[i], R[(k, n, "inf")])
        if (k, n, "sup") in R: hi[i] = min(hi[i], R[(k, n, "sup")])
    return lo, hi


def certify(p, lo, hi, ids):
    """Exact lower bound on min_{x in superset} |x - p|_inf, plus the binding coordinates."""
    n = 48; m = len(ids)
    A = np.zeros((m, n)); b = np.zeros(m)
    for r, (row, rhs) in enumerate(ids):
        for name, c in row.items(): A[r, I[name]] = float(c)
        b[r] = float(rhs)
    lf = np.array([float(v) for v in lo]); hf = np.array([float(v) for v in hi])
    # variables: y (m, free), lam (n), mu (n), gp (n), gm (n):  maximize y.(b-Ap) + lam.(l-p) - mu.(u-p)
    # s.t. A^T y + lam - mu - gp + gm = 0,  sum(gp + gm) <= 1
    nv = m + 4 * n
    c = np.concatenate([-(b - A @ p), -(lf - p), (hf - p), np.zeros(2 * n)])
    Aeq = np.hstack([A.T, np.eye(n), -np.eye(n), -np.eye(n), np.eye(n)])
    Aub = np.concatenate([np.zeros(m + 2 * n), np.ones(2 * n)])[None, :]
    bounds = [(None, None)] * m + [(0, None)] * (4 * n)
    r = linprog(c, A_ub=Aub, b_ub=[1.0], A_eq=Aeq, b_eq=np.zeros(n), bounds=bounds, method="highs")
    z = r.x
    y = [F(v).limit_denominator(10 ** 9) for v in z[:m]]
    lam = [max(F(0), F(v).limit_denominator(10 ** 9)) for v in z[m:m + n]]
    mu = [max(F(0), F(v).limit_denominator(10 ** 9)) for v in z[m + n:m + 2 * n]]
    P = [F(float(v)) for v in p]                      # p's float entries, exactly
    g = [lam[i] - mu[i] for i in range(n)]
    for r_, (row, rhs) in enumerate(ids):
        for name, cc in row.items(): g[I[name]] += y[r_] * cc
    N = sum(y[r_] * (rhs - sum(cc * P[I[name]] for name, cc in row.items())) for r_, (row, rhs) in enumerate(ids))
    N += sum(lam[i] * (lo[i] - P[i]) - mu[i] * (hi[i] - P[i]) for i in range(n))
    g1 = sum(abs(v) for v in g)
    bound = N / g1 if (N > 0 and g1 > 0) else F(0)
    support = [NAME[i] for i in range(n) if g[i] != 0]
    return bound, -r.fun, support


def main():
    d = json.load(open("cfr_sweep.json"))
    P = np.array(d["profiles"]); E = np.array(d["exploitability"]); ex = E.max(axis=1)
    L, fam = leaves(); IDS = identities(); R = ranges()
    sub = {k: ("A" if int(L[k][I["c11"]]) == 0 else ("B" if int(L[k][I["c21"]]) == MIX else "C")) for k in fam}
    boxes = {k: leaf_box(k, L[k], R) for k in fam}
    rows = []
    for s, p in enumerate(P):
        best = None
        per = {}
        for k in fam:
            lo, hi = boxes[k]
            bd, lpv, supp = certify(p, lo, hi, IDS[k])
            per[k] = (bd, lpv, supp)
            if best is None or bd < per[best][0]: best = k
        rows.append(dict(seed=s, expl=float(ex[s]), dist_lb=per[best][0], lp=per[best][1], leaf=best,
                         sub=sub[best], support=per[best][2],
                         by_sub={t: float(min(per[k][0] for k in fam if sub[k] == t)) for t in "ABC"}))
    lb = np.array([float(r["dist_lb"]) for r in rows])
    lpv = np.array([r["lp"] for r in rows])
    print("R14 RE-READ: exact lower bounds on dist_inf(MCCFR output, complete Nash set of Theorem 5)")
    print("150 outputs (cfr_sweep.json: ES-MCCFR, 10^6 iterations each)\n")
    print("certified lower bound vs float LP value: max |diff| = %.2e (rationalised duals lose nothing)"
          % np.abs(lb - lpv).max())
    print("distance lower bound: min %.4f  median %.4f  mean %.4f  max %.4f" % (lb.min(), np.median(lb), lb.mean(), lb.max()))
    for t in (0.005, 0.01, 0.02, 0.05, 0.1):
        print("   outputs certified at distance > %.3f: %3d / 150" % (t, (lb > t).sum()))
    print("exploitability (max over players): median %.5f;  ratio dist_lb / expl: median %.1f, min %.1f"
          % (np.median(ex), np.median(lb / ex), (lb / ex).min()))
    print("correlation(dist_lb, expl) = %+.3f" % np.corrcoef(lb, ex)[0, 1])
    print("\nnearest sub-family (by certified bound): " + "  ".join("%s %d" % (t, sum(r["sub"] == t for r in rows)) for t in "ABC"))
    from collections import Counter
    cnt = Counter(c for r in rows for c in r["support"])
    print("coordinates carrying the certificate (how often in 150):")
    print("   " + "  ".join("%s %d" % kv for kv in cnt.most_common(16)))

    # ---- old classification, for the record
    def subfam(p):
        b11, b21, c11 = p[I["b11"]], p[I["b21"]], p[I["c11"]]
        if c11 < 0.02 and b11 <= b21 + 0.02: return "A"
        if 0.02 <= c11 <= 0.48 and abs(b21 - b11) <= 0.02: return "B"
        if c11 > 0.48 and b21 <= min(b11, 0.5 - 2 * b11) + 0.02: return "C"
        return "none"
    old = [subfam(p) for p in P]
    none = np.array([o == "none" for o in old])
    print("\nR14's 'in none of the three' (tolerance 0.02): %d / 150" % none.sum())
    print("   their certified distance: median %.4f, min %.4f;  the other %d: median %.4f"
          % (np.median(lb[none]), lb[none].min(), (~none).sum(), np.median(lb[~none])))

    # ---- off path: Table 2 pins vs Table 4 windows
    T2 = {"b12": 0, "b22": 0, "c13": 0, "c23": 0, "b42": 1, "c43": 1, "b44": 1, "c44": 1, "a44": 1,
          "a14": 0, "a24": 0, "c14": 0, "c24": 0, "a13": 0, "a23": 0, "a43": 1, "c12": 0, "c22": 0, "c42": 1}
    U = {}
    for line in open("nefull_ranges.txt").read().split("=== union")[1].splitlines()[1:]:
        m = re.match(r"\s+(\w+)\s+\[(\S+), (\S+)\]", line)
        if m: U[m.group(1)] = (float(F(m.group(2))), float(F(m.group(3))))
    print("\nOFF PATH (P1 never bets, so P2's/P3's answers to a bet are unreached):")
    print("   coord  Table2  Table4 window      MCCFR median   max |p - Table2|   outside Table4 (by > 0.02)")
    for n, v in T2.items():
        col = P[:, I[n]]; w = U.get(n, (0.0, 1.0))
        out4 = ((col < w[0] - 0.02) | (col > w[1] + 0.02)).sum()
        print("   %-5s  %5d   [%.4f, %.4f]   %10.4f   %10.4f          %3d" % (n, v, w[0], w[1], np.median(col), np.abs(col - v).max(), out4))
    json.dump([{**r, "dist_lb": str(r["dist_lb"])} for r in rows], open("reread14.json", "w"), indent=0)
    print("\n[reread14.json written]")


if __name__ == "__main__":
    main()
