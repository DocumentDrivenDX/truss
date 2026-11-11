# umf-truss: the Truss Python package

`umf-truss` (import `truss`) is Truss: an embeddable, property-oriented graph store on PostgreSQL 18.6
whose types come from UMF documents. It is experimental. See the [repository README](../../README.md)
for the install command and a five-minute quickstart, and [CHANGELOG](../../CHANGELOG.md) for versions.

```sh
pip install "umf-truss[local,native,query]" \
  --find-links https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2
```

| Extra | Adds |
| --- | --- |
| `native` | `psycopg` 3.3, the supported PostgreSQL driver |
| `query` | `umf-weft`, for Weft query compilation |
| `local` | `pgserver-pg18` (PostgreSQL 18.6), `LocalPostgres` and the `truss-local-postgres` command |
| `typed-sdk` | experimental: `truss.access`, needs umf-access 0.10.11 (not yet published) |
| `experimental-pg8000` | experimental pg8000 driver |

Runnable examples are in [`examples/`](examples/): [`quickstart.py`](examples/quickstart.py) (install,
register, create, look up, query, feed) and [`adopter_workflow.py`](examples/adopter_workflow.py) (adds
receipts, replay, imports and dry runs).

## Local PostgreSQL

`LocalPostgres(directory)` is a context manager that owns one PostgreSQL 18.6 cluster in `directory`
with a private Unix socket (no TCP listener). It starts and stops the server; it never installs Truss
or upgrades data. `runtime.info.connection_uri` is the connection URI. `initdb` can take over a minute on
a slow disk: set `TRUSS_LOCAL_TIMEOUT_S` (default 300) to allow longer. A killed process can leave a
server running; stop it with `pg_ctl -D <directory>/data stop` from the `pgserver` package.

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

## Fresh installation and access

Call `install_in_transaction(tx)` on a fresh database without a `truss` schema,
then commit the caller transaction. The call defaults to the adopted host's
operation deadline. A caller that needs more time for the ordered installation
DDL may pass `operation_timeout_ms=180000`; this extends only that one install
operation, with a maximum of 180 seconds. The host's native statement timeout
remains capped at 60 seconds, and later operations keep the host's configured
deadline. The timeout requests cancellation; it does not guarantee backend
termination or settle the caller's transaction. Inspect `status_in_transaction(tx)`
rather than treating assembly construction as proof of installation.

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

Fresh installation requires a database without a `truss` schema. Installing a new wheel never
migrates or resets an existing database; an installation that does not match the packaged runtime is
refused.

The local launcher can install or confirm a current installation:

```sh
truss-local-postgres --data-dir /tmp/truss-current --install --probe
```

Use a new directory for a fresh local runtime. `--install` never resets existing
data, and `--upgrade` is not a recognized option. The output confirms the
committed installation identity and exact current release through a fresh
status check.

## Public operations

The concrete `CatalogReferenceAssembly` returned for
`CatalogRuntimeConfiguration()` offers these methods. Its capability selectors
return concrete `Native*` providers for the selected installed profiles; a
broader draft protocol does not imply that every declared profile is implemented.

| Need | Public assembly methods |
| --- | --- |
| Register UMF | `prepare_catalog`, `accept_in_transaction` |
| Catalog reports | `report_in_transaction`, `catalog_view_in_transaction` |
| Cached write planning | `prepare_group_in_transaction`, `catalog_revision_in_transaction` |
| Reader-scoped catalog/source | `reader_catalog_in_transaction`, `accepted_document_in_transaction` |
| Object IDs and business keys | `get_object_in_transaction`, `lookup_key_in_transaction` |
| Object and relationship pages | `page_objects_in_transaction`, `get_edge_in_transaction`, `page_edges_in_transaction` |
| Build and apply groups | `group_context_in_transaction`, `get_type_reference_in_transaction`, `get_relationship_reference_in_transaction`, `apply_in_transaction` |
| Imports and provenance | `import_context_in_transaction`, `object_import_record_in_transaction`, `edge_import_record_in_transaction`, `import_in_transaction`, `lookup_import_source_in_transaction` |
| Retained history | `page_history_in_transaction`, `reconstruct_in_transaction` |
| Weft queries | `query_in_transaction`, or `compiled_execution(assembly.compiled_selection)` |
| Receipt visibility | `reached_in_transaction` |
| Feed enrollment/delivery | `register_feed_consumer_in_transaction`, `read_feed_in_transaction`, `reread_feed_in_transaction`, `acknowledge_feed_in_transaction` |
| Installation | `install_in_transaction`, `status_in_transaction` |

Catalog, groups, imports, direct reads, history and feed also have typed
capability selectors. Imports/groups accept exact original `CatalogDocument`
inputs. The legacy `bun_executable` keyword is retained for source compatibility
and does not select or launch an executable.
Separate broad `mutations` and physical-optimization families remain unavailable.

