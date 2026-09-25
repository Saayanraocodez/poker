"""
The Szafron / Gibson / Sturtevant (AAMAS 2013) parameterized family of
equilibrium profiles for three-player Kuhn poker.

Transcribed verbatim from:
    D. Szafron, R. Gibson, N. Sturtevant, "A Parameterized Family of
    Equilibrium Profiles for Three-Player Kuhn Poker", AAMAS 2013, pp.247-254.
    https://www.ifaamas.org/Proceedings/aamas2013/docs/p247.pdf

TABLE 2  (the 21 necessary parameter values)
    a12 = a13 = a14 = a24 = 0        a42 = a43 = a44 = 1
    b12 = b13 = b14 = b24 = 0        b42 = b43 = b44 = 1
    c12 = c13 = c14 = c24 = 0        c42 = c43 = c44 = 1

TABLE 3  (the family; beta = max{b11, b21}, kappa = 1/24)
    P1                    P2                                     P3
    a11 = 0               b11 <= b21              if c11 = 0     c11 <= min{1/2,
    a21 = 0               b11 <= 1/4              if c11 != 0           (2 - b11)
    a22 = 0               b21 <= 1/4              if c11 = 0        / (3 + 2 b11
    a23 = 0               b21 = b11               if 0<c11<1/2         + 2 b21)}
    a31 = 0               b21 <= min{b11, 1/2 - 2 b11} if c11 = 1/2
    a32 = 0               b22 = 0                                c21 = 1/2 - c11
    a33 = 1/2             b23 <= max{0, (b11 - b21) / (2(1-b21))} c22 = 0
    a34 = 0               b31 = 0                                c23 = 0
    a41 = 0               b32 <= 1/2 + (3/4)(b11+b21) + beta/4   c31 = 0
                          b33 = 1/2 + (b11+b21)/2 + beta/2       c32 = 0
                                     - b23 (1 - b21)             1/2 - b32 <= c33
                          b34 = 0                                  <= 1/2 - b32
                          b41 = 2 b11 + 2 b21                      + (3/4)(b11+b21)
                                                                   + beta/4
                                                                 0 <= c34 <= 1
                                                                 c41 = 1

    u1 = -kappa (1/2 + beta)      u2 = -kappa (1/2)      u3 = kappa (1 + beta)

Three sub-families, distinguished by c11 (paper, Section 5):
    'A' : c11 = 0          free: b11, b21, b32, c33   (+ c34);  beta = b21
    'B' : 0 < c11 < 1/2    free: b11, c11, b32, c33   (+ c34);  beta = b11 = b21
    'C' : c11 = 1/2        free: b11, b21, b23, b32, c33 (+ c34); beta = b11
"""

import numpy as np

import kuhn3p as K

I = K.NAME_IDX
TOL = 1e-12


def _blank():
    return np.full(K.NPARAM, np.nan)


def table2(p):
    """Apply the 21 necessary values of Table 2."""
    for n in ("a12", "a13", "a14", "a24",
              "b12", "b13", "b14", "b24",
              "c12", "c13", "c14", "c24"):
        p[I[n]] = 0.0
    for n in ("a42", "a43", "a44",
              "b42", "b43", "b44",
              "c42", "c43", "c44"):
        p[I[n]] = 1.0
    return p


def beta_of(b11, b21):
    return max(b11, b21)


def b33_of(b11, b21, b23):
    """Table 3:  b33 = 1/2 + (b11+b21)/2 + beta/2 - b23 (1 - b21)."""
    return 0.5 + (b11 + b21) / 2.0 + beta_of(b11, b21) / 2.0 - b23 * (1.0 - b21)


def b32_max(b11, b21):
    """Table 3:  b32 <= 1/2 + (3/4)(b11 + b21) + beta/4."""
    return 0.5 + 0.75 * (b11 + b21) + beta_of(b11, b21) / 4.0


