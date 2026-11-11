"""Re-derive betting branches with the exact prover (enumc7.py) and replay each tree with the
independent checker (checkenum2.py), smallest first, and compare the node counts with the committed
ledger enumc7_summary_nash.txt.  A reproducibility check of the Theorem 4 certificate trees on a
fresh clone -- it re-runs the repo's own prover and checker, so it is NOT an independent proof.

    python makeD.py
    python independent_check/rerun_branches.py <processes> <seconds budget> [max ledger seconds per branch]

Each branch runs enumc7 with 1 worker; <processes> branches run side by side.  Branches whose ledger
time exceeds the third argument (default 130 s on the original 20-26 workers) are skipped: the six
hard branches need hours.  Output: independent_check/rerun_ledger.txt (appended).

Result of 2026-11-11 (Linux, Python 3.13, 4 cores): see rerun_ledger.txt -- every branch run has
checkenum2 OK, 0 failed, 0 missing, and the same node / split / pkill / kill / leaf counts as the ledger.
"""
import subprocess, sys, os, re, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
P = int(sys.argv[1]) if len(sys.argv) > 1 else 2
BUDGET = float(sys.argv[2]) if len(sys.argv) > 2 else 3600
MAXSEC = int(sys.argv[3]) if len(sys.argv) > 3 else 130

ref = {}
for l in open(os.path.join(ROOT, 'enumc7_summary_nash.txt')):
    m = re.search(r'^(\S+)\s+nodes\s+(\d+) split\s+(\d+) pkill\s+(\d+) kill\s+(\d+) leaf\s+(\d+).*enum (\d+)s', l)
    if m: ref[m.group(1)] = (tuple(int(m.group(i)) for i in range(2, 7)), int(m.group(7)))
specs = [s for s in sorted(ref, key=lambda s: ref[s][1]) if ref[s][1] <= MAXSEC]
t00 = time.time()
env = dict(os.environ, KUHN_MODE='nash', KUHN_ORDER='bet')
out = open(os.path.join(HERE, 'rerun_ledger.txt'), 'a', buffering=1)


def one(spec):
    if time.time() - t00 > BUDGET: return
    tag = 'r_' + '_'.join(p.split(':')[1].replace('MIX', 'M') for p in spec.split(',')) + 'N'
    t0 = time.time()
    try:
        rc = subprocess.run([sys.executable, '-u', 'enumc7.py', spec, '1', tag], cwd=ROOT, env=env, capture_output=True, text=True,
                            timeout=max(60, BUDGET - (time.time() - t00))).returncode
    except subprocess.TimeoutExpired:
        out.write('%-34s TIMEOUT after %.0fs (resumable: rerun)\n' % (spec, time.time() - t0)); return
    te = time.time() - t0
    res = subprocess.run([sys.executable, '-u', 'checkenum2.py', 'enumc_%s.jsonl.gz' % tag, '1'], cwd=ROOT, env=env, capture_output=True, text=True)
    last = [l for l in res.stdout.splitlines() if ' nodes ' in l]
    m = re.search(r'(\d+) nodes\s+split (\d+)\s+pkill (\d+)\s+kill (\d+)\s+leaf (\d+) (\{.*?\})\s+failed (\d+)\s+children never seen (\d+).*(OK|NOT VERIFIED)', last[-1]) if last else None
    if not m:
        out.write('%-34s ERROR rc %s  %s\n' % (spec, rc, (res.stdout + res.stderr)[-200:].replace('\n', ' '))); return
    got = tuple(int(m.group(i)) for i in range(1, 6))
    out.write('%-34s nodes %6d split %5d pkill %5d kill %5d leaf %4d %s failed %s missing %s %s  same-as-ledger %s  enum %.0fs (ledger %ds)\n' % (
        spec, *got, m.group(6), m.group(7), m.group(8), m.group(9), got == ref[spec][0], te, ref[spec][1]))


with ThreadPoolExecutor(P) as ex:
    list(ex.map(one, specs))
out.write('# %s  %d branches attempted, %.0fs\n' % (time.strftime('%Y-%m-%d %H:%M'), len(specs), time.time() - t00))
