---
ddx:
  id: US-015
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

# US-015: Journal every change atomically with its origin

**Feature**: FEAT-004 — Journal and History
**Feature Requirements**: JNL-01, JNL-03
**PRD Requirements**: FR-22, FR-23
**Priority**: P0
**Status**: Draft

## Story

**As a** Auditor
**I want** see for every change what changed, from what to what, when, under which revision and as which actor and database role
**So that** I can audit data without trusting the application's account of itself

## Context

The database role comes from the database; the actor is what the caller asserts.

## Walkthrough

1. Engineer, as role `w` with actor `a`, changes two properties of an Order.
2. System writes two property-delta journal rows plus one complete record-boundary metadata witness, sharing entity, version and transaction.
3. Auditor reads the rows.
4. Auditor forces a journal write failure and repeats the change.

## Acceptance Criteria

- [ ] **US-015-AC1** — Given a change to two properties, when it commits, then two property-delta rows exist with old and new values, the same version, origin actor `a` and database role `w`, plus one complete record-boundary metadata witness in the same complete mutation group.
- [ ] **US-015-AC2** — Given a caller that supplies a database role in the origin, when the change commits, then the stored role is the database's, not the caller's.
- [ ] **US-015-AC3** — Given a forced journal write failure, when a change is attempted, then the change is not stored.
- [ ] **US-015-AC4** — Given a create, an update and a delete, when the rows are read, then each has the operation and the whole-record payloads defined for it.

## Edge Cases

- **Retained data added by a later write**: a `retain` row.
- **Definer functions**: the role is read from the session setting, never the current user.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Rows | US-015-AC1 | Role `w`, actor `a` | Change 2 props | 2 property deltas plus complete record-boundary witness; shared original group/version/origin |
| Role | US-015-AC2 | Caller sends role | Change | Database role stored |
| Atomic | US-015-AC3 | Forced failure | Change | Not stored |
| Operations | US-015-AC4 | Create/update/delete | Read rows | Defined payloads |

## Dependencies

- **Stories**: None
- **Feature Spec**: FEAT-004
- **Feature Requirements**: JNL-01, JNL-03
- **PRD Requirements**: FR-22, FR-23
- **External**: CONTRACT-002, Rows per operation and origin.

## Out of Scope

None.
