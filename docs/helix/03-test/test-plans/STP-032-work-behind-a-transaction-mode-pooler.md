---
ddx:
  id: STP-032
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-032
      kind: informed_by
    - id: TD-032
      kind: informed_by
    - id: SD-008
      kind: informed_by
---

# STP-032: Transaction-mode pooler

## Story Reference and Scope

US-032, TD-032, SD-008, TP-001 and CONTRACT-007. Tests are planned; qualify actual connection profiles and both execution modes.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-032-AC1 | `pooler_corpus_has_no_session_dependency` | Complete selected corpus passes with backend rotation between transactions and no role/origin leakage to another borrower | `@covers US-032-AC1` | Native integration | `tests/host/pooler.test.ts`; real transaction-mode pooler |
| US-032-AC2 | `unprepared_profile_preserves_corpus_results` | Prepared-disabled corpus matches independent expectations and reports unprepared mode; injection-like parameters remain data | `@covers US-032-AC2` | Native integration | Same file; explicit disabled preparation |
| US-032-AC3 | `paired_point_reads_meet_incremental_cost_bound` | At 1,000 types, agreed paired-cost statistic is at most 0.05 ms; raw samples/configuration accompany verdict | `@covers US-032-AC3` | Performance integration | `tests/performance/unprepared.test.ts`; matched plans/data and agreed statistic |

## Data, Failure Probes and Executable Proof

Pin adapter/server/pooler configuration, capability and corpus manifest. Independent observer confirms transaction boundaries, backend identity and state after commit/rollback/cancellation. Force multiple physical backends, reuse one for different roles and test caller adoption without connection release. Assert exact numeric/null results as well as operation outcomes. Missing corpus cases block completeness; two equally wrong modes cannot pass by agreement alone.

Future commands `bun test tests/host/pooler.test.ts` and `bun test tests/performance/unprepared.test.ts` require implemented files/harness. Preserve timing samples, failures and preparation reporting. Report unsupported prepared combinations explicitly. No performance pass until statistic, environment and repetitions are fixed before measurement.

## Recovery-registry pooling supplements

Force a different native backend for the reconciliation transaction after an interrupted original call. Preserve exact registry target/attempt evidence, re-establish transaction-local role and reject session-variable/temp-object dependence. Run prepared and unprepared variants. Native backend PID reuse or an empty result on a newly assigned backend cannot alone resolve original termination or authorize replay. Confirm that registry integration does not pin a transaction-mode pooler connection beyond the admitted transaction or leak the old role into the next borrower. A direct-connection pass does not close these pooler cases.

## Build Handoff

Resolve pooler/profile and measurement gates, implement red tests, then adapters. All three criteria block story closeout. A native direct-connection pass remains separate evidence.

Shared execution-failure check: `bun docs/helix/04-build/evidence/design-audit/check-execution-failure.ts <Ajv Draft 2020-12 module path>` passes ten shape cases. Independently refuse false SQLSTATE classification, unknown commit promoted to rerun and nontransactional job uncertainty promoted to whole-transaction retry. Verify current diagnostic disclosure and no credential/connection/handle exposure; original protected recovery evidence remains exact. Shape cannot prove actual native cleanup or classification.

The fixed diagnostic candidate in CONTRACT-007 requires hostile exception objects (throwing getters/toJSON, nested causes and oversized sensitive messages), exact public-code/message pairing, optional native-code omission and complete canonical wire bounds. Native schedules must preserve commit/containment precedence under those same failures and keep exact original evidence in host custody across backend rotation. Producer checks do not qualify adapter mapping or recovery.

Producer-integrity schedules additionally fault diagnostic admission before submission, the surviving producer after submission, sent-COMMIT observation and post-confirmed-COMMIT bookkeeping. Assert no invented unavailable Outcome branch, no downgraded commit uncertainty, no automatic replay and no pool reuse after fatal transport failure. A broken-transport Promise rejection is missing conforming outcome evidence; independent native observation and original recovery custody determine effects.

