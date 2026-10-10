---
ddx:
  id: US-019
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-004
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-019: Trim the journal by dropping partitions

**Feature**: FEAT-004 — Journal and History
**Feature Requirements**: JNL-06
**PRD Requirements**: FR-27
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** partition the journal by time and remove old history only by dropping whole partitions
**So that** retention never edits an audit row

## Context

A default partition would trap rows that later cannot be moved into a partition
(verified), so there is none. Accepted ADR-007 allows very short or zero local
retention after complete qualified handoff and protection release. Zero selects
no additional age window; it does not omit journal production or guarantee that
an active/protected whole partition is immediately absent. Removal follows the
selected partition granularity, writer exclusion and complete eligibility.

Before dropping a whole eligible partition, recheck every original consumer,
receipt, recovery, history/definition/configuration and archive dependency.
Upload success, elapsed age or a cursor alone cannot establish durable complete
handoff. Required local protections remain until the selected independent archive
and lifecycle evidence admits their release. New writes still require a covering
partition; a zero retention setting cannot create an accepted clock-range hole.

## Walkthrough

1. Engineer creates monthly partitions ahead.
2. A write lands in the current month.
3. Engineer verifies complete handoff and all protections under the selected exclusions, then drops an eligible whole partition and records original settlement.
4. A write is attempted at a time no partition covers.

## Acceptance Criteria

- [ ] **US-019-AC1** — Given partitions created ahead, when a change is made, then its row lands in the covering partition.
- [ ] **US-019-AC2** — Given no partition covers the time, when a change is made, then it fails with a check violation and nothing is stored.
- [ ] **US-019-AC3** — Given a role truss recognizes, when it tries to update or delete a journal row, then it is refused.
- [ ] **US-019-AC4** — Given a partition past retention, when it is dropped, then the other months are unaffected.

## Edge Cases

- **Privileged DDL altering a guard**: native ownership alone is not an admitted runtime action. The selected security/installation profile must account for that path; drift makes the affected capability unavailable until independently qualified reconciliation.
- **Partition created for a range with rows in a default**: not applicable; there is no default.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Lands | US-019-AC1 | Partition exists | Change | Row in partition |
| No partition | US-019-AC2 | None covers | Change | Fails; not stored |
| Append-only | US-019-AC3 | Any role | Update a row | Refused |
| Drop | US-019-AC4 | Old partition | Drop | Others intact |

## Dependencies

- **Stories**: US-015
- **Feature Spec**: FEAT-004
- **Feature Requirements**: JNL-06
- **PRD Requirements**: FR-27
- **External**: CONTRACT-002, Partitions and retention.

## Out of Scope

None.
