#!/usr/bin/env bash
# Result parity (A vs C row counts over sample keys), EXPLAIN (ANALYZE, BUFFERS) per shape, and on-disk sizes.
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
W=$WORK/bench/plans; rm -rf $W; mkdir -p $W
$BUN $SPIKE/harness/queries.ts >/dev/null
awk -v dir=$W '/^-- /{name=$2; next} NF{print > (dir "/a_" name ".body")}' $SPIKE/sql/queries_a.sql
awk -v dir=$W '/^-- /{name=$2; next} NF{print > (dir "/c_" name ".body")}' $SPIKE/sql/queries_c.sql
sub() { sed "s/:k/$2/g; s/:lo/$3/g" $W/$1.body | sed 's/;$//'; }
echo "== result parity: sum of rows over sample keys (A vs C)"
for q in q1_fetch q2_hop1 q3_hop2 q4_hop3 q5_range; do
  for o in a c; do
    tot=0; for k in 1 2 3 17 101 999 5000 12345 19999; do lo=$((k*2)); n=$(psql -X -At -c "SELECT count(*) FROM ($(sub ${o}_$q $k $lo)) s"); tot=$((tot+n)); done
    echo "$o $q rows=$tot"
  done
done
echo "== EXPLAIN (ANALYZE, BUFFERS): heaviest customer k=1 for hops; order k=4242; range lo=5000"
for q in q1_fetch q2_hop1 q3_hop2 q4_hop3 q5_range; do
  for o in a c; do
    k=1; [ $q = q2_hop1 ] && k=4242
    echo "---- ${o}_$q"
    psql -X -At -c "EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) $(sub ${o}_$q $k 5000)"
  done
done
echo "== sizes (MB): table heap, indexes, total incl. TOAST"
psql -X -c "SELECT n.nspname||'.'||c.relname AS rel, round(pg_relation_size(c.oid)/1048576.0,1) heap_mb, round(pg_indexes_size(c.oid)/1048576.0,1) idx_mb, round(pg_total_relation_size(c.oid)/1048576.0,1) total_mb
  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('sales','c') AND c.relkind='r' ORDER BY 1"
psql -X -c "SELECT n.nspname AS schema, round(sum(pg_total_relation_size(c.oid))/1048576.0,1) total_mb FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('sales','c') AND c.relkind='r' GROUP BY 1"
psql -X -c "SELECT schemaname, indexrelname, round(pg_relation_size(indexrelid)/1048576.0,1) mb FROM pg_stat_user_indexes WHERE schemaname IN ('sales','c') ORDER BY 1,2"
