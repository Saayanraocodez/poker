"""
Does an equilibrium REFINEMENT collapse rho's indeterminacy?

The indeterminacy lives entirely at information sets of reach probability zero
(b32, c33, c34, c44), which are unreached because P1 never bets.  Nash imposes
nothing there.  Refinements (Selten 1975 trembling-hand, Kreps-Wilson 1982
sequential) do: they require the OWNER of each such set to act optimally given
beliefs obtained as a limit of fully-mixed play.

Method.  Perturb P1's opening with trembles a_{j1} = eps * r_j, r a ratio
vector.  Every information set then has positive reach, so the owner's optimal
action at each off-path set is decided by the sign of du_owner/dx, and the
belief there is an explicit function of r.  We ask, for each off-path
parameter: what does the owner want, and does that agree with Table 3?
"""
import itertools

import numpy as np

import kuhn3p as K
import family as F

I = K.NAME_IDX
KAP = K.KAPPA
PN = ("P1", "P2", "P3")
OWNER = {"b32": 1, "c33": 2, "c34": 2, "c44": 2}


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


def tremble(p, eps, r=(1., 1., 1., 1.)):
    q = p.copy()
    for j in range(1, 5):
        q[I["a%d1" % j]] = eps * r[j - 1]
    return q


def adv(p, name, eps, r):
    """Per-unit-reach advantage of the AGGRESSIVE action at `name`'s info set."""
    q = tremble(p, eps, r)
    g = K.exact_coord_derivative(q, I[name])[OWNER[name]]
    rr = K.reach(q)[I[name]]
    return (g / rr if rr > 1e-18 else np.nan), rr


# ===========================================================================
hdr("1.  What does the OWNER of each off-path set want, under a uniform tremble?")
base = dict(b11=.15, b21=.15, b23=0., b32=.40, c11=.25, c34=.5)
lo, hi = F.c33_range(base["b11"], base["b21"], base["b32"])
p = F.make_profile(c33=(lo + hi) / 2, **base)
print("   family point b11=b21=0.15, b32=0.40, c11=0.25, c34=0.5,")
print("   c33 = %.4f (midpoint of Table 3's interval [%.4f, %.4f])\n" % ((lo + hi) / 2, lo, hi))
print("   param  owner  reach@eps=1e-3   advantage of the aggressive action   -> wants")
for nm in ("b32", "c33", "c34", "c44"):
    a, rr = adv(p, nm, 1e-3, (1, 1, 1, 1))
    want = "1 (call)" if a > 1e-12 else ("0 (fold)" if a < -1e-12 else "indifferent")
    print("   %-5s  %s     %.3e        %+.8f                     %s"
          % (nm, PN[OWNER[nm]], rr, a, want))
print("\n   Table 3 says: b32 free in [0, %.4f], c33 free in [%.4f, %.4f],"
      % (F.b32_max(.15, .15), lo, hi))
print("   c34 free in [0,1]; Table 2 pins c44 = 1.")

# ===========================================================================
hdr("2.  Is the advantage tremble-independent, or does it hinge on the ratios?")
print("   P3 at BF holding the 3: pot is 4, folding costs 1, calling risks 2 to")
print("   win 3.  Calling beats folding iff  3q - 2(1-q) > -1, i.e. q > 1/5,")
print("   where q = P(P1 holds 1 or 2 | P1 bet, P2 folded, P3 holds the 3).\n")
print("   tremble ratio r = (r1,r2,r3,r4) on P1's opening      q        c33 adv     wants")
for r, lbl in (((1, 1, 1, 1), "uniform"),
               ((1, 1, 1, 0.5), "P1 rarely opens the 4"),
               ((1, 1, 1, 2), "P1 often opens the 4"),
               ((1, 1, 1, 4), "P1 much more often the 4"),
               ((0.5, 0.5, 1, 2), "half weight on 1,2"),
               ((1, 1, 1, 8), "extreme")):
    q = tremble(p, 1e-3, r)
    # belief q from the engine's reach decomposition
    w = {}
    for j in (1, 2, 4):
        qq = q.copy()
        for k in (1, 2, 3, 4):
            if k != j:
                qq[I["a%d1" % k]] = 0.0
        w[j] = K.reach(qq)[I["c33"]]
    tot = sum(w.values())
    qbel = (w[1] + w[2]) / tot if tot > 0 else np.nan
    a, _ = adv(p, "c33", 1e-3, r)
    want = "call" if a > 1e-12 else ("fold" if a < -1e-12 else "indifferent")
    print("   %-22s %-26s %.5f  %+.6f   %s"
          % (str(r), lbl, qbel, a, want))
print("\n   Indifference (q = 1/5) needs r4 = 2*(r1+r2).  Solve and check:")
r_star = (1, 1, 1, 4)
a, _ = adv(p, "c33", 1e-3, r_star)
print("      r = (1,1,1,4):  c33 advantage = %+.3e  -> %s"
      % (a, "INDIFFERENT" if abs(a) < 1e-12 else "not indifferent"))

