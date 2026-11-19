# Range endpoint evidence

Of 522 recovered range endpoints, **402 are attained**, **91 are excluded**, and **29 remain unknown**.

ATTAINED means a full 48-coordinate rational profile lies in the specified FAMILY leaf, reaches the bound exactly, satisfies every leaf D-condition, and gives all three players zero exploitability under the independent rules engine. Together with the previously replayed range certificate, this proves an exact extremum.

EXCLUDED means the bound cannot be reached: an open MIX label, a strictly stronger certified bound, or an exact emptiness certificate proves this. It does **not** establish that an excluded bound is a tight infimum or supremum. UNKNOWN means neither claim is established by this bounded search.

Verification: https://github.com/Saayanraocodez/poker/actions/runs/44449523958

All endpoint evidence was checked exactly; numerical least-squares results were used only to propose rational witnesses. Five negative controls reject an invalid profile, wrong endpoint, false open-label exclusion, missing endpoints, and empty evidence.

Historical table flags are not trusted. Comparisons use only matching exact bounds; recovered decimal bounds were rounded outward. Comparable historical label contradictions found: **0**.

## Coverage by leaf

| Leaf | Attained | Excluded | Unknown |
|---|---:|---:|---:|
| 18 | 54 | 0 | 0 |
| 62 | 29 | 8 | 1 |
| 70 | 34 | 4 | 0 |
| 72 | 54 | 0 | 0 |
| 77 | 22 | 14 | 4 |
| 97 | 27 | 10 | 3 |
| 99 | 29 | 7 | 2 |
| 196 | 21 | 14 | 7 |
| 198 | 26 | 10 | 4 |
| 211 | 50 | 4 | 2 |
| 440 | 36 | 4 | 0 |
| 469 | 20 | 16 | 6 |

## Unresolved endpoints

| Leaf | Coordinate | Direction | Bound |
|---|---|---|---|
| 62 | b44 | inf | 4/5 |
| 77 | a44 | inf | 79453/100000 |
| 77 | b44 | inf | 389843/500000 |
| 77 | c23 | sup | 7/12 |
| 77 | c33 | inf | 0 |
| 97 | a44 | inf | 79453/100000 |
| 97 | b44 | inf | 4/5 |
| 97 | c33 | inf | 0 |
| 99 | a44 | inf | 79/100 |
| 99 | b44 | inf | 4/5 |
| 196 | a44 | inf | 51/64 |
| 196 | b21 | sup | 1/6 |
| 196 | b32 | sup | 19/24 |
| 196 | b41 | sup | 2/3 |
| 196 | b44 | inf | 4/5 |
| 196 | c33 | inf | 0 |
| 196 | c33 | sup | 19/24 |
| 198 | a44 | inf | 79453/100000 |
| 198 | b33 | inf | 1/2 |
| 198 | b44 | inf | 4/5 |
| 198 | c33 | inf | 0 |
| 211 | a33 | inf | 0 |
| 211 | b44 | inf | 399609/500000 |
| 469 | a44 | inf | 79453/100000 |
| 469 | b22 | sup | 7/12 |
| 469 | b42 | inf | 31/40 |
| 469 | b44 | inf | 17/32 |
| 469 | c23 | sup | 7/12 |
| 469 | c43 | inf | 775027/1000000 |

## Reproduce

Install numpy, scipy, and sympy, then run:

```sh
python makeD.py
python check_attainment.py
python test_attainment_checker.py
```

The committed evidence lives in `attainment/leaf-*.json.gz`; `attainment/summary.json` records coverage and hashes. Original outer-bound certificates remain unchanged. General global tremble-selection questions are outside this endpoint audit.

## Committed-branch audit

The integrated audit passed on `7eb54013ca76da9b5cbd31c7244e0e5d05db7ae4`, including endpoint evidence and all five negative controls:
https://github.com/Saayanraocodez/poker/actions/runs/44449997950
