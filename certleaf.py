"""Re-derive every leaf verdict of a symleaf run WITH A STORED CERTIFICATE, for
checkcert.py to replay independently.  Same decision procedure as
symleaf.decide (K0 root box, K1 Groebner, K1b normal forms, K2 forced MIX
coordinate, K3 box B&B, FAMILY identities and ranges), but

  * every box proof is certbox.prove_empty_cert (contraction trace + LP duals),
  * every Groebner fact becomes an explicit cofactor identity (nullcert.lift):
        EMPTY_GB      1 = sum q_k e_k
        EMPTY_MIX     1 = sum q_k e_k + q0 (1 - t x)      (or 1 - x)
        EMPTY_CONST   p - r = sum q_k e_k,  r a constant of the wrong sign
        K1b rows      g = sum q_k e_k (basis element),  p - NF(p) = sum q_k e_k
        identities    1 = sum q_k e_k + q0 (1 - t h)   or box proofs of h > 0, h < 0
    (sympy still FINDS the basis; the certificate no longer depends on it).

Output: cert_<tag>.json.gz = {"leaves": "enum6_pat_<tag>.npy", "leaves_cert": [...]}
with one record per leaf: verdict, gens, E, derived rows, and the certificate.
A leaf whose certificate could not be produced is recorded as UNCERTIFIED with
symleaf's verdict for reference (none expected; reported at the end).

usage:  python certleaf.py <tag> <workers> [maxnodes] [limit]
"""
import numpy as np, sys, time, os, json, gzip
import sympy as sp
from fractions import Fraction as F
import kuhn3p as K, symbet, exactbox, symleaf as SL, certbox, nullcert

U, MIX, DC = 9, 2, 3
NAME = K.PARAM_NAME; I = K.NAME_IDX


def dpoly(expr, gens):
    """sympy expr -> dict poly over gens (Fractions)"""
    return exactbox.to_poly(expr, gens) if expr != 0 else {}


def ser(p): return certbox.pstr(p)