# ===========================================================================
hdr("3.  So: does the refinement pin c33, and does the pole survive?")
print("   Under a GENERIC tremble ratio P3 strictly prefers one action, so")
print("   sequential rationality forces c33 to a CORNER:")
for r, lbl in (((1, 1, 1, 1), "uniform"), ((1, 1, 1, 8), "r4 large"),
               ((1, 1, 1, 2), "r4 = 2")):
    a, _ = adv(p, "c33", 1e-3, r)
    forced = 1.0 if a > 1e-12 else (0.0 if a < -1e-12 else None)
    inside = (forced is not None) and (lo - 1e-12 <= forced <= hi + 1e-12)
    print("      r=%-10s -> P3 forced to c33 = %s;  Table 3 interval is"
          " [%.4f, %.4f]  ->  %s"
          % (str(r), forced, lo, hi,
             "INSIDE" if inside else "OUTSIDE the family"))
print("\n   Only the knife-edge ratio r4 = 2(r1+r2) leaves P3 indifferent, and")
print("   only then is an interior c33 sequentially rational.")

print("\n   Does the knife-edge survive across the family?  (r = (1,1,1,4))")
print("      b11   b21   b32   | c33 interval        | c33 adv at midpoint")
for b11, b21, b32 in ((.15, .15, .40), (.00, .00, .00), (.25, .25, .00),
                      (.10, .20, .25), (.20, .05, .30)):
    if b32 > F.b32_max(b11, b21):
        continue
    l2, h2 = F.c33_range(b11, b21, b32)
    c11v = 0.0 if b11 <= b21 else 0.5
    if not (b11 <= b21 or b21 <= min(b11, .5 - 2 * b11)):
        continue
    pp = F.make_profile(b11, b21, 0., b32, c11v, (l2 + h2) / 2, .5)
    a, _ = adv(pp, "c33", 1e-3, (1, 1, 1, 4))
    print("      %.2f  %.2f  %.2f  | [%.4f, %.4f]    | %+.3e  %s"
          % (b11, b21, b32, l2, h2, a,
             "indifferent" if abs(a) < 1e-10 else "STRICT"))

# ===========================================================================
hdr("4.  Perturbed-game exploitability: does ANY family member survive?")
print("   Restrict every parameter to [eps, 1-eps] (Selten's perturbed game).")
print("   u_i is multilinear, so the constrained best response is attained at a")
print("   vertex of the box: enumerate {eps, 1-eps}^4 per card, exactly.\n")


def br_eps(p, player, eps):
    q = np.empty(K.NPARAM + 1)
    q[:K.NPARAM] = np.clip(p, eps, 1 - eps)
    q[K.DUMMY] = 1.0
    tot = 0.0
    for j in K.CARDS:
        si, sa, sp = K._SUB[(player, j)]
        sp = sp[:, player]
        own = [K.pidx(player, j, k) for k in K.SITUATIONS]
        best = None
        for bits in itertools.product((eps, 1 - eps), repeat=4):
            qq = q.copy()
            for i, b in zip(own, bits):
                qq[i] = b
            v = K.KAPPA * float((np.where(sa, qq[si], 1 - qq[si]).prod(axis=1) * sp).sum())
            best = v if best is None or v > best else best
        tot += best
    return tot


print("   eps        max_i (BR_i^eps - u_i^eps)   for the family midpoint profile")
for eps in (1e-1, 1e-2, 1e-3, 1e-4, 1e-5):
    pc = np.clip(p, eps, 1 - eps)
    u = K.utilities(pc)
    gap = max(br_eps(pc, i, eps) - u[i] for i in range(3))
    print("   %.0e    %.6e" % (eps, gap))
print("\n   For comparison, the same profile with c33 pushed to the corner P3")
print("   actually wants under a uniform tremble:")
a, _ = adv(p, "c33", 1e-3, (1, 1, 1, 1))
corner = 1.0 if a > 0 else 0.0
p_ref = F.make_profile(c33=corner, **base)
for eps in (1e-2, 1e-3, 1e-4):
    pc = np.clip(p_ref, eps, 1 - eps)
    u = K.utilities(pc)
    gap = max(br_eps(pc, i, eps) - u[i] for i in range(3))
    print("   c33=%.0f  eps=%.0e   gap = %.6e   (unperturbed exploitability %.1e,"
          " in Table 3 interval: %s)"
          % (corner, eps, gap, np.abs(K.exploitability(p_ref)).max(),
             lo - 1e-12 <= corner <= hi + 1e-12))

# ===========================================================================
hdr("5.  Consequence for rho")
print("   rho's poles for +e_a11 / +e_a21 sit at c33 = lo, and for +e_a41 at")
print("   c33 = hi.  A refinement that forces c33 to a single value removes the")
print("   interval, hence the attainable boundary, hence clause (ii) of the pole")
print("   criterion -- UNLESS the forced value is itself an endpoint.\n")
for nm, star in (("a11", lo), ("a41", hi)):
    g_int = K.exact_coord_derivative(F.make_profile(c33=(lo + hi) / 2, **base), I[nm])
    g_star = K.exact_coord_derivative(F.make_profile(c33=star, **base), I[nm])
    print("   %s: du1 at c33 midpoint = %+.8f (rho = %+.4f);"
          " at c33 = %.4f = %+.1e (pole)"
          % (nm, g_int[0], -g_int[2] / g_int[0], star, g_star[0]))
print("\n   And the knife-edge tremble that keeps interior c33 alive leaves the")
print("   WHOLE interval alive, endpoints included -- so the poles survive")
print("   exactly when the indeterminacy does.  Refinement does not separate them.")
