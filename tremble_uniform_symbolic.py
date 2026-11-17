"""Exact local diagnostic for uniform trembles, not a global selection proof.
Desingularize the eight observed mixed-coordinate equations at epsilon=0.
"""
import pickle, json
from pathlib import Path
from fractions import Fraction
import sympy as S
names = [p+str(c)+str(k) for p in "abc" for c in range(1,5) for k in range(1,5)]
idx = {n:i for i,n in enumerate(names)}
e = S.Symbol("eps", positive=True)
mixed = ["a32","a33","a41","b21","b33","b41","c21","c33"]
z = S.symbols("z0:8")
base = dict(zip(mixed,[47,S.Rational(1,2),4,S.Rational(1,4),S.Rational(3,4),S.Rational(1,2),S.Rational(1,2),S.Rational(3,4)]))
sample = json.loads(Path("continuations/tremble_shapes_0.json").read_text())[0]
x = [1-e if v > .9 else e for v in sample["x"]]
for n,v in zip(mixed,z): x[idx[n]] = e*v if n in ("a32","a41") else v
D = pickle.load(open("D_all.pkl","rb"))
eqs=[]; powers=[]
for n in mixed:
    expr = S.expand(sum(S.Rational(c.numerator,c.denominator)*S.prod(x[j]**a for j,a in enumerate(m) if a) for m,c in D[idx[n]].items()))
    p = S.Poly(expr,e)
    power = min(m[0] for m,c in p.terms() if c)
    q = S.cancel(expr/e**power)
    eqs.append(q.subs(e,0)); powers.append(power)
subs = dict(zip(z,[base[n] for n in mixed]))
vals = [S.factor(q.subs(subs)) for q in eqs]
J = S.Matrix(eqs).jacobian(z).subs(subs)
report = {"scope":"uniform-shape local mixed equations only; global selection and floor inequalities not proved",
          "mixed":mixed,"epsilon_powers":powers,"equations":[str(S.factor(q)) for q in eqs],
          "candidate":{n:str(base[n]) for n in mixed},"residuals":[str(v) for v in vals],
          "jacobian_rank":J.rank(),"jacobian_determinant":str(J.det())}
Path("audit-results/tremble-uniform-symbolic.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
