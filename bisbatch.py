"""Batched depth-limited value bisection: sound infeasibility pruning."""
import numpy as np, bnb2

U, MIX, DC = bnb2.U, bnb2.MIX, bnb2.DC

def bisect(labs, depth=8, keepcap=60000):
    """labs (B,48) int8 complete label patterns ->
       (pid, LO, HI) surviving boxes; patterns absent from pid are PROVEN
       to contain no point satisfying the first-order Nash conditions."""
    B = labs.shape[0]
    lab = labs.astype(np.int8)
    LO = np.where(lab == 1, 1.0, 0.0)
    HI = np.where(lab == 0, 0.0, 1.0)
    pid = np.arange(B)
    lab, LO, HI, al = bnb2.propagate(lab, LO, HI)
    lab, LO, HI, pid = lab[al], LO[al], HI[al], pid[al]
    for _ in range(depth):
        if lab.shape[0] == 0: break
        W = np.where(lab == MIX, HI - LO, 0.0)
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
