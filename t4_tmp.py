import numpy as np, time, refine
L = np.load("enum6_pat_silentR.npy"); NAME = refine.NAME
lab = L[469]
print("leaf 469: iterated forcing under trembles")
t0 = time.time(); out, pin = refine.closure(lab)
print("forced %d coordinates in %.0fs" % (len(out), time.time()-t0))
print("still free:", [NAME[w] for w in range(48) if w not in pin])
