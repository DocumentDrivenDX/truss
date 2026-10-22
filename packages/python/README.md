# Truss Python toolkit

Version **0.0.49** adds explicit managed platform grants to the separate
[v0.0.48 HF baseline](../../docs/helix/04-build/releases/v0.0.48.md). Consult the
[v0.0.49 release notes](../../docs/helix/04-build/releases/v0.0.49.md) and linked
qualification evidence for the published release status. The installation and
example commands below require checksum-verified public v0.0.49 assets and their
matching tag; do not substitute v0.0.48 when managed-grants support is required.

<a id="runtime-migrations--v0048"></a>

## Runtime migrations — v0.0.49

This guide retains its historical v0.0.48 link anchor. The v0.0.49 migration
route includes admission of the actual public v0.0.48 wheel; consult the v0.0.49
release notes and linked qualification evidence for the published route status.
The existing admitted sources and migration procedure below remain the baseline.

Truss supports the latest application runtime only. Previous databases move
forward through `RuntimeMigrations` or the explicit `truss-migrate` command;
older application runtimes are not maintained as compatibility modes.
Admitted databases do not expire by release age. The latest tool follows the
complete declared route in one transaction and appends one final receipt; it
does not launch intermediate application releases. Existing receipts retain
their original bytes and remain observable through current tooling.

The offline, transactional routes accept the exact UMF 0.10 installation
from v0.0.44 and the shared installed tuple from v0.0.45/v0.0.46, on PostgreSQL
18.6, plus v0.0.47 native0.73. The target is native `0.74-candidate`; exact manifest and installed definitions,
privileges and preparation configuration decide admission. Matching release/layout
labels alone do not. Pre-0.10 and protected-query installations are excluded.
Unknown or modified sources refuse with their data intact. Current authored-name
requirements apply to new registrations; already accepted v0.0.44 unnamed Records
and Fields retain their original source and are exercised through latest reads/writes.

Quiesce application and administrative writers and take a backup before applying.
For logical backups on the qualified PG18.6 profile, also save
`truss-migrate backup-metadata --registry ./truss-recovery.sqlite` alongside the
dump. PG18.6 dump/restore omits private table-row-type ACLs in this profile.
During an explicit offline restore, apply that original companion's
`rowTypePrivilegeRestoreSql` before verification, migration or application access.
Migration refuses privilege drift and never repairs it automatically. The two
observed deparse spelling changes are qualified by identical pinned native parse
trees. Inventory observation uses UTC and preserves the observer's timezone.
The two exact journal-horizon initialization profiles created by the original
installer under UTC and America/New_York are qualified separately; migration
preserves the source bounds without conversion. Other differences refuse.
The migration tool owns a separate idle administrative connection and its entire
transaction. Application startup and `--install` never upgrade or reset a database.
Set `TRUSS_DATABASE_URI` to the administrative connection URI, then use a durable,
host-owned recovery registry and retain the returned reference across restarts:

```sh
truss-migrate status --registry ./truss-recovery.sqlite
truss-migrate prepare --registry ./truss-recovery.sqlite
truss-migrate apply --registry ./truss-recovery.sqlite --reference RETURNED_REFERENCE
truss-migrate reconcile --registry ./truss-recovery.sqlite --reference RETURNED_REFERENCE
truss-migrate verify --registry ./truss-recovery.sqlite
```

`migrated` and `already_applied` carry the original receipt reference and fresh verification.
Use `truss-migrate receipt --registry ./truss-recovery.sqlite --reference RETURNED_REFERENCE`
to export the complete immutable original request, recipe, native inventories,
ordered step/privilege evidence and preservation bytes. `preparedAt` is receipt
creation time, not a commit timestamp.
`rolled_back` confirms the original rollback; a new attempt is explicit.
`commit_unknown` and `recovery_required` retain the same reference for reconciliation.
`committed_unverified` preserves a confirmed commit while verification or original
resource cleanup remains unresolved. Do not repeat steps to resolve uncertainty.
A later release retains immutable recipes and historical manifest evidence, so
migration and receipt lookup stay in the latest tooling. Old unsubmitted requests
cannot execute an older target. Applied recipes are immutable; repairs move forward.

