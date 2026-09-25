import numpy as np, time, refine, sympy as sp
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
FAM = [18, 62, 70, 72, 77, 97, 99, 196, 198, 211, 440, 469]
D, R, X = refine.build_DR()
eps = sp.Symbol("eps", positive=True)
for k in FAM:
    lab = L[k]; t0 = time.time()
    out, pin = refine.closure(lab, verbose=False)
    onpath = [NAME[w] for w in range(48) if lab[w] == 2]
    # of the coordinates still free, which have a vacuous condition even under trembles?
    sub = {}; rs = []
    for w, val in pin.items():
        rw = sp.Symbol("r_" + NAME[w]); rs.append(rw)
        sub[X[w]] = eps * rw if val == 0 else 1 - eps * rw
    free = [w for w in range(48) if w not in pin]
    vac = []; live = []
    for v in free:
        if lab[v] == 2: continue
        kd, A = refine.leading(D[v].subs(sub), eps)
        (vac if kd is None else live).append(NAME[v])
    print("%4d  MIX(on path) %-40s  forced %2d %-34s  still free off path %2d %s%s" % (
        k, ",".join(onpath), len(out), "{" + ",".join("%s=%d" % (NAME[v], r[0]) for v, r in sorted(out.items())) + "}",
        len(live), ",".join(live), ("   vacuous: " + ",".join(vac)) if vac else ""), flush=True)
