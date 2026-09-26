#!/usr/bin/env bash
# Method 5 latency (indicative only): six shapes x {A, C} with pgbench, warm-up discarded, REPS repeated runs,
# per-transaction logs in $WORK/bench (not committed). Prints p50/p95/p99 per run and the median across runs.
# Usage: MODE=prepared|simple N=3000 WARM=300 REPS=3 bash bench/run_bench.sh
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
N=${N:-3000}; WARM=${WARM:-300}; REPS=${REPS:-3}; MODE=${MODE:-prepared}
W=$WORK/bench/$MODE; rm -rf $W; mkdir -p $W
$BUN $SPIKE/harness/queries.ts >/dev/null
# split the generated SQL files into one statement per shape
split_sql() { awk -v dir=$W -v pre=$1 '/^-- /{name=$2; next} NF{print > (dir "/" pre "_" name ".body")}' $2; }
split_sql a $SPIKE/sql/queries_a.sql; split_sql c $SPIKE/sql/queries_c.sql
hdr() { case $1 in
  q1_fetch|q3_hop2|q4_hop3) echo "\\set k random(1, ${NC:-20000})";;
  q2_hop1) echo "\\set k random(1, ${NO:-100000})";;
  q5_range) echo '\set lo random(0, 20000)';;
  q6_update*) printf '%s\n%s\n' '\set k random(1, 20)' '\set n random(1, 5)';;
esac; }
clients() { case $1 in q6_update*) echo 2;; *) echo 1;; esac; }
mk() { f=$W/$1_$2.sql; { hdr $2; sed "s/:s::text/('s' || :n)::text/g; s/= :s /= ('s' || :n) /g" $W/$1_$2.body; } > $f; echo $f; }
echo "== $(psql -X -At -c 'select version()'); mode=$MODE N=$N WARM=$WARM REPS=$REPS"
printf "%-22s %4s %8s %8s %8s %8s %6s\n" query run p50 p95 p99 mean fails
for q in q1_fetch q2_hop1 q3_hop2 q4_hop3 q5_range q6_update; do
  for o in a c; do
    shapes="$q"; [ $o = c ] && [ $q = q6_update ] && shapes="q6_update q6_update_nojournal"
    for s in $shapes; do
      f=$(mk $o $s); cl=$(clients $s)
      pgbench -n -M $MODE -c $cl -j $cl -t $WARM -f $f >/dev/null 2>&1
      for r in $(seq 1 $REPS); do
        rm -f $W/log.*; (cd $W && pgbench -n -M $MODE -c $cl -j $cl -t $N -f $f -l --log-prefix=log > $W/${o}_${s}_$r.out 2>&1)
        cat $W/log.* | awk '{print $3/1000.0}' | sort -n > $W/${o}_${s}_$r.lat
        n=$(wc -l < $W/${o}_${s}_$r.lat)
        p() { awk -v n=$n -v p=$1 'NR==int((n*p)+0.999999){printf "%.3f", $1; exit}' $W/${o}_${s}_$r.lat; }
        fails=$(grep -E "number of failed" $W/${o}_${s}_$r.out | awk '{print $5}')
        printf "%-22s %4s %8s %8s %8s %8s %6s\n" ${o}_$s $r $(p 0.50) $(p 0.95) $(p 0.99) $(awk '{s+=$1} END {printf "%.3f", s/NR}' $W/${o}_${s}_$r.lat) "${fails:-0}"
      done
    done
  done
done
