#!/bin/bash
# wait for each region proposer; when it ends with a candidate (LP value < 0), run both exact checkers
cd /c/Users/raosa/OneDrive/Documents/poker/k35
export KUHN_CARDS=5 OMP_NUM_THREADS=2
pending="open4pos open5one open5zero open3zero open3one open1zero open1one open2one open1zero_open2zero"
while [ -n "$pending" ]; do
  next=""
  for r in $pending; do
    L=fullcert/log_$r.txt
    if grep -q "wrote fullcert" $L 2>/dev/null; then
      if grep -q "candidate emptiness certificate" $L; then
        python fullcheck35.py fullcert/$r.json > fullcert/check_$r.txt 2>&1 < /dev/null
        python fullcheck35b.py fullcert/$r.json >> fullcert/check_$r.txt 2>&1 < /dev/null
        echo "$r: $(grep -E 'CERTIFIED|NOT a' fullcert/check_$r.txt | tr '\n' ' ')"
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
echo "autocheck done"
