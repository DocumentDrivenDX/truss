#!/usr/bin/env bash
# E3 at 1000 types, reduced: the chosen layout (L2) in full; L0 and L1 with small samples and only the two modes
# that matter (prepared on first use, never prepared). Their per-query planning cost is already measured in E1.
set -u
cd "$(dirname "$0")"
uv run --quiet --python 3.11 --with pgserver --with "psycopg[binary]" python e3_prepared.py --lib pgserver --types 1000 --layouts L2_flat_key_table --out out/e3_pg16.jsonl
uv run --quiet --python 3.12 --with pgembed --with "psycopg[binary]" python e3_prepared.py --lib pgembed --types 1000 --layouts L2_flat_key_table --out out/e3_pg17.jsonl
uv run --quiet --python 3.11 --with pgserver --with "psycopg[binary]" python e3_prepared.py --lib pgserver --types 1000 --layouts L0_flat_partial_idx,L1_list_per_type --modes prep0,none --scale 0.02 --no-extras --out out/e3_pg16_small.jsonl
uv run --quiet --python 3.12 --with pgembed --with "psycopg[binary]" python e3_prepared.py --lib pgembed --types 1000 --layouts L0_flat_partial_idx,L1_list_per_type --modes prep0,none --scale 0.02 --no-extras --out out/e3_pg17_small.jsonl
echo DONE > out/e2_e3.done
