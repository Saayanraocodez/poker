"""Full pipeline for one P1-opening branch: enumerate -> sound bisection ->
LM feasibility -> survivors."""
import numpy as np, sys, time, bnb, bisbatch, screen, branchrun, kuhn3p as K
I = K.NAME_IDX; A1 = [I[n] for n in ("a11","a21","a31","a41")]

def run_branch(code, depth=8, maxnodes=None, seed=0, verbose=True):
    lab = np.full(48, bnb.U)
    for k, t in enumerate(A1): lab[t] = code[k]
    rng = np.random.default_rng(seed)
    stats = dict(leaves=0, proven=0, boxes=0)
    SP, SX = [], []
    def sink(blk):
        blk = blk.astype(np.int8)
        stats['leaves'] += blk.shape[0]
        for s in range(0, blk.shape[0], 1024):
            b = blk[s:s+1024]
            pid, l2, LO, HI = bisbatch.bisect(b, depth=depth)
            al = np.unique(pid)
            stats['proven'] += b.shape[0] - len(al)
            if len(pid) == 0: continue
            stats['boxes'] += len(pid)
            pat = b[pid]; cen = 0.5 * (LO + HI)
            for u in range(0, pat.shape[0], 1024):
                X, r = screen.screen(pat[u:u+1024], rng, iters=14, jac_every=7,
                                     x0=cen[u:u+1024])
                g = r < 1e-6
                if g.any(): SP.append(pat[u:u+1024][g]); SX.append(X[g])
    t0 = time.time()
    _, st = bnb.run(lab, branchrun.ORDER, cap=4096, maxnodes=maxnodes, sink=sink)
    stats.update(nodes=st['nodes'], abort=st.get('ABORT', False), secs=time.time()-t0)
    P = np.concatenate(SP) if SP else np.zeros((0,48), np.int8)
    X = np.concatenate(SX) if SX else np.zeros((0,48))
    return stats, P, X

def _job(a):
    c, mx = a
    s, P, X = run_branch(c, maxnodes=(mx or None))
    return c, s, P, X

if __name__ == "__main__":
    import ast
    from multiprocessing import Pool
    codes = ast.literal_eval(sys.argv[1]); nw = int(sys.argv[2])
    mx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    with Pool(nw) as pool:
        allX = []
        for c, s, P, X in pool.imap_unordered(_job, [(c, mx) for c in codes]):
            print(c, s, "survivors", len(X), flush=True)
            if len(X): allX.append((c, P, X))
    if allX:
        np.save("bsurv_X.npy", np.concatenate([x for _,_,x in allX]))
        np.save("bsurv_P.npy", np.concatenate([p for _,p,_ in allX]))
        print("saved", sum(len(x) for _,_,x in allX))
