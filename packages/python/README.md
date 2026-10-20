# Truss Python toolkit

Version 0.0.43 includes the embedder changes described in the
[E0/E1 execution plan](../../docs/helix/04-build/embedder-e0-e1-plan.md).
The [v0.0.43 notes](../../docs/helix/04-build/releases/v0.0.43.md) record the selected E1 qualification.
The historical release qualifications below describe their original bytes.

Historical release Truss `0.0.41` selects native `0.72-candidate` and Weft `0.4.48`.
Its qualification is local macOS ARM64 with PostgreSQL 18.6: 11 focused
cache/cohort controls and nine current-query/disclosure runtime checks pass.
The clean wheel contains the complete current runtime source inventory. The
unchanged native SQL and embedded owner assets retain the three real-schema
and 11 stress-case results from v0.0.40; those workloads were not repeated.
Other platforms receive packaging checks only. See the
[v0.0.42 qualification notes](../../docs/helix/04-build/releases/v0.0.42.md) and
[qualification summary](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.42/qualification.json).
The earlier [v0.0.40 evidence archive](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.40/qualification-evidence.tar.gz)
retains the original scoped workload results and incomplete broad discovery
receipt; no full-suite pass is claimed.

This version accepts only UMF `0.10.0` source documents and fresh current
installations. Earlier UMF source formats are unsupported, as are upgrades from an older Truss
installation. `upgrade_in_transaction` returns an explicit unsupported error
without issuing SQL; the CLI has no `--upgrade` option. No automatic migration,
reset or data rewrite is performed. Historical catalog revisions, receipts and
retained events created within a current installation remain supported.
Earlier release evidence retains its original scope and does not extend this
version's compatibility.
Python deployment uses embedded V8 and requires no Bun, Node or external
JavaScript process. This version includes owned graphs, explicit subtree reparenting, cascade
deletion, atomic owned imports, owned-object catalog evolution, compact
registration reports and batched native writes.

The v0.0.39 source passed both complete Linux x86_64/macOS ARM64 native jobs,
including the original 1,024-operation capacity controls and full
1,000-object/1,000-edge workload, with unchanged 10s SQL/30s operation limits.
Those results qualify v0.0.39 only; they do not establish v0.0.40 qualification.
[Historical v0.0.39 notes](../../docs/helix/04-build/releases/v0.0.39.md)
retain that release's scope. The current
[performance record](../../docs/helix/03-test/performance/README.md) identifies
0.0.40's installed payload and completed local workloads. Provisional latency
budgets and recorded performance triage signals do not establish p95 certification.

Current owned groups admit up to 1,024 operations per atomic group. Basic native tests cover
1,024 real creates, committed changed updates, original receipt replay and
complete ordered public readback, plus refusal at 1,025 and rollback on a
failure at operation 1,024. Other
byte/value limits and ordinary deadlines still apply.

Version 0.0.43 pins `weft-sql==0.4.48`, backend `0.4.41` / binding `0.5`,
and query ABI 1.1. The backend version identifies the runtime ABI separately
from the compiler package version. The historical v0.0.39 package used
`weft-sql==0.4.41` with the same backend/binding versions.
ABI 1.1 buffers complete source sets before caller predicates and scans at most
10,000 rows per selected Record or Relationship type; a small output limit does
not bypass that source bound. Complete-entity relationships have a separate
100-related-key limit. The million-object stress case reports its SQL list
outside the source cap; its declared ID/key read and write workload still runs.
The dense case retains its edge-source cap and exact scalar-list control; the
skewed case retains the 100-related-key cap and explicit bounded-read truncation.
Existing local release tests exercise the default public compiler with owned
descendants, the original Northwind Product model, decimal(12,2), and stable
UMF IDs for unnamed records and fields. These checks do not qualify the broader
protected engine.

Version 0.0.40 uses one source-only catalog preparation path; a mandatory
inspector transcript is no longer required. Loaded views reuse immutable schema
indexes in application memory for the exact source and catalog basis. Warm
eligible writes reuse compiled record schemas without another schema query or
legacy per-record value validation. Native admission still checks the current
registration identity, source basis, revision and authority.
Current APIs include explicit atomic owned imports, alternate-key backfill
and retained-value rebinding for existing owned objects. Ordinary Date queries
preserve canonical Gregorian `YYYY-MM-DD` tokens for years
0001–9999, including exact equality, optional values and query pages. Date ordering,
Date business keys, typed-engine Date outputs/parameters and other generic-decimal
SQL query domains remain unfinished.