`prepare_group_in_transaction(tx,
records=((document_id, module_id, record_id),), relationships=())`, returning the
catalog revision, group context and requested references together. A host may
cache this planning metadata for the same installation, source epoch, principal
and catalog basis. `catalog_revision_in_transaction(tx, document_id=...)` provides
a small revision probe. Build groups with the cached `prepared.context.input(...)`
and the returned definition pins; the write still checks its current basis and
authority. A stale write refuses rather than silently retrying a mutation. This
API is exercised by the test suite.

## Catalog meaning and evolution

A `CatalogDocument(document_id, document_revision, content)` carries exact
original UTF-8 document bytes. Preparation runs the bundled UMF owner producer
inside embedded V8; registration requires no external JavaScript runtime. Ordinary key
operations derive keys in PostgreSQL, while catalog admission uses the broader
UMF producer.
The Python registration preparation routes require an explicitly authored,
nonempty `name` on every Record and Field, including unreferenced Fields. UMF
itself still permits unnamed elements. A refusal raises
`PreparationRejected(reason='invalid_document')`; decode each entry of
`error.diagnostics` with `json.loads` for `TRUSS-NAME-MISSING`, document/revision,
module/element IDs, kind, JSON pointer and message. No catalog write occurs.
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

The owned scalar-graph profile permits 1,024 operations and 3,072 preconditions
per group. The retired rootless condition-inventory component retains its
128-condition ceiling; this does not restore executable legacy-profile support. Conditions
use unique IDs across the whole group and all observe prestate, including when
an earlier operation creates or changes their target. Failed conditions take
precedence over operation failures. The existing input-byte, scope, lock and
operation-time limits also apply; an oversized group is never silently split.

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

Contained permission denials return `UnauthorizedPerson` for group context,
`CatalogRefused` for catalog planning/reference calls, and `ObjectReadRefused`
for direct object/key/edge/page/traversal calls. Each has the stable
`unauthorized` code (`unauthorized_person` for `UnauthorizedPerson`) without
disclosing hidden existence or role details. Native
transport failures and unusable transactions retain their outer `Error`.
`GroupOperationFailure.code` remains `group_failed`; its `operation_code`
exposes the native leaf classification and `inner_error` retains the original
artifact. Batched key conflicts identify the original colliding operation,
including conflicts with reserved deleted keys.

Imports return `ImportReported` or `ImportExecutionFailed` directly, rather than
the general outer `Ok`/`Error` wrapper. Host-owned imports return per-item created/skipped/rejected outcomes and batch
dispositions. Retain the load ID, authenticated actor and immutable source
provenance. For legacy imports, rejected items do not imply that other items in a
caller-committed batch failed. For legacy inputs, `run_import_batches` supplies separate
engine-owned one-record transactions on a fresh connection, preserving prior
confirmed commits when a later batch fails. Explicit owned inputs use one atomic
aggregate transaction. The runner returns unknown commit outcomes explicitly.

Legacy `ImportInput` calls accept at most 128 records and 8 MiB of canonical
input, with a 1 MiB payload ceiling per record. These are per-call limits, not a
promise that repeated calls fit the cumulative transaction limits. The current
legacy builder and executor perform work per record; larger and batched imports
remain separate work. Handle `ImportInvalid`, `ImportReported`,
`ImportResourceLimited` and `ImportExecutionFailed` according to their declared
carriers; retain every report's pending, rollback and unknown durability state.

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

The atomic owned-import profile uses `owned_import_context_in_transaction`,
`owned_object_import_record_in_transaction` and
`owned_edge_import_record_in_transaction`. Build rootless roots first, then
children with `root=root_record.identity`, then edges whose endpoints are those
primary-key selections. Pass the records to `context.input(...)` and the existing
`import_in_transaction` method. One group and all original source attachments
share one savepoint. A dependent failure rolls back every new record; existing
identities skip before replacement payload decoding. References must identify
live objects or earlier eligible records; forward references refuse.

Caller-owned execution leaves settlement to the host. `run_import_batches` also
accepts this explicit owned input and commits the entire aggregate as one batch;
legacy inputs retain one-record batches. Original record indices, source bytes
and load IDs remain available through `lookup_import_source_in_transaction`.
Managed-database and broader performance qualification remain separate.

## Values, reads and query limits

`query_with_catalog_in_transaction(tx, sql=sql, document_ids=(document_id,),
catalog_validator=previous_validator)` returns `QueryCatalogRead`: query rows,
a current `ReaderCatalogSnapshot` or `ReaderCatalogUnchanged`, and exact original
`QueryDocument` bytes/digests. It uses one adopted caller transaction and one
operation, with a final check for both query and catalog visibility. Retain the
snapshot with its validator. Use this route when a host otherwise opens separate
transactions for catalog access, document retrieval and the query. It creates no
connection or transaction. The regular query API remains available.

Successful compilations are cached under the complete exact compiler request,
including parameters, model bytes/pins, binding and profiles. Different values
miss; there is no value-independent template API. Warm query metadata uses a
native current-person/dependency check and source-digest validator instead of
transferring the complete source again. Neither cache retains authorization.

