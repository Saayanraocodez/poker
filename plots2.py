"""
Figure 4: why P1 is the only player exposed to off-path indeterminacy.

Off-path parameters are not arbitrary -- they are the threats that keep some
OTHER player off the path.  What matters is whether that deterrence constraint
binds with slack (an interval, leaving residual freedom) or with equality (a
point, leaving none).  Both ends of P1's interval are attainable, and each end
is a pole of rho for a different P1 opening deviation.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import kuhn3p as K
import family as F

I = K.NAME_IDX
plt.rcParams.update({"figure.dpi": 130, "font.size": 8.5,
                     "axes.grid": True, "grid.alpha": .3,
                     "axes.titlesize": 9, "legend.fontsize": 7.2})

b11 = b21 = 0.15
b32 = 0.40
lo, hi = F.c33_range(b11, b21, b32)
cs = np.linspace(max(0, lo - .12), min(1, hi + .12), 401)


def prof(c33):
    return F.make_profile(b11, b21, 0., b32, .25, c33, .5)


def rho1(c33, name):
    g = K.exact_coord_derivative(prof(c33), I[name])
    return np.nan if abs(g[0]) < 1e-13 else -g[2] / g[0]


g11 = np.array([K.exact_coord_derivative(prof(c), I["a11"])[0] for c in cs])
g41 = np.array([K.exact_coord_derivative(prof(c), I["a41"])[0] for c in cs])
ex1 = np.array([K.exploitability(prof(c))[0] for c in cs])

fig, ax = plt.subplots(1, 3, figsize=(11.5, 3.6), constrained_layout=True)

# ---- (a) the deterrence window -------------------------------------------
a = ax[0]
a.axvspan(lo, hi, color="tab:green", alpha=.11, lw=0)
a.plot(cs, g11, color="tab:red", lw=1.7, label=r"$du_1/da_{11}$  (= $du_1/da_{21}$)")
a.plot(cs, g41, color="tab:purple", lw=1.7, label=r"$du_1/da_{41}$")
a.axhline(0, color="k", lw=.8)
a.axvline(lo, color="tab:green", lw=1.1, ls="--")
a.axvline(hi, color="tab:green", lw=1.1, ls="--")
a.set_title("Table 3's $c_{33}$ interval IS P1's deterrence window\n"
            r"$b_{11}=b_{21}=0.15,\ b_{32}=0.40$")
a.set_xlabel(r"$c_{33}$  (an information set nobody ever reaches)")
a.set_ylabel("P1's incentive to open")
a.legend(loc="center left")
a.text(lo, a.get_ylim()[1] * .80, r" $\frac{1}{2}-b_{32}$", color="tab:green",
       fontsize=8.5, ha="left")
a.text(hi, a.get_ylim()[0] * .80, "upper edge ", color="tab:green",
       fontsize=8.5, ha="right")

# ---- (b) rho across the window: a pole at EACH endpoint --------------------
b = ax[1]
sel = (cs >= lo) & (cs <= hi)
r11 = np.array([rho1(c, "a11") for c in cs[sel]])
r41 = np.array([rho1(c, "a41") for c in cs[sel]])
r31 = np.array([rho1(c, "a31") for c in cs[sel]])
b.axvspan(lo, hi, color="tab:green", alpha=.11, lw=0)
b.plot(cs[sel], r11, color="tab:red", lw=1.9,
       label=r"$+e_{a_{11}}$ (opens the 1) $\rightarrow$ pole at LOW edge")
b.plot(cs[sel], r41, color="tab:purple", lw=1.9,
       label=r"$+e_{a_{41}}$ (opens the 4) $\rightarrow$ pole at HIGH edge")
b.plot(cs[sel], r31, color="tab:blue", lw=1.7, ls="--",
       label=r"$+e_{a_{31}}$ (opens the 3) $\rightarrow$ no pole, ever")
b.axhline(0, color="k", lw=.8)
b.set_ylim(-12, 12)
b.set_title("Each endpoint is a pole for a DIFFERENT deviation\n"
            r"($a_{21}$ coincides with $a_{11}$ exactly)")
b.set_xlabel(r"$c_{33}$")
b.set_ylabel(r"$\rho=-(du_3/d\epsilon)/(du_1/d\epsilon)$")
b.legend(loc="upper center", fontsize=6.6)
b.annotate("", xy=(lo, -10.6), xytext=(lo + .045, -10.6),
           arrowprops=dict(arrowstyle="->", color="tab:red", lw=1.2))
b.text(lo + .05, -10.6, r"$du_1/da_{11}\rightarrow 0$", color="tab:red",
       fontsize=7, va="center")
b.annotate("", xy=(hi, 10.6), xytext=(hi - .045, 10.6),
           arrowprops=dict(arrowstyle="->", color="tab:purple", lw=1.2))
b.text(hi - .05, 10.6, r"$du_1/da_{41}\rightarrow 0$", color="tab:purple",
       fontsize=7, va="center", ha="right")

# ---- (c) interval vs point ------------------------------------------------
c = ax[2]
c.plot(cs, ex1, color="tab:red", lw=1.9,
       label=r"float $c_{33}$  (P1's off-path set)")
p0 = F.make_profile(0., 0., 0., 0., 0., .5, 0.)          # beta = 0
vs = np.linspace(0, 1, 401)
ex2 = np.array([np.abs(K.exploitability(
    np.where(np.arange(48) == I["a33"], v, p0))).max() for v in vs])
c.plot(vs, ex2, color="tab:blue", lw=1.9, ls="--",
       label=r"float $a_{33}$ at $\beta=0$  (P2's off-path set)")
c.axvspan(lo, hi, color="tab:green", alpha=.11, lw=0)
c.plot([0.5], [0], "o", color="tab:blue", ms=6, zorder=5)
c.set_title("Slack vs. no slack\nan interval of equilibria, or a single point")
c.set_xlabel("parameter value")
c.set_ylabel("max exploitability")
c.set_ylim(-.006, .12)
c.legend(loc="upper center")
c.text(.5, .011, "point", color="tab:blue", fontsize=8, ha="center")
c.text((lo + hi) / 2, .011, "interval", color="tab:red", fontsize=8, ha="center")

fig.suptitle("Off-path parameters are the threats that keep somebody else off "
             r"the path — both ends of P1's deterrence window are a pole for $\rho$",
             fontsize=10)
fig.savefig("fig4_offpath_deterrence.png", bbox_inches="tight")
print("wrote fig4_offpath_deterrence.png")
