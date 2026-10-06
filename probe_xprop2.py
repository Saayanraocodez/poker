"""xprop (exact, label level) against treesize6.propagate (float) along random paths: kills reproduced,
exact box inside the float box, labels equal (implied 0/1 and DC).  usage: python probe_xprop2.py <spec> <walks> <workers>"""
import os, sys, time, json
os.environ.setdefault("KUHN_MODE", "nash"); os.environ.setdefault("KUHN_ORDER", "bet")
import numpy as np
from multiprocessing import Pool


def walk(a):
    spec, seed = a
    import treesize6 as T6, xprop as X
    U, MIX, DC = T6.U, T6.MIX, T6.DC
    rng = np.random.default_rng(seed); weak = T6.WEAK
    root, LO, HI = T6.root_of(spec)
    L1, A1, B1, al = T6.propagate(root[None], LO[None], HI[None], weak)
    flab, flo, fhi = L1[0], A1[0], B1[0]
    xlab, xlo, xhi, xal = X.root_state(spec)
    st = {"children": 0, "fdead": 0, "repro": 0, "not_repro": 0, "exact_stronger": 0, "box_out": 0, "lab_diff": 0, "xtime": 0.0, "depth": 0}
    st["root_lab_diff"] = int(list(flab) != xlab)
    for depth in range(60):
        u = [x for x in T6.ORDER if xlab[x] == U]
        if not u: break
        v = u[0]
        if flab[v] != U: st["lab_diff"] += 1; break
        kids = []
        for l in (0, 1, MIX):
            l2 = flab.copy(); a2 = flo.copy(); b2 = fhi.copy(); l2[v] = l
            if l == 0: b2[v] = 0.0
            elif l == 1: a2[v] = 1.0
            kids.append((l2, a2, b2))
        Lk, Ak, Bk, alk = T6.propagate(np.array([q[0] for q in kids]), np.array([q[1] for q in kids]), np.array([q[2] for q in kids]), weak)
        fallow = [flo[v] <= 0, fhi[v] >= 1, fhi[v] > 0 and flo[v] < 1]
        live = []
        for t, l in enumerate((0, 1, MIX)):
            t0 = time.time(); cl, clo, chi, cal, why = X.child(xlab, xlo, xhi, v, l); st["xtime"] += time.time() - t0
            fa = bool(fallow[t] and alk[t]); st["children"] += 1
            if not fa:
                st["fdead"] += 1; st["repro" if not cal else "not_repro"] += 1
            elif not cal: st["exact_stronger"] += 1
            if fa and cal:
                if any(clo[i] < Ak[t][i] or chi[i] > Bk[t][i] for i in range(48)): st["box_out"] += 1
                if list(Lk[t]) != cl: st["lab_diff"] += 1
                live.append((t, cl, clo, chi))
        if not live: break
        t, cl, clo, chi = live[rng.integers(len(live))]
        flab, flo, fhi = Lk[t], Ak[t], Bk[t]; xlab, xlo, xhi = cl, clo, chi; st["depth"] = depth + 1
    return st


if __name__ == "__main__":
    spec, nwalk, nw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    tot = {}; t0 = time.time()
    with Pool(nw) as pool:
        for st in pool.imap_unordered(walk, [(spec, 500 + s) for s in range(nwalk)]):
            for k, v in st.items(): tot[k] = tot.get(k, 0) + v
    tot = {k: (round(v, 1) if isinstance(v, float) else v) for k, v in tot.items()}
    print(spec, json.dumps(tot), " %.2f s per exact child, %.0f s wall" % (tot["xtime"] / max(1, tot["children"]), time.time() - t0))
