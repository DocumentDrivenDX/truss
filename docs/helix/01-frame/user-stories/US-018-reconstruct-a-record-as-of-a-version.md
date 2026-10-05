---
ddx:
  id: US-018
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

# US-018: Reconstruct a record as of a version

**Feature**: FEAT-004 — Journal and History
**Feature Requirements**: JNL-05
**PRD Requirements**: FR-26
**Priority**: P0
**Status**: Draft

## Story

**As a** Auditor
**I want** see what a record held at any version, interpreted under the definitions then in force
**So that** I can reproduce a past state exactly

## Context

A revision may have changed a property's definition after the row was written.

## Walkthrough

1. Auditor asks for an Order at version 2.
2. System starts from the create row and applies versions 2 and below.
3. A property whose definition changed is read with the definition recorded for that revision.

## Acceptance Criteria

- [ ] **US-018-AC1** — Given an Order with versions 1 to 4, when version 2 is requested, then the properties equal the create values with updates up to version 2 applied.
- [ ] **US-018-AC2** — Given a revision that changed a property's definition in place, when an earlier version is read, then the definition in force then is used.
- [ ] **US-018-AC3** — Given a version never written, when it is requested, then the history is empty and no error is raised.

## Edge Cases

- **As-of by wall-clock time**: not defined; time is not a commit time.
- **Rebind and transform rows**: applied in order.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| As of v2 | US-018-AC1 | v1 to v4 | Read v2 | Values at v2 |
| Definition | US-018-AC2 | Definition changed | Read earlier | Earlier definition |
| Unwritten | US-018-AC3 | No v9 | Read v9 | Empty |

## Dependencies

- **Stories**: US-015
- **Feature Spec**: FEAT-004
- **Feature Requirements**: JNL-05
- **PRD Requirements**: FR-26
- **External**: CONTRACT-002, As-of reads.

## Out of Scope

None.
