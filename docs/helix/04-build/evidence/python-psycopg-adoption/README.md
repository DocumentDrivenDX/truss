# Supported psycopg host adoption component

Astra Ultra reviewed the plan and final source. All 26 native methods pass on
Python 3.11.17, psycopg/binary 3.3.6, libpq 18.6, PostgreSQL 16.15.
The receipt pins tested source and retained logs. Module boundaries pass.

This establishes local adoption/containment behavior only. It does not qualify
catalog operations, full engine delivery, arbitrary cursor methods, Lakebase,
other profiles, durable commit recovery, packaging, or peak memory. Fixture
shutdown is part of the test class; no independent cleanup receipt is claimed.

Reproduce with the selected Python environment, the pinned psycopg native extra,
TRUSS_CENSUS_POSTGRES_BIN pointing at PostgreSQL 16.15 binaries, and
PYTHONPATH=packages/python/src:packages/python/tests, then run
`python -m unittest test_psycopg_host_native -v` from the repository root.
