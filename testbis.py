import numpy as np, time, bnb2, branchrun, kuhn3p as K
P = np.load('pats_0000.npy')
rng = np.random.default_rng(11)
N = int(__import__('sys').argv[1]); BD = int(__import__('sys').argv[2])
sel = P[rng.choice(len(P), N, replace=False)].astype(np.int8)
alive = np.zeros(N, bool); nbox = np.zeros(N, int)
t = time.time()
for i in range(N):
    lab = sel[i]
    cnt = [0]
    st = bnb2.search(lab, branchrun.ORDER, bdepth=BD, wtol=1e-9, cap=512,
                     sink=lambda l, lo, hi: cnt.__setitem__(0, cnt[0] + l.shape[0]))
    nbox[i] = cnt[0]; alive[i] = cnt[0] > 0
dt = time.time() - t
print("bdepth=%d  sample=%d  survive=%d (%.2f%%)  %.1fs (%.1f ms/pattern)  mean boxes %.1f"
      % (BD, N, alive.sum(), 100*alive.mean(), dt, dt/N*1000, nbox[alive].mean() if alive.any() else 0))
np.save("bis_alive_%d.npy" % BD, alive); np.save("bis_sel.npy", sel)
