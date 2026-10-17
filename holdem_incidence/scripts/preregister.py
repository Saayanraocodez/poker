"""Freeze the experiment configurations and the analysis plan BEFORE any panel profile exists.

Writes results/preregistration.json: UTC timestamp, SHA-256 of every config file and of
hinc/plan.py, the plan constants, and the budget rationale (from results/smoke/budget.json).
Refuses to overwrite an existing preregistration (amendments are appended with --amend "text").

usage:  python scripts/preregister.py            |   python scripts/preregister.py --amend "why"
"""
import datetime
import glob
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from hinc import plan  # noqa: E402

PATH = os.path.join(ROOT, "results", "preregistration.json")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def main(argv):
    if len(argv) > 2 and argv[1] == "--amend":
        doc = json.load(open(PATH))
        doc.setdefault("amendments", []).append({"utc": now(), "text": argv[2], "plan_sha256": sha(os.path.join(ROOT, "hinc", "plan.py")),
                                                 "configs_sha256": {os.path.relpath(f, ROOT).replace("\\", "/"): sha(f) for f in cfgs()}})
        json.dump(doc, open(PATH, "w"), indent=1)
        print("amendment recorded")
        return
    if os.path.exists(PATH):
        raise SystemExit("preregistration exists; use --amend")
    budget = json.load(open(os.path.join(ROOT, "results", "smoke", "budget.json")))
    doc = {"utc": now(),
           "statement": ("Configurations and analysis plan fixed before any panel profile was trained or any "
                         "incidence result on the expanded games was examined.  Candidate profiles are selected "
                         "by residual only; every run passing the residual criterion is analysed; negative "
                         "findings are retained."),
           "configs_sha256": {os.path.relpath(f, ROOT).replace("\\", "/"): sha(f) for f in cfgs()},
           "plan_sha256": sha(os.path.join(ROOT, "hinc", "plan.py")),
           "plan": {k: getattr(plan, k) for k in dir(plan) if k.isupper()},
           "budget_rationale": {
               "measured": [{"config": g["config"], "ms_per_iter_dcfr": g["ms_per_iter_dcfr"],
                             "ms_per_iter_cfr+": g["ms_per_iter_cfr+"], "peak_rss_MB": g["peak_rss_MB"]}
                            for g in budget["games"]],
               "choice": ("pilot: 30,000 iterations x 2 variants x 6 seeds on the 24-hand game (~5 min/run at "
                          "10.4 ms/iter); panel: 12,000 DCFR iterations x 3 seeds (<= 8.5 min/run at <= 42 ms/iter); "
                          "control: 5,000 CFR+ iterations x 2 seeds.  Runs execute in parallel, one process each, "
                          "< 200 MB each.  Full traversal throughout: sampling (MCCFR) is not needed at these sizes.")}}
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    json.dump(doc, open(PATH, "w"), indent=1)
    print("preregistration written:", PATH)


def cfgs():
    return sorted(glob.glob(os.path.join(ROOT, "configs", "*.json")) + glob.glob(os.path.join(ROOT, "configs", "*", "*.json")))


if __name__ == "__main__":
    main(sys.argv)
