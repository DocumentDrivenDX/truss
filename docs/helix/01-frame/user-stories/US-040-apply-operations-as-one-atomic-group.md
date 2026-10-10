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

A single operation is already atomic; a business action usually needs several. The group plans and revalidates the complete affected lock set under CONTRACT-009 before graph effects, then validates cross-row invariants against the complete simulated final state. Submitted order determines aliases and ordered results; transient intermediate state cannot be advertised as the final graph. The opposed-order no-deadlock criterion covers groups honoring the shared hierarchy without arbitrary earlier host locks; a host-induced deadlock follows the separate retry/containment contract. Request-free group atomicity does not require receipt storage and does not provide exact-input replay. Request-enabled retry consumes the independently qualified complete receipt profile.

## Walkthrough

1. Implementer builds a group: create an Order, create an OrderLine, and an edge from the Order to the line, referring to the new records by alias.
2. System admits the original catalog/context once, acquires and revalidates the complete planned lock set, validates the final candidate graph, and applies the submitted operations in order.
3. System returns ordered results with one origin: pending inside an adopted transaction, or committed only after confirmed settlement of its engine-owned outer transaction.
4. Implementer repeats it with an invalid edge in the group.

## Acceptance Criteria

- [ ] **US-040-AC1** — Given a valid group, when it is applied, then every operation takes effect, all journal rows share one transaction and one origin, and the results come back in order.
- [ ] **US-040-AC2** — Given a group whose third operation is invalid, when it is applied, then none of the operations takes effect and the error names index 2 and its own error kind.
- [ ] **US-040-AC3** — Given two groups that touch the same objects in different orders, when they run concurrently, then neither deadlocks, because locks are taken in ascending order.
- [ ] **US-040-AC4** — Given catalog acceptance racing with a group, when acceptance commits before the group acquires its catalog share lock, then a group expecting the old revision is refused without effects; when the group acquires its share lock first, acceptance waits until that transaction ends and cannot invalidate the group mid-transaction.

## Edge Cases

- **An operation that refers to an alias created later in the group**: refused.
- **An empty group**: refused as invalid.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Valid group | US-040-AC1 | 3 operations | Apply | All effective; one origin |
| Failure | US-040-AC2 | Third invalid | Apply | None effective; index 2 |
| Ordering | US-040-AC3 | Two groups | Run concurrently | No deadlock |
| Catalog race | US-040-AC4 | Acceptance and group race on head lock | Run both lock-acquisition orders | Acceptance-first: stale refusal; group-first: acceptance waits |

## Dependencies

- **Stories**: US-012
- **Feature Spec**: FEAT-003
- **Feature Requirements**: MUT-07
- **PRD Requirements**: FR-51
- **External**: CONTRACT-004, `apply_group`.

## Out of Scope

None.
