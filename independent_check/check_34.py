"""Independent exact re-check of the (3,4)-Kuhn results, 2026-11-11.

Everything here is recomputed with indep.py: an engine written from the rules alone (history
strings, recursion, information-set best responses), in fractions.Fraction, sharing no code
with kuhn3p.py / tree.py.  The repo's modules are imported only in section 1, to be compared.

    python independent_check/check_34.py          (about 40 s, no data files needed)

Sections
  1  the game: indep.py == kuhn3p.py == tree.py (utilities, best responses, D = stripped gradient)
  2  the SGS family is exactly Nash, with Table 3's utilities (900 random rational points)
  3  stated witnesses and closed forms (Theorems 2, 3; Proposition 8; Theorem 6(1); the b12 witness)
  4  ERRATA found by this check (each an exact counter-witness)
  5  hand lemma: the six cells a11 = a21 = 0 < a41 are empty (covers root81's three float kills)
"""
import os, sys, random
from fractions import Fraction as F
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(1, os.path.dirname(HERE))
import indep as I

random.seed(20261111)
KAP = F(1, 24)
FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg); print("   *** FAIL:", msg)


def rnd(lo, hi, den=240):
    lo, hi = F(lo), F(hi)
    return lo + (hi - lo) * F(random.randint(0, den), den)


def rand_family(sub=None, interior=False):
    sub = sub or random.choice('ABC')
    lo0 = F(1, 50) if interior else 0
    if sub == 'A':
        b21 = rnd(lo0, F(1, 4)); b11 = rnd(0, b21); b23 = F(0); c11 = F(0)
    elif sub == 'B':
        b11 = rnd(lo0, F(1, 4)); b21 = b11; b23 = F(0)
        c11 = rnd(0, min(F(1, 2), (2 - b11) / (3 + 2 * b11 + 2 * b21)))
    else:
        b11 = rnd(lo0, F(1, 4)); b21 = rnd(0, min(b11, F(1, 2) - 2 * b11)); c11 = F(1, 2)
        b23 = rnd(0, max(F(0), (b11 - b21) / (2 * (1 - b21))))
    beta = max(b11, b21)
    b32 = rnd(0, min(F(1), F(1, 2) + F(3, 4) * (b11 + b21) + beta / 4))
    lo, hi, w = I.window(b11, b21, b32)
    return sub, dict(b11=b11, b21=b21, b23=b23, b32=b32, c11=c11, c33=rnd(max(F(0), lo), min(F(1), hi)), c34=rnd(0, 1))


# =============================================================================== 1
print("1. the game")
th = I.terminal_histories()
check(len(th) == 13, "13 terminal histories per deal")
check(all(sum(I.payoff(d, h)) == 0 for d in I.deals() for h in th), "zero sum at every leaf")
try:
    import numpy as np, kuhn3p as K, tree as T
    check([K.PARAM_NAME[i] for i in range(48)] == I.NAMES, "coordinate naming")
    mx = 0.0
    for t in range(200):
        v = [min(F(1), F(random.choice([0, 0, 1, 1] + list(range(13))), 12)) if random.random() < .7 else F(random.randint(0, 997), 997) for _ in range(48)]
        u = I.utilities(I.from_vec(v))
        check(tuple(u) == tuple(K.utilities_exact(v)), "utilities differ from kuhn3p.utilities_exact")
        mx = max(mx, max(abs(float(a) - b) for a, b in zip(u, T.tree_util([float(x) for x in v]))))
    print("   utilities: 200 random rational profiles, exact agreement with kuhn3p; tree.py float max diff %.1e" % mx)
    mx = 0.0
    for t in range(40):
        v = [F(random.randint(0, 20), 20) for _ in range(48)]
        for pl in range(3):
            mx = max(mx, abs(float(I.br_value(I.from_vec(v), pl)[0]) - K.best_response_value(np.array([float(x) for x in v]), pl)[0]))
    print("   best responses (information-set DP here, 4 x 2^4 enumeration there): max diff %.1e" % mx)
    check(mx < 1e-12, "best response values")
except ImportError as ex:
    print("   (repo engine comparison skipped: %s)" % ex)
for t in range(15):
    p = I.from_vec([F(random.randint(0, 20), 20) for _ in range(48)])
    D, R = I.D_all(p)
    for nm in I.NAMES:
        pl, card, k = nm[0], nm[1], int(nm[2])
        own = (1 - p['a' + card + '1']) if (pl == 'a' and k >= 2) else ((1 - p['b' + card + '1']) if (pl == 'b' and k >= 3) else F(1))
        check(I.grad(p, nm)['abc'.index(pl)] == own * D[nm], "du/dx = own reach x D at " + nm)