The Python entry point is `from truss.migrations import RuntimeMigrations` with
`RuntimeMigrations(connection_factory, host_recovery_registry)`. The factory must
return a newly owned, idle, autocommit psycopg connection. The host registry uses
CONTRACT-007's installed target and immutable register/append/inspect operations;
`truss.recovery_registry.HostRecoveryRegistry(path)` is the local SQLite-backed,
restart-durable implementation. `upgrade_in_transaction` refuses caller-owned
transaction upgrades and directs callers to this separate administrative boundary.

Default migration limits are 256 MiB per preservation pass, 10s per SQL
statement and a 30s operation deadline. Resource selection is retained in the
original request. Larger finite scan/deadline budgets are explicit Python constructor
parameters, with separate workload qualification; they do not change support to an old runtime. A limit refusal rolls back; no scale claim beyond the qualification
fixtures follows. Preserve registry and database backups together. A package downgrade
is not database rollback. The tested backup recovery is logical dump/restore into a
new database identity before target writes, followed by migration to latest;
other restore/incarnation procedures need their own qualification.

The release-blocking [migration gate](../../scripts/qualify-runtime-migrations.py)
runs every admitted source against the installed latest wheel and refuses removed
paths or changed published recipes. Exact source-bound evidence and delivery status are recorded in the
[execution plan](../../docs/helix/04-build/runtime-migration-restoration-plan.md).
Published release assets include the Linux migration receipt, original native
evidence archive, dependency pins and checksums; the tag workflow requires all
selected installed-runtime gates before publication.


Version 0.0.46 adds an explicit local PostgreSQL 18.6 launcher using private
per-instance data and Unix-socket directories. It installs or confirms the
current Truss installation, retains data on stop, and keeps shell `PG*`
settings from redirecting the owned server or installation connection. It
does not provide an HTTP, MCP or TrussRPC service. Local macOS 27 ARM64 evidence
uses Python 3.11.17 and records eight focused lifecycle/isolation/CLI tests plus
a clean `uvx` installation and same-identity status confirmation. See the
[0.0.46 release notes](../../docs/helix/04-build/releases/v0.0.46.md),
[local validation record](../../docs/helix/04-build/evidence/isolated-local-install-20261021/validation.json),
[Python 3.11 receipt](../../docs/helix/04-build/evidence/isolated-local-install-20261021/python311/receipt.json) and
[focused test log](../../docs/helix/04-build/evidence/isolated-local-install-20261021/python311/focused-native-tests.log).

Historical version 0.0.45 added verified runtime and exact compiler caches, conditional query
bindings, a combined catalog/source/query API and set-based independent imports.
Registration now requires Record/Field names, with element-specific diagnostics;
UMF optional-name semantics remain unchanged.
See the [0.0.45 notes](../../docs/helix/04-build/releases/v0.0.45.md).

Version 0.0.44 added batched imports, conditional catalog reads, document revision
checks, condition preview, lifecycle outcomes and scoped group/load audit.
The [v0.0.44 notes](../../docs/helix/04-build/releases/v0.0.44.md) describe compatibility and qualification;
the [delivery plan](../../docs/helix/04-build/embedder-e2-e8-plan.md) records the accepted request dispositions.
The historical release qualifications below describe their original bytes.

Historical release Truss `0.0.41` selects native `0.72-candidate` and Weft `0.4.48`.
Its qualification is local macOS ARM64 with PostgreSQL 18.6: 11 focused
cache/cohort controls and nine current-query/disclosure runtime checks pass.
The clean wheel contains its complete release runtime source inventory. The
unchanged native SQL and embedded owner assets retain the three real-schema
and 11 stress-case results from v0.0.40; those workloads were not repeated.
Other platforms receive packaging checks only. See the
[v0.0.41 qualification notes](../../docs/helix/04-build/releases/v0.0.41.md) and
[qualification summary](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.41/qualification.json).
The earlier [v0.0.40 evidence archive](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.40/qualification-evidence.tar.gz)
retains the original scoped workload results and incomplete broad discovery
receipt; no full-suite pass is claimed.

Historical [v0.0.42](../../docs/helix/04-build/releases/v0.0.42.md) adds the registered synchronous action host and strict group-response decoding. Its separate [qualification receipt](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.42/qualification.json) records 31 component controls and six focused native cases, including one registered create-action fixture under ordinary ACLs. Those cases do not rerun the v0.0.41 query/disclosure cohort above.

