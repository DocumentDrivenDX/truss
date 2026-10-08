# First inert runtime package — 2026-10-08

The Ashlar owner's end-to-end instruction explicitly includes standing up Truss.
This implementation starts the accepted TypeScript/Bun package boundary without
substituting the older 0.2 native layout for the selected 0.12 source. The native
bootstrap remains closed under CONTRACT-008/012: required bodies, role/security
and complete installation tuple/inventory are not implemented or qualified.

`packages/postgresql` now has an actual ESM ES2022 build and declarations. The
private candidate name is `@documentdrivendx/truss-postgresql`, version
`0.0.0-experimental.1`. No npm release or general package-name adoption is claimed.
Its supported assembly profile is explicitly inert and supports no native
capability. Existing contract declarations remain the canonical source; their
37-file public dependency closure is emitted exactly. Core data semantics remain
UMF-owned; this package interprets no UMF model and exports no value encoder.

Three Bun tests / 18 assertions pass for no native/registry calls, immutable
configuration snapshots, unsupported/incompatible/accessor refusal, unverified
readiness and disposal without touching host-owned resources. Initial declaration
compilation refused an untyped readiness parameter; adding its governing
CapabilitySelection annotation fixed that error. TypeScript 7.0.2 strict build
passes, and the runtime graph has no host import, driver, compiler startup or
native clock. Source declaration files and emitted files have recorded hashes.

`packed-check.json` records an empty consumer's typecheck and actual Bun runtime
through the public package export, plus copied-brand refusal and exactly one
transaction-brand declaration in the published closure. `packed-consumer.ts`
retains its source. These are local packaging/inertness checks, not a native
conformance result, browser/Node evidence, actual schema acceptance or a running
Truss feed. Native capability methods remain explicitly unavailable.

Reproduce with the commands in the package README. Generated `dist` artifacts are
retained for review; build evidence records their hashes and the original owning
binding digests. Future tooling/adapters must consume the same public PostgreSQL
brand identity; they cannot independently copy its declaration closure.


## Native vector decoder prerequisite

The package now exports `decodeNativeVector` for CONTRACT-008's proposed
`truss-bootstrap-native-vector-decoder/0.1.0` output grammar. Original text and
ordered canonical tokens remain immutable. OID/int2 domains use bounded exact
BigInt arithmetic, with byte/token limits and optional exact count correspondence.
All eight original independently authored vectors are exercised; additional
controls refuse normalization, malformed spelling and exceeded limits. The
combined suite has five tests and 45 assertions. Strict build and clean packed
consumer checks pass.

`native-vector.json` retains exact SQL/stdout and decoded correspondence from
three constant vector observations on the existing local PostgreSQL 17.9 sandbox.
The empty OID vector is observed as empty text with bounds `[0:-1]`. No mutation
occurs. Reproduce with `bun scripts/check-native-vector.ts` against that sandbox.
This narrow observation does not qualify complete catalog collection, index or
signature field semantics, all dimensions/JSON correspondence, native installation
or driver/resource/containment support. Those obligations remain explicit.


## Ordinary native array decoder prerequisite

`decodeNativeTextArray` implements CONTRACT-008's proposed comma-delimited
text-element output subset. It retains exact original text, ordered nested
elements, native-null distinctions and exact signed bounds. Rectangular shape
and supplied native dimensions must correspond. UTF-8 scalar validation and
explicit byte/node/depth limits bound parsing; decoded values are frozen.
Unknown output syntax refuses. Element/array type selection remains a separate
admission obligation; no generic parser grants ACL authority or interprets UMF.

All eight original independently authored array vectors and further escape,
shape, scalar and resource controls pass. Combined package suite: seven tests,
88 assertions; strict build and clean packed consumer pass. `native-array.json`
retains one read-only SQL query, exact original stdout and seven decoded native
arrays with exact original JSON correspondence on local PostgreSQL 17.9.
Reproduce with `bun scripts/check-native-array.ts`. Complete catalog field/type
coverage, aggregate collector custody and installation remain unfinished.


## Native trigger argument decoder prerequisite

`decodeNativeTriggerArguments` implements CONTRACT-008's UTF8 tgargs framing
subset: exact nonnegative native-int2 count, original lowercase hex, exact byte
length, bounded allocation and precisely count NUL terminators consuming all bytes.
Empty strings and BOM characters remain data; invalid UTF8 cannot be replaced.
All twelve original independent vectors and further domain/encoding/resource
controls pass. Combined suite: nine tests, 116 assertions; strict build and clean
packed consumer pass. `native-trigger.json` retains original SQL/stdout and exact
argument correspondence from one actual temporary trigger on local PostgreSQL
17.9 UTF8. The entire probe transaction rolls back. Reproduce using
`bun scripts/check-native-trigger.ts`. No Truss triggers are installed; complete
trigger definition, WHEN/dependency admission and native bootstrap remain open.


## Actual routine carrier composition