print("   du_k/dx_i = R_k(i) D_i exactly (Definition 4), 15 random profiles x 48 coordinates")

# =============================================================================== 2
print("2. the SGS family")
cnt = {'A': 0, 'B': 0, 'C': 0}
for t in range(900):
    sub, par = rand_family('ABC'[t % 3])
    p = I.family(**par); beta = max(par['b11'], par['b21'])
    check(I.utilities(p) == [-KAP * (F(1, 2) + beta), -KAP / 2, KAP * (1 + beta)], "Table 3 utilities")
    check(I.exploitability(p) == [0, 0, 0], "family point not Nash: %s %s" % (sub, par))
    cnt[sub] += 1
print("   exploitability exactly (0,0,0) and Table-3 utilities at %s random rational points" % cnt)
p = I.family(F(1, 5), F(1, 20), 0, 0, F(1, 2), F(1, 2), 0)
q = dict(p); q['b33'] = (1 + F(1, 5) + 2 * F(1, 20)) / 2
check(I.exploitability(q) == [0, 0, F(1, 160)] and I.grad(p, 'b33') == [0, 0, 0], "erratum 1 of SGS")
print("   SGS erratum 1 (prose b33): exploitability exactly (0, 0, 1/160), although du/db33 = (0,0,0)")

# =============================================================================== 3
print("3. witnesses and closed forms")
p = I.family(F(1, 4), 0, 0, F(23, 100), F(1, 2), F(1, 4), F(9, 10)); p.update(b12=F(9, 100), b22=F(1, 40), c23=F(1, 25))
q = dict(p); q['b12'] = F(0)
q2 = dict(q); q2['b22'] = F(0); q2['c23'] = F(0)
check(I.exploitability(p) == [0, 0, 0] and I.dcond(p) == [], "off-path witness")
check(I.exploitability(q) == [F(1, 300), 0, 0] and I.exploitability(q2) == [F(1, 150), 0, 0], "off-path witness: gains 1/300, 1/150")
print("   b12 = 9/100 witness: exactly Nash; b12 := 0 gives P1 1/300, Table-2 pins 1/150")
n = 0
for t in range(100):
    sub, par = rand_family(interior=True)
    lo, hi, w = I.window(par['b11'], par['b21'], par['b32'])
    for dev, root, Dp in (('a11', lo, -4 * KAP), ('a21', lo, -4 * KAP), ('a41', hi, 2 * KAP), ('a31', None, F(0))):
        def DN(c33):
            g = I.grad(I.family(**{**par, 'c33': c33}), dev)
            return g[0], -g[2], g[1]
        D0, N0, _ = DN(F(0)); D1, N1, _ = DN(F(1))
        check(D1 - D0 == Dp and N1 - N0 == Dp, "D' = N' = %s for %s" % (Dp, dev))
        if root is None: continue
        Dr, Nr, t2 = DN(root)
        check(Dr == 0 and Nr == t2, "root of du1/d%s at the window end" % dev)
        for c33 in (F(1, 7), F(2, 5), F(9, 10)):
            if c33 != root:
                Dc, Nc, _ = DN(c33)
                check(Nc / Dc == 1 + (t2 / Dp) / (c33 - root), "Theorem 2 at " + dev); n += 1
    pr = I.family(**par)
    check(I.grad(pr, 'a11')[0] == -4 * KAP * (par['c33'] - lo) == I.grad(pr, 'a21')[0] and I.grad(pr, 'a41')[0] == -2 * KAP * (hi - par['c33']), "Theorem 3 costs")
    check(-I.grad(pr, 'b31')[0] / I.grad(pr, 'b31')[1] == F(3, 5), "rho(b31) = 3/5")
print("   Theorem 2 (rho = 1 + R/(c33 - c33*), R = t/D', D'/kappa = -4,-4,+2,0): %d exact identities" % n)
print("   Theorem 3 costs 4k(c33-lo), 4k(c33-lo), 2k(hi-c33) and rho(b31) = 3/5: exact at 100 points")
xA = I.family(F(1, 20), F(1, 5), 0, 0, 0, F(1, 2), 0); xC = I.family(F(1, 5), F(1, 20), 0, 0, F(1, 2), F(1, 2), 0)
mid = {}
for nm in I.NAMES:
    pl, card, k = nm[0], nm[1], int(nm[2])
    first = pl + card + '1'
    rx, ry = ((1 - xA[first], 1 - xC[first]) if ((pl == 'a' and k >= 2) or (pl == 'b' and k >= 3)) else (F(1), F(1)))
    mid[nm] = (rx * xA[nm] + ry * xC[nm]) / (rx + ry) if rx + ry else xA[nm]
