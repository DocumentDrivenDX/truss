---
ddx:
  id: US-003
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

# US-003: Decide what happens to an unknown entity type

**Feature**: FEAT-001 — Catalog and Revisions
**Feature Requirements**: CAT-03
**PRD Requirements**: FR-3
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** say whether a relationship to an undefined entity is rejected, held as a provisional type, or skipped
**So that** I can import a schema that refers to entities defined elsewhere without losing the reference silently

## Context

A relationship may name an entity that no document in the set and no earlier revision defines.

## Walkthrough

1. Engineer registers `orders` without `sales`.
2. Under the default policy the system rejects and names the unknown entity.
3. Engineer registers again with policy provisional.
4. System creates a provisional `Line` type and the relationship, and reports it.
5. A later revision defines `Line` and the provisional flag clears.

## Acceptance Criteria

- [ ] **US-003-AC1** — Given an unknown endpoint and the reject policy, when the set is registered, then it is rejected and the report names the endpoint and its relationship.
- [ ] **US-003-AC2** — Given the provisional policy, when the set is registered, then a provisional type exists with no properties, the relationship is derived, and the report lists the type until it is defined.
- [ ] **US-003-AC3** — Given the skip policy, when the set is registered, then the relationship is not derived and the report records the loss.
- [ ] **US-003-AC4** — Given a provisional type, when a later revision defines it, then its identifier is unchanged and the provisional flag is cleared.

## Edge Cases

- **Data held for a provisional type**: retained and reported (US-008).
- **A type that stays provisional**: listed in every later report.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Reject | US-003-AC1 | Unknown `Line` | Register, reject policy | Rejected, `Line` named |
| Provisional | US-003-AC2 | Unknown `Line` | Register, provisional | Provisional type; reported |
| Skip | US-003-AC3 | Unknown `Line` | Register, skip | Relationship absent; loss reported |
| Define later | US-003-AC4 | Provisional `Line` | Register `sales` | Same id; flag cleared |

## Dependencies

- **Stories**: US-001
- **Feature Spec**: FEAT-001
- **Feature Requirements**: CAT-03
- **PRD Requirements**: FR-3
- **External**: CONTRACT-003, Unknown entity types.

## Out of Scope

None.