`decodeNativeRoutineCarriers` composes the selected vector/text-array decoders
for input argument OIDs and names/modes/settings. Count and zero-based input
vector dimensions must match; native text-array elements must correspond exactly
to their original JSON projections. Full original catalog row text remains opaque
and unchanged, including unknown content. No integer JSON parsing of that full
row occurs. This subset does not admit other routine fields or grant authority.

Eleven package tests with 124 assertions, strict build and clean packed consumer
pass. `native-routine.json` retains the original observation query hash, executed
SQL, exact original stdout and decoded values. `check-native-routine.ts` executes
the governing proposal query for one temporary routine on existing local
PostgreSQL 17.9 and rolls back the full transaction. The actual signature/name
values independently match the authored probe. Exact source query parameter is
bound to the current temporary namespace; no expected-name routine filter is used.

This is carrier composition only. Other fields/all-argument types/ACLs, full native
dependencies/security, aggregate collector memory/work/cut/transport custody and
Truss installation remain unfinished. Per-carrier decoder limits cannot establish
the full collector resource ledger.


## Shared decoder accounting

`NativeDecodeBudget` supplies caller-owned aggregate input-byte/materialized-node
reservations across selected vector/array fields and routine raw-row/JSON
projections. A failed reservation permanently exhausts the ledger; prior
reservations are not refunded and no reset or implicit retry is available.
Per-carrier limits still apply. Routine composition passes the same optional
ledger through all selected codecs. Tests demonstrate aggregate refusal for
individually valid fields, node exhaustion, immutable snapshots and combined
raw-row/projection custody. Fourteen tests, 134 assertions, strict build and clean
packed consumer pass. No new native workload occurred.

This accounts selected decoded input and nodes only, not total heap allocations:
bound strings, JSON parser allocations, dimensions, hex buffers, transport
materialization, work/deadlines/cancellation/native containment and collector
completion remain separate obligations. Callers without the optional ledger
retain only per-carrier limits. Existing native receipts qualify the original
observations, not native deployment of this aggregate accounting.


## Native Bun execution foundation

`bun-execution.json` records a small actual Bun 1.4.2 SQL probe on the existing
local PostgreSQL 17.9 sandbox. `scripts/check-bun-execution.ts` verifies explicit
text transport for large integer/decimal/timestamp/JSON parameter values and SQL
NULL, native SERIALIZABLE/read-only settings, same-transaction backend affinity,
original controlled callback exception with independently observed temporary-table
rollback, and savepoint rollback preserving earlier work. Credentials are read
in memory from the explicitly labeled private sandbox and never retained. No
persistent table remains; no cloud or configuration change occurs.

This establishes the direct unprepared driver path for the next executor
implementation. It is not an Executor conformance claim: original caller adoption,
transaction generation/public-operation arbitration, cancellation/cleanup, unknown
COMMIT/quarantine/recovery, prepared statements, poolers and Node remain unfinished.
A future adapter cannot infer confirmed rollback or native settlement merely
from a rejected promise. Bun API references inspected for this probe:
https://bun.sh/docs/runtime/sql and https://bun.sh/reference/bun/TransactionSQL.


## Engine-owned executor composition

`createEngineExecutor` implements the canonical Executor interface over mandatory
`NativeConnectionSource`/`NativeConnection` host ports. Engine handles are issued
into a private affinity/lifetime map; ended/foreign/concurrent handles refuse.
Savepoint identities are issuer-owned, scoped to the original entry and invalidated
according to native rollback/release ordering. Results are copied/frozen with
text/null cells and exact text affected-row counts. Callback exceptions propagate
only after the host confirms rollback/release. Commit uncertainty closes admission
and invokes original-resource quarantine, without release or guessed rollback.

Eighteen package tests, 146 assertions, strict build and clean packed consumer
pass. New executor tests use controlled native ports, not actual driver execution.
The earlier Bun probe establishes only its separately described native subset.
The concrete Bun bridge remains unfinished; port promises cannot constitute
native confirmation without a qualified bridge. Caller adoption and cancellation
explicitly refuse. Parameter-domain/JSON validation, SQLSTATE-specific error
mapping, full native result/resource admission, current public-operation registry,
quarantine/recovery authority and driver qualification remain unfinished. No
complete Executor conformance or native Truss readiness is claimed.


## Actual direct PostgreSQL executor bridge

The separate host-only `packages/pg-runtime` source composes pg 8.16.3 with the
engine-owned executor. Bun's ordered-result metadata lacked native column
descriptions in the observed subset; pg supplies them for duplicate names and
empty results. All native text-format type parsers return original text, preventing
default numeric/JSON/date coercion. Safe nonnegative command-tag counts convert
to exact text; unsafe/null counts and multiple result sets refuse. Native COMMIT
and ROLLBACK command correspondence is mandatory. Unknown resources remain held
in quarantine; pool shutdown refuses unresolved quarantine.

