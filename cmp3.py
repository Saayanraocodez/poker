import numpy as np, time, sys, bnb, bnb3, branchrun, kuhn3p as K
I=K.NAME_IDX; A1=[I[n] for n in ("a11","a21","a31","a41")]
code=eval(sys.argv[1])
lab=np.full(48,bnb.U)
for k,t in enumerate(A1): lab[t]=code[k]
c=[0]; t0=time.time()
st=bnb.run(lab, branchrun.ORDER, cap=4096, sink=lambda b: c.__setitem__(0,c[0]+b.shape[0]))
print("bnb  (labels only)      nodes=%d leaves=%d  %.1fs"%(st[1]['nodes'],c[0],time.time()-t0), flush=True)
for ns,bd in ((2,6),(2,10),(4,8)):
    c=[0]; t0=time.time()
    st=bnb3.search(lab, branchrun.ORDER, nsplit=ns, bdepth=bd, cap=4096,
                   sink=lambda l,lo,hi: c.__setitem__(0,c[0]+l.shape[0]))
    print("bnb3 nsplit=%d bdepth=%-2d      nodes=%d boxes=%d  %.1fs"%(ns,bd,st['nodes'],c[0],time.time()-t0), flush=True)