The current candidate accepts UMF `0.10.0` source and the explicitly qualified
forward migration routes above. Earlier UMF source formats are unsupported.
`upgrade_in_transaction` refuses caller-owned transaction upgrades; use the
separate administrative tool. Startup never migrates or resets a database.
Historical catalog revisions, receipts and
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

Version 0.0.45 pins `weft-sql==0.4.49`, backend `0.4.41` / binding `0.5`,
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
Use the exact current release cohort. Existing installations require a qualified forward migration before application use.

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

## Embedder APIs

The additive APIs below are qualified as described in the
[E2–E8 plan](../../docs/helix/04-build/embedder-e2-e8-plan.md).
They retain the legacy import and transaction contracts.

`build_import_records_in_transaction(tx, drafts)` builds an entire tuple of
`ObjectImportDraft` / `EdgeImportDraft` values from accepted definitions in one
native call. Its `BuiltImportRecords` result contains `context` and `records`:

```python
built = assembly.build_import_records_in_transaction(tx, drafts).value
input = built.context.input(
    built.records, load_id="seed-1", asserted_origin=MapValue(entries=()),
    chunk_size=128,
)
result = assembly.import_batched_in_transaction(tx, input, documents=documents)
# result.result is the existing tagged ImportExecutionResult.
# On an admitted empty input, result.empty_load_settlement is explicit.
```

The selected batched profile accepts at most 1,024 original records, an 8-MiB
input envelope and 1-MiB individual payloads. Chunks contain 1–128 records.
Objects precede edges across the complete input, with results attributed to
original indices. Each eligible record has its own native subtransaction;
created, skipped and rejected records can share a chunk. Existing identities
skip before payload interpretation, after byte/hash admission. Source `at`
strings on this profile must be exact RFC3339 instants. Legacy source strings
and the legacy 128-record/per-record-settlement profile remain unchanged.

Caller-owned imports remain pending. `run_import_batches` selects engine-owned
chunk commits only for `BatchedImportInput`; it retains one-record commits for
legacy inputs and atomic settlement for `OwnedImportInput`. The new route
returns `BatchedImportExecutionResult`, wrapping the existing tagged result.
`EmptyLoadDisposition` records pending, committed, rolled-back, commit-unknown
or transaction-unresolved settlement without inventing a record index. A
report can be withheld when current complete disclosure authority is unavailable.
No unresolved commit is retried. Native retained work is bounded at 4,096
records/256 MiB per transaction, with a separate nonrewinding submitted-work
budget per adopted host handle; these are not a global CPU/allocation quota.

On the measured local matching-timeout fixture, a builder uses three client
statements; a single-chunk execution plus final report authorization uses six.
Each additional chunk adds three. Connection/adoption and engine settlement are
separate costs. This describes client statements, not set-based native DML or
a universal latency guarantee.

`reader_catalog_if_changed_in_transaction(tx, validator=...)` returns a typed
`ReaderCatalogSnapshot(catalog, validator)` or `ReaderCatalogUnchanged(validator)`.
Retain the snapshot and validator together. Each call rechecks current authority;
the validator grants no access. Module entries expose `sourceCatalogRevision`.
`registrar_status_in_transaction` is an advisory typed capability probe.
Acceptance supports `expected_revision` and document-scoped
`CatalogDocumentExpectation` values in `expected_documents`; zero requires that
source document to be absent. Exact authorized request replay precedes current
expectation checks. A contained `CatalogCASConflict` is distinct from a real
serialization/deadlock retry. Known UMF core 0.10.0 / `umf.ddd` 0.1.0 paired
optional Field/member additions retain original validation and unknown content;
other extension changes keep their explicit compatibility refusal.

`preview_group_conditions_in_transaction` evaluates `GroupConditionPreviewInput`
on one data snapshot and returns `PreviewObserved` or `PreviewRefused`. Its
observation basis is advisory and cannot be used as a mutation receipt. It does
not reserve keys, create attempts or journal effects. Mutations still re-evaluate
conditions under their own locks. Restrictive delete returns the typed dependency
refusal; explicitly selected owned cascade retains its separate contract.

