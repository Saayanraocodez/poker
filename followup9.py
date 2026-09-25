"""
Refinement, part 2: the tremble-consistency check across ALL off-path sets, and
what survives on the resulting refined face.  (Part 1 is followup8.py.)
"""
import numpy as np

import kuhn3p as K
import family as F

I = K.NAME_IDX
OWN = {"b32": 1, "c33": 2, "c34": 2, "c44": 2}
base = dict(b11=.15, b21=.15, b23=0., b32=.40, c11=.25, c34=.5)
lo0, hi0 = F.c33_range(base["b11"], base["b21"], base["b32"])
p = F.make_profile(c33=(lo0 + hi0) / 2, **base)


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


def adv(prof, nm, eps, r):
    """Per-unit-reach advantage of the aggressive action, under P1 trembles."""
    q = prof.copy()
    for j in range(1, 5):
        q[I["a%d1" % j]] = eps * r[j - 1]
    g = K.exact_coord_derivative(q, I[nm])[OWN[nm]]
    rr = K.reach(q)[I[nm]]
    return g / rr if rr > 1e-18 else np.nan


hdr("1.  c34 and c44 are pinned by DOMINANCE, not by beliefs")
print("   (advantage is identical under every tremble ratio -> belief-free)")
print("   r                    c34 adv      c44 adv")
for r in ((1, 1, 1, 1), (1, 1, 1, 4), (1, 1, 1, 8), (5, 1, 1, 1),
          (1, 5, 1, .2), (.1, 3, 7, 1)):
    print("   %-20s %+.6f    %+.6f" % (str(r), adv(p, "c34", 1e-3, r),
                                       adv(p, "c44", 1e-3, r)))
print("\n   c34: at BC holding the 3, P2 has called -- and in this family P2 calls")
print("   only with the 4 or the 3 (prob b32).  P3 holds the 3, so P2 holds the 4")
print("   and P3 loses for sure.  Folding is dominant: advantage exactly -1.")
print("   Table 3 leaves c34 free in [0,1]; ANY refinement forces c34 = 0.")
print("   c44 = 1 (Table 2) is confirmed: advantage exactly +5.")

hdr("2.  Consistency: is one tremble ratio simultaneously OK for c33 and b32?")
print("   Belief at P3's BF/card-3 set: q = (r1+r2)/(r1+r2+2*r4).")
print("   P3 calls iff 3q - 2(1-q) > -1, i.e. q > 1/5; indifferent iff")
print("   r4 = 2(r1+r2).  Table 3 needs c33 INTERIOR, hence exact indifference.\n")
print("   r4      q        c33 adv      b32 adv      c33 ok?    b32 ok?")
for r4 in (0.5, 1, 2, 3, 4, 5, 6, 8, 12, 20):
    r = (1, 1, 1, r4)
    q = 2.0 / (2.0 + 2.0 * r4)
    a33, a32 = adv(p, "c33", 1e-3, r), adv(p, "b32", 1e-3, r)
    ok33 = "yes (mix)" if abs(a33) < 1e-10 else "NO"
    ok32 = ("yes (mix)" if abs(a32) < 1e-10
            else ("yes (->0)" if a32 < 0 else "NO (->1, outside)"))
    print("   %-7s %.5f  %+.6f    %+.6f    %-10s %s" % (r4, q, a33, a32, ok33, ok32))
print("\n   Exactly one ratio works: r4 = 2(r1+r2).  There b32's advantage is")
print("   -0.1667 < 0, so P2 strictly folds and b32 = 0 is FORCED.")

hdr("3.  The refined face:  b32 = 0, c34 = 0.  Do the poles survive?")
print("   With b32 = 0, Table 3's c33 window becomes [1/2, b32max].\n")
print("   b11   b21  | c33 interval        width  | a11 edge   a41 edge  rho@mid(a11)")
for b11, b21 in ((.15, .15), (.10, .20), (.25, .25), (.20, .05), (.00, .00)):
    if b11 > b21 and b21 > min(b11, .5 - 2 * b11) + 1e-12:
        continue
    c11 = 0.0 if b11 <= b21 else 0.5
    lo, hi = F.c33_range(b11, b21, 0.0)
    out = []
    for nm, star in (("a11", lo), ("a41", hi)):
        g = K.exact_coord_derivative(F.make_profile(b11, b21, 0., 0., c11, star, 0.),
                                     I[nm])
        out.append("POLE" if abs(g[0]) < 1e-13 and abs(g[2]) > 1e-13 else "none")
    mid = K.exact_coord_derivative(
        F.make_profile(b11, b21, 0., 0., c11, (lo + hi) / 2, 0.), I["a11"])
    rm = "n/a" if abs(mid[0]) < 1e-13 else "%+.4f" % (-mid[2] / mid[0])
    print("   %.2f  %.2f | [%.4f, %.4f]   %.4f | %-9s %-9s %s"
          % (b11, b21, lo, hi, hi - lo, out[0], out[1], rm))

mx = 0.0
for b11, b21 in ((.15, .15), (.10, .20), (.25, .25), (.20, .05)):
    c11 = 0.0 if b11 <= b21 else 0.5
    lo, hi = F.c33_range(b11, b21, 0.0)
    for t in np.linspace(0, 1, 21):
        mx = max(mx, np.abs(K.exploitability(
            F.make_profile(b11, b21, 0., 0., c11, lo + t * (hi - lo), 0.))).max())
print("\n   max exploitability on the refined face = %.2e" % mx)
print("   -> it is a sub-family of Table 3, still exactly Nash.")

q = F.make_profile(.15, .15, 0., 0., .25, .6, 0.)
q[I["a11"]] = 0.5
print("\n   reach(c44) after a11 = 0.5, with b32 = 0 forced: %.1f" % K.reach(q)[I["c44"]])
print("   -> c44 becomes genuinely INERT; the refinement removes it from the")
print("      numerator as well.")

vals = []
for b11, b21 in ((.15, .15), (.10, .20), (.25, .25), (.20, .05), (.05, .22)):
    if b11 > b21 and b21 > min(b11, .5 - 2 * b11) + 1e-12:
        continue
    c11 = 0.0 if b11 <= b21 else 0.5
    lo, hi = F.c33_range(b11, b21, 0.0)
    for t in np.linspace(0.02, 1.0, 50):
        g = K.exact_coord_derivative(
            F.make_profile(b11, b21, 0., 0., c11, lo + t * (hi - lo), 0.), I["a11"])
        if abs(g[0]) > 1e-13:
            vals.append(-g[2] / g[0])
v = np.array(vals)
print("\n   rho for +e_a11 on the refined face (%d points): [%.4f, %.4f]"
      % (len(v), v.min(), v.max()))
print("   sign flips: %s   (unrefined range was [-48.75, +22.00], which DID flip)"
      % bool((v > 0).any() and (v < 0).any()))
print("\n   VERDICT: refinement kills the NUMERATOR indeterminacy (c34, c44, b32)")
print("   and removes rho's sign ambiguity, but leaves the c33 interval -- the")
print("   DENOMINATOR source -- intact, so both poles survive.")
