"""Train candidate profiles with full-traversal CFR variants, in parallel, resumably.

For each (game, variant, seed): results/<group>/<game>/<variant>_s<seed>/
    ckpt.npz / ckpt.json   regrets, average numerators and weights, iteration, history (resume)
    history.csv            convergence history (avg and current strategy residuals, utilities)
    policy_avg.json        the AVERAGE strategy, complete three-player profile, with the
                           information-set table, avg weights and the zero-weight list
    policy_cur.json        the final CURRENT strategy
    run.json               game record, variant, seed, averaging rule, wall time, final residuals

usage:  python scripts/run_training.py pilot|panel|potsweep|control [workers] [iterations]
        (re-running continues every run from its checkpoint up to the planned iteration count)
"""
import csv
import glob
import json
import os
import sys
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
RESULTS = os.environ.get("HINC_RESULTS", os.path.join(ROOT, "results"))   # scratch runs: point elsewhere
from hinc import plan                             # noqa: E402
from hinc.cfr import CFR                          # noqa: E402
from hinc.game import RiverGame                   # noqa: E402
from hinc.strategy import save_profile            # noqa: E402

AVERAGING = {"cfr": "uniform weights; simultaneous updates; regret matching",
             "cfr+": "linear weights max(t - delay, 0), delay 0; alternating updates; regret matching+",
             "dcfr": "weights t^2 (DCFR gamma=2); alternating; regrets discounted alpha=1.5, beta=0"}


def jobs(group, iterations=None):
    if group == "pilot":
        cfgs, P = [plan.PILOT["game"]], plan.PILOT
    elif group == "panel":
        cfgs, P = sorted(glob.glob(os.path.join(ROOT, "configs", "panel", "*.json"))), plan.PANEL
    elif group == "potsweep":
        cfgs, P = sorted(glob.glob(os.path.join(ROOT, "configs", "potsweep", "*.json"))), plan.POTSWEEP
    elif group == "control":
        cfgs, P = [plan.CONTROL["game"]], plan.CONTROL
    else:
        raise SystemExit("group must be pilot, panel, potsweep or control")
    out = []
    for c in cfgs:
        for v in P["variants"]:
            for s in P["seeds"]:
                out.append((group, os.path.join(ROOT, c) if not os.path.isabs(c) else c, v, s, iterations or P["iterations"]))
    return out


def fixed_rows(g, spec):
    """Declared restrictions.  'P1_open_check': P1's opening forced to check for every hand."""
    if spec is None:
        return None
    if spec == "P1_open_check":
        return {I.index: [1.0, 0.0] for I in g.isets if I.player == 0 and I.history == ""}
    raise ValueError(spec)


def run(job):
    group, cfgpath, variant, seed, iters = job[:5]
    spec = job[5] if len(job) > 5 else None
    cfg = json.load(open(cfgpath))
    g = RiverGame(cfg)
    d = os.path.join(RESULTS, group, cfg["name"], "%s_s%d" % (variant.replace("+", "p"), seed))
    os.makedirs(d, exist_ok=True)
    ck = os.path.join(d, "ckpt")
    if os.path.exists(ck + ".json"):
        c = CFR.load(g, ck)
    else:
        c = CFR(g, variant, seed=seed, fixed=fixed_rows(g, spec))
    cps = [t for t in plan.CHECKPOINTS if t <= iters] + [iters]
    logf = open(os.path.join(d, "log.txt"), "a")
    c.run(iters, checkpoints=cps, ckpt_path=ck, log=lambda s: (logf.write(s + "\n"), logf.flush()))
    logf.close()
    avg, zero = c.average()
    zero_ids = [g.isets[i].id for i in zero]
    common = {"variant": variant, "seed": seed, "iterations": c.t, "averaging": AVERAGING[variant],
              "restriction": spec}
    save_profile(os.path.join(d, "policy_avg.json"), g, avg,
                 extra={"which": "average", **common, "avg_weight": [float(w) for w in c.W],
                        "zero_weight_infosets": zero_ids,
                        "zero_weight_fallback": "final current strategy (documented in hinc/cfr.py)"})
    save_profile(os.path.join(d, "policy_cur.json"), g, c.current(), extra={"which": "current", **common})
    with open(os.path.join(d, "history.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "wall_s", "avg_r1", "avg_r2", "avg_r3", "avg_max_r", "avg_nashconv",
                    "cur_r1", "cur_r2", "cur_r3", "cur_nashconv", "avg_u1", "avg_u2", "avg_u3",
                    "zero_weight_infosets", "infosets_reach_below_1e-9"])
        for h in c.history:
            w.writerow([h["t"], h["wall_s"]] + h["avg"]["r"] + [h["avg"]["max_r"], h["avg"]["nashconv"]] +
                       h["cur"]["r"] + [h["cur"]["nashconv"]] + h["avg"]["u"] +
                       [h["zero_weight_infosets"], h["infosets_reach_below_1e-9"]])
    last = c.history[-1]
    rec = {"game": g.record(), **common, "wall_s": c.wall, "final": last,
           "zero_weight_infosets": zero_ids, "dir": os.path.relpath(d, RESULTS).replace("\\", "/")}
    json.dump(rec, open(os.path.join(d, "run.json"), "w"), indent=1)
    return rec["dir"], last["avg"]["nashconv"], c.wall


def main(argv):
    group = argv[1]
    workers = int(argv[2]) if len(argv) > 2 else min(24, os.cpu_count() - 2)
    js = jobs(group, int(argv[3]) if len(argv) > 3 else None)   # [iterations]: a declared continuation
    print("%d runs, %d workers" % (len(js), workers), flush=True)
    with Pool(workers) as pool:
        for d, nc, wall in pool.imap_unordered(run, js):
            print("done %-50s NashConv(avg) %.3e  %.0fs" % (d, nc, wall), flush=True)


if __name__ == "__main__":
    main(sys.argv)
