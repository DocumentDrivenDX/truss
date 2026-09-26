#!/usr/bin/env bash
# Re-runs SPIKE-002 end to end. Prerequisites: build/build_pg17.sh, build/init_cluster.sh (PGVER=17 and 18),
# UMF master exported to $UMF_DIR with `bun install`. Scripts resolve paths from this file; WORK is scratch.
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
cd $SPIKE
bash harness/environment.sh > out/00_environment.txt 2>&1
$BUN model/make_model.ts && $BUN model/validate_and_generate.ts > /dev/null
$BUN harness/queries.ts > /dev/null
# --- PostgreSQL 17: revisions need fresh loads (they mutate data) ---
bash setup.sh > /dev/null
VARIANT=a $BUN harness/revisions.ts > /dev/null
VARIANT=c-engine $BUN harness/revisions.ts > /dev/null
bash setup.sh > /dev/null
$BUN harness/enforcement.ts > /dev/null              # installs the 52 conditional CHECKs, runs the matrix
VARIANT=c-db $BUN harness/revisions.ts > /dev/null
# --- PostgreSQL 17: fidelity, write cost, key tuples, latency on a fresh rev0 load ---
bash setup.sh > /dev/null
$BUN harness/enforcement.ts > /dev/null
$BUN harness/fidelity.ts > /dev/null
$BUN harness/engine_cost.ts > /dev/null
$BUN harness/key_tuple.ts > /dev/null
bash bench/parity_plans_sizes.sh > out/50_parity_plans_sizes_pg17.txt 2>&1
bash bench/planner_probe.sh > out/53_planner_probe_pg17.txt 2>&1
MODE=prepared bash bench/run_bench.sh > out/51_latency_prepared_pg17_with_checks.txt 2>&1
MODE=simple bash bench/run_bench.sh > out/51_latency_simple_pg17_with_checks.txt 2>&1
psql -X -q -f sql/generated_c/c_checks_drop.sql                 # engine-enforced configuration for the primary runs
MODE=prepared bash bench/run_bench.sh > out/51_latency_prepared_pg17.txt 2>&1
MODE=simple bash bench/run_bench.sh > out/51_latency_simple_pg17.txt 2>&1
bash bench/run_heavy.sh > out/51_latency_heavy_prepared_pg17.txt 2>&1
bash bench/partition_probe.sh > out/54_partition_probe_pg17.txt 2>&1
psql -X -q -f sql/generated_c/c_checks.sql
bash bench/run_keytuple_bench.sh > out/52_latency_keytuple_pg17.txt 2>&1
bash bench/write_cost.sh > out/22_write_cost_pg17.txt 2>&1   # last on 17: it inserts and deletes rows
# --- PostgreSQL 17: scale 5 (5x the plan's dataset) in a second database, prepared latency only ---
( export PGDATABASE=bakeoff_s5 SCALE=5; bash setup.sh > /dev/null
  NC=100000 NO=500000 MODE=prepared bash bench/run_bench.sh > out/51_latency_prepared_pg17_scale5.txt 2>&1
  TOP=1000 bash bench/run_heavy.sh > out/51_latency_heavy_prepared_pg17_scale5.txt 2>&1 )
# --- PostgreSQL 18.6: repeat fidelity and enforcement ---
pg18() { ( export PGVER=18; source "$SPIKE/env.sh"; "$@" ); }   # re-source env.sh so PGPORT/PGDATA follow PGVER
pg18 bash setup.sh > /dev/null
pg18 $BUN harness/enforcement.ts > /dev/null
pg18 $BUN harness/fidelity.ts > /dev/null
pg18 bash bench/sizes.sh > out/56_sizes_fresh_pg18.txt 2>&1
python3 harness/summarize.py > out/60_latency_summary.txt
echo "done; outputs in $SPIKE/out"
