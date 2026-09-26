#!/usr/bin/env bash
# Tail check for skewed fan-out: 2- and 3-hop shapes started only from the heaviest 1% of customers (ids 1..200,
# 26-728 orders each), prepared, 3 x 1000 timed transactions after 100 warm-up.
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
W=$WORK/bench/heavy; rm -rf $W; mkdir -p $W
awk -v dir=$W '/^-- /{name=$2; next} NF{print > (dir "/a_" name ".body")}' $SPIKE/sql/queries_a.sql
awk -v dir=$W '/^-- /{name=$2; next} NF{print > (dir "/c_" name ".body")}' $SPIKE/sql/queries_c.sql
echo "== $(psql -X -At -c 'select version()'); prepared; start customers 1..${TOP:-200}"
echo "orders per start customer: $(psql -X -At -c "select min(n)||'..'||max(n)||' (median '||percentile_disc(0.5) within group (order by n)||')' from (select count(*) n from sales.orders where \"customerId\" <= ${TOP:-200} group by \"customerId\") s")"
printf "%-10s %4s %8s %8s %8s\n" query run p50 p95 p99
for q in q3_hop2 q4_hop3; do for o in a c; do
  f=$W/${o}_$q.sql; { echo "\\set k random(1, ${TOP:-200})"; cat $W/${o}_$q.body; } > $f
  pgbench -n -M prepared -c 1 -t 100 -f $f >/dev/null 2>&1
  for r in 1 2 3; do rm -f $W/log.*; (cd $W && pgbench -n -M prepared -c 1 -t 1000 -f $f -l --log-prefix=log >/dev/null 2>&1)
    cat $W/log.* | awk '{print $3/1000.0}' | sort -n > $W/l; n=$(wc -l < $W/l)
    p() { awk -v n=$n -v p=$1 'NR==int((n*p)+0.999999){printf "%.3f", $1; exit}' $W/l; }
    printf "%-10s %4s %8s %8s %8s\n" ${o}_$q $r $(p 0.50) $(p 0.95) $(p 0.99); done
done; done
