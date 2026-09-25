"""Exploratory pass: what does the derivative landscape look like?"""
import numpy as np

import kuhn3p as K
import family as F
import directions as D

np.set_printoptions(precision=6, suppress=True)

POINTS = [
    ("A  b11=.10 b21=.20 t_b32=.5 t_c33=.5",
     F.profile_A(0.10, 0.20, 0.5, 0.5, 0.3)),
    ("A  b11=.25 b21=.25 t_b32=.5 t_c33=.5",
     F.profile_A(0.25, 0.25, 0.5, 0.5, 0.3)),
    ("A  b11=0   b21=0   t_b32=.5 t_c33=.5",
     F.profile_A(0.0, 0.0, 0.5, 0.5, 0.3)),
    ("A  b11=.10 b21=.20 t_c33=0 (lower edge)",
     F.profile_A(0.10, 0.20, 0.5, 0.0, 0.3)),
    ("A  b11=.10 b21=.20 t_c33=1 (upper edge)",
     F.profile_A(0.10, 0.20, 0.5, 1.0, 0.3)),
    ("B  b11=.15 c11=.25 t_b32=.5 t_c33=.5",
     F.profile_B(0.15, 0.25, 0.5, 0.5, 0.3)),
    ("C  b11=.20 b21=.05 t_b23=.5 t_c33=.5",
     F.profile_C(0.20, 0.05, 0.5, 0.5, 0.5, 0.3)),
]

for label, (p, meta) in POINTS:
    print("\n" + "=" * 92)
    print(label)
    print("   u =", K.utilities(p), "  beta =", F.beta_of(meta["b11"], meta["b21"]))
    print("   exploitability =", K.exploitability(p))
    for A in range(3):
        rows = D.scan(p, A)
        strict = [r for r in rows if r["dA"] > D.TOL]
        costly = [r for r in rows if r["dA"] < -D.TOL]
        free = [r for r in rows if abs(r["dA"]) <= D.TOL]
        freemove = [r for r in free if np.abs(r["fd"]).max() > D.TOL]
        print("   --- A = %s :  %d feasible dirs | improving %d | costly %d |"
              " neutral-for-A %d (of which %d move the others)"
              % (D.PLAYER_NAME[A], len(rows), len(strict), len(costly),
                 len(free), len(freemove)))
        for r in sorted(costly, key=lambda r: -r["dA"])[:6]:
            print("        costly  %-5s %+d  du=%s  fd_err=%.1e"
                  % (r["param"], r["sign"], np.round(r["fd"], 8), r["fd_err"]))
        for r in freemove:
            print("        FREE    %-5s %+d  du=%s"
                  % (r["param"], r["sign"], np.round(r["fd"], 8)))
