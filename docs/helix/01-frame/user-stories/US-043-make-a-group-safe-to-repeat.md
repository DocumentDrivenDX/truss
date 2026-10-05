---
ddx:
  id: US-043
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

# US-043: Make a group safe to repeat

**Feature**: FEAT-003 — Mutation and Concurrency
**Feature Requirements**: MUT-08
**PRD Requirements**: FR-54
**Priority**: P1
**Status**: Draft

## Story

**As a** Implementer
**I want** apply a group with a request identifier so that retrying it, even concurrently, applies it once
**So that** a retried request after a timeout never duplicates records

## Context

The request id travels in the journal origin; the group's rows are found again by an index and duplicates serialize on a lock; no table is needed.

## Walkthrough

1. Implementer applies a group with request id `r` and a hash of its inputs.
2. Implementer applies it again.
3. Two identical requests arrive at once.
4. The id is reused with different inputs.

## Acceptance Criteria

- [ ] **US-043-AC1** — Given a group applied with a request id, when it is applied again with the same hash, then nothing changes and the original results return, rebuilt from the group's journal rows.
- [ ] **US-043-AC2** — Given two concurrent requests with one id, when both run, then the group is applied once and the other returns the original results.
- [ ] **US-043-AC3** — Given the id reused with a different hash, when applied, then it fails as `request_conflict` and nothing changes.
- [ ] **US-043-AC4** — Given the id after at least 24 hours, when applied again, then it is still honored while the journal rows are retained.

## Edge Cases

- **A group that changed nothing**: wrote no rows and is applied again.
- **An id never used**: applied normally.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Replay | US-043-AC1 | Applied | Apply again | Original results |
| Concurrent | US-043-AC2 | Two requests | Run together | Applied once |
| Conflict | US-043-AC3 | Other hash | Apply | `request_conflict` |
| Window | US-043-AC4 | 24 h later | Apply | Honored |

## Dependencies

- **Stories**: US-040
- **Feature Spec**: FEAT-003
- **Feature Requirements**: MUT-08
- **PRD Requirements**: FR-54
- **External**: CONTRACT-004, `apply_group`; SPIKE-003 F10.

## Out of Scope

None.
