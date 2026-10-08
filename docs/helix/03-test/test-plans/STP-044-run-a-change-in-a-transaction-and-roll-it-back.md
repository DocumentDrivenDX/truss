---
ddx:
  id: STP-044
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-044
      kind: informed_by
    - id: TD-044
      kind: informed_by
    - id: SD-003
      kind: informed_by
---

# STP-044: Caller-owned transactions

## Story Reference and Scope

US-044, TD-044, SD-003, TP-001 and CONTRACT-007/009. Tests are planned. Native ownership/lifetime proofs qualify each adapter independently.

## Acceptance Criteria Test Mapping

Additional outcome-stage probes under CONTRACT-007: cancel before a statement, during a write, after savepoint release and around engine-owned COMMIT. Require confirmed rollback before reporting cancelled/no effects; a sent COMMIT with unknown result yields commit_unknown, while confirmed commit remains committed despite a late cancellation signal. Prove unresolved connections are quarantined before pool reuse. A cancel acknowledgment with unconfirmed rollback is insufficient. Hold the original transaction open while outcome lookup sees no receipt; no reapplication may follow temporary absence. Adopted transactions never receive a Truss-issued whole-transaction end command. These planned fault/barrier cases qualify each adapter independently.

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-044-AC1 | `adopted_scope_reads_pending_group_effects` | Same transaction sees complete group effects and pending result; independent observer sees no uncommitted graph | `@covers US-044-AC1` | Native integration | `tests/host/caller-transaction.test.ts`; host and observer connections |
| US-044-AC2 | `host_rollback_removes_effects_and_releases_locks` | All graph/derived/audit/source/request effects disappear and waiting transaction obtains locks after rollback | `@covers US-044-AC2` | Native concurrency | Same file; selected receipt profile and lock barriers |
| US-044-AC3 | `host_commit_has_single_group_origin_and_journal` | Committed effects match independent engine-owned expectation with one origin and no duplicate journaling | `@covers US-044-AC3` | Native integration | Same file; qualified engine/trigger profiles separately |
| US-044-AC4 | `truss_never_ends_or_releases_adopted_transaction` | Earlier host sentinel survives operation failure; success remains pending until host action and connection stays owned | `@covers US-044-AC4` | Native integration | Same file; native transaction-state and statement-trace observation |

## Data and Failure Probes

Adoption/access-mode matrix: actual READ ONLY with expected read_write refuses; actual read_write with expected read_only refuses rather than SET TRANSACTION; exact read-only adoption permits qualified reads while mutation/import/catalog acceptance refuses before write effects. Verify isolation and the same native connection, including session/transaction pooler paths. End the host transaction during asynchronous verification and require no usable handle; reject a failed native transaction without silently rolling it back. A native observation failure follows transaction_unusable/liveness rules and cannot trigger automatic host cleanup or substitute another connection. Retain statement traces proving no BEGIN/COMMIT/ROLLBACK/SET TRANSACTION and independent host state witnesses; trace-only evidence is insufficient.

For repeatable-read hosts, establish a snapshot before adoption and prove it remains the data snapshot afterward. If no snapshot was established yet, ordinary admitted native reads may establish one naturally; this does not license explicit snapshot replacement or a promise to preserve an unobserved prior cut. Current authority remains independently qualified under CONTRACT-005. Caller-declared accessMode is an expectation, never proof of native state.

Use earlier host write, valid group, invalid group and later host write in one transaction. Verify per-call origin restoration and no role broadening. Inject cancellation, failed savepoint cleanup, inactive/cross-adapter handle and concurrent-handle misuse. Statement trace is supporting evidence; native pending visibility/host rollback proves no hidden commit. Confirm id sequence advances may survive rollback without confusing gaps with graph effects.

For lock release use explicit blocked waiter and transaction-end barriers; observe both row/catalog and advisory request/business identity locks when enabled. Caller success followed by whole rollback removes all pending calls; failed call preserves earlier host work. Node/pooler coverage is unverified until actually run.

