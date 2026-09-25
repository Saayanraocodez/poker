"""D_all<n>.pkl for the (3, n)-card game: the own-reach-stripped gradients as
dict-polys over the NPARAM coordinates, computed exactly from the tree (the
checkD.py recursion), no sympy.   usage: KUHN_CARDS=5 python makeD.py"""
import pickle, time
from fractions import Fraction as F
import tree as T, kuhn3p as K
NV = K.NPARAM
def var(j): return {tuple(1 if t == j else 0 for t in range(NV)): F(1)}
def const(c): return {tuple([0] * NV): F(c)} if c else {}
def padd(p, q, s=F(1)):
    out = dict(p)
    for m, c in q.items(): out[m] = out.get(m, F(0)) + s * c
    return {m: c for m, c in out.items() if c}
def pmul(p, q):
    out = {}
    for m1, c1 in p.items():
        for m2, c2 in q.items():
            m = tuple(a + b for a, b in zip(m1, m2)); out[m] = out.get(m, F(0)) + c1 * c2
    return {m: c for m, c in out.items() if c}
def pscale(p, c): return {m: c * v for m, v in p.items()} if c else {}
t0 = time.time()
INT = list(T.INTERNAL); LEAF = list(T.LEAFPOS)
D = [{} for _ in range(NV)]
for d in range(T.ND):
    V = {}
    for pos in LEAF: V[pos] = [const(F(int(T.PAYT[d, pos, i]))) for i in range(3)]
    for pos in INT[::-1]:
        x = var(T.COORD[d, pos]); one_x = padd(const(1), x, F(-1))
        V[pos] = [padd(pmul(x, V[T.AGGC[pos]][i]), pmul(one_x, V[T.PASC[pos]][i])) for i in range(3)]
    R = {0: [const(1)] * 3}
    for pos in INT:
        x = var(T.COORD[d, pos]); one_x = padd(const(1), x, F(-1)); own = T.OWNER[pos][0]
        R[T.AGGC[pos]] = [R[pos][i] if i == own else pmul(R[pos][i], x) for i in range(3)]
        R[T.PASC[pos]] = [R[pos][i] if i == own else pmul(R[pos][i], one_x) for i in range(3)]
    for pos in INT:
        i = T.OWNER[pos][0]; c = T.COORD[d, pos]
        D[c] = padd(D[c], pscale(pmul(R[pos][i], padd(V[T.AGGC[pos]][i], V[T.PASC[pos]][i], F(-1))), K.KAPPA_F))
pickle.dump(D, open("D_all%d.pkl" % K.NCARDS, "wb"))
print("D_all%d.pkl: %d gradients, %d terms, %.0fs" % (K.NCARDS, NV, sum(len(p) for p in D), time.time() - t0))
