---
ddx:
  id: US-024
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

# US-024: Enumerate the types of the catalog

**Feature**: FEAT-005 — Reads and Traversal
**Feature Requirements**: RD-05
**PRD Requirements**: FR-32
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** list the types in force with their properties, keys and relationship endpoints, from one revision
**So that** I can see what the database can hold

## Context

A listing assembled from several reads could mix two revisions.

## Walkthrough

1. Engineer asks for the catalog's types.
2. System reads the catalog in one transaction.
3. System returns types, properties, keys, endpoints and the revision.

## Acceptance Criteria

- [ ] **US-024-AC1** — Given 1,000 types, when they are enumerated, then all are returned with properties, keys and relationship endpoints and one revision number.
- [ ] **US-024-AC2** — Given a revision accepted during the call, when the answer returns, then it is entirely from one revision.
- [ ] **US-024-AC3** — Given 100 sequential enumerations at benchmark size, when latency is measured, then p95 is at most 20 ms (proposed).

## Edge Cases

- **Retired and provisional types**: shown with their flags.
- **An empty catalog**: revision 0 and no types.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| All | US-024-AC1 | 1,000 types | Enumerate | Complete, one revision |
| Consistent | US-024-AC2 | Accept mid-call | Enumerate | One revision |
| Latency | US-024-AC3 | Benchmark | 100 calls | p95 ≤ 20 ms |

## Dependencies

- **Stories**: US-001
- **Feature Spec**: FEAT-005
- **Feature Requirements**: RD-05
- **PRD Requirements**: FR-32
- **External**: CONTRACT-001, catalog tables.

## Out of Scope

None.