## Executable Proof and Handoff

Future command `bun test tests/host/caller-transaction.test.ts` requires implemented adapters and native harness. Pin server/adapter/isolation/journal mode/receipt profile and retain state/lock/trace outcomes. All four criteria block closeout. No driver mock alone qualifies transaction ownership.

## Public facade supplements

Invoke standalone mutation and group facades through the same adopted scope; independently verify neither commits, changes host isolation/access mode or ends host resources. Standalone operations reject aliases, use stored owner/endpoint/target identities and cannot return creation aliases. Inject native cleanup failure after tentative effects: return outer execution failure/quarantine, not ordinary failed/unchanged. Retain facade handles across disposal and require no new SQL. Successful inner pending results remain subject to the outer host commit/rollback.

Combined strict declaration checking includes `truss-mutation-group-capability-v0.1.typecheck.ts`: independent consumers reject standalone aliases, premature in-transaction commit, same-transaction replay labeled committed and failure with success payload. These are type distinctions only; native context and effects require the cases above.


The implementation plan's M00–M07 first integration fixture supplies independently authored graph states. M05 changes B.note from absent to explicit null: same adopted context sees pending null, fresh qualified observer sees committed absence, and host rollback restores complete graph/key/value/source/journal baseline. M06 host commit advances B exactly once and publishes only the selected note transition; toolkit disposal does not end host resources. Refused duplicate key/third relationship/stale version each compare full original before/after state after confirmed containment. Unknown termination/outcome leaves the checkpoint unresolved and cannot advance the runner or imply rollback. These remain planned native scenarios.


M00–M07 now has the authored Account/Item UMF 0.7 fixture in the implementation-plan handoff. Current owner metadata validation is valid but incomplete and proves no adopted transaction/native support. Preserve original experimental diagnostics; derive native note absent/null and exact numeric carriers only from the selected Truss profiles. Decimal precision/scale alone cannot establish authored lexical token recovery. Missing endpoint, missing target key and inverted relationship bounds have source-only refusal evidence; caller-owned native schedules remain unexecuted.


Reference fixture setup preserves the five exact original UMF experimental diagnostics and independently records selected Truss support/required-check outcomes. No source warning is dropped, demoted or rewritten complete by native evidence. Unknown new diagnostics refuse the selected setup handoff. The five-warning planning manifest and six corruption controls prove source/obligation consistency only; pending producer profiles cannot be assumed adopted to start transaction tests.


M00–M07 setup now retains original UMF authored member/key/relationship operation receipts and exact selections. Independently distinguish Account.code from Item.code and Record-qualified by-code keys before storing symbolic A/B/C/D. Same display name/key ID cannot merge catalog identities; native IDs and response IDs never replace original authored correspondence. Five ideal operations/two corrupted-receipt refusals have owner source evidence only; no native transaction, allocation or enforcement support follows.


K01–K04 companion schedules in the implementation plan separate pending portable key bytes from qualified native key ownership, complete canonical/derived correspondence and relationship counts. First contender commit versus confirmed rollback versus unknown outcome have different expected admissions; no observer absence permits retry while original work is unresolved. Incoming source bound with distinct Account parents requires complete affected target/root/invariant exclusion under the existing hierarchy or selected serializable protocol. Five UMF tuple-byte checks/two refusals prove source transport only; native barrier/lock/commit schedules remain planned.


### Caller constraint-timing containment cases

Add three planned native cases to the selected actual writer profile: (1) host writes an independently observed sentinel, sets the relevant Truss guards immediate, then calls a mutation whose native check fires before full finalization; (2) one Truss operation completes pending, host explicitly performs immediate checks, then a later distinct operation encounters unfinished-check refusal; (3) qualified fault injection loses rollback/restoration confirmation after that refusal. Observe the actual operation-local savepoint before any admission effect and retain native statement/firing evidence.

