"""THEOREM 6 WITH REPLAYABLE EVIDENCE -- the prover side.

Re-runs the per-leaf enumeration of off-path patterns so that every exclusion leaves
evidence the independent checker (checkseqcert.py) replays.  Every system is built from
checkseqcert's own row constructors (seqforms: the game tree in Fractions), so prover and
checker cannot disagree about what a row IS; the prover contributes only the search
(certbox) and the witness search.

  closure   exact dominance (D_v = c R_v), then robustly one-signed leading forms;
  onesigned an assigned value contradicting a robustly one-signed form;
  cert      a certbox certificate whose rows are named by origin;
  orderings one certificate per ordered partition of a tremble group;
  witness   an exact profile and a CONCRETE tremble curve (order and ratio per trembling
            coordinate), checked by checkseqcert.check_witness before it is recorded.

Soundness restrictions shared with the checker: belief rows only when multi-homogeneous in
the sets' ratios; robust one-signedness only for forms linear in one set's ratios.
No forcing is injected and nothing is pruned without evidence.

usage (windowless):  pythonw.exe seqcert.py [workers] [leaf ...]  -> seqcert_<leaf>.jsonl.gz
"""
import sys as _sys, os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
if _sys.stdout is None or _sys.stderr is None:
    _sys.stdout = _sys.stderr = open("log_seqcert.txt", "a", buffering=1, encoding="utf-8", errors="replace")
import json, gzip, time, sys, itertools
import numpy as np
from fractions import Fraction as F
import seqforms as SF
import checkseqcert as CK
import certbox, seqset, kuhn3p as K

NAME = K.PARAM_NAME; I = K.NAME_IDX
MIX, DC = 2, 3
G_A = ("a11", "a21", "a31", "a41"); G_B = ("b11", "b21", "b31", "b41")


def prove(case, full, budget, order=None, group=None):
    origins, gens = CK.system(case, full, order, group)
    if not gens: return None
    rowof = CK.build_rowof(case, gens, order, group)
    P = []; Kd = []
    for o in origins:
        p, k = rowof(o); P.append(p); Kd.append(k)
    box = CK.expected_box(case, gens, group)
    bounds = [(b[0], b[1], b[2], b[3]) for b in box]
    r = certbox.prove_empty_cert(P, Kd, None, bounds, budget, origins=[list(o) for o in origins],
                                 chord=False, exact_dual=False)
    if not r[0]: return None
    c = r[1]; c["gens"] = gens
    return c


def dominance():
    D, R = SF.DR(); out = {}
    for v in range(48):
        if not D[v] or not R[v]: continue
        m0 = next(iter(R[v])); c = D[v].get(m0, F(0)) / R[v][m0]
        if c != 0 and SF.padd(D[v], R[v], -c) == {}: out[v] = c
    return out


def closure(lab, unreached):
    forced = []; assign = {}
    for v, c in sorted(dominance().items()):
        if lab[v] == DC:
            val = 1 if c > 0 else 0
            forced.append((v, val, "dominance")); assign[v] = val
    while True:
        new = None
        case = CK.Case(lab, dict(assign))
        for v in unreached:
            if v in assign: continue
            s = CK.robust_sign(case.belief(v), case.openx)
            if s: new = (v, 1 if s > 0 else 0); break
        if new is None: return forced
        forced.append((new[0], new[1], "robust")); assign[new[0]] = new[1]


def onesigned_conflict(case):
    for v, val in case.assign.items():
        s = CK.robust_sign(case.belief(v), case.openx)
        if s < 0 and val != 0: return v
        if s > 0 and val != 1: return v
    return None


# ------------------------------------------------------------------ witnesses
def curve_from(s, beliefs, order):
    """a concrete tremble curve: every coordinate at 0 or 1 trembles; ratios from the
    belief vector, orders 1 + class for an ordered group, 1 otherwise; a trembling
    coordinate absent from the beliefs trembles at a much higher order (it played no
    part in the leading forms)."""
    cands = []
    for high in (60, 1):
        cur = {}
        for w in range(48):
            if s[w] not in (0, 1): continue
            key = "r_" + NAME[w]
            if key in beliefs:
                cur[NAME[w]] = [1 + int(order.get(NAME[w], 0)) if order else 1, str(beliefs[key])]
            else:
                cur[NAME[w]] = [high, "1"]
        cands.append(cur)
    return cands


