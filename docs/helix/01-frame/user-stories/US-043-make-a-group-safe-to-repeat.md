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

## Selected decision handoff — 2026-10-07

ADR-005 is selected. Every request-enabled batch, including all-no-op batches, atomically stores complete original ordered results with its effects. Matching identity/full input replays, different input conflicts, and acknowledgment loss resolves through same-ID retry/lookup. Expired identities never silently reapply. Request-free groups remain receipt-free; existing complete-result protection remains independent of journal trimming.


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

FR-54 requires complete original ordered results, including no-op entries, and verified input equivalence. The journal request-index spike demonstrates bounded serialization/recovery but does not establish full replay. CONTRACT-009 owns replay ordering; ADR-005 proposes complete persistence and remains unaccepted. This story states required behavior without selecting a storage table or journal envelope.

## Walkthrough

1. Implementer applies a group with request id `r` and a hash of its inputs.
2. Implementer applies it again.
3. Two identical requests arrive at once.
4. The id is reused with different inputs.

## Acceptance Criteria

- [ ] **US-043-AC1** — Given a group applied with a request id, when it is applied again with the same verified semantic input, then nothing changes and every original ordered result returns, including no-op entries; a caller hash alone is not equality proof.
- [ ] **US-043-AC2** — Given two concurrent requests with one id, when both run, then the group is applied once and the other returns the original results.
- [ ] **US-043-AC3** — Given the id reused with different verified semantic inputs, when applied, then it fails as `request_conflict` and nothing changes, even if the caller supplies the original claimed hash.
- [ ] **US-043-AC4** — Given the id after at least 24 hours, when applied again, then it is still honored while the journal rows are retained.

## Edge Cases

- **A group that changed nothing**: its complete results and input identity remain replayable; repeat does not re-evaluate it against later data. Receipt-only persistence is a separate proposed administrative/layout decision and does not invent property-change journal rows.
- **An id never used**: applied normally.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Replay | US-043-AC1 | Applied | Apply again | Original results |
| Concurrent | US-043-AC2 | Two requests | Run together | Applied once |
| Conflict | US-043-AC3 | Other hash | Apply | `request_conflict` |
| Window | US-043-AC4 | 24 h later | Apply | Honored |

## Remaining retention reconciliation

AC4 retains its original while-journal-retained promise. ADR-005's independent receipt expiry/namespace proposal must reconcile that promise explicitly before adoption; a 24-hour receipt pass alone cannot narrow or close AC4 when journal retention is longer. Persistence, replay authorization and canonical wire profiles remain gates.

## Dependencies

- **Stories**: US-040
- **Feature Spec**: FEAT-003
- **Feature Requirements**: MUT-08
- **PRD Requirements**: FR-54
- **External**: CONTRACT-004, `apply_group`; SPIKE-003 F10.

## Out of Scope

None.
