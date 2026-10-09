"""Where are the degeneracies of a float (3,5) equilibrium's interior system?  High-precision
pseudo-inverse Newton (tolerates a singular Jacobian), then the SVD: null COLUMN vectors (free
directions among the interior coordinates) and null ROW vectors (conditions that are combinations of
the others).  usage (from k35/):  KUHN_CARDS=5 python degen35.py ../q2_polish35.json <entry> [digits]"""
import os, sys, json
os.environ.setdefault("KUHN_CARDS", "5")
import mpmath as mp
import cert35check as H
from cert35gen import kgen_to_k35, build
import kuhn3p as K

NP = K.NPARAM

if __name__ == "__main__":
    entry = json.load(open(sys.argv[1]))[int(sys.argv[2])]
    mp.mp.dps = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    p = kgen_to_k35(entry["profile"])
    S = [i for i in range(NP) if 1e-9 < p[i] < 1 - 1e-9]
    pure = {i: (0 if p[i] < 0.5 else 1) for i in range(NP) if i not in S}
    nv = len(S); names = [H.NAME[i] for i in S]
    x = [H.var(S.index(i), nv) if i in S else H.const(pure[i], nv) for i in range(NP)]
    u, D = build(x, nv)
    F = [H.add(H.subst_const(u[H.OWNER[i]], k, 1), H.subst_const(u[H.OWNER[i]], k, 0), -1) for k, i in enumerate(S)]
    J = [[H.diff(f, k) for k in range(nv)] for f in F]
    def ev(poly, pt):
        v = mp.mpf(0)
        for m_, c in poly.items():
            t = mp.mpf(c.numerator) / c.denominator
            for xx, e in zip(pt, m_):
                if e: t *= xx ** e
            v += t
        return v
    y = [mp.mpf(p[i]) for i in S]
    for it in range(40):
        f = [ev(g, y) for g in F]; nf = max(abs(v) for v in f)
        if nf < mp.mpf(10) ** -(mp.mp.dps - 10): break
        Jm = mp.matrix([[ev(J[a][b], y) for b in range(nv)] for a in range(nv)])
        U, Sv, V = mp.svd_r(Jm); tol = Sv[0] * mp.mpf(10) ** -25
        yv = U.T * mp.matrix(f)
        y = [y[k] - sum(V[s, k] * yv[s] / Sv[s] for s in range(nv) if Sv[s] > tol) for k in range(nv)]
    Jm = mp.matrix([[ev(J[a][b], y) for b in range(nv)] for a in range(nv)])
    U, Sv, V = mp.svd_r(Jm)
    print("seed %s: %d interior %s" % (entry.get("seed"), nv, names))
    print("  Newton %d it, max|F| %s; in cube: %s" % (it, mp.nstr(nf, 3), all(0 < v < 1 for v in y)))
    print("  singular values (smallest 4): %s" % [mp.nstr(s, 3) for s in sorted(Sv)[:4]])
    for s in range(nv):
        if Sv[s] < mp.mpf(10) ** -20:
            col = {names[k]: mp.nstr(V[s, k], 4) for k in range(nv) if abs(V[s, k]) > 1e-10}
            row = {names[k]: mp.nstr(U[k, s], 4) for k in range(nv) if abs(U[k, s]) > 1e-10}
            print("  NULL column (free direction): %s" % col)
            print("  NULL row (dependent conditions): %s" % row)
    print("  values: %s" % {n: mp.nstr(v, 8) for n, v in zip(names, y)})
