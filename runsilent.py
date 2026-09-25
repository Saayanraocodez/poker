import numpy as np, time, bnb, kuhn3p as K
I = K.NAME_IDX
lab = np.full(48, bnb.U)
for n in ("a11","a21","a31","a41"): lab[I[n]] = 0
order = [I[n] for n in ("c11","c21","c31","c41","b11","b21","b31","b41",
                        "a22","a32","a33","a34","a23",
                        "b22","b23","b32","b33","b34",
                        "c22","c23","c32","c33","c34",
                        "a12","a13","a14","a24","b12","b13","b14","b24",
                        "c12","c13","c14","c24","a42","a43","a44",
                        "b42","b43","b44","c42","c43","c44","a11","a21","a31","a41")]
t = time.time()
pats, st = bnb.run(lab, order, cap=4096, log=25, maxnodes=int(__import__("sys").argv[1]) if len(__import__("sys").argv)>1 else None)
print("P1-SILENT: complete patterns %d  search nodes %d  %.1fs" % (len(pats), st['nodes'], time.time()-t))
np.save("pats_silent.npy", pats)
print(st)
