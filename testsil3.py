import numpy as np, time, sys, bnb3, branchrun, kuhn3p as K
I=K.NAME_IDX
lab=np.full(48,bnb3.U)
for n in ("a11","a21","a31","a41"): lab[I[n]]=0
ns,bd,mn=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3])
c=[0]; t0=time.time()
st=bnb3.search(lab, branchrun.ORDER, nsplit=ns, bdepth=bd, cap=4096, maxnodes=mn,
               sink=lambda l,lo,hi: c.__setitem__(0,c[0]+l.shape[0]), log=400)
print("SILENT nsplit=%d bdepth=%d nodes=%d boxes=%d abort=%s %.0fs"%(ns,bd,st['nodes'],c[0],st.get('ABORT'),time.time()-t0), flush=True)
