"""Bounded fresh-clone audit. Missing proof inputs are BLOCKED, never PASS."""
import sys, subprocess, json, re, time
from pathlib import Path
out = Path("audit-results"); out.mkdir(exist_ok=True)
results=[]
def run(name,args,cwd=".",marker=None):
    start=time.time()
    try:
        p=subprocess.run([sys.executable,*args],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=1800)
        text=p.stdout; ok=p.returncode==0 and (marker is None or marker(text))
        status="PASS" if ok else "FAIL"
    except subprocess.TimeoutExpired as ex:
        text=str(ex); status="FAIL"
    (out/(name+".log")).write_text(text)
    results.append({"check":name,"status":status,"seconds":round(time.time()-start,1)})
    print(name,status,flush=True)
    print(text,flush=True)
run("independent-game",["independent_check/check_34.py"],marker=lambda s:"ALL CHECKS PASSED" in s and "skipped:" not in s)
run("gradient-generation",["makeD.py"])
run("range-generator-inputs",["-c","import nefull, nefull_refine; assert len(nefull.family_labels()) == 12; assert len(nefull._leaf(18)[0]) == 48; print('Committed family inputs loaded')"])
run("gradient-recomputation",["checkD.py"],marker=lambda s:"48 of 48 gradients agree" in s and "*** FAIL" not in s)
run("sharpened-ranges",["check_sharpened.py"],marker=lambda s:bool(re.search(r"certificates: 36 verified, 0 failed; exact witnesses: [1-9][0-9]* verified, 0 failed",s)))
run("stored-ce-witnesses",["audit_ce_witnesses.py"],marker=lambda s:"ALL STORED CE WITNESSES VERIFIED" in s)
run("ante-witnesses",["pot_exact.py"],cwd="continuations",marker=lambda s:"ALL EXACT CHECKS PASSED" in s)
run("uniform-tremble-diagnostic",["tremble_uniform_symbolic.py"])
if results[-1]["status"] == "PASS": results[-1]["status"] = "DIAGNOSTIC_ONLY"
for name,inputs in [
    ("original-range-certificates",["nefull_certs.json.gz","independent_check/family_leaves.json"]),
    ("sequential-pattern-certificates",["seqcert_"+str(k)+".jsonl.gz" for k in (18,62,70,72,77,97,99,196,198,211,440,469)])
]:
    missing=[p for p in inputs if not Path(p).is_file()]
    if missing:
        results.append({"check":name,"status":"BLOCKED","missing":missing})
    elif name == "original-range-certificates":
        run(name,["checknefull.py"],marker=lambda s:"range certificates: 522 verified, 0 failed" in s)
    else:
        run(name,["checkseqcert.py",*inputs],marker=lambda s:"12 files, 0 failed  OK" in s)
run("range-endpoint-evidence",["check_attainment.py"],marker=lambda s:"ALL ENDPOINT EVIDENCE VERIFIED" in s)
run("range-endpoint-negative-controls",["test_attainment_checker.py"],marker=lambda s:"ALL FIVE NEGATIVE CONTROLS PASSED" in s)
summary={"scope":"Available committed supplemental artifacts; excludes the already completed 81-cell replay and historical data outside git.","results":results}
(out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
sys.exit(any(r["status"]=="FAIL" for r in results))
