#!/usr/bin/env bash
# Re-runs the whole Apache AGE spike against the running PG18.6 + AGE 1.8.0 instance.
# Build first with build/build.sh (PG18 + AGE) and optionally build/build_pg19.sh (PG19 beta smoke test);
# cluster setup (initdb, shared_preload_libraries='age', port 54318) is described in the findings file.
set -u
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
cd $SPIKE
{ uname -a; grep PRETTY_NAME /etc/os-release; psql -X -At -c "select version()"; psql -X -At -c "select extversion from pg_extension where extname='age'"; } > out/00_environment.txt 2>&1
$PSQL -f sql/01_types_nulls.sql   > out/01_types_nulls.txt 2>&1
$PSQL -f sql/02_constraints.sql   > out/02_constraints.txt 2>&1
mkdir -p /tmp/age && chown postgres /tmp/age   # AGE 1.8.0 loader base directory is hard-coded to /tmp/age/
$PSQL -f bench/00_load.sql        > out/10_load.txt 2>&1
$PSQL -f sql/03_indexes.sql       > out/03_indexes.txt 2>&1
$PSQL -f sql/04_cypher.sql        > out/04_cypher.txt 2>&1
bash sql/05_concurrency.sh        > out/05_concurrency.txt 2>&1
(cd node && /opt/node22/bin/node c9_client.mjs; echo; /root/.bun/bin/bun c9_client.mjs; /root/.bun/bin/bun c9_bunsql.ts) > out/06_c9_client.txt 2>&1
$PSQL -f sql/07_casts.sql         > out/07_casts.txt 2>&1
N=3000 WARM=300 bash bench/run_bench.sh > out/12_bench.txt 2>&1
N=1000 bash bench/run_mixed.sh    > out/12_bench_mixed.txt 2>&1
bash bench/vle_cache.sh           > out/12_vle_cache.txt 2>&1
echo "done; outputs in $SPIKE/out"
