"""Exhaustive interval partition of P1's opening coordinates, driven by bnb5.

Replaces the label-based decomposition of `allbranch3.py`, which drives `bnb3`
-- the {0, 1, interior} label alphabet that s15.5 records as non-terminating on
these branches.  The defect is redundancy: the label "interior" has to be
carried as the box [0,1], which *contains* both pure labels, so an interior
branch re-does the entire problem.

A partition into intervals has no such redundancy.  Grid per opening
coordinate, edges 0 < LOCUT < HICUT < 1:

    [0, LOCUT]        hi < 1           ==>  du/dx <= 0
    [LOCUT, HICUT]    lo > 0, hi < 1   ==>  du/dx  = 0
    [HICUT, 1]        lo > 0           ==>  du/dx >= 0

Every cell therefore carries a Nash condition on all four openers immediately.
The 3^4 = 81 cells cover [0,1]^4 and meet only on faces, so proving every cell
empty proves the space empty -- an equilibrium sitting exactly on a face is
contained in both neighbouring cells, never lost.

THE ALL-LOW CELL IS NOT COVERED BY DEFAULT.  Cell (0,0,0,0) = [0,LOCUT]^4
contains the P1-silent point, but it is *not* the silent branch: it holds every
profile with small positive opening frequencies.  It does not terminate at any
sane node budget (measured: 300k nodes -> 103,465 boxes, still ABORT), because
it is essentially the whole silent problem plus a neighbourhood.  Running it
alongside the other 80 would burn the entire budget on one cell and return
ABORT, which proves nothing.

So this driver settles the 80 cells in which P1 bets some card with probability
at least LOCUT.  Proving those empty does NOT finish the completeness question:
the residual is profiles where all four openers lie in (0, LOCUT) -- P1
bluffing at a tiny but nonzero frequency.  That residual needs the enumeration
treatment, or a finer sub-partition, and is reported explicitly at the end
rather than being quietly folded into a "81/81 empty" claim.

usage:  python allbranch5.py <maxnodes> <workers> [tag] [locut] [hicut] [alllow]
        alllow=1 includes cell (0,0,0,0); default 0 excludes it.
"""
import numpy as np, sys, time, itertools, bnb5, kuhn3p as K
from multiprocessing import Pool

I = K.NAME_IDX
OPEN = [I[n] for n in ("a11", "a21", "a31", "a41")]
WTOL = 0.06
MAXDEPTH = 26


def cell_box(code, edges):
    """Box for one cell: `code[k]` indexes the slab of opener k."""
    LO = np.zeros(48)
    HI = np.ones(48)
    for k, v in enumerate(OPEN):
        LO[v] = edges[code[k]]
        HI[v] = edges[code[k] + 1]
    return LO, HI


def job(a):
    code, edges, maxnodes = a
    LO, HI = cell_box(code, edges)
    t0 = time.time()
    st, boxes = bnb5.search(LO0=LO, HI0=HI, wtol=WTOL, maxdepth=MAXDEPTH,
                            cap=4096, maxnodes=maxnodes)
    if boxes:
        BLO = np.concatenate([b[0] for b in boxes])
        BHI = np.concatenate([b[1] for b in boxes])
    else:
        BLO = np.zeros((0, 48)); BHI = np.zeros((0, 48))
    return code, st, time.time() - t0, BLO, BHI


if __name__ == "__main__":
    maxnodes = int(sys.argv[1])
    nw = int(sys.argv[2])
    tag = sys.argv[3] if len(sys.argv) > 3 else "b5"
    locut = float(sys.argv[4]) if len(sys.argv) > 4 else 0.02
    hicut = float(sys.argv[5]) if len(sys.argv) > 5 else 0.25
    alllow = bool(int(sys.argv[6])) if len(sys.argv) > 6 else False
    edges = [0.0, locut, hicut, 1.0]

    codes = list(itertools.product((0, 1, 2), repeat=4))
    if not alllow:
        codes = [c for c in codes if c != (0, 0, 0, 0)]
    # cheapest-looking first: cells with a coordinate pinned high tend to die at
    # the root, so the run reports progress early instead of stalling on one
    # hard cell for an hour with nothing on screen.
    codes.sort(key=lambda c: -sum(c))
    print("partition edges %s   cells %d (all-low %s)   workers %d   maxnodes %d"
          % (edges, len(codes), "included" if alllow else "EXCLUDED", nw, maxnodes),
          flush=True)

    t0 = time.time()
    empty = 0; openc = 0; aborted = 0; done = 0
    keepLO = []; keepHI = []; keepC = []
    with Pool(nw) as pool:
        for code, st, dt, BLO, BHI in pool.imap_unordered(
                job, [(c, edges, maxnodes) for c in codes]):
            done += 1
            ab = st.get('ABORT', False)
            if ab:
                aborted += 1; verdict = "ABORT (node cap)"
            elif st['boxes'] == 0:
                empty += 1; verdict = "EMPTY (proven)"
            else:
                openc += 1; verdict = "open: %d boxes" % st['boxes']
            print("%-14s nodes=%-10d %-22s %6.0fs   [%d/%d  empty %d  open %d  abort %d  %.0fs]"
                  % (str(code), st['nodes'], verdict, dt,
                     done, len(codes), empty, openc, aborted, time.time() - t0),
                  flush=True)
            if len(BLO):
                keepLO.append(BLO); keepHI.append(BHI)
                keepC += [code] * len(BLO)

    if keepLO:
        np.save("b5box_lo_%s.npy" % tag, np.concatenate(keepLO))
        np.save("b5box_hi_%s.npy" % tag, np.concatenate(keepHI))
        np.save("b5box_code_%s.npy" % tag, np.array(keepC))
        print("saved %d open boxes" % sum(len(a) for a in keepLO), flush=True)
    print("DONE  empty %d/%d  open %d  abort %d  %.0fs"
          % (empty, len(codes), openc, aborted, time.time() - t0), flush=True)
    if empty == len(codes) and not alllow:
        print("\nAll %d searched cells are PROVEN EMPTY: no equilibrium has any P1\n"
              "opening frequency >= %g.  STILL OPEN: the all-low cell [0,%g)^4,\n"
              "i.e. P1 bluffing at a tiny nonzero frequency.  The completeness\n"
              "question is NOT closed by this run alone." % (len(codes), locut, locut),
              flush=True)
    elif openc or aborted:
        print("\n%d cells open and %d aborted -- these carry candidate boxes and are\n"
              "NOT proven empty.  Raise maxnodes on those before drawing conclusions."
              % (openc, aborted), flush=True)
