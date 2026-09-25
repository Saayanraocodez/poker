"""
A fully hand-reproducible grid point.

Grid point:  sub-family A (c11 = 0) with b11 = b21 = 0, so beta = 0,
             b23 = 0, b32 = 0, c33 = 1/2, c34 = 0.
Player A  :  P2.
Direction :  d_A = +e_{b31}  (P2 starts betting the 3 after P1 checks;
             the family says b31 = 0, so +e is the only feasible direction).

Only the 6 deals in which P2 holds the 3 can be affected, so the whole
directional derivative is a 6-row hand calculation.
"""
from fractions import Fraction as Fr

import numpy as np

import kuhn3p as K
import family as F

I = K.NAME_IDX
p, meta = F.profile_A(0.0, 0.0, t_b32=0.0, t_c33=0.0, c34=0.0)

print("=" * 78)
print("THE GRID POINT")
print("=" * 78)
print("  sub-family A (c11 = 0),  b11 = b21 = 0  =>  beta = 0")
for pl, ch in enumerate("abc"):
    for j in K.CARDS:
        row = ["%s%d%d=%s" % (ch, j, k,
                              Fr(p[K.pidx(pl, j, k)]).limit_denominator(64))
               for k in K.SITUATIONS]
        print("     " + "  ".join("%-10s" % r for r in row))
    print()
u = K.utilities(p)
print("  u = (%s, %s, %s)  =  (%.6f, %.6f, %.6f)"
      % (Fr(u[0]).limit_denominator(10**5), Fr(u[1]).limit_denominator(10**5),
         Fr(u[2]).limit_denominator(10**5), u[0], u[1], u[2]))
print("  Table 3 predicts u = (-k(1/2+0), -k/2, k(1+0)) = (-1/48, -1/48, 1/24)")
print()
print("  In words: P1 never bets and never calls except with the 4 (and calls")
print("  half the time with the 3 when P2 bet and P3 folded).  P2 never bets.")
print("  P3 bets the 4 always and the 2 half the time after two checks;")
print("  everyone else checks.  Nobody ever faces a bet from P1 or P2, so")
print("  b32, c33, c34 are never reached.")

# --------------------------------------------------------------------------
# per-deal breakdown of the b31 deviation, in exact arithmetic
# --------------------------------------------------------------------------
print()
print("=" * 78)
print("DIRECTIONAL DERIVATIVE OF THE b31 DEVIATION, DEAL BY DEAL")
print("=" * 78)
print("  d u_i / d b31 = (1/24) * SUM over the 6 deals with P2 holding the 3")
print("                  of  [ payoff if P2 BETS  -  payoff if P2 CHECKS ]")
print()

i31 = I["b31"]
p_bet, p_chk = p.copy(), p.copy()
p_bet[i31], p_chk[i31] = 1.0, 0.0

# per-deal expected payoff vectors, conditional on the deal
mask3 = K.HOLDER[:, 1] == 3
deals = sorted({tuple(K.HOLDER[r]) for r in range(K.NLEAF) if mask3[r]})


def deal_value(prof, deal):
    q = np.append(prof, 1.0)
    sel = np.all(K.HOLDER == np.array(deal), axis=1)
    w = np.where(K.AGG[sel], q[K.IDX[sel]], 1 - q[K.IDX[sel]]).prod(axis=1)
    return (w[:, None] * K.PAY[sel]).sum(axis=0)      # conditional on the deal


def fr(x):
    return str(Fr(x).limit_denominator(64))


print("   deal          P2 BETS                P2 CHECKS            "
      "  difference")
print("  (P1,P2,P3)   (u1, u2, u3)           (u1, u2, u3)           "
      "(du1,du2,du3)")
print("  " + "-" * 74)
tot = np.zeros(3)
for d in deals:
    vb, vc = deal_value(p_bet, d), deal_value(p_chk, d)
    df = vb - vc
    tot += df
    print("  %s  (%5s,%5s,%5s)   (%5s,%5s,%5s)   (%5s,%5s,%5s)"
          % (d, fr(vb[0]), fr(vb[1]), fr(vb[2]),
             fr(vc[0]), fr(vc[1]), fr(vc[2]),
             fr(df[0]), fr(df[1]), fr(df[2])))
print("  " + "-" * 74)
print("  %-12s %-22s %-22s (%5s,%5s,%5s)"
      % ("SUM", "", "", fr(tot[0]), fr(tot[1]), fr(tot[2])))
print()
print("  d u / d b31 = (1/24) * (%s, %s, %s) = (%s, %s, %s)"
      % (fr(tot[0]), fr(tot[1]), fr(tot[2]),
         fr(tot[0] / 24), fr(tot[1] / 24), fr(tot[2] / 24)))
print("              = (%+.6f, %+.6f, %+.6f)" % tuple(tot / 24))

fd = K.central_diff(p, np.eye(K.NPARAM)[i31], 1e-5)
ex = K.exact_coord_derivative(p, i31)
print()
print("  engine, central finite difference (h=1e-5): (%+.8f, %+.8f, %+.8f)"
      % tuple(fd))
print("  engine, exact multilinear derivative      : (%+.8f, %+.8f, %+.8f)"
      % tuple(ex))
print("  hand calculation                          : (%+.8f, %+.8f, %+.8f)"
      % tuple(tot / 24))
print("  max discrepancy: %.3e" % max(np.abs(fd - tot / 24).max(),
                                      np.abs(ex - tot / 24).max()))
print()
print("  zero-sum check:  du1 + du2 + du3 = %s + %s + %s = %s"
      % (fr(tot[0] / 24), fr(tot[1] / 24), fr(tot[2] / 24),
         fr(tot.sum() / 24)))
print()
print("  A = P2  =>  B = P3, C = P1   (cyclic convention)")
print("  rho = -(du_C/de)/(du_A/de) = -(du_1)/(du_2) = -(%s)/(%s) = %s = %.4f"
      % (fr(tot[0] / 24), fr(tot[1] / 24), fr(-tot[0] / tot[1]),
         -tot[0] / tot[1]))
print("  complementary share  rho_{P2->P3} = -(du_3)/(du_2) = %s = %.4f"
      % (fr(-tot[2] / tot[1]), -tot[2] / tot[1]))
print("  the two shares sum to %s, as they must (zero sum)."
      % fr((-tot[0] - tot[2]) / tot[1]))
print()
print("  P2 pays 2.5/24 chips per unit of eps; 1.5/24 (60%) of that lands on")
print("  P1 and 1.0/24 (40%) on P3.  The denominator is strictly negative, so")
print("  rho is well defined HERE -- and it stays exactly 3/5 over the whole")
print("  family (see the sweep).")