def c33_range(b11, b21, b32):
    """Table 3:  1/2 - b32 <= c33 <= 1/2 - b32 + (3/4)(b11+b21) + beta/4."""
    lo = 0.5 - b32
    hi = b32_max(b11, b21) - b32
    return max(0.0, lo), min(1.0, hi)


def c11_max(b11, b21):
    """Table 3:  c11 <= min{1/2, (2 - b11) / (3 + 2 b11 + 2 b21)}."""
    return min(0.5, (2.0 - b11) / (3.0 + 2.0 * b11 + 2.0 * b21))


def b23_max(b11, b21):
    """Table 3:  b23 <= max{0, (b11 - b21) / (2 (1 - b21))}."""
    return max(0.0, (b11 - b21) / (2.0 * (1.0 - b21)))


def make_profile(b11, b21, b23, b32, c11, c33, c34):
    """Build the full 48-vector from Table 2 + Table 3 (no validity check)."""
    p = table2(_blank())
    # ---- P1: completely determined, no free parameters -------------------
    for n in ("a11", "a21", "a22", "a23", "a31", "a32", "a34", "a41"):
        p[I[n]] = 0.0
    p[I["a33"]] = 0.5
    # ---- P2 ---------------------------------------------------------------
    p[I["b11"]] = b11
    p[I["b21"]] = b21
    p[I["b22"]] = 0.0
    p[I["b23"]] = b23
    p[I["b31"]] = 0.0
    p[I["b32"]] = b32
    p[I["b33"]] = b33_of(b11, b21, b23)
    p[I["b34"]] = 0.0
    p[I["b41"]] = 2.0 * b11 + 2.0 * b21
    # ---- P3 ---------------------------------------------------------------
    p[I["c11"]] = c11
    p[I["c21"]] = 0.5 - c11
    p[I["c22"]] = 0.0
    p[I["c23"]] = 0.0
    p[I["c31"]] = 0.0
    p[I["c32"]] = 0.0
    p[I["c33"]] = c33
    p[I["c34"]] = c34
    p[I["c41"]] = 1.0
    assert not np.any(np.isnan(p)), "profile incomplete"
    return p


def violations(b11, b21, b23, b32, c11, c33, c34, subfamily):
    """Return the list of Table 3 constraints violated by these values."""
    v = []
    beta = beta_of(b11, b21)

    def chk(cond, msg):
        if not cond:
            v.append(msg)

    chk(0 <= b11 <= 1, "b11 in [0,1]")
    chk(0 <= b21 <= 1, "b21 in [0,1]")
    chk(0 <= b23 <= 1, "b23 in [0,1]")
    chk(0 <= b32 <= 1, "b32 in [0,1]")
    chk(0 <= c11 <= 1, "c11 in [0,1]")
    chk(0 <= c34 <= 1, "c34 in [0,1]")

    if subfamily == "A":
        chk(abs(c11) <= TOL, "sub-family A needs c11 = 0")
        chk(b11 <= b21 + TOL, "c11=0 => b11 <= b21")
        chk(b21 <= 0.25 + TOL, "c11=0 => b21 <= 1/4")
        chk(abs(b23) <= TOL, "c11=0 => b23 = 0")
    elif subfamily == "B":
        chk(TOL < c11 < 0.5 - TOL, "sub-family B needs 0 < c11 < 1/2")
        chk(abs(b21 - b11) <= TOL, "0<c11<1/2 => b21 = b11")
        chk(b11 <= 0.25 + TOL, "c11!=0 => b11 <= 1/4")
        chk(abs(b23) <= TOL, "0<c11<1/2 => b23 = 0")
    elif subfamily == "C":
        chk(abs(c11 - 0.5) <= TOL, "sub-family C needs c11 = 1/2")
        chk(b11 <= 0.25 + TOL, "c11!=0 => b11 <= 1/4")
        chk(b21 <= min(b11, 0.5 - 2 * b11) + TOL,
            "c11=1/2 => b21 <= min{b11, 1/2 - 2 b11}")
    else:
        v.append("unknown sub-family")

    chk(b23 <= b23_max(b11, b21) + TOL, "b23 <= max{0,(b11-b21)/(2(1-b21))}")
    chk(c11 <= c11_max(b11, b21) + TOL,
        "c11 <= min{1/2,(2-b11)/(3+2b11+2b21)}")
    chk(b32 <= b32_max(b11, b21) + TOL, "b32 <= 1/2+3(b11+b21)/4+beta/4")
    lo, hi = 0.5 - b32, b32_max(b11, b21) - b32
    chk(lo - TOL <= c33 <= hi + TOL, "1/2-b32 <= c33 <= 1/2-b32+3(b11+b21)/4+beta/4")

    b33 = b33_of(b11, b21, b23)
    b41 = 2 * b11 + 2 * b21
    # TOL here for the same reason every other check in this function has it:
    # at b11 = b21 = 1/4, b41 = 2(b11+b21) is exactly 1 and rounds to 1 + 1e-12,
    # so an exact-bound check calls the family's own corner a violation.
    chk(-TOL <= b33 <= 1 + TOL, "b33 in [0,1]")
    chk(-TOL <= b41 <= 1 + TOL, "b41 in [0,1]")
    chk(-TOL <= 0.5 - c11 <= 1 + TOL, "c21 = 1/2 - c11 in [0,1]")
    return v


