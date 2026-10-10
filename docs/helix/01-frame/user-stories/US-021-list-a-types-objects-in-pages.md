---
ddx:
  id: US-021
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-005
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-021: List a type's objects in pages

**Feature**: FEAT-005 — Reads and Traversal
**Feature Requirements**: RD-02
**PRD Requirements**: FR-29
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** page through every object of one type with a required limit and a marker that says whether more remain
**So that** listing a small type is as cheap as a large one, whatever the number of types

## Context

Without an index on `(type_id, id)` a small type took 1.2 to 1.6 ms to page (SPIKE-003). The 120-object acceptance fixture has stable authorized membership. Complete stable multi-page enumeration requires one caller-held repeatable-read snapshot or a stronger qualified profile; a continuation marker cannot recreate or extend a transaction. Each page is admitted under its declared consistency mode and current authorization before publication.

## Walkthrough

1. Engineer lists Customers with limit 50.
2. System returns 50 and a marker.
3. Engineer passes the marker and receives the next page.
4. Engineer lists a type with 3 objects.

## Acceptance Criteria

- [ ] **US-021-AC1** — Given 120 Customers, when listed with limit 50, then three pages of 50, 50 and 20 are returned and only the last says no more remain.
- [ ] **US-021-AC2** — Given a call without a limit, when it runs, then it is refused.
- [ ] **US-021-AC3** — Given a limit above the deployment maximum, when it runs, then it is refused as invalid.
- [ ] **US-021-AC4** — Given 10 types and then 1,000 types, when a small type is listed, then the page cost is the same within 2×.

## Edge Cases

- **Objects created during paging**: live READ COMMITTED continuation follows immutable ID boundaries. A continuously eligible object above the boundary is not skipped, but a late commit with a previously allocated lower ID can be missed. Stable membership requires the held-snapshot profile; expired snapshot custody refuses continuation.
- **A type with no objects**: an empty page and no marker.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Pages | US-021-AC1 | 120 objects | List limit 50 | 50, 50, 20; marker only on the first two |
| No limit | US-021-AC2 | None | List | Refused |
| Too large | US-021-AC3 | Limit 10,000 | List | Invalid |
| Scale | US-021-AC4 | 10 vs 1,000 types | List small type | Same cost |

## Dependencies

- **Stories**: US-007
- **Feature Spec**: FEAT-005
- **Feature Requirements**: RD-02
- **PRD Requirements**: FR-29
- **External**: CONTRACT-004, `list_objects`; CONTRACT-001, indexes.

## Out of Scope

None.
