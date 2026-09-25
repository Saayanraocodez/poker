"""THE FULL NASH SET, off path included: exact ranges of every coordinate over
each of the 12 FAMILY leaves of the silent branch (and over their union).

A FAMILY leaf's system (symleaf._sys with the leaf's labels: D_i = 0 on MIX,
sign conditions on 0/1, the pair on DC, private DC dropped) is, by Lemma 1,
exactly the set of profiles in that label cell that satisfy the D-condition
everywhere; the union over the 12 leaves, with own-unreached coordinates
freed, is the complete Nash set (PAPER_KIT Theorem 5).  This script makes
the set explicit:

  * for each leaf: the system in reduced form (Groebner normal forms of the
    0/1 sign conditions -- the deterrence inequalities that bound the
    off-path coordinates), written to nefull_systems.txt;
  * for each leaf and coordinate x_v (MIX or constrained DC): inf and sup
    over the leaf, each as an EMPTINESS CERTIFICATE ({leaf system, x_v > T}
    has no point: certbox, checked by checknefull.py) plus an exact rational
    WITNESS point of the leaf with x_v = T where the bound is attained
    (verified by exact evaluation of every constraint), or the statement
    that the bound is not attained ({x_v >= T} empty as well).
    Written to nefull_ranges.txt and nefull_certs.json.gz.

usage:  python nefull.py [workers]      (KUHN_RANGE_BUDGET: B&B nodes per certificate, default 40)
"""
import numpy as np, sys, time, json, gzip, os
import sympy as sp
from fractions import Fraction as F
import kuhn3p as K, symleaf as SL, certbox
from scipy.optimize import minimize

NAME = K.PARAM_NAME; I = K.NAME_IDX
U, MIX, DC = 9, 2, 3


def leaf_system(lab):
    X, syms, G = SL.build(lab)
    mixv = [i for i in range(48) if lab[i] == MIX]; dcv = [i for i in range(48) if lab[i] == DC]
    polys, kinds = SL._sys(lab, G, mixv, X)
    orig = [("D", int(i)) for i in mixv if G[i] != 0]
    for i in range(48):
        if lab[i] == 0 and G[i] != 0: orig.append(("0", int(i)))
        if lab[i] == 1 and G[i] != 0: orig.append(("1", int(i)))
        if lab[i] == DC and G[i] != 0: orig.append(("DCx", int(i))); orig.append(("DC1", int(i)))
    others = {}
    for p, k in zip(polys, kinds):
        for g in p.free_symbols: others[g] = others.get(g, 0) + 1
    priv = []
    for i in dcv:
        v = syms[i]
        own = sum(1 for p, k in zip(polys, kinds) if p.has(v) and (p == sp.expand(X[i] * G[i]) or p == sp.expand(-(1 - X[i]) * G[i])))
        if others.get(v, 0) == own: priv.append(i)
    keep = [not any(p.has(syms[i]) for i in priv) for p in polys]
    polys = [p for p, kp in zip(polys, keep) if kp]; kinds = [k for k, kp in zip(kinds, keep) if kp]; orig = [o for o, kp in zip(orig, keep) if kp]
    dcv = [i for i in dcv if i not in priv]
    gens = [syms[i] for i in mixv + dcv]
    return X, syms, G, mixv, dcv, priv, gens, polys, kinds, orig


def exact_eval(polys, kinds, gens, vals):
    sub = {g: sp.Rational(v.numerator, v.denominator) for g, v in vals.items()}
    for p, k in zip(polys, kinds):
        r = sp.Rational(sp.expand(p.subs(sub)))
        if k == "=" and r != 0: return False
        if k == ">=" and r < 0: return False
        if k == ">" and r <= 0: return False
    return True


def numeric_extreme(polys, kinds, gens, v, sign, x0s):
    fs = [sp.lambdify(gens, p, "numpy") for p in polys]
    n = len(gens); best = None
    cons = [{"type": "eq" if k == "=" else "ineq", "fun": (lambda f: lambda x: float(f(*x)))(f)} for f, k in zip(fs, kinds)]
    for x0 in x0s:
        try:
            r = minimize(lambda x: -sign * x[v], np.array(x0, float), method="SLSQP", bounds=[(0.0, 1.0)] * n, constraints=cons, options={"maxiter": 300, "ftol": 1e-12})
        except Exception:
            continue
        viol = max([abs(float(f(*r.x))) for f, k in zip(fs, kinds) if k == "="] + [max(0.0, -float(f(*r.x))) for f, k in zip(fs, kinds) if k != "="] + [0.0])
        if viol < 1e-8 and (best is None or sign * r.x[v] > sign * best[v]): best = r.x.copy()
    return best


