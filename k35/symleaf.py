"""EXACT algebraic decision for an enum6 leaf: is its support pattern empty of
equilibria, and if not, is everything in it the SGS family on path?

Why this exists.  Interval bisection (prove6pat, proveall) plateaus on leaves
that are FAMILY-ADJACENT: a pattern identical to one carrying an equilibrium
except that some coordinate the family holds at 0 (or 1) is labelled MIX.  The
closure of such a leaf contains family points, so no interval bound over a
closed box can ever prove it empty -- but the indifference equalities force
that coordinate to exactly 0, contradicting "strictly interior", and that is
a two-line exact computation.  This is the "different bound" s15.10.3 said the
residual needed.

Per leaf (labels 0 / 1 / MIX / DC), with the 0/1 coordinates substituted the
OWN-REACH-STRIPPED gradients D_i (symbet.build_D: opponents' reach times the
value difference, the player's own earlier choices set to 1) are small
multilinear polynomials over Q in the MIX and DC coordinates.  The system is
sequential rationality at every information set the player can reach by their
own deviation:

    D_i = 0            i MIX          (indifference)
    D_i <= 0           i labelled 0
    D_i >= 0           i labelled 1
    x D_i >= 0, (1-x) D_i <= 0   i DC (best response there too, if the set is
                                 unreached only through the player's own choice)
    0 < x_i < 1        i MIX          (interior means open)
    0 <= x_i <= 1      i DC

By the one-deviation principle over each player's own decision tree this is
EXACTLY the Nash condition, up to re-choosing coordinates at own-unreached
sets -- which never changes on-path play.  (The plain reach-weighted G_i = 0
conditions are weaker: with G, P2 always betting card 4 could be "supported" by
a dominated off-path continuation, and that is what the OPEN leaves of the
first pass were.)  Every rule below only ADDS conditions of this system, so an
EMPTY verdict is sound in whichever mode (nash / seq) produced the leaf, and
FAMILY means: every Nash equilibrium in the leaf is the family on path.

Certificates, in order of strength:
  EMPTY_GB      1 in <E>:  the equalities have no complex solution at all.
  EMPTY_MIX     for a MIX coordinate v, 1 in <E, 1 - t v>  (Rabinowitsch), so
                v = 0 on every solution; or the same with 1 - v.  Contradicts
                v in (0,1).  Pure ideal membership over Q -- no solving, no
                floating point, complete by construction.
  EMPTY_CONST   after reducing modulo the Groebner basis of E, an inequality
                is a constant of the wrong sign (exact elimination).
  EMPTY_BOX     exactbox.prove_empty: exact rational interval B&B on the whole
                system with the MIX coordinates in OPEN (0,1); every box dies.
  FAMILY        the leaf may be non-empty, and every feasible point satisfies
                Table 3 on its reached coordinates: the pinned zeros/ones are
                the leaf's own labels, and each identity h = 0 (a33 = 1/2,
                b41 = 2(b11+b21), c21 = 1/2 - c11, b33's formula split on
                b11 <=> b21) is proved either by radical membership
                (h vanishes on V(E)) or by exactbox on {h > 0} and {h < 0}.
  FAMILY_WIDE   the identities hold but some Table-3 parameter RANGE (b11 <= 1/4,
                sub-family C's b21 <= 1/2 - 2 b11, ...) could not be proved on
                the feasible set: the on-path structure is the family's, the
                parameter set may be larger.  info["range"] names them.
  OPEN          none of the above within the node budget; the surviving box and
                the failed identities are printed.  No sympy.solve anywhere:
                every verdict is an exact certificate.

usage:  python symleaf.py <tag> <workers> [index.npy|-] [limit|0] [maxnodes] [timeout_s]
        writes symleaf_<tag>.npz (verdict per leaf) and log lines to stdout.
"""
import numpy as np, sys, time, os
import sympy as sp
import kuhn3p as K, symbet, exactbox
from fractions import Fraction as F

