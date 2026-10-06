"""Control for option 2's propagation certificates: along random walks the independent checker
(xcheck) must replay every certificate the prover (xprop) writes and reach the SAME verdict and box,
and must reject tampered certificates.  usage: python test_xcheck.py <spec> <walks> <workers>"""
import os, sys, time, json, random
os.environ.setdefault("KUHN_MODE", "nash"); os.environ.setdefault("KUHN_ORDER", "bet")
from fractions import Fraction as F
from multiprocessing import Pool


def tamper(steps, rng, lab, lo, hi):
    """(description, corrupted steps) pairs that must all be rejected.  Where a corruption could by
    chance still be a TRUE step (another condition, an invented force), the PROVER's engine (xprop,
    a separate implementation) is the oracle: only corruptions it finds invalid are used."""
    import xprop as X
    out = []
    lo = list(lo); hi = list(hi)
    mix = [lab[i] == X.MIX for i in range(48)]; wk = X.certain_reach(lab)
    for k, st in enumerate(steps):
        ng = [lo[i] > 0 or mix[i] for i in range(48)]; nl = [hi[i] < 1 or mix[i] for i in range(48)]
        if st[0] == "C":
            v = st[1]; w = hi[v] - lo[v]
            L = list(lo); H = list(hi); L[v] = H[v] = lo[v]; l0, u0 = X.bounds(L, H)[:2]
            L = list(lo); H = list(hi); L[v] = H[v] = hi[v]; l1, u1 = X.bounds(L, H)[:2]
            for j, (side, i, val) in enumerate(st[2]):
                q = F(val); eps = F(1, 1 << 60)
                if (side == "lo" and q + eps <= hi[v]) or (side == "hi" and q - eps >= lo[v]):
                    s2 = json.loads(json.dumps(steps)); s2[k][2][j][2] = str(q + eps if side == "lo" else q - eps)
                    if side == "lo":   # truly invalid only if NO condition reaches the pushed bound
                        ts = [t for c in X.DEP[v] for t in (
                            (-u0[c] / (u1[c] - u0[c])) if ng[c] and u0[c] < 0 <= u1[c] else None,
                            (l0[c] / (l0[c] - l1[c])) if nl[c] and l0[c] > 0 >= l1[c] else None) if t is not None]
                        if not any(lo[v] + w * t >= q + eps for t in ts): out.append(("chord pushed one grid step", s2))
                    else:
                        ts = [t for c in X.DEP[v] for t in (
                            (u0[c] / (u0[c] - u1[c])) if ng[c] and u1[c] < 0 <= u0[c] else None,
                            (-l0[c] / (l1[c] - l0[c])) if nl[c] and l1[c] > 0 >= l0[c] else None) if t is not None]
                        if not any(lo[v] + w * t <= q - eps for t in ts): out.append(("chord pushed one grid step", s2))
                for c in rng.sample(range(48), 48):        # another condition that does NOT justify the bound
                    if c in (i, v): continue
                    if side == "lo":
                        t = max([t for t in ((-u0[c] / (u1[c] - u0[c])) if ng[c] and u0[c] < 0 <= u1[c] else None,
                                             (l0[c] / (l0[c] - l1[c])) if nl[c] and l0[c] > 0 >= l1[c] else None) if t is not None], default=None)
                        bad = t is None or lo[v] + w * t < q
                    else:
                        t = min([t for t in ((u0[c] / (u0[c] - u1[c])) if ng[c] and u1[c] < 0 <= u0[c] else None,
                                             (-l0[c] / (l1[c] - l0[c])) if nl[c] and l1[c] > 0 >= l0[c] else None) if t is not None], default=None)
                        bad = t is None or lo[v] + w * t > q
                    if bad:
                        s3 = json.loads(json.dumps(steps)); s3[k][2][j][1] = c
                        out.append(("chord on another condition", s3)); break
            for side, i, val in st[2]:
                if side == "lo": lo[v] = F(val)
                else: hi[v] = F(val)
        if st[0] == "F":
            DLO, DHI, RH, DMIN, DMAX = X.bounds(lo, hi)
            if st[1]:
                s2 = json.loads(json.dumps(steps)); i, val = s2[k][1][0]; s2[k][1][0][1] = 1 - val
                if not (DLO[i] > 0 or (wk[i] and DMIN[i] > 0)) if val == 0 else not (DHI[i] < 0 or (wk[i] and DMAX[i] < 0)):
                    out.append(("force flipped", s2))
            for i, val in st[1]:
                if val == 1: lo[i] = F(1)
                else: hi[i] = F(0)
        if st[0] == "K" and st[1] in ("ge", "le", "f1", "f0"):
            DLO, DHI, RH, DMIN, DMAX = X.bounds(lo, hi)
            for c in rng.sample(range(48), 48):
                valid = {"ge": ng[c] and DHI[c] < 0, "le": nl[c] and DLO[c] > 0,
                         "f1": (DLO[c] > 0 or (wk[c] and DMIN[c] > 0)) and hi[c] < 1,
                         "f0": (DHI[c] < 0 or (wk[c] and DMAX[c] < 0)) and lo[c] > 0}[st[1]]
                if not valid:
                    s2 = json.loads(json.dumps(steps)); s2[k][2] = c; out.append(("kill on another condition", s2)); break
    # an invented force, on a coordinate the prover's engine finds NOT forced at the start box
    lo0, hi0 = [F(x) for x in tamper.start[0]], [F(x) for x in tamper.start[1]]
    DLO, DHI, RH, DMIN, DMAX = X.bounds(lo0, hi0)
    ng0 = [lo0[i] > 0 or mix[i] for i in range(48)]
    for c in rng.sample(range(48), 48):
        if hi0[c] == 1 and lo0[c] < 1 and not (DLO[c] > 0 or (wk[c] and DMIN[c] > 0)):
            out.append(("invented force", [["F", [[c, 1]]]] + json.loads(json.dumps(steps)))); break
    return out


