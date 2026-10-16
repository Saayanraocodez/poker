"""Computed content for the proof workbook (PROOF_WORKBOOK.pdf).

Every formula, table and exercise answer the workbook prints is produced HERE from the project's
own exact objects (kuhn3p's leaf table, D_all.pkl, the leaf labels, the stored certificates), and
every hand derivation the text walks through is ASSERTED equal to the machine's version before it
is printed.  Output: workbook/fragments.json (HTML snippets with KaTeX math).

usage (from the repository root):  python workbook/gen.py
"""
import os, sys, json, gzip, pickle, itertools
from fractions import Fraction as F
import numpy as np
import sympy as sp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
import kuhn3p as K, refine, seqset, symleaf as SL, qperf, reread14 as R

I = K.NAME_IDX; NAME = K.PARAM_NAME
SYM = {n: sp.Symbol(n) for n in I}                                 # plain names for computation
TEX = {SYM[n]: "%s_{%s}" % (n[0], n[1:]) for n in I}               # a11 -> a_{11}
DALL = pickle.load(open("D_all.pkl", "rb"))
OUT = {}


def tex(e):
    return sp.latex(e, symbol_names=TEX)


def frac(q):
    q = F(q)
    if q.denominator == 1: return "%d" % q.numerator
    return "%s\\tfrac{%d}{%d}" % ("-" if q < 0 else "", abs(q.numerator), q.denominator)


def tosym(p):
    return sp.Add(*[sp.Rational(F(c).numerator, F(c).denominator) * sp.Mul(*[SYM[NAME[w]] for w, e in enumerate(m) if e])
                    for m, c in p.items()])


DS = {n: sp.expand(tosym(DALL[I[n]])) for n in I}


def lin(e):
    """e as tfrac(1, den) times (numerator) with PLAIN parentheses, so KaTeX can break the line
    between terms (inline math breaks after top-level + and -; a frac or a left-paren group cannot break)."""
    e = sp.expand(e)
    num, den = sp.fraction(sp.together(e))
    num = sp.expand(num)
    if num == 0: return "0"
    if den == 1: return tex(num)
    sgn = ""
    if sp.Poly(num, *sorted(num.free_symbols, key=str)).LC() < 0 if num.free_symbols else num < 0:
        num = -num; sgn = "-"
    return r"%s\tfrac{1}{%s}\,(%s)" % (sgn, den, tex(num))
m = lambda s: "\\(" + s + "\\)"
M = lambda s: "\\[" + s + "\\]"

# ------------------------------------------------------------------ chapter 1: one deal's 13 leaves
HIST = {}
def history(fac):
    """terminal history string from the factor list of _leaves_for_deal"""
    s = ""
    for i, agg in fac:
        sit = i % 4 + 1
        first = (i // 16 == 0 and sit == 1) or (i // 16 == 1 and sit == 1) or (i // 16 == 2 and sit == 1)
        s += ("B" if agg else "K") if first else ("C" if agg else "F")
    return s

rows = []
for fac, pay in K._leaves_for_deal((1, 2, 4)):
    f = "\\,".join(("%s" if a else "(1-%s)") % TEX[SYM[NAME[i]]] for i, a in fac)
    rows.append("<tr><td><code>%s</code></td><td>%s</td><td>%s</td></tr>" % (history(fac), m(f), m("(%d,%d,%d)" % pay)))
    assert sum(pay) == 0
OUT["leaves124"] = "<table class='t'><tr><th>terminal history</th><th>reach factor</th><th>payoff (P1, P2, P3)</th></tr>%s</table>" % "".join(rows)

# all-check profile: u = 0 (exercise 1.2)
assert K.utilities_exact([F(0)] * 48) == (0, 0, 0)

# ------------------------------------------------------------------ chapter 3: D_c33 by hand, in general
# P3 holds 3, history B F: P1 bet with card j (a_j1), P2 folded with card k (1 - b_k2).
# value(call) - value(fold) for P3: call -> pot 5, P3 put in 2, wins iff 3 > P1's card: +3 or -2; fold: -1.
hand = 0; rows = []
for j, k in [(1, 2), (1, 4), (2, 1), (2, 4), (4, 1), (4, 2)]:
    reach = SYM["a%d1" % j] * (1 - SYM["b%d2" % k])
    diff = (3 - (-1)) if 3 > j else (-2 - (-1))
    hand += sp.Rational(1, 24) * reach * diff
    rows.append("<tr><td>(%d, %d, 3)</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
        j, k, m(tex(reach)), m("+3" if 3 > j else "-2"), m("-1"), m("%+d" % diff)))