def certify(lab, maxnodes=300, dmax=6):
    lab = np.asarray(lab).astype(np.int8)
    X, syms, G = SL.build(lab)
    mixv = [i for i in range(48) if lab[i] == MIX]; dcv = [i for i in range(48) if lab[i] == DC]
    gens = [syms[i] for i in mixv + dcv]
    E = [G[i] for i in mixv if G[i] != 0]
    polys, kinds = SL._sys(lab, G, mixv, X)
    # origin of every row, in symleaf._sys's order, so the certificate can name
    # rows instead of carrying their polynomials
    orig = [("D", int(i)) for i in mixv if G[i] != 0]
    for i in range(48):
        if lab[i] == 0 and G[i] != 0: orig.append(("0", int(i)))
        if lab[i] == 1 and G[i] != 0: orig.append(("1", int(i)))
        if lab[i] == DC and G[i] != 0: orig.append(("DCx", int(i))); orig.append(("DC1", int(i)))
    assert len(orig) == len(polys)
    # private DC coordinates dropped exactly as symleaf does (dropping rows is sound)
    others = {}
    for p, k in zip(polys, kinds):
        for g in p.free_symbols: others[g] = others.get(g, 0) + 1
    priv = []
    for i in dcv:
        v = syms[i]
        own = sum(1 for p, k in zip(polys, kinds) if p.has(v) and (p == sp.expand(X[i] * G[i]) or p == sp.expand(-(1 - X[i]) * G[i])))
        if others.get(v, 0) == own: priv.append(i)
    if priv:
        keep = [not any(p.has(syms[i]) for i in priv) for p in polys]
        polys = [p for p, kp in zip(polys, keep) if kp]; kinds = [k for k, kp in zip(kinds, keep) if kp]
        orig = [o for o, kp in zip(orig, keep) if kp]
        dcv = [i for i in dcv if i not in priv]
        gens = [syms[i] for i in mixv + dcv]
    gidx = mixv + dcv; nv = len(gens)
    bounds = SL._bounds(lab, mixv, dcv)
    Ed = [dpoly(e, gens) for e in E]
    rec = {"gens": gidx, "E": [ser(e) for e in Ed], "derived": []}
    def boxcert(pl, kd, budget, og):
        r = certbox.prove_empty_cert(pl, kd, gens, bounds, budget, origins=og, lab=[int(v) for v in lab], gidx=gidx)
        if r[0]:
            c = r[1]; c["gens"] = gidx; return c
        return None
    # ---- K0
    c = boxcert(polys, kinds, 1, orig)
    if c is not None:
        rec.update(verdict="EMPTY_BOX", cert=c, stage="K0"); return rec
    # ---- K0b: a short B&B on the base system with the tree rules and the chord
    # contractor, BEFORE any Groebner work: leaf 1793 of b_M_M_0_MNR dies here in
    # 5 nodes / 4 s while its K1b cofactor lifts took longer than the 900 s watchdog
    c = boxcert(polys, kinds, min(maxnodes, 120), orig)
    if c is not None:
        rec.update(verdict="EMPTY_BOX", cert=c, stage="K0b"); return rec
    gensE = [g for g in gens if any(e.has(g) for e in E)]
    small = len(gensE) <= 8 and sum(len(sp.Add.make_args(e)) for e in E) <= 60
    GB = None
    # ---- K1
    if E and small and SL.in_ideal_one(E, gens):
        q = nullcert.lift({tuple([0] * nv): F(1)}, Ed, nv, dmax)
        if q is not None:
            rec.update(verdict="EMPTY_GB", q=[ser(x) for x in q]); return rec
        rec["note"] = "EMPTY_GB without cofactors at dmax"
    # ---- K1b: normal forms with cofactors
    if E and small:
        gb = sp.groebner(E, *gens, order="grevlex")
        gpolys = [dpoly(g, gens) for g in gb.exprs]
        okgb = True; derived = []
        for g, gd in zip(gb.exprs, gpolys):
            q = nullcert.lift(gd, Ed, nv, dmax)
            if q is None: okgb = False; break
            derived.append({"how": "gb", "poly": ser(gd), "q": [ser(x) for x in q]})
        if okgb:
            npolys = []; nkinds = []; const_hit = None
            for p, k in zip(polys, kinds):
                if k == "=": continue
                r = sp.expand(gb.reduce(p)[1])
                pd = dpoly(p, gens); rd = dpoly(r, gens)
                q = nullcert.lift(nullcert_sub(pd, rd), Ed, nv, dmax)
                if q is None: okgb = False; break
                if r.is_number:
                    rv = F(int(sp.Rational(r).p), int(sp.Rational(r).q))
                    if rv < 0 or (k == ">" and rv == 0):
                        const_hit = {"poly": ser(pd), "r": certbox.fstr(rv), "kind": k, "q": [ser(x) for x in q]}
                        break
                    continue
                derived.append({"how": "ideal", "poly": ser(pd), "r": ser(rd), "kind": k, "q": [ser(x) for x in q]})
                npolys.append(r); nkinds.append(k)
            if okgb and const_hit is not None:
                rec.update(verdict="EMPTY_CONST", const=const_hit, derived=derived); return rec
            if okgb:
                rec["derived"] = derived
                polys = list(gb.exprs) + npolys; kinds = ["="] * len(gb.exprs) + nkinds
                orig = [("der", d) for d, x in enumerate(derived) if x["how"] == "gb"] + [("der", d) for d, x in enumerate(derived) if x["how"] == "ideal"]
                assert len(orig) == len(polys)
                E = list(gb.exprs); GB = gb
            else:
                rec["note"] = "K1b cofactors missing; continuing with the original system"
    # ---- K3a
    if GB is not None:
        c = boxcert(polys, kinds, 1, orig)
        if c is not None:
            rec.update(verdict="EMPTY_BOX", cert=c, stage="K3a"); return rec
    # ---- K2 (radical membership over the ORIGINAL equalities Ed, which the checker knows)
    if E and small:
        for t, i in enumerate(mixv):
            v = syms[i]
            for val, f in ((0, v), (1, 1 - v)):
                if SL.vanishes(E, gens, f):
                    fd = dpoly(f, gens)
                    q = nullcert.radical(Ed, fd, nv, dmax)
                    if q is not None:
                        rec.update(verdict="EMPTY_MIX", coord=t, value=val, q=[ser(x) for x in q]); return rec
                    rec["note"] = "EMPTY_MIX without a radical certificate"
    # ---- K3b
    if SL._has_witness(lab):
        rec["witness"] = True
    else:
        c = boxcert(polys, kinds, maxnodes, orig)
        if c is not None:
            rec.update(verdict="EMPTY_BOX", cert=c, stage="K3b"); return rec
    # ---- FAMILY
    def x(nm): return X[I[nm]]
    def reached(nm): return lab[I[nm]] != DC
    pins = []; why = []
    for nm in SL.PIN0:
        if reached(nm):
            if lab[I[nm]] != 0: why.append(nm)
            else: pins.append([int(I[nm]), 0])
    for nm in SL.PIN1:
        if reached(nm):
            if lab[I[nm]] != 1: why.append(nm)
            else: pins.append([int(I[nm]), 1])
    if why:
        rec.update(verdict="UNCERTIFIED", why="pins " + ",".join(why)); return rec
    H = []
    if reached("a33"): H.append(("a33", x("a33") - sp.Rational(1, 2), []))
    H.append(("b41", x("b41") - 2 * (x("b11") + x("b21")), []))
    H.append(("c21", x("c21") - (sp.Rational(1, 2) - x("c11")), []))
    if reached("b33"):
        b23 = x("b23") if reached("b23") else sp.Integer(0)
        base = sp.Rational(1, 2) + (x("b11") + x("b21")) / 2 - b23 * (1 - x("b21"))
        H.append(("b33|b11<=b21", x("b33") - (base + x("b21") / 2), [x("b21") - x("b11")]))
        H.append(("b33|b11>=b21", x("b33") - (base + x("b11") / 2), [x("b11") - x("b21")]))
    idents = []
    for nm, h, extra in H:
        h = sp.expand(h); hd = dpoly(h, gens)
        item = {"name": nm, "h": ser(hd), "hyp": [[ser(dpoly(sp.expand(e), gens)), ">="] for e in extra]}
        hr = h
        if GB is not None:
            hr = sp.expand(GB.reduce(h)[1]); hrd = dpoly(hr, gens)
            q = nullcert.lift(nullcert_sub(hd, hrd), Ed, nv, dmax)
            if q is None:
                rec.update(verdict="UNCERTIFIED", why="identity %s: reduction cofactors" % nm); return rec
            item["red"] = {"hred": ser(hrd), "q": [ser(x) for x in q]}
        hrd = dpoly(hr, gens)
        if not hrd:
            item["how"] = "zero"; idents.append(item); continue
        if hr.is_number:
            rec.update(verdict="UNCERTIFIED", why="identity %s reduces to a nonzero constant" % nm); return rec
        done = False
        if E and small and SL.vanishes(E, gens, hr):
            q = nullcert.radical(Ed, hrd, nv, dmax)
            if q is not None:
                item["how"] = "radical"; item["q"] = [ser(x) for x in q]; done = True
        if not done:
            og = orig + [("hyp", u) for u in range(len(extra))] + [("side",)]
            pos = boxcert(polys + extra + [hr], kinds + [">="] * len(extra) + [">"], max(1, maxnodes // 6), og)
            neg = boxcert(polys + extra + [-hr], kinds + [">="] * len(extra) + [">"], max(1, maxnodes // 6), og)
            if pos is None or neg is None:
                rec.update(verdict="UNCERTIFIED", why="identity %s: no box certificate" % nm); return rec
            item["how"] = "box"; item["pos"] = pos; item["neg"] = neg
        idents.append(item)
    # ranges
    lc11, lc21 = lab[I["c11"]], lab[I["c21"]]
    b11, b21, c11 = x("b11"), x("b21"), x("c11")
    b23 = x("b23") if reached("b23") else sp.Integer(0)
    R = []
    if lc11 == 0:
        R += [("A:b11<=b21", b11 - b21), ("A:b21<=1/4", b21 - sp.Rational(1, 4))]
    elif lc11 == MIX and lc21 == MIX:
        R += [("B:b11<=1/4", b11 - sp.Rational(1, 4)), ("B:c11<=(2-b11)/(3+4b11)", c11 * (3 + 4 * b11) - (2 - b11))]
        H2 = sp.expand(b21 - b11)
        # B's b21 = b11 is an identity: certify like the others
        hd = dpoly(H2, gens); item = {"name": "B:b21=b11", "h": ser(hd), "hyp": []}
        hr = H2
        if GB is not None:
            hr = sp.expand(GB.reduce(H2)[1]); hrd = dpoly(hr, gens)
            q = nullcert.lift(nullcert_sub(hd, hrd), Ed, nv, dmax)
            if q is None:
                rec.update(verdict="UNCERTIFIED", why="B:b21=b11 reduction cofactors"); return rec
            item["red"] = {"hred": ser(hrd), "q": [ser(x) for x in q]}
        hrd = dpoly(hr, gens)
        if not hrd: item["how"] = "zero"
        elif hr.is_number:
            rec.update(verdict="UNCERTIFIED", why="B:b21=b11 reduces to a constant"); return rec
        else:
            done = False
            if E and small and SL.vanishes(E, gens, hr):
                q = nullcert.radical(Ed, hrd, nv, dmax)
                if q is not None: item["how"] = "radical"; item["q"] = [ser(x) for x in q]; done = True
            if not done:
                og = orig + [("side",)]
                pos = boxcert(polys + [hr], kinds + [">"], max(1, maxnodes // 6), og); neg = boxcert(polys + [-hr], kinds + [">"], max(1, maxnodes // 6), og)
                if pos is None or neg is None:
                    rec.update(verdict="UNCERTIFIED", why="B:b21=b11: no box certificate"); return rec
                item["how"] = "box"; item["pos"] = pos; item["neg"] = neg
        idents.append(item)
    elif lc11 == MIX and lc21 == 0:
        R += [("C:b21<=b11", b21 - b11), ("C:b21<=1/2-2b11", b21 - (sp.Rational(1, 2) - 2 * b11)),
              ("C:b11<=1/4", b11 - sp.Rational(1, 4)), ("C:b23<=(b11-b21)/(2(1-b21))", 2 * b23 * (1 - b21) - (b11 - b21))]
    else:
        rec.update(verdict="UNCERTIFIED", why="c11/c21 labels not A/B/C"); return rec
    ranges = []
    for nm, h in R:
        h = sp.expand(h); hd = dpoly(h, gens)
        item = {"name": nm, "h": ser(hd)}
        hr = h
        if GB is not None:
            hr = sp.expand(GB.reduce(h)[1]); hrd = dpoly(hr, gens)
            q = nullcert.lift(nullcert_sub(hd, hrd), Ed, nv, dmax)
            if q is None:
                rec.update(verdict="UNCERTIFIED", why="range %s: reduction cofactors" % nm); return rec
            item["red"] = {"hred": ser(hrd), "q": [ser(x) for x in q]}
        if hr.is_number:
            rv = F(int(sp.Rational(hr).p), int(sp.Rational(hr).q))
            if rv > 0:
                rec.update(verdict="FAMILY_WIDE", why="range %s fails (constant %s)" % (nm, rv)); return rec
            item["how"] = "const"; item["r"] = certbox.fstr(rv)
        else:
            c = boxcert(polys + [hr], kinds + [">"], max(1, maxnodes // 6), orig + [("side",)])
            if c is None:
                rec.update(verdict="FAMILY_WIDE", why="range %s not proved" % nm); return rec
            item["how"] = "box"; item["cert"] = c
        ranges.append(item)
    rec.update(verdict="FAMILY", pins=pins, identities=idents, ranges=ranges)
    return rec


def nullcert_sub(p, q):
    out = dict(p)
    for m, c in q.items(): out[m] = out.get(m, F(0)) - c
    return {m: c for m, c in out.items() if c}


def _job(a):
    k, lab, maxnodes = a
    t0 = time.time()
    try:
        rec = certify(lab, maxnodes)
    except Exception as ex:
        import traceback
        rec = {"verdict": "UNCERTIFIED", "why": "exception: %s" % traceback.format_exc()[-300:]}
    rec["leaf"] = int(k); rec["sec"] = round(time.time() - t0, 2)
    return rec


def _worker(qin, qout):
    while True:
        a = qin.get()
        if a is None: return
        qout.put(_job(a))


def run_pool(jobs, nw, timeout):
    """symleaf.run_pool for certificates: a worker that exceeds `timeout` on one
    leaf is killed, the leaf recorded UNCERTIFIED (timeout), the worker replaced."""
    import multiprocessing as mp
    ctx = mp.get_context("spawn"); qout = ctx.Queue()
    pending = list(jobs)[::-1]; workers = {}
    def spawn():
        qin = ctx.Queue(); p = ctx.Process(target=_worker, args=(qin, qout)); p.start(); workers[p.pid] = [p, qin, None]
    for _ in range(min(nw, len(pending))): spawn()
    ndone = 0; total = len(pending)
    while ndone < total:
        for pid, w in list(workers.items()):
            if w[2] is None and pending:
                job = pending.pop(); w[1].put(job); w[2] = (job, time.time())
        try:
            rec = qout.get(timeout=1.0); ndone += 1
            for pid, w in workers.items():
                if w[2] is not None and w[2][0][0] == rec["leaf"]: w[2] = None
            yield rec
        except Exception:
            pass
        now = time.time()
        for pid, w in list(workers.items()):
            if w[2] is not None and now - w[2][1] > timeout:
                job = w[2][0]; w[0].terminate(); w[0].join(5); del workers[pid]; spawn(); ndone += 1
                yield {"verdict": "UNCERTIFIED", "why": "timeout %.0fs" % timeout, "leaf": int(job[0]), "sec": round(now - w[2][1], 1)}
    for pid, w in workers.items(): w[1].put(None)
    for pid, w in workers.items():
        w[0].join(5)
        if w[0].is_alive(): w[0].terminate()


if __name__ == "__main__":
    from multiprocessing import Pool
    tag, nw = sys.argv[1], int(sys.argv[2])
    maxnodes = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    L = np.load("enum6_pat_%s.npy" % tag).astype(np.int8)
    idx = list(range(len(L)))
    if limit: idx = idx[:limit]
    with np.load("symleaf_%s.npz" % tag) as z: vd = z["verdict"]
    t0 = time.time(); out = []; cnt = {}; mism = 0
    timeout = float(os.environ.get("KUHN_CERT_TIMEOUT", "900"))
    if True:
        for n, rec in enumerate(run_pool([(k, L[k], maxnodes) for k in idx], nw, timeout)):
            out.append(rec); v = rec["verdict"]; cnt[v] = cnt.get(v, 0) + 1
            sv = SL.VERD[vd[rec["leaf"]]] if vd[rec["leaf"]] >= 0 else "UNSET"
            if v == "UNCERTIFIED" or (v.startswith("EMPTY") != sv.startswith("EMPTY")) or (v == "FAMILY") != (sv == "FAMILY"):
                if v != "UNCERTIFIED": mism += 1
                print("   leaf %d  cert %s  (symleaf %s)  %s" % (rec["leaf"], v, sv, rec.get("why", "")[:120]), flush=True)
            if (n + 1) % 100 == 0 or n + 1 == len(idx):
                print("   %d/%d  %s  %.0fs" % (n + 1, len(idx), cnt, time.time() - t0), flush=True)
    out.sort(key=lambda r: r["leaf"])
    with gzip.open("cert_%s.json.gz" % tag, "wt") as f:
        json.dump({"leaves": "enum6_pat_%s.npy" % tag, "tag": tag, "maxnodes": maxnodes, "leaves_cert": out}, f)
    print("\nTOTAL %d leaves: %s   verdict-class mismatches vs symleaf: %d   %.0fs  -> cert_%s.json.gz" % (len(out), cnt, mism, time.time() - t0, tag))
