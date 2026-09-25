import numpy as np, time, bnb2, branchrun, kuhn3p as K
I=K.NAME_IDX
lab=np.full(48,bnb2.U)
for n in ("a11","a21","a31","a41"): lab[I[n]]=0
import sys
bd=int(sys.argv[1]); mn=int(sys.argv[2])
cnt=[0]
st=bnb2.search(lab, branchrun.ORDER, bdepth=bd, cap=4096, maxnodes=mn,
               sink=lambda l,lo,hi: cnt.__setitem__(0,cnt[0]+l.shape[0]))
print("bdepth=%d nodes=%d boxes=%d %s"%(bd,st['nodes'],cnt[0],st.get('ABORT')))