assert sp.expand(hand - DS["c33"]) == 0
OUT["dc33_table"] = ("<table class='t'><tr><th>deal (P1,P2,P3)</th><th>others' reach to the node</th><th>P3 calls</th>"
                     "<th>P3 folds</th><th>difference</th></tr>%s</table>" % "".join(rows))
OUT["dc33_formula"] = M(r"\begin{aligned}D_{c_{33}}=\tfrac1{24}\Big[&4a_{11}\big((1-b_{22})+(1-b_{42})\big)+4a_{21}\big((1-b_{12})+(1-b_{42})\big)\&-a_{41}\big((1-b_{12})+(1-b_{22})\big)\Big]\end{aligned}")
OUT["dc33_machine"] = M(r"24\,D_{c_{33}} = " + tex(sp.expand(24 * DS["c33"])))

# ------------------------------------------------------------------ the family substitution
PINS = {}
for n in ("a12", "a13", "a14", "a24", "b12", "b13", "b14", "b24", "c12", "c13", "c14", "c24"): PINS[n] = 0
for n in ("a42", "a43", "a44", "b42", "b43", "b44", "c42", "c43", "c44"): PINS[n] = 1
for n in ("a11", "a21", "a22", "a23", "a31", "a32", "a34", "a41", "b22", "b31", "b34", "c22", "c23", "c31", "c32"): PINS[n] = 0
PINS["c41"] = 1
FSUB = {SYM[k]: v for k, v in PINS.items()}
DF = {n: sp.factor(sp.expand(DS[n].subs(FSUB))) for n in I}

