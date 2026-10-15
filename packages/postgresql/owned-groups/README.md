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

`delete.sql` computes the complete outward descendant closure at an operation's
ordered position and returns unique sorted node/owned-edge ordinals, including
incoming owned edges from surviving parents. An independent incident edge,
including one entirely inside the deleted set, refuses unless removed earlier.
The bounded visited set permits temporary cycles and multiple parents: final
forest validation remains deferred. `node_count` covers only component nodes;
the next 256 ordinals are independent endpoint witnesses, never deletion targets
or owned-edge endpoints. The executor must supply complete current incident
edges, retain the exact identity map and authorize every resulting effect.
This uninstalled helper performs no graph writes and enables no public provider.

`transition.generated.sql` and `transition-upgrade.generated.sql` come from
UMF's native PostgreSQL exporter via `scripts/build-unified-object-transition.ts`.
The separate 0.2 native/core models remove the physical before-image NOT NULL
constraint without changing the original 0.1 models. SQL NULL represents an
absent before-image; it does not by itself prove a create. The future executor
must bind genuine version-1 creates to original input/profile evidence, retain
creation reservations and one journal custodian, and update attribution/history
guards. These candidate files are not installed by native66.

Five basic PostgreSQL 18 tests cover exact create/update values, an invalid
required-field removal, unchanged graph/journal/key/receipt row counts, and a
subtree move with parallel edges followed by a cycle refusal. The scope case uses
public catalog acceptance/object creation, then rolled-back administrative graph
fixture rows to test complete component/boundary images and lifecycle refusal;
it does not demonstrate a public owned mutation workflow.

The transition case applies the owner-generated ALTER to a real committed public
update, verifies the original transition is unchanged, and rolls back the DDL.
It does not enable unified create execution or qualify the complete next upgrade.
The delete case covers a descendant cascade with parallel incoming edges,
independent incident-edge refusals, prior-unlink ordering and temporary cycle
traversal without enforcing final-forest validity early. Its latest standalone
PostgreSQL 18 run passed one case in 5.940s; this is component evidence only.
Run all five cases with:

```sh
PYTHONPATH=packages/python/src:packages/python/tests python -m unittest discover -s packages/postgresql/owned-groups -p 'test_*.py' -v
```

Use the project Python environment with psycopg and pgserver-pg18. Bun must be on
PATH or selected with `TRUSS_BUN_EXECUTABLE`.