def predicted_utilities(b11, b21):
    """Table 3:  u1 = -k(1/2+beta),  u2 = -k/2,  u3 = k(1+beta)."""
    beta = beta_of(b11, b21)
    k = K.KAPPA
    return np.array([-k * (0.5 + beta), -k * 0.5, k * (1.0 + beta)])


# --------------------------------------------------------------------------
# Convenient sub-family constructors: all free parameters given on [0,1] where
# their valid range is an interval, so a grid sweep is easy and always legal.
# --------------------------------------------------------------------------
def profile_A(b11, b21, t_b32=0.0, t_c33=0.0, c34=0.0):
    """c11 = 0.  Requires 0 <= b11 <= b21 <= 1/4."""
    b23 = 0.0
    b32 = t_b32 * b32_max(b11, b21)
    lo, hi = c33_range(b11, b21, b32)
    c33 = lo + t_c33 * (hi - lo)
    return make_profile(b11, b21, b23, b32, 0.0, c33, c34), dict(
        b11=b11, b21=b21, b23=b23, b32=b32, c11=0.0, c33=c33, c34=c34,
        subfamily="A")


def profile_B(b11, c11, t_b32=0.0, t_c33=0.0, c34=0.0):
    """0 < c11 < 1/2.  Requires b21 = b11 <= 1/4 and c11 <= c11_max."""
    b21, b23 = b11, 0.0
    b32 = t_b32 * b32_max(b11, b21)
    lo, hi = c33_range(b11, b21, b32)
    c33 = lo + t_c33 * (hi - lo)
    return make_profile(b11, b21, b23, b32, c11, c33, c34), dict(
        b11=b11, b21=b21, b23=b23, b32=b32, c11=c11, c33=c33, c34=c34,
        subfamily="B")


def profile_C(b11, b21, t_b23=0.0, t_b32=0.0, t_c33=0.0, c34=0.0):
    """c11 = 1/2.  Requires b11 <= 1/4 and b21 <= min{b11, 1/2 - 2 b11}."""
    b23 = t_b23 * b23_max(b11, b21)
    b32 = t_b32 * b32_max(b11, b21)
    lo, hi = c33_range(b11, b21, b32)
    c33 = lo + t_c33 * (hi - lo)
    return make_profile(b11, b21, b23, b32, 0.5, c33, c34), dict(
        b11=b11, b21=b21, b23=b23, b32=b32, c11=0.5, c33=c33, c34=c34,
        subfamily="C")
