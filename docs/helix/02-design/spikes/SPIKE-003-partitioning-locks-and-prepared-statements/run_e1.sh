#!/usr/bin/env bash
# E1 on both embedded engines. Sequential on purpose: concurrent runs would distort latencies.
set -u
cd "$(dirname "$0")"
for N in 10 100 1000; do
  uv run --quiet --python 3.11 --with pgserver --with "psycopg[binary]" python e1_layout.py --lib pgserver --types $N --out out/e1_pg16.jsonl
done
for N in 10 100 1000; do
  uv run --quiet --python 3.12 --with pgembed --with "psycopg[binary]" python e1_layout.py --lib pgembed --types $N --out out/e1_pg17.jsonl
done
echo DONE > out/e1.done