def snap_witness(polys, kinds, gens, x, v, T, mixmask):
    for den in (2, 4, 8, 16, 32, 64, 128, 256, 1024, 4096, 10**4, 10**6):
        vals = {}
        for t, g in enumerate(gens):
            q = F(T) if t == v else F(float(x[t])).limit_denominator(den)
            vals[g] = min(F(1), max(F(0), q))
        if all((0 < vals[g] < 1) for t, g in enumerate(gens) if mixmask[t]) and exact_eval(polys, kinds, gens, vals):
            return vals
    return None


_CACHE = {}
def _leaf(k):
    if k not in _CACHE:
        L = np.load("enum6_pat_silentR.npy"); lab = L[k]
        W = np.concatenate([np.load("certified_eq_all.npy"), np.load("hunt_eq_bet2.npy")])
        X, syms, G, mixv, dcv, priv, gens, polys, kinds, orig = leaf_system(lab)
        gidx = mixv + dcv; mixmask = [g in [syms[i] for i in mixv] for g in gens]
        ok = np.ones(len(W), bool)
        for i in range(48):
            if lab[i] == 0: ok &= W[:, i] <= 1e-9
            elif lab[i] == 1: ok &= W[:, i] >= 1 - 1e-9
            elif lab[i] == MIX: ok &= (W[:, i] >= 1e-6) & (W[:, i] <= 1 - 1e-6)
        pts = W[ok][:, gidx]
        rng = np.random.default_rng(0)
        starts = [pts[j] for j in rng.choice(len(pts), min(6, len(pts)), replace=False)] if len(pts) else [np.full(len(gens), 0.5)]
        _CACHE[k] = (lab, X, syms, G, mixv, dcv, priv, gens, polys, kinds, orig, gidx, mixmask, pts, starts)
    return _CACHE[k]


def leaf_text(k):
    lab, X, syms, G, mixv, dcv, priv, gens, polys, kinds, orig, gidx, mixmask, pts, starts = _leaf(k)
    sub = "A" if lab[I["c11"]] == 0 else ("B" if lab[I["c21"]] == MIX else "C")
    E = [G[i] for i in mixv if G[i] != 0]
    gb = sp.groebner(E, *gens, order="grevlex") if E else None
    txt = ["\n=== leaf %d  sub-family %s ===\nMIX (parameters): %s\nconstrained DC (off path): %s\nfree (private, D = 0): %s\n" % (k, sub, [NAME[i] for i in mixv], [NAME[i] for i in dcv], [NAME[i] for i in priv])]
    if gb: txt.append("identities (Groebner basis): %s\n" % [str(g) for g in gb.exprs])
    txt.append("inequalities (normal forms; D of a 0-label <= 0, of a 1-label >= 0; DC pairs x D >= 0 >= (1-x) D):\n")
    for p, kd, og in zip(polys, kinds, orig):
        if kd == "=": continue
        r = sp.factor(sp.expand(gb.reduce(p)[1])) if gb else sp.factor(p)
        if r == 0 or (r.is_number and r >= 0): continue
        txt.append("   %-4s %-4s %s %s 0\n" % (og[0], NAME[og[1]], r, kd))
    return sub, len(gens), "".join(txt)


