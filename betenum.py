"""How big is the support enumeration of a P1-BETTING branch?

`runsilent.py` enumerated the P1-silent branch (a11=a21=a31=a41=0): 18 live
coordinates, 3,045,358 complete patterns, 525 s.  That enumeration is what made
the silent branch decidable -- every pattern then went through bisection + LM.

The bet branch has no such result, and the box-partition route cannot supply one
(feas.py's boxes all hit maxdepth, and the depth ladder shows the box count
growing geometrically).  So the question is whether the LABEL enumeration is
sized for a betting branch at all.  This measures it: same engine, same order,
one opening coordinate labelled interior instead of 0.

Counts leaves through a sink so nothing accumulates in RAM, and reports the
leaf rate so an aborted run still gives an extrapolation.

With `save`, leaves are appended to `pats_<coord>_<label>.i8` as they are
produced rather than accumulated -- the silent branch was 3.0M patterns, and a
betting branch that turns out to be 50x that would be 7 GB of int8 held in RAM
by a list of blocks.  `spill_to_npy` turns the raw file into the .npy the
pipe2 screen expects.

usage:  python betenum.py <coord> <label> <maxnodes> [save]
        e.g.  python betenum.py a11 MIX 200000000 save
"""
import numpy as np, sys, time, bnb, kuhn3p as K

I = K.NAME_IDX
ORDER = [I[n] for n in ("c11", "c21", "c31", "c41", "b11", "b21", "b31", "b41",
                        "a22", "a32", "a33", "a34", "a23",
                        "b22", "b23", "b32", "b33", "b34",
                        "c22", "c23", "c32", "c33", "c34",
                        "a12", "a13", "a14", "a24", "b12", "b13", "b14", "b24",
                        "c12", "c13", "c14", "c24", "a42", "a43", "a44",
                        "b42", "b43", "b44", "c42", "c43", "c44",
                        "a11", "a21", "a31", "a41")]
LAB = {"0": 0, "1": 1, "MIX": bnb.MIX}


def spill_to_npy(raw, out, chunk=2000000):
    """Raw int8 spill -> (N,48) .npy, without holding it all in RAM."""
    import numpy.lib.format as fmt, os
    n = os.path.getsize(raw) // 48
    m = fmt.open_memmap(out, mode='w+', dtype=np.int8, shape=(n, 48))
    with open(raw, "rb") as f:
        o = 0
        while o < n:
            k = min(chunk, n - o)
            m[o:o+k] = np.frombuffer(f.read(k * 48), dtype=np.int8).reshape(k, 48)
            o += k
    m.flush(); del m
    return n

if __name__ == "__main__":
    coord = sys.argv[1]; lab_s = sys.argv[2]
    maxnodes = int(sys.argv[3])
    save = len(sys.argv) > 4

    lab = np.full(48, bnb.U)
    lab[I[coord]] = LAB[lab_s]
    t0 = time.time()
    n = [0]
    raw = "pats_%s_%s.i8" % (coord, lab_s)
    fh = open(raw, "wb") if save else None

    def sink(blk):
        n[0] += blk.shape[0]
        if fh is not None:
            blk.astype(np.int8).tofile(fh)
        if n[0] % 500000 < blk.shape[0]:
            print("   leaves=%d  %.0fs" % (n[0], time.time() - t0), flush=True)

    pats, st = bnb.run(lab, ORDER, cap=4096, log=200, maxnodes=maxnodes, sink=sink)
    dt = time.time() - t0
    print("%s=%s : leaves=%d  nodes=%d  abort=%s  %.0fs  (%.0f leaves/s, %.0f nodes/s)"
          % (coord, lab_s, n[0], st['nodes'], st.get('ABORT', False), dt,
             n[0] / max(dt, 1e-9), st['nodes'] / max(dt, 1e-9)), flush=True)
    if fh is not None:
        fh.flush(); import os; os.fsync(fh.fileno()); fh.close()
        out = "pats_%s_%s.npy" % (coord, lab_s)
        print("converting spill -> %s" % out, flush=True)
        print("saved %s (%d patterns)" % (out, spill_to_npy(raw, out)), flush=True)
