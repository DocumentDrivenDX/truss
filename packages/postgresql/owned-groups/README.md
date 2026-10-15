# Owned-group implementation in progress

`values.sql` implements the value simulation used before owned-group graph
changes. It retains exact numeric carriers, validates required properties and
returns key definitions alongside each ordered operation's complete value image.
It has no graph effects or authority issuance. It is not installed by the public
runtime and does not enable owned-object operations yet. The full executor must
use this component for its planned images and persistence.

Inputs and stored values are bounded to 1 MiB; the complete result is bounded to
4 MiB. The function is security-invoker and revoked from PUBLIC.

`forest.sql` derives immediate parents and aggregate roots for every node in a
complete simulated forest, including isolated roots and parallel owned edges.
Its local node/edge ordinals support existing objects and pending aliases without
allocating native IDs. The eventual executor must retain the separate exact
identity/alias map, prove complete scoped closure and admit catalog lifecycle,
permissions and effects. This helper provides none of those guarantees. Invoke it
only at states requiring forest validity; it does not change the deferred timing
of final group validation. It permits 128 nodes and 1,024 edges and refuses cycles
or multiple distinct parents. It is uninstalled, security-invoker and revoked
from PUBLIC.

Two basic PostgreSQL 18 tests cover exact create/update values, an invalid
required-field removal, unchanged graph/journal/key/receipt row counts, and a
subtree move with parallel edges followed by a cycle refusal:

```sh
PYTHONPATH=packages/python/src:packages/python/tests python -m unittest discover -s packages/postgresql/owned-groups -p test_values.py -v
```

Use the project Python environment with psycopg and pgserver-pg18. Bun must be on
PATH or selected with `TRUSS_BUN_EXECUTABLE`.
