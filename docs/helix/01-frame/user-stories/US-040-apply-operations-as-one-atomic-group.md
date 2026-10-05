---
ddx:
  id: US-040
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-003
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-040: Apply several operations as one atomic group

**Feature**: FEAT-003 — Mutation and Concurrency
**Feature Requirements**: MUT-07
**PRD Requirements**: FR-51
**Priority**: P1
**Status**: Draft

## Story

**As a** Implementer
**I want** create an object, update another and connect them in one unit that commits or fails as a whole
**So that** a business operation that touches several records is never half applied

## Context

A single operation is already atomic; a business action usually needs several.

## Walkthrough

1. Implementer builds a group: create an Order, create an OrderLine, and an edge from the Order to the line, referring to the new records by alias.
2. System runs the catalog check once and each operation in order.
3. System commits the group with one origin.
4. Implementer repeats it with an invalid edge in the group.

## Acceptance Criteria

- [ ] **US-040-AC1** — Given a valid group, when it is applied, then every operation takes effect, all journal rows share one transaction and one origin, and the results come back in order.
- [ ] **US-040-AC2** — Given a group whose third operation is invalid, when it is applied, then none of the operations takes effect and the error names index 2 and its own error kind.
- [ ] **US-040-AC3** — Given two groups that touch the same objects in different orders, when they run concurrently, then neither deadlocks, because locks are taken in ascending order.
- [ ] **US-040-AC4** — Given a revision accepted while the group runs, when the group reaches commit, then it is not accepted against the old revision.

## Edge Cases

- **An operation that refers to an alias created later in the group**: refused.
- **An empty group**: refused as invalid.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Valid group | US-040-AC1 | 3 operations | Apply | All effective; one origin |
| Failure | US-040-AC2 | Third invalid | Apply | None effective; index 2 |
| Ordering | US-040-AC3 | Two groups | Run concurrently | No deadlock |
| Stale | US-040-AC4 | Revision accepted mid-group | Commit | Not accepted |

## Dependencies

- **Stories**: US-012
- **Feature Spec**: FEAT-003
- **Feature Requirements**: MUT-07
- **PRD Requirements**: FR-51
- **External**: CONTRACT-004, `apply_group`.

## Out of Scope

None.
