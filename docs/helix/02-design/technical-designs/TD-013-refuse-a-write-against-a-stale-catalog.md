---
ddx:
  id: TD-013
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-013
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
---

# TD-013: Refuse stale catalog writes

**Story:** [[US-013]]. **Parent:** [[SD-003]]. **Feature:** FEAT-003.

## Technical Approach

Use the single mutable head row and locking protocol in CONTRACT-001/004. The writer's first catalog/data lock is the shared head check; acceptance holds its exclusive head lock through persistence and commit. An old pin observed before locking is refused at READ COMMITTED after a newer acceptance. A REPEATABLE READ snapshot established before the head update exercises the native serialization outcome when attempting the locking check. Acceptance cannot replace a head while a writer already holds its shared lock.

The optional queue is not implemented by a process-local mutex: independent hosts must share its admission boundary. Consume CONTRACT-003’s proposed transaction-scoped advisory prelude and original admission/reentry/unknown-state procedure. Exact native mechanism, participating-path coverage, fairness/wait behavior and caller-savepoint/timeout realization still require adoption and qualification before AC3’s 50 ms guarantee is executable. Preserve the requirement as gated, not deleted.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/catalog/head.ts` | Shared/exclusive head checks, pin comparison and native error mapping | US-013-AC1, US-013-AC2 |
| `packages/postgresql/src/catalog/accept.ts` | Lock timeout, rederive/revalidate against the locked current head | US-013-AC3, US-013-AC4 |
| `tests/catalog/races.test.ts` | Explicit multi-client interleavings and state assertions | All criteria |
| `tests/benchmarks/catalog-admission.ts` | Continuous-writer and qualified optional-queue wait measurements | US-013-AC3 |

Head gating and optional prelude compose through the existing catalog admission/executor components; exact native implementation remains unfinished. The authored shared prelude is a candidate, not a second process-local queue or measured fairness guarantee.

## API/Interface Design

CONTRACT-001/004 own locks and stale/retry kinds; CONTRACT-003 owns acceptance; CONTRACT-007 owns caller/owned transaction scope. Queue configuration and admission semantics must be specified in a contract before implementation, not defined as a local API here.

## Data Model and Integration

Use the existing head row, never append-only revision rows as the lock target. Proposed acceptance data may be prevalidated, but must be revalidated against the head it actually locks. Two acceptances serialize; the second may refuse incompatibility rather than automatically succeed. Every mutation uses this gate before graph locks under CONTRACT-009.

## Security and Performance

Host owns connections and timeout policy within the published profile. Writers cannot bypass the head check through another public mutation path. Parameterize catalog operations and preserve acting-role context. Capture lock acquisition wait separately from validation/persistence duration; optional queue timing starts at its contract-defined admission boundary. Sustained-load tests record failures and starvation, not just successful request medians.

## Testing

STP-013 owns the four criteria. Use barriers before the locking head check, after lock acquisition and before acceptance commit. Independent observers assert head and graph/journal state. A supplementary held-share-lock case proves acceptance waits. Under transaction-fatal serialization, caller whole-transaction retry belongs to the host; savepoint rollback cannot be assumed sufficient.

## Migration and Rollback

No schema change. Failed acceptance leaves head/catalog/data/journal unchanged. Lock timeout rolls back the attempt; no retry inside an unusable transaction. Retain prior qualified protocol and reject unsupported isolation/context rather than substituting advisory-only protection.

## Implementation Sequence

1. Write deterministic RC/RR and dual-acceptance red tests with observed locks.
2. Implement head gating/revalidation and error mapping through the common executor.
3. Adopt/implement the existing optional shared admission prelude under exact original native/driver/privilege profiles, then qualify its complete sixteen-writer timing and failure schedules.
4. Review every public write for gate coverage and native evidence.

## Risks and Gates

US-013's walkthrough explicitly places acceptance between pre-lock observation and locking admission; the held-share-lock control separately proves acceptance waits through outer termination. A mid-held-lock head replacement is impossible under the contract. The optional queue/prelude procedure and timing observation candidate are authored; actual cross-host fairness, realizable original custody and the selected workload/measurement profile remain unqualified. Exact stale/error precedence inherits US-012. No language-neutral correctness claim follows from one adapter's lock test.


## Proposed optional-queue timing observation protocol

US-013-AC3 retains its 50 ms continuous-sixteen-writer requirement. Define candidate measurement truss-catalog-admission-wait/0.1.0 around the complete admission path: t0 is original acceptance submission to the registered optional admission service, before its first enqueue/lock/native wait; t1 is receipt of the original confirmed queue/head admission result on the same owned transaction. Use one qualified harness monotonic clock, not application timestamps or subtraction across unsynchronized host/server clocks. The measured t1-t0 includes queue transport/service delay, preexisting writer drain and exclusive head acquisition. Validation/transforms/persistence after admission are separate duration fields. No timer reset at queue ownership or after retries removes an earlier wait.

This conservative end-to-end admission interval may overestimate native lock wait; passing the entire interval within 50 ms supports the wait upper bound for that exact case. If native head acquisition is established before a delayed/lost reply, preserve the separately bracketed native observation, but do not manufacture a successful caller-observed duration or substitute it for this profile. Unknown admission/termination is unverified/interrupted evidence, not zero wait or discarded sample. A new admitted retry is a distinct sample tied to its original prior failure; report all failures/retries and complete original wait observations.

The qualified workload pins sixteen independent actual writers, exact operations/data sizes/transaction ownership and hold-duration policy, all participating admission paths, acceptance request sequence, server/adapter/pool/runtime/host deployment, warmup/repetitions and independent barriers. Every claimed bounded wait is assessed across all required measured acceptance attempts; medians/percentiles cannot replace the per-attempt bound. Report absolute worst observed wait, full raw samples, timeout/cancel/starvation/unknown counts and complete elapsed coverage. Qualification remains limited to the declared workload/environment; arbitrary host-owned transactions can retain share locks beyond a call and cannot inherit a universal 50 ms bound.

The queue still requires a separately defined cross-host fairness/admission/abandonment/native exclusion protocol. A timing profile neither implements that queue nor proves fairness from observed favorable scheduling. Preserve core head correctness and explicit timeout/retry without the optional queue. This proposal needs product/performance review; it does not change AC3, narrow its sixteen-writer workload to process-local callers or claim passing measurements.


CONTRACT-003 now proposes truss-catalog-advisory-prelude/0.1.0 for the optional queue: original database-wide advisory identity, transaction shared/exclusive pre-head stage, full participating path inventory, no post-effect upgrade and original timeout/savepoint/termination custody. It retains mandatory native head freshness. The candidate is an adoption design, not proven native fairness; exact native callable/grant/held-state/resource profiles and complete sixteen-writer timing evidence remain open.


Optional admission belongs to original native transaction/generation, not each public call. CONTRACT-003 now specifies initial/reentry/unknown states, retained original admission for sequential host calls, incompatible session holds and full transaction drain timing. Host/executor coordination must preserve original acquisition/savepoint/termination custody; pg_locks presence alone cannot prove the required acquisition history. Exact native/pool/registry profiles remain adoption dependencies.


Timeout integration consumes CONTRACT-007 original native setting capture/authorization/deadline/restoration. Native lock_timeout is per acquisition, so advisory and head waits cannot reset the original complete admission deadline. Preserve stricter active host settings and prior SET LOCAL/savepoint semantics; uncertain restoration remains original recovery. Exact parameterized native setting/rollback/cancellation and measurement profiles are A2/A4 outputs; configured timeout text is not measured fairness/latency evidence.