# D_b11 on the family, by hand (P2 holds 1 after P1's check)
rows = []; tot = 0
for p1, p3 in [(2, 3), (2, 4), (3, 2), (3, 4), (4, 2), (4, 3)]:
    if p3 == 4: bet, how = -2, r"P3 calls (\(c_{42}=1\)), P1 folds (\(a_{%d4}=0\)), P3's 4 wins" % p1
    elif p1 == 2: bet, how = 2, r"P3 folds, P1 folds the 2 (\(a_{23}=0\)): P2 takes the pot"
    elif p1 == 3: bet, how = 2 - 4 * SYM["a33"], r"P3 folds; P1 calls with prob. \(a_{33}\) (P2 gets \(-2\)), else folds (P2 gets \(+2\))"
    else: bet, how = -2, r"P3 folds, P1 calls with the 4 (\(a_{43}=1\))"
    tot += sp.Rational(1, 24) * (bet - (-1))
    rows.append("<tr><td>(%d, 1, %d)</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (p1, p3, m(tex(sp.sympify(bet))), m("-1"), how))
assert sp.expand(tot - DF["b11"]) == 0
OUT["db11_table"] = ("<table class='t'><tr><th>deal (P1,P2,P3)</th><th>P2 bets</th><th>P2 checks</th><th>what happens after the bet (family values)</th></tr>%s</table>"
                     % "".join(rows))
OUT["db11_result"] = M(r"\begin{aligned}D_{b_{11}}\big|_{\text{family}}&=\tfrac1{24}\big[(2+1)+(-2+1)+(2-4a_{33}+1)+3\cdot(-2+1)\big]\&=\tfrac{2-4a_{33}}{24}=" + tex(DF["b11"]) + r"\end{aligned}")

# ------------------------------------------------------------------ chapter 5: the family's incentive table
fam_rows = [
    ("a33", "P1 calls with the 3 after K B F", "\\(a_{33}\\) interior \\(\\Rightarrow\\) \\(b_{41}=2(b_{11}+b_{21})\\)"),
    ("b11", "P2 bluffs the 1 after K", "\\(b_{11}\\) interior \\(\\Rightarrow\\) \\(a_{33}=\\tfrac12\\)"),
    ("b21", "P2 bluffs the 2 after K", "with \\(a_{33}=\\tfrac12\\): \\(-b_{23}(2c_{11}-1)/12\\)"),
    ("b23", "P2 calls with the 2 after K K B F", "\\(b_{23}>0\\Rightarrow c_{11}=\\tfrac12\\) (sub-family C only)"),
    ("b33", "P2 calls with the 3 after K K B F", "\\(b_{33}\\) interior \\(\\Rightarrow c_{11}+c_{21}=\\tfrac12\\)"),
    ("b41", "P2 bets the 4 after K", "consistent with \\(a_{33}=\\tfrac12=c_{11}+c_{21}\\)"),
    ("c11", "P3 bluffs the 1 after K K", "\\(c_{11}\\) interior \\(\\Rightarrow\\) \\(b_{33}=\\tfrac12+\\tfrac{b_{41}-b_{21}}2-b_{23}(1-b_{21})\\)"),
    ("c21", "P3 bluffs the 2 after K K", "\\(c_{21}\\) interior \\(\\Rightarrow\\) \\(b_{33}=\\tfrac{1+b_{41}-b_{11}}2\\)"),
    ("a11", "P1 bets the 1 (deterrence)", "\\(\\le0\\iff c_{33}\\ge \\tfrac12-b_{32}=:\\mathrm{lo}\\)"),
    ("a21", "P1 bets the 2 (deterrence)", "identical to \\(a_{11}\\)"),
    ("a41", "P1 bets the 4 (deterrence)", "\\(\\le 0\\iff c_{33}\\le \\mathrm{hi}\\) (see Ch. 6)"),
    ("a31", "P1 bets the 3 (deterrence)", "strictly negative: the costliest opening"),
    ("a22", "P1 calls with the 2 after K K B", "\\(\\le0\\iff c_{11}\\le\\frac{2-b_{11}}{3+b_{41}}\\) (Table 3's cap on \\(c_{11}\\))"),
    ("a32", "P1 calls with the 3 after K K B", "\\(\\le 0\\) on the family (a round-2 deterrence)"),
    ("b31", "P2 bluffs the 3 after K", "with \\(c_{11}+c_{21}=\\tfrac12\\): exactly \\(-\\tfrac5{48}\\)"),
    ("c31", "P3 bets the 3 after K K", "strictly negative on the family"),
    ("b32", "P2 calls P1's bet with the 3", "\\(0\\): unreached (P1 never bets)"),
    ("c33", "P3 calls with the 3 after B F", "\\(0\\): unreached"),
    ("c34", "P3 calls with the 3 after B C", "\\(0\\): unreached"),
]
rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (m("D_{%s_{%s}}" % (n[0], n[1:])), d, m(lin(DF[n])), c) for n, d, c in fam_rows)
OUT["family_table"] = "<table class='t'><tr><th>coordinate</th><th>decision</th><th>\\(D\\) on the family (Tables 2, 3 pins)</th><th>what it says</th></tr>%s</table>" % rows
# the identities as a by-hand chain (asserted)
b11, b21, b23, b33, b41, c11, c21, a33 = (SYM[n] for n in ("b11", "b21", "b23", "b33", "b41", "c11", "c21", "a33"))
assert sp.expand(DF["b11"] - (1 - 2 * a33) / 12) == 0
assert sp.expand(DF["a33"] - (2 * b11 + 2 * b21 - b41) / 12) == 0
assert sp.expand(DF["b33"] - (2 * c11 + 2 * c21 - 1) / 12) == 0
assert sp.expand(DF["c11"] - (2 * b21 * b23 - b21 - 2 * b23 - 2 * b33 + b41 + 1) / 12) == 0
assert sp.expand(DF["c21"] - (-(b11 + 2 * b33 - b41 - 1) / 12)) == 0
assert sp.expand(DF["b23"] - (2 * c11 - 1) / 12) == 0
assert sp.expand(DF["b31"].subs(c21, sp.Rational(1, 2) - c11) + sp.Rational(5, 48)) == 0
assert sp.expand(DF["a11"] - (-(2 * SYM["b32"] + 2 * SYM["c33"] - 1) / 12)) == 0
# a41: the upper end of the window, per sub-family
a41 = sp.expand(DF["a41"])
c33, b32 = SYM["c33"], SYM["b32"]
hiA = sp.solve(a41.subs({c11: 0, c21: sp.Rational(1, 2)}), c33)[0]
hiC = sp.solve(a41.subs({c11: sp.Rational(1, 2), c21: 0}), c33)[0]
hiB = sp.solve(a41.subs({b21: b11, c21: sp.Rational(1, 2) - c11}), c33)[0]
assert sp.expand(hiA - (sp.Rational(1, 2) - b32 + sp.Rational(3, 4) * (b11 + b21) + b21 / 4)) == 0
assert sp.expand(hiC - (sp.Rational(1, 2) - b32 + sp.Rational(3, 4) * (b11 + b21) + b11 / 4)) == 0
assert sp.expand(hiB - (sp.Rational(1, 2) - b32 + sp.Rational(7, 4) * b11)) == 0
OUT["hiA"] = M("\\text{A }(c_{11}=0,\\ \\beta=b_{21}):\\quad c_{33}\\le " + tex(hiA))
OUT["hiC"] = M("\\text{C }(c_{11}=\\tfrac12,\\ \\beta=b_{11}):\\quad c_{33}\\le " + tex(hiC))
OUT["hiB"] = M("\\text{B }(b_{21}=b_{11}=\\beta):\\quad c_{33}\\le " + tex(hiB))
# a22 cap
a22s = sp.solve(DF["a22"], c11)[0]
assert sp.simplify(a22s - (2 - b11) / (3 + b41)) == 0