Case 1 requires either independently qualified immediate-compatible completion or truthful original native failure with confirmed operation-only containment; Truss never silently changes timing. Case 2 preserves the earlier pending graph/markers/version/history and exact immutable result after confirmed containment of the later call, without declaring any host work committed. Fresh outside observations remain at the original committed state until explicit host commit. Case 3 remains unresolved and prevents new admission; it cannot claim sentinel preservation or usable context without original evidence. Host SQL after a verified usable rollback and explicit host commit/rollback is separately controlled by the host, not an automatic Truss retry.

Verify exact original constraint modes/firing outcomes where the selected native harness can establish them; initially-deferred catalog metadata alone cannot pass. Missing native timing/containment producer is an unmet prerequisite. Existing Outcome/error/cancellation rules apply without a new application error code. These cases are unimplemented and unexecuted.


Conditional registry-index failure tests independently trigger a second unfinished operation and a genuine business-key uniqueness conflict, retaining each original admitted invocation and actual native failure provenance. Identical uniqueness SQLSTATE does not produce identical domain classification. Substitute matching diagnostic names/text, wrong original phase/object context or a forged prior receipt and require unavailable/qualified execution failure rather than duplicate business identity, not-found or replay success. Native failure with confirmed operation savepoint rollback preserves the first operation and unrelated caller work; lost rollback/status/termination retains unresolved original custody and closes reuse. Inspect no aborted/unknown connection for guessed error meaning and perform no automatic callback retry, first-operation deletion/finalization or whole-host rollback. Fixed public diagnostics remain bounded/current-authority while full protected original evidence stays under recovery custody. These are planned adapter/native classification controls and introduce no new public error code.


Operation-ordinal tests admit A, retain its private host capture, confirm rollback of A's original savepoint and then admit B on the same original native transaction. Require a fresh issued ordinal for B and refusal of every A capture even when native row absence would let a MAX-based allocator reuse A's number. Restore earlier registry/index/capacity state independently and preserve unrelated host work. Variants lose allocator state, race wrappers sharing one issuer, reach exact native ordinal limit/one-over and lose rollback completion; no replacement counter, wrapped number, duplicate adoption or automatic retry can admit work. Distinguish native operation, protocol cycle and savepoint creation ordinals in the original receipt; equal numeric values confer no cross-custody authority. Rollback across a previously finalized operation removes surviving native membership without converting its old pending result into commit evidence. These planned controls use existing context/outcome boundaries and qualify no driver until executed on its selected original profile.

### Operation admission ordering controls

Under the selected original executor profile, independently observe private ordinal/cleanup reservation, savepoint submission and completion, and native registry/capacity/graph effects. Ordinal exhaustion and failed enclosing permit reservation must refuse before this operation submits savepoint control; earlier adoption observations may exist. A submitted savepoint with lost completion consumes its ordinal, closes new admission and performs no registry/capacity/graph effects until original reconciliation proves containment. After confirmed rollback or reconciled failed creation, a subsequent admissible attempt receives a fresh ordinal. Verify native state against the independently captured pre-attempt state and preserve earlier caller work. Exercise cleanup with the operation budget exhausted: its original reserved permits remain available. Status flags, facade reconstruction and a surviving-row MAX allocator are negative controls, not confirmation producers. These are planned native cases, not executed driver evidence.

### Host command custody controls

The selected adapter harness inventories all original command submission aliases and proves their participation in the existing shared executor arbitration. Interleave host parameterized reads/writes with Truss operations and verify original command order, completion custody and preservation of host work. Exercise host rollback-to, release, complete transaction end and transaction replacement through participating paths; affected Truss captures must invalidate before subsequent admission. Independently expose an unmediated driver alias as a configuration control and require adoption refusal, not a claimed successful detection via xid/status polling. Lose a participating host-control completion and require closed admission with original recovery. No case may acquire a substitute connection or silently convert caller-owned work into an engine-owned transaction. These tests require a selected host integration and independent native observations; ordinary transaction-object declarations do not qualify them.

