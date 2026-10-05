---
ddx:
  id: US-022
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

# US-022: List an object's edges, bounded

**Feature**: FEAT-005 — Reads and Traversal
**Feature Requirements**: RD-03
**PRD Requirements**: FR-30
**Priority**: P1
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** list the edges of one object in a stable order, bounded, with a marker when more remain
**So that** an object with many connections cannot return an unbounded answer

## Context

Ordered relationships use an order key; others are ordered by identifier.

## Walkthrough

1. Engineer lists an Order's outgoing edges with limit 100.
2. System returns up to 100 with a marker.
3. Engineer lists the incoming edges of a Product.

## Acceptance Criteria

- [ ] **US-022-AC1** — Given an object with 250 edges, when listed with limit 100, then 100 are returned with a marker.
- [ ] **US-022-AC2** — Given an ordered relationship, when its edges are listed, then they are in order-key order, with unset keys last.
- [ ] **US-022-AC3** — Given direction in or out, when listed, then only edges of that direction are returned.

## Edge Cases

- **An object with no edges**: empty list.
- **Edges deleted between pages**: no edge is returned twice.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Bounded | US-022-AC1 | 250 edges | List 100 | 100 + marker |
| Ordered | US-022-AC2 | Ordered rel | List | By order key |
| Direction | US-022-AC3 | In/out | List in | Incoming only |

## Dependencies

- **Stories**: US-010
- **Feature Spec**: FEAT-005
- **Feature Requirements**: RD-03
- **PRD Requirements**: FR-30
- **External**: CONTRACT-004, `list_edges`.

## Out of Scope

None.
