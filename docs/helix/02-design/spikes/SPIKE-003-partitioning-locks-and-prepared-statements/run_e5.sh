#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
uv run --quiet --python 3.11 --with pgserver --with "psycopg[binary]" python e5_pairs.py --lib pgserver --out out/e5.jsonl
uv run --quiet --python 3.12 --with pgembed --with "psycopg[binary]" python e5_pairs.py --lib pgembed --out out/e5.jsonl
echo DONE > out/e5.done