def range_task(a):
    """(leaf k, gen index t, sign) -> (k, t, sign, T, attained, cert, witness)"""
    k, t, sign = a
    lab, X, syms, G, mixv, dcv, priv, gens, polys, kinds, orig, gidx, mixmask, pts, starts = _leaf(k)
    g = gens[t]; bounds = SL._bounds(lab, mixv, dcv)
    budget = int(os.environ.get("KUHN_RANGE_BUDGET", "40"))
    xbest = numeric_extreme(polys, kinds, gens, t, sign, starts)
    # the best known equilibrium point is a lower bound on sup (upper on inf); SLSQP may stop at a local optimum
    guess = float(xbest[t]) if xbest is not None else 0.5
    if len(pts):
        ext = float(pts[:, t].max() if sign > 0 else pts[:, t].min())
        if sign * ext > sign * guess:
            guess = ext; xbest = pts[np.argmax(pts[:, t]) if sign > 0 else np.argmin(pts[:, t])]
    def empty_beyond(Tq, strict, full=True):
        Tr = sp.Rational(Tq.numerator, Tq.denominator)
        side = g - Tr if sign > 0 else Tr - g
        # cheapest first: root LP, a short LP-only B&B, then (full only) a short B&B with the chord contractor
        ladder = ((1, False), (max(4, budget // 4), False)) + (((budget, True),) if full else ())
        for bud, chord in ladder:
            r = certbox.prove_empty_cert(polys + [side], kinds + [">" if strict else ">="], gens, bounds, bud, origins=orig + [("side",)], lab=[int(v) for v in lab], gidx=gidx, chord=chord, exact_dual=chord)
            if r[0]:
                r[1]["gens"] = gidx; return r[1]
        return None
    # outward search with LP-only certificates in coarse then fine steps
    T = F(guess).limit_denominator(100); cert = None
    for step, n in ((F(1, 20), 20), (F(1, 100), 5)):
        Tc = T
        for _ in range(n):
            c = empty_beyond(Tc, True, full=False)
            if c is not None: cert = c; T = Tc; break
            Tc = min(F(1), max(F(0), Tc + step * (1 if sign > 0 else -1)))
        if cert is not None: break
        T = Tc
    if cert is None:
        cert = empty_beyond(T, True, full=True)
    if cert is None: return (k, t, sign, None, None, None, None)
    certified = T; other = F(guess).limit_denominator(10**6)
    for _ in range(12):
        if abs(certified - other) <= F(1, 10**3): break
        mid = F((certified + other) / 2).limit_denominator(10**6)
        c2 = empty_beyond(mid, True)
        if c2 is not None: certified = mid; cert = c2
        else: other = mid
    # snap to a small-denominator rational when that certifies too
    for den in (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 48, 64, 96, 100):
        cand = F(round(float(certified) * den), den)
        if (sign > 0 and other <= cand <= certified) or (sign < 0 and certified <= cand <= other):
            c3 = empty_beyond(cand, True)
            if c3 is not None: certified = cand; cert = c3; break
    T = certified
    wit = snap_witness(polys, kinds, gens, xbest if xbest is not None else np.full(len(gens), 0.5), t, T, mixmask)
    attained = wit is not None
    if not attained:
        c4 = empty_beyond(T, False)
        attained = None if c4 is None else False
    return (k, t, sign, T, attained, cert, None if wit is None else {str(gg): certbox.fstr(q) for gg, q in wit.items()})


def main(nw=8):
    from multiprocessing import Pool
    t0 = time.time()
    L = np.load("enum6_pat_silentR.npy")
    with np.load("symleaf_silentR.npz") as z: vd = z["verdict"]
    fam = [int(k) for k in np.flatnonzero(vd == SL.VC["FAMILY"])]
    info = {k: leaf_text(k) for k in fam}
    with open("nefull_systems.txt", "w") as f:
        for k in fam: f.write(info[k][2])
    tasks = [(k, t, sgn) for k in fam for t in range(info[k][1]) for sgn in (1, -1)]
    print("%d leaves, %d range tasks" % (len(fam), len(tasks)), flush=True)
    res = {}; certs = {}; done = 0
    with Pool(nw) as pool:
        for (k, t, sign, T, att, cert, wit) in pool.imap_unordered(range_task, tasks, chunksize=1):
            res[(k, t, sign)] = (T, att); done += 1
            if cert is not None:
                name = NAME[_leaf(k)[11][t]]
                certs["%d:%s:%s" % (k, name, "sup" if sign > 0 else "inf")] = {"T": certbox.fstr(T), "sign": sign, "attained": att, "cert": cert, "witness": wit}
            if done % 25 == 0: print("   %d/%d tasks  %.0fs" % (done, len(tasks), time.time() - t0), flush=True)
    fmt = lambda T: "?" if T is None else ("%s" % T if T.denominator <= 100 else "%.6f" % float(T))
    glob = {}
    with open("nefull_ranges.txt", "w") as f:
        f.write("leaf sub  coord label     inf            sup      attained(inf,sup)\n")
        for k in fam:
            lab, X, syms, G, mixv, dcv, priv, gens, polys, kinds, orig, gidx, mixmask, pts, starts = _leaf(k)
            for t in range(len(gens)):
                name = NAME[gidx[t]]; lbl = "MIX" if mixmask[t] else "DC"
                Ti, ai = res[(k, t, -1)]; Ts, as_ = res[(k, t, 1)]
                f.write("%4d  %s   %-4s %-4s  %12s   %12s      %-5s %-5s\n" % (k, info[k][0], name, lbl, fmt(Ti), fmt(Ts), ai, as_))
                if Ti is not None and Ts is not None:
                    g0 = glob.get(name, (Ti, Ts)); glob[name] = (min(g0[0], Ti), max(g0[1], Ts))
        f.write("\n=== union over the 12 leaves (coordinates that are MIX or constrained DC somewhere) ===\n")
        for name in sorted(glob, key=lambda n: I[n]):
            lo_, hi_ = glob[name]; f.write("   %-4s  [%s, %s]\n" % (name, fmt(lo_), fmt(hi_)))
    with gzip.open("nefull_certs.json.gz", "wt") as f: json.dump(certs, f)
    print("done -> nefull_systems.txt, nefull_ranges.txt, nefull_certs.json.gz  %.0fs" % (time.time() - t0))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8)