Private bytea parameter native cases send independently authored zero/non-UTF-8/backslash bytes, empty bytes and parameter NULL through the existing text carrier and explicit native bytea cast. Observe exact server bytes and returned hex separately. Missing/altered prefix, Base64 substitution, implicit Buffer/binary parameter and text-resource expansion undercount refuse or fail original fidelity qualification. Errors after binding/submission preserve possible native effects and original containment. These cases require a selected actual driver/input-format profile and introduce no public binary carrier.

### Cumulative resource account rollback controls

Planned selected-profile tests independently observe original account identity and retained/spent/pending state. Spend comparison/allocation work, roll back its savepoint, and require restored retained graph/custody occupancy while spent usage remains monotone. Repeat through another facade and deferred helper invocation; all consume the same original epoch allowance. At one-over capacity, reservation refuses atomically before work without partial counter changes. Lose completion after submission and require the full unresolved admitted charge retained, closed ordinary admission and original recovery. Confirm release of buffers before peak-occupancy reclamation; output absence alone cannot prove release. Exhaust ordinary work while a previously reserved containment action remains needed and verify cleanup can use only its own permits. After unknown complete transaction termination, a reconstructed wrapper must not open a fresh budget. These controls remain not_run; host-ledger observations alone do not qualify unavoidable native accounting.

The [seven independently authored accounting state vectors](resource-account-state-vectors.proposal.json) fix small symbolic ceilings and exact occupancy/spent/pending transitions for rollback, atomic refusal, unknown completion, reconstructed facades, reserved cleanup, concurrent reservations and pending-to-spent settlement. RA06 admits either participant as winner, but never both. The fixture values are not production limits or exposed ledger fields. Map each transition to selected original host/native observations before execution; no verifier may derive these expectations from candidate ledger output.

### Conditional native-account lifecycle qualification

If the backend-local account candidate is selected, execute RA01–RA07 through actual native helpers and raw-client deferred guards. Initialize inside nested host savepoints, roll back the creating level and require cumulative charges retained through the original outer epoch. Release nested levels and verify occupancy transfers without budget reset. Cause native error immediately after charge-before-work and require no spent refund; exhaustion and aborted cleanup use original reserved metadata. Reload or reconstruct a host facade and refuse account reset. Terminate the backend, preserve unknown client outcome/recovery custody and reject old captures on a replacement connection. Exercise parallel/two-phase requests before claiming their accounting support; an unimplemented transfer/lifetime path cannot pass through a callback name. Transaction-end cleanup never counts as native precommit validation or host commit acknowledgment. These cases remain planned and conditional on deployment/profile selection.


### Native routine attribute controls

Before selected-profile execution, compare every installed helper's volatility/parallel/security attributes and original body/dependency identity with the reviewed manifest. Negative installations substitute immutable or stable attributes for a stateful guard, add a stable outer wrapper, or mark a backend-local account path parallel safe; each must fail installation/profile admission rather than rely on a convenient query plan to expose the mismatch.

Execute repeated validation within one statement and across prepared-plan reuse after admitted graph/profile changes. Independently require current-state validation and cumulative charges on each required invocation; a stale cached success or skipped charge fails. Observe the selected exclusion/cut separately, since volatile snapshots alone do not guarantee coherent multi-query validation. For a separately selected pure codec, vary every declared environmental dependency and require either input-explicit semantics or refusal of the purity claim. All cases remain planned, with actual helper bodies, deployment and native observations required.

### Request-free unknown commit classification

For a request-free group or non-replayable write, lose original COMMIT acknowledgment after submission and require commit_unknown with retryScope none, retained original recovery custody and no automatic mutation retry or receipt-service call. Independently observe original native/commit settlement under the registered recovery profile; absence of a request receipt cannot prove rollback. The request-enabled control emits qualified_request_lookup only with its original admitted request and actual authorized lookup protocol. Substitute a receipt identity from another attempt or make lookup unavailable: no replacement execution or downgraded request-free path follows. Shared wire/type checks cover discriminators only; these native/host schedules remain required.