`read_profile='complete-entity'` adds native facts and relationship-key columns
to a supported single-source `alias.*` projection. An explicit `RELATED_KEYS`
output whose alias collides with an added relationship column is refused with
`WFT-OUTPUT-NAME`; the compiler does not overwrite or rename either output.
Choose a distinct explicit alias, for example
`RELATED_KEYS(a."A-B",100) AS "_A-B"`, when also selecting `a.*`. Quote aliases
whose spelling/case must be preserved. The complete relationship column is
bounded at 100 keys and refuses rather than silently truncating; an explicit
bounded related-key projection has its own reported truncation semantics.
Wildcard `EXCLUDE`/`REPLACE` syntax is not selected for this release, and no
delivery date is committed. To omit or rename wildcard members, write an explicit
projection list; to add a relationship projection after `a.*`, use a unique alias.

`maximum_scan_rows` is a **source population bound**, capped at 10,000. It applies
before outer SQL predicates, joins, ordering, aggregates and `LIMIT`. A selective
key predicate or small output does not make a large type admissible.

| Statement shape | Source subject to the bound |
| --- | --- |
| Projection or singleton predicate, with or without `LIMIT` | Every object of each scanned type |
| `COUNT`, grouped aggregates | Every object of each scanned type, even when one aggregate row is returned |
| Property joins | Each scanned type independently; not merely matching joined rows |
| `HAS_RELATED`, `RELATED_KEYS`, complete-entity relationships | Every object/edge source invoked by lowering; the separate related-key bound also applies |
| Explicit entity-page and typed query-page APIs | The current page source delegates to the same complete bounded object source; continuation does not exempt it |

Weft's compiled `logicalPlan` describes source/joins/relationship expressions;
its emitted SQL names the fixed `query_objects`, `query_edges` and
`query_page_objects` sources. Hosts can compile against admitted cached inputs
and inspect that plan before dispatching data SQL, then conservatively refuse
any source whose population is not known to fit. There is no cached cardinality
or admission promise: native row and byte limits remain authoritative and a
concurrent insert can make a previously fitting query refuse `limits`.

Published rootless JSON-home objects and independent directed relationships
support strings and exact scalar properties: integer, decimal, boolean,
timestamp and binary. Acyclic nested arrays/maps use required item Fields and
exact scalar leaves. Owned objects and composed
graphs, plus direct date and generic-decimal values. Ordinary Date queries support
projection and equality with literals, fields and `TextValue(kind="date", text="2000-02-29")`
parameters, preserving absent and null. Broader generic-decimal SQL queries remain unfinished. Record-valued cells and cyclic value definitions
remain unsupported. Exact numeric/time carriers preserve text semantics; do not
route them through floating point or lossy date conversions. Retained history
can reconstruct stored images after updates/deletion; archival/offload and
cleanup are unfinished.

Business-key lookup supports authored required string, integer, supported fixed-decimal,
boolean and binary keys. Query pages support the typed-key subset described below. Direct object/edge pages have explicit live continuations. Query results
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
remain strings. The shared
`umf-rfc3339-exact-instant/1.0.0` profile for timestamp equality. Required and
absent-allowed timestamp fields compare exact instants across offsets with
arbitrary fractional digits within the1MiB token limit, using literals, another
timestamp field, or `TextValue(kind="timestamp", text="2024-01-01T00:00:00.123456789Z")`.
Original timestamp text remains recoverable; `-00:00` retains unknown local-offset
knowledge while identifying a known instant. Binary/timestamp ordering, grouping
and temporal keys remain unsupported. The development compile/IR/backend interfaces
are `0.2.7`, with the unchanged SQL dialect `0.2.0`; released SDK22 remains0.2.5.
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
For a request-bearing group, Truss returns the token in `AppliedPending`,
before outer commit. An authorized observer sees `not_yet` until that commit;
the original token becomes included after commit without replaying the request.
A rolled-back token remains `not_yet`. The token alone does not establish a
confirmed commit or authorize publication. Committed replay remains available
for recovery of an unknown outcome.
`reached_in_transaction(tx, token, consumer_id='sink')` compares the registered
consumer's committed source checkpoint. The latter requires a fresh read-only
transaction with no assigned transaction ID, so pending ACKs cannot count as
committed progress. Valid behind receipts return false; invalid tokens,
unauthorized/missing consumers or unavailable evidence refuse.

ACKs are caller assertions about source delivery. They do not prove downstream
application, another database's commit or replica freshness. This runtime retains
source history indefinitely; it has no retention cleanup or archival protocol.


## Experimental and not covered by CI

Temporal values (`LocalTimestampValue` and related carriers), bulk job control, the `typed-sdk` and
`experimental-pg8000` extras, and the `truss-local-postgres` / `truss-migrate` commands are experimental.
Existing installations are never migrated or reset automatically. Historical release notes are in git
history; `CHANGELOG.md` summarizes them.
