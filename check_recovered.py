"""Assemble recovered bounds and independently replay complete supplemental coverage."""
import gzip,json,subprocess,sys,hashlib
from pathlib import Path
from family_data import family_labels

def main():
    certs={}
    for k in family_labels():
        path=Path(f"recovered-ranges-{k}.json.gz")
        with gzip.open(path,"rt") as f: part=json.load(f)
        assert part and all(key.startswith(f"{k}:") for key in part), path
        assert not (certs.keys() & part.keys()), "Duplicate range keys"
        certs.update(part)
    with gzip.open("nefull_certs.json.gz","wt") as f: json.dump(certs,f,sort_keys=True)
    results=[]
    for script,args in [
        ("checknefull.py",[]),
        ("checkseqcert.py",[f"seqcert_{k}.jsonl.gz" for k in family_labels()])
    ]:
        r=subprocess.run([sys.executable,script,*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(r.stdout,flush=True)
        Path("recovered-"+script+".log").write_text(r.stdout)
        results.append({"script":script,"returncode":r.returncode})
        if r.returncode: raise SystemExit(r.returncode)
    # Negative coverage test: a valid witness for one pattern cannot cover an omitted coordinate.
    import checkseqcert as CK, tempfile
    src=Path("seqcert_62.jsonl.gz")
    with gzip.open(src,"rt") as f: records=[json.loads(line) for line in f]
    records[0]["decide"] = records[0]["decide"][:-1]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"incomplete.jsonl.gz"
        with gzip.open(path,"wt") as f:
            for rec in records: f.write(json.dumps(rec)+"\n")
        try: CK.check_file(path)
        except CK.Bad as ex:
            assert "decide omits" in str(ex), str(ex)
        else: raise AssertionError("Incomplete coordinate coverage was accepted")
    paths=[Path("nefull_certs.json.gz")]+[Path(f"seqcert_{k}.jsonl.gz") for k in family_labels()]
    summary={"range_certificates":len(certs),"sequential_leaves":len(family_labels()),
        "checks":results,"negative_coverage_test":"PASS",
        "scope":"Outer range bounds and full sequential pattern certificates. Range attainment is not asserted.",
        "sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    Path("recovered-verification.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("ALL RECOVERED CERTIFICATES VERIFIED",flush=True)
if __name__=="__main__": main()
