---
ddx:
  id: STP-013
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-013
      kind: informed_by
    - id: TD-013
      kind: informed_by
    - id: SD-003
      kind: informed_by
---

# STP-013: Refuse stale catalog writes

## Story Reference

US-013, TD-013, SD-003, TP-001 and CONTRACT-001/003/004/007/009. Planned tests are not evidence of a qualified protocol.

## Scope and Objective

Prove head pinning across isolation levels and serialized acceptance. Optional queue performance remains gated by its future shared contract.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-013-AC1 | `rc_old_pin_refused_before_graph_effects` | Acceptance commits after old unlocked observation but before writer head lock; writer observes new head/refuses old pin; graph/journal unchanged | `@covers US-013-AC1` | Native integration | `tests/catalog/races.test.ts`; independent clients/barriers |
| US-013-AC2 | `rr_old_snapshot_requires_whole_retry` | Establish old snapshot, commit acceptance elsewhere, then locking head check produces native serialization/retry and no committed effects | `@covers US-013-AC2` | Native integration | Same file; explicit REPEATABLE READ |
| US-013-AC3 | `continuous_writers_admission_is_bounded` | Sixteen continuous writers coexist with completed acceptance and observed lock timeout; optional qualified queue wait meets 50 ms under declared boundary/load profile | `@covers US-013-AC3` | Native performance integration | `tests/benchmarks/catalog-admission.ts`; shared queue contract required |
| US-013-AC4 | `second_acceptance_validates_new_head` | Concurrent proposals serialize; second uses first committed head, accepting or refusing according to updated validity; no revision collision | `@covers US-013-AC4` | Native integration | `tests/catalog/races.test.ts`; compatible and incompatible proposals |

## Executable Proof

Future commands `bun test tests/catalog/races.test.ts` and `bun tests/benchmarks/catalog-admission.ts` require committed harness/files. Each test carries its criterion citation and exact server/adapter/isolation pins. AC3 cannot be declared passing before admission/statistic semantics are settled.

## Data and Setup

Separate catalog lock wait, shared admission queue wait and end-to-end acceptance duration. The optional 50 ms queue target cannot be substituted for native lock timeout or complete acceptance time. Register queue-entry/admission events from the shared mechanism, writer transaction/hold-time distributions, offered arrival rate, acceptance frequency, measurement interval and timeout/retry classification. Sixteen clients alone do not define sustained load; retain completed and failed attempts with actual concurrency/lock witnesses. Independent host queues cannot claim a global admission bound. Before a pass, select the queue protocol and target statistic explicitly; native stale-head correctness remains independently testable without that optional mechanism.

Use explicit barriers and inspect native lock state. The separate held-share-lock fixture must prove acceptance waits until writer completion. Observe head/catalog and canonical/journal state independently. Record benchmark wait distributions, timeout failures, starvation and full run configuration; do not count retries as one successful bounded wait.

## Edge Cases and Failure Modes

Acceptance timeout leaves old state; writer cancellation releases owned scope correctly; caller-held locks persist until host commit/rollback. Two independent host queues must not bypass shared admission. Snapshot/lock interleavings are asserted, never inferred from sleeps. A failed second proposal cannot partially change the head.

## Build Handoff

Write red native interleavings, implement head gating and second-proposal revalidation, then define/qualify shared optional queue behavior. All criteria and held-lock supplement block story closeout for the complete profile. Without queue evidence, report that optional guarantee unverified rather than silently removing it.


## Optional-queue timing evidence

Implement the proposed TD-013 complete admission timing protocol with one independently qualified monotonic harness clock. Barrier controls prove t0 precedes enqueue/native wait and t1 follows original exclusive head admission. Hold an existing writer past 50 ms and require that sample to fail the bounded workload profile or be explicitly outside a predeclared host-hold profile; never start the timer after it drains. Add delayed/lost queue/head replies, timeout/cancel, retry and actual cross-host writers. Preserve all original samples and unknown attempts; percentiles, omitted failures and per-process mutex timing cannot qualify AC3.

Native admission/transaction evidence establishes the schedule separately from timing. A queue ownership event alone is not head admission, and a library return alone cannot prove original head remained held. Validate exact workload/native configuration and raw sample inventory independently. The future benchmark remains blocked on queue protocol and product/performance profile review, not marked passed by this measurement design.


Optional prelude schedules hold an earlier shared transaction, queue exclusive acceptance and then start later shared writers across independent hosts. Independently establish ordering/wait/drain and eventual exclusive admission after original holders terminate; a same-process mutex cannot establish it. Exercise another installation using the exact database-wide identity and preserve its contribution to the declared cohort/timing. Inject unparticipating granted writer, post-effect shared-to-exclusive upgrade, changed identity on retry, savepoint rollback, timeout/cancel and lost native reply. Qualification fails or remains unverified as appropriate; mandatory head checks are never omitted to improve the queue benchmark. Planned tests must pin actual native lock ownership/termination and all original attempts.


Original-transaction reentry cases perform two sequential Truss calls plus host writes while exclusive acceptance waits. Require retained original shared custody, no fresh queue acquisition after lower locks, no host commit and complete hold duration in acceptance wait evidence. First optional admission after unsafe earlier host locking refuses that profile while preserving earlier host work. Lost initial acquire reply stays original unresolved, not replaced acquire.

Place a session-level hold on the exact queue identity, including a hold surviving transaction rollback/pool return, and verify the next transaction cannot infer original admission from pg_locks/connection identity alone. Mixed session/transaction reentrant calls while another exclusive waiter exists must fail the profile's custody/control admission rather than be a fairness pass. Cleanup does not unlock another owner's session state. Pin actual transaction/checkout generations, acquisition/savepoint observations and original native termination independently; matching metadata cannot supply them. These are planned native controls.


Cross-connection queue cases hold original data/migration admission, queue an exclusive acceptance, then make a separate coordinator require admission/head. The composition must reject the unsafe wait dependency before coordinated work; no timeout-based deadlock escape may count as successful qualification. Repeat with policy guard already held on coordinator and require rejection of a later earlier-lock acquisition. A separately reviewed acquisition-free observer path requires its own original authority/exclusion oracle. Queue-only and read-only-coordinator-only passes cannot qualify this combined deployment.


Prelude callable cases independently observe the fixed native key, exact shared/exclusive mode and actual native holder/waiter behavior through the intended internal grants. Shared caller cannot invoke exclusive helper; PUBLIC/ordinary caller cannot gain helper-owner authority. Read-only refusal precedes advisory acquisition, and invocation changes no timeout/mode/head/policy state. Result faults include zero/two rows, changed mode/key, NULL, JS-number conversion and extra/duplicate columns; valid negative bigint key remains exact text. Loss after native acquisition retains original unresolved custody; no automatic replacement call, session unlock or cached head success follows. PL/pgSQL body/native grants must be compiled/invoked independently before claiming support.


Timeout ownership cases combine prior host SET LOCAL limits, disabled/native zero limits, stricter statement versus lock timeout, native unit/integer extremes and two separately delayed advisory/head acquisitions. Require one original elapsed deadline, no per-lock reset or host-bound enlargement, and unchanged host settings/scope after qualified operation completion/savepoint rollback. Reject unauthorized setting changes before admission. Inject lost SET/result/restore replies and aborted transaction errors: no guessed restoration/defaults, hidden host rollback or reused adoption; original setting/native recovery remains retained. Confirmed commit followed by cleanup failure stays committed with separate unresolved cleanup. Native setting snapshots/termination and original host writes are independently observed; none of these cases has run for the new profile.