### Outer-envelope settlement controls

Retain a pending group result through a successful original withTransaction call and verify the inner object remains pending while the outer envelope is committed. Pair a pending result with another attempt's committed envelope: the host must refuse settlement. Let a callback return an application failure while deliberately retaining unrelated permitted host work; outer commit must not transform that failure into success. Lose original commit acknowledgment after a complete pending result: preserve the exact result as unresolved evidence and perform no replacement mutation. After original recovery confirms commit, return the original result only when its complete ordered evidence remains available. A lost result with known commit cannot be repaired by a fresh current-state read or replaying no-ops. Process restart controls distinguish actually admitted durable result custody from process-lifetime-only registry configuration; native commit evidence cannot qualify missing semantic bytes.

### Complete-history service and disclosure boundary

Construct an assembly with proposal-only retained payload tooling and no admitted new event/native history tuple: construction makes no SQL calls, and history selection cannot claim that payload as a complete capability. Retain a previously admitted facade across profile/decoder/authority drift; reject stale invocation or required unsupported meaning without old-decoder fallback, current-state repair, partial page/cursor or synthetic unwritten result. Native loader failure stays an outer executor outcome and preserves caller transaction ownership.

Supply observability hooks that record ordinary public phase observations. Under a hidden old-owner snapshot fixture, inspect callback/error/log payloads for private values, original owner inventory and integrity bytes: no leakage beyond the independently selected authorized projection. Returning a privileged verifier result directly through reconstruct is not allowed. These planned cases require exact selected service/authority/publication profiles and do not qualify those services by interface shape alone.

### Native history error-detail disclosure controls

Inject a native collector error whose detail/hint/context contains independently authored hidden old-owner values and whose top-level original code/phase/containment is known. Public Outcome/callback/log projection preserves required failure/recovery meaning but exposes no private detail; independently authorized internal recovery still has exact required evidence. Repeat with unknown termination and lost commit acknowledgment: withholding detail cannot imply confirmed rollback/commit or permit reapplication. Revocation before later recovery disclosure applies current authority without deleting internal evidence.

Configure insufficient protected evidence storage before admission: the dependent operation refuses before effects rather than retaining a digest-only substitute or truncated original. Use authored domain strings resembling tokens/URLs as exact data controls; no heuristic mutation of original values is allowed. These planned tests require selected native error/custody/diagnostic/account producers and cannot be proved by TypeScript shape or throwing a synthetic exception before any native work.


### Selected reference owned-lease qualification (planned OL-01–04)

Qualify the CONTRACT-007 adapter-private lease separately from adopted host transactions. Pin actual driver/pool/version, original issuer/arbitration, native cycle/termination/descriptor and session-cleanup producers. Use independent command and lease-return observations, plus an outside database observer for committed effects. All cases remain not_run.

| Case | Controlled schedule | Required result |
| --- | --- | --- |
| OL-01 exclusive admission | Expose an independently submitting physical-client alias before BEGIN, then request owned execution | Refuse that lease/profile before BEGIN or callback invocation; locking only Truss methods does not establish command exclusivity |
| OL-02 one command queue | Submit concurrent callback operations and cancellation/control requests; pause one native cycle before completion | All commands retain original queue/epoch/ordinal association; no overlap or reordered settlement. Cancellation closes admission while original pending work remains under recovery, with no callback replay |
| OL-03 committed cleanup failure | Independently confirm COMMIT and committed state, then fail drain/session reset/pool bookkeeping | Preserve the existing ok outcome with original callback value and durability committed, quarantine the actual lease and prove zero pool return/reuse. Injected drain/reset/release exceptions cannot overwrite retained COMMIT confirmation or produce retry, rolled_back or commit_unknown. Retain bounded authorized internal recovery evidence without exposing a raw lease |
| OL-04 unknown settlement | Lose COMMIT or rollback completion, or retain unresolved native termination; attempt another owned transaction | Original outcome/recovery custody remains unresolved; no pool return, guessed idle epoch or callback reapplication. A fresh physical lease has separate incarnation/epoch and cannot redeem the old handle |

