---
ddx:
  id: truss.typed-sdk-adoption
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
---

# Typed SDK original engine read adoption

**Version:** `weft.engine-read/0.1` and `umf.engine-catalog/0.1`.
**Status:** local implementation candidate; RC module ACL scope.

## Purpose and scope

Expose source-bound generated SDK reads through the original Truss public
catalog/transaction/query path. `truss.access.TrussTarget` takes an explicit
host-owned operation context; it opens no connection, interprets no storage,
lowers no native SQL and invents no table/Key/actor/receipt identity.

This initial path qualifies ordinary RC module-access reads only. It does not
route around protected current-query activation, mint action permits, issue bulk
manifests, or qualify protected security/temporal/managed semantics. A protected
installation must continue to refuse legacy read access. Separate original
current-policy/action source and native release gates remain mandatory.

## Original context capture and execution

`query_catalog_sources_in_transaction` obtains the complete real
`truss.query_binding` bundle, compiles the original request through the selected
Weft Truss compiler and executes native `truss.query_scope` admission before
returning inert original request JSON. The bytes grant no runtime permission.

An engine catalog preserves the complete model/module/SQL/backend/binding
request and original Weft artifact. Runtime `query_in_transaction` with
`engine_program` reacquires the actual native binding and invokes Weft's complete
original-program comparison before executing native SQL. Only parameter values
may change; source/model/binding/SQL/inventory/backend drift refuses. The returned
current artifact must equal the exact artifact about to execute. All original
Truss native scope, integrity, deadline, descriptor and final checks still run.
No field is removed from an original context to obtain equality.

The explicit local development compiler selections retain the existing ordinary
compiler profile. Engine catalog operations additionally select the new custody
API in the exact tested development Weft cohorts. Evidence must identify the
whole wheel/module/source hash; a development version alone is not a broad
qualification claim.

## Candidate constructor identity

The constructor requires an original `QueryCatalogSources` capture through
`catalog_sources`, or original `EngineRead` values in `catalog_entries`. Supplying
both requires one identical complete target. Each original binding text must
match its SHA-256 and the configured binding. Construction without either source,
with mixed targets or inconsistent binding bytes refuses before native dispatch.
This is a deliberate candidate constructor change; no backend version is guessed.

Identity/backend/profile come from the complete retained original target. Every
read compares its whole target before native dispatch. This metadata grants no
authority: native `query_binding`, `query_scope`, original compiler/current-artifact
correspondence and final transaction settlement remain authoritative. A native
ABI/profile update needs a fresh capture and newly compiled catalog; old programs
are never relabeled. Typed Date and other temporal selections remain HELD.

## Typed release and host responsibilities

The target revalidates strict generated parameters, submits original SQL through
the public assembly and requires complete ordered QueryRows. Native refusal or
unavailability remains an inspectable original outcome; it never becomes empty
rows. A selected absent ColumnSet raises ADOPTION_MISMATCH. DTO validators run
inside the host transaction interval and no rows escape failed final settlement.

The supplied `operation(timeout)` must own its adopted transaction and configure
native statement and operation deadlines no greater than the requested budget.
The target checks the whole elapsed budget before dispatch and release. The host
settles and releases the transaction; the target never borrows a foreign handle.
Eager verification uses the same complete native read/page path. Candidate pages
retain the complete original `weft.engine-page/0.1` artifact, exact page bound,
hidden authored Key outputs and owner cursor. Native execution recompiles and
compares the original program against the complete current binding and page
metadata before data SQL. Optional typed cursor values must match the owner's
original lexical cursor under its own Key codecs. `QueryPage.next_sort_values`
retains those native decoded values; the SDK never reconstructs a native cursor.

The subset is a single nonaggregated source with native authored primary-Key
ordering, size1..999, and supported non-temporal Key carriers. Native compiler
refusals remain original outcomes. Streams and protected current-query source
envelopes still require separately admitted profiles: the current catalog's RC
requirement does not establish the SDK snapshot stream contract.

## Validation

Actual owned PostgreSQL18.6 E2Es accept original core0.8 schemas, create instances
through public groups, capture original native binding/compiler inputs, build and
check the real CLI catalog, invoke generated typed queries and validate exact
DTOs. Bound-injection, valid-but-different original SQL and removal of every
native read-capable module role are refusal controls. Native source/instance
identities are observed from actual public acceptance, never fixture IDs.
Temporal qualification remains HELD.


