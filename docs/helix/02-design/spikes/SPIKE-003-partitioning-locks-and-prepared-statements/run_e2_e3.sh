#!/usr/bin/env bash
# E2 (catalog lock) and E3 (prepared statements) on both engines, after E1. Sequential on purpose.
set -u
cd "$(dirname "$0")"
uv run --quiet --python 3.11 --with pgserver --with "psycopg[binary]" python e2_catalog_lock.py --lib pgserver --out out/e2_pg16.json
uv run --quiet --python 3.12 --with pgembed --with "psycopg[binary]" python e2_catalog_lock.py --lib pgembed --out out/e2_pg17.json
for N in 100 1000; do
  uv run --quiet --python 3.11 --with pgserver --with "psycopg[binary]" python e3_prepared.py --lib pgserver --types $N --out out/e3_pg16.jsonl
  uv run --quiet --python 3.12 --with pgembed --with "psycopg[binary]" python e3_prepared.py --lib pgembed --types $N --out out/e3_pg17.jsonl
done
echo DONE > out/e2_e3.done