def walk(a):
    spec, seed = a
    import xprop as X, xcheck as XC
    rng = random.Random(seed)
    st = {"children": 0, "agree": 0, "disagree": 0, "excluded": 0, "dead": 0, "tamper": 0, "tamper_caught": 0, "tamper_missed": [],
          "xtime": 0.0, "ctime": 0.0, "csteps": 0}
    steps = []; lab0, lo0, hi0 = X.spec_state(spec)
    lab, lo, hi, al = X.propagate(lab0, lo0, hi0, steps=steps)
    clo, chi, cal = XC.replay(lab0, lo0, hi0, steps)
    st["root_agree"] = int(cal == al and clo == lo and chi == hi)
    for depth in range(60):
        u = [x for x in X.ORDER if lab[x] == X.U] if hasattr(X, "ORDER") else None
        import treesize6 as T6
        u = [x for x in T6.ORDER if lab[x] == X.U]
        if not u: break
        v = u[0]; live = []
        for l in (0, 1, X.MIX):
            steps = []; t0 = time.time()
            cl, clo2, chi2, cal2, why = X.child(lab, lo, hi, v, l, steps=steps); st["xtime"] += time.time() - t0
            st["children"] += 1
            if why == "excluded":
                st["excluded"] += 1
                if XC.excluded(lo, hi, v, l): st["agree"] += 1
                else: st["disagree"] += 1
                continue
            lab2 = list(lab); lab2[v] = l; lo2 = list(lo); hi2 = list(hi)
            if l == 0: hi2[v] = F(0)
            elif l == 1: lo2[v] = F(1)
            t0 = time.time()
            try:
                rlo, rhi, ral = XC.replay(lab2, lo2, hi2, steps); ok = (ral == cal2) and (not ral or (rlo == clo2 and rhi == chi2))
                if ral: ok = ok and XC.implied_labels(lab2, rlo, rhi) == [x if x != X.DC else X.U for x in cl] or \
                    ok and [x if x != X.DC else X.U for x in XC.implied_labels(lab2, rlo, rhi)] == [x if x != X.DC else X.U for x in cl]
            except XC.Bad as ex:
                ok = False
            st["ctime"] += time.time() - t0; st["csteps"] += len(steps)
            st["agree" if ok else "disagree"] += 1
            if not cal2: st["dead"] += 1
            tamper.start = (lo2, hi2)
            for desc, bad in tamper(steps, rng, lab2, lo2, hi2):
                st["tamper"] += 1
                try:
                    XC.replay(lab2, lo2, hi2, bad)
                    st["tamper_missed"].append(desc)          # every corruption here is invalid by the oracle
                except XC.Bad:
                    st["tamper_caught"] += 1
            if cal2: live.append((cl, clo2, chi2))
        if not live: break
        lab, lo, hi = live[rng.randrange(len(live))]
    return st


if __name__ == "__main__":
    spec, nwalk, nw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    tot = {}; missed = []
    with Pool(nw) as pool:
        for st in pool.imap_unordered(walk, [(spec, 900 + s) for s in range(nwalk)]):
            missed += st.pop("tamper_missed")
            for k, v in st.items(): tot[k] = tot.get(k, 0) + v
    print(spec, json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in tot.items()}))
    print("prover %.2f s per child, checker %.2f s per child, %.1f steps per child; tampered certificates NOT rejected: %d %s" % (
        tot["xtime"] / max(1, tot["children"]), tot["ctime"] / max(1, tot["children"] - tot["excluded"]),
        tot["csteps"] / max(1, tot["children"] - tot["excluded"]), len(missed), sorted(set(missed))))
