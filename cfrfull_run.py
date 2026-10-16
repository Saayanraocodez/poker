"""Open problem 5: run the full-width CFR variants (cfrfull.py) from many starts and record, at
log-spaced checkpoints, where the average strategy is relative to the complete Nash set.

Per checkpoint: max-player exploitability (float), the certified distance to the Nash set
(reread14.certify: an exact lower bound, shown by reread14b to equal the distance), the nearest
FAMILY leaf and sub-family, the payoffs u (float), beta = max(b11, b21), and the coordinates the
refinement analysis cares about (b32, c33's position in its window, c34, a32).

usage:  python cfrfull_run.py <variants,comma> <iters> <nseed> [workers]  -> cfrfull_<variants>_<iters>.json
"""
import sys, json
import numpy as np
from multiprocessing import Pool
import cfrfull as CF, kuhn3p as K, reread14 as R, family as FM

I = K.NAME_IDX
_CTX = {}


def ctx():
    if not _CTX:
        L, fam = R.leaves(); IDS = R.identities(); RG = R.ranges()
        _CTX.update(L=L, fam=fam, IDS=IDS, boxes={k: R.leaf_box(k, L[k], RG) for k in fam},
                    sub={k: ("A" if int(L[k][I["c11"]]) == 0 else ("B" if int(L[k][I["c21"]]) == 2 else "C")) for k in fam})
    return _CTX


def measure(p):
    c = ctx()
    per = {k: R.certify(p, *c["boxes"][k], c["IDS"][k])[0] for k in c["fam"]}
    k = min(per, key=per.get)
    b11, b21, b32, c33 = (p[I[n]] for n in ("b11", "b21", "b32", "c33"))
    lo = 0.5 - b32; hi = FM.b32_max(b11, b21) - b32
    return dict(expl=float(K.exploitability(p).max()), dist=float(per[k]), leaf=k, sub=c["sub"][k],
                u=[float(x) for x in K.utilities(p)], beta=float(max(b11, b21)),
                b11=float(b11), b21=float(b21), c11=float(p[I["c11"]]), b23=float(p[I["b23"]]),
                a32=float(p[I["a32"]]), b32=float(b32), c33=float(c33), c34=float(p[I["c34"]]),
                c33frac=float((c33 - lo) / (hi - lo)) if hi - lo > 1e-9 else None)


def job(args):
    v, iters, seed = args
    cps = sorted({int(round(10 ** e)) for e in np.arange(2, np.log10(iters) + 1e-9, 0.5)} | {iters})
    p, snaps = CF.run(v, iters, seed, cps)
    out = {t: measure(CF.avg_of(S)) for t, S in snaps.items()}
    return dict(variant=v, seed=seed, iters=iters, final=out[iters], trace=out, profile=p.tolist())


def main():
    vs = sys.argv[1].split(","); iters = int(float(sys.argv[2])); ns = int(sys.argv[3])
    nw = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    tasks = [(v, iters, s) for v in vs for s in range(ns)]
    with Pool(nw) as pool:
        res = pool.map(job, tasks, chunksize=1)
    fn = "cfrfull_%s_%d.json" % ("-".join(vs), iters)
    json.dump(res, open(fn, "w"))
    print("written", fn)


if __name__ == "__main__":
    main()
