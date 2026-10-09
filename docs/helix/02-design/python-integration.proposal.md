# Python consumer integration design

This proposal implements the short-term consumer path in the [build plan](../04-build/implementation-plan.md#python-consumer-integration-priority--2026-10-09). ADR-001 remains accepted and ADR-003 remains proposed; the human requested a Python implementation promptly and asked for details before selecting the route. This document supplies those details without recording acceptance. CONTRACT-004/007/010/011/012 and the shared authorization design govern behavior. The [original consumer requirements](../04-build/evidence/consumer-python-requirements-2026-10-08.md) supply R1–R10.

## Implementation boundary

Recommend a separately packaged Python 3.11 implementation of the Truss contracts, using the same fixed PostgreSQL layout and protected SQL/PLpgSQL routines as the TypeScript reference. Python owns host integration and protocol orchestration. Weft's Rust core owns logical SQL compilation. PostgreSQL owns transactions, persistence and qualified native enforcement. Authorization policy/resolver semantics and their compiled/native handoff belong to the active security workstream.

This route needs no Rust port of Truss. It does require an independent Python adapter and exact codecs, shared callable database protocols, and a corpus that catches divergence from TypeScript. Shared native enforcement is intentional; language-neutral expected results remain independently authored. Performance evidence must determine whether any Python planning/resolution step needs a native implementation.

| Component | Python responsibility | Shared or owner-supplied dependency |
| --- | --- | --- |
| Catalog and installation | Invoke explicit installer/check procedures; expose admitted module revisions/layout version; refuse incompatible majors | UMF-authored original layout/DDL and Truss installer/admission; complete accepted catalog/report producer |
| Queries | Prepare admitted input, invoke compiler, preserve ordered parameters/obligations, submit through the original transaction, decode exact results | Weft compiler and admitted Truss physical mapping; direct key/page procedures for direct-read shapes |
| Mutation/import | Validate request shape; orchestrate group/precondition/import protocols; retain pending versus committed/unknown distinction | Shared protected native effects, journal, immutable receipt and finalization |
| Authorization | Supply the host-authenticated connection and consume the security workstream's admitted invocation boundary | Original database session person, current grants/policy, admitted subject/key/fact mappings and compiled enforcement |
| Exact values | Decode text/tagged values with exact integer/decimal/time/JSON handling and selected codecs | CONTRACT-010 and pinned shared value profiles; no float intermediates |
| Feed and reached | Consume complete manifests, apply atomically, retain original durable proof, compare opaque tokens through selected operation | CONTRACT-006 source epochs, complete feed/application/ACK and current authority |
| Conformance | Execute the same versioned fixtures and emit complete observations | CONTRACT-011 manifest/result/divergence/assessment grammar and STP-028 interchange |

Weft's committed source exposes `weft.compile_json(request: str) -> str` through the `weft-sql` PyO3/maturin package. Its `truss-postgresql-qualified` build feature is distinct from candidate/test configurations. Python packaging must pin the actual admitted feature/backend tuple, not infer it from an import or package version. Test-only configuration exports cannot serve as production registration. This source observation does not prove wheel availability or Python authorization/compiler qualification.

## Consumer count-summary integration

Committed Weft `5856c73db0342363e64802905a94abb96209d757` defines COUNT(*)
in CONTRACT-004's application-read 0.2 dialect and resolves it in
`crates/weft-core/src/application_resolve.rs`. R8 should consume that owner
implementation rather than add a Truss aggregate compiler. The explicit
readProfile is version `weft-application-read/0.2.0`, subset `count-summary`;
omitting it does not supply bounded interactive-read semantics.

For this profile, grouped counts require complete grouping order and LIMIT;
global counts have one row and exclude ORDER BY/LIMIT. Cursor and relationship
predicates are excluded. Empty global input produces one zero-count row; empty
grouped input produces no rows. Joins retain bag multiplicity. Python preserves
the admitted exact integer carrier without float conversion, ordered parameters
and every original host obligation. Query LIMIT bounds returned groups, not
necessarily scanned input or native execution work.

PY-02/05 must independently test empty/global/grouped inputs, duplicate joined
rows, exact count decoding, parameter domains, omitted/partial grouping order,
missing grouped LIMIT and forbidden cursor/relationship constructs. Use actual
authorized native data and plans with finite selected scan/statement/transport
budgets. Compiler acceptance alone does not prove the Truss backend supports
the selected aggregate, security mapping or exact decoder; missing obligations
refuse the whole read. Parsed-query input remains a separate Weft-owned ABI
dependency: its availability cannot be inferred from SQL-text count support.

## Host transaction adapter

Use the semantic Executor operations of CONTRACT-007 rather than a language-specific second transaction protocol. The adapter accepts the caller's actual live connection/transaction object, validates ownership/lifetime, and retains it internally. No transaction identifier is accepted as a substitute. Initial delivery selects one driver/transaction mode and qualifies it; sync and async modes cannot share a support claim without separate evidence. Driver selection remains explicit.

- Owned execution begins on one connection, commits after complete native finalization, and publishes durable results only after observed commit. Failed or unknown commit preserves recovery state.
- Adopted execution issues no outer BEGIN/COMMIT/ROLLBACK. Group-local savepoints contain failed effects while preserving prior caller work. Pending results settle only through the original adapter's outer-commit observation.
- Dry-run invokes the actual group path and its final-state/deferred validations, then the caller rolls back the outer transaction. The adapter must restore any operation-local constraint mode. No journal, request identity or receipt survives. A simulated success cannot rely on skipping commit-time validation.
- No automatic callback retry occurs. A connection loss may mean commit_unknown; exact request-ID recovery uses the same original semantic input and original ordered result. Retrying with a new request ID is a new action.
- Reads use the caller-person read-only transaction and current disclosure policy. A successful application-role lookup does not give access to private integrity observations.

## Security workstream handoff

Consume the security agent's model and implementation. Do not create an independent Python ACL policy parser, host role map, or alternative predicate compiler. Their current Truss predicate/key/namespace/transport/stored-key/query-use modules are component candidates, and their TypeScript interfaces are not yet a language-neutral public Python ABI.

The shared invocation design must specify: original authenticated subject/session binding; complete original policy/model/key identities; admitted compiler artifact and obligation inventory; native entrypoint, physical parameter/selector order and protected publication rules; current-authority refresh/invalidation; and exact denied/unavailable/error behavior. Artifact hashes identify bytes but do not grant authority. Python can orchestrate resolution through that boundary while native policies enforce the applicable rules.

R4's database reader/writer membership and any model-level ACLs are separately applicable rules. R5's authenticated connection actor and an asserted origin are separate facts. Internal definer ownership cannot replace either. The consumer's x- action extension must survive the same selected origin/journal path. Security qualification covers reads, group effects, imports, receipt replay disclosure, catalog enumeration, feed and reached.

A Python adapter must refuse an unavailable shared security profile; it cannot use the raw predicate fixture or a caller-supplied actor as a fallback. Exact registered policy/native context and privacy behavior are the security workstream's outputs. This proposal defines the consumer-facing dependency and its required tests without choosing their policy semantics.

### Current security-owner native observation handoff

The working-source CONTRACT-053 reviewed in
[the current boundary receipt](../04-build/evidence/design-audit/security-current-boundary-review-2026-10-09.json)
specifies a private principal observer returning native superuser, bypass and
encoding facts as TEXT. SESSION_USER and CURRENT_USER are selected outside the
definer as original/effective actor. That response is exactly one row with five
ordered fields, OIDs `[19,19,25,25,25]`, text format zero and non-null valid UTF-8.
The separate direct-principal option uses five TEXT fields: these are distinct
profiles, not decoder fallbacks. Inspection on 2026-10-09 still observes this
distinction; it does not adopt the uncommitted owner contract as a released ABI.

PY-01/03 must demonstrate original raw field metadata/byte custody before
decoded identity use. A driver-returned string tuple alone cannot prove the
selected OIDs, formats or original connection observation. Verify actual
session actor, admitted effective actor/reset state, false superuser/bypass and
UTF-8 through the owner's procedure. Missing/malformed facts close admission;
do not substitute catalog lookup or a host-supplied role map.

Subject-key results remain ordered TEXT OID25 even when a selected ordinary
subject preflight uses native name for its SESSION_USER argument. Argument
carrier selection does not change key-output semantics or authorize the caller.
Preserve owner-issued registration and original policy/key/context provenance;
serialized configuration cannot mint an issued resolver handle.

Independent Python cases must swap actor/key OIDs, reorder fields, return NULL
or malformed UTF-8, change the actual session/effective actor and lose the
original response. None may reach application effects or publish protected
facts. A host deadline does not prove native cancellation/rollback: retain
original unresolved execution and quarantine custody until qualified native
termination under CONTRACT-007. Security-owned routine/privilege closure and
actual Python driver evidence remain dependencies of this slice.

## Exact transport

Use Python `int` for admitted integral domains and `Decimal` constructed from exact text for decimals, with domain/arithmetic context explicit. Driver raw cells remain text until profile decoding. Decimal operations must not inherit an ambient low-precision context that rounds accepted values. Timestamp transport retains the original exact text and offset; expose an aware `datetime` only when its microsecond representation is lossless. Finer precision requires a lossless wrapper/text representation or explicit refusal of the convenience view. Preserve raw exact JSON bytes; a convenience parser uses an admitted numeric decoder, never the default float path. Python bool must be distinguished from int at validation boundaries.

Read shapes retain absent versus explicit null, ordered key components, exact large integral values and original selected decimal/token meaning. Known JSON-like values and retained unknown extensions cannot be normalized into different meanings. Exact wire grammar remains CONTRACT-010's responsibility; these mappings are Python implementation obligations, not new UMF types.

### PY-01 independent exact-value expectations

Materialize these pairs under explicitly admitted authored definitions and the
shared CONTRACT-010 carrier; the examples do not expand a selected native domain.
Retain the original wire alongside any Python convenience value. Compare both
original bytes/meaning and independently expected logical presence through
Python-write/TypeScript-read and the reverse.

| Input distinction | Required expectation |
| --- | --- |
| Adjacent integral values 9007199254740992 / 9007199254740993 | Distinct exact Python integers and readback; no float intermediary or equal rounded key |
| Decimal text 1.0 / 1.00 | Preserve each original lexical form where the selected value contract requires it; mathematical equality or Decimal equality cannot rewrite stored/original request bytes |
| Signed decimal zero / unsigned zero | Preserve selected lexical/sign semantics; key canonicalization is a separate admitted operation and cannot redefine value transport |
| Decimal exceeding the process's ambient precision | Construction/readback stays exact; arithmetic requires an explicit admitted context or refusal, never incidental rounding |
| Timestamp with nine fractional digits | Preserve all original digits and offset; a microsecond datetime is unavailable unless the actual value has an exact representation |
| Same instant with different authored offsets | Preserve original text/offset; UTC conversion as a convenience does not replace the retained authored value |
| Nested JSON numeric token and ordinary numeric-looking string | Preserve distinct families recursively; a number-token decoder cannot reinterpret the string or discard original unknown extension content |
| Absent, explicit null, empty string and empty collection | Four distinct admitted values/presence states; no defaulting or truthiness conversion merges them |
| Python True supplied for an integral field | Reject at the typed validation boundary despite bool being an int subclass; actual boolean fields retain boolean meaning |

Include native domain refusals separately from host precision refusals. A value
outside the selected database domain cannot become supported merely because
Python can represent it. Exercise both unprojected siblings and projected values
through the selected complete-value decoder, preserving whole-result refusal
when mandatory meaning cannot be decoded.

## Execution slices and independent test schedule

| Slice | Depends on | Deliverable and test gate |
| --- | --- | --- |
| PY-01 protocol adapter and codecs | Selected driver and CONTRACT-007/010 bindings | Inert construction; original connection adoption; no outer transaction commands; lossless raw transport; large integers/decimal/time/JSON/absent/null independent vectors; Python bool/int refusal |
| PY-02 compiler integration | Published/pinned Weft wheel and admitted mapping | Clean Python 3.11 consumer compiles original supported queries; preserves parameters/obligations; rejects unsupported profiles before native submission. Do not use test-original configuration as production authority |
| PY-03 identity/security | Security workstream's complete handoff | Writer succeeds; reader write refuses; outsider read refuses; no identity refuses before application SQL; conflicting actor refuses; definer execution retains original person; denied queries publish no protected facts |
| PY-04 groups, dry-run and retries | Complete accepted catalog/install, PY-01/03, protected group/receipt procedures | Real group/preconditions; operation rollback preserves prior caller work; dry-run and apply violations agree; lost acknowledgment replays original ordered results; changed input conflicts; all-no-op receipt survives; commit_unknown remains unresolved |
| PY-05 reads/import/enumeration | PY-02/03/04 and native indexed/direct routes | Bounded key/equality/relationship/page/aggregate cases with actual plans; read-only enforcement; atomic/per-item imports/provenance; module revisions and incompatible layout refusal |
| PY-06 feed/visibility | Complete source manifest/application/ACK and receipt-token design | Whole transactions only; durable applied position; restart equality; reached false before apply only with admitted original token commitment and snapshot-exclusion evidence, otherwise unavailable; true only after complete durable inclusion proof; old snapshots, incomparable epochs and missing retention evidence explicit; no numeric xid-order shortcut |
| PY-07 publication/interchange | All applicable slices and versioned shared corpus | Clean wheel install; named layout/corpus/backend versions; Python-write/TypeScript-read and reverse on one real database; independent state/journal/receipt observations; unknown/newer required corpus and skipped cases prevent qualification |

Author setup/call/expected-result/error/journal fixtures before collecting observations. Reuse the existing conformance manifest's separate fixture/input/expected/identity-alias artifacts. Opaque identities are saved aliases, not fixed generated IDs. Existing seventeen-field accepted reports and original source epochs remain native outputs; no fixture accepted revision or invented epoch enables these slices.

## Decisions still required

ADR-003 acceptance and Python package/repository ownership; initial driver and sync/async mode; published Weft wheel/feature tuple; admitted authorization ABI; stable install version and consumer-migration route; exact managed Lakebase version/extension/identity/transaction profile; native realization of CONTRACT-009's specified minimum 24-hour receipt protection; and receipt-token/reached ABI. Python adapter/codec/corpus work can start independently where these choices do not affect semantics. Complete public capability release still waits for the shared protected runtime and qualification.


## Consumer closure order and accountable outputs

R1–R10 are release outcomes, not ten additional votes on already selected
transaction, exact-value or receipt semantics. Close the route decision first;
author corpus cases alongside shared runtime work; qualify native identity
before consumer effects; then run the complete release conjunction.

| Requirement | Required output and implementation slice | Outstanding selection versus execution |
| --- | --- | --- |
| R1 Python route | ADR-003 owner decision, named package home and corresponding ADR-001 amendment | Owner decision pending; do not accept either ADR by inference |
| R2 shared corpus | Versioned data manifest, setup/calls/expected/error/journal/alias artifacts and native two-way interchange runner; PY-07/B-015 | Shared case/operation/identity grammar proposals are authored; exact admitted fixture/procedure/observer profiles and full corpus artifacts remain to author; actual TypeScript/Python runs then required |
| R3 installation | Stable compatible layout, exact DDL digest, installer/check plus explicit consumer deployment invocation; CH-01 and LM-01–06 | Stable release tuple and managed target selection open; native install/migration evidence not yet qualified |
| R4 membership | Security-owned person membership and enforced read/write boundary; PY-03 | Shared authorization ABI/profile belongs to security workstream; native writer/reader/outsider/no-identity cases required |
| R5 origin | Original session actor and separately retained asserted action extension; PY-03/04 | Security/native origin handoff, then actual journal correspondence; host cannot supply authority |
| R6 dry-run | Adopted original transaction with contained savepoints and actual final-state validation; PY-01/04 | Select one driver/mode; execute same-plan dry-run/apply and unchanged-after-rollback cases |
| R7 retry/reached | Immutable original result/token, current-snapshot comparison and complete applied coverage; PY-04/06 | Select token/resolver and native clock/protection profiles implementing the existing minimum 24-hour floor from first trusted confirmed commit observation; execute RV-01–14, including lost-ACK, no-op, snapshot, restart, exact expiry boundaries and epoch cases |
| R8 interactive reads | Direct versus Weft routes and finite indexed/work budgets; PY-02/05 | Parsed-input ABI is Weft-owned; aggregate/index resource profiles remain; actual native plans required |
| R9 exact values | Existing CONTRACT-010 wire plus Python int/Decimal/lossless time/JSON projections; PY-01 | Select owner codec tuple; independent boundary and round-trip vectors required without float intermediates |
| R10 publication | Release names Python/TypeScript, PostgreSQL/managed target, layout, corpus, UMF, Weft and authorization/profile versions; PY-07/B-014 | Exact artifacts and publication tuple open; clean package install and full matching receipts required |

The first consumer-ready release must satisfy every row; a working compiler or
adapter alone cannot replace it. Until R3/R10 close, describe source pins as
recorded experimental integration inputs rather than stable dependencies. No
managed Lakebase or Aurora support claim follows from isolated PostgreSQL 17.9
evidence. Qualification names the actual target version, extension availability,
authenticated connection semantics and transaction restrictions.

## Original configuration snapshot protocol

PY-01 can consume the [shared twelve-column native snapshot wire](contracts/installed-context-admission.proposal.md#original-snapshot-host-projection-and-shared-native-wire). PostgreSQL retains the pre-effect capsule and compares live current state before returning bytes. Python preserves canonical xid/ordinal/generation text, exact hex bytes and direct SHA-256; it keeps original adapter/transaction/cut/profile custody and rechecks at use. Current-only collection remains a different protocol. The TypeScript/native 171-check component establishes scoped correspondence; Python execution, qualified transport/security/installation and public report/finalization remain PY-01/03/04 evidence.
