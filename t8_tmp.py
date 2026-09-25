import numpy as np, sympy as sp, time, seqset, refine
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
lab = L[469]; t0 = time.time(); pieces = seqset.leaf_pieces(lab)
unre = pieces[6]
order = [v for v in unre]
print("order:", [NAME[v] for v in order], flush=True)
alive, st = seqset.dfs(lab, pieces, order, budget=40, leaf_budget=200, log=lambda s: print(s, flush=True))
print("stats", st, "alive", len(alive), "%.0fs" % (time.time()-t0))
