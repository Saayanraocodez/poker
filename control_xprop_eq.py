"""SOUNDNESS CONTROL for option 2: exact propagation must never discard a known equilibrium.
For certified equilibria (certified_eq_all.npy: 744 distinct family equilibria of the silent branch,
expl < 1e-13), follow each one's own labels down the enumc7 label tree from the silent root: at every
node the child it belongs to must survive exact propagation (xprop.child) and its box must contain
the point (to 1e-9: the points are certified floats), and at every layer depth the certificate
ladder from the node's exact box must FAIL to kill the node.  usage: python control_xprop_eq.py <n> <workers>"""
import os, sys, time
os.environ.setdefault("KUHN_MODE", "nash"); os.environ.setdefault("KUHN_ORDER", "bet")
import numpy as np
from multiprocessing import Pool
TOL = 1e-9


def follow(a):
    k, p = a
    import xprop as X, treesize6 as T6, enumc7 as E7
    U, MIX = X.U, X.MIX
    lab0 = [U] * 48; import kuhn3p as K
    spec = "a11:0,a21:0,a31:0,a41:0"
    lab, lo, hi, al = X.root_state(spec)
    if not al: return k, "root killed"
    def inside(lo, hi): return all(float(lo[i]) - TOL <= p[i] <= float(hi[i]) + TOL for i in range(48))
    if not inside(lo, hi): return k, "root box excludes the point"
    depth = 0; layer_tests = 0
    while True:
        u = [x for x in T6.ORDER if lab[x] == U]
        if not u: return k, "ok leaf after %d levels, %d layer tests" % (depth, layer_tests)
        v = u[0]
        l = 0 if p[v] <= 1e-12 else 1 if p[v] >= 1 - 1e-12 else MIX
        cl, clo, chi, cal, why = X.child(lab, lo, hi, v, l)
        if not cal: return k, "DISCARDED at depth %d (coordinate %d, label %d, %s)" % (depth, v, l, why)
        if not inside(clo, chi): return k, "BOX EXCLUDES the point at depth %d" % depth
        for i in range(48):
            if cl[i] in (0, 1) and abs(p[i] - cl[i]) > 1e-12: return k, "IMPLIED LABEL wrong at %d (depth %d)" % (i, depth)
        lab, lo, hi = cl, clo, chi; depth += 1
        if depth % E7.K_LAYER == 0:
            layer_tests += 1
            if E7.kill_cert_box(lab, lo, hi, (0, 1, 2, 3)) is not None:
                return k, "LAYER TEST KILLED the point's node at depth %d" % depth


if __name__ == "__main__":
    n, nw = int(sys.argv[1]), int(sys.argv[2])
    P = np.load("certified_eq_all.npy")
    idx = np.random.default_rng(7).choice(len(P), min(n, len(P)), replace=False)
    t0 = time.time(); bad = 0; ok = 0
    with Pool(nw) as pool:
        for k, msg in pool.imap_unordered(follow, [(int(i), P[i]) for i in idx]):
            if msg.startswith("ok"): ok += 1
            else: bad += 1; print("equilibrium %d: %s" % (k, msg), flush=True)
    print("%d equilibria followed: %d reach a leaf intact, %d discarded or excluded   (%.0fs)  %s" % (
        len(idx), ok, bad, time.time() - t0, "PASS" if bad == 0 else "*** FAIL"), flush=True)