`person_runtime_status_in_transaction` gives minimal installation compatibility
and empty/accepted catalog state to enrolled people, including audit-only roles.
Role-name recovery is a separate administrator-only API. Installation exclusion
returns a typed busy refusal. Module grant batches remain atomic; invalid batches
return original indexed `ModuleAccessBatchRefused` diagnostics before changes.
Existing installations are not automatically migrated or reset.

Audit access is separately configured by an installation administrator using
`ModuleAuditGrant`; writers cannot self-grant. The metadata-only load/group page
APIs require current audit membership across every retained owner in the complete
selected group or load. Ordinary data-read grants alone do not authorize audit.
Pages include native identities, operation kinds, actor/action and explicit
observed times, with committed-visibility evidence; observation time and XID are
not claimed to be commit time/order. Raw origin, key/property/source values and
input payloads are excluded. Discovery filters and typed continuation cursors
retain a fixed committed frontier. Deleted and unchanged operations remain
represented. Literal empty loads are retained but have no module scope and require
the separate registrar disclosure path.

## Install version 0.0.49

The commands below select v0.0.49 and its matching dependencies. Use them only
with the publicly published v0.0.49 assets after verifying their published
checksums. The v0.0.49 release notes and linked qualification evidence are the
authority for the exact release status and supported cohort. Source builds must
select a matching source and dependency cohort; existing installations require
explicit migration.

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
Protected-profile installation upgrades remain unsupported for this candidate.

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
  --find-links https://github.com/DocumentDrivenDX/truss/releases/expanded_assets/v0.0.49 \
  --find-links https://github.com/DocumentDrivenDX/weft/releases/expanded_assets/v0.4.51 \
  --find-links https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2 \
  'truss-toolkit[local,native,query]==0.0.49'
```

Python deployment requires no Bun, Node, or external JavaScript process. The
wheel uses `mini-racer==0.14.1` to execute the preserved UMF producer inside V8.
Original producer manifests retain their build-time Bun pins; these are provenance,
not deployment requirements. Ordinary object keys are derived in PostgreSQL
for admitted current catalogs. Create/update, imports, preconditions, backfills
and lookups require no client encoder or per-key receipt. Weft remains optional
through `query` and is not a key-encoding dependency.
Each release publishes package checksums and source/runtime/backend pins. The
release receipts distinguish local macOS ARM64 native checks from hosted Linux
x86_64 qualification. Other platforms are outside the selected release gates.

## Run a real workflow

After the v0.0.49 tag and assets are public, verify their published checksums,
then obtain the matching examples and run with a new directory:

```sh
git clone --branch v0.0.49 --depth 1 https://github.com/DocumentDrivenDX/truss.git
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

## Run local PostgreSQL 18.6

With `uv` installed, the following command selects v0.0.49 in an isolated Python
3.11 tool environment. Run it only after the v0.0.49 wheel and constraints asset
are publicly available and their published checksums have been verified. Consult
the v0.0.49 release notes and linked qualification evidence for release status
and supported platforms:

```sh
uvx --no-config --isolated --python 3.11 \
  --constraints https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.49/isolated-runtime-constraints.txt \
  --find-links https://github.com/DocumentDrivenDX/truss/releases/expanded_assets/v0.0.49 \
  --find-links https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2 \
  --from 'truss-toolkit[local,native]==0.0.49' \
  truss-local-postgres \
  --data-dir "$HOME/.local/share/truss/beads" \
  --install
```

The first run may download Python and package wheels. The launcher creates a
private PostgreSQL cluster and Truss schema/routines using Unix sockets only;
it needs no system PostgreSQL, administrator access, TCP listener or port
configuration. It runs in the foreground. Ctrl-C stops the server and retains
data; repeat with the same directory to restart. Add `--probe` to install or
confirm Truss and stop while retaining data. This is a local database runtime,
not an HTTP, MCP or TrussRPC application service. Tools still embed the Python
library, connect with an ordinary identity and register UMF documents. Public
business-role and module-access configuration remains a separate step.

```sh
./scripts/truss-local --data-dir "$HOME/.local/share/truss/beads" --install
```