# ------------------------------------------------------------------ Theorem 2: N' = D' because P2 does not care about c33
U = {}
def u_sym(k):
    """u_k as a sympy polynomial (exact), from the leaf table"""
    tot = 0
    for fac_rows in [K._leaves_for_deal(d) for d in itertools.permutations(K.CARDS, 3)]:
        for fac, pay in fac_rows:
            t = sp.Integer(1)
            for i, a in fac: t *= SYM[NAME[i]] if a else 1 - SYM[NAME[i]]
            tot += t * pay[k]
    return sp.expand(tot / 24)
U = [u_sym(k) for k in range(3)]
d2 = [sp.expand(sp.diff(U[k], SYM["a11"], SYM["c33"])) for k in range(3)]
assert d2[1] == 0 and sp.expand(d2[0] + d2[2]) == 0
OUT["thm2_mixed"] = M(r"\begin{aligned}\frac{\partial^2 u_1}{\partial a_{11}\partial c_{33}}&=" + tex(d2[0]) + r",\ \frac{\partial^2 u_2}{\partial a_{11}\partial c_{33}}&=" + tex(d2[1]) + r",\ \frac{\partial^2 u_3}{\partial a_{11}\partial c_{33}}&=" + tex(d2[2]) + r"\end{aligned}")
for k in range(3):
    assert sp.expand(sum(U)) == 0

# ------------------------------------------------------------------ the 3/5 example
d = [sp.expand(sp.diff(U[k], SYM["b31"]).subs(FSUB)) for k in range(3)]
d = [sp.factor(x) for x in d]
assert sp.simplify(d[0].subs(c21, sp.Rational(1, 2) - c11) - sp.Rational(1, 16)) == 0
assert sp.simplify(d[1].subs(c21, sp.Rational(1, 2) - c11) + sp.Rational(5, 48)) == 0
OUT["ex35"] = M(r"\begin{aligned}\frac{\partial u_1}{\partial b_{31}}&=" + tex(d[0]) + r",\ \frac{\partial u_2}{\partial b_{31}}&=" + tex(d[1]) + r"\end{aligned}")

# ------------------------------------------------------------------ chapter 4: the point P* and its 48 D values
lab469, Pstar = qperf.point(F(9, 16))
assert seqset.verify_point(lab469, Pstar) is None
rows = []
for i in range(48):
    x = Pstar[i]; dv = refine.ev(DALL[i], Pstar)
    if 0 < x < 1: need, ok = "\\(D=0\\)", dv == 0
    elif x == 0: need, ok = "\\(D\\le 0\\)", dv <= 0
    else: need, ok = "\\(D\\ge 0\\)", dv >= 0
    assert ok
    rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (m("%s_{%s}" % (NAME[i][0], NAME[i][1:])), m(frac(x)), m(frac(dv)), need))
half = len(rows) // 2
OUT["pstar_table"] = ("<div class='two'><table class='t s'><tr><th>coord.</th><th>value</th><th>\\(D_v\\)</th><th>needs</th></tr>%s</table>"
                      "<table class='t s'><tr><th>coord.</th><th>value</th><th>\\(D_v\\)</th><th>needs</th></tr>%s</table></div>" % ("".join(rows[:24]), "".join(rows[24:])))
uP = K.utilities_exact(Pstar)
assert uP == (F(-5, 192), F(-1, 48), F(3, 64))
OUT["pstar_u"] = M("u(P^\\ast)=\\Big(%s,\\ %s,\\ %s\\Big)=\\big(-\\kappa(\\tfrac12+\\beta),\\ -\\tfrac{\\kappa}2,\\ \\kappa(1+\\beta)\\big)\\text{ with }\\beta=\\tfrac18" % tuple(frac(v) for v in uP))
# exercise: c33 = 3/4 is outside the window [1/2, 23/32]
_, P34 = qperf.point(F(3, 4))
da41 = refine.ev(DALL[I["a41"]], P34)
assert da41 == F(1, 384)
OUT["ex_c33_34"] = frac(da41)

# ------------------------------------------------------------------ dominance (Theorem 6.1)
Dr, Rr, X = refine.build_DR()
dom = []
for n in [p + s for p in "abc" for s in ("12", "13", "14", "24", "43", "44")]:
    v = I[n]; c = sp.simplify(Dr[v] / Rr[v])
    assert c.is_number
    dom.append((n, c))
