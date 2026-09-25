"""Silent-branch pipeline: sound bisection prune -> LM feasibility -> Nash check."""
import numpy as np, sys, time, os
import bisbatch, screen2 as screen, bnb2, solve2, bgrad

def process(args):
    lo, hi, path, depth, seed = args
    P = np.load(path, mmap_mode='r')[lo:hi].astype(np.int8)
    rng = np.random.default_rng(seed)
    surv_pat, surv_x, surv_r = [], [], []
    nproven = 0; nbox = 0
    CH = 1024
    for s in range(0, P.shape[0], CH):
        blk = P[s:s+CH]
        pid, lab, LO, HI = bisbatch.bisect(blk, depth=depth)
        alive = np.unique(pid)
        nproven += blk.shape[0] - len(alive)
        if len(alive) == 0: continue
        nbox += len(pid)
        # one LM start per surviving box, from its centre
        cen = 0.5 * (LO + HI)
        pat = blk[pid]
        for u in range(0, pat.shape[0], 1024):
            pp = pat[u:u+1024]; cc = cen[u:u+1024]
            X, r = screen.screen(pp, rng, iters=14, jac_every=7, x0=cc)
            good = r < 1e-6
            if good.any():
                surv_pat.append(pp[good]); surv_x.append(X[good]); surv_r.append(r[good])
    if surv_pat:
        return (np.concatenate(surv_pat), np.concatenate(surv_x),
                np.concatenate(surv_r), nproven, nbox, P.shape[0])
    return (np.zeros((0,48),np.int8), np.zeros((0,48)), np.zeros(0), nproven, nbox, P.shape[0])

if __name__ == "__main__":
    from multiprocessing import Pool
    path = sys.argv[1]; nw = int(sys.argv[2]); depth = int(sys.argv[3])
    tag = sys.argv[4]
    N = np.load(path, mmap_mode='r').shape[0]
    step = 10000
    jobs = [(i, min(i+step, N), path, depth, i) for i in range(0, N, step)]
    print("patterns %d  jobs %d  workers %d" % (N, len(jobs), nw), flush=True)
    t0 = time.time(); AP=[]; AX=[]; AR=[]; pv=0; bx=0; tot=0
    with Pool(nw) as pool:
        for k,(sp,sx,sr,npv,nb,nt) in enumerate(pool.imap_unordered(process, jobs)):
            AP.append(sp); AX.append(sx); AR.append(sr); pv+=npv; bx+=nb; tot+=nt
            if k % 10 == 0:
                print("  %d/%d done  proven-infeasible %d/%d  survivors %d  %.0fs"
                      % (k+1, len(jobs), pv, tot, sum(len(a) for a in AP), time.time()-t0), flush=True)
    AP=np.concatenate(AP); AX=np.concatenate(AX); AR=np.concatenate(AR)
    print("TOTAL patterns %d  proven infeasible %d  boxes %d  LM survivors %d  %.0fs"
          % (tot, pv, bx, len(AP), time.time()-t0), flush=True)
    np.save("surv_pat_%s.npy"%tag, AP); np.save("surv_x_%s.npy"%tag, AX)
