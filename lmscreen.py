"""LM feasibility screen over every enumerated support pattern (no bisection)."""
import numpy as np, sys, time
from multiprocessing import Pool
import screen2 as screen

def _job(a):
    lo, hi, path, seed, starts = a
    P = np.load(path, mmap_mode='r')[lo:hi].astype(np.int8)
    rng = np.random.default_rng(seed)
    SP, SX, SR = [], [], []
    for s in range(0, P.shape[0], 1024):
        blk = P[s:s+1024]
        best = None
        for k in range(starts):
            x0 = np.full(blk.shape, 0.5) if k == 0 else None
            X, r = screen.screen(blk, rng, iters=16, jac_every=8, x0=x0)
            if best is None: best = (X, r)
            else:
                m = r < best[1]
                best[0][m] = X[m]; best[1][m] = r[m]
        X, r = best
        g = r < 1e-6
        if g.any(): SP.append(blk[g]); SX.append(X[g]); SR.append(r[g])
    if SP: return np.concatenate(SP), np.concatenate(SX), P.shape[0]
    return np.zeros((0,48),np.int8), np.zeros((0,48)), P.shape[0]

if __name__ == "__main__":
    path, nw, starts, tag = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    N = np.load(path, mmap_mode='r').shape[0]
    step = 8000
    jobs = [(i, min(i+step,N), path, i, starts) for i in range(0, N, step)]
    print("patterns %d jobs %d" % (N, len(jobs)), flush=True)
    t0=time.time(); AP=[];AX=[];tot=0
    with Pool(nw) as pool:
        for k,(sp,sx,nt) in enumerate(pool.imap_unordered(_job, jobs)):
            AP.append(sp); AX.append(sx); tot+=nt
            if k % 20 == 0:
                print("  %d/%d  scanned %d  survivors %d  %.0fs"%(k+1,len(jobs),tot,sum(len(a) for a in AP),time.time()-t0), flush=True)
    AP=np.concatenate(AP); AX=np.concatenate(AX)
    print("TOTAL scanned %d  survivors %d  %.0fs"%(tot,len(AP),time.time()-t0), flush=True)
    np.save("lm_pat_%s.npy"%tag, AP); np.save("lm_x_%s.npy"%tag, AX)
