"""Control for bnb5's checkpoint/resume.

`bnb5.search` had no resume, so the two 22-hour feas.py tasks that were in
flight on 2026-09-02 were lost entirely when the machine was powered off.  The
fix spills emitted boxes to a raw file and checkpoints the DFS stack.

The failure this control exists to catch is silent: a resume that loses boxes
shrinks an exhaustive claim, and one that replays boxes inflates it, and in
both cases the search still finishes and still prints a plausible verdict.  So
the test is not "does it resume" but "is the resumed answer bit-identical to
the uninterrupted one".

usage:  python control_ck.py
"""
import numpy as np, os, glob, sys, bnb5, family as F, eqtools as E

WTOL, MAXDEPTH, CAP = 0.06, 26, 4096          # the production feas.py settings
PFX = "ckctl"

def clean():
    for p in glob.glob(PFX + "*"):
        os.remove(p)

def boxes_of(out):
    if not out: return np.zeros((0, 96))
    return np.concatenate([np.hstack([a, b]) for a, b in out])

def spill_of(pfx):
    lo, hi = bnb5._spill_paths(pfx)
    a = np.fromfile(lo, dtype=np.float64).reshape(-1, 48)
    b = np.fromfile(hi, dtype=np.float64).reshape(-1, 48)
    return np.hstack([a, b])

def canon(M):
    """Box sets are compared as multisets: the DFS may legitimately emit in a
    different order, but it must emit the same boxes with the same multiplicity."""
    if len(M) == 0: return M
    return M[np.lexsort(M.T[::-1])]

p = F.profile_A(0.125, 0.25)[0]
assert np.abs(E.expl(p)).max() < 1e-12, "control point is not an equilibrium"
LO0 = np.clip(p - 0.06, 0.0, 1.0)      # ~143k nodes / 66k boxes: big
HI0 = np.clip(p + 0.06, 0.0, 1.0)      # enough to have real stack depth

fail = 0

# ---- reference: one uninterrupted run ------------------------------------
print("--- reference run (no checkpoint)")
stA, outA = bnb5.search(LO0=LO0, HI0=HI0, wtol=WTOL, maxdepth=MAXDEPTH, cap=CAP)
A = canon(boxes_of(outA))
print("    nodes=%d boxes=%d abort=%s" % (stA['nodes'], stA['boxes'],
                                          stA.get('ABORT', False)))
assert not stA.get('ABORT'), "reference aborted -- pick a smaller box"
assert stA['boxes'] > 1000, "box too easy to be a real test (%d)" % stA['boxes']

# ---- 1. checkpointed, uninterrupted, checkpointing on EVERY iteration ------
print("\n--- 1. ckevery=0 (checkpoint every loop) must not change the answer")
clean()
stB, outB = bnb5.search(LO0=LO0, HI0=HI0, wtol=WTOL, maxdepth=MAXDEPTH, cap=CAP,
                        ckpt=PFX, ckevery=0.5, tag="ck0")
B = canon(spill_of(PFX))
ok = (len(outB) == 0 and stB['nodes'] == stA['nodes']
      and stB['boxes'] == stA['boxes'] and B.shape == A.shape
      and np.array_equal(A, B))
fail += not ok
print("    nodes %d/%d  boxes %d/%d  rows %d/%d  identical %s  %s"
      % (stB['nodes'], stA['nodes'], stB['boxes'], stA['boxes'],
         len(B), len(A), np.array_equal(A, B), "ok" if ok else "*** FAIL"))