def find_witness(lab, pieces, assign):
    tries = []
    w = seqset.witness_for(lab, pieces, assign)
    if w is not None: tries.append(w)
    if not tries:
        import witC
        grids = {"b11": witC.B11, "b21": witC.B21, "b23": witC.B23, "c11": witC.C11}
        fixed = {n: F(int(lab[I[n]])) for n in ("b11", "b21", "b23", "c11") if lab[I[n]] in (0, 1)}
        free = [n for n in ("b11", "b21", "b23", "c11") if n not in fixed]
        mixed = [v for v, val in assign.items() if val == "mix"]
        t0 = time.time()
        for pars in itertools.product(*[grids[n] for n in free]):
            if tries or time.time() - t0 > 300: break
            pv = dict(zip(free, pars)); pv.update(fixed)
            for vals in itertools.product(witC.MIXV, repeat=len(mixed)):
                off = {NAME[v]: F(int(val)) for v, val in assign.items() if val in (0, 1)}
                for i in range(48):
                    if lab[i] == 0: off.setdefault(NAME[i], F(0))
                    elif lab[i] == 1: off.setdefault(NAME[i], F(1))
                off.update({NAME[v]: x for v, x in zip(mixed, vals)})
                for n in ("b11", "b21", "b23", "c11"): off.pop(n, None)
                s = seqset.family_point(pv["b11"], pv["b21"], pv["b23"], pv["c11"], off)
                if seqset.verify_point(lab, s) is not None: continue
                st, m, r = seqset.is_sequential(pieces, s, lab)
                if st == "sequential": tries.append((s, r, {})); break
                st2, order, sol = seqset.seq_orderings_any(lab, s, pieces)
                if st2 == "sequential": tries.append((s, sol, order)); break
    if not tries:
        w = seqset.witness_guided(lab, pieces, assign)
        if w is not None: tries.append(w)
    for s, beliefs, order in tries:
        for cur in curve_from(s, beliefs, order or {}):
            rec = {"witness": {NAME[i]: str(s[i]) for i in range(48)}, "curve": cur}
            try:
                CK.check_witness([int(x) for x in lab], assign, rec)
                return rec
            except CK.Bad:
                continue
    return None


# ------------------------------------------------------------------ the enumeration
def run(k):
    L = np.load("enum6_pat_silentR.npy"); lab = [int(x) for x in L[k]]; t0 = time.time()
    pieces = seqset.leaf_pieces(L[k])
    unreached = pieces[6]
    forced = closure(lab, unreached)
    assign0 = {v: val for v, val, why in forced}
    rest = [v for v in unreached if v not in assign0 and lab[v] == DC]
    out = gzip.open("seqcert_%d.jsonl.gz" % k, "wt")
    out.write(json.dumps({"kind": "head", "leaf": int(k), "closure": [[NAME[v], val, why] for v, val, why in forced],
                          "decide": [NAME[v] for v in rest]}) + "\n")
    st = {"cert": 0, "onesigned": 0, "orderings": 0, "witness": 0, "undecided": 0}

    def rec(assign, **kw):
        d = {"assign": {NAME[v]: (val if val == "mix" else int(val)) for v, val in assign.items() if v not in assign0}}
        d.update(kw); out.write(json.dumps(d) + "\n"); out.flush()

    stack = [dict(assign0)]
    while stack:
        assign = stack.pop()
        todo = [v for v in rest if v not in assign]
        case = CK.Case(lab, assign)
        c = onesigned_conflict(case)
        if c is not None:
            rec(assign, kind="kill", ev="onesigned", v=NAME[c]); st["onesigned"] += 1; continue
        cert = prove(case, not todo, 60 if todo else 400)
        if cert is not None:
            rec(assign, kind="kill", ev="cert", full=not todo, cert=cert); st["cert"] += 1; continue
        if todo:
            v = todo[0]
            for val in (0, 1, "mix"):
                a2 = dict(assign); a2[v] = val; stack.append(a2)
            continue
        killed = False
        for grp in (G_A, G_B):
            certs = {}
            for order in CK.ordered_partitions(grp):
                c2 = prove(case, True, 300, order, list(grp))
                if c2 is None: break
                certs[json.dumps(sorted(order.items()))] = c2
            else:
                rec(assign, kind="kill", ev="orderings", group=list(grp), certs=certs)
                st["orderings"] += 1; killed = True; break
        if killed: continue
        w = find_witness(L[k], pieces, assign)
        if w is not None:
            rec(assign, kind="witness", **w); st["witness"] += 1
        else:
            rec(assign, kind="undecided"); st["undecided"] += 1
    out.close()
    return k, st, time.time() - t0, len(forced), len(rest)


if __name__ == "__main__":
    nw = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    leaves = [int(a) for a in sys.argv[2:]] or seqset.FAM
    from multiprocessing import Pool
    with open("seqcert_summary.txt", "a") as f:
        with Pool(nw) as pool:
            for k, st, secs, nf, nr in pool.imap_unordered(run, leaves):
                line = time.strftime("%m-%d %H:%M  ") + "leaf %4d  closure %2d  decided %2d  %s  %.0fs" % (k, nf, nr, st, secs)
                f.write(line + "\n"); f.flush(); print(line, flush=True)