The public-only owned example runs installation, registration, owned creation,
explicit subtree reparenting, caller rollback, read-only key/edge/traversal reads,
cascade deletion, retained history and committed receipt replay. With the
current package and local PG18 dependencies installed:

```sh
python packages/python/examples/owned_objects_workflow.py /tmp/truss-owned-demo
```

It uses the adjacent `notes-owned.umf.json`, validated as complete current
UMF0.10 source. The directory must be new or empty. Compiled queries have separate
native workflows using the matching published Weft wheel.

The Python reference assembly provides catalog registration, object and edge
mutations, business-key reads, Weft queries, imports, retained history, receipt
recovery, committed feeds and acknowledgements. It embeds into a caller-owned
synchronous psycopg connection. The caller begins and settles assembly transactions. The separate
`run_import_batches` function owns a fresh connection. Legacy inputs commit one
record per batch; explicit owned inputs commit the entire aggregate as one batch.
Objects precede edges across the complete input. It performs no
automatic retries. Results distinguish confirmed commits, rollbacks and unknown
commit outcomes. Repeating input uses current identity policy and does not
recover the original import report. Reports may be withheld when current
disclosure authority cannot be established.

## Current release scope

This release retains exact scalar values, required scalar-field/key backfill,
acyclic nested arrays/maps with required item Fields, owned graphs, imports,
history, receipts and feed reads. Cyclic definitions, descendant evolution and
record-valued properties remain unsupported. Source validation selects UMF
0.10.0; UUID, bits128 and 128-bit integer storage are explicitly refused.

Otherwise-supported standalone singular scalar Fields remain declarations until
a Record uses them. The authored document revision is distinct from its content
hash. Object reads distinguish rootless and owned objects with typed roots.
The Python distribution, native runtime and compiler versions are separate pins.
Use the exact release cohort listed above; no older installation is upgraded.

The `truss.access` typed-SDK integration remains experimental and requires its
matching UMF SDK 0.5.3 / host 0.1.0.dev5 cohort through the `typed-sdk` extra.
Install that optional host from the UMF release assets. A bounded cursor
stream that cannot prove exhaustion raises `QueryStreamRefused` after cleaning
up its portal and transaction. An exact row-limit boundary is not exhaustion.

The synchronous generated-action bridge is also experimental. A host composes
`TrussActionTransport` with one `SchemaBinding` per generated source digest,
an original-source observer that returns `None` only after byte-exact
acceptance, typed decoders, and native whole-action handlers
that use public Truss group operations. Truss does not interpret generated
action semantics or infer native key mappings: the host supplies receipt
validators tied to the accepted source and actual native group result. The
connection factory supplies an exclusive context-managed idle/autocommit
psycopg lease with a mandatory discard operation for unresolved owned settlement
or cleanup; its exit releases the connection only, while the transport owns and
explicitly acknowledges its READ COMMITTED transaction. The local operation
timeout checks admission, dispatch, settlement and release but cannot preempt
trusted synchronous host callbacks. Requests and staged JSON receipts are limited to
1 MiB, 100,000 values, and 64 levels. A newly applied native
group result remains pending until the outer commit is confirmed. Replays are
accepted only with the original native same-transaction or committed-receipt
evidence. An unconfirmed commit or failed post-commit lease release returns
`WRITE_OUTCOME_UNKNOWN` with the caller's idempotency key; the bridge never
retries. Reads, non-atomic batches and actions without a qualified whole-batch
handler return `UNSUPPORTED`. See the experimental public composition in
`truss.action_transport` and its focused native tests for the exact cohort.

## Install version 0.0.43

Use the matching Truss and Weft release artifacts below. Source builds require
the same version cohort; an older installation is not upgraded.