Also require zero raw-client/release exposure from public callback handles and explicit confirmed settlement/drain/session cleanup before normal pool return. Do not treat pool callback completion, an idle-status byte or after-state absence as proof of original COMMIT/rollback. This owned-path qualification does not admit arbitrary adopted-host command paths.


Extend OL-04 with disposal while a native cycle or COMMIT completion is unresolved. Retain the same original adapter recovery lease after facade closure, reject a replacement facade/pool borrower, and prove no pool return on close-request acknowledgment or timeout. Independently confirm physical termination: physical lease custody may retire while the earlier unknown COMMIT outcome remains unresolved. Saturate the selected bounded recovery capacity and require refusal before another pool acquisition, without deleting old outcome/lease evidence. All cases require actual driver/pool/account/termination producers and remain not_run.


### Owned-lease resource boundary qualification (planned LR-01–03)

LR-01 independently occupies all 64 reference lease slots using a mixture of active, queued/uncertain acquisition and quarantined clients under one original executor. Attempt the 65th admission through a second assembly: require refusal before any pool acquisition/native BEGIN and no old slot eviction. Confirm one physical termination and allow fresh admission only after its lease occupancy release is independently observed; do not release its unresolved settlement record. Smaller actual pool/host limits take precedence, so the fixture must select a compatible test pool rather than infer 64 deployed connections are supported.

LR-02 retain 128 original settlement records while their physical leases have been confirmed retired. The 129th required reservation refuses before pool acquisition even with zero active leases. Actual original resolution plus discharged retention obligations may release a record; facade disposal, elapsed age and confirmed physical termination alone cannot. Record exact full original identities and compare that no older unknown outcome is transferred to a replacement issuer or truncated to make room.

LR-03 independently account source/retained copies at the 65,536-byte per-record and 8,388,608-byte aggregate ceilings; exercise one-over and simultaneously retained copy variants. Require refusal before the next unbounded acquisition/materialization, never after truncating original evidence. A future record’s complete worst-case custody bound must be reserved before native BEGIN; missing producer bounds refuse without work. Record-count and byte ceilings are conjunctive, so tests cannot reset or ignore one to manufacture success at another. These are planned adapter/account/retention tests; no source policy or counter mock establishes actual native lifetime/copy qualification.


Extend OL-01/LR-01 with pool completion barriers immediately before and after original acquisition deadline/cancellation/disposal. A late client must produce zero BEGIN/callback calls and remain under original cleanup custody; failed cleanup quarantines it. A timeout before client delivery retains the original capacity reservation and issues zero phantom release/replacement-acquisition calls. Qualified confirmed no-client cancellation may release reservation; confirmed late-client cleanup may release its actual lease. Independently observe each original pool request/client association and arbitration ordering. The 30,000ms reference limit is public waiting, not proof of native resource release. These adapter/pool cases remain not_run.


Extend OL-03 with distinct pool baselines and independently introduced role/setting/prepared-state residue. Confirm outer settlement, then omit a required baseline observation or fail a selected restoration command: require quarantine and zero pool return while retaining committed outcome. Verify transaction-local origin is restored at each operation boundary and absent from the next admitted borrower under actual native observation. A blanket reset with mismatched driver prepared-state custody cannot satisfy cleanliness. These selected baseline/driver/session cases remain not_run; equality of a subset of settings is insufficient.


