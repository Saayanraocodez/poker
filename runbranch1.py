import numpy as np, time, branchrun
code=(0,0,0,0)
c,n,st,dt,out = branchrun.work((code, 4096, None))
print("branch", code, "leaves", n, "stats", st, "%.1fs"%dt, flush=True)
np.save("pats_0000.npy", out)
