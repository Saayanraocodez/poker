"""Summarise probe_knuth.jsonl: Knuth estimates (mean over walks of sum w*t) per branch and
context, split by ladder outcome; 'saved' = time a rung-0-only ladder would not spend, and
'lost kills' = estimated nodes such a ladder would no longer kill (killed at rung 1-3)."""
import json, collections
W = [json.loads(l) for l in open("probe_knuth.jsonl")]
by = collections.defaultdict(list)
for w in W: by[w["spec"]].append(w)
grand = collections.Counter()
for spec, ws in sorted(by.items()):
    n = len(ws); acc = collections.Counter()
    for w in ws:
        for r in w["rows"]:
            t = sum(r["ts"]); c = r["ctx"]; x = r["w"] / n
            acc[c, "time"] += x * t; acc[c, "calls"] += x
            if r["rung"] == -1: acc[c, "fail_time"] += x * t; acc[c, "fails"] += x
            if r["ts"]: acc[c, "saved"] += x * (t - r["ts"][0])
            if r["rung"] in (1, 2, 3): acc[c, "lost"] += x
    ends = collections.Counter(w["end"] for w in ws)
    print("%s  walks %d  ends %s  max depth %d" % (spec, n, dict(ends), max(w["depth"] for w in ws)))
    for c in sorted({k[0] for k in acc}):
        print("   %-9s est calls %10.0f  time %10.0f s  in fails %10.0f s  rung0-only saves %10.0f s  lost kills %8.0f" % (
            c, acc[c, "calls"], acc[c, "time"], acc[c, "fail_time"], acc[c, "saved"], acc[c, "lost"]))
        for k in ("time", "fail_time", "saved", "lost", "calls"): grand[c, k] += acc[c, k]
print("ALL SIX")
for c in sorted({k[0] for k in grand}):
    print("   %-9s est calls %10.0f  time %10.0f s  in fails %10.0f s  rung0-only saves %10.0f s  lost kills %8.0f" % (
        c, grand[c, "calls"], grand[c, "time"], grand[c, "fail_time"], grand[c, "saved"], grand[c, "lost"]))