[Original page evidence](../../04-build/evidence/typed-sdk-native-20261016/pages/README.md)
records the exact two-interpreter installed cohort and retained wrong-driver
refusal. The original read/page compiler0.4.40 is public. The separate cursor profile
below uses an explicitly selected unpublished0.4.41.dev0 candidate cohort;
complete protected action/manifest bulk qualification remains open.

## Consistent export candidate — 2026-10-16

This is an implementation design, not stream qualification. It extends the
ordinary module-ACL subset only; protected current-policy and SDK temporal
qualification remain held. UMF CONTRACT-072 owns the public stream behavior;
Truss owns the following engine equivalent of its fixed-snapshot requirement.
The corresponding explicit Truss exception must first be adopted in UMF
CONTRACT-072; ordinary RC pages do not establish that exception.

A stream consumes a complete initial `weft.engine-page/0.1` program. A distinct
Weft-owned export entrypoint first recompiles and checks that whole original
page program against the current native request, then constructs an authored-Key
ordered cursor plan with no logical or native result LIMIT. This must be a
separate delivery profile with its own obligation; ordinary read/page compiler
selection and artifacts retain their meanings. The adapter must not remove a
SQL LIMIT, derive physical columns, invent a Key or relabel an old artifact.
Source/query/parameters/actor/native binding remain bound throughout the export.

The Truss export owner holds a `NO SCROLL ... WITHOUT HOLD` portal in one owned
READ COMMITTED READ ONLY transaction. PostgreSQL fixes the portal's data query
snapshot; separate RC admission statements see current authority. Every FETCH
must independently recapture the complete native binding, compare the original
program and current compiler result, and run original `truss.query_scope` before
and after fetching. The actual session actor must still match. Any drift or
refusal discards the current buffered page and terminates the export. No
transaction snapshot lower bound is advertised as an exact snapshot identifier.

`max_rows` is a positive required integer with no fixed API ceiling. Native
profile scan/byte/resource limits remain explicit and may refuse the export;
they must never silently truncate it. The current native `query_binding` and
`query_scope` permit at most10,000 scanned rows; `query_objects`/`query_edges`
materialize complete bounded sources and root witnesses, scanning cap+1 and
refusing excess. This is a whole-source limit, not a per-page allowance.
An export of fewer rows can therefore refuse because its source exceeds the
native bound. Unrestricted `max_rows` is an API property, not an uncapped native
source claim. A scalable-source profile requires separately reviewed owner
native-source design and E2Es; this bounded initial profile cannot close that
remaining qualification gate. Each page holds at most the admitted page
size (1..999 for the current original page profile), with its own timeout and
native statement/operation deadline. The complete ordered native text signature,
hidden authored Key fields and strict generated DTO validation are checked
before that page is yielded. Client row buffering must depend on page size, not `max_rows`. Server source
materialization and query processing retain the separately reported native
whole-source limits; no page-bounded server-memory claim is made.
No cursor deadline object may outlive its individual host operation.

The host explicitly and exclusively leases an idle connection for the entire
stream lifetime, including intervals between yielded pages. A preexisting transaction is
refused before any BEGIN/COMMIT/ROLLBACK, preserving unrelated work. The export
owner closes its portal and settles its owned transaction on EOF, max_rows,
early generator close, cancellation and errors. A failed/unknown cleanup
quarantines the connection through the original host; no rows escape a failed
page. Final-page delivery and successful completion require positive native portal
close and transaction rollback. Reaching `max_rows` is a bound, not a declaration
of natural exhaustion. After any page failure the portal is terminal: a
savepoint rollback does not rewind cursor position and must not enable retry.
Earlier complete pages may already have been delivered; a later failure
is explicit and must never be presented as a completed export. No internal retry
or reconstructed continuation restarts a failed stream.

### Module boundaries and required evidence

Weft core owns the unbounded authored-Key logical plan. Its PostgreSQL backend
owns cursor-delivery SQL and obligations. `weft-runtime` owns original engine
program checking, with the same Rust implementation exported through Python and
WASM. Truss `query_stream.py` owns public stream custody and lifecycle;
`_query_stream_runtime.py` owns execution through the existing guarded psycopg
host. `catalog_runtime.py` and `access.py` integrate these APIs. The SDK adapter
imports no psycopg or SQL lowering implementation. Existing Date/compiler
defaults and native SQL installation files are outside this slice.

