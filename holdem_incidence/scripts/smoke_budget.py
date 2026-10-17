"""Smoke run + budget measurement: build time, ms per CFR iteration (each variant), residual time,
exact (rational) residual time, and peak memory, for the bridge, the 24-hand game, the control and
every panel game.  Output: results/smoke/budget.json (+ printed table).

usage:  python scripts/smoke_budget.py
"""
import glob
import json
import os
import sys
import time

import psutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from hinc.bestresponse import residuals          # noqa: E402
from hinc.cfr import CFR                          # noqa: E402
from hinc.game import RiverGame                   # noqa: E402
from hinc.strategy import to_exact, normalise_exact  # noqa: E402

OUT = os.path.join(ROOT, "results", "smoke")
os.makedirs(OUT, exist_ok=True)


def rss():
    return psutil.Process().memory_info().rss / 2 ** 20


def main():
    files = ["configs/bridge.json", "configs/expanded24.json", "configs/control_2p.json"] + \
        sorted(glob.glob(os.path.join("configs", "panel", "*.json")))
    rows = []
    for f in files:
        f = f.replace("\\", "/")
        m0 = rss()
        t = time.perf_counter()
        g = RiverGame(json.load(open(os.path.join(ROOT, f))))
        build = time.perf_counter() - t
        rec = {"config": f, "counts": g.counts(), "build_s": round(build, 3), "rss_after_build_MB": round(rss(), 1),
               "rss_delta_build_MB": round(rss() - m0, 1)}
        for var in ("cfr", "cfr+", "dcfr"):
            c = CFR(g, var, seed=1)
            n = 50 if g.D < 30000 else 20
            t = time.perf_counter()
            for _ in range(n):
                c.iterate()
            rec["ms_per_iter_" + var] = round(1000 * (time.perf_counter() - t) / n, 2)
        avg, _ = c.average()
        t = time.perf_counter()
        res = residuals(g, avg)
        rec["residual_eval_s"] = round(time.perf_counter() - t, 3)
        rec["nashconv_after_smoke"] = float(res["nashconv"])
        if g.D <= 7000:
            ex = normalise_exact(g, to_exact(avg, 10 ** 6))
            t = time.perf_counter()
            rx = residuals(g, ex)
            rec["exact_residual_eval_s"] = round(time.perf_counter() - t, 2)
            rec["exact_nashconv_after_smoke"] = float(rx["nashconv"])
        rec["peak_rss_MB"] = round(rss(), 1)
        rows.append(rec)
        print("%-40s D=%6d  build %.1fs  cfr %.1f / cfr+ %.1f / dcfr %.1f ms/it  resid %.2fs  rss %.0f MB" % (
            f, g.D, build, rec["ms_per_iter_cfr"], rec["ms_per_iter_cfr+"], rec["ms_per_iter_dcfr"],
            rec["residual_eval_s"], rec["peak_rss_MB"]))
    doc = {"machine": {"cpus": os.cpu_count(), "ram_GB": round(psutil.virtual_memory().total / 2 ** 30, 1),
                       "python": sys.version.split()[0]},
           "note": "single process; one CFR+/DCFR iteration = three alternating full traversals, CFR = one",
           "games": rows}
    json.dump(doc, open(os.path.join(OUT, "budget.json"), "w"), indent=1)


if __name__ == "__main__":
    os.chdir(ROOT)
    main()
