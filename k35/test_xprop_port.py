"""Checks for the k35 port of xprop.  usage (from k35/):
  KUHN_CARDS=4 python test_xprop_port.py regress   -- the port reproduces the 4-card xprop bit for bit
  KUHN_CARDS=5 python test_xprop_port.py struct    -- DEP / certain_reach against k35's bnb6 / treesize6
  KUHN_CARDS=5 python test_xprop_port.py agree <spec> <walks> <workers>   -- exact vs float along paths"""
import os, sys, time, json
os.environ.setdefault("KUHN_MODE", "nash"); os.environ.setdefault("KUHN_ORDER", "bet")
import numpy as np


def regress():
    import importlib.util, xprop as XP
    spec_ = importlib.util.spec_from_file_location("xprop4", os.path.join("..", "xprop.py"))
    sys.path.insert(1, "..")                      # the 4-card xprop imports ../tree.py through k35's tree (identical file)
    X4 = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(X4)
    import treesize6 as T6
    rng = np.random.default_rng(5); n = 0
    for spec in ("a11:0,a21:MIX,a31:0,a41:MIX", "a11:MIX,a21:MIX,a31:MIX,a41:1", "a11:0,a21:0,a31:0,a41:0"):
        a = XP.root_state(spec); b = X4.root_state(spec)
        assert a == b, "root differs for %s" % spec
        lab, lo, hi, al = a
        for depth in range(12):
            u = [x for x in T6.ORDER if lab[x] == XP.U]
            if not u: break
            v = u[0]; live = []
            for l in (0, 1, XP.MIX):
                s1, s2 = [], []
                r1 = XP.child(lab, lo, hi, v, l, steps=s1); r2 = X4.child(lab, lo, hi, v, l, steps=s2)
                assert r1 == r2 and s1 == s2, "child differs at depth %d" % depth
                n += 1
                if r1[3]: live.append(r1)
            if not live: break
            lab, lo, hi = live[rng.integers(len(live))][:3]
    print("regress: %d children, the k35 port reproduces the 4-card xprop bit for bit (states and certificates)" % n)


def struct():
    import xprop as X, bnb6, treesize6 as T6, kuhn3p as K
    NP = K.NPARAM
    ok = all(set(X.DEP[v]) == set(int(i) for i in np.flatnonzero(bnb6.DEPM[:, v])) for v in range(NP))
    rng = np.random.default_rng(3); bad = 0
    for _ in range(1000):
        lab = rng.choice([0, 1, 2, 3, 9], NP)
        if X.certain_reach(list(lab)) != [bool(x) for x in T6.certain_reach(lab[None])[0]]: bad += 1
    print("struct (%d cards, %d coordinates): DEP matches bnb6.DEPM %s; certain_reach mismatches %d / 1000" % (K.NCARDS, NP, ok, bad))


def walk(a):
    spec, seed = a
    import treesize6 as T6, xprop as X
    U, MIX, DC = T6.U, T6.MIX, T6.DC
    rng = np.random.default_rng(seed); weak = T6.WEAK
    root, LO, HI = T6.root_of(spec)
    L1, A1, B1, al = T6.propagate(root[None], LO[None], HI[None], weak)
    flab, flo, fhi = L1[0], A1[0], B1[0]
    xlab, xlo, xhi, xal = X.root_state(spec)
    st = {"children": 0, "fdead": 0, "repro": 0, "not_repro": 0, "exact_stronger": 0, "box_out": 0, "xtime": 0.0, "root_alive": [bool(al[0]), bool(xal)]}
    if not (al[0] and xal): return st
    for depth in range(80):
        u = [x for x in T6.ORDER if xlab[x] == U]
        if not u or flab[u[0]] != U: break
        v = u[0]; kids = []
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
                if any(clo[i] < Ak[t][i] or chi[i] > Bk[t][i] for i in range(len(clo))): st["box_out"] += 1
                live.append((t, cl, clo, chi))
        if not live: break
        t, cl, clo, chi = live[rng.integers(len(live))]
        flab, flo, fhi = Lk[t], Ak[t], Bk[t]; xlab, xlo, xhi = cl, clo, chi
    return st


def agree(spec, nwalk, nw):
    from multiprocessing import Pool
    tot = {}; t0 = time.time()
    with Pool(nw) as pool:
        for st in pool.imap_unordered(walk, [(spec, 700 + s) for s in range(nwalk)]):
            ra = st.pop("root_alive")
            for k, v in st.items(): tot[k] = tot.get(k, 0) + v
    tot = {k: (round(v, 1) if isinstance(v, float) else v) for k, v in tot.items()}
    print("agree", spec, "root alive float/exact", ra, json.dumps(tot), " %.2f s per exact child, %.0f s wall" % (
        tot.get("xtime", 0) / max(1, tot.get("children", 0)), time.time() - t0))


if __name__ == "__main__":
    {"regress": regress, "struct": struct}.get(sys.argv[1], lambda: agree(sys.argv[2], int(sys.argv[3]), int(sys.argv[4])))()
