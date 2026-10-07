---
ddx:
  id: STP-016
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-016
      kind: informed_by
    - id: TD-016
      kind: informed_by
    - id: SD-004
      kind: informed_by
---

# STP-016: Journal plain SQL changes

## Story Reference

US-016, TD-016, SD-004, TP-001 and CONTRACT-002/004/007. All tests are planned.

## Scope and Objective

Prove exclusive journal/version writers and honest raw-SQL audit guarantees per configured mode.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-016-AC1 | `raw_sql_is_journaled_in_trigger_mode` | Raw insert/update/delete creates exact expected events and version/time effects; journal failure rolls back canonical work | `@covers US-016-AC1` | Native integration | `tests/journal/modes.test.ts`; ordinary writer and qualified triggers |
| US-016-AC2 | `engine_does_not_duplicate_trigger_writer` | Engine mutation causes exactly one event set and one version increment; no-op remains unchanged | `@covers US-016-AC2` | Native integration | Same file; trigger-mode engine executor |
| US-016-AC3 | `engine_mode_reports_raw_sql_gap` | Raw SQL emits no journal event in engine mode; report explicitly describes bypass gap | `@covers US-016-AC3` | Native integration | Same file; independent canonical/journal observer and report fixture |

## Executable Proof

Future command `bun test tests/journal/modes.test.ts` requires harness/files. Criterion citations and server/adapter/mode/trigger/grant pins are required. Missing trigger profile qualification is unverified, not a skipped pass.

## Data and Setup

Independent expected events cover object and edge changes, retained values, absence/null and complete envelopes. Observe native version and time separately from event count. Force mode-switch contention while a writer transaction remains open; assert exclusive behavior after its completion. Multiple caller calls use distinct origin fixtures to expose leakage.

## Edge Cases and Failure Modes

Attempt trigger disable, direct version manipulation and mode alteration as the qualified writer; these must not bypass advertised behavior. Exercise no-op SQL, bulk mutations, trigger recursion/order and missing journal partition. Caller rollback removes events/effects. Mode transition contract and historical envelope gates must close before expectations are final.

## Build Handoff

Finalize trigger/exclusion/privilege design, create red native cases, implement one writer path per mode and qualify transition races. All three criteria and operation/privilege supplements block full trigger-profile support. Endpoint/multiplicity guard support remains separately tested.

### Transaction-wide mode transition schedules

Use explicit barriers: writer A admits engine mode, makes a mutation and remains in its host transaction; administrator B requests a mode-only trigger switch. B cannot confirm the switch while A retains exclusion. A's second operation uses the same admitted writer with no duplicate or missing events. After A's observed commit or rollback, B verifies target readiness and confirms its own actual commit; fresh writer C admits trigger mode. Repeat with trigger-mode raw SQL, cancellation/timeout while B waits, old data snapshots and an unknown B commit acknowledgment. No callback retry or host transaction termination is permitted to obtain a newer mode.

Roll back A's first operation to a savepoint that releases its native admission, then invoke another operation: a stale cached pin cannot be reused. Fault target-readiness validation and require unchanged mode. Exercise ordinary setting/trigger tampering refusals. Separately schedule dispatcher DDL competing with native row-trigger admission and administrative mode exclusion; qualify the complete selected wait matrix or refuse that composition rather than claiming the mode-only protocol proves DDL safety. All schedules remain planned until exact native dispatcher/exclusion/current-setting producers are selected.
