---
ddx:
  id: US-036
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-001
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-036: Record who accepted a revision

**Feature**: FEAT-001 — Catalog and Revisions
**Feature Requirements**: CAT-09
**PRD Requirements**: FR-47
**Priority**: P0
**Status**: Draft

## Story

**As a** Auditor
**I want** see who or what accepted each catalog revision, and as which database role
**So that** the most consequential change in the system is as auditable as a data change

## Context

A revision can retire types and re-bind or transform stored data. Journal rows already record an actor and a role; revisions did not.

## Walkthrough

1. Engineer, as role `w` with actor `a` and reason `add Shipment`, registers a revision.
2. System accepts it and records its origin with the revision.
3. Auditor reads the revision.
4. Engineer sends a database role in the origin.

## Acceptance Criteria

- [ ] **US-036-AC1** — Given a revision accepted as role `w` with actor `a`, when it is read, then its origin has actor `a`, role `w` and the reason.
- [ ] **US-036-AC2** — Given a caller that sends a database role in the origin, when the revision is accepted, then the stored role is the database's, not the caller's.
- [ ] **US-036-AC3** — Given a revision rejected as a whole, when the revisions are listed, then no origin row exists for it.
- [ ] **US-036-AC4** — Given the origin is not a JSON object, when a revision is inserted, then the database refuses it.

## Edge Cases

- **No actor given**: the origin still records the role.
- **A host key `x-...`**: kept as given.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Origin | US-036-AC1 | Role `w`, actor `a` | Accept | Actor, role, reason recorded |
| Role | US-036-AC2 | Caller sends role | Accept | Database role stored |
| Rejected | US-036-AC3 | Rejected set | List revisions | No row |
| Shape | US-036-AC4 | Origin `[]` | Insert | Refused |

## Dependencies

- **Stories**: US-001
- **Feature Spec**: FEAT-001
- **Feature Requirements**: CAT-09
- **PRD Requirements**: FR-47
- **External**: CONTRACT-003, Input; CONTRACT-002, `origin`.

## Out of Scope

None.
