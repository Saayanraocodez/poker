"""Committed FAMILY labels, independently matched by the 81-cell replay.
No placeholder rows or historical enumeration arrays are needed.
"""
import json
from pathlib import Path

def family_labels():
    data = json.loads((Path(__file__).parent / "independent_check/family_leaves.json").read_text())
    out = {int(k): v for k, v in data.items()}
    assert set(out) == {18,62,70,72,77,97,99,196,198,211,440,469}
    assert all(len(v) == 48 and all(x in (0,1,2,3) for x in v) for v in out.values())
    return out