Plan SB-01–03 for the PostgreSQL 17 owned-session baseline floor. SB-01 supplies equal textual search_path on two actual role/namespace contexts with differing resolved current_schemas or dependency identity; require original correspondence refusal before protected work rather than string-only acceptance. SB-02 independently changes session_replication_role to an incompatible integrity mode, or grants a role an unqualified bypass path; require admission refusal even when that value matches the pool baseline. Restoring a matching settings string cannot establish effective RLS/trigger/FK authority. SB-03 changes a required decoding/timeout/default-transaction observation, omits transaction_timeout under a substituted engine version or returns a native NULL/unsupported descriptor; require explicit version/profile refusal or unavailable observation before interpreting it as a default. Verify complete original values, actual allowed transaction-local changes, native descriptors and after-settlement comparison; no baseline overwrite or arbitrary session reset supplies the expected evidence. All cases remain not_run and require actual driver/server/profile producers.

## Selected driver predecode and protocol-capture qualification

DH-01–DH-05 qualify the two integration boundaries identified by CONTRACT-007’s frozen node-postgres review and the [driver handoff](../../02-design/contracts/reference-driver-hook-review.proposal.md). All are `not_run`. Use a controlled protocol peer for independently authored wire bytes and a real PostgreSQL fixture for successful transaction semantics; neither peer-only parsing nor successful driver queries establish the whole adapter profile. Pin the actual driver/runtime/transport hook and complete dependency tuple in every receipt.

| Case | Independent stimulus and observation | Required result |
| --- | --- | --- |
| DH-01 / `predecode_frame_and_utf8_admission` | Split each selected RowDescription/DataRow/CommandComplete/ReadyForQuery packet across header, field-length, UTF-8 and terminator boundaries. Include valid replacement-character bytes, SQL NULL versus empty text, invalid/overlong UTF-8, missing cstring terminators, truncated fields and inconsistent field counts. Observe the selected hook before parser allocation and decoding. | Valid fragmentation preserves exact cells/control text. Invalid bytes/framing refuse before publication; a decoder replacement character cannot repair invalid source. SQL NULL remains distinct from empty bytes. The original cycle enters containment with no pool return until actual end is known. |
| DH-02 / `allocation_before_retention_and_growth` | Instrument original ingress, retained fragments, parser capacity growth and overlapping copies. Submit oversized declared frame, unfinished frame, repeated fragments and a small wire payload causing larger growth capacity. Compare allocation order against the original shared account using a separate ledger observer. | Admission precedes each controlled allocation/retention; full physical capacity/overlap is charged. Unknown socket/parser producer bounds refuse profile admission. No post-row size check, fresh per-chunk budget or early refund substitutes for preallocation custody. |
| DH-03 / `original_completion_metadata` | Supply independently authored command counts above JavaScript’s safe integer range, ordered descriptors and native ready statuses; compare private captured metadata with original wire bytes and public Result conversions. Inject extra completion, missing ready, foreign cycle and stale descriptor. | Exact original count/tag/descriptor custody survives conversion. Unexpected native sequence cannot produce success. Ready status alone never proves commit; only the original confirmed COMMIT cycle does. A fabricated count peer case is transport evidence, not proof that PostgreSQL executed that number of effects. |
| DH-04 / `cancel_rejection_is_not_native_end` | With native barriers, reject the query promise or acknowledge cancellation while the original server cycle remains in flight; then separately confirm rollback, commit or terminate with an unresolved COMMIT. Attempt pool reuse and duplicate adoption through another facade throughout. | No premature custody release or fresh epoch. Confirmed commit preserves the original committed outcome even after cancellation; unknown COMMIT remains unknown after physical termination. Adopted transactions receive no engine outer COMMIT/ROLLBACK. |
| DH-05 / `hook_lifetime_and_build_substitution` | Register capture after submission, replace a hook/dependency build, enable pipelining or expose an unmediated raw-client alias; attempt a query under the retained prior profile. Also instrument direct per-query identity parsing/array rows without predecode admission. | Admission fails before dependent work for a known incompatible profile; no mutable private-field repair. Earlier unresolved work remains in original recovery custody. Raw/array convenience alone cannot make the profile available or overwrite original evidence. |

