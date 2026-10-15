# Truss Python toolkit

The Python reference assembly provides catalog registration, object and edge
mutations, business-key reads, Weft queries, imports, retained history, receipt
recovery, committed feeds and acknowledgements. It embeds into a caller-owned
synchronous psycopg connection. The caller begins and settles assembly transactions. The separate
`run_import_batches` function owns a fresh connection and commits one record
per batch; objects precede edges across the complete input. It performs no
automatic retries. Results distinguish confirmed commits, rollbacks and unknown
commit outcomes. Repeating input uses current identity policy and does not
recover the original import report. Reports may be withheld when current
disclosure authority cannot be established.

This is an experimental implementation: Python distribution `truss-toolkit==0.0.32`,
native runtime `0.67-candidate`, layout `1.0`
candidate, UMF core `0.7.0` and `0.8.0`, and Weft runtime backend `0.4.36`. The tested local
stack is DocumentDrivenDX `pgserver-pg18==18.6.1`, PostgreSQL 18.6,
psycopg/psycopg-binary 3.3.6 and libpq 18.6. Aurora, Lakebase and other driver or
server versions are not qualified. The broader protected-engine security
activation remains unfinished; this runtime does enforce its own installed
ordinary-person/module boundaries.

This release is [v0.0.32](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.32).
Registration-owned optional and required non-key rebinding is included in25; its
[report0.3 contract](../../docs/helix/02-design/contracts/catalog-rebind-report-v0.2.md)
retains original effects/events and requires current data-reader authority.

The Python distribution version is distinct from native runtime/layout versions;
future distributed changes receive a new package version.

## Current feature scope

SDK31/native66 is published with matching Weft31/backend36. It supports required
scalar-field/key backfill and acyclic nested array/map properties with required
item Fields and exact scalar leaves, including writes, reads, history, imports,
Weft queries and retained-cell rebinding. The
[rebind addendum](../../docs/helix/02-design/contracts/catalog-rebind-report-v0.4.md)
and [key-backfill contract](../../docs/helix/02-design/contracts/catalog-key-backfill-report-v0.1.md)
define those scopes. Cyclic definitions, descendant evolution and record/composed
ownership remain unfinished. The failed SDK28 tag published no wheel; SDK29
corrects its duplicate-map-key refusal mapping.

The [owned-object implementation plan](../../docs/helix/04-build/python-owned-objects-plan.md)
covers ownership inputs, complete cascades, historical/replay authority and
matching queries. Its UMF storage candidates are not callable ownership support.

## Native66 scope and compiler pairing

UMF0.8 support0.17 admits otherwise-supported standalone singular scalar Fields
as declarations. Their original assertions remain in the accepted source/report;
no stored property is allocated until a Field is a Record member. The supplied
`CatalogDocument.document_revision` is preserved independently of its content
SHA256. Unknown selected shapes and standalone containers refuse.

Direct object, key and page results expose `object.ownership.state` as
`rootless` for the currently supported read profile. Owned reads remain unfinished.

The exact consumer model passes public accept/apply/readback and native binding
export. Populated native65 upgrades preserve transitions and receipt replay.
Published SDK0.0.32 selects Weft0.4.32 for native66 queries and original
mutation-selection registration/lowering, preserving native65. See the
[SDK31 release evidence](../../docs/helix/04-build/releases/v0.0.32.md).
This compiler support does not enable a protected bulk-action executor.

## Install the release

The main checkout also contains an **unreleased current-policy query candidate**:
`assembly.query_current_in_transaction(tx, executor=..., sql=...,
document_ids=(...), parameters=...)`. It composes an ordinary caller's actual
Subject and module access, original UMF policy evaluation, original Weft query
preparation, private PostgreSQL staging and guarded `QueryRows` release.
The [basic workflow](tests/test_current_query_runtime_native.py) creates data
through the public API and queries an exact signed64 salary while returning its
masked String value.

Before opening protected callers, finish bootstrap data and Subject enrollment,
quiesce all other client sessions and prevent new connections, then call
`activate_current_query_protection_in_transaction(installer, tx,
subject_registration=subjects)` and commit. Activation checks that no other
client sessions remain. It revokes every ordinary legacy data routine grant;
only scoped catalog metadata and the verified own-session Subject facade remain.
Guarded queries require this committed activation. Cached legacy query bindings
do not retain access. Module configuration, feed enrollment, runtime upgrades and privileged bootstrap
installers refuse after activation until an explicit protection migration exists.

This first protected profile supports reads through `query_current_in_transaction`.
Legacy mutations, imports, direct reads, history and feed are unavailable after
activation until equivalent policy-aware providers land. Activation records the activating administrator as the sole trusted login for
this first profile. Other CONNECT-capable logins cannot have direct, inherited,
or SET-reachable raw authority. Pre-existing external SECURITY DEFINER functions
whose owners reach privileged/raw authority refuse activation even when private;
this conservatively includes benign admin-owned extension functions. Externally
accessible views or rewrite rules over Truss data also refuse. External triggers
(including disabled ones), operators, casts and other catalog attachments to
Truss routines refuse; only attachments on original private relation homes are
admitted. The activating
administrator must keep database/role DDL quiescent; this profile does not protect
against that administrator or qualify arbitrary database extensions.

The host supplies a separate privileged connection and a fresh transaction
dedicated to one query. It also keeps administrative runtime DDL quiescent.
Truss does not commit, roll back or close either connection. After the operation,
the host should settle the private transaction to release its table/role cuts:

```python
from truss import CurrentQueryExecutor, adopt_psycopg_host

worker_connection.execute("BEGIN")
worker = adopt_psycopg_host(worker_connection, operation_timeout_ms=30000)
worker_tx = worker.adopt_transaction().value
try:
    executor = CurrentQueryExecutor(worker, worker_tx, subject_registration)
    result = assembly.query_current_in_transaction(
        tx, executor=executor,
        sql="SELECT r.salary FROM Resource r WHERE r.salary=:minimum",
        document_ids=("domain",), parameters={"minimum": 9007199254740993},
    )
finally:
    worker.detach()
    worker_connection.rollback()
```

The original source/Subject registrations must already be committed. Their
installers are exported as `register_current_query_sources_in_transaction` and
`register_current_query_subjects_in_transaction`; installer authority is checked
natively. These registrations do not themselves grant query permission.
`prepare_current_query_originals(opaque_sources_bytes)` preserves the original
source bytes and selects an explicitly supported installed computation cohort.
Unknown modules refuse. Reopening a registration under another known wheel still
requires an explicit migration; the factory never upgrades retained pins.

