import numpy as np, sympy as sp, time, seqset, refine
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
lab = L[469]; t0 = time.time()
polys, kinds, syms, A, B, rsym, unreached, mixv, dcv = seqset.leaf_pieces(lab)
print("pieces in %.0fs" % (time.time()-t0))
print("nash system: %d constraints over %s" % (len(polys), sorted(str(s) for s in set().union(*[p.free_symbols for p in polys]))))
print("unreached coordinates (%d): %s" % (len(unreached), [NAME[v] for v in unreached]))
rall = set()
for v in unreached: rall |= {s for s in A[v].free_symbols if str(s).startswith("r_")}
print("tremble ratios that appear (%d): %s" % (len(rall), sorted(str(s) for s in rall)))
for v in unreached:
    fs = sorted(str(s) for s in A[v].free_symbols)
    print("  A_%-4s : %d terms over %s" % (NAME[v], len(A[v].as_ordered_terms()), fs))
