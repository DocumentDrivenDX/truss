---
ddx:
  id: US-044
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

# US-044: Run a change inside my transaction and roll it back

**Feature**: FEAT-003 — Mutation and Concurrency
**Feature Requirements**: MUT-09
**PRD Requirements**: FR-55
**Priority**: P1
**Status**: Draft

## Story

**As a** Implementer
**I want** apply a group inside a transaction I control, look at its effects, and roll it back
**So that** I can ask what a change would do without keeping it

## Context

An embedded host adopts its actual live transaction, applies the group through
real Truss precondition/effect/final-state validation, reads pending results and
rolls back. Dry-run success cannot skip deferred Truss validation that a real
apply must pass. Truss contains operation failure with savepoints and restores
its operation-local validation context, preserving prior caller work. A caller rollback to an earlier host savepoint can subsequently remove a successful pending Truss call without ending the outer transaction; its retained result then cannot be published or settled as committed.

Pending IDs/results remain inside that original transaction until confirmed
outer commit. Commit acknowledgment loss requires original recovery, not a
committed label or a replacement allocation. Network callers instead submit a
complete atomic batch through an engine-owned transaction; no create/commit-by-ID
network transaction API is implied.

## Walkthrough

1. Implementer opens a transaction and applies a group of three operations.
2. Implementer reads the effects inside the transaction.
3. Implementer rolls back.
4. Implementer repeats it and commits.

## Acceptance Criteria

- [ ] **US-044-AC1** — Given a group applied inside a caller's transaction, when the caller reads, then the effects are visible there.
- [ ] **US-044-AC2** — Given the caller rolls back, when the data is read afterwards, then no object, edge or key row, journal row, tombstone or request record remains and no lock is held.
- [ ] **US-044-AC3** — Given the caller commits, when the data is read, then the group took effect as if the engine had committed it, with one origin and one set of journal rows.
- [ ] **US-044-AC4** — Given the engine, when it runs an operation in the caller's transaction, then it never commits or ends that transaction itself.

## Edge Cases

- **Ids consumed by a rolled-back group**: ordinary rollback does not reset the sequence, so gaps are allowed. IDs remain provisional within the original transaction; sequence behavior alone does not promise precommit crash/failover durability. Committed IDs are never reused.
- **A long caller transaction**: holds row locks and the catalog head's share lock until it ends.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Visible | US-044-AC1 | Group applied | Read inside | Effects visible |
| Rollback | US-044-AC2 | Rolled back | Read after | Nothing remains |
| Commit | US-044-AC3 | Committed | Read | Took effect |
| No commit | US-044-AC4 | Operation | Run | Engine never commits |

## Dependencies

- **Stories**: US-040
- **Feature Spec**: FEAT-003
- **Feature Requirements**: MUT-09
- **PRD Requirements**: FR-55
- **External**: CONTRACT-004, Caller-controlled transactions.

## Out of Scope

None.
