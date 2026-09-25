"""Does bisecting the DC coordinates decide the undecided residual?
bisbatch.bisect only splits MIX. Here: split MIX or DC, widest first."""
import numpy as np, bnb2, time, sys
U, MIX, DC = bnb2.U, bnb2.MIX, bnb2.DC

def bisect_dc(labs, depth=8, keepcap=60000, split_dc=True):
    B = labs.shape[0]
    lab = labs.astype(np.int8)
    LO = np.where(lab == 1, 1.0, 0.0)
    HI = np.where(lab == 0, 0.0, 1.0)
    pid = np.arange(B)
    lab, LO, HI, al = bnb2.propagate(lab, LO, HI)
    lab, LO, HI, pid = lab[al], LO[al], HI[al], pid[al]
    for _ in range(depth):
        if lab.shape[0] == 0: break
        free = (lab == MIX) | (lab == DC) if split_dc else (lab == MIX)
        W = np.where(free, HI - LO, 0.0)
        v = W.argmax(axis=1)
        if W.max() <= 0: break
        n = lab.shape[0]
        mid = 0.5 * (LO[np.arange(n), v] + HI[np.arange(n), v])
        L2 = np.repeat(lab, 2, axis=0); LO2 = np.repeat(LO, 2, axis=0)
        HI2 = np.repeat(HI, 2, axis=0); pid2 = np.repeat(pid, 2)
        r = np.arange(n)
        HI2[2 * r, v] = mid
        LO2[2 * r + 1, v] = mid
        L2, LO2, HI2, al = bnb2.propagate(L2, LO2, HI2)
        lab, LO, HI, pid = L2[al], LO2[al], HI2[al], pid2[al]
        if lab.shape[0] > keepcap: break
    return pid, lab, LO, HI

if __name__ == "__main__":
    P = np.load('pats_undecided2.npy')
    n = int(sys.argv[1]); depth = int(sys.argv[2]); blk = int(sys.argv[3])
    rng = np.random.default_rng(0)
    sel = rng.choice(len(P), n, replace=False); Q = P[sel]
    for split_dc in (False, True):
        t0 = time.time(); alive = 0; boxes = 0
        for s in range(0, n, blk):
            pid, lab, LO, HI = bisect_dc(Q[s:s+blk], depth, split_dc=split_dc)
            alive += len(np.unique(pid)); boxes += len(pid)
        print("split_dc=%-5s depth %d block %d : %d of %d still alive (%.1f%% proven)  boxes %d  %.0fs"
              % (split_dc, depth, blk, alive, n, 100*(1-alive/n), boxes, time.time()-t0), flush=True)
