"""R14 re-read, part 2: UPPER bounds on dist_inf(MCCFR output, complete Nash set), by exact witnesses.

For each output p and each FAMILY leaf l, SLSQP (float, decides nothing) minimises |x - p|_inf over
the leaf system S_l (nefull.leaf_system), keeping every inequality >= 1e-9 so the point can be
snapped.  The point is then made EXACT: free coordinates rounded to rationals, the leaf's
identities solved exactly for their dependent coordinates, every constraint of S_l re-evaluated in
exact arithmetic (nefull.exact_eval), and the profile re-checked as a Nash equilibrium from scratch
by exact best-response enumeration (xnash below: Fractions only, kuhn3p's leaf table).  The upper
bound is the exact |x - p|_inf.  Together with reread14.py's certified lower bound this brackets
the distance.

usage:  python reread14b.py [workers]   -> log_reread14b.txt (stdout), reread14b.json
"""
import json, sys, itertools
from fractions import Fraction as F
import numpy as np
import sympy as sp
from multiprocessing import Pool
from scipy.optimize import minimize
import kuhn3p as K, nefull as NF
from reread14 import leaves

I = K.NAME_IDX; NAME = K.PARAM_NAME
MIX, DC = 2, 3


def xnash(x):
    """exact: max over players of (best-response value - value); 0 iff Nash."""
    u = K.utilities_exact(x)
    gap = F(0)
    for pl in range(3):
        tot = F(0)
        for j in K.CARDS:
            own = [K.pidx(pl, j, k) for k in K.SITUATIONS]
            best = None
            for bits in itertools.product((0, 1), repeat=4):
                y = list(x)
                for i, v in zip(own, bits): y[i] = F(v)
                # value of the card-j part: utilities restricted to deals where pl holds j
                val = _card_value(y, pl, j)
                best = val if best is None or val > best else best
            tot += best
        gap = max(gap, tot - u[pl])
    return gap


def _card_value(y, pl, j):
    q = list(y) + [F(1)]
    sub_idx, sub_agg, sub_pay = K._SUB[(pl, j)]
    tot = F(0)
    for r in range(len(sub_idx)):
        w = F(1)
        for k in range(sub_idx.shape[1]):
            i = int(sub_idx[r, k]); w *= q[i] if sub_agg[r, k] else 1 - q[i]
            if w == 0: break
        if w: tot += w * int(sub_pay[r, pl])
    return K.KAPPA_F * tot


_LEAF = {}
def leaf(k):
    if k not in _LEAF:
        L, _ = leaves(); lab = L[k]
        X, syms, G, mixv, dcv, priv, gens, polys, kinds, orig = NF.leaf_system(lab)
        fs = [sp.lambdify(gens, p, "numpy") for p in polys]
        ids = [p for p, kd in zip(polys, kinds) if kd == "="]
        # exact solver for the identities: Groebner basis, then solve for one linear variable each
        gb = list(sp.groebner(ids, *gens, order="lex").exprs) if ids else []
        _LEAF[k] = (lab, gens, polys, kinds, fs, gb, mixv, dcv, priv, syms)
    return _LEAF[k]


def reduced(k):
    """the leaf system with its identities solved: dependent coordinates as expressions in the free ones."""
    lab, gens, polys, kinds, fs, gb, mixv, dcv, priv, syms = leaf(k)
    dep = {}
    lead = []
    for e in gb:
        lm = sp.Poly(e, *gens).monoms(order="lex")[0]
        lead.append([g for g, d in zip(gens, lm) if d])
    taken = {g for L in lead if len(L) == 1 for g in L}
    for e, L in zip(gb, lead):
        if len(L) == 1 and sp.Poly(e, L[0]).degree() == 1:
            dep[L[0]] = sp.solve(e, L[0])[0]; continue
        for g in sorted(e.free_symbols, key=str):            # nonlinear leading term: solve for a linear, unused variable
            if g not in taken and sp.Poly(e, g).degree() == 1 and sp.Poly(e, g).coeffs()[0].is_number:
                dep[g] = sp.solve(e, g)[0]; taken.add(g); break
        else:
            raise ValueError(("cannot solve identity", k, e))
    free = [g for g in gens if g not in dep]
    # dependent expressions may involve other dependent variables: substitute to a fixed point
    for _ in range(len(dep) + 1):
        dep = {g: sp.expand(ex.subs(dep)) for g, ex in dep.items()}
    ineq = []
    for p_, kd in zip(polys, kinds):
        q = sp.expand(p_.subs(dep))
        if kd == "=":
            assert q == 0, ("identity not implied", k, p_)
            continue
        if q.is_number:
            assert q >= 0, ("constant violated", k, p_); continue
        ineq.append(q)
    for g, ex in dep.items():                                  # 0 <= dependent <= 1
        ineq += [ex, 1 - ex]
    return free, dep, ineq