The experimental **current-policy query interface** is:
`assembly.query_current_in_transaction(tx, executor=..., sql=...,
document_ids=(...), parameters=...)`. It composes an ordinary caller's actual
Subject and module access, original UMF policy evaluation, original Weft query
preparation, private PostgreSQL staging and guarded `QueryRows` release.
The [basic workflow](tests/test_current_query_runtime_native.py) creates data
through the public API and queries an exact signed64 salary while returning its
masked String value. A complete public-API reference example includes installation,
ordinary-person catalog/data writes, Subject/source enrollment, activation,
transaction adoption and the masked query. From a source checkout with the
matching wheels installed:

```sh
python packages/python/examples/current_query_workflow.py /tmp/truss-policy-example
```

Expected output is `{"columns": ["salary"], "rows": [["[private]"]]}`. The adjacent model,
policy and static binding are the original reference fixture; they are not a
universal security configuration or a protected-write API.

Before opening protected callers, finish bootstrap data and Subject enrollment,
quiesce all other client sessions and prevent new connections, then call
`activate_current_query_protection_in_transaction(installer, tx,
subject_registration=subjects)` and commit. Activation checks that no other
client sessions remain. It revokes every ordinary legacy data routine grant;
only scoped catalog metadata and the verified own-session Subject facade remain.
Guarded queries require this committed activation. Cached legacy query bindings
do not retain access. Module configuration, feed enrollment and privileged bootstrap installers
refuse after activation until an explicit protection migration exists.
Installation upgrades are unsupported for this release.

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

This first local PostgreSQL18.6 profile uses exact original candidate Weft ABI2
and UMF child pins. Its native workflow tests pass locally on macOS ARM64;
the release qualification archive records the public reference-example run.
Linux x64 and other platforms, and newer result ABIs, remain unqualified.
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

### Unreleased opt-in tagged current disclosures

The separate `query_current_disclosure_in_transaction` candidate returns
`CurrentDisclosureRows`, preserving UMF V2 original, absent, withheld and
transformed cells in UTF-8 `batch_json`. `columns` contains SQL output aliases;
`field_indexes` maps those output positions to the batch's unique field columns,
including repeated projections. It does not convert these cells to `QueryRows`.

This separate experimental candidate requires the exact current presence-enabled
compiler and UMF producer identities. Earlier local-cohort evidence does not
qualify this candidate. Further SQL coverage requires corresponding compiler and
adapter integration.

For a fresh trusted installation, explicitly enroll
`prepare_current_disclosure_originals(opaque_sources_bytes)` using
`register_current_disclosure_sources_in_transaction(...,
disclosure_originals=...)`. Its source profile is distinct from ABI2, with a
`presence-designation` source and a version0.4 application-lineage request.
Existing registrations do not migrate implicitly. Both source installers reject
the other profile's originals; the ordinary current-query API rejects a
`CurrentDisclosureExecutor`, and the disclosure API rejects a
`CurrentQueryExecutor`.

After the same committed Subject enrollment and protection bootstrap described
above, use a dedicated fresh private transaction and
`CurrentDisclosureExecutor(worker, worker_tx, subject_registration)`, then call:

```python
result = assembly.query_current_disclosure_in_transaction(
    tx, executor=disclosure_executor,
    sql="SELECT r.salary FROM Resource r", document_ids=("domain",),
)
```

The original compiler parent stays held through native staging, exact transport
checking, inspection by the same live UMF producer, and closing caller/source
checks. The host settles both outer transactions. Caller byte limits include
public alias/index metadata and the V2 batch; private captures have separate
bounds. The transport's16MiB inspection capacity does not establish a16MiB
composed application payload: the owner decoder and compiler transport have
additional explicit bounds, documented with the evidence.

Earlier local disclosure evidence retains its original version scope and does
not qualify the current candidate or activate a complete security profile.

Use a fresh Python3.11+ environment on the locally qualified macOS ARM64
PostgreSQL18 profile. Prebuilt Weft wheels remove the Rust/Cargo build requirement:

```sh
python -m pip install --only-binary=:all: \
  --find-links https://github.com/DocumentDrivenDX/truss/releases/expanded_assets/v0.0.43 \
  --find-links https://github.com/DocumentDrivenDX/weft/releases/expanded_assets/v0.4.48 \
  --find-links https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2 \
  'truss-toolkit[local,native,query]==0.0.43'
```

