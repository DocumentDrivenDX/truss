#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
uv run --quiet --python 3.11 --with pgserver --with "psycopg[binary]" python e4_rls.py --lib pgserver --out out/e4.jsonl
uv run --quiet --python 3.12 --with pgembed --with "psycopg[binary]" python e4_rls.py --lib pgembed --out out/e4.jsonl
echo DONE > out/e4.done
