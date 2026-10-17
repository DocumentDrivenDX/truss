# Subject-held source and data cut

Newly enrolled ordinary Subject helpers hold the complete accepted-source tables,
module access, objects, key buckets and edges in the caller's transaction using
SHARE/NOWAIT locks. Existing Subject/session/source/key predicates and the
source-epoch nonempty refusal remain unchanged. This addresses CONTRACT-005's
current-authority and guarded-read obligations without enabling Graph admission.
Existing enrolled helpers are not migrated or globally rejected.

The installed PostgreSQL 18.6 / psycopg 3.3.6 test passed in 5.208 seconds after
reconciling with main c9d5693f; fixture cleanup completed. The real ordinary caller
held all 25 source/data cuts, including the empty edge relation; external writes
refused and became possible after caller rollback. A pre-existing edge writer
refused before key encoding, retained no partial cut, and allowed a fresh
observation after its rollback. See the [original result](weft-b008-subject-cut-post-rebase-native-20261016.json)
and [terminal test log](weft-b008-subject-cut-post-rebase-native-20261016.log.gz).

The tested wheel SHA-256 was
`05c8a811a17b84899edf60bc4fa8c0aef9751da67bf2adf40b390666ccc7e665`.
The three integrated source/test/checker files match frozen source commit
`4b75097b2b35f115c6753dd186e2fac5626878ea`. Full producer receipts and built
artifacts remain on that owner commit, outside this concise main-tree record.

These locks can delay writes until the caller ends its transaction. The test
uses privileged external fixture writers and does not establish malicious-owner
containment, authentication/role-DDL closure, continuous authority, native Graph
activation or guarded public release. No acceptance case or default dependency
pin is promoted.

Astra Ultra reviewed the frozen source, test and completed native evidence before
integration; no blocking defect was found within this stated component scope.