def nearest(p, k):
    lab, gens, polys, kinds, fs, gb, mixv, dcv, priv, syms = leaf(k)
    free, dep, ineq = reduced(k)
    fixed = [i for i in range(48) if int(lab[i]) in (0, 1)]
    t0 = max([abs(p[i] - int(lab[i])) for i in fixed] + [0.0])
    n = len(free)
    pf = np.array([p[I[str(g)]] for g in free])
    dl = [sp.lambdify(free, ex, "numpy") for ex in dep.values()]
    pd = np.array([p[I[str(g)]] for g in dep])
    gl = [sp.lambdify(free, q, "numpy") for q in ineq]
    cons = [{"type": "ineq", "fun": (lambda f: lambda z: float(f(*z[:n])) - 1e-9)(f)} for f in gl]
    cons += [{"type": "ineq", "fun": (lambda t: lambda z: z[n] - (z[t] - pf[t]))(t)} for t in range(n)]
    cons += [{"type": "ineq", "fun": (lambda t: lambda z: z[n] + (z[t] - pf[t]))(t)} for t in range(n)]
    cons += [{"type": "ineq", "fun": (lambda f, v: lambda z: z[n] - (float(f(*z[:n])) - v))(f, v)} for f, v in zip(dl, pd)]
    cons += [{"type": "ineq", "fun": (lambda f, v: lambda z: z[n] + (float(f(*z[:n])) - v))(f, v)} for f, v in zip(dl, pd)]
    best = None
    for start in (np.clip(pf, 1e-3, 1 - 1e-3), np.full(n, 0.5), np.full(n, 0.25)):
        z0 = np.append(start, 0.3)
        try:
            r = minimize(lambda z: z[n], z0, method="SLSQP", bounds=[(1e-9, 1 - 1e-9)] * n + [(0, 1)],
                         constraints=cons, options={"maxiter": 1000, "ftol": 1e-14})
        except Exception:
            continue
        viol = max([max(0.0, -float(f(*r.x[:n]))) for f in gl] + [0.0])
        if viol < 1e-8 and (best is None or r.x[n] < best[n]): best = r.x.copy()
    if best is None: return None
    return snap(p, k, free, dep, best[:n])


def snap(p, k, free, dep, z):
    lab, gens, polys, kinds, fs, gb, mixv, dcv, priv, syms = leaf(k)
    mixmask = {syms[i] for i in mixv}
    for den in (10 ** 4, 10 ** 6, 10 ** 8, 10 ** 10, 10 ** 12):
        vals = {g: min(F(1), max(F(0), F(float(z[t])).limit_denominator(den))) for t, g in enumerate(free)}
        sub = {g: sp.Rational(v.numerator, v.denominator) for g, v in vals.items()}
        ok = True
        for g, ex in dep.items():
            v = sp.Rational(ex.subs(sub))
            if not (0 <= v <= 1): ok = False; break
            vals[g] = F(int(v.p), int(v.q))
        if not ok: continue
        if not all(0 < vals[g] < 1 for g in gens if g in mixmask): continue
        if not NF.exact_eval(polys, kinds, gens, vals): continue
        x = [F(int(lab[i])) if int(lab[i]) in (0, 1) else F(0) for i in range(48)]
        for g, v in vals.items(): x[I[str(g)]] = v
        for i in priv: x[i] = min(F(1), max(F(0), F(float(p[i])).limit_denominator(10 ** 6)))   # D = 0: any value
        for i in range(48):                     # coordinates outside the system (U-free): copy p, then the Nash re-check decides
            if int(lab[i]) not in (0, 1) and sp.Symbol(NAME[i]) not in vals and i not in priv:
                x[i] = min(F(1), max(F(0), F(float(p[i])).limit_denominator(10 ** 6)))
        if xnash(x) != 0: return ("NOT_NASH", None)
        P = [F(float(v)) for v in p]
        return ("OK", max(abs(a - b) for a, b in zip(x, P)), x)
    return None


def job(args):
    s, p, ks = args
    out = []
    for k in ks:
        r = nearest(np.array(p), k)
        if r and r[0] == "OK": out.append((k, r[1]))
        elif r and r[0] == "NOT_NASH": out.append((k, "NOT_NASH"))
    good = [(k, d) for k, d in out if d != "NOT_NASH"]
    if not good: return s, None, None, out
    k, d = min(good, key=lambda t: t[1])
    return s, k, str(d), [(k_, str(d_)) for k_, d_ in out]


def main():
    nw = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    d = json.load(open("cfr_sweep.json")); P = np.array(d["profiles"])
    R = json.load(open("reread14.json"))
    _, fam = leaves()
    tasks = [(s, P[s].tolist(), fam) for s in range(len(P))]
    with Pool(nw) as pool:
        res = pool.map(job, tasks, chunksize=1)
    lb = np.array([float(F(r["dist_lb"])) for r in R])
    ub = np.array([float(F(r[2])) if r[2] else np.nan for r in res])
    bad = sum(1 for r in res for _, d_ in r[3] if d_ == "NOT_NASH")
    print("R14 RE-READ part 2: exact equilibrium witnesses near each MCCFR output")
    print("witness found (exact, re-verified Nash by exact best responses): %d / %d;  snapped points failing the Nash re-check: %d"
          % (np.isfinite(ub).sum(), len(ub), bad))
    ok = np.isfinite(ub)
    print("upper bound: median %.4f  max %.4f" % (np.median(ub[ok]), ub[ok].max()))
    print("upper / lower: median %.3f  max %.3f   (1 = the certified lower bound is the exact distance)" %
          (np.median(ub[ok] / lb[ok]), (ub[ok] / lb[ok]).max()))
    print("seeds with ub <= 1.01 lb: %d / %d" % ((ub[ok] <= 1.01 * lb[ok]).sum(), ok.sum()))
    json.dump([dict(seed=r[0], leaf=r[1], dist_ub=r[2], per_leaf=r[3]) for r in res], open("reread14b.json", "w"), indent=0)
    print("[reread14b.json written]")


if __name__ == "__main__":
    main()
