#!/usr/bin/env bash
# Why simple-protocol C queries are slow: planning time per shape (median of 25 EXPLAIN SUMMARY runs), then again
# after adding partial indexes for 100 extra synthetic types (2 on c.object + 1 on c.edge per type), as a model grows.
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
W=$WORK/bench/planner; rm -rf $W; mkdir -p $W
awk -v dir=$W '/^-- /{name=$2; next} NF{print > (dir "/a_" name ".body")}' $SPIKE/sql/queries_a.sql
awk -v dir=$W '/^-- /{name=$2; next} NF{print > (dir "/c_" name ".body")}' $SPIKE/sql/queries_c.sql
plan() { for i in $(seq 1 25); do psql -X -At -c "EXPLAIN (SUMMARY, COSTS OFF) $(sed "s/:k/42/g; s/:lo/5000/g" $W/$1.body | sed 's/;$//')" | awk '/Planning Time/{print $3}'; done | sort -n | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
report() { echo "-- $1 (c.object indexes: $(psql -X -At -c "select count(*) from pg_indexes where schemaname='c' and tablename='object'"), c.edge indexes: $(psql -X -At -c "select count(*) from pg_indexes where schemaname='c' and tablename='edge'"))"
  for q in q1_fetch q2_hop1 q3_hop2 q4_hop3 q5_range; do printf "  %-9s planning ms  A %6s   C %6s\n" $q $(plan a_$q) $(plan c_$q); done; }
echo "== $(psql -X -At -c 'select version()')"
report "current model (5 types)"
psql -X -q -c "DO \$\$BEGIN FOR t IN 1000..1099 LOOP
  EXECUTE format('CREATE UNIQUE INDEX syn_key_t%s ON c.object (((props->>%L)::bigint)) WHERE type_id = %s', t, (t*100)::text, t);
  EXECUTE format('CREATE INDEX syn_idx_t%s ON c.object (((props->>%L)::numeric)) WHERE type_id = %s', t, (t*100+1)::text, t);
  EXECUTE format('CREATE UNIQUE INDEX syn_edge_r%s ON c.edge (source_id) WHERE rel_type_id = %s', t, t); END LOOP; END\$\$"
psql -X -q -c "ANALYZE c.object; ANALYZE c.edge"
report "after 100 synthetic types (+200 object, +100 edge partial indexes)"
psql -X -q -c "DO \$\$DECLARE r record; BEGIN FOR r IN SELECT indexname FROM pg_indexes WHERE schemaname='c' AND indexname LIKE 'syn_%' LOOP EXECUTE 'DROP INDEX c.'||r.indexname; END LOOP; END\$\$"
