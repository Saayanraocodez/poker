import numpy as np, time, sys, bnb3, branchrun, kuhn3p as K
I=K.NAME_IDX
lab=np.full(48,bnb3.U)
for n in ("a11","a21","a31","a41"): lab[I[n]]=0
ns=int(sys.argv[1]); bd=int(sys.argv[2]); mn=int(sys.argv[3])
cnt=[0]; t=time.time()
st=bnb3.search(lab, branchrun.ORDER, nsplit=ns, bdepth=bd, cap=2048, maxnodes=mn,
               sink=lambda l,lo,hi: cnt.__setitem__(0,cnt[0]+l.shape[0]))
print("nsplit=%d bdepth=%d  nodes=%d boxes=%d abort=%s  %.0fs"%(ns,bd,st['nodes'],cnt[0],st.get('ABORT'),time.time()-t), flush=True)
