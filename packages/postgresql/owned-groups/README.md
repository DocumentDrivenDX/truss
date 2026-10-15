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

`scope.sql` captures one statement-snapshot image of complete existing ownership
components and all their incident edges. Independent outside endpoints and their
referenced roots remain bounded observed witnesses, not traversed components or
proofs of those components' validity. Unknown lifecycles refuse. The complete
image retains actual rows, catalog owners and root correspondence. Limits are
128 component nodes, 1,024 incident edges, 256 boundary witnesses and 4 MiB for
the complete returned image. This uninstalled security-invoker helper issues no
authority and takes no locks. The executor must collect earlier guards, acquire
the common graph gate, reobserve the whole image and refuse expanded earlier
guard scope before effects.
Explicit `nodeOrder` and `ownedEdgeOrder` arrays retain local-to-native identity
correspondence. Stored root membership without a connecting owned-edge path
refuses; the helper never fabricates that missing edge.

Three basic PostgreSQL 18 tests cover exact create/update values, an invalid
required-field removal, unchanged graph/journal/key/receipt row counts, and a
subtree move with parallel edges followed by a cycle refusal. The scope case uses
public catalog acceptance/object creation, then rolled-back administrative graph
fixture rows to test complete component/boundary images and lifecycle refusal;
it does not demonstrate a public owned mutation workflow:

```sh
PYTHONPATH=packages/python/src:packages/python/tests python -m unittest discover -s packages/postgresql/owned-groups -p 'test_*.py' -v
```

Use the project Python environment with psycopg and pgserver-pg18. Bun must be on
PATH or selected with `TRUSS_BUN_EXECUTABLE`.
