#!/usr/bin/env bash
# Mitigation probe for C's planning growth: the same flat-JSONB objects LIST-partitioned by type_id (one partition per
# type, per-partition key indexes instead of partial indexes on one table), with 100 extra empty synthetic types.
# Compares planning time (median of 25 EXPLAIN SUMMARY runs) and prepared-statement latency with the unpartitioned
# c.object carrying the equivalent 200 extra partial indexes. Throwaway; drops what it creates.
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
echo "== $(psql -X -At -c 'select version()')"
psql -X -q -v ON_ERROR_STOP=1 <<'SQL'
SET client_min_messages = warning;
DROP SCHEMA IF EXISTS cp CASCADE; CREATE SCHEMA cp;
CREATE TABLE cp.object (id bigint NOT NULL, type_id int NOT NULL, props jsonb NOT NULL, retained jsonb, rev int NOT NULL,
  PRIMARY KEY (id, type_id)) PARTITION BY LIST (type_id);
DO $$BEGIN
  FOR t IN 1..5 LOOP EXECUTE format('CREATE TABLE cp.object_t%s PARTITION OF cp.object FOR VALUES IN (%s)', t, t); END LOOP;
  FOR t IN 1000..1099 LOOP EXECUTE format('CREATE TABLE cp.object_t%s PARTITION OF cp.object FOR VALUES IN (%s)', t, t);
    EXECUTE format('CREATE UNIQUE INDEX ON cp.object_t%s (((props->>%L)::bigint))', t, (t*100)::text);
    EXECUTE format('CREATE INDEX ON cp.object_t%s (((props->>%L)::numeric))', t, (t*100+1)::text); END LOOP; END$$;
INSERT INTO cp.object SELECT id, type_id, props, retained, rev FROM c.object;
CREATE UNIQUE INDEX ON cp.object_t1 (((props->>'1')::bigint));
CREATE UNIQUE INDEX ON cp.object_t1 (((props->>'2') COLLATE "C"));
CREATE UNIQUE INDEX ON cp.object_t3 (((props->>'12')::bigint));
CREATE INDEX ON cp.object_t3 (((props->>'16')::numeric));
CREATE UNIQUE INDEX ON cp.object_t4 (((props->>'17')::bigint));
CREATE UNIQUE INDEX ON cp.object_t5 (((props->>'22')::bigint));
ANALYZE cp.object;
DO $$BEGIN FOR t IN 1000..1099 LOOP
  EXECUTE format('CREATE UNIQUE INDEX syn_key_t%s ON c.object (((props->>%L)::bigint)) WHERE type_id = %s', t, (t*100)::text, t);
  EXECUTE format('CREATE INDEX syn_idx_t%s ON c.object (((props->>%L)::numeric)) WHERE type_id = %s', t, (t*100+1)::text, t); END LOOP; END$$;
