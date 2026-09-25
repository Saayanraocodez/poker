#!/bin/sh
# Continuation past depth 24.  The per-stage rate stopped collapsing once the
# block-size bug was fixed, so further levels keep paying and each runs on a
# smaller input.
#
# The wait condition matters: `prove_surv_t24.npy` is rewritten at EVERY
# checkpoint, not just at completion, so testing for that file starts the next
# stage on a PARTIAL residual -- depth 28 would then "prove" against a pattern
# set missing everything not yet processed, and the final count would be wrong
# while looking clean.  Wait for provechain2's own CHAINDONE instead.
set -e
while ! grep -q CHAINDONE log_provechain2.txt 2>/dev/null; do sleep 60; done
python -u proveall.py prove_surv_t24.npy  28  14 t28
python -u proveall.py prove_surv_t28.npy  32  14 t32
python -u proveall.py prove_surv_t32.npy  36  14 t36
echo CHAIN3DONE