Python deployment requires no Bun, Node, or external JavaScript process. The
wheel uses `mini-racer==0.14.1` to execute the preserved UMF producer inside V8.
Original producer manifests retain their build-time Bun pins; these are provenance,
not deployment requirements. Ordinary object keys are derived in PostgreSQL
for admitted current catalogs. Create/update, imports, preconditions, backfills
and lookups require no client encoder or per-key receipt. Weft remains optional
through `query` and is not a key-encoding dependency.
Each release publishes package checksums and source/runtime/backend pins. The
current evidence qualifies the exact installed wheel on local macOS ARM64 only;
it does not claim Linux x86_64 or other native-platform qualification.

## Run a real workflow

Check out the v0.0.43 tag to obtain the examples, then run with a new directory:

```sh
git clone --branch v0.0.43 --depth 1 https://github.com/DocumentDrivenDX/truss.git
cd truss
python packages/python/examples/adopter_workflow.py /tmp/truss-adopter-demo
```

The [example](examples/adopter_workflow.py) installs the runtime, registers the
[original UMF document](examples/notes.umf.json), configures ordinary-person access,
commits Notes and a link, recovers the original request, reads by key, compiles a
relationship query, rolls back a dry-run, imports a Note and durably saves feed
pages before source ACKs. Administrator SQL sets up roles only.

The [historical public Python preview labeled 0.10](../../docs/helix/04-build/corpus/public-python/0.10/README.md)
retains22 basic and10 exact-scalar observations for UMF0.7 and runtime0.38.
It is incompatible with the current UMF0.10-only v0.0.40 candidate; earlier
previews retain their historical pins and none claims independent interchange.

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

## Fresh installation and access

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

The current candidate has no installation upgrade route. Install only into a
fresh database without a `truss` schema. `upgrade_in_transaction(tx)` returns
`Error` with `catalog_code='unsupported_profile'` and performs no database work.
An existing installation with different release pins refuses current operations;
installing this wheel does not migrate or repair it. Keep the older package and
its database together if that deployment must remain in service.

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

Version 0.0.40 includes `prepare_group_in_transaction(tx,
records=((document_id, module_id, record_id),), relationships=())`, returning the
catalog revision, group context and requested references together. A host may
cache this planning metadata for the same installation, source epoch, principal
and catalog basis. `catalog_revision_in_transaction(tx, document_id=...)` provides
a small revision probe. Build groups with the cached `prepared.context.input(...)`
and the returned definition pins; the write still checks its current basis and
authority. A stale write refuses rather than silently retrying a mutation. This
API is exercised by the local release tests and public workload runs. It was not
available in v0.0.39.

## Catalog meaning and evolution

A `CatalogDocument(document_id, document_revision, content)` carries exact
original UTF-8 document bytes. Preparation runs the bundled UMF owner producer
inside embedded V8; registration requires no external JavaScript runtime. Ordinary key
operations derive keys in PostgreSQL, while catalog admission uses the broader
UMF producer.
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
This feature shipped in v0.0.39 with basic PostgreSQL18.6 workflow coverage.
Managed-database and broader performance qualification remain separate.

## Values, reads and query limits

`read_profile='complete-entity'` adds native facts and relationship-key columns
to a supported single-source `alias.*` projection. An explicit `RELATED_KEYS`
output whose alias collides with an added relationship column is refused with
`WFT-OUTPUT-NAME`; the compiler does not overwrite or rename either output.
Choose a distinct explicit alias, for example
`RELATED_KEYS(a."A-B",100) AS "_A-B"`, when also selecting `a.*`. Quote aliases
whose spelling/case must be preserved. The complete relationship column is
bounded at 100 keys and refuses rather than silently truncating; an explicit
bounded related-key projection has its own reported truncation semantics.

Published rootless JSON-home objects and independent directed relationships
support strings and exact scalar properties: integer, decimal, boolean,
timestamp and binary. Acyclic nested arrays/maps use required item Fields and
exact scalar leaves. Version0.0.39 adds owned objects and composed
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
remain strings. SDK0.0.23 additionally selects the shared
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
For a request-bearing group, the v0.0.40 candidate returns the token in `AppliedPending`,
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
