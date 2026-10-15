# Owned-group implementation in progress

`values.sql` implements the value simulation used before owned-group graph
changes. It retains exact numeric carriers, validates required properties and
returns key definitions alongside each ordered operation's complete value image.
It has no graph effects or authority issuance. It is not installed by the public
runtime and does not enable owned-object operations yet. The full executor must
use this component for its planned images and persistence.

Inputs and stored values are bounded to 1 MiB; the complete result is bounded to
4 MiB. The function is security-invoker and revoked from PUBLIC.

The single basic PostgreSQL 18 test covers exact create/update values, an invalid
required-field removal and unchanged graph/journal/key/receipt row counts:

```sh
PYTHONPATH=packages/python/src:packages/python/tests python -m unittest discover -s packages/postgresql/owned-groups -p test_values.py -v
```

Use the project Python environment with psycopg and pgserver-pg18. Bun must be on
PATH or selected with `TRUSS_BUN_EXECUTABLE`.
