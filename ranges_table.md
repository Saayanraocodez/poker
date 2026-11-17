| coordinate | role | over all equilibria | A | B | C |
|---|---|---|---|---|---|
| `a13` | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| `a14` | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| `a23` | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| `a24` | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| `a33` | on path (Table 3) | [0, 1/2] | [0, 1/2] | [0, 1/2] | [0, 1/2] |
| `a34` | off path | [0, 1] | [0, 1] | [0, 1ᶜ] | [0, 1] |
| `a43` | off path | [1, 1] | [1, 1] | [1, 1] | [1, 1] |
| `a44` | off path | [0, 1] | [0, 1] | [0ᶜ, 1] | [0, 1] |
| `b11` | on path (Table 3) | [0, 1/4] | [0, 1/4] | [0, 1/4ᶜ] | [0, 1/4] |
| `b12` | off path | [0, 0.41668ᶜ] | [0, 0.41668ᶜ] | [0, 5/12] | [0, 0.27779ᶜ] |
| `b21` | on path (Table 3) | [0, 1/4] | [0, 1/4] | [0, 1/4] | [0, 1/6] |
| `b22` | off path | [0, 0.58334ᶜ] | [0, 0.58334ᶜ] | [0, 7/12] | [0, 0.38890ᶜ] |
| `b23` | on path (Table 3) | [0, 1/8] | [0, 0] | [0, 0] | [0, 1/8] |
| `b32` | off path | [0, 15/16] | [0, 15/16] | [0, 15/16ᶜ] | [0, 19/24] |
| `b33` | on path (Table 3) | [1/2, 7/8] | [1/2, 7/8] | [1/2ᶜ, 7/8] | [1/2, 3/4] |
| `b41` | on path (Table 3) | [0, 1] | [0, 1] | [0, 1] | [0, 2/3] |
| `b42` | off path | [31/40ᶜ, 1] | [0.77579ᶜ, 1] | [31/40ᶜ, 1] | [0.77579ᶜ, 1] |
| `b43` | off path | [0, 1] | [0, 1] | [0, 1] | [1, 1] |
| `b44` | off path | [0, 1] | [0, 1] | [0, 1] | [4/5, 1] |
| `c11` | on path (Table 3) | [0, 1/2] | [0, 0] | [0⁻, 1/2⁻] | [1/2, 1/2] |
| `c12` | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| `c13` | off path | [0, 0.52623ᶜ] | [0, 0.52623ᶜ] | [0, 0.52623ᶜ] | [0, 0.34509ᶜ] |
| `c14` | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| `c21` | on path (Table 3) | [0, 1/2] | [1/2, 1/2] | [0⁻, 1/2⁻] | [0, 0] |
| `c22` | off path | [0, 0] | [0, 0] | [0, 0] | [0, 0] |
| `c23` | off path | [0, 7/12] | [0, 7/12ᶜ] | [0, 7/12] | [0, 0.38890ᶜ] |
| `c24` | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |
| `c32` | off path | [0, 1/2] | [0, 1/2] | [0, 1/2] | [0, 1/2] |
| `c33` | off path | [0, 15/16] | [0, 15/16ᶜ] | [0, 15/16] | [0, 19/24] |
| `c34` | off path | [0, 1] | [0, 1] | [0, 1ᶜ] | [0, 1] |
| `c42` | off path | [1, 1] | [1, 1] | [1, 1] | [1, 1] |
| `c43` | off path | [0.77503ᶜ, 1] | [0.77579ᶜ, 1] | [0.77503ᶜ, 1] | [0.77579ᶜ, 1] |
| `c44` | off path | [0, 1] | [0, 1] | [0, 1] | [0, 1] |

‡ `b44` is free in [0, 1] in leaves 70, 440 (private, or own-unreached where `b41 = 1`). In the leaves where it is constrained: all [17/32ᶜ, 1], A [0.77969⁻, 1], B [17/32ᶜ, 1], C [4/5, 1].
‡ `b43` equals 1 wherever `b41 < 1` (a reached call with the top card); in the two leaves with `b41 = 1` (70, 440) it is own-unreached and free.

36 bounds are sharper than nefull_ranges.txt: certified by sharpen_ranges.py at a rational just outside the best equilibrium value found, and replayed by check_sharpened.py (2026-11-17).

Marks: a bare number is attained (exact rational witness in the leaf, verified); ⁻ = certified strict bound (not attained); ᶜ = certified bound, attainment undecided at the search precision (the true extremum lies between the best known equilibrium value and this bound).
