"""Negative controls for endpoint verification."""
import copy,gzip,json,tempfile
from pathlib import Path
import check_attainment as CK
files=sorted(Path("attainment").glob("leaf-*.json.gz"))
data={}
for path in files:
    with gzip.open(path,"rt") as f: data.update(json.load(f))
key=next(k for k,r in data.items() if r["status"]=="ATTAINED")
def rejected(records,full=False):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"bad.json.gz"
        with gzip.open(p,"wt") as f: json.dump(records,f)
        try: CK.check([p],full=full)
        except (AssertionError,ValueError,KeyError,CK.C.Bad): return
        raise AssertionError("Invalid evidence was accepted")
bad=copy.deepcopy(data[key]); bad["profile"][CK.K.NAME_IDX[key.split(":")[1]]]="2"
rejected({key:bad})
bad=copy.deepcopy(data[key]); bad["T"]=str(CK.F(bad["T"])+1)
rejected({key:bad})
bad=copy.deepcopy(data[key]); bad["status"]="EXCLUDED";bad["kind"]="open_label"
# ATTAINED at a genuine leaf endpoint cannot be excluded by its MIX label.
rejected({key:bad})
rejected({key:data[key]},full=True)
rejected({})
print("ALL FIVE NEGATIVE CONTROLS PASSED")
