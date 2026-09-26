#!/usr/bin/env bash
# Question 2 cost: single-row insert latency/throughput for A (typed table) and C (shared objects table) with
# no CHECKs, with the 52 generated conditional CHECKs, and with 52 + 500 synthetic CHECKs (50 extra types x 10
# properties) to show how the shared-table cost grows with model size. Also times adding the 52 CHECKs to the
# loaded table. pgbench, 1 client, prepared, 5000 tx (500 for 100-row statements) after 500 warm-up, synchronous_commit=on.
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
W=$WORK/writecost; rm -rf $W; mkdir -p $W
psql -X -q -c "CREATE SEQUENCE IF NOT EXISTS c.key_seq START 10000000"
cat > $W/a.sql <<'SQL'
\set n random(1, 1000000000)
INSERT INTO sales.products (id, sku, name, price) VALUES (nextval('sales.id_seq'), 'W-' || :n, 'write cost probe', 12.34);
SQL
cat > $W/c.sql <<'SQL'
\set n random(1, 1000000000)
INSERT INTO c.object (type_id, props, rev) VALUES (5, jsonb_build_object('22', nextval('c.key_seq'), '23', 'W-' || :n, '24', 'write cost probe', '25', 12.34), 0);
SQL
cat > $W/c100.sql <<'SQL'
\set n random(1, 1000000000)
INSERT INTO c.object (type_id, props, rev) SELECT 5, jsonb_build_object('22', nextval('c.key_seq'), '23', 'W-' || :n || '-' || g, '24', 'write cost probe', '25', 12.34), 0 FROM generate_series(1, 100) g;
SQL
cat > $W/a100.sql <<'SQL'
\set n random(1, 1000000000)
INSERT INTO sales.products (id, sku, name, price) SELECT nextval('sales.id_seq'), 'W-' || :n || '-' || g, 'write cost probe', 12.34 FROM generate_series(1, 100) g;
SQL
run() { pgbench -n -M prepared -c 1 -j 1 -t 500 -f $W/$2.sql >/dev/null 2>&1
  pgbench -n -M prepared -c 1 -j 1 -t ${3:-5000} -f $W/$2.sql 2>&1 | awk -v l="$1" '/latency average/{lat=$4} /^tps/{tps=$3} END{printf "%-52s latency avg %s ms  tps %s\n", l, lat, tps}'; }
echo "== $(psql -X -At -c 'select version()')"
ncheck() { psql -X -At -c "SELECT count(*) FROM pg_constraint WHERE conrelid='c.object'::regclass AND contype='c'"; }
psql -X -q -f $SPIKE/sql/generated_c/c_checks_drop.sql
psql -X -q -c "DO \$\$DECLARE r record; BEGIN FOR r IN SELECT conname FROM pg_constraint WHERE conrelid='c.object'::regclass AND conname LIKE 'ck_syn_%' LOOP EXECUTE 'ALTER TABLE c.object DROP CONSTRAINT '||r.conname; END LOOP; END\$\$"
run "A sales.products (typed columns, PK)" a
run "C c.object, $(ncheck) CHECK constraints" c
s=$(date +%s.%N); psql -X -q -v ON_ERROR_STOP=1 -f $SPIKE/sql/generated_c/c_checks.sql; e=$(date +%s.%N)
echo "adding the 52 generated CHECKs to c.object ($(psql -X -At -c 'select count(*) from c.object') rows, validated): $(echo "$e - $s" | bc) s"
run "C c.object, $(ncheck) CHECK constraints" c
run "C c.object, $(ncheck) CHECKs, 100 rows per INSERT" c100 500
run "A sales.products, 100 rows per INSERT" a100 500
psql -X -q -c "DO \$\$BEGIN FOR t IN 1000..1049 LOOP FOR p IN 1..10 LOOP EXECUTE format('ALTER TABLE c.object ADD CONSTRAINT ck_syn_t%s_p%s CHECK (type_id <> %s OR NOT (jsonb_typeof(props->%L) IS NOT NULL AND jsonb_typeof(props->%L) <> %L) OR (jsonb_typeof(props->%L) = %L AND length(props->>%L) <= 100)) NOT VALID', t, p, t, (t*100+p)::text, (t*100+p)::text, 'null', (t*100+p)::text, 'string', (t*100+p)::text); END LOOP; END LOOP; END\$\$"
run "C c.object, $(ncheck) CHECK constraints" c
run "C c.object, $(ncheck) CHECKs, 100 rows per INSERT" c100 500
psql -X -q -c "DO \$\$DECLARE r record; BEGIN FOR r IN SELECT conname FROM pg_constraint WHERE conrelid='c.object'::regclass AND conname LIKE 'ck_syn_%' LOOP EXECUTE 'ALTER TABLE c.object DROP CONSTRAINT '||r.conname; END LOOP; END\$\$"
psql -X -q -f $SPIKE/sql/generated_c/c_checks_drop.sql
psql -X -q -f $SPIKE/sql/c_validate_trigger.sql
run "C c.object, catalog-driven validation trigger" c
echo "== trigger variant: violating and control writes (each rolled back), then detection for a tightened rule"
psql -X -e -v ON_ERROR_STOP=0 -f $SPIKE/bench/trigger_probe.sql 2>&1
psql -X -q -c "DROP TRIGGER IF EXISTS object_validate ON c.object"
psql -X -q -f $SPIKE/sql/generated_c/c_checks.sql
# probe rows are unreferenced; skip per-row FK checks (products has no index on order_lines.productId, see HAND-8/9)
psql -X -q -c "SET session_replication_role = replica" -c "DELETE FROM c.object WHERE type_id = 5 AND (props->>'22')::bigint >= 10000000" -c "DELETE FROM sales.products WHERE id >= 10000000"