Adoption arbitration schedules use two wrappers around one original host transaction, concurrent asynchronous adoption, original host end during observation, same-connection later generation, host statements racing an active Truss call, and disposal while containment remains unresolved. Verify duplicate refusal preserves the first handle/earlier host work; host exclusion is real beyond the adapter mutex; old savepoints/handles cannot attach to the new generation; unresolved custody survives disposal without caller connection release or transaction end. Exact native profile recognition is required, so mocked wrapper identity alone cannot close these cases.

Operation-admission scenarios must also show sequential host write → Truss call → host write → Truss call succeeds through one original handle without detach or re-adoption. Race different capability calls on that handle and prove refusal before interleaving; verify a group's internal executor/savepoint calls use its original private token without recursive acquisition deadlock. Cancellation delivery alone cannot free the token; known operation-local containment permits subsequent host work, whereas unresolved containment prevents reuse. No mock mutex pass qualifies host-side coordination.

Arbitration integration must use two distinct assemblies/capabilities sharing one executor-issued original transaction. Prove one original public-operation registry and separate short native-call guards: concurrent public calls refuse, internal sequential executor calls complete, and no AsyncLocalStorage/thread identity/caller reentrancy flag is required. A per-assembly WeakMap or added token hidden in an unqualified driver wrapper cannot substitute for the selected original composition integration.

Arbitration lost-reply schedules require a returned original prepared attempt before acquire, then faults before/after atomic admission. Repeated acquire/observe cannot mint a second lease; observe of undecided work cannot acquire; definitive busy refusal permits only an explicitly new attempt; released original attempts cannot resurrect authority. Exercise disposed prepared attempts, cleanup observation after disposal, missing/foreign attempt custody and bounded preparation refusal before ownership.

Prepared cleanup/resource tests race acquire with abandonPrepared and assembly close, fill exact prepared/retained/lease/byte limits, and exercise one-over refusal before ownership. Ensure unresolved and closed retained records stay charged, cleanup capacity survives saturated admission, stale reclaimed handles cannot reacquire, and a lost acquire reply never permits prepared abandonment. Native recovery after process crash is separately qualified; registry bounds do not prove RSS/GC limits.

Capacity scenarios distinguish per-attempt and aggregate limits: filling attempts with maximal metadata must refuse before exceeding aggregate bytes even below 4096 records. Fill 64 active/unresolved leases, then acquire a previously prepared attempt; assert definitive recorded resource refusal and no native call, later capacity release cannot change that original refusal. Exercise 64 concurrent maximal completion buffers with exact reservations and no concealed host/native copies; register the 65th assembly only as resource refusal. These limits are independent ceilings, not simultaneous achievable maxima.

Completion admission tests omit an original native call/savepoint/coordinator resource, substitute a later transaction generation, forge original evidence references, conflict duplicate completion bytes and claim idle after known unusability. Verify native transaction end does not imply cross-connection coordinator cleanup; unresolved resources retain the original lease. Completion bytes precede registry closure evidence and cannot contain a future release hash. Independent original native-call inventory must detect omission even when the authored completion shape is valid.

Separate confirmed original termination with unknown COMMIT outcome from uncertain native termination. In the first schedule, permit ended-generation lease closure only after all owned/coordinator containment, retain commit_unknown and exact recovery records, and forbid replay/old-handle reuse. In the second, preserve unresolved lease/quarantine. Confirm that capacity refund removes only released resources and that outcome evidence/retained attempt charges survive either path.

Private arbitration declaration consumers: strict TypeScript compilation of bindings/truss-operation-arbitration-v0.1.typecheck.ts rejects attempt-as-lease, lease-as-attempt, forged attempt/registration metadata, unresolved admission with a usable lease and empty recovery inventory. Six negative controls pass; they do not prove original issuer recognition, runtime ownership, native state or race behavior. E06's exact original integration and E04's native observation remain required.

