"""Control: does any of this survive into TWO-player Kuhn poker?"""
from fractions import Fraction as Fr

import numpy as np

import kuhn2p as T


def hdr(s):
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


hdr("0.  Engine + family checks")
print("   leaves: %d = %d per deal x %d deals" % (T.NLEAF, T.NLEAF // 6, 6))
print("   every leaf zero-sum: %s" % bool(np.all(np.abs(T.PAY.sum(1)) < 1e-12)))
rng = np.random.default_rng(0)
print("   sum u_i on random profiles: %s"
      % ["%.1e" % T.utilities(rng.random(12)).sum() for _ in range(3)])

AL = np.linspace(0, 1 / 3, 201)
U = np.array([T.utilities(T.family(a)) for a in AL])
E = np.array([T.exploitability(T.family(a)) for a in AL])
print("   201 alphas in [0,1/3]: max exploitability = %.3e -> all Nash" % E.max())
print("   u1 range over the family: [%.12f, %.12f]   (-1/18 = %.12f)"
      % (U[:, 0].min(), U[:, 0].max(), -1 / 18))
print("   u1 SPREAD across the whole family = %.3e" % (U[:, 0].max() - U[:, 0].min()))
pf = [Fr(x).limit_denominator(10**6) for x in T.family(1 / 6)]
print("   exact rational check at alpha=1/6: u = %s"
      % (tuple(str(x) for x in T.utilities_exact(pf)),))
for a in (-0.02, 1 / 3 + 0.02):
    print("   alpha = %+.4f (outside [0,1/3]): max exploitability = %.6f"
          % (a, T.exploitability(T.family(a)).max()))

hdr("1.  COSTLESS TRANSFER DIRECTIONS: can they exist at all?")
n_costless, n_null, n_costly = 0, 0, 0
worst_zs = 0.0
for a in AL:
    p = T.family(a)
    for i in range(12):
        for s in (+1.0, -1.0):
            if (s > 0 and p[i] > 1 - 1e-12) or (s < 0 and p[i] < 1e-12):
                continue
            du = s * T.exact_coord_derivative(p, i)
            worst_zs = max(worst_zs, abs(du.sum()))
            A = 0 if i < 6 else 1
            B = 1 - A
            if abs(du[A]) <= 1e-12:
                if abs(du[B]) > 1e-12:
                    n_costless += 1
                else:
                    n_null += 1
            else:
                n_costly += 1
print("   over 201 alphas x every feasible single-coordinate direction:")
print("      strictly costly (du_A < 0)          : %d" % n_costly)
print("      du_A = 0 AND opponent moves         : %d   <-- costless transfers" % n_costless)
print("      du_A = 0 and nothing moves (null)   : %d" % n_null)
print("      max |du_1 + du_2|                   : %.3e" % worst_zs)
print("\n   This is forced: with two players zero-sum gives du_2 = -du_1 identically,")
print("   so du_A = 0 implies du_B = 0.  A costless transfer needs a THIRD party.")

hdr("2.  rho, and whether any pole exists")
rhos, mins = [], []
for a in AL:
    p = T.family(a)
    for i in range(12):
        du = T.exact_coord_derivative(p, i)
        A = 0 if i < 6 else 1
        if abs(du[A]) > 1e-12:
            rhos.append(-du[1 - A] / du[A])
            mins.append(abs(du[A]))
rhos = np.array(rhos)
print("   rho = -(du_other/d eps)/(du_A/d eps) over %d defined (point,direction) pairs"
      % len(rhos))
print("      range = [%.15f, %.15f]" % (rhos.min(), rhos.max()))
print("      identically 1?  %s" % bool(np.all(np.abs(rhos - 1) < 1e-12)))
print("      min |du_A| among defined = %.3e   -> rho stays exactly 1 regardless"
      % min(mins))
print("   No pole is possible: the numerator and denominator are the SAME number")
print("   up to sign, so they vanish together.  rho is 1 or 0/0, never unbounded.")

hdr("3.  OFF-PATH PARAMETERS and DETERRENCE SLACK")
print("   reach of each information set across the family:")
R = np.array([T.reach(T.family(a)) for a in AL])
print("   param   reach@alpha=0   reach@alpha=1/3   never reached anywhere?")
never = []
for i in range(12):
    nv = R[:, i].max() < 1e-12
    if R[:, i].min() < 1e-12:
        never.append(T.NAME[i])
    print("   %-6s  %.6f        %.6f          %s"
          % (T.NAME[i], R[0, i], R[-1, i], "yes" if nv else "no"))
print("\n   -> the off-path region exists ONLY at the single endpoint alpha = 0,")
print("      where P1 never bets and P2's calling parameters y_j2 go unreached.")
print("      In 3-player Kuhn P1 never bets for the WHOLE family, so that region")
print("      is family-wide, not an endpoint.")

print("\n   Is there SLACK in those off-path parameters at alpha = 0?")
print("   (sweep each one over [0,1], everything else fixed; an INTERVAL of zero")
print("    exploitability = slack, a single point = none)")
p0 = T.family(0.0)
for nm in ("y12", "y22", "y32"):
    i = T.IDX_OF[nm]
    vs = np.linspace(0, 1, 401)
    ex = []
    for v in vs:
        pp = p0.copy()
        pp[i] = v
        ex.append(T.exploitability(pp).max())
    ex = np.array(ex)
    ok = vs[ex < 1e-12]
    span = (ok.max() - ok.min()) if len(ok) else 0.0
    print("      %-4s : zero-exploitability set = [%.4f, %.4f], width %.4f  (%s)"
          % (nm, ok.min() if len(ok) else np.nan, ok.max() if len(ok) else np.nan,
             span, "INTERVAL - slack" if span > 1e-9 else "single point - no slack"))

print("\n   And with slack present, is anything transferable there?")
for nm in ("y12", "y22", "y32"):
    i = T.IDX_OF[nm]
    du = T.exact_coord_derivative(p0, i)
    print("      du/d%-4s at alpha=0 = (%+.8f, %+.8f)" % (nm, du[0], du[1]))

hdr("4.  THE CONTRAST WITH THREE PLAYERS")
import kuhn3p as K
import family as F
print("   utilities across the equilibrium family:")
print("      2-player: u1 = %s for every alpha in [0,1/3]   (spread %.2e)"
      % (Fr(U[0, 0]).limit_denominator(1000), U[:, 0].max() - U[:, 0].min()))
u3 = np.array([K.utilities(F.profile_A(b, b, .5, .5, 0.)[0])
               for b in np.linspace(0, .25, 51)])
print("      3-player: u1 = -k(1/2+beta) ranges over [%.6f, %.6f]  (spread %.4f)"
      % (u3[:, 0].min(), u3[:, 0].max(), u3[:, 0].max() - u3[:, 0].min()))
print("                u3 = +k(1+beta)  ranges over [%.6f, %.6f]  (spread %.4f)"
      % (u3[:, 2].min(), u3[:, 2].max(), u3[:, 2].max() - u3[:, 2].min()))
print("                u2 = -k/2 constant                              (spread %.2e)"
      % (u3[:, 1].max() - u3[:, 1].min()))
print("\n   Two-player zero-sum equilibria are INTERCHANGEABLE: every member of the")
print("   family pays exactly -1/18.  The three-player family is not: moving beta")
print("   moves kappa*beta from P1 to P3 while P2 is unaffected.  That is the")
print("   guarantee that is lost, and it is what makes rho a meaningful quantity")
print("   at all -- with two players rho is 1 by arithmetic, with nothing to measure.")
