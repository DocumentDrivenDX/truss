---
ddx:
  id: US-004
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

# US-004: Keep identifiers stable across revisions

**Feature**: FEAT-001 — Catalog and Revisions
**Feature Requirements**: CAT-04
**PRD Requirements**: FR-4
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** have every type, property, key and relationship keep its identifier as the schema evolves, and never see one reused
**So that** stored data and journal entries stay meaningful across revisions

## Context

Stored values are keyed by property identifier, so a changed or reused identifier would corrupt meaning.

## Walkthrough

1. Engineer registers revision 1 with `Customer.email`.
2. Engineer registers revision 2 that retires `email` and adds `phone`.
3. System keeps `email`'s identifier retired and gives `phone` a new one.
4. Engineer registers the identical bytes again.

## Acceptance Criteria

- [ ] **US-004-AC1** — Given an element whose UMF identity is unchanged, when a revision is accepted, then its identifier is unchanged.
- [ ] **US-004-AC2** — Given a retired property, when a new property is added, then the new identifier differs from every identifier ever issued.
- [ ] **US-004-AC3** — Given the same document bytes registered twice, when the second registration runs, then no new revision is created.

## Edge Cases

- **A retired element redefined**: follows the identity rule; it is not given a retired identifier.
- **Two documents defining one element differently**: rejected as a duplicate definition.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Stable | US-004-AC1 | `Customer.email` id 12 | Register revision 2 | Still id 12 |
| No reuse | US-004-AC2 | `email` retired | Add `phone` | New id, not 12 |
| Idempotent | US-004-AC3 | Revision 2 accepted | Register same bytes | No new revision |

## Dependencies

- **Stories**: US-001
- **Feature Spec**: FEAT-001
- **Feature Requirements**: CAT-04
- **PRD Requirements**: FR-4
- **External**: CONTRACT-003, Identity stability.

## Out of Scope

None.