ANALYZE c.object;
SQL
declare -A Q
Q[c_fetch]="SELECT id, props::text FROM c.object o WHERE o.type_id = 1 AND ((o.props->>'1')::bigint) = :k"
Q[cp_fetch]="SELECT id, props::text FROM cp.object o WHERE o.type_id = 1 AND ((o.props->>'1')::bigint) = :k"
Q[c_hop1]="SELECT x.id, x.props::text FROM c.object s JOIN c.edge e0 ON e0.source_id = s.id AND e0.rel_type_id = 3 JOIN c.object x ON x.id = e0.target_id WHERE s.type_id = 3 AND ((s.props->>'12')::bigint) = :k"
Q[cp_hop1]="SELECT x.id, x.props::text FROM cp.object s JOIN c.edge e0 ON e0.source_id = s.id AND e0.rel_type_id = 3 JOIN cp.object x ON x.id = e0.target_id AND x.type_id = 4 WHERE s.type_id = 3 AND ((s.props->>'12')::bigint) = :k"
Q[c_hop3]="SELECT x.id, x.props::text FROM c.object s JOIN c.edge e0 ON e0.target_id = s.id AND e0.rel_type_id = 2 JOIN c.edge e1 ON e1.source_id = e0.source_id AND e1.rel_type_id = 3 JOIN c.edge e2 ON e2.source_id = e1.target_id AND e2.rel_type_id = 4 JOIN c.object x ON x.id = e2.target_id WHERE s.type_id = 1 AND ((s.props->>'1')::bigint) = :k"
Q[cp_hop3]="SELECT x.id, x.props::text FROM cp.object s JOIN c.edge e0 ON e0.target_id = s.id AND e0.rel_type_id = 2 JOIN c.edge e1 ON e1.source_id = e0.source_id AND e1.rel_type_id = 3 JOIN c.edge e2 ON e2.source_id = e1.target_id AND e2.rel_type_id = 4 JOIN cp.object x ON x.id = e2.target_id AND x.type_id = 5 WHERE s.type_id = 1 AND ((s.props->>'1')::bigint) = :k"
plan() { for i in $(seq 1 25); do psql -X -At -c "EXPLAIN (SUMMARY, COSTS OFF) $(echo "${Q[$1]}" | sed 's/:k/42/g')" | awk '/Planning Time/{print $3}'; done | sort -n | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
echo "parity (rows for k=1, 42, 777): $(for q in c_hop3 cp_hop3; do for k in 1 42 777; do psql -X -At -c "SELECT count(*) FROM ($(echo "${Q[$q]}" | sed "s/:k/$k/g")) s"; done | paste -sd/; done | paste -sd' ')"
echo "-- 105 types: c.object has $(psql -X -At -c "select count(*) from pg_indexes where schemaname='c' and tablename='object'") indexes; cp.object has $(psql -X -At -c "select count(*) from pg_inherits where inhparent='cp.object'::regclass") partitions"
printf "%-8s %10s %10s\n" shape "c plan ms" "cp plan ms"
for s in fetch hop1 hop3; do printf "%-8s %10s %10s\n" $s $(plan c_$s) $(plan cp_$s); done
W=$WORK/bench/partition; rm -rf $W; mkdir -p $W
echo "-- prepared latency, 3000 tx after 300 warm-up (ms): p50 p95"
for q in c_fetch cp_fetch c_hop1 cp_hop1 c_hop3 cp_hop3; do
  case $q in *fetch|*hop3) r=20000;; *) r=100000;; esac
  printf '\\set k random(1, %s)\n%s;\n' $r "${Q[$q]}" > $W/$q.sql
  pgbench -n -M prepared -c 1 -t 300 -f $W/$q.sql >/dev/null 2>&1; rm -f $W/log.*
  (cd $W && pgbench -n -M prepared -c 1 -t 3000 -f $W/$q.sql -l --log-prefix=log >/dev/null 2>&1)
  cat $W/log.* | awk '{print $3/1000.0}' | sort -n > $W/$q.lat; n=$(wc -l < $W/$q.lat)
  printf "%-8s %8s %8s\n" $q $(awk -v n=$n 'NR==int(n*0.5+0.999999){printf "%.3f",$1}' $W/$q.lat) $(awk -v n=$n 'NR==int(n*0.95+0.999999){printf "%.3f",$1}' $W/$q.lat)
done
echo "-- sizes (MB): cp.object partitions total $(psql -X -At -c "select round(sum(pg_total_relation_size(inhrelid))/1048576.0,1) from pg_inherits where inhparent='cp.object'::regclass")"
psql -X -q -c "SET client_min_messages = warning; DROP SCHEMA cp CASCADE" -c "DO \$\$DECLARE r record; BEGIN FOR r IN SELECT indexname FROM pg_indexes WHERE schemaname='c' AND indexname LIKE 'syn_%' LOOP EXECUTE 'DROP INDEX c.'||r.indexname; END LOOP; END\$\$"