# ---- 2. interrupted repeatedly, then resumed to completion -----------------
# maxnodes is a deterministic stand-in for a kill: the run stops mid-search
# with a checkpoint on disk, exactly as an interruption leaves it.
print("\n--- 2. five forced stops + resumes must reach the same answer")
clean()
caps = [max(stA['nodes'] // 6, 1) * k for k in (1, 2, 3, 4, 5)]
for i, mn in enumerate(caps):
    st, _ = bnb5.search(LO0=LO0, HI0=HI0, wtol=WTOL, maxdepth=MAXDEPTH, cap=CAP,
                        maxnodes=mn, ckpt=PFX, ckevery=1e9, tag="seg%d" % i)
    print("    stop %d: cap=%-8d nodes=%-8d boxes=%-8d abort=%s"
          % (i, mn, st['nodes'], st['boxes'], st.get('ABORT', False)))
stC, _ = bnb5.search(LO0=LO0, HI0=HI0, wtol=WTOL, maxdepth=MAXDEPTH, cap=CAP,
                     ckpt=PFX, ckevery=1e9, tag="final")
C = canon(spill_of(PFX))
ok = (stC['nodes'] == stA['nodes'] and stC['boxes'] == stA['boxes']
      and C.shape == A.shape and np.array_equal(A, C))
fail += not ok
print("    resumed: nodes %d/%d  boxes %d/%d  rows %d/%d  identical %s  %s"
      % (stC['nodes'], stA['nodes'], stC['boxes'], stA['boxes'], len(C), len(A),
         np.array_equal(A, C), "ok" if ok else "*** FAIL"))

# ---- 3. a crash between spill-write and checkpoint must not duplicate ------
# The spill is flushed before the checkpoint records its row count, so after a
# crash the spill can only be AHEAD.  Those rows get re-derived by the restored
# stack, so the resume must truncate them -- otherwise they are emitted twice
# and the box count silently inflates.
print("\n--- 3. spill rows written past the last checkpoint are dropped")
clean()
bnb5.search(LO0=LO0, HI0=HI0, wtol=WTOL, maxdepth=MAXDEPTH, cap=CAP,
            maxnodes=max(stA['nodes'] // 3, 1), ckpt=PFX, ckevery=1e9, tag="tr")
before = [os.path.getsize(q) for q in bnb5._spill_paths(PFX)]
junk = np.full((777, 48), -9.0)
for q in bnb5._spill_paths(PFX):
    with open(q, "ab") as f: junk.tofile(f)
stD, _ = bnb5.search(LO0=LO0, HI0=HI0, wtol=WTOL, maxdepth=MAXDEPTH, cap=CAP,
                     ckpt=PFX, ckevery=1e9, tag="tr2")
D = canon(spill_of(PFX))
ok = (stD['boxes'] == stA['boxes'] and D.shape == A.shape and np.array_equal(A, D)
      and not (D == -9.0).any())
fail += not ok
print("    boxes %d/%d  rows %d/%d  junk gone %s  identical %s  %s"
      % (stD['boxes'], stA['boxes'], len(D), len(A), not (D == -9.0).any(),
         np.array_equal(A, D), "ok" if ok else "*** FAIL"))

# ---- 4. re-running a finished search is a no-op ----------------------------
print("\n--- 4. re-running a completed checkpoint returns immediately")
n0 = len(spill_of(PFX))
stE, _ = bnb5.search(LO0=LO0, HI0=HI0, wtol=WTOL, maxdepth=MAXDEPTH, cap=CAP,
                     ckpt=PFX, ckevery=1e9, tag="again")
ok = (stE['boxes'] == stA['boxes'] and stE['nodes'] == stA['nodes']
      and len(spill_of(PFX)) == n0)
fail += not ok
print("    nodes %d  boxes %d  rows unchanged %s  %s"
      % (stE['nodes'], stE['boxes'], len(spill_of(PFX)) == n0,
         "ok" if ok else "*** FAIL"))

# ---- 5. a checkpoint from a different problem must be refused --------------
print("\n--- 5. resuming under changed constraints is refused, not silently mixed")
try:
    bnb5.search(LO0=np.zeros(48), HI0=np.ones(48), wtol=WTOL, maxdepth=MAXDEPTH,
                cap=CAP, ckpt=PFX, ckevery=1e9, tag="wrong")
    print("    *** FAIL: accepted a checkpoint for a different box"); fail += 1
except SystemExit as e:
    print("    refused: %s" % str(e).split("\n")[0][:90]); print("    ok")

# ---- 6. spill_to_npy round-trips ------------------------------------------
print("\n--- 6. spill_to_npy writes the same boxes feas.py used to return")
n = bnb5.spill_to_npy(PFX, PFX + "_out_lo.npy", PFX + "_out_hi.npy")
M = canon(np.hstack([np.load(PFX + "_out_lo.npy"), np.load(PFX + "_out_hi.npy")]))
ok = (n == len(A) and np.array_equal(A, M))
fail += not ok
print("    rows %d/%d  identical %s  %s" % (n, len(A), np.array_equal(A, M),
                                            "ok" if ok else "*** FAIL"))
clean()
print("\n%s  (%d failures)"
      % ("ALL CHECKPOINT CONTROLS PASSED" if fail == 0 else "*** CONTROLS NOT PASSED",
         fail))
sys.exit(0 if fail == 0 else 1)
