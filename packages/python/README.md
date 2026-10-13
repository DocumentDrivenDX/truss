# Truss Python toolkit

The Python reference assembly provides catalog registration, object and edge
mutations, business-key reads, Weft queries, imports, retained history, receipt
recovery, committed feeds and acknowledgements. It embeds into a caller-owned
synchronous psycopg connection. The caller begins and settles every transaction.

This is an experimental implementation: Python distribution `truss-toolkit==0.0.5`,
native runtime `0.40-candidate`, layout `0.16`
candidate, UMF core `0.7.0` and `0.8.0`, and Weft runtime backend `0.4.10`. The tested local
stack is DocumentDrivenDX `pgserver-pg18==18.6.1`, PostgreSQL 18.6,
psycopg/psycopg-binary 3.3.6 and libpq 18.6. Aurora, Lakebase and other driver or
server versions are not qualified. The broader protected-engine security
activation remains unfinished; this runtime does enforce its own installed
ordinary-person/module boundaries.

The current release is [v0.0.5](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.5).
The Python distribution version is distinct from native runtime/layout versions;
future distributed changes receive a new package version.

## Install the release

Use a fresh Python3.11+ environment on the declared Linuxx86_64/macOSarm64
PG18 profile. Prebuilt Weft wheels remove the Rust/Cargo build requirement:

```sh
python -m pip install --only-binary=:all: \
  --find-links https://github.com/DocumentDrivenDX/truss/releases/expanded_assets/v0.0.5 \
  --find-links https://github.com/DocumentDrivenDX/weft/releases/expanded_assets/v0.4.7 \
  --find-links https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2 \
  'truss-toolkit[local,native,query]==0.0.5'
```

Bun1.4.2 is still required for UMF preparation and key production. Each release
publishes package checksums and source/runtime/backend pins. The Truss release
workflow exercises the exact uploaded wheel with published Weft0.4.7 and verified
PG18 dependency wheels on both declared native platforms.

## Run a real workflow

Check out the v0.0.5 tag to obtain the examples, then run with a new directory:

```sh
git clone --branch v0.0.5 --depth 1 https://github.com/DocumentDrivenDX/truss.git
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
0.23 through 0.39 to 0.40 for published v0.0.5. The trusted administrator must quiesce consumers and
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
through Bun; registration and key production still require Bun in the app image.
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
adding endpoints. Unchanged IDs/pins remain stable. Key backfill, retirement,
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
batch failed. Engine-owned transaction batches are not implemented.

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
absence and explicit null. Timestamp/binary filters, ordering, grouping, keys and
parameters remain unsupported. The selected compile/IR/backend interfaces are
`0.2.4`, with the unchanged SQL dialect `0.2.0`.
Successful native `QueryRows` and `QueryPage` results carry `as_of: QueryReadPosition`. Its opaque `value` identifies a conservative committed lower bound captured immediately before the data query; `at` is the database capture time as a timezone-aware UTC `datetime`. The following READ COMMITTED statement can include newer commits. `caller_xid_assigned` reports only whether the caller already had a transaction ID; it does not prove writes or commitment. Constructors retain an optional default for compatibility, while this provider fills the position on every successful result, including empty rows.

Read-position values use their own namespace and are not receipt tokens. Do not pass them to `reached`, infer ordering from their strings or timestamps, or treat them as exact snapshots. An adapter may publish this position only with the stated lower-bound semantics. Current authority/context checks must pass before the result and position are returned.

Compiled queries require complete read authority for all modules in each selected
original document, including modules the SQL does not name.

`query_page_in_transaction(tx, sql=sql, document_ids=(document_id,), limit=100, cursor=None)` returns `QueryPage(columns, rows, catalog_revision, next_cursor)`. Pass `next_cursor` back to continue; `None` means the last page. The same call is available through the compiled-execution capability. Weft resolves the authored primary key, adds key ordering and continuation, and supplies hidden key outputs that Truss removes. The original SQL need not project the key or contain `ORDER BY`.

This public page call initially supports one nonaggregated source with a complete required-string primary key. Caller `ORDER BY`/`LIMIT`, joins and relationship predicates refuse. Cursors bind the original SQL, exact parameters, document selection, connecting person, catalog/installation/release context, limit and resource budgets. Keep those inputs unchanged for continuation. Each page rechecks current authority in the caller's transaction; pages are live, so concurrent changes can affect traversal.

`entity-page` and `related-entity-page` query profiles require complete authored
keys in `ORDER BY`, an explicit limit and caller-supplied continuation predicates.
`count-summary` supports ungrouped counts and grouped counts on required, non-nullable string/boolean fields. Grouped summaries require the complete grouping order and an explicit `LIMIT`. Query continuation is live, not a
stable snapshot or exactly-once traversal. Multi-hop relationships, non-string
page keys and optional/numeric grouped keys remain unsupported. Bounded sources are checked
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
The full original consumer corpus, genuinely independent native interchange,
stable layout, broader value/query support and managed-service qualification
remain open. Experimental pg8000 and older private profiles are historical paths.

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

### Exact numeric facets (v0.0.5)

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

### Typed business keys (v0.0.5)

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
Timestamp/float keys are refused. Weft pagination and relationship-key projections
still require string keys. This tranche was added after v0.0.2.

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
