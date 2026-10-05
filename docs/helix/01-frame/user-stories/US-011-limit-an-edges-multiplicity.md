---
ddx:
  id: US-011
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-002
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-011: Limit an edge's multiplicity without an index per relationship

**Feature**: FEAT-002 — Storage, Identity and Exactness
**Feature Requirements**: STO-06
**PRD Requirements**: FR-14
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** declare that an Order has at most one billing address and have the database enforce it
**So that** limits hold under concurrent writes and do not slow every query

## Context

A per-relationship partial index would add one index per relationship to the edge table; at 1,000 relationships that cost 110 ms of planning (SPIKE-003).

## Walkthrough

1. Engineer declares `bill_to` with a maximum of one per Order.
2. Engineer creates the edge.
3. Engineer creates a second `bill_to` for the same Order.
4. System refuses it.
5. Engineer deletes the first edge and creates the second.

## Acceptance Criteria

- [ ] **US-011-AC1** — Given a maximum of one, when a second edge for the same source is created, then the database refuses it, including under concurrent creates.
- [ ] **US-011-AC2** — Given the first edge is deleted, when a second is created, then it is accepted.
- [ ] **US-011-AC3** — Given 1,000 relationships, when a one-hop query is planned, then planning is within 2× of the figure with 10 relationships.
- [ ] **US-011-AC4** — Given a maximum of three, when a fourth edge is created, then the write protocol refuses it under the parent lock.

## Edge Cases

- **Maximum on the target side**: enforced the same way.
- **Cross-row rule for larger maxima**: reported as engine enforcement.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Max one | US-011-AC1 | One edge | Create second, concurrently | One accepted |
| Delete | US-011-AC2 | Edge deleted | Create | Accepted |
| Planning | US-011-AC3 | 10 vs 1,000 rels | Plan one hop | Within 2× |
| Max three | US-011-AC4 | 3 edges | Create fourth | Refused |

## Dependencies

- **Stories**: US-010
- **Feature Spec**: FEAT-002
- **Feature Requirements**: STO-06
- **PRD Requirements**: FR-14
- **External**: SPIKE-003 F3.

## Out of Scope

None.