This first local PostgreSQL18.6/macOS ARM profile uses exact original candidate
Weft ABI2 and UMF child pins. Published Weft0.4.32 lacks the needed CQP feature;
The exact standard-feature Weft0.4.33 macOS ARM CI wheel is additionally
qualified for this existing ABI2 flow. Published bytes and other platforms still
need explicit qualification before a wider release claim.
It currently requires rootless, present String or explicit signed64 query
domains. Empty or all-read-denied populations return empty rows when genuine
compiled operator routes establish one unambiguous original projection domain;
prohibited routes still refuse. Projection-only fields without that metadata,
nullable/structured outputs, aggregates and keyed/vault comparison scopes remain
unfinished. Prohibited routes refuse; logical limits return `QueryRefused`
with code `limits` after cleanup. Existing `query_in_transaction` retains its
published module-access behavior.
Caller scan limits count read-admitted source occurrences, and caller byte limits
count public scalar carriers. Private fact capture and contributor metadata have
separate fixed limits; denied facts do not consume a caller-selected budget.

Use a fresh Python3.11+ environment on the declared Linuxx86_64/macOSarm64
PG18 profile. Prebuilt Weft wheels remove the Rust/Cargo build requirement:

```sh
python -m pip install --only-binary=:all: \
  --find-links https://github.com/DocumentDrivenDX/truss/releases/expanded_assets/v0.0.32 \
  --find-links https://github.com/DocumentDrivenDX/weft/releases/expanded_assets/v0.4.32 \
  --find-links https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2 \
  'truss-toolkit[local,native,query]==0.0.32'
```

Bun1.4.2 is still required for UMF preparation. SDK 0.0.32 /
native 0.67 derives ordinary object keys in PostgreSQL for admitted UMF 0.7/0.8
catalogs. Create/update, imports, preconditions, backfills and lookups require no
client encoder or per-key receipt. Existing stored key and namespace bytes are
preserved. Weft remains optional through `query` (version 0.4.32); it is not a
key-encoding dependency. The separate protected security observation retains its
original producer boundary.
The older released installation example above retains its historical dependency
requirements. Each release
publishes package checksums and source/runtime/backend pins. The Truss release
workflow exercises the exact uploaded wheel with its exactly paired published Weft wheels and verified
PG18 dependency wheels on both declared native platforms.

## Run a real workflow

Check out the v0.0.32 tag to obtain the examples, then run with a new directory:

```sh
git clone --branch v0.0.32 --depth 1 https://github.com/DocumentDrivenDX/truss.git
cd truss
python packages/python/examples/adopter_workflow.py /tmp/truss-adopter-demo --bun bun
```

The [example](examples/adopter_workflow.py) installs the runtime, registers the
[original UMF document](examples/notes.umf.json), configures ordinary-person access,
commits Notes and a link, recovers the original request, reads by key, compiles a
relationship query, rolls back a dry-run, imports a Note and durably saves feed
pages before source ACKs. Administrator SQL sets up roles only.

The [portable preview0.10](../../docs/helix/04-build/corpus/public-python/0.10/README.md)
retains22 basic and10 exact-scalar observations for runtime0.38. Earlier previews
retain their historical pins; none claims independent interchange.

For a local server with an installed Truss candidate, use the explicit launcher
option after installing the `[local,native]` extras:

```sh
truss-local-postgres --data-dir /tmp/truss-local --install
```

Add `--probe` to install, confirm committed status and stop while retaining data.
The launcher installs only when public status reports no Truss namespace. On a
current retained installation it confirms status and preserves the installation
ID. Unsupported or corrupt installations refuse; this option never upgrades or
repairs them. The JSON output follows commit and a fresh status observation.
Fresh owner/registrar role names come from the installation result; save them
for access setup. A restart reports confirmed status without inventing those
names. Ordinary-person registration and module access still require the role
configuration described below. Without `--install`, the launcher only starts
PostgreSQL. Confirmed candidate status does not establish full security readiness.

## Embed in your host

Use an ordinary authenticated person's connection for business operations.
Installation and role administration use a separate trusted connection.
`SET ROLE` must be `none`; identity comes from the connecting person.

```python
from truss import CatalogRuntimeConfiguration, Ok, adopt_psycopg_host, create_reference_assembly

connection.execute('BEGIN READ ONLY')
connection.execute("SET LOCAL statement_timeout = '10000ms'")
host = adopt_psycopg_host(connection, statement_timeout_ms=10000,
                         operation_timeout_ms=30000)
try:
    adopted = host.adopt_transaction(access_mode='read_only')
    if not isinstance(adopted, Ok):
        raise RuntimeError(adopted.error.message)
    tx = adopted.value
    built = create_reference_assembly(CatalogRuntimeConfiguration(), host)
    if not isinstance(built, Ok):
        raise RuntimeError(built.error.message)
    assembly = built.value
    result = assembly.reader_catalog_in_transaction(tx)
    if not isinstance(result, Ok):
        raise RuntimeError(result.error.message)
finally:
    host.detach()
    connection.rollback()
```

Reads support read-only READ COMMITTED transactions. Writes use read-write READ
COMMITTED transactions. Idle or failed transactions cannot be adopted. Keep raw
connection aliases unused during toolkit operations; reacquire a transaction
handle after caller settlement. Truss does not manage a pool or commit/rollback
the outer transaction. The example's `transaction` context manager demonstrates
caller settlement for successful writes, refusals and exceptions.

The host must establish a native `statement_timeout` between 1 and 60000 ms
before adoption; PostgreSQL's default zero refuses. The host adapter applies its
requested temporary operation bound only after admission. Ordinary deadlines and
cancellation do not guarantee hard wall-clock termination. Failed containment
can quarantine a connection; detach/re-adoption does not clear that condition.
Recover the host transaction/connection before reuse.

## Installation, access and upgrades

Call `install_in_transaction(tx)` on a fresh database without a `truss` schema,
then commit the caller transaction. Inspect `status_in_transaction(tx)` rather
than treating assembly construction as proof of installation.

`CatalogRuntimeStatus` includes the observed `release_id`, `release_sha256` and
`layout_profile` (`ProfilePin`) alongside installation ID, catalog revision and
capabilities. All three are `None` when no installation exists. A mismatched
installed release refuses instead of supplying substituted version facts.
The local launcher's installation JSON exposes `releaseId`, `releaseSha256` and
`layoutProfile` from a fresh post-commit status check. These are candidate marker
facts; status does not certify the complete schema or security readiness. Existing
installer/registrar status authorization remains unchanged.

