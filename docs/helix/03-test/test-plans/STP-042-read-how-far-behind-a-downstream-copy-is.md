---
ddx:
  id: STP-042
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-042
      kind: informed_by
    - id: TD-042
      kind: informed_by
    - id: SD-004
      kind: informed_by
---

# STP-042: Feed freshness

## Story Reference and Scope

US-042, TD-042, SD-004, TP-001 and CONTRACT-002/006. Tests are planned. Qualify confirmed source acknowledgment and same-snapshot freshness over every required fact kind in the selected complete-feed profile. Durable downstream application is independently evidenced, not inferred from that acknowledgment; actual native producers remain shared prerequisites.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-042-AC1 | `durable_apply_advances_checkpoint_and_update_time` | Successful durable apply advances position/time atomically; failed apply does not acknowledge | `@covers US-042-AC1` | Native integration | `tests/feed/freshness.test.ts`; independent replica/consumer |
| US-042-AC2 | `lag_uses_earliest_unapplied_publishable_write` | Lag equals observation time minus minimum eligible unapplied at, not newest write or heartbeat | `@covers US-042-AC2` | Native integration | Same file; known native timestamps/checkpoint |
| US-042-AC3 | `held_committed_changes_are_separate_from_publishable_lag` | Older open transaction holds later committed changes; held state is separate and clears after blocker ends | `@covers US-042-AC3` | Native concurrency | Same file; explicit transaction/watermark barriers |
| US-042-AC4 | `copy_statement_names_actual_durable_position` | Published copy descriptor names its applied position and scope/epoch, never speculative source head | `@covers US-042-AC4` | Contract | Same file; independently expected replica descriptor |

## Data and Failure Probes

Checkpoint race probes use two workers with the same expected prior boundary: one advance succeeds, the other conflicts without overwriting. Equal acknowledgment is idempotent; reverse acknowledgment refuses; earlier delivery replay leaves the durable checkpoint unchanged. Wrong epoch/profile and unknown consumer cannot auto-register or reset. Crash after downstream apply before source acknowledgment resumes through durable dedup; crash before downstream commit cannot advance the source. A speculative high position with no complete application evidence refuses, independently of whether a stored checkpoint lies ahead of a later observer's watermark.

State discrimination probes require genuinely empty scoped backlog to differ from unauthorized scope, retained gap, wrong epoch, missing consumer and failed observation. None of the unavailable cases may return zero-lag success. An empty publishable set with held committed rows must retain the held state. A long adopted transaction uses observation time rather than transaction-start now(); injected negative clock age produces unavailable rather than zero clamping. Output cannot expose hidden record timestamps/counts. Use the existing complete-feed v0.2 checkpoint/freshness interfaces for side-record freshness; original native producer/profile admission remains unqualified. Do not design a second checkpoint interface or substitute journal-only timing.

Use independently captured row timestamps and exact checkpoint positions. Test no consumer, no eligible rows, ahead watermark, retained gap and unauthorized checkpoint changes. Long caller transaction tests observation clock versus transaction-start time. Concurrent acknowledgment/writer probes ensure one coherent snapshot. Held reporting covers committed visible rows only; do not invent uncommitted row counts.

## Executable Proof and Handoff

Future command `bun test tests/feed/freshness.test.ts` consumes the existing complete-feed freshness v0.2 envelope and requires selected original clock/observation producers and native harness. Retain raw observed_at/oldest_at/positions/watermark with query/profile pins. All four criteria block closeout. Journal lag alone cannot qualify full revision/source/reservation freshness or transport delivery SLA.

## Complete-feed freshness supplements

Include revision-only and side-only transactions with independently captured trusted original write times; missing timing cannot become empty. Authored source.at is deliberately different and cannot affect lag. Seed-represented transactions require persisted classifier/coverage verification before exclusion. Awaiting registrations return unavailable. Verify source acknowledgment descriptor against ahead downstream state without overwriting either. Current authorization gaps remove all protected timestamps/boundaries, and native overflow/cancellation cannot become zero-lag success.

## Fact-clock storage supplements

Capture independent original statement times for every required kind. Repeated identical registration and forced finalizer rebuild retain the first time; savepoint rollback removes it. Add a later member after early finalization and verify any cached transaction minimum is refreshed from complete membership. Legacy missing clocks remain unavailable for complete freshness even when delivery is otherwise qualified. Native tests must establish exact precision and journal-time agreement rather than comparing two calls to the same implementation helper.


## Complete transaction timing and boundary controls (planned)

CF-01–CF-04 use the existing complete-feed v0.2 wire and independently authored
transaction/member fixtures. Each required original member is enumerated before
running the freshness reader; observed reader output cannot define expected
membership or timestamps. These controls remain `not_run`.

| Case | Independent arrangement | Required observation |
| --- | --- | --- |
| CF-01 earliest side fact | One complete unapplied transaction contains a revision fact at T1, reservation fact at T2 and journal change at T3, with T1 < T2 < T3. All are below the watermark, and authored payload times deliberately differ. | Oldest write time is the retained trusted T1; exact age uses the same admitted observation clock. Omitting revision/reservation membership or using payload, heartbeat or journal-only time cannot pass. Repeat with each required kind independently oldest. |
| CF-02 incomplete downstream transaction | Deliver and stage the earliest member, but leave a required sibling unapplied and the downstream transaction uncommitted. Then commit all required members and durable dedup/checkpoint, but lose source acknowledgment. | Neither fragment staging nor downstream-only progress removes the transaction from source-acknowledged backlog. Original source freshness remains conservative until confirmed source acknowledgment; the copy's independently evidenced applied descriptor may be ahead. No partial member acknowledgment or inferred downstream failure. |
| CF-03 exclusive watermark | Independently observe committed complete transactions below and exactly at the safe watermark, where the selected native schedule permits an equal-boundary committed transaction. Also hold an earlier transaction open with uncommitted effects. | Only the below-boundary committed transaction is publishable. The equal-boundary committed transaction is held; no uncommitted fact count or timestamp is invented. If that equal-boundary state cannot occur under the selected producer, retain the impossibility evidence and exercise the exclusive comparison with an independent boundary control instead of fabricating native state. |
| CF-04 complete timing versus visibility | Keep complete delivery membership but remove one required original timing association; separately make full membership unavailable through retained loss or denied scope. | Missing timing yields the affected clock-unavailable state; unavailable membership cannot yield present or empty from surviving rows. Scope-level admission failure exposes no protected checkpoint/timestamps. Schema-valid timestamps and a zero-row query cannot establish complete absence. |

Preserve actual source acknowledgment settlement, downstream durability,
original fact clock/profile association and coherent native observation as
separate evidence. All age arithmetic uses exact integer nanoseconds under the
selected timestamp precision/range; no JavaScript floating-point duration or
negative-age clamping. Existing held/empty/ahead-boundary and cancellation
controls continue to apply.