OUT["dominance"] = ", ".join(m("%s_{%s}" % (n[0], n[1:]) + ":\\ " + str(c)) for n, c in dom)

# ------------------------------------------------------------------ appendix: the 48 D polynomials
rows = []
for i in range(48):
    n = NAME[i]
    rows.append("<p class='dpoly'>%s</p>" % m(r"24\,D_{%s_{%s}}=%s" % (n[0], n[1:], tex(sp.expand(24 * DS[n])))))
OUT["allD"] = "".join(rows)

# ------------------------------------------------------------------ appendix: the twelve FAMILY leaves
L, fam = R.leaves(); IDS = R.identities()
lines = open("nefull_systems.txt").read().split("=== leaf ")[1:]
idtxt = {}
for blk in lines:
    k = int(blk.split()[0])
    for ln in blk.splitlines():
        if ln.startswith("identities"): idtxt[k] = ln.split(":", 1)[1].strip()
rows = []
for k in fam:
    lab = L[k]
    sub = "A" if int(lab[I["c11"]]) == 0 else ("B" if int(lab[I["c21"]]) == 2 else "C")
    s = "".join({0: "0", 1: "1", 2: "M", 3: "D", 9: "U"}[int(v)] for v in lab)
    labs = " ".join(s[16 * p:16 * p + 16] for p in range(3))
    ids = [sp.sympify(t.strip().strip("'"), locals=SYM) for t in idtxt[k].strip("[]").split(",")]
    rows.append("<tr><td>%d</td><td>%s</td><td><code>%s</code></td><td>%s</td></tr>" % (
        k, sub, labs, ", ".join(m(tex(e) + "=0") for e in ids)))
OUT["leaves12"] = "<table class='t s'><tr><th>leaf</th><th>sub</th><th>labels (a11..a44 b11..b44 c11..c44)</th><th>identities</th></tr>%s</table>" % "".join(rows)

# ------------------------------------------------------------------ a certificate walked through by hand: 62:b33:inf
cert = json.load(gzip.open("nefull_certs.json.gz", "rt"))["62:b33:inf"]
c = cert["cert"]; gens = [NAME[g] for g in c["gens"]]
lab62 = L[62]
Xs = []
for i in range(48):
    Xs.append(sp.Integer(int(lab62[i])) if int(lab62[i]) in (0, 1) else SYM[NAME[i]])
def restricted(i):
    return sp.factor(sp.expand(DS[NAME[i]].subs({SYM[NAME[j]]: Xs[j] for j in range(48) if int(lab62[j]) in (0, 1)})))
steps = c["nodes"][0]["steps"]
origins = c["origins"]
used = sorted({s[-1] for s in steps if s[0] in ("lo", "hi")} | {s[1] for s in steps if s[0] == "kill"})
cons_txt = []
for ci in used:
    kind, *rest = origins[ci]
    if kind == "D":
        cons_txt.append("<li>constraint %d: %s (\\(%s\\) is MIX on leaf 62)</li>" % (ci, m("D_{%s_{%s}}=%s=0" % (NAME[rest[0]][0], NAME[rest[0]][1:], tex(restricted(rest[0])))), "%s_{%s}" % (NAME[rest[0]][0], NAME[rest[0]][1:])))
    elif kind == "side":
        cons_txt.append("<li>constraint %d: the hypothesis to refute, %s</li>" % (ci, m("\\tfrac12-b_{33}>0")))
step_txt = []
for s in steps:
    if s[0] in ("lo", "hi"):
        _, j, val, strict, ci = s
        step_txt.append("<li>from constraint %d: %s %s %s</li>" % (ci, m("%s_{%s}" % (gens[j][0], gens[j][1:])), m("\\ge" if s[0] == "lo" else "\\le"), m(frac(F(val)))))
    elif s[0] == "kill":
        step_txt.append("<li>constraint %d is now impossible on the box: \\(b_{33}\\ge\\tfrac12\\) makes \\(\\tfrac12-b_{33}\\le 0\\). The set is empty.</li>" % s[1])
OUT["cert_constraints"] = "<ul>%s</ul>" % "".join(cons_txt)
OUT["cert_steps"] = "<ol>%s</ol>" % "".join(step_txt)
assert restricted(I["a33"]) == sp.factor((2 * b21 - b41) / 12) or sp.expand(restricted(I["a33"]) - (2 * b21 - b41) / 12) == 0

json.dump(OUT, open(os.path.join(ROOT, "workbook", "fragments.json"), "w"), indent=0)
print("fragments:", ", ".join(sorted(OUT)))