A direct trusted installer needs PostgreSQL `CREATEROLE` plus database
`CREATE WITH GRANT OPTION` or database ownership. A PostgreSQL superuser is not
required by the tested non-superuser installation path. Installation returns
fresh private owner and registrar role names. Grant registrar membership only
to ordinary people allowed to register catalogs; never grant consumers the
private owner or raw-table privileges.

Create safe non-login read/write roles, then call
`configure_module_access_in_transaction(tx, (ModuleAccessGrant(document_id,
module_id, reader_role, writer_role), ...))`. The method grants selected facades;
it does not create roles or grant people membership. The administrator supplies
those memberships. Configuration updates only supplied document/module pairs.
Existing-installation administration additionally needs inherited authority over
the retained owner role. Ordinary business calls refuse elevated installers and
owner members.

`upgrade_in_transaction(tx)` supports the exact retained runtime candidates
0.23 through 0.52 to the current runtime0.53. The trusted administrator must quiesce consumers and
settle the upgrade transaction. Active consumers cause a nonblocking refusal;
there is no retry loop. Supported upgrades preserve installation identity,
catalog IDs, data, receipts and feed checkpoints. Arbitrary older versions,
modified installations and downgrade routes are unsupported.

The local launcher exposes that same explicit migration operation:

```sh
truss-local-postgres --data-dir /tmp/truss-local --upgrade --probe
```

`--upgrade` and `--install` are mutually exclusive. A missing installation or
unsupported source refuses without falling back to installation. The output
reports `upgraded` or `unchanged`, with actual previous/current release IDs, only
after commit and fresh status confirmation of the same installation identity.
An explicit upgrade of the current candidate is unchanged. Keep application
connections quiescent for the migration; ordinary launch and `--install` never
perform upgrades.

## Public operations

The concrete `CatalogReferenceAssembly` returned for
`CatalogRuntimeConfiguration()` offers these methods. Its capability selectors
return concrete `Native*` providers for the selected installed profiles; a
broader draft protocol does not imply that every declared profile is implemented.

| Need | Public assembly methods |
| --- | --- |
| Register UMF | `prepare_catalog`, `accept_in_transaction` |
| Catalog reports | `report_in_transaction`, `catalog_view_in_transaction` |
| Reader-scoped catalog/source | `reader_catalog_in_transaction`, `accepted_document_in_transaction` |
| Object IDs and business keys | `get_object_in_transaction`, `lookup_key_in_transaction` |
| Object and relationship pages | `page_objects_in_transaction`, `get_edge_in_transaction`, `page_edges_in_transaction` |
| Build and apply groups | `group_context_in_transaction`, `get_type_reference_in_transaction`, `get_relationship_reference_in_transaction`, `apply_in_transaction` |
| Imports and provenance | `import_context_in_transaction`, `object_import_record_in_transaction`, `edge_import_record_in_transaction`, `import_in_transaction`, `lookup_import_source_in_transaction` |
| Retained history | `page_history_in_transaction`, `reconstruct_in_transaction` |
| Weft queries | `query_in_transaction`, or `compiled_execution(assembly.compiled_selection)` |
| Receipt visibility | `reached_in_transaction` |
| Feed enrollment/delivery | `register_feed_consumer_in_transaction`, `read_feed_in_transaction`, `reread_feed_in_transaction`, `acknowledge_feed_in_transaction` |
| Installation | `install_in_transaction`, `status_in_transaction`, `upgrade_in_transaction` |

Catalog, groups, imports, direct reads, history and feed also have typed
capability selectors. Imports/groups accept exact original `CatalogDocument`
inputs and the Bun executable where required by their selected provider.
Separate broad `mutations` and physical-optimization families remain unavailable.

## Catalog meaning and evolution

A `CatalogDocument(document_id, document_revision, content)` carries exact
original UTF-8 document bytes. Preparation runs the bundled UMF owner producer
through Bun; registration still requires Bun in the app image. The unreleased
prepared key boundary removes that requirement from ordinary key operations,
while leaving catalog admission with the broader UMF producer.
Native accepted IDs and definition pins come from the catalog, not fixtures.
Addresses are document-qualified. The authenticated person is recorded separately
from asserted origin, such as `origin_bytes=b'{"x-action":"register"}'`.

Registration returns a pending result until the host commits. Exact request-key
replay returns the original report; different input/origin under the same key
conflicts. An exact unchanged document has an unchanged result. Reader-scoped
catalog/source methods support authorized module readers and read-only
transactions. Accepted document bytes require complete read authority for all
modules in that document; partial-document disclosure refuses. The complete catalog-view facade requires registrar membership
and a read-write transaction. Original accepted bytes, digest and revision are
retained; document revision, artifact identity and registration ID are distinct
reported fields, not interchangeable IDs.

Compatible evolution supports additional Records, optional scalar properties,
relaxing non-key presence and widening independent relationship multiplicity or
adding endpoints. Unchanged IDs/pins remain stable. Candidate key-backfill support is described above. Retirement,
removal, identity rebinding and structured changes are unsupported. Incompatible
scalar/retained-name changes return typed rules and affected counts subject to
current authority. New optional properties do not manufacture object updates.

## Writes, conditions and retries

Build operations from `truss.groups`: `CreateObject`, `UpdateObject`, `Delete`,
`CreateEdge` and `UpdateEdge`. Multi-operation groups support newly created
endpoint aliases, edge retargeting and final-state multiplicity checks. Obtain
actual type/relationship references through the public methods. Caller rollback
of a successful group is the dry-run path.

For an idempotent atomic batch, submit one group containing every operation,
with one request key and one committed receipt token after commit recovery. Retain the original semantic input and request
for retries. The consumer example exercises two creates, committed replay and
a failed batch precondition leaving no partial object; native unique condition
IDs are explicitly mapped to the authored action labels. Independent per-item
batches are host orchestration with separate groups and caller transactions.

`context.input(..., preconditions=(...))` evaluates `ObjectExists`, `KeyAbsent`,
`PropertyEquals`, `RelationshipAbsent` and `RelationshipCount` against locked
prestate. Failed conditions return their caller IDs/reasons in order with no
group effects. `expected_version` remains available for updates/deletes.
`PropertyEquals` compares exact typed representations: absence, null and token
spelling remain distinct.

Use `context.request(your_idempotency_key)` to request durable replay, or
`RequestNone()` to omit it. Retain the original input/request for recovery; do not
rebuild retries using a later catalog. Repeating committed original input returns
`CommittedReceiptReplay` with its original results and receipt token, subject to
current authority. A successful first apply is pending until caller commit.
Unknown commit execution requires recovery with that original request rather
than allocating another logical write. No internal retry loops hide refusals.

