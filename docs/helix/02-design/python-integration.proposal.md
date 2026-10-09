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

## Exact transport

Use Python `int` for admitted integral domains and `Decimal` constructed from exact text for decimals, with domain/arithmetic context explicit. Driver raw cells remain text until profile decoding. Decimal operations must not inherit an ambient low-precision context that rounds accepted values. Timestamp transport retains the original exact text and offset; expose an aware `datetime` only when its microsecond representation is lossless. Finer precision requires a lossless wrapper/text representation or explicit refusal of the convenience view. Preserve raw exact JSON bytes; a convenience parser uses an admitted numeric decoder, never the default float path. Python bool must be distinguished from int at validation boundaries.

Read shapes retain absent versus explicit null, ordered key components, exact large integral values and original selected decimal/token meaning. Known JSON-like values and retained unknown extensions cannot be normalized into different meanings. Exact wire grammar remains CONTRACT-010's responsibility; these mappings are Python implementation obligations, not new UMF types.

## Execution slices and independent test schedule

| Slice | Depends on | Deliverable and test gate |
| --- | --- | --- |
| PY-01 protocol adapter and codecs | Selected driver and CONTRACT-007/010 bindings | Inert construction; original connection adoption; no outer transaction commands; lossless raw transport; large integers/decimal/time/JSON/absent/null independent vectors; Python bool/int refusal |
| PY-02 compiler integration | Published/pinned Weft wheel and admitted mapping | Clean Python 3.11 consumer compiles original supported queries; preserves parameters/obligations; rejects unsupported profiles before native submission. Do not use test-original configuration as production authority |
| PY-03 identity/security | Security workstream's complete handoff | Writer succeeds; reader write refuses; outsider read refuses; no identity refuses before application SQL; conflicting actor refuses; definer execution retains original person; denied queries publish no protected facts |
| PY-04 groups, dry-run and retries | Complete accepted catalog/install, PY-01/03, protected group/receipt procedures | Real group/preconditions; operation rollback preserves prior caller work; dry-run and apply violations agree; lost acknowledgment replays original ordered results; changed input conflicts; all-no-op receipt survives; commit_unknown remains unresolved |
| PY-05 reads/import/enumeration | PY-02/03/04 and native indexed/direct routes | Bounded key/equality/relationship/page/aggregate cases with actual plans; read-only enforcement; atomic/per-item imports/provenance; module revisions and incompatible layout refusal |
| PY-06 feed/visibility | Complete source manifest/application/ACK and receipt-token design | Whole transactions only; durable applied position; restart equality; reached false before apply and true afterward; old snapshots, incomparable epochs and missing retention evidence explicit; no numeric xid-order shortcut |
| PY-07 publication/interchange | All applicable slices and versioned shared corpus | Clean wheel install; named layout/corpus/backend versions; Python-write/TypeScript-read and reverse on one real database; independent state/journal/receipt observations; unknown/newer required corpus and skipped cases prevent qualification |

Author setup/call/expected-result/error/journal fixtures before collecting observations. Reuse the existing conformance manifest's separate fixture/input/expected/identity-alias artifacts. Opaque identities are saved aliases, not fixed generated IDs. Existing seventeen-field accepted reports and original source epochs remain native outputs; no fixture accepted revision or invented epoch enables these slices.

## Decisions still required

ADR-003 acceptance and Python package/repository ownership; initial driver and sync/async mode; published Weft wheel/feature tuple; admitted authorization ABI; stable install version and consumer-migration route; exact managed Lakebase version/extension/identity/transaction profile; receipt minimum retry lifetime; and receipt-token/reached ABI. Python adapter/codec/corpus work can start independently where these choices do not affect semantics. Complete public capability release still waits for the shared protected runtime and qualification.