U, MIX, DC = 9, 2, 3
NAME = K.PARAM_NAME; I = K.NAME_IDX
VERD = ["EMPTY_GB", "EMPTY_MIX", "EMPTY_BOX", "EMPTY_CONST", "FAMILY", "OPEN", "ERROR", "TIMEOUT", "FAMILY_WIDE"]
VC = {v: k for k, v in enumerate(VERD)}
_t = sp.Symbol("_t")

# Table 3 pins on reached coordinates (Table 2 is implied by reach + dominance
# and is checked too when the coordinate is not DC)
PIN0 = ("a11", "a21", "a22", "a23", "a31", "a32", "a34", "a41", "b22", "b31", "b34",
        "c22", "c23", "c31", "c32",
        "a12", "a13", "a14", "a24", "b12", "b13", "b14", "b24", "c12", "c13", "c14", "c24")
PIN1 = ("c41", "a42", "a43", "a44", "b42", "b43", "b44", "c42", "c43", "c44")


def build(lab):
    X = [None] * K.NPARAM; syms = {}
    for i in range(K.NPARAM):
        if lab[i] == 0: X[i] = sp.Integer(0)
        elif lab[i] == 1: X[i] = sp.Integer(1)
        else:
            syms[i] = sp.Symbol(NAME[i]); X[i] = syms[i]
    return X, syms, symbet.build_D(X)


def in_ideal_one(polys, gens):
    """1 in <polys> ?"""
    polys = [p for p in polys if p != 0]
    if not polys: return False
    gb = sp.groebner(polys, *gens, order="grevlex")
    return list(gb.exprs) == [1]


def vanishes(E, gens, f):
    """f == 0 on V(E) (over C)?   <=>   1 in <E, 1 - t f>"""
    return in_ideal_one(list(E) + [1 - _t * f], list(gens) + [_t])


def _bounds(lab, mixv, dcv):
    return [(F(0), F(1), True, True) for _ in mixv] + [(F(0), F(1), False, False) for _ in dcv]


def _sys(lab, G, mixv, X=None):
    """the leaf's necessary conditions as (poly, kind) lists for exactbox.
    G here is the own-reach-stripped gradient D (symbet.build_D): sequential
    rationality at every information set the player can reach on their own.
    A DC coordinate x (unreached in the box) gets the same condition in the
    form  x D >= 0  and  (1 - x) D <= 0 : vacuous when an opponent keeps the
    set unreached (D = 0), the best-response condition when only the player's
    own earlier choice does."""
    polys = []; kinds = []
    for i in mixv:
        if G[i] != 0: polys.append(G[i]); kinds.append("=")
    for i in range(K.NPARAM):
        if lab[i] == 0 and G[i] != 0: polys.append(-G[i]); kinds.append(">=")
        if lab[i] == 1 and G[i] != 0: polys.append(G[i]); kinds.append(">=")
        if lab[i] == DC and G[i] != 0 and X is not None:
            polys.append(sp.expand(X[i] * G[i])); kinds.append(">=")
            polys.append(sp.expand(-(1 - X[i]) * G[i])); kinds.append(">=")
    return polys, kinds


