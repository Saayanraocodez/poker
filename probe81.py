import numpy as np, itertools, time, bnb, branchrun, kuhn3p as K
from multiprocessing import Pool
I=K.NAME_IDX; A1=[I[n] for n in ("a11","a21","a31","a41")]
def job(code):
    lab=np.full((1,48),bnb.U)
    for k,t in enumerate(A1): lab[0,t]=code[k]
    t0=time.time()
    l2,alive=bnb.propagate(lab.copy())
    if not alive[0]: return (code,'DEAD',0,0,time.time()-t0)
    cnt=[0]
    pats,st=bnb.run(l2[0], branchrun.ORDER, cap=4096, maxnodes=400000,
                    sink=lambda b: cnt.__setitem__(0,cnt[0]+b.shape[0]))
    return (code, cnt[0], st['nodes'], st.get('ABORT',False), time.time()-t0)
if __name__=="__main__":
    codes=[c for c in itertools.product((0,1,bnb.MIX),repeat=4) if c!=(0,0,0,0)]
    with Pool(10) as p:
        for r in p.imap_unordered(job, codes):
            print(r, flush=True)
