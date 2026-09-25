"""Global questions about the equilibrium set, answered by interval B&B with
objective pruning.  A search that terminates with 0 surviving boxes PROVES that
no equilibrium attains an objective value above the threshold."""
import numpy as np, sys, time, ivl, bnb5, kuhn3p as K
I = K.NAME_IDX

def lin_obj(c):
    c = np.asarray(c, float)
    pos = c > 0; neg = c < 0
    def f(LO, HI):
        return (HI[:, pos] * c[pos]).sum(axis=1) + (LO[:, neg] * c[neg]).sum(axis=1)
    def split(LO, HI, W):
        s = W.copy(); s[:, c != 0] *= 40.0
        return s
    return f, split

def util_obj(t, sign=1):
    def f(LO, HI):
        ul, uh = ivl.util_box(LO, HI)
        return uh[:, t] if sign > 0 else -ul[:, t]
    return f, None

QUESTIONS = {}
for j in (1, 2, 3, 4):
    c = np.zeros(48); c[I['a%d1' % j]] = 1.0
    QUESTIONS['max_a%d1' % j] = (lin_obj(c), None)
c = np.zeros(48)
for j in (1,2,3,4): c[I['a%d1'%j]] = 1.0
QUESTIONS['max_sum_a_j1'] = (lin_obj(c), None)
for n, t, s in [('max_u1',0,1), ('min_u1',0,-1), ('max_u2',1,1), ('min_u2',1,-1),
                ('max_u3',2,1), ('min_u3',2,-1)]:
    QUESTIONS[n] = (util_obj(t, s), None)
for n in ('b31','c31','c22','c32','b34','a22','a32','a23','a34','b22','c23'):
    c = np.zeros(48); c[I[n]] = 1.0
    QUESTIONS['max_' + n] = (lin_obj(c), None)
for n, tgt in [('c41', 1.0)]:
    c = np.zeros(48); c[I[n]] = -1.0
    QUESTIONS['min_' + n] = (lin_obj(c), None)

def run(name, thresh, maxnodes, wtol=0.02, maxdepth=70, log=None):
    (f, split), _ = QUESTIONS[name]
    t0 = time.time()
    st, boxes = bnb5.search(objf=f, thresh=thresh, objsplit=split, wtol=wtol,
                            maxdepth=maxdepth, cap=4096, maxnodes=maxnodes, log=log)
    nb = sum(len(b[0]) for b in boxes)
    return dict(name=name, thresh=thresh, nodes=st['nodes'], boxes=st['boxes'],
                abort=st.get('ABORT', False), secs=time.time()-t0), boxes

def _job(a):
    name, th, mn = a
    r, boxes = run(name, th, mn)
    LO = np.concatenate([b[0] for b in boxes]) if boxes else np.zeros((0,48))
    HI = np.concatenate([b[1] for b in boxes]) if boxes else np.zeros((0,48))
    return r, LO, HI

if __name__ == "__main__":
    from multiprocessing import Pool
    import ast
    tasks = ast.literal_eval(sys.argv[1]); nw = int(sys.argv[2])
    with Pool(nw) as pool:
        for r, LO, HI in pool.imap_unordered(_job, tasks):
            print("%-16s thresh=%-12g nodes=%-9d boxes=%-8d abort=%-5s %.0fs"
                  % (r['name'], r['thresh'], r['nodes'], r['boxes'], r['abort'], r['secs']), flush=True)
            if len(LO):
                np.save("qbox_lo_%s.npy" % r['name'], LO)
                np.save("qbox_hi_%s.npy" % r['name'], HI)
    print("DONE", flush=True)
