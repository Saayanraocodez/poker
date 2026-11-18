# Recovered supplemental certificates

The fresh-clone gap is closed for the range-bound and sequential-pattern certificate sets.
Generation used committed FAMILY labels, already matched against the complete 81-cell proof.
No historical enumeration arrays or numerical sample databases are required by these checkers.

## Independent verification

- 522 range-bound certificates, covering both directions of every listed coordinate in all twelve leaves.
- Twelve complete sequential-pattern certificates, with every required off-path coordinate enumerated.
- An intentionally incomplete coordinate list is rejected by the checker.
- Missing inputs, empty certificate sets, and failed proofs produce a nonzero exit status.

Verification run: https://github.com/Saayanraocodez/poker/actions/runs/44222640083
Machine-readable verdict and SHA-256 hashes: `recovered-verification.json`.
Exact replay logs: `recovered-checknefull.py.log` and `recovered-checkseqcert.py.log`.

## Scope of the range recovery

`nefull_certs.json.gz` contains regenerated **outer-bound** proofs, not a byte-for-byte restoration
of the missing historical file. Rational bounds were reproduced exactly. Displayed decimal bounds
were moved outward by one final decimal unit (1e-6) before exact certification because the original
unrounded rationals were unavailable. Historical attainment flags and witnesses were not copied:
the recovered records explicitly leave attainment unknown. The separate 36 sharpened certificates
and their attaining witness remain available and independently checked.

This recovery does not settle global tremble-selection uniqueness or arbitrary positive tremble
shapes; those are mathematical questions beyond the missing-file repair.

## Fresh-clone replay

Install numpy, scipy, and sympy, then run:

```sh
python makeD.py
python checkD.py
python checknefull.py
python checkseqcert.py
python audit_remaining.py
```

The audit explicitly supplies all twelve sequential filenames. `checkseqcert.py` without arguments
checks all files found and fails if there are none; use the audit for the required full set.

## Regeneration

```sh
python makeD.py
python seqcert.py 4
```

For each leaf in `independent_check/family_leaves.json`, run
`python recover_ranges.py LEAF`, then `python check_recovered.py`.
The latter merges the twelve range batches, checks the full key set, replays both proof sets,
and runs the negative coverage test.

`nefull.py` and `nefull_refine.py` also load the committed family labels directly.
Historical numerical samples are optional search seeds for `nefull.py`, never trusted proof inputs.

## Committed-branch audit

The complete audit also passed on commit `147a68638c973d0980efdd82b12a1d7101d10e3f`:
https://github.com/Saayanraocodez/poker/actions/runs/44223799547

`audit-results/summary.json` records nine passing checks and the separately scoped uniform-tremble diagnostic; no certificate check is blocked.