Outer `Ok`/`Error` describes execution. An `Ok` can contain a semantic refusal or
unavailable value: inspect its concrete result type. Groups distinguish
`GroupSuccess` from `GroupFailed`, including unauthorized-person, invalid-input
and failed-precondition carriers. Known catalog execution refusals expose
`ExecutionFailure.catalog_code`. Use typed codes, not message parsing.

Imports return `ImportReported` or `ImportExecutionFailed` directly, rather than
the general outer `Ok`/`Error` wrapper. Host-owned imports return per-item created/skipped/rejected outcomes and batch
dispositions. Retain the load ID, authenticated actor and immutable source
provenance. Rejected items do not imply that other items in a caller-committed
batch failed. `run_import_batches` supplies separate engine-owned one-record
transactions on a fresh connection, preserving prior confirmed commits when
a later batch fails. It returns unknown commit outcomes explicitly.

Build relationship import records through the same selected import provider:

```python
from truss.groups import NullOrderKey

record = imports.edge_import_record_in_transaction(
    tx, document_id='notes', module_id='notes', relationship_id='references',
    source_endpoint=first_identity, target_endpoint=second_identity,
    values=(), order_key=NullOrderKey(),
)
```

The builder returns `Outcome[EdgeImportRecord]` with the actual accepted
relationship pin and exactly the supplied endpoint identities. Optional `source`
carries immutable import provenance, as it does for object records. Construction
does not establish live endpoints or authorize a write: `import_in_transaction`
validates current endpoint types, access, reservations and payload semantics.

## Values, reads and query limits

Rootless JSON-home objects and independent directed relationships support
strings and exact scalar properties: integer, decimal, boolean, timestamp and
binary. Exact numeric/time carriers preserve text semantics; do not route them
through floating point or lossy date conversions. Structured values, ownership
and composed graphs remain unsupported. Retained history can reconstruct stored
scalar images after updates/deletion; archival/offload and cleanup are unfinished.

Business-key lookup supports authored required string/integer/decimal18,4/boolean/binary
keys. Query pages currently require authored required-string keys. Direct object/edge pages have explicit live continuations. Query results
preserve absence versus null versus empty strings. Supported Weft queries include
string/boolean/integer/decimal projection, filters, property joins, counts,
ordering/limits, `alias.*`, and forward/inverse `HAS_RELATED`/`RELATED_KEYS` for
supported independent directed relationships. Decimal parameters use Python
`Decimal`; exact integer parameters use Python `int`. Binary floats refuse.
Supported projections and counts can use records/documents containing timestamp
and binary siblings. The complete original member mapping is retained, and every
source cell is validated before filtering. Timestamp and binary projections, including `alias.*`, return the existing
`TextValue` carriers with their original exact text; optional fields preserve
absence and explicit null. Required or absent-allowed singular binary fields support byte equality
with canonical base64 SQL literals, another binary field, or
`TextValue(kind="binary", text="AP8=")` parameters. Ordinary `str` parameters
remain strings. SDK0.0.23 additionally selects the shared
`umf-rfc3339-exact-instant/1.0.0` profile for timestamp equality. Required and
absent-allowed timestamp fields compare exact instants across offsets with
arbitrary fractional digits within the1MiB token limit, using literals, another
timestamp field, or `TextValue(kind="timestamp", text="2024-01-01T00:00:00.123456789Z")`.
Original timestamp text remains recoverable; `-00:00` retains unknown local-offset
knowledge while identifying a known instant. Binary/timestamp ordering, grouping
and temporal keys remain unsupported. The selected compile/IR/backend interfaces
are `0.2.6`, with the unchanged SQL dialect `0.2.0`; released SDK22 remains0.2.5.
Successful native `QueryRows` and `QueryPage` results carry `as_of: QueryReadPosition`. Its opaque `value` identifies a conservative committed lower bound captured immediately before the data query; `at` is the database capture time as a timezone-aware UTC `datetime`. The following READ COMMITTED statement can include newer commits. `caller_xid_assigned` reports only whether the caller already had a transaction ID; it does not prove writes or commitment. Constructors retain an optional default for compatibility, while this provider fills the position on every successful result, including empty rows.

Read-position values use their own namespace and are not receipt tokens. Do not pass them to `reached`, infer ordering from their strings or timestamps, or treat them as exact snapshots. An adapter may publish this position only with the stated lower-bound semantics. Current authority/context checks must pass before the result and position are returned.

Compiled queries require complete read authority for all modules in each selected
original document, including modules the SQL does not name.

`query_page_in_transaction(tx, sql=sql, document_ids=(document_id,), limit=100, cursor=None)` returns `QueryPage(columns, rows, catalog_revision, next_cursor)`. Pass `next_cursor` back to continue; `None` means the last page. The same call is available through the compiled-execution capability. Weft resolves the authored primary key, adds key ordering and continuation, and supplies hidden key outputs that Truss removes. The original SQL need not project the key or contain `ORDER BY`.

This public page call supports one nonaggregated source with a complete required primary key, including exact signed64, supported fixed-decimal and boolean components alongside strings. Returned numeric cells preserve Python integer/Decimal precision; continuation retains lossless lexical key tokens. Caller `ORDER BY`/`LIMIT`, joins and relationship predicates refuse. Cursors bind the original SQL, exact parameters, document selection, connecting person, catalog/installation/release context, limit and resource budgets. Keep those inputs unchanged for continuation. Each page rechecks current authority in the caller's transaction; pages are live, so concurrent changes can affect traversal.

`entity-page` and `related-entity-page` query profiles require complete authored
required-string keys in `ORDER BY`, an explicit limit and caller-supplied continuation predicates.
`count-summary` supports ungrouped counts and grouped counts on required, non-nullable string/boolean fields. Grouped summaries require the complete grouping order and an explicit `LIMIT`. Query continuation is live, not a
stable snapshot or exactly-once traversal. Multi-hop relationships, optional primary-key
components and optional/numeric grouped keys remain unsupported. Bounded sources are checked
before filters/limits; resource overflow refuses rather than truncating a source.

## Feed and receipt visibility

An administrator enrolls a named consumer with a safe reader role. An ordinary
authorized consumer reads exact committed `FeedPage` bytes, saves them durably,
then acknowledges that original page in a separate caller-committed transaction.
The example fsyncs both the content-addressed file and containing directory
before ACK. Read-only `reread_feed_in_transaction` recovers the exact retained
page; checkpoints do not advance until the ACK transaction commits.

