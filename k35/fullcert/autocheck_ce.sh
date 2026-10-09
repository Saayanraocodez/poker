#!/bin/bash
# wait for each region proposer; when it ends with a candidate (LP value < 0), run both exact checkers
cd /c/Users/raosa/OneDrive/Documents/poker/k35
export KUHN_CARDS=5 OMP_NUM_THREADS=2
pending="open4pos open5one open3zero open1zero open1zero_open2zero"
while [ -n "$pending" ]; do
  next=""
  for r in $pending; do
    L=fullcert/log_ce_$r.txt
    if grep -q "wrote fullcert" $L 2>/dev/null; then
      if grep -q "candidate emptiness certificate" $L; then
        python fullcheck35.py fullcert/${r}_ce.json > fullcert/check_ce_$r.txt 2>&1 < /dev/null
        python fullcheck35b.py fullcert/${r}_ce.json >> fullcert/check_ce_$r.txt 2>&1 < /dev/null
        echo "$r: $(grep -E 'CERTIFIED|NOT a' fullcert/check_ce_$r.txt | tr '\n' ' ')"
      else
        echo "$r: proposer found no certificate: $(grep 'local search finds' $L)"
      fi
    elif grep -q Traceback $L 2>/dev/null; then
      echo "$r: proposer CRASHED"
    else
      next="$next $r"
    fi
  done
  pending="$next"
  [ -n "$pending" ] && sleep 30
done
echo "autocheck_ce done"
