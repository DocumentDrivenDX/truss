#!/usr/bin/env bash
# Build both options on the cluster selected by PGVER (17 default, 18): generate data (once), run UMF's generator
# output + hand-written DDL for A, catalog + generated DDL for C, bulk load, analyze. Output: out/10_setup_pg$PGVER.txt
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
SCALE=${SCALE:-1}; D=$WORK/data; [ "$SCALE" = 1 ] || D=$WORK/data_s$SCALE; mkdir -p $D
[ -f $D/orders.jsonl ] || $BUN $SPIKE/harness/gen_data.ts $D $SCALE
psql -X -q -d postgres -c "CREATE DATABASE $PGDATABASE" 2>/dev/null || true
SUF=""; [ "$SCALE" = 1 ] || SUF="_s$SCALE"
exec > >(tee $SPIKE/out/10_setup_pg$PGVER$SUF.txt) 2>&1
t() { date +%s.%N; }
echo "== $(psql -X -At -c 'select version()')"
psql -X -q -c "SET client_min_messages=warning; DROP SCHEMA IF EXISTS sales CASCADE; DROP SCHEMA IF EXISTS c CASCADE;"
echo "== dataset"; cat $D/summary.json; echo
echo "== option A: UMF-generated tables+indexes"; psql -X -q -v ON_ERROR_STOP=1 -f $SPIKE/sql/a_generated_tables_indexes.sql
$BUN $SPIKE/harness/load_a.ts $D
s=$(t)
psql -X -q -v ON_ERROR_STOP=1 <<SQL
\copy sales.customers FROM '$D/a_customers.csv' CSV
\copy sales.products FROM '$D/a_products.csv' CSV
\copy sales.orders FROM '$D/a_orders.csv' CSV
\copy sales.order_lines FROM '$D/a_lines.csv' CSV
SQL
m=$(t); psql -X -q -v ON_ERROR_STOP=1 -f $SPIKE/sql/a_handwritten.sql; e=$(t)
echo "A: copy $(echo "$m - $s" | bc) s; hand-written keys/FKs/indexes/checks $(echo "$e - $m" | bc) s"
echo "== option C: fixed schema + loader"
psql -X -q -v ON_ERROR_STOP=1 -f $SPIKE/sql/c_schema.sql
s=$(t); $BUN $SPIKE/loader/load_c.ts $D $WORK/generated_c$SUF; [ "$SCALE" = 1 ] && cp $WORK/generated_c/*.sql $SPIKE/sql/generated_c/; e=$(t); echo "C loader (UMF validate, catalog, encode+validate all records, write CSV): $(echo "$e - $s" | bc) s"
psql -X -q -v ON_ERROR_STOP=1 -f $WORK/generated_c$SUF/c_catalog_rev0.sql
s=$(t)
psql -X -q -v ON_ERROR_STOP=1 <<SQL
\copy c.object FROM '$D/c_object.csv' CSV
\copy c.edge FROM '$D/c_edge.csv' CSV
SELECT setval('c.id_seq', $(cat $D/c_nextid.txt));
SQL
m=$(t); psql -X -q -v ON_ERROR_STOP=1 -f $SPIKE/sql/c_post_load.sql -f $WORK/generated_c$SUF/c_indexes.sql -f $SPIKE/sql/c_triggers.sql; e=$(t)
echo "C: copy $(echo "$m - $s" | bc) s; generic + generated indexes/triggers $(echo "$e - $m" | bc) s"
psql -X -q -c "ANALYZE c.object; ANALYZE c.edge;"
echo "== row counts"
psql -X -c "SELECT 'A customers' t, count(*) FROM sales.customers UNION ALL SELECT 'A orders', count(*) FROM sales.orders UNION ALL SELECT 'A order_lines', count(*) FROM sales.order_lines UNION ALL SELECT 'A products', count(*) FROM sales.products UNION ALL SELECT 'C object type '||type_id, count(*) FROM c.object GROUP BY type_id UNION ALL SELECT 'C edge rel '||rel_type_id, count(*) FROM c.edge GROUP BY rel_type_id ORDER BY 1"
