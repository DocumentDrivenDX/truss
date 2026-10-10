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

Attempt trigger disable, direct version manipulation and mode alteration as the qualified writer; these must not bypass advertised behavior. Exercise no-op SQL, bulk mutations, trigger recursion/order and missing journal partition. Caller rollback removes events/effects. The mode-only transition algorithm is authored; exact native exclusion/dispatcher/readiness producers and historical envelope profiles must qualify before these expectations can be executed.

## Build Handoff

Finalize trigger/exclusion/privilege design, create red native cases, implement one writer path per mode and qualify transition races. All three criteria and operation/privilege supplements block full trigger-profile support. Endpoint/multiplicity guard support remains separately tested.

### Transaction-wide mode transition schedules

Use explicit barriers: writer A admits engine mode, makes a mutation and remains in its host transaction; administrator B first qualifies the already-installed target trigger dispatcher and complete original readiness inventory, then requests a mode-only trigger switch. This request installs no trigger/helper/grant objects. B cannot confirm the switch while A retains exclusion. A's second operation uses the same admitted writer with no duplicate or missing events. After A's observed commit or rollback, B acquires exclusive admission, confirms that the original qualified target inventory/configuration remains current under the selected installation-authority exclusion, changes only the mode and confirms its own actual commit; fresh writer C admits trigger mode. A stale readiness observation refuses instead of installing or repairing objects while holding mode exclusion. Repeat with trigger-mode raw SQL, cancellation/timeout while B waits, old data snapshots and an unknown B commit acknowledgment. No callback retry or host transaction termination is permitted to obtain a newer mode.

Roll back A's first operation to a savepoint that releases its native admission, then invoke another operation: a stale cached pin cannot be reused. Fault target-readiness validation and require unchanged mode. Exercise ordinary setting/trigger tampering refusals. Separately schedule dispatcher DDL competing with native row-trigger admission and administrative mode exclusion; qualify the complete selected wait matrix or refuse that composition rather than claiming the mode-only protocol proves DDL safety. All schedules remain planned until exact native dispatcher/exclusion/current-setting producers are selected.


## Producer ownership includes timestamp and complete group

For the independently authored two-property mutation in US-015, observe exactly two original property-delta rows and the complete record-boundary witness under the selected event profile. Compare their full before/after values, group identity, original revision/origin, actual version and timestamp effects; counting only two delta rows is insufficient complete-group evidence. Repeat through engine API in trigger mode and qualified raw SQL in trigger mode. Neither route may invoke a second journal producer, increment the version twice or overwrite the original update timestamp with a host-generated value. A no-op must preserve all three categories of state.

Inject journal failure after canonical effects are staged and independently observe rollback of values, derived keys, version, timestamp and every staged group member. An uncertain outer termination follows original transaction recovery, not an assumed rollback based on a thrown callback. Run each case under the exact installed routine/trigger/privilege and transport profile; a superuser fixture that disables triggers cannot qualify ordinary-writer audit support. These are planned native schedules, not executed evidence.


A readiness-drift control pauses B after its initial target inventory observation and before exclusive mode admission. A separately authorized installation transition replaces or invalidates a target dependency under its own qualified exclusion. B must detect lost correspondence and preserve the prior mode; matching trigger names or a cached successful readiness flag cannot authorize the switch. Observe native mode, effective installed inventory and both writer paths independently. The mode-only request must contain no DDL, even when target readiness fails. This control remains planned and requires the security/installation owner’s actual exclusion protocol; it does not define a competing native authority lock.