check(I.utilities(xA) == I.utilities(xC) and I.exploitability(mid) == [0, 0, F(1, 320)], "Proposition 8")
print("   Proposition 8: sequence-form midpoint of two equal-payoff equilibria has exploitability exactly (0, 0, 1/320)")
want = {x + s: F(c) for x in 'abc' for s, c in (('12', -1), ('13', -1), ('14', -1), ('24', -1), ('43', 4), ('44', 5))}
ratios = {nm: set() for nm in I.NAMES}
for t in range(12):
    D, R = I.D_all(I.from_vec([F(random.randint(1, 29), 30) for _ in range(48)]))
    for nm in I.NAMES: ratios[nm].add(D[nm] / R[nm])
check({nm: next(iter(s)) for nm, s in ratios.items() if len(s) == 1} == want, "the 18 dominance coordinates")
print("   Theorem 6(1): D_v = c R_v with c = -1 / +4 / +5 holds at exactly the 18 stated coordinates")

# =============================================================================== 4
print("4. errata found")
bad = 0; tot = 0
for t in range(300):
    sub, par = rand_family()
    pr = I.family(**par); s = par['b11'] + par['b21']; m = par['b23'] * (1 - par['b21'])
    g = I.grad(pr, 'c31')
    check(-g[1] / g[2] == (2 - 4 * s - m) / (4 - 5 * s - m), "corrected rho(c31)")
    if m: tot += 1; bad += (-g[1] / g[2] != (2 - 4 * s) / (4 - 5 * s))
    g = I.grad(pr, 'c22')
    check(g == [KAP * par['b21'], KAP * (par['b11'] + 3 * par['b21']), -KAP * (par['b11'] + 4 * par['b21'])], "du/dc22")
print("   (i)  rho_{P3->P2}(+e_c31) = (2-4s)/(4-5s) fails at %d of %d sampled points with b23 > 0;" % (bad, tot))
print("        exact form: (2 - 4s - m)/(4 - 5s - m), m = b23 (1 - b21), from du/dc31 = k (2-s, 2-4s-m, m-4+5s)")
print("   (ii) rho_{P3->P2}(+e_c22) = (b11 + 3 b21)/(b11 + 4 b21): 4/5 only on b11 = b21; range [3/4, 1]")
p = I.family(F(1, 4), F(1, 4), 0, 0, 0, F(1, 2), 0)
q = dict(p); q['b44'] = F(0)
q0 = dict(q); q0['b43'] = F(0)
check(p['b41'] == 1 and I.exploitability(q) == [0, 0, 0] and I.dcond(q) == [] and I.exploitability(q0) == [0, 0, 0], "b44 witness")
print("   (iii) Table 4, row b44: [17/32, 1] 'over all equilibria' is false.  At b11 = b21 = 1/4 (b41 = 1) the")
print("        family point with b44 := 0 is exactly Nash AND satisfies the D-condition everywhere; with b43 := 0")
print("        as well it is still exactly Nash (own-unreached).  Correct windows: b43, b44 in [0, 1], attained.")

# =============================================================================== 5
print("5. hand lemma: no equilibrium has a11 = a21 = 0 < a41")
# If P1 bets only cards 3/4 and a41 > 0, every set 'facing P1's bet with card 1, 2 or 3' is reached and calling
# there loses for sure (c = -1 at every node), so b12 = b22 = b32 = c13 = c23 = c33 = 0 in any equilibrium of the
# cell.  Then betting card 1 is called at most by a 4: value >= (1/3)(+2) + (2/3)(-2) = -2/3, while checking card 1
# is worth at most -1.  So a11 = 0 is not a best reply.  Sanity check of that arithmetic at every vertex of the
# responses the cell leaves free (a41 = 1; the argument itself needs only a41 > 0):
worst = None
for bits in range(2 ** 10):
    p = {nm: F(0) for nm in I.NAMES}
    free = ['b42', 'c43', 'c14', 'c24', 'c34', 'c44', 'a31', 'a12', 'a13', 'a14']
    for nm, b in zip(free, range(10)): p[nm] = F((bits >> b) & 1)
    p['a41'] = F(1)
    _, plan = I.br_value(p, 0)
    va, vp = plan['a11']                        # value of betting / of checking (then playing optimally), card 1
    gain = (va - vp) * 4                         # per deal with card 1 (the plan values carry the 1/4 card probability)
    worst = gain if worst is None else min(worst, gain)
check(worst is not None and worst >= F(1, 3), "bluffing card 1 gains at least 1/3")
print("   over all 2^10 vertices of the unconstrained responses: bet(card 1) - check(card 1) >= %s > 0" % worst)

print()
print("ALL CHECKS PASSED" if not FAILS else "%d CHECK(S) FAILED" % len(FAILS))
sys.exit(1 if FAILS else 0)
