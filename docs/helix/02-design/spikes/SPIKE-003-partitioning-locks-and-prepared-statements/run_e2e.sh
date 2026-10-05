#!/usr/bin/env bash
# Mechanism E (advisory lock, then FOR SHARE on the in-place head row), plus B and C as controls, on both engines.
set -u
cd "$(dirname "$0")"
uv run --quiet --python 3.11 --with pgserver --with "psycopg[binary]" python e2_catalog_lock.py --lib pgserver --mechs B,C,E --out out/e2e_pg16.json
uv run --quiet --python 3.12 --with pgembed --with "psycopg[binary]" python e2_catalog_lock.py --lib pgembed --mechs B,C,E --out out/e2e_pg17.json
echo DONE > out/e2e.done
