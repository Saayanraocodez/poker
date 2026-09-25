"""Symbolic derivation: given the support structure that the enumeration says
is the ONLY one carrying P1-silent equilibria, solve the indifference system
exactly and compare with SGS Table 3."""
import sympy as sp, numpy as np, tree as T, kuhn3p as K
I = K.NAME_IDX
t,p,q,y,z,r,s,w,m,n,o = sp.symbols('a33 b11 b21 b23 b33 b41 c11 c21 b32 c33 c34', nonnegative=True)
X = [sp.Integer(0)]*48
def st(nm,v): X[I[nm]] = v
for nm in ("a11","a21","a31","a41","a12","a22","a32","a13","a23","a14","a24","a34",
           "b12","b13","b14","b22","b24","b31","b34","c12","c13","c14","c22","c23",
           "c24","c31","c32"): st(nm, sp.Integer(0))
for nm in ("a42","a43","a44","b42","b43","b44","c41","c42","c43","c44"): st(nm, sp.Integer(1))
st("a33",t); st("b11",p); st("b21",q); st("b23",y); st("b33",z); st("b41",r)
st("c11",s); st("c21",w); st("b32",m); st("c33",n); st("c34",o)

# symbolic tree pass
V = [[None]*T.NPOS for _ in range(T.ND)]
for d in range(T.ND):
    for pos in T.LEAFPOS: V[d][pos] = [sp.Integer(int(T.PAYT[d,pos,i])) for i in range(3)]
    for pos in list(T.INTERNAL)[::-1]:
        x = X[T.COORD[d,pos]]
        V[d][pos] = [sp.expand(x*V[d][T.AGGC[pos]][i] + (1-x)*V[d][T.PASC[pos]][i]) for i in range(3)]
R = [[sp.Integer(0)]*T.NPOS for _ in range(T.ND)]
for d in range(T.ND):
    R[d][0] = sp.Integer(1)
    for pos in T.INTERNAL:
        x = X[T.COORD[d,pos]]
        R[d][T.AGGC[pos]] = sp.expand(R[d][pos]*x)
        R[d][T.PASC[pos]] = sp.expand(R[d][pos]*(1-x))
G = [sp.Integer(0)]*48
for d in range(T.ND):
    for pos in T.INTERNAL:
        i = T.OWNER[pos][0]
        G[T.COORD[d,pos]] += sp.Rational(1,24)*R[d][pos]*(V[d][T.AGGC[pos]][i]-V[d][T.PASC[pos]][i])
G = [sp.expand(g) for g in G]
U = [sp.expand(sp.Rational(1,24)*sum(V[d][0][i] for d in range(T.ND))) for i in range(3)]

print("=== indifference equations for the interior coordinates ===")
for nm in ("a33","b11","b21","b23","b33","b41","c11","c21"):
    print("  d/d%-4s : %s = 0" % (nm, sp.factor(sp.simplify(G[I[nm]]))))
print()
sol = sp.solve([G[I['a33']], G[I['c21']], G[I['b33']], G[I['b41']]],
               [r, z, w, t], dict=True)
print("solving the four that determine b41,b33,c21,a33:")
for d_ in sol:
    for k_,v_ in d_.items(): print("   %s = %s" % (k_, sp.simplify(v_)))
print()
print("SGS Table 3 says:  b41 = 2(b11+b21),  c21 = 1/2 - c11,  a33 = 1/2,")
print("                   b33 = 1/2 + (b11+b21)/2 + beta/2 - b23(1-b21)")
print()
sub = sol[0] if sol else {}
if sub:
    print("check b41 - 2(b11+b21)  ->", sp.simplify(sub[r] - 2*(p+q)))
    print("check c21 - (1/2-c11)   ->", sp.simplify(sub[w] - (sp.Rational(1,2)-s)))
    print("check a33 - 1/2         ->", sp.simplify(sub[t] - sp.Rational(1,2)))
    b33f = sp.Rational(1,2) + (p+q)/2 + sp.Max(p,q)/2 - y*(1-q)
    print("b33 solved              ->", sp.simplify(sub[z]))
    print("b33 Table3 (beta=b11)   ->", sp.simplify(sp.Rational(1,2)+(p+q)/2+p/2-y*(1-q)))
    print("b33 Table3 (beta=b21)   ->", sp.simplify(sp.Rational(1,2)+(p+q)/2+q/2-y*(1-q)))
    print()
    UU = [sp.simplify(u.subs(sub)) for u in U]
    print("utilities at the solution:")
    for i,u_ in enumerate(UU): print("   u%d = %s" % (i+1, sp.factor(u_)))

print()
print("="*72)
print("CASE ANALYSIS -- which coordinates are interior decides the sub-family")
print("="*72)
eqA33 = G[I['a33']]; eqB11=G[I['b11']]; eqB21=G[I['b21']]; eqB23=G[I['b23']]
eqB33 = G[I['b33']]; eqB41=G[I['b41']]; eqC11=G[I['c11']]; eqC21=G[I['c21']]
print("\n[all of a33,b11,b21,b33,b41,c21 interior; c11 interior]  -> sub-family B")
solB = sp.solve([eqA33,eqB11,eqB21,eqB33,eqB41,eqC11,eqC21],[t,r,z,w,y,q],dict=True)
for d_ in solB:
    print("   ", {str(k_): sp.simplify(v_) for k_,v_ in d_.items()})
print("\n[c11 = 0 (boundary), c21 interior, b23 = 0 (boundary)]  -> sub-family A")
sA = {s: 0, y: 0}
solA = sp.solve([eqA33.subs(sA),eqB11.subs(sA),eqB33.subs(sA),eqB41.subs(sA),eqC21.subs(sA)],[t,r,z,w],dict=True)
for d_ in solA:
    print("   ", {str(k_): sp.simplify(v_) for k_,v_ in d_.items()})
    print("    u =", [sp.factor(sp.simplify(u.subs(sA).subs(d_))) for u in U])
print("\n[c11 = 1/2 (interior value), c21 = 0 (boundary), b23 interior] -> sub-family C")
sC = {s: sp.Rational(1,2), w: 0}
solC = sp.solve([eqA33.subs(sC),eqB11.subs(sC),eqB33.subs(sC),eqB41.subs(sC),eqC11.subs(sC)],[t,r,z],dict=True)
for d_ in solC:
    print("   ", {str(k_): sp.simplify(v_) for k_,v_ in d_.items()})
    tab = sp.Rational(1,2)+(p+q)/2+p/2-y*(1-q)
    print("    b33 - Table3(beta=b11) =", sp.simplify(d_[z]-tab))
    print("    u =", [sp.factor(sp.simplify(u.subs(sC).subs(d_))) for u in U])
