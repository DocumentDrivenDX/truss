---
ddx:
  id: US-023
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

# US-023: Traverse one to three hops

**Feature**: FEAT-005 — Reads and Traversal
**Feature Requirements**: RD-04
**PRD Requirements**: FR-31
**Priority**: P1
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** reach related objects up to three hops away within the latency target
**So that** connected queries are practical on PostgreSQL

## Context

The vision's bar is p95 within 2× of a hand-designed schema.

## Walkthrough

1. Engineer starts from a Customer.
2. System follows `placed` to Orders and `order_line` to OrderLines.
3. System returns the OrderLines.

## Acceptance Criteria

- [ ] **US-023-AC1** — Given the benchmark corpus, when a one-hop traversal runs, then p95 is within 2× of the hand-designed schema.
- [ ] **US-023-AC2** — Given two and three hops, when they run, then p95 is within 2×.
- [ ] **US-023-AC3** — Given 10 and 1,000 types, when a one-hop traversal is planned, then planning is within 2×.

## Edge Cases

- **A hop through a high-degree object**: bounded by the same limit and marker.
- **Cycles**: a traversal does not revisit an object within one result.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| 1 hop | US-023-AC1 | Corpus | Run | ≤ 2× |
| 2-3 hops | US-023-AC2 | Corpus | Run | ≤ 2× |
| Scale | US-023-AC3 | 10 vs 1,000 | Plan | Within 2× |

## Dependencies

- **Stories**: US-022
- **Feature Spec**: FEAT-005
- **Feature Requirements**: RD-04
- **PRD Requirements**: FR-31
- **External**: Benchmark harness.

## Out of Scope

A traversal language.