def holds(h, polys, kinds, gens, bounds, E, maxnodes, small=True, GB=None, LAB=None, GIDX=None):
    """is h == 0 on every feasible point?  radical membership first (cheap,
    over the whole complex variety), else the box prover on h > 0 and h < 0.
    h is first reduced modulo the Groebner basis of E (same value on V(E)):
    the LP relaxation only recognises a linear consequence of the leaf's
    inequalities when both sides are written in the same monomials."""
    h = sp.expand(h)
    if GB is not None: h = sp.expand(GB.reduce(h)[1])
    if h == 0: return True
    if h.is_number: return False
    if E and small and vanishes(E, gens, h): return True
    for side in (h, -h):
        ok, n, _ = exactbox.prove_empty(polys + [side], kinds + [">"], gens, bounds, max(1, maxnodes // 6), lab=LAB, gidx=GIDX)
        if not ok: return False
    return True


_WIT = None
def _has_witness(lab):
    """some certified equilibrium (certified_eq_all.npy, 744 family points) lies
    strictly inside this leaf: labels 0/1 matched to 1e-9, MIX in [1e-6, 1-1e-6]."""
    global _WIT
    if _WIT is None:
        try: _WIT = np.load("certified_eq_all.npy")
        except Exception: _WIT = np.zeros((0, K.NPARAM))
    if len(_WIT) == 0: return False
    ok = np.ones(len(_WIT), bool)
    for i in range(K.NPARAM):
        if lab[i] == 0: ok &= _WIT[:, i] <= 1e-9
        elif lab[i] == 1: ok &= _WIT[:, i] >= 1 - 1e-9
        elif lab[i] == MIX: ok &= (_WIT[:, i] >= 1e-6) & (_WIT[:, i] <= 1 - 1e-6)
    return bool(ok.any())


def decide(lab, maxnodes=20000, verbose=False):
    lab = np.asarray(lab).astype(np.int8)
    X, syms, G = build(lab)
    mixv = [i for i in range(K.NPARAM) if lab[i] == MIX]; dcv = [i for i in range(K.NPARAM) if lab[i] == DC]
    gens = [syms[i] for i in mixv + dcv]
    E = [G[i] for i in mixv if G[i] != 0]
    info = {"nE": len(E), "nMIX": len(mixv), "nDC": len(dcv)}
    polys, kinds = _sys(lab, G, mixv, X)
    # a DC coordinate that occurs in no constraint but its own best-response
    # pair is a private variable: the pair is satisfiable for every value of
    # its D (x = 1 if D > 0, x = 0 if D < 0, anything if D = 0), so drop both.
    # Nash-mode leaves carry ~25 DC coordinates; most are private.
    others = {}
    for p, k in zip(polys, kinds):
        for g in p.free_symbols: others[g] = others.get(g, 0) + 1
    priv = []
    for i in dcv:
        v = syms[i]
        own = sum(1 for p, k in zip(polys, kinds) if p.has(v) and (p == sp.expand(X[i] * G[i]) or p == sp.expand(-(1 - X[i]) * G[i])))
        if others.get(v, 0) == own:
            priv.append(i)
    if priv:
        keep = [not any(p.has(syms[i]) for i in priv) for p in polys]
        polys = [p for p, kp in zip(polys, keep) if kp]; kinds = [k for k, kp in zip(kinds, keep) if kp]
        dcv = [i for i in dcv if i not in priv]
        gens = [syms[i] for i in mixv + dcv]
        info["priv"] = len(priv)
    bounds = _bounds(lab, mixv, dcv)
    # ---- K0: root box only -- contraction + exact LP relaxation, milliseconds.
    # This is where almost every empty leaf dies, including the family-adjacent
    # ones; it runs before anything that can be slow.
    ok, n, box = exactbox.prove_empty(polys, kinds, gens, bounds, 1, lab=lab, gidx=mixv + dcv)
    if ok:
        info["nodes"] = 1
        return "EMPTY_BOX", info
    # Groebner bases have no timeout and blow up on the big betting-branch
    # systems (15 variables, 14-term equations): only use them when small.
    gensE = [g for g in gens if any(e.has(g) for e in E)]
    small = len(gensE) <= 8 and sum(len(sp.Add.make_args(e)) for e in E) <= 60
    GB = None
    # ---- K1: no complex solution (cheap Groebner)
    if E and small and in_ideal_one(E, gens):
        return "EMPTY_GB", info
    # ---- K1b: exact elimination -- replace every inequality by its normal form
    # modulo the Groebner basis of E (equal on V(E)), and E by the basis itself.
    # A leaf whose equalities force a32 = 1/2, c11 = c21 = 1/4 turns the b41
    # condition into the constant -1/96: interval reasoning never sees that.
    if E and small:
        gb = sp.groebner(E, *gens, order="grevlex")
        npolys = []; nkinds = []
        for p, k in zip(polys, kinds):
            if k == "=": continue
            r = sp.expand(gb.reduce(p)[1])
            if r.is_number:
                if r < 0 or (k == ">" and r == 0):
                    return "EMPTY_CONST", dict(info, value=str(r))
                continue
            npolys.append(r); nkinds.append(k)
        polys = list(gb.exprs) + npolys; kinds = ["="] * len(gb.exprs) + nkinds
        E = list(gb.exprs); GB = gb
    # ---- K3a: root again on the Groebner-reduced system (when it was reduced)
    if GB is not None:
        ok, n, box = exactbox.prove_empty(polys, kinds, gens, bounds, 1, lab=lab, gidx=mixv + dcv)
        if ok:
            info["nodes"] = 1
            return "EMPTY_BOX", info
    # ---- K2: a MIX coordinate is forced to 0 or 1 on the whole variety
    if E and small:
        for i in mixv:
            v = syms[i]
            if vanishes(E, gens, v):      return "EMPTY_MIX", dict(info, coord=NAME[i], value=0)
            if vanishes(E, gens, 1 - v):  return "EMPTY_MIX", dict(info, coord=NAME[i], value=1)
    # ---- K3b: exact interval B&B with a small budget (a leaf that is not empty
    # cannot be proven empty at any budget, and FAMILY does not need emptiness).
    # Skipped when a certified equilibrium lies strictly inside the leaf.
    if _has_witness(lab):
        info["witness"] = True; box = None
    else:
        ok, n, box = exactbox.prove_empty(polys, kinds, gens, bounds, maxnodes, lab=lab, gidx=mixv + dcv)
        info["nodes"] = n
        if ok:
            return "EMPTY_BOX", info
    # ---- FAMILY: Table 3 identities on the reached coordinates, on the feasible set
    def x(nm): return X[I[nm]]
    def reached(nm): return lab[I[nm]] != DC
    why = []
    for nm in PIN0:
        if reached(nm) and lab[I[nm]] != 0: why.append("%s:%s" % (nm, "1" if lab[I[nm]] == 1 else "MIX"))
    for nm in PIN1:
        if reached(nm) and lab[I[nm]] != 1: why.append("%s:%s" % (nm, "0" if lab[I[nm]] == 0 else "MIX"))
    if not why:
        H = []
        if reached("a33"): H.append(("a33", x("a33") - sp.Rational(1, 2), []))
        H.append(("b41", x("b41") - 2 * (x("b11") + x("b21")), []))
        H.append(("c21", x("c21") - (sp.Rational(1, 2) - x("c11")), []))
        if reached("b33"):
            b23 = x("b23") if reached("b23") else sp.Integer(0)
            base = sp.Rational(1, 2) + (x("b11") + x("b21")) / 2 - b23 * (1 - x("b21"))
            H.append(("b33|b11<=b21", x("b33") - (base + x("b21") / 2), [x("b21") - x("b11")]))
            H.append(("b33|b11>=b21", x("b33") - (base + x("b11") / 2), [x("b11") - x("b21")]))
        for nm, h, extra in H:
            if not holds(h, polys + extra, kinds + [">="] * len(extra), gens, bounds, E, maxnodes, small, GB, lab, mixv + dcv):
                why.append(nm)
    if not why:
        # Table 3's PARAMETER RANGES on the reached parameters, sub-family by the
        # labels of c11 / c21 (A: c11 = 0; B: both MIX, c11 < 1/2; C: c11 MIX,
        # c21 = 0 i.e. c11 = 1/2).  Each range  h <= 0  is proved by showing
        # {feasible, h > 0} empty.  Off-path ranges (b32, c33, c34, b22, c23) are
        # NOT part of the on-path theorem -- offpath.py showed Nash does not need
        # them.  Identities that hold with ranges violated -> FAMILY_WIDE.
        lc11, lc21 = lab[I["c11"]], lab[I["c21"]]
        b11, b21, c11 = x("b11"), x("b21"), x("c11")
        b23 = x("b23") if reached("b23") else sp.Integer(0)
        R = []
        if lc11 == 0:
            R += [("A:b11<=b21", b11 - b21), ("A:b21<=1/4", b21 - sp.Rational(1, 4))]
        elif lc11 == MIX and lc21 == MIX:
            R += [("B:b11<=1/4", b11 - sp.Rational(1, 4)), ("B:c11<=(2-b11)/(3+4b11)", c11 * (3 + 4 * b11) - (2 - b11))]
            if not holds(b21 - b11, polys, kinds, gens, bounds, E, maxnodes, small, GB, lab, mixv + dcv): why.append("B:b21=b11")
        elif lc11 == MIX and lc21 == 0:
            R += [("C:b21<=b11", b21 - b11), ("C:b21<=1/2-2b11", b21 - (sp.Rational(1, 2) - 2 * b11)),
                  ("C:b11<=1/4", b11 - sp.Rational(1, 4)), ("C:b23<=(b11-b21)/(2(1-b21))", 2 * b23 * (1 - b21) - (b11 - b21))]
        else:
            why.append("c11/c21 labels not A/B/C")
        rng = []
        for nm, h in R:
            h = sp.expand(h)
            if GB is not None: h = sp.expand(GB.reduce(h)[1])
            if h.is_number:
                if h > 0: rng.append(nm)
                continue
            ok, n_, _ = exactbox.prove_empty(polys + [h], kinds + [">"], gens, bounds, max(1, maxnodes // 6), lab=lab, gidx=mixv + dcv)
            if not ok: rng.append(nm)
        if rng: info["range"] = ",".join(rng)
        if not why:
            return ("FAMILY" if not rng else "FAMILY_WIDE"), info
    # surviving box, for the record
    info["why"] = ",".join(why)
    if box is not None:
        info["box"] = " ".join("%s[%s,%s]" % (NAME[i], float(b[0]), float(b[1])) for i, b in zip(mixv + dcv, box) if b[1] - b[0] < 1)
    return "OPEN", info


def _worker(qin, qout):
    while True:
        a = qin.get()
        if a is None: return
        k, lab, maxnodes = a
        t0 = time.time()
        try:
            v, info = decide(lab, maxnodes)
        except Exception as ex:
            v, info = "ERROR", {"err": str(ex)[:80]}
        qout.put((k, v, info, time.time() - t0))


def run_pool(jobs, nw, timeout):
    """N worker processes with a per-leaf wall-clock watchdog: a worker that
    exceeds `timeout` on one leaf is killed, that leaf is reported TIMEOUT and
    the worker is replaced.  Pool.imap cannot do this -- a stuck worker stays
    stuck and eventually every worker is."""
    import multiprocessing as mp
    ctx = mp.get_context("spawn")
    qout = ctx.Queue()
    pending = list(jobs)[::-1]
    workers = {}          # pid -> (proc, qin, (job, t_start) or None)
    def spawn():
        qin = ctx.Queue(); p = ctx.Process(target=_worker, args=(qin, qout)); p.start()
        workers[p.pid] = [p, qin, None]
    for _ in range(min(nw, len(pending))): spawn()
    ndone = 0; total = len(pending)
    while ndone < total:
        for pid, w in list(workers.items()):
            if w[2] is None and pending:
                job = pending.pop(); w[1].put(job); w[2] = (job, time.time())
        try:
            k, v, info, dt = qout.get(timeout=1.0)
            ndone += 1
            for pid, w in workers.items():
                if w[2] is not None and w[2][0][0] == k: w[2] = None
            yield k, v, info, dt
        except Exception:
            pass
        now = time.time()
        for pid, w in list(workers.items()):
            if w[2] is not None and now - w[2][1] > timeout:
                job = w[2][0]
                w[0].terminate(); w[0].join(5); del workers[pid]
                spawn()
                ndone += 1
                yield job[0], "TIMEOUT", {"timeout": timeout}, now - w[2][1]
    for pid, w in workers.items():
        w[1].put(None)
    for pid, w in workers.items():
        w[0].join(5)
        if w[0].is_alive(): w[0].terminate()


if __name__ == "__main__":
    tag, nw = sys.argv[1], int(sys.argv[2])
    L = np.load("enum6_pat_%s.npy" % tag).astype(np.int8)
    idx = np.arange(len(L))
    if len(sys.argv) > 3 and sys.argv[3] != "-":
        idx = np.load(sys.argv[3])
    if len(sys.argv) > 4 and int(sys.argv[4]) > 0:
        idx = idx[:int(sys.argv[4])]
    maxnodes = int(sys.argv[5]) if len(sys.argv) > 5 else 300
    timeout = float(sys.argv[6]) if len(sys.argv) > 6 else 180.0
    print("tag %s  leaves %d  workers %d  maxnodes %d  timeout %.0fs" % (tag, len(idx), nw, maxnodes, timeout), flush=True)
    verd = np.full(len(L), -1, np.int8); tsec = np.zeros(len(L))
    counts = {v: 0 for v in VERD}; t0 = time.time()
    # RESUME: the verdict file is checkpointed every 100 leaves; on a restart
    # keep every leaf already decided and only run the rest (2026-09-18)
    if os.path.exists("symleaf_%s.npz" % tag):
        with np.load("symleaf_%s.npz" % tag) as z:
            if len(z["verdict"]) == len(L):
                verd = z["verdict"].copy(); tsec = z["tsec"].copy()
        # OPEN / TIMEOUT from an earlier pass are not decisions: run them again
        # (they then also get the second pass at 10x the budget)
        verd[(verd == VC["OPEN"]) | (verd == VC["TIMEOUT"])] = -1
        done_ = [int(k) for k in idx if verd[k] >= 0]
        for k in done_: counts[VERD[verd[k]]] += 1
        idx = np.array([int(k) for k in idx if verd[k] < 0], dtype=np.int64)
        print("   resumed: %d leaves already decided, %d to go" % (len(done_), len(idx)), flush=True)
    for n, (k, v, info, dt) in enumerate(run_pool([(int(k), L[k], maxnodes) for k in idx], nw, timeout)):
        verd[k] = VC[v]; tsec[k] = dt; counts[v] += 1
        if v in ("OPEN", "ERROR", "TIMEOUT"):
            print("   leaf %d  %s  %s" % (k, v, info), flush=True)
        if (n + 1) % 100 == 0 or n + 1 == len(idx):
            print("   %d/%d  %s  %.0fs" % (n + 1, len(idx), "  ".join("%s %d" % (a, b) for a, b in counts.items() if b), time.time() - t0), flush=True)
            np.savez("symleaf_%s.npz" % tag, verdict=verd, tsec=tsec, idx=idx)
    # second pass: OPEN / TIMEOUT leaves get ten times the budget (branch 3 of
    # runbet6 had 6 OPEN at 300 nodes; all six died between 303 and 941 nodes)
    again = [int(k) for k in idx if verd[k] in (VC["OPEN"], VC["TIMEOUT"])]
    if again:
        print("   second pass on %d OPEN/TIMEOUT leaves at %d nodes" % (len(again), 10 * maxnodes), flush=True)
        for k, v, info, dt in run_pool([(k, L[k], 10 * maxnodes) for k in again], min(nw, len(again)), 3 * timeout):
            counts[VERD[verd[k]]] -= 1; counts[v] += 1
            verd[k] = VC[v]; tsec[k] += dt
            if v in ("OPEN", "ERROR", "TIMEOUT"):
                print("   leaf %d  %s  %s" % (k, v, info), flush=True)
    np.savez("symleaf_%s.npz" % tag, verdict=verd, tsec=tsec, idx=idx)
    print("\nTOTAL %d leaves:  %s   %.0fs" % (len(idx), "  ".join("%s %d" % (a, b) for a, b in counts.items()), time.time() - t0), flush=True)
