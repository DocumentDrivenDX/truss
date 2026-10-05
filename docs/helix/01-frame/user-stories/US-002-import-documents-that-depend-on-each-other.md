---
ddx:
  id: US-002
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

# US-002: Import documents in dependency order

**Feature**: FEAT-001 — Catalog and Revisions
**Feature Requirements**: CAT-02
**PRD Requirements**: FR-2
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** register documents in any order and have the catalog order them by dependency
**So that** I do not have to sequence my schema files by hand

## Context

`orders` declares a relationship to `Product`, which `sales` defines. The set may arrive in either order.

## Walkthrough

1. Engineer registers `orders` and `sales` together, `orders` first.
2. System sorts them so `sales` comes first.
3. System derives every type before any relationship.
4. System accepts the set.

## Acceptance Criteria

- [ ] **US-002-AC1** — Given `orders` depends on `sales`, when both are registered in either order, then the resulting order is `sales` then `orders` and the endpoint resolves.
- [ ] **US-002-AC2** — Given two documents that depend on each other, when they are registered, then they are accepted together in order of document identifier.
- [ ] **US-002-AC3** — Given the same set in a different submission order, when registered, then the recorded document order is identical.

## Edge Cases

- **Tie between unrelated documents**: ordered by document identifier in byte order.
- **A document that depends on one not in the set**: its endpoints follow the unknown-endpoint policy (US-003).

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Either order | US-002-AC1 | `orders`, `sales` | Register in both orders | Same sorted order |
| Cycle | US-002-AC2 | A and B reference each other | Register | Accepted together by identifier |
| Determinism | US-002-AC3 | Fixed set | Register shuffled | Same order recorded |

## Dependencies

- **Stories**: US-001
- **Feature Spec**: FEAT-001
- **Feature Requirements**: CAT-02
- **PRD Requirements**: FR-2
- **External**: CONTRACT-003 step 2.

## Out of Scope

None.
