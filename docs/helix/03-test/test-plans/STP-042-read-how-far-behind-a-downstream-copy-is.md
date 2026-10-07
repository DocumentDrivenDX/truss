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

US-042, TD-042, SD-004, TP-001 and CONTRACT-002/006. Tests are planned. Qualify actual durable checkpoint and same-snapshot journal lag; full feed extensions remain shared gates.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-042-AC1 | `durable_apply_advances_checkpoint_and_update_time` | Successful durable apply advances position/time atomically; failed apply does not acknowledge | `@covers US-042-AC1` | Native integration | `tests/feed/freshness.test.ts`; independent replica/consumer |
| US-042-AC2 | `lag_uses_earliest_unapplied_publishable_write` | Lag equals observation time minus minimum eligible unapplied at, not newest write or heartbeat | `@covers US-042-AC2` | Native integration | Same file; known native timestamps/checkpoint |
| US-042-AC3 | `held_committed_changes_are_separate_from_publishable_lag` | Older open transaction holds later committed changes; held state is separate and clears after blocker ends | `@covers US-042-AC3` | Native concurrency | Same file; explicit transaction/watermark barriers |
| US-042-AC4 | `copy_statement_names_actual_durable_position` | Published copy descriptor names its applied position and scope/epoch, never speculative source head | `@covers US-042-AC4` | Contract | Same file; independently expected replica descriptor |

## Data and Failure Probes

Checkpoint race probes use two workers with the same expected prior boundary: one advance succeeds, the other conflicts without overwriting. Equal acknowledgment is idempotent; reverse acknowledgment refuses; earlier delivery replay leaves the durable checkpoint unchanged. Wrong epoch/profile and unknown consumer cannot auto-register or reset. Crash after downstream apply before source acknowledgment resumes through durable dedup; crash before downstream commit cannot advance the source. A speculative high position with no complete application evidence refuses, independently of whether a stored checkpoint lies ahead of a later observer's watermark.

State discrimination probes require genuinely empty scoped backlog to differ from unauthorized scope, retained gap, wrong epoch, missing consumer and failed observation. None of the unavailable cases may return zero-lag success. An empty publishable set with held committed rows must retain the held state. A long adopted transaction uses observation time rather than transaction-start now(); injected negative clock age produces unavailable rather than zero clamping. Output cannot expose hidden record timestamps/counts. Full side-record freshness remains unqualified until its checkpoint profile exists.

Use independently captured row timestamps and exact checkpoint positions. Test no consumer, no eligible rows, ahead watermark, retained gap and unauthorized checkpoint changes. Long caller transaction tests observation clock versus transaction-start time. Concurrent acknowledgment/writer probes ensure one coherent snapshot. Held reporting covers committed visible rows only; do not invent uncommitted row counts.

## Executable Proof and Handoff

Future command `bun test tests/feed/freshness.test.ts` requires finalized envelope, clock and native harness. Retain raw observed_at/oldest_at/positions/watermark with query/profile pins. All four criteria block closeout. Journal lag alone cannot qualify full revision/source/reservation freshness or transport delivery SLA.

## Complete-feed freshness supplements

Include revision-only and side-only transactions with independently captured trusted original write times; missing timing cannot become empty. Authored source.at is deliberately different and cannot affect lag. Seed-represented transactions require persisted classifier/coverage verification before exclusion. Awaiting registrations return unavailable. Verify source acknowledgment descriptor against ahead downstream state without overwriting either. Current authorization gaps remove all protected timestamps/boundaries, and native overflow/cancellation cannot become zero-lag success.

## Fact-clock storage supplements

Capture independent original statement times for every required kind. Repeated identical registration and forced finalizer rebuild retain the first time; savepoint rollback removes it. Add a later member after early finalization and verify any cached transaction minimum is refreshed from complete membership. Legacy missing clocks remain unavailable for complete freshness even when delivery is otherwise qualified. Native tests must establish exact precision and journal-time agreement rather than comparing two calls to the same implementation helper.
