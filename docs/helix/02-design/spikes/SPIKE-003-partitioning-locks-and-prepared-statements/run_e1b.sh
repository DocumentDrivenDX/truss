#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
for R in 100 1000; do
  uv run --quiet --python 3.11 --with pgserver --with "psycopg[binary]" python e1b_followups.py --lib pgserver --rels $R --out out/e1b_pg16.jsonl
  uv run --quiet --python 3.12 --with pgembed --with "psycopg[binary]" python e1b_followups.py --lib pgembed --rels $R --out out/e1b_pg17.jsonl
done
echo DONE > out/e1b.done