`reached_in_transaction(tx, token)` checks source receipt visibility.
`reached_in_transaction(tx, token, consumer_id='sink')` compares the registered
consumer's committed source checkpoint. The latter requires a fresh read-only
transaction with no assigned transaction ID, so pending ACKs cannot count as
committed progress. Valid behind receipts return false; invalid tokens,
unauthorized/missing consumers or unavailable evidence refuse.

ACKs are caller assertions about source delivery. They do not prove downstream
application, another database's commit or replica freshness. This runtime retains
source history indefinitely; it has no retention cleanup or archival protocol.

## Evidence and remaining work

The public workflow and JSON preview use installed packages on the exact local
PG18 tuple. Evidence is recorded in
[the mixed-catalog, upgrade and preview receipt](../../docs/helix/04-build/evidence/python-mixed-catalog-20261012.json)
and [receipt/feed integration](../../docs/helix/04-build/evidence/python-feed-reached-20261012.json).
Broader value/query support, security activation and managed-service qualification
remain open. Independent implementation interchange is deferred under the owner’s
accepted scope amendment. Experimental pg8000 and older private profiles are historical paths.

The [runtime history](docs/runtime-history.md) preserves the earlier release diary.
Its old limitations describe their named versions, not the current interface.

## Historical section links

These links retain earlier README section addresses.

<a id="run-the-adopter-workflow"></a>

