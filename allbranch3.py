import numpy as np, sys, time, itertools, bnb3, branchrun, kuhn3p as K
from multiprocessing import Pool
I=K.NAME_IDX; A1=[I[n] for n in ("a11","a21","a31","a41")]

def job(a):
    code, ns, bd, mn = a
    lab = np.full(48, bnb3.U)
    for k, t in enumerate(A1): lab[t] = code[k]
    box = []
    def sink(l, lo, hi):
        if sum(len(b[0]) for b in box) < 200000: box.append((l.copy(), lo.copy(), hi.copy()))
    t0 = time.time()
    st = bnb3.search(lab, branchrun.ORDER, nsplit=ns, bdepth=bd, cap=4096,
                     maxnodes=mn, sink=sink)
    nb = st['boxes']
    L = np.concatenate([b[0] for b in box]) if box else np.zeros((0,48),np.int8)
    LO = np.concatenate([b[1] for b in box]) if box else np.zeros((0,48))
    HI = np.concatenate([b[2] for b in box]) if box else np.zeros((0,48))
    return code, st['nodes'], nb, st.get('ABORT', False), time.time()-t0, L, LO, HI

if __name__ == "__main__":
    ns, bd, mn, nw = 4, 8, int(sys.argv[1]), int(sys.argv[2])
    rows = [eval(l) for l in open('log_probe81.txt') if l.strip().startswith('((')]
    alive = [r[0] for r in rows if r[1] != 'DEAD']
    print("running %d surviving P1-betting branches" % len(alive), flush=True)
    keepL=[];keepLO=[];keepHI=[];keepC=[]
    with Pool(nw) as pool:
        for code, nodes, nb, ab, dt, L, LO, HI in pool.imap_unordered(
                job, [(c, ns, bd, mn) for c in alive]):
            print("%s nodes=%-9d boxes=%-7d abort=%-5s %.0fs" % (code, nodes, nb, ab, dt), flush=True)
            if len(L):
                keepL.append(L);keepLO.append(LO);keepHI.append(HI)
                keepC += [code]*len(L)
    if keepL:
        np.save("bet_box_lab.npy", np.concatenate(keepL))
        np.save("bet_box_lo.npy", np.concatenate(keepLO))
        np.save("bet_box_hi.npy", np.concatenate(keepHI))
        np.save("bet_box_code.npy", np.array(keepC))
    print("DONE", flush=True)