`pg-executor.json` records an actual small read-only PostgreSQL 17.9 transaction
through `createEngineExecutor` and this bridge under Bun 1.4.2. Large integer and
decimal values remain exact text without SQL text casts; duplicate column names,
empty-result descriptions, savepoints and confirmed commit pass. Host strict
typecheck, eighteen package tests/146 assertions, portable build and clean packed
consumer pass. Dependency lockfile is retained. The build compiler path now uses
the installed file directly, fixing Bun package-export resolution; the relative
packed-check compiler invocation initially failed and the absolute invocation
passed. No persistent tables/cloud workload/settings change occurred.

The host package remains source-only. Caller adoption/cancellation, native lost
COMMIT/rollback termination/recovery settlement, parameter domains, complete
resource/error/current-operation admission and prepared/pooler/Node qualification
remain open. This is actual engine executor integration, not native Truss bootstrap.


## Native writes and error containment

The pg executor probe now includes actual parameterized bigint/JSON writes,
a deliberate uniqueness violation followed by rollback/release of its original
savepoint, and exact retained prior-write observation. A controlled callback
exception rolls back temporary-table creation and insertion; a following
transaction independently observes absence. Successful write scope drops its
temporary table before confirmed commit. No persistent native tables remain.
Known rowless CREATE/DROP/ALTER/SET/GRANT/REVOKE/COMMENT commands with absent
command counts return zero affected data rows; unknown absent-count commands
still refuse. This fixes DDL execution needed by bootstrap without treating
unknown metadata as a known count.

Integer, decimal, boolean and JSON carrier domains now validate before native
execution. JSON syntax validation transmits original text unchanged; no decoded
JSON tree becomes storage authority. Nineteen tests/154 assertions, strict host
typecheck, portable build and packed consumer pass. The final native probe was
rerun after validation changes. Native error-to-SQLSTATE mapping, exact resource
admission, caller adoption/cancellation, uncertain native settlement and full
bootstrap remain unfinished. No cloud/settings change occurred.


## Native deadlock retry settlement

Statement SQLSTATE 40001/40P01 now returns `retry/whole_transaction` with the
original state code, without native error-detail disclosure. The original entry
remains failed; savepoint rollback cannot clear a whole-transaction retry. If the
callback returns after this failure, the outer executor confirms rollback/release
and returns the original retry failure rather than committing or replacing it
with generic transaction_unusable. Other native state codes retain no-retry
transaction-unusable semantics until their explicit classification is implemented.

Twenty tests/164 assertions, strict host typecheck, build and packed consumer
pass. The native probe adds two concurrent direct transactions taking two private
transaction-scoped advisory locks in opposite order: one actual 40P01 victim
returns whole-transaction retry after outer rollback; the other commits. No
automatic retry, table or persistent lock remains. Initial native attempts instead
returned 55P03 under the default one-second lock timeout and both rolled back.
The successful probe uses a three-second transaction-local lock timeout under
the existing five-second statement limit; no deployment setting changes. Final
original outcomes are retained in pg-executor.json. COMMIT-phase SQLSTATE-specific
settlement, cancellation and full native recovery/bootstrap remain unfinished.


## Native COMMIT rejection settlement

The mandatory native commit port now distinguishes committed from rejected only
after original server error and confirmed same-connection rollback. The pg bridge
recognizes actual pg DatabaseError instances in SQLSTATE classes 23/40, queues
ROLLBACK on that original connection and checks its command response before
returning rejected. Unknown error/transport/rollback remains commit_unknown and
quarantined. The executor releases a confirmed rejected resource and returns
40001/40P01 as whole-transaction retry; other admitted constraint rejections
return transaction_unusable with no retry. Successful callback data remains withheld.

Twenty-one tests/168 assertions, strict host typecheck, build and packed consumer
pass. Actual deferred-FK COMMIT rejection returns 23503 with zero quarantined
resources after confirmed rollback; a following transaction independently verifies
that both temporary tables are absent. Native evidence remains in pg-executor.json.
No persistent tables or deployment/cloud changes occur. Actual native 40001 at
COMMIT, lost transport/containment/settlement, adoption/cancellation, resource
admission and complete bootstrap remain unqualified. A caller-fabricated error
code is not sufficient native rejection evidence in the bridge.


## Built host package integration

The host package now has public ESM/declaration exports and a retained strict
TypeScript/Bun build with source hashes in its dist/build-evidence.json. Its public
declarations import the owning Truss package by name, preserving canonical handle
types without source-relative/private paths. pg remains an external host-only
dependency; exact runtime/type dependencies and workspace resolution are locked.
The root references both workspace packages for integration tooling. An initial
public import failed because the root lacked those workspace dependency links;
adding them and reinstalling resolved it. The actual native pg executor probe
now imports both built packages by public name and passes the existing text,
column, write, rollback, deadlock and deferred-COMMIT checks.

This replaces the earlier source-only host delivery status. Published release,
clean packed-host consumer, Node/pooler qualification and full native bootstrap
remain unfinished. The required routine bodies additionally depend on protected
original-operation producers/security; observation SQL alone is not a routine
implementation. Full Truss/feed capability readiness remains unavailable.
