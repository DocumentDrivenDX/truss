---
ddx:
  id: US-010
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

# US-010: Refuse bad edges and protect connected objects

**Feature**: FEAT-002 — Storage, Identity and Exactness
**Feature Requirements**: STO-05
**PRD Requirements**: FR-13
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** have the database refuse an edge to the wrong kind of object and refuse to delete an object that still has edges
**So that** relationships stay valid even when a caller bypasses the engine

## Context

`Order` to `OrderLine` is the allowed relationship.

## Walkthrough

1. Engineer creates an `order_line` edge from an Order to an OrderLine.
2. Engineer attempts the edge from a Customer to an OrderLine.
3. System refuses it.
4. Engineer deletes the Order while the edge exists.
5. System refuses.

## Acceptance Criteria

- [ ] **US-010-AC1** — Given a relationship that allows Order to OrderLine, when an edge from a Customer to an OrderLine is created, then the database refuses it.
- [ ] **US-010-AC2** — Given an edge to an object that does not exist, when it is created, then it is refused.
- [ ] **US-010-AC3** — Given an object with an edge, when it is deleted, then the delete is refused, including when attempted with plain SQL.
- [ ] **US-010-AC4** — Given the edge is deleted first, when the object is deleted, then the delete succeeds.

## Edge Cases

- **Composition**: owned objects are deleted with their owner by the engine, edges first.
- **An edge created concurrently with the delete**: one of them fails; no dangling edge.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Bad type | US-010-AC1 | Customer to OrderLine | Create | Refused |
| Missing | US-010-AC2 | No target | Create | Refused |
| Protected | US-010-AC3 | Object with edge | Delete (plain SQL) | Refused |
| After edge | US-010-AC4 | Edge deleted | Delete object | Succeeds |

## Dependencies

- **Stories**: US-007
- **Feature Spec**: FEAT-002
- **Feature Requirements**: STO-05
- **PRD Requirements**: FR-13
- **External**: CONTRACT-001, Constraints.

## Out of Scope

None.
