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
upper_names = {"a42","a43","a44","b42","b43","b44","c41","c42","c43","c44"}
x = [1-e if n in upper_names else e for n in names]
for n,v in zip(mixed,z): x[idx[n]] = e*v if n in ("a32","a41") else v
D = pickle.load(open("D_all.pkl","rb"))
eqs=[]; powers=[]; full=[]
for n in mixed:
    expr = S.expand(sum(S.Rational(c.numerator,c.denominator)*S.prod(x[j]**a for j,a in enumerate(m) if a) for m,c in D[idx[n]].items()))
    p = S.Poly(expr,e)
    power = min(m[0] for m,c in p.terms() if c)
    q = S.cancel(expr/e**power)
    eqs.append(q.subs(e,0)); full.append(q); powers.append(power)
subs = dict(zip(z,[base[n] for n in mixed]))
vals = [S.factor(q.subs(subs)) for q in eqs]
J = S.Matrix(eqs).jacobian(z).subs(subs)
report = {"scope":"uniform-shape local mixed equations only; global selection and floor inequalities not proved",
          "mixed":mixed,"epsilon_powers":powers,"equations":[str(S.factor(q)) for q in eqs],
          "candidate":{n:str(base[n]) for n in mixed},"residuals":[str(v) for v in vals],
          "jacobian_rank":J.rank(),"jacobian_determinant":str(J.det())}
# The limiting b41 row is dependent: eliminate it before dividing by epsilon.
combo = S.cancel((full[5] + full[3]/2 + full[4]/2)/e)
assert S.denom(combo).subs(e,0) != 0
regular = list(full); regular[5] = combo
r0 = S.Matrix([q.subs(e,0) for q in regular])
J2 = r0.jacobian(z).subs(subs)
report["regularized_row"] = str(S.factor(combo.subs(e,0)))
report["regularized_residuals"] = [str(S.factor(v.subs(subs))) for v in r0]
report["regularized_rank"] = J2.rank()
report["regularized_determinant"] = str(J2.det())
if J2.det() != 0 and all(v.subs(subs) == 0 for v in r0):
    # Implicit-function theorem gives a local mixed-equation branch.
    # Check leading floor signs; zero coefficients remain unresolved.
    dz = -J2.inv()*S.Matrix([S.diff(q,e).subs(e,0).subs(subs) for q in regular])
    report["z_derivative"] = {n:str(v) for n,v in zip(mixed,dz)}
    floor_checks = {}
    for i,n in enumerate(names):
        if n in mixed: continue
        expr = S.expand(sum(S.Rational(c.numerator,c.denominator)*S.prod(x[j]**a for j,a in enumerate(m) if a) for m,c in D[i].items()))
        v0 = S.factor(expr.subs(e,0).subs(subs))
        v1 = S.factor((S.diff(expr,e)+sum(S.diff(expr,v)*dv for v,dv in zip(z,dz))).subs(e,0).subs(subs))
        leading = v0 if v0 != 0 else v1
        upper = n in upper_names
        higher = None
        if leading == 0:
            poly = S.Poly(expr,e)
            order = min(m[0] for m,c in poly.terms() if c)
            coefficient = S.factor(poly.nth(order).subs(subs))
            if order >= 2 and coefficient != 0:
                leading = coefficient
                higher = {"power":order,"coefficient":str(coefficient)}
        floor_checks[n] = {"constant":str(v0),"linear":str(v1),"higher":higher,
                           "status":"UNRESOLVED" if leading == 0 else ("CORRECT" if (leading>0)==upper else "WRONG")}
    report["floor_signs_through_first_order"] = floor_checks
assert all(v == "0" for v in report["regularized_residuals"])
assert report["regularized_rank"] == 8
assert all(v["status"] == "CORRECT" for v in report["floor_signs_through_first_order"].values())
report["scope"] = "Exact local uniform-tremble branch: nonsingular mixed equations and all 40 floor signs verified. Arbitrary shapes and global uniqueness remain unproved."
report["local_uniform_branch_checks"] = "PASS"
Path("audit-results/tremble-uniform-symbolic.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
