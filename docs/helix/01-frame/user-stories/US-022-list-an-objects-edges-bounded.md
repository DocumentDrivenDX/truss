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

The selected direct-list comparator orders non-null order keys using the qualified C comparator, then immutable edge ID for ties, with null keys last and ordered by ID. All-null relationships therefore use ID order. Mixed relationship selections use the same global comparator, rather than a different comparator per relationship. Complete stable paging requires one caller-held qualified snapshot; each page also requires current authorization before publication.

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
- **Edges changed between pages**: a held snapshot preserves original membership/order and avoids repeats. Separate live READ COMMITTED pages can omit or repeat an edge whose mutable order key crosses the prior boundary; deletion alone does not repeat a stable-order edge. The declared live mode cannot promise frozen enumeration.

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
