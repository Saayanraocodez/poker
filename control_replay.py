"""Control for enumc6's parallel replay: on a partial output, replay(nw=1) and replay(nw=8) must
give the same unfinished nodes with bit-identical states.  usage:  python control_replay.py <tag> <spec>"""
import os, sys, time
os.environ.setdefault("KUHN_MODE", "nash"); os.environ.setdefault("KUHN_ORDER", "bet")
import numpy as np
import enumc6

if __name__ == "__main__":
    tag, spec = sys.argv[1], sys.argv[2]
    header, seen, splits, cnt, maxid, tail = enumc6.scan("enumc_%s.jsonl.gz" % tag)
    print("records %d  splits %d  tail %s" % (len(seen), len(splits), tail))
    res = {}
    for nw in (1, 8):
        t0 = time.time(); opens, nneed = enumc6.replay(spec, seen, splits, nw)
        res[nw] = {o[0]: o[1:] for o in opens}
        print("nw=%d: %d unfinished nodes (%d distinct), %d ancestor splits, %.1fs" % (nw, len(opens), len(res[nw]), nneed, time.time() - t0))
    a, b = res[1], res[8]
    same_ids = set(a) == set(b)
    diff = [i for i in a if i in b and not (np.array_equal(a[i][0], b[i][0]) and np.array_equal(a[i][1], b[i][1])
                                            and np.array_equal(a[i][2], b[i][2]) and a[i][3] == b[i][3] and a[i][4] == b[i][4])]
    print("same unfinished ids: %s   states differing: %d   -> %s" % (same_ids, len(diff), "PASS" if same_ids and not diff else "FAIL"))