For source development, `./scripts/truss-local` runs the checkout with its local
constraints and PostgreSQL wheel source. Use a different data directory for each
independent tool or instance.

The Unix-only local runtime leases its cluster directory, makes it private
(`0700`), and uses a distinct short private socket directory beneath
`/private/tmp/truss-pg18-<uid>` on macOS or `/tmp/truss-pg18-<uid>` on Linux.
The socket directory and socket are private (`0700`); every instance uses the
same socket number5432 without opening a TCP listener. A long data path therefore
does not require port discovery or shared sockets. The launcher reports its
socket directory and exact connection URI. Shell PostgreSQL settings cannot
redirect the owned server or installation connection.

Stop the foreground launcher with SIGINT/SIGTERM; cluster data is retained.
Repeat the command with the same directory to confirm the current installation
and retain its identity. Socket directories contain transient runtime state and
remain separate from durable cluster data. Local socket access trusts the owning
OS user; this is installation isolation, not a security sandbox between processes
running as that user. A stale postmaster marker or incompatible installation
requires explicit recovery; startup never resets or upgrades it.

Add `--probe` to install, confirm committed status and stop while retaining data.
The launcher installs only when public status reports no Truss namespace. On a
current retained installation it confirms status and preserves the installation
ID. Unsupported or corrupt installations refuse; this option never upgrades or
repairs them. The JSON output follows commit and a fresh status observation.
Fresh owner/registrar role names come from the installation result; save them
for access setup. A restart reports confirmed status without inventing those
names. Ordinary-person registration and module access still require the role
configuration described below. Without `--install`, the launcher only starts
PostgreSQL. Confirmed installation status does not by itself establish full
security readiness; consult the qualification evidence for the selected release.

### Managed platform grants — v0.0.49

Managed-grantee support is part of the v0.0.49 interface; v0.0.48 does not
include it. For a released deployment, use the checksum-verified v0.0.49 assets
and consult that release's notes and qualification evidence for its status and
supported cohort. From a matching source checkout, an explicit fresh local
install can pass one or more exact PostgreSQL role names:

```sh
./scripts/truss-local \
  --data-dir "$HOME/.local/share/truss/beads-managed" \
  --install \
  --tolerated-grantee databricks_service \
  --tolerated-grantee operator_reader
```

The option records selected native role identities and existing ACL observations;
it does not issue grants. Named roles must already exist; a missing role returns
`invalid_roles`. Names are exact and patterns are unsupported. The flag
is valid only for fresh installation. Later status and migration checks use the
stored policy. The embedding API uses
`install_in_transaction(tx, tolerated_grantees=("databricks_service", ...))`.
An `InstallRefused` with `code="third_party_grant"` carries bounded
`role_name`, `object_class` and `phase` fields only after the host confirms
operation rollback; map those fields directly in an Arras adapter and preserve
outer transaction/transport failures. The local CLI writes a safe refusal JSON
object and exits with status 1; other transaction/transport failures retain their
original failure path.

The following records are historical pre-integration candidate evidence. They
describe only the exact candidate identified by each receipt and do not establish
the status of the released v0.0.49 artifacts. The earlier local candidate wheel
SHA-256 is
`7a41a223033c1af0da4a2df2d377c672fcd3b3be1fcfc5b5bf8232d009725ed4`,
with native manifest
`35fd797b5cf48dd888c68e53b9e599df20cffe00f8f3d33e1563820ea808d59f`.
[Selected installed regression](../../docs/helix/04-build/evidence/design-audit/managed-grants-20261022/attempt-4/selected-components/qualification.json)
passes 19 modules/116 tests with zero skips.
[Other final local gates](../../docs/helix/04-build/evidence/design-audit/managed-grants-20261022/attempt-5/qualification.json)
pass the 61-case HF corpus, 9 strict protected regressions, all 80 supported
migration controls and the original 1,000-object/1,000-edge public workload.
[Managed lifecycle evidence](../../docs/helix/04-build/evidence/design-audit/managed-grants-20261022/supplemental/final-3/receipt.json)
qualifies supported evolution, contained unsupported-retirement refusal and later
selected ACL changes without rewriting initial evidence.

