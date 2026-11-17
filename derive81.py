"""Derive the certificate trees that proof34/ still lacks (enumc7.py is resumable: rerun to continue).

    python makeD.py
    python derive81.py [workers=4] [cell spec ...]      default: every cell without a complete tree

Each cell is derived by enumc7 under KUHN_MODE=nash, KUHN_ORDER=bet and copied to
proof34/cell_<labels>.jsonl.gz when its checkpoint says complete.  Then:  python check81.py proof34
Trees from an earlier machine (enumc_c7_*N.jsonl.gz) can simply be copied into a directory and given to
check81.py instead: it reads the cell from each file's header.
Sizes: the 75 cells present on 2026-11-17 hold 6,912 nodes; the missing ones are the silent cell
(about 4,700 nodes) and five large betting cells (about 26,000 nodes; hours on 4 cores).
"""
import sys, os, json, glob, gzip, shutil, subprocess
import check81

nw = sys.argv[1] if len(sys.argv) > 1 else "4"
have = set()
for f in glob.glob(os.path.join("proof34", "*.jsonl.gz")):
    try: have.add(json.loads(gzip.open(f, "rt").readline())["spec"])
    except Exception: pass
todo = sys.argv[2:] or [c for c in check81.cells() if c not in have]
env = dict(os.environ, KUHN_MODE="nash", KUHN_ORDER="bet", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
for spec in todo:
    lab = "_".join(p.split(":")[1].replace("MIX", "M") for p in spec.split(","))
    tag = "p34_" + lab
    print("deriving", spec, flush=True)
    rc = subprocess.call([sys.executable, "-u", "enumc7.py", spec, nw, tag], env=env)
    ck = "enumc_%s.ckpt" % tag
    if rc == 0 and os.path.exists(ck) and json.load(open(ck)).get("complete"):
        shutil.copy("enumc_%s.jsonl.gz" % tag, os.path.join("proof34", "cell_%s.jsonl.gz" % lab))
        print("   -> proof34/cell_%s.jsonl.gz" % lab, flush=True)
    else:
        print("   not complete (rc %s); rerun to resume" % rc, flush=True)
