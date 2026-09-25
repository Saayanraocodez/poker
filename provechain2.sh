#!/bin/sh
set -e
python -u proveall.py prove_surv_s08.npy  12  14 t12
python -u proveall.py prove_surv_t12.npy  16  14 t16
python -u proveall.py prove_surv_t16.npy  20  14 t20
python -u proveall.py prove_surv_t20.npy  24  14 t24
echo CHAINDONE
