"""Recreate the two git-ignored files that the Theorem 5 / 6 scripts index into, in the leaf numbering
the committed artifacts use (nefull_ranges.txt, nefull_systems.txt, seq_<leaf>.json, perf_witnesses.json):

    enum6_pat_silentR.npy     label vectors, row = leaf id (only the 12 FAMILY leaves are filled)
    symleaf_silentR.npz       verdicts (FAMILY at those 12 rows)

enuml.py numbers leaves in the order its workers finish, so a fresh enumeration gives the same twelve
FAMILY leaves under different ids (610 leaves on a 3-worker re-run against 668 originally).  The labels
here come from independent_check/family_leaves.json, which that re-run produced and matched to the
committed ids by their MIX and DC sets.  With these two files checkseq.py, forcecheck.py, perfwit.py,
qperf.py, ranges_table.py, seqrun.py, ... run on a fresh clone.

usage:  python makeD.py ; python make_leaf_files.py
"""
import json, os
import numpy as np

FAMILY = 4                                   # symleaf.VERD.index("FAMILY")
lv = {int(k): v for k, v in json.load(open(os.path.join("independent_check", "family_leaves.json"))).items()}
n = max(lv) + 1
L = np.full((n, 48), 9, dtype=np.int8); vd = np.full(n, -1, dtype=np.int8)
for k, v in lv.items(): L[k] = v; vd[k] = FAMILY
for f in ("enum6_pat_silentR.npy", "symleaf_silentR.npz"):
    if os.path.exists(f): raise SystemExit("%s exists; not overwriting" % f)
np.save("enum6_pat_silentR.npy", L)
np.savez("symleaf_silentR.npz", verdict=vd, tsec=np.zeros(n), idx=np.arange(n))
print("wrote enum6_pat_silentR.npy and symleaf_silentR.npz for leaves", sorted(lv))
