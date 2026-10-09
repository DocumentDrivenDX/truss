---
ddx:
  id: US-013
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

# US-013: Refuse a write against a stale catalog

**Feature**: FEAT-003 — Mutation and Concurrency
**Feature Requirements**: MUT-03, MUT-04
**PRD Requirements**: FR-17, FR-18
**Priority**: P0
**Status**: Draft

## Story

**As a** Implementer
**I want** be certain a write is never accepted against a catalog revision that was replaced while it ran
**So that** a revision can be accepted at any time without corrupting data

## Context

SPIKE-003 found that a new-row-per-revision head and an advisory-only lock both let a stale write through in some isolation levels. The selected protocol uses one mutable catalog head with shared writer/exclusive acceptance locking. “Accepted mid-write” in AC1/AC2 means acceptance commits after an earlier unprotected pin/snapshot observation but before the writer successfully acquires its locking head admission. Once admitted, the writer retains its share lock through actual outer transaction termination; acceptance waits rather than replacing its head. An adopted transaction is not silently ended to allow acceptance through.

## Walkthrough

1. A writer retains an expected head pin or establishes an older repeatable-read snapshot before acquiring the catalog share lock.
2. Another session accepts a revision.
3. The writer attempts its original locking head admission against the now-changed row.
4. System refuses as catalog changed or the qualified serialization/retry outcome, with original containment. The host may explicitly retry under the required scope; Truss does not automatically rerun the host transaction.

## Acceptance Criteria

- [ ] **US-013-AC1** — Given READ COMMITTED, when a revision is accepted mid-write, then the write detects the new head and does not commit against the old revision.
- [ ] **US-013-AC2** — Given REPEATABLE READ, when a revision is accepted mid-write, then the write fails as a serialization failure reported as retry.
- [ ] **US-013-AC3** — Given sixteen continuous writers, when an acceptance runs, then it completes and sets a lock timeout; with the optional queue its wait is at most 50 ms.
- [ ] **US-013-AC4** — Given two simultaneous acceptances, when both run, then they serialize and the second validates against the first.

## Edge Cases

- **Acceptance cannot get the lock in time**: rolls back and may be retried.
- **Optional queue absent**: waits grow to seconds under constant load.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| RC | US-013-AC1 | Read committed | Accept mid-write | Write detects; not committed |
| RR | US-013-AC2 | Repeatable read | Accept mid-write | Retry |
| Load | US-013-AC3 | 16 writers | Accept | Completes; queue wait ≤ 50 ms |
| Two | US-013-AC4 | Two acceptances | Run together | Serialized |

## Dependencies

- **Stories**: US-012
- **Feature Spec**: FEAT-003
- **Feature Requirements**: MUT-03, MUT-04
- **PRD Requirements**: FR-17, FR-18
- **External**: CONTRACT-001, Concurrency; SPIKE-003 F6.

## Out of Scope

None.
