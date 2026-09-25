#!/bin/sh
# Iterative deepening: each stage proves only what the previous one could not.
# Running depth 18 straight at all 3,045,358 patterns spends depth-18 effort on
# the 80% that depth 8 kills instantly -- 376 of 1523 chunks in 14 hours.  The
# residual shrinks ~5x at the first stage, so every later (more expensive) level
# runs on a far smaller input.
set -e
python -u proveall.py pats_0000.npy        8  14 s08
python -u proveall.py prove_surv_s08.npy  12  14 s12
python -u proveall.py prove_surv_s12.npy  16  14 s16
python -u proveall.py prove_surv_s16.npy  20  14 s20
python -u proveall.py prove_surv_s20.npy  24  14 s24
python -u proveall.py prove_surv_s24.npy  28  14 s28
echo CHAINDONE