[Run the adopter workflow](docs/runtime-history.md#run-the-adopter-workflow) — historical release notes.

<a id="public-catalog-workflow"></a>

[Public catalog workflow](docs/runtime-history.md#public-catalog-workflow) — historical release notes.

<a id="python-execution-contracts"></a>

[Python execution contracts](docs/runtime-history.md#python-execution-contracts) — historical release notes.

<a id="draft-public-group-contracts"></a>

[Draft public group contracts](docs/runtime-history.md#draft-public-group-contracts) — historical release notes.

<a id="draft-import-contracts"></a>

[Draft import contracts](docs/runtime-history.md#draft-import-contracts) — historical release notes.

<a id="prepare-original-umf-for-catalog-registration"></a>

[Prepare original UMF for catalog registration](docs/runtime-history.md#prepare-original-umf-for-catalog-registration) — historical release notes.

<a id="private-native-catalog-staging"></a>

[Private native catalog staging](docs/runtime-history.md#private-native-catalog-staging) — historical release notes.

<a id="private-catalog-report-integration"></a>

[Private catalog report integration](docs/runtime-history.md#private-catalog-report-integration) — historical release notes.

<a id="selected-host-transaction-entry-point"></a>

[Selected host transaction entry point](docs/runtime-history.md#selected-host-transaction-entry-point) — historical release notes.

<a id="explicit-postgresql-186-host-profile"></a>

[Explicit PostgreSQL 18.6 host profile](docs/runtime-history.md#explicit-postgresql-186-host-profile) — historical release notes.

<a id="public-object-identity-read"></a>

[Public object identity read](docs/runtime-history.md#public-object-identity-read) — historical release notes.

<a id="public-create-only-group-provider-runtime-04"></a>

[Public create-only group provider: runtime 0.4](docs/runtime-history.md#public-create-only-group-provider-runtime-04) — historical release notes.

<a id="ordinary-reader-catalog-and-accepted-source-runtime-05"></a>

[Ordinary-reader catalog and accepted source: runtime 0.5](docs/runtime-history.md#ordinary-reader-catalog-and-accepted-source-runtime-05) — historical release notes.

<a id="public-reads-on-read-only-transactions-runtime-06"></a>

[Public reads on read-only transactions: runtime 0.6](docs/runtime-history.md#public-reads-on-read-only-transactions-runtime-06) — historical release notes.

<a id="typed-catalog-failure-codes-runtime-07"></a>

[Typed catalog failure codes: runtime 0.7](docs/runtime-history.md#typed-catalog-failure-codes-runtime-07) — historical release notes.

<a id="business-key-lookup-runtime-08"></a>

[Business-key lookup: runtime 0.8](docs/runtime-history.md#business-key-lookup-runtime-08) — historical release notes.

<a id="atomic-caller-preconditions-runtime-015-candidate"></a>

[Atomic caller preconditions (runtime 0.15 candidate)](docs/runtime-history.md#atomic-caller-preconditions-runtime-015-candidate) — historical release notes.

<a id="public-object-updates-and-deletes-runtime-014-candidate"></a>

[Public object updates and deletes (runtime 0.14 candidate)](docs/runtime-history.md#public-object-updates-and-deletes-runtime-014-candidate) — historical release notes.

<a id="changed-document-scalar-refusal-runtime-013-candidate"></a>

[Changed-document scalar refusal (runtime 0.13 candidate)](docs/runtime-history.md#changed-document-scalar-refusal-runtime-013-candidate) — historical release notes.

<a id="exact-input-unchanged-registration-runtime-09-candidate"></a>

[Exact-input unchanged registration (runtime 0.9 candidate)](docs/runtime-history.md#exact-input-unchanged-registration-runtime-09-candidate) — historical release notes.

<a id="additional-documents-runtime-010-candidate"></a>

[Additional documents (runtime 0.10 candidate)](docs/runtime-history.md#additional-documents-runtime-010-candidate) — historical release notes.

<a id="exact-scalar-properties-runtime-011-candidate"></a>

[Exact scalar properties (runtime 0.11 candidate)](docs/runtime-history.md#exact-scalar-properties-runtime-011-candidate) — historical release notes.

<a id="live-object-pages-runtime-012-candidate"></a>

[Live object pages (runtime 0.12 candidate)](docs/runtime-history.md#live-object-pages-runtime-012-candidate) — historical release notes.

<a id="independent-directed-relationships-runtime-016-candidate"></a>

[Independent directed relationships (runtime 0.16 candidate)](docs/runtime-history.md#independent-directed-relationships-runtime-016-candidate) — historical release notes.

<a id="committed-receipt-tokens-and-reached-runtime-017-candidate"></a>

[Committed receipt tokens and reached (runtime 0.17 candidate)](docs/runtime-history.md#committed-receipt-tokens-and-reached-runtime-017-candidate) — historical release notes.

<a id="caller-owned-imports-runtime-018-candidate"></a>

[Caller-owned imports (runtime 0.18 candidate)](docs/runtime-history.md#caller-owned-imports-runtime-018-candidate) — historical release notes.

<a id="compatible-document-acceptance-runtime-019-candidate"></a>

[Compatible document acceptance (runtime 0.19 candidate)](docs/runtime-history.md#compatible-document-acceptance-runtime-019-candidate) — historical release notes.

<a id="public-committed-feed-and-source-ack-runtime-020-candidate"></a>

[Public committed feed and source ACK (runtime 0.20 candidate)](docs/runtime-history.md#public-committed-feed-and-source-ack-runtime-020-candidate) — historical release notes.

<a id="selected-native-capability-objects"></a>

[Selected native capability objects](docs/runtime-history.md#selected-native-capability-objects) — historical release notes.

<a id="public-retained-history-runtime-021-candidate"></a>

[Public retained history (runtime 0.21 candidate)](docs/runtime-history.md#public-retained-history-runtime-021-candidate) — historical release notes.

<a id="read-only-feed-recovery-runtime-022-candidate"></a>

[Read-only feed recovery (runtime 0.22 candidate)](docs/runtime-history.md#read-only-feed-recovery-runtime-022-candidate) — historical release notes.

<a id="retained-import-provenance-runtime-023-candidate"></a>

[Retained import provenance (runtime 0.23 candidate)](docs/runtime-history.md#retained-import-provenance-runtime-023-candidate) — historical release notes.

<a id="additive-runtime-upgrade-023--024-candidate"></a>

[Additive runtime upgrade (0.23 → 0.24 candidate)](docs/runtime-history.md#additive-runtime-upgrade-023--024-candidate) — historical release notes.

<a id="installation-without-postgresql-superuser-runtime-025-candidate"></a>

[Installation without PostgreSQL superuser (runtime 0.25 candidate)](docs/runtime-history.md#installation-without-postgresql-superuser-runtime-025-candidate) — historical release notes.

<a id="public-compiled-queries"></a>

[Public compiled queries](docs/runtime-history.md#public-compiled-queries) — historical release notes.

<a id="compiled-query-pages"></a>

[Compiled query pages](docs/runtime-history.md#compiled-query-pages) — historical release notes.

<a id="has-a-feed-consumer-acknowledged-a-receipt"></a>

[Has a feed consumer acknowledged a receipt?](docs/runtime-history.md#has-a-feed-consumer-acknowledged-a-receipt) — historical release notes.

<a id="versioned-public-preview-corpus"></a>

[Versioned public preview corpus](docs/runtime-history.md#versioned-public-preview-corpus) — historical release notes.

Catalog registration also retains original vocabulary and extension artifacts and
owner-reported module actions as uninterpreted metadata. It preserves the original
validation diagnostics and partial interpretation; it does not execute actions or
interpret placement, DDD or security annotations. Required core semantics still
must be supported. The original consumer corpus has fourteen original read/action/import workflows
exercised through public registration, grouped object/edge mutation, committed replay, receipt visibility and read-only queries;
Mixed imports exercise native create/skip/reject results and provenance; a missing
relationship endpoint is a separately identified host rejection after public
source/catalog/key reads. Replica execution and the full consumer corpus remain unqualified.

Select `read_profile="complete-entity"` for `alias.*` with complete relationship
keys and `_version`, `_created_by`, `_created_at`, `_updated_by`, `_updated_at`, `_original_author` and
`_original_at` and `_load_id`. Truss derives attribution from original native mutation/import
evidence. Missing evidence, output-name collisions or more than100 related keys
refuse the query. Single-component relationship keys are immutable scalar tuples;
composite keys retain nested tuples. Ordinary projections keep their authored
member shape. Whole-object timestamps use exact six-fraction UTC strings from the verified object image. The original whole-entity SQL/output observations pass on the pinned tuple; position/time shape checks use the declared committed lower-bound semantics, while complete consumer-adapter and harness qualification remain open.

The original consumer AddSolution example is a trusted host handler bound to the exact retained fixture document. It resolves a target by public business-key lookup, submits one create/link group with a native ObjectExists precondition and x-action origin, retains the invocation's original request for committed recovery, and reads the result through the public API. It does not interpret arbitrary UMF action declarations. Counts, initial disposition and versions come from native semantic results; the committed token is attached only after verified replay following the host's known commit.

The selected AddUseCase retry workflow maps its caller key directly to the group request ID, applies the original native KeyAbsent predicate, and retains the canonical input/request for retry. Every repeated step still calls Truss; the host cache supplies no result. The original committed token and semantic result are returned with replay disposition, and readback finds one object. The original AddSolution dry-run case now uses the public caller-rollback group workflow; other consumer action cases remain outside this example handler.

Dry-run previews execute the actual create/link group and roll back the caller transaction before returning validation. They return no provisional identity or receipt token and retain no invocation cache. A later real write with the same caller key is admitted normally. Missing-target previews require an exact public ObjectNotFound plus current authorized source/catalog/type/key visibility in the known fixture; other results refuse. This is a host authority observation, not a general native key-exists predicate. The dry-run case uses its own fresh basic fixture; rolled-back sequence allocations may still leave gaps.

The original CorrectSolution workflow now resolves the authored business key, applies an optimistic-version UpdateObject with the declared ObjectExists precondition, and recovers the committed native receipt using its original request. Complete-entity readback proves one version increment and preserves creation attribution while recording the connecting person as updater. This is a trusted host handler for the exact retained consumer document, not a general action interpreter.

The original `read.count-group-by` case is runnable with `--case`, including its record seed through public groups. Counts are exact integers, but the unchanged case currently fails its positional row oracle: the SQL has no `ORDER BY` and PostgreSQL returns the correct groups in another order. It is excluded from the passing aggregate pending a consumer-owned ordering expectation correction.

The original edge-first import workflow is exercised by a trusted host mapping: import objects, resolve both authored business keys through public reads, then import relationships within the same caller transaction. The two native reports stay unchanged and pending as returned; the host publishes aggregate consumer counts only after its outer commit. This supports the selected consumer flow without inventing endpoint identities, a combined ImportReport or a commit token. General unresolved-reference batch ingestion remains outside the low-level typed-identity API.


### Destination receipt retention and ACK recovery (runtime0.38)

The ordinary feed provider exposes these methods, also available on CatalogReferenceAssembly:

```python
pending = feed.acknowledge_feed_with_receipt_in_transaction(
    tx, page, destination_id="ashlar-delta", request_sha256=request_digest,
    publication_id=publication_id, receipt_bytes=exact_destination_receipt,
)
# The host commits its PostgreSQL transaction.
observed = feed.reconcile_feed_ack_in_transaction(
    fresh_read_only_tx, page, destination_id="ashlar-delta",
    request_sha256=request_digest, publication_id=publication_id,
    receipt_bytes=exact_destination_receipt,
)
```

Both calls return Outcome. A successful write carries FeedReceiptAcknowledged
with pending durability and advanced/equal disposition. A successful read carries
FeedAckReconciled with matched/missing/conflicting, the observed checkpoint and
an authorized retained FeedAckReceipt (None only for missing). The receipt binds
installation/source epoch, consumer/registration, exact prior/next cursors and
feed digest to destination identity, request digest, publication identity and
exact opaque bytes. Receipt bytes are limited to1MiB; destination/publication IDs
to1024/4096 UTF-8 bytes. Hashes never replace exact-byte comparison.

Reconciliation assigns no transaction ID and performs no ACK write. Use a fresh
read-only transaction after an uncertain COMMIT; an earlier matching receipt
remains matched after later checkpoint advances. Missing means no committed
receipt is visible in this observation, not proof of rollback or permission to
republish. Conflicting evidence refuses a write without checkpoint movement.
Plain ACK has no receipt evidence and cannot be backfilled after its advance.
First receipt creation refuses a zero-width interval. Receipts remain retained;
there is no cleanup API. The destination consumer verifies its own publication
before ACK. Truss confirms source retention and checkpoint inclusion and does
not verify another database's commit or grant history-deletion authority.

### Exact numeric facets (v0.0.14)

Numeric support began in v0.0.2 and is retained by runtime `0.40-candidate`
and Weft `0.4.5` / backend `0.4.10`. Fresh UMF 0.7 and 0.8 catalogs can declare signed
64-bit integers and decimal precision 18, scale 4. Public creates, updates,
imports, reads and compiled queries enforce these facets without float coercion
or rounding. Decimal `1.2`, `1.2300` and `1.23000` are exact representable values;
`1.23001` is refused. Direct reads preserve the authored token; Python queries
return `int` and `Decimal`. Other facet combinations and key-facet evolution remain
unsupported. Existing non-key properties may add/remove these known facets after
native real-data validation. A narrowing that fails returns typed
`property.facets` rules and affected counts; acceptance preserves object versions
and original value tokens. Enforcement is through runtime operations, not bare-table CHECKs.
Existing installation upgrades preserve original reports and receipts.

These capabilities were added after v0.0.1.

### Typed business keys (v0.0.14)

The `0.0.3` package / runtime `0.40-candidate` adds authored business-key
writes, updates, lookup, imports and key-absence preconditions for strings,
integers, decimal(18,4), booleans and binary. The matching compiler is Weft
`0.4.5` / backend `0.4.10`. Use existing `TextValue` and `BooleanValue` key
components; bare strings retain their previous meaning. For example:

```python
values = ('invoice', TextValue(kind='integer', text='9007199254740993'),
          TextValue(kind='decimal', text='1.23000'), BooleanValue(value=True),
          TextValue(kind='binary', text='AP8='))
result = reads.lookup_key_in_transaction(
    tx, document_id='orders', module_id='orders', record_id='Invoice',
    key_id='primary', values=values, bun_executable='bun',
)
```

Equal decimal spellings identify the same key without changing stored tokens.
Updates preserve old reservations; imports skip reserved or live identities.
Historical committed requests retain their original results across upgrade.
Timestamp/float keys are refused. Weft pagination still requires string keys. Relationship predicates and key
projections now also support required boolean, integer and decimal(18,4) keys. This tranche was added after v0.0.2.

## One-call graph traversal

After obtaining a current typed object identity and relationship reference:

```python
from truss import TraversalHop, TraversalComplete, TraversalLimited
relationship = assembly.get_relationship_reference_in_transaction(
    tx, document_id="notes", module_id="notes", relationship_id="related").value
result = assembly.traverse_in_transaction(
    tx, start=note.identity, hops=(TraversalHop(relationship=relationship),),
    maximum_objects=100, maximum_path_states=10000)
```

One to three ordered hops support outgoing, incoming or both directions over
independent directed relationships. Complete results contain all unique terminal
objects in numeric type/id order. Paths cannot repeat a typed object, including
the start. Read-only READ COMMITTED transactions work. All selected relationship,
endpoint and property declaration modules require current read access.

A limited result contains no objects and requires restart. Bounds cover logical
attempted states and output; use ordinary PostgreSQL deadlines too. Membership is
live per call; no cursor, held snapshot, resume or exact backend allocation claim.

## Scalar arrays and maps (v0.0.14)

Original UMF core0.7/0.8 Fields may declare `cardinality: array` or `map`
with an explicit same-document `itemType` reference to a required singular
scalar Field. Item-only Fields remain schema definitions, not object properties.
String, integer, decimal, boolean, timestamp and binary items use the scalar
carriers, including signed64 and decimal(18,4) facets. Nested containers,
record-valued items and optional items are refused.

Pass `SequenceValue(items=(...))` or `MapValue(entries=(MapEntry(...), ...))`
in `AuthoredValue`. Sequences preserve order and duplicates; map keys must be
unique exact strings and are stored in canonical key order. Absent, null and
empty containers remain distinct. Writes, imports, direct reads, preconditions
and retained history preserve exact item tokens. The item definition's module
requires current reader or writer authority alongside property declarations.

Containers have at most1024 items, map keys at most4096 UTF-8 bytes and complete
cells at most1 MiB, in addition to ordinary group/result bounds. Item meaning or
reference changes are refused in this tranche. Native admission recognizes old
scalar-only import payloads; the Python importer requires its current profile.
Development Weft0.4.9 projects these values and complete entities through
`QueryRows`: arrays become tuples, maps become immutable key-sorted mappings,
and integer/decimal items become exact Python int/Decimal values. v0.0.6 with
Weft0.4.8 still refuses container-bearing query selections. Container comparisons,
unnesting and nested values remain unsupported.
Runtime0.43 upgrades0.42 additively without rewriting original data or receipts.

## Typed relationship keys (v0.0.14)

`HAS_RELATED`, `RELATED_KEYS` and complete-entity relationship key lists support
required string, boolean, integer (unfaceted or signed64), and decimal(18,4)
components. Comparison and ordering are typed; projection preserves original
numeric token text until exact Python int/Decimal decoding. `QueryRelatedKeys`
contains immutable tuples of those types, with its existing truncation flag.
Complete lists refuse overflow rather than returning a partial complete result.

Business-key query pages remain string-only. Binary/timestamp relationship keys
and unfaceted decimal business keys remain unsupported. This is native0.45 /
Weft0.4.10/backend0.4.15; original0.44 upgrades additively.

## Exact typed SQL pages (v0.0.14)

`assembly.query_page_in_transaction(tx, sql=..., document_ids=(...), limit=100,
cursor=prior.next_cursor)` supports required string, boolean, integer and
decimal(18,4) authored primary keys. The entrypoint supplies complete primary-key
ordering and lookahead; caller SQL must omit ORDER BY/LIMIT, aggregates and joins.
Returned int/Decimal/bool values remain exact. Opaque cursor0.2 carries lossless
lexical key tokens and the original query/catalog/runtime context.

A page is live per call, not a held multi-call snapshot. Catalog/query/runtime
changes invalidate continuation. Existing explicit `entity-page` and
`related-entity-page` query profiles retain their string-only key scope; typed
pages use the selected Weft SQL-page0.2 wrapper. No binary/timestamp or unfaceted
decimal key claim. Native0.46 upgrades0.45 additively.

## Record names and member order (v0.0.14)

Reaccept a document to rename a Record or reorder retained qualified members.
Catalog IDs and stored object/key rows stay stable. SQL uses the current Record
name and complete-entity column order follows its members. Property names, key
components and all other Record meaning retain compatibility guards. Original
documents, reports, committed history and idempotent receipt replay are retained.
Native0.47/layout0.16 pairs with Weft0.4.12/backend0.4.17;0.46 upgrades additively.

## Compatible required-field tightening (v0.0.14)

Existing non-key singular scalar fields may change from absent-allowed to
required. Acceptance refuses missing/null/incompatible values with rule and
affected-object counts. Repair with ordinary public writes and reaccept. No
object values, versions, IDs or original history are changed by acceptance.
New required fields, key-participating fields and containers retain their
existing restrictions. Native0.48/Weft backend0.4.18 upgrade0.47 additively.

## Compatible relationship bounds (v0.0.14)

Existing independent relationships may tighten min/max bounds when current
data satisfies them. CatalogAcceptanceRefused.violations can contain
CatalogRelationshipCompatibilityViolation with document_id, module_id,
relationship_id, side, rule and affected_object_count. Side source counts
source objects using targetMultiplicity; side target counts target objects
using sourceMultiplicity. Zero-edge objects participate. Relationship and
all endpoint modules require current read authority to disclose counts.
Repair using public groups and retry acceptance. Tightening preserves endpoint
declarations. Existing object/edge rows remain unchanged; later writes enforce
the new bounds. Native0.49/Weft backend0.4.19 upgrade0.48 additively.

## Required flat containers (v0.0.14)

Existing non-key scalar array/map fields can tighten absent-allowed to required
while keeping cardinality, item reference and definition unchanged. Missing or
null containers refuse with property.required counts; empty arrays/maps count
as present. Repair through public writes and reaccept. Native0.50/Weft
backend0.4.20 upgrades0.49 additively. Nested values remain outside this profile.


## Parallel independent edges (v0.0.15)

Create distinct edge IDs with the same relationship and endpoints, including
self-edges. Each occurrence counts toward multiplicity. Edge pages/history keep
the IDs; relationship-key lists preserve duplicate occurrences; traversal
still returns distinct terminal objects. Delete a chosen edge by its ID.
Endpoint-only imports refuse multiple live matches before decoding payloads.

Layout1.0 removes the old unique endpoint index. Use the trusted administrative
upgrade for populated layout0.16 installations. Genesis, original receipts and
saved feed pages remain retained; new facts carry their producing transaction's
configuration. Native0.52 pairs with Weft0.4.17/backend0.4.22.


## Relationship presentation names (v0.0.16)

Reaccept a document to rename an existing relationship `name` or an existing
string `inverse` label. Stable document/module/relationship IDs, endpoints,
keys, direction and lifecycle retain their guards. This tranche does not add or
remove inverse labels. Current SQL uses the new forward/inverse labels; obtain
a fresh relationship reference for mutations and traversal. Acceptance leaves
edge IDs, versions and values unchanged. Original request replay and history
retain the original meaning. Native0.53/layout1.0 pairs with
Weft0.4.18/backend0.4.23 and upgrades0.52 additively.

## Binary byte equality (SDK0.0.17 source tranche)

Native0.54 and Weft0.4.19/backend0.4.24 add required singular binary equality to
filters and INNER joins. Query-page filters retain the same exact parameter map
in their cursor context. Canonical base64 is checked independently in Python
and Weft; SQL compares decoded bytes while projections preserve source text.
Empty binary values are valid. Timestamp semantics remain projection-only.
The native upgrade from0.53 retains existing data, receipts and feed custody.

## Optional binary equality (SDK0.0.18 source tranche)

Native0.55 and Weft0.4.20/backend0.4.25 extend byte equality to optional
binary fields. Absent and explicit null retain distinct projections and yield
SQL UNKNOWN in equality predicates; neither matches an ordinary binary value.
Empty bytes remain a value. The new optional-equality capability is refused by
the retained required-only backend0.4.24. No timestamp, ordering, grouping or
null-parameter support is implied. Wire0.2.5 remains unchanged.

## Decimal(18,2) and field names (v0.0.21)

Adds original decimal(18,2) facets alongside decimal(18,4) across catalog acceptance, writes/imports, reads, business keys and Weft queries/pages. Exact tokens are preserved, including redundant zeros. Maximum9999999999999999.99 is valid; excess precision or nonrepresentable scale refuses. Name-only Field evolution retains property/key identities. Native57 upgrades56 transactionally and requires matching Weft0.4.22/backend0.4.27. The unpublished20 candidate failed retained-extension checks;21 corrects that omission. Published21 passed its release workflows on both declared native platforms.

## Original documents and compact reports (v0.0.22)

Prepare a model without starting PostgreSQL:

```python
from truss import CatalogDocument, prepare_catalog

prepared = prepare_catalog((CatalogDocument(document_id, revision, original_bytes),),
                           source_version="0.8.0")
```

The assembly method uses the same preparation. Registration still uses the caller's transaction. UMF0.8 support0.14 preserves top-level title metadata and emits catalog report0.2 with same-report source references; exact source bytes remain in acceptedInput. Use public `resolve_catalog_report_source(report_bytes, entry["source"])` to retrieve their checked bytes, digest, identity and revision. Occurrence locations and required-field inventory remain in assertion entries; unknown extension content stays intact. See the [source-reference contract](../../docs/helix/02-design/contracts/catalog-source-reference-v0.1.md).

One unchanged original commerce slice is tested through registration, supplier/product/required relationship creation, key lookup, exact decimal(18,2) queries, committed replay and feed. Other packs are separately unqualified. Matching native58/layout1.0 and Weft0.4.23/backend0.4.28 are required; native57 upgrades transactionally. Published22 passed its Linux and macOS release workflows; the install example above selects22 and matching Weft23.
