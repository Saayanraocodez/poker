"""Is D_v = c * R_v exactly (strict dominance at the set, by c chips)?"""
import sympy as sp, tree as T, kuhn3p as K
NAME = K.PARAM_NAME; I = K.NAME_IDX
X = [sp.Symbol(NAME[i]) for i in range(48)]
V = [[None] * T.NPOS for _ in range(T.ND)]
for d in range(T.ND):
    for pos in T.LEAFPOS: V[d][pos] = [sp.Integer(int(T.PAYT[d, pos, i])) for i in range(3)]
    for pos in list(T.INTERNAL)[::-1]:
        x = X[T.COORD[d, pos]]
        V[d][pos] = [sp.expand(x * V[d][T.AGGC[pos]][i] + (1 - x) * V[d][T.PASC[pos]][i]) for i in range(3)]
R = [[None] * T.NPOS for _ in range(T.ND)]
for d in range(T.ND):
    R[d][0] = [sp.Integer(1)] * 3
    for pos in T.INTERNAL:
        x = X[T.COORD[d, pos]]; own = T.OWNER[pos][0]
        for c_, f in ((T.AGGC[pos], x), (T.PASC[pos], 1 - x)):
            R[d][c_] = [sp.expand(R[d][pos][i] * (1 if i == own else f)) for i in range(3)]
D = [sp.Integer(0)] * 48; REACH = [sp.Integer(0)] * 48
for d in range(T.ND):
    for pos in T.INTERNAL:
        i = T.OWNER[pos][0]; v = T.COORD[d, pos]
        D[v] += sp.Rational(1, 24) * R[d][pos][i] * (V[d][T.AGGC[pos]][i] - V[d][T.PASC[pos]][i])
        REACH[v] += sp.Rational(1, 24) * R[d][pos][i]
for name in ("a14", "a24", "a44", "b12", "b42", "c14", "c24", "c44"):
    v = I[name]; d = sp.expand(D[v]); r = sp.expand(REACH[v])
    q = sp.simplify(sp.cancel(d / r))
    print("  %-4s  D = %s * reach   (%s)" % (name, q, "constant: STRICT DOMINANCE" if q.is_number else "NOT constant"))