Those receipts qualify their exact earlier candidate, before integration of
the newer HF62/compiler cohort and v0.0.48 migration source. They are retained as
historical evidence; consult the published v0.0.49 release notes and linked
receipts for the final wheel/archive hashes and release qualification. None of
these records establishes Lakebase support. The retained legacy all-discovery
diagnostic remains incomplete and unqualified outside the mandatory supported
campaign in [the Linux release workflow](../../.github/workflows/release.yml).
Consult the published release evidence for the status and scope of that campaign
and public-artifact verification.
Arras adoption must bind the exact qualified Truss wheel and native target
manifest together with its UMF/Weft dependency pins, use the qualified
PostgreSQL 18.6 / psycopg 3.3.6 local profile for local evidence, and separately
retain the actual Lakebase TLS, transaction and consumer-workflow receipt.

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

Fresh installation requires a database without a `truss` schema. Existing
installations use the explicit qualified migration route above. Installing a wheel
does not migrate a database. Latest application operations refuse the old tuple
until migration completes; old application runtimes refuse the upgraded tuple.

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
This feature shipped in v0.0.39 with basic PostgreSQL18.6 workflow coverage.
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

For the pinned Weft0.4.49 Truss backend0.4.41 and query ABI1.1,
`maximum_scan_rows` is a **source population bound**, capped at10,000. It applies
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

## Arras follow-up cohort — v0.0.48

This cohort pins Weft0.4.51, compile/IR0.2.8, backend43/44, interface0.2.9
and Truss query ABI1.2. Native-indexed exact string/boolean equality and eligible
single required string key pages can select over populations above10,000 rows.
Complete candidate/byte limits still apply before residual filters and LIMIT;
numeric, temporal, composite and larger-key routes retain the bounded fallback.
A cursor retains its statement snapshot while current person/scope checks stay
live. Compiler descriptors accompany empty/null results, pages and streams.
`QueryEntityProjection(facts=(...), relationships=False)` explicitly selects
ordered facts and relationship expansion; continuation is bound to that choice.

The selected compiler retains opaque `arras.view` Record/Field metadata when the
same original UMF document declares vocabulary version `0.1.0`. Original bytes and
pins, including unselected unknown content, remain intact. Malformed envelopes or
unsupported selected versions/semantics refuse without SQL. This preserves
presentation metadata; it does not interpret Arras view terms or qualify its parser.

`freeze_group_request` freezes original complete inputs/documents before state
resolution. `recover_group_request_in_transaction` observes the retained request
without executing on a missing receipt or reconstructing it from current rows.
It preserves full-input conflict and current retained-owner checks. A successful
group exposes its existing stable attempt ID; no cross-person replay namespace
is implied. Ordinary runtime receipts are retained indefinitely.

`complete_in_transaction(tx)` checks Truss's deferred constraints under host-owned
rollback containment. `dry_run_in_transaction(tx, input, documents=...)` executes
the ordinary request-free group, forces those completion checks, and returns a
`GroupValidationObserved` only after confirmed rollback. Its basis is an
observation, with original input/document digests, native snapshot, source epoch
and catalog revision. It issues no receipt/committed position; sequences may
advance. Neither method settles the caller transaction or forces unrelated host
constraints. Native errors and uncertain cleanup retain their execution outcome.

Audit discovery accepts either a qualified document/module pair or neither.
Unqualified discovery omits whole groups/loads without complete current audit
authority. Mutation filters may explicitly request `includeData=True` for
retained operation key/version projections, requiring separate complete data
readership. `entityKey` also accepts the named reference shape
`{documentId, moduleId, recordId, keyId, values}`; native resolution owns its
actual definition pin and key number. Key filtering requires data readership.
Whole mutation pages admit up to4,096 events within the independent byte bound.
New relationship-only imports retain their declaration/endpoint owner union.
Older incomplete audit headers remain immutable and unavailable through a known
reference; they cannot be discovered through a scope that was never retained.
No historical backfill, commit timestamp or total commit order is invented.

The release's independent conformance archive includes original asserted test
producers, exact profile pins and `scripts/run-hf-conformance.py`. Unzip it outside
the checkout and run the installed final cohort with `--installed-package`.
The runner rejects skips and checks the loaded native compiler hash/source against
the exact corpus and installed Truss cohort. The separate migration gate
covers every admitted source, real multi-edge routes and prior publication.
