"""Feasibility of option 2: along random paths of a hard branch, propagate every child in float
(treesize6.propagate) and EXACTLY (xprop_proto, from the exact parent box), and count float kills
the exact propagation does not reproduce.  usage: python probe_xprop.py <spec> <walks> <workers>"""
import os, sys, time, json
os.environ.setdefault("KUHN_MODE", "nash"); os.environ.setdefault("KUHN_ORDER", "bet")
import numpy as np
from fractions import Fraction as F
from multiprocessing import Pool


def walk(a):
    spec, seed = a
    import treesize6 as T6, xprop_proto as X
    U, MIX, DC = T6.U, T6.MIX, T6.DC
    rng = np.random.default_rng(seed); weak = T6.WEAK
    root, LO, HI = T6.root_of(spec)
    L1, A1, B1, al = T6.propagate(root[None], LO[None], HI[None], weak)
    lab = root.copy(); lab[(lab == U) & (L1[0] == DC)] = DC
    flo, fhi = A1[0], B1[0]
    def xp(lb, lo_, hi_):
        mix = [bool(lb[i] == MIX) for i in range(48)]
        wk = None if weak else [bool(x) for x in T6.certain_reach(lb[None])[0]]
        return X.propagate(lo_, hi_, mix, mix, wk)
    xlo, xhi, xal, _ = xp(root, [F(x) for x in LO], [F(x) for x in HI])
    st = {"steps": 0, "fdead": 0, "fdead_xdead": 0, "fdead_xalive": 0, "falive_xdead": 0, "xtime": 0.0, "xcalls": 0, "ftime": 0.0,
          "box_not_inside": 0}
    depth = 0
    while depth < 60:
        u = [x for x in T6.ORDER if lab[x] == U]
        if not u: break
        v = u[0]; kids = []
        for l in (0, 1, MIX):
            l2 = lab.copy(); a2 = flo.copy(); b2 = fhi.copy(); l2[v] = l
            if l == 0: b2[v] = 0.0
            elif l == 1: a2[v] = 1.0
            kids.append((l2, a2, b2))
        t0 = time.time()
        Lk, Ak, Bk, alk = T6.propagate(np.array([q[0] for q in kids]), np.array([q[1] for q in kids]), np.array([q[2] for q in kids]), weak)
        st["ftime"] += time.time() - t0
        fallow = [flo[v] <= 0, fhi[v] >= 1, fhi[v] > 0 and flo[v] < 1]
        xallow = [xlo[v] <= 0, xhi[v] >= 1, xhi[v] > 0 and xlo[v] < 1]
        live = []
        for t, l in enumerate((0, 1, MIX)):
            fa = fallow[t] and alk[t]
            if xallow[t]:
                lo_ = list(xlo); hi_ = list(xhi)
                if l == 0: hi_[v] = F(0)
                elif l == 1: lo_[v] = F(1)
                t0 = time.time(); clo, chi, cal, nc = xp(kids[t][0], lo_, hi_); st["xtime"] += time.time() - t0; st["xcalls"] += nc
            else:
                cal = False
            st["steps"] += 1
            if not fa:
                st["fdead"] += 1
                if cal: st["fdead_xalive"] += 1
                else: st["fdead_xdead"] += 1
            elif not cal: st["falive_xdead"] += 1
            if fa and cal:
                if any(clo[i] < Ak[t][i] - 1e-12 or chi[i] > Bk[t][i] + 1e-12 for i in range(48)): st["box_not_inside"] += 1
                live.append((t, clo, chi))
        if not live: break
        t, clo, chi = live[rng.integers(len(live))]
        lab = kids[t][0].copy(); lab[(lab == U) & (Lk[t] == DC)] = DC
        flo, fhi = Ak[t], Bk[t]; xlo, xhi = clo, chi; depth += 1
    st["depth"] = depth
    return st


if __name__ == "__main__":
    spec, nwalk, nw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    tot = {}; t0 = time.time()
    with Pool(nw) as pool:
        for st in pool.imap_unordered(walk, [(spec, 100 + s) for s in range(nwalk)]):
            for k, v in st.items(): tot[k] = tot.get(k, 0) + v
            tot["walks"] = tot.get("walks", 0) + 1
            print("walk depth %2d  steps %3d  float-dead %3d  reproduced %3d  NOT %d  exact-stronger %d  box-not-inside %d  exact %.1fs  float %.2fs" % (
                st["depth"], st["steps"], st["fdead"], st["fdead_xdead"], st["fdead_xalive"], st["falive_xdead"], st["box_not_inside"], st["xtime"], st["ftime"]), flush=True)
    print("TOTAL", json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in tot.items()}))
    print("exact propagate: %.2f s per child, %.0f bounds calls per child; float %.3f s per 3-child call; %.0f s wall" % (
        tot["xtime"] / max(1, tot["steps"]), tot["xcalls"] / max(1, tot["steps"]), tot["ftime"] / max(1, tot["steps"] / 3), time.time() - t0))