Receipts must distinguish observer-controlled peer bytes, actual native effects, driver-public conversions and the original private capture. Expected wire values come from the peer specification; native transaction outcomes come from independent server/connection evidence. Each case retains resource/cycle observations through containment, plus zero unauthorized replacement acquisition, pool return or public success. Existing OL/LR/SB cases remain required for full owned-lease/session qualification, and adopted host mediation remains a separate gate.

### Original parser and backing-allocation controls (planned)

Extend DH-02 in its existing native driver test file and US-044 allocation. Use independently authored complete frames plus fragmented ingress, and separately instrument the actual pinned parser/allocator rather than accepting adapter-reported byte totals as the oracle.

- At the frozen mergeBuffer geometric capacity equality boundary, demonstrate that a late frame-length observer cannot prevent the prior growth/copy. The selected pre-parser integration must either keep parser residual zero before/after each admitted complete frame or pre-admit the exact observed residual/growth path. Complete frame size alone is insufficient.
- Deliver two complete frames in one admitted ingress chunk and retain differently sized views of the same original backing allocation across capture/parser/publication. Verify one complete physical backing charge, correct individual span/work counters, and no refund while any required alias survives. Repeat with two genuinely independent backing allocations whose identical bytes cannot merge their custody.
- Exercise the isolated-copy path with source/destination overlap and one-over total capacity. Refusal precedes controlled copy/allocation; dropping a reference or substituting a smaller visible slice cannot pass the physical bound. Qualify runtime allocator retention/reclamation separately rather than assuming immediate garbage collection.
- Substitute a hook installed after Parser.parse or Query/Result conversion. It must fail original-source/allocation qualification despite correct decoded rows. Retain actual original command count text, descriptors, ready status and cycle/termination evidence; failure does not grant pool release or automatic replay.

These controls remain not_run. Controlled peer tests establish framing/instrumentation behavior only; actual server/TLS/runtime/driver/account and transaction schedules are still required for the complete selected adapter tuple.


### Packed assembly recreation with unresolved original recovery

Run two clean packed consumers against the same host-owned recovery registry and independently selected native composition. Consumer A creates assembly A, adopts the host's actual transaction and stages a qualified operation. Lose the operation/cleanup acknowledgment at the selected original phase so the outcome/resource remains unresolved, with complete original issuer/epoch/context, operation and recovery obligation. Record original pending host sentinel and native ownership independently. Close A's new admission and dispose it through the public facade. Retained facade/scope handles refuse new work without SQL; disposal does not end the adopted host transaction, fabricate rollback or erase the recovery obligation. Independently show the unresolved physical resource cannot return to the pool.

Consumer B creates fresh assembly B through packed public exports using the same host registry. Construction is inert and cannot adopt A's issuer, operation ordinal or quarantined connection merely because registry identity, profile pins or native backend labels match. Passing A's scope/facade/observation as B's fresh admission refuses; creating B must not clear A's unresolved recovery entry. B may use an independently admitted unrelated resource while A remains unresolved, provided shared host arbitration and original resource ownership remain complete. Absence of A's registry entry in B's local memory is not settlement or permission to reuse it.

Settle A only through the original qualified host recovery path with complete original transaction/containment/outcome correspondence; append observations without rewriting the earlier result. Confirmed host rollback removes the original pending operation and sentinel; a committed outcome requires its own original evidence. Only independently proved termination/release permits the original resource's later reuse under a new admitted lifetime. Native termination with unknown commit cannot produce a replay/committed result. B's separate successful work cannot resolve A. Retain complete registry/native/pool and public consumer observations across both assembly lifetimes.

This supplements US-044 lifetime/rollback controls and B-014 packed delivery; it does not add a registry implementation to Truss or a new recovery API. Host registry lifetime remains host-owned under the architecture. Repeat per actually selected adapter and keep constructor/import checks separate from native outcome evidence. The scenario is not_run.
