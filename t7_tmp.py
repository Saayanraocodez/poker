import numpy as np, sympy as sp, time, seqset, refine
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME; I = refine.I
lab = L[469]; pieces = seqset.leaf_pieces(lab)
unre = pieces[6]
free = [v for v in unre if lab[v] == 3]
print("unreached & free:", [NAME[v] for v in free])
# single-coordinate questions: can c34 be 1?  can b22 be positive?  etc.
for name in ("c34", "b22", "b32", "c33", "c43", "c13", "c23"):
    v = I[name]; row = []
    for val in (0, 1, "mix"):
        P, Kd, gens, bounds, deg = seqset.build_case(lab, pieces, {v: val})
        t0 = time.time()
        if P is None: row.append("%s:EMPTY(triv)" % val); continue
        e, c = seqset.empty(P, Kd, gens, bounds, 200)
        row.append("%s:%s(%.0fs)" % (val, "EMPTY" if e else "alive", time.time()-t0))
    print("  %-4s  %s" % (name, "  ".join(row)), flush=True)