Completion wire check: `bun docs/helix/04-build/evidence/design-audit/check-operation-completion.ts <Ajv Draft 2020-12 module path>` passes 12 discriminant/closed-field cases. It rejects caller commitment, missing termination for unknown commit, future release hash and unresolved completion. Foreign generations, omitted resources and forged termination references deliberately pass shape and require independent original issuer/ledger/native evidence refusal. This distinction blocks schema success from qualifying release behavior.

Process arbitration store schedules inject faults immediately before/after immutable-root replacement, race acquire/abandon/close and release a stale generation. Independently inspect original root sequence/phase/issuer indexes and exact counter transitions; no callback/await/native statement may run in the critical section. Two isolates with copied registries must remain unsupported unless routed through the same original service or a separately qualified atomic-store profile. Process-store observation does not prove host statement exclusion or native termination.

Unresolved attempt cases must retain exact last-confirmed phase/evidence. Lost admitted reply cannot rewrite the root to prepared; lost closed reply cannot reopen it; missing evidence cannot fabricate preparation. Independently verify admitted lease/native custody persists without a disclosed usable lease and conflicting later metadata does not replace original lineage. Shape-valid last-confirmed assertions still need actual issuer/root observation.

Attempt wire check: `bun docs/helix/04-build/evidence/design-audit/check-operation-attempt.ts <Ajv Draft 2020-12 module path>` passes 12 state/closed-field cases, including forbidden prepared/closed lease disclosure, missing last-confirmed evidence, empty recovery and future-state hash. Forged acquisition and false last-confirmed history deliberately pass shape; original issuer/root/transition admission must independently refuse them. No wire record grants opaque attempt/lease authority.


## Layered deadline precedence

Planned native/adapter cases trigger lock, statement, supported transaction/session, idle, request/transport and host lease deadlines independently and in paired races. Record original scope/start/connection generation and native effects/statement/transaction termination independently. Unsupported version setting differs from unavailable observation and disabled zero. Host transaction already older than a configured Truss duration cannot obtain a fresh native lifetime by adoption.

Race deadlines before submit, during native effect, at commit submission/acknowledgment and after confirmed commit during cleanup. Assert existing executor classification with honest original outcome, no automatic retry or new timeout code, no guessed savepoint reuse/session rollback, and retained quarantine/recovery for unknown active work. A client request rejects while the server query continues: pool reuse/replacement connection cannot conceal it. Earlier host writes survive confirmed operation-only restoration; independently confirmed whole native transaction termination is reported separately. Driver/server/pool clock observations remain distinct, never subtracted across unqualified clocks. All cases are planned until exact native target/adapter/pool profiles exist.


Caller retry classification regression: inject independently observed serialization/deadlock completion with known failed original transaction state and no unresolved cleanup/commit outcome. Expect retry with whole_transaction scope, no Truss whole-host rollback/callback rerun and no ordinary admission through that failed generation. The host separately ends/restarts its complete transaction. Contrast native error identity without confirmed statement termination/state, which retains original unusable/recovery custody; operation-local recovery cannot convert the restart instruction into statement retry.


## Backend rotation versus live-context affinity

Independently observe native transaction/backend generations for two completed ordinary transactions and force rotation between them. Then hold one caller-owned transaction through host write, Truss mutation, direct page and next Truss operation: each must use its original native transaction and exact admitted principal/context. Attempt to continue its handle or held-snapshot cursor on another backend before completion; refuse before native work, without committing or ending the original transaction. Backend PID equality alone is insufficient identity because PIDs can be reused.

Repeat with preparation disabled and with each explicitly selected prepared protocol. Reuse a pooled backend after confirmed rollback/cancellation containment for a different admitted principal and independently observe no origin/configuration/temporary-state leakage. If original statement or termination remains unknown, quarantine it rather than returning it to the pool or silently substituting a fresh connection. Administrative install/upgrade uses its separate dedicated ownership procedure; an incompatible pooled administrative configuration refuses before DDL. The complete corpus retains all applicable cases and records unsupported combinations explicitly rather than dropping them to obtain a pooled pass. These are planned native integration controls, not a pooler support claim.
