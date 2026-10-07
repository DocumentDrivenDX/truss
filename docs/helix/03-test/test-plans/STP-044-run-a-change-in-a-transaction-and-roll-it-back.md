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