Qualification must exercise accepted core0.8 schema and public instance creation,
actual ordinary-role native binding and generated SDK calls: 2,500 rows exported
with max_rows2,200; writer commits after the first page; snapshot excludes the
new data; grants/source drift between and during pages prevent the affected
page; exact ordering and DTO validation; page deadline; early close; injected
fetch/cleanup failure; foreign transaction preservation; portal inventory and
owned server shutdown. Compiler refusal/drift controls and browser/Python
entrypoint parity are required. The existing boundary checker must own each new
module before promotion.

The [mechanics probe](../../04-build/evidence/typed-sdk-stream-20261016/cursor-mechanics.json)
confirms only PostgreSQL18.6 portal behavior on a synthetic table. Both HOLD and
NO HOLD cursors retain their data snapshot but continue FETCH after SELECT
revocation; fresh native privilege inspection observes the revocation. Therefore
that probe cannot establish Truss authority, current-policy safety or SDK stream
qualification. Original admission before/after each page remains mandatory.

### Related-Key result conversion — 2026-10-17

The optional Python SDK adapter converts native `QueryRelatedKeys` to the
original generated Key class under `truss-related-keys/0.1`. It checks the
original output decoder, compiled representation and model pins before row
iteration, including empty results. It retains equal ordered Key tuples as
separate parallel-edge occurrences. Exact component types, the declared bound,
owner field validators and the complete result DTO are checked before release.
Read, page and stream share this conversion; native results and transaction
settlement remain unchanged.

Three basic adapter checks using genuine generated commerce Keys and five
existing stream lifecycle checks pass against the SDK R14 wheel (SHA256
`8197bac52d8b170f43a401e600d27f3fd8451685616bb3d1596c73fed89616d0`).
Run `scripts/test_typed_sdk_related_keys.py` with that runtime and its generated
commerce package on `PYTHONPATH`. These adapter checks construct synthetic
metadata; genuine compiler-issued stage-two/native integration remains
unfinished. Compiler versions, IR admission and the ordinary published Weft
0.4.40 default are unchanged. This increment establishes no end-to-end
navigation, publication or release qualification claim.

### Genuine RelatedKeys workflow — 2026-10-17

The optional development cohort now has a [passing public native workflow](../../04-build/evidence/typed-sdk-related-20261017/verification.json), using the [exact pinned wheels and generator](../../04-build/evidence/typed-sdk-related-20261017/cohort.json). It accepts the original Core 0.8 schema, creates objects and parallel edges through public APIs with caller commits, captures original native requests, runs genuine SDK CLI generation/check, and calls generated reads, pages and streams. Results retain actual generated CustomerKey classes, parallel occurrences, truncation and empty bags. The workflow also checks cursor cleanup, ordinary qualified SQL and refusal of a different valid original program.

This is macOS arm64/Python 3.14.8/psycopg 3.3.6/PostgreSQL 18.6/Bun 1.4.2 evidence. UMF's shared stream mapping fix is included in the pinned SDK; no Truss output shim is used. The compiler gate requires the actual Truss read/page compile and original-program check APIs for `0.4.42-dev.0`. Published Weft 0.4.40 remains the ordinary default; backend 0.4.41 and ordinary IR 0.2.7 checks remain exact. New navigation IR, ordered-page profiles, Graph, temporal, protected actions and publication remain outside this result.

`scripts/check-typed-sdk-related-native.py` uses the original [schema fixture](../../../../packages/python/examples/typed_sdk_related_schema.json). Supply `--generated` from the pinned UMF generator with package `native_sales`, records `sales.order` and `sales.customer`, and projection `{name: "OrderIdentity", record: {module: "sales", element: "order"}, fields: [{module: "sales", element: "id"}]}`. Pass the same schema as `--model`, a fresh `--output`, the pgserver PostgreSQL 18.6 `--pg-bin`, and exact Bun 1.4.2 `--bun-executable`. The harness obtains SQL through the SDK's original capture/render API before native capture; it does not repair bindings or captured SQL.
