#!/bin/bash
# one P1-opening cell: CCE proposer, then both exact checks if it produced a candidate
cd /c/Users/raosa/OneDrive/Documents/poker/k35
export KUHN_CARDS=5 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
r=$1
python fullprop35v2.py $r fullcert/cell_$r.json 400 48 > fullcert/log_cell_$r.txt 2>&1 < /dev/null
if grep -q "candidate emptiness" fullcert/log_cell_$r.txt; then
  python fullcheck35.py fullcert/cell_$r.json > fullcert/check_cell_$r.txt 2>&1 < /dev/null
  python fullcheck35b.py fullcert/cell_$r.json >> fullcert/check_cell_$r.txt 2>&1 < /dev/null
  echo "$r: $(grep -cE '^CERTIFIED' fullcert/check_cell_$r.txt)/2 certified  $(grep -E 'NOT a' fullcert/check_cell_$r.txt | head -1)"
else
  echo "$r: no candidate ($(grep 'local search finds' fullcert/log_cell_$r.txt | cut -c1-80))"
fi
