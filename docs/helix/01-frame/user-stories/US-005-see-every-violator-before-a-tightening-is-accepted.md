---
ddx:
  id: US-005
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

# US-005: See every violator before a tightening is accepted

**Feature**: FEAT-001 — Catalog and Revisions
**Feature Requirements**: CAT-05, CAT-06
**PRD Requirements**: FR-5, FR-6
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** learn which stored objects would break a tightened rule before I accept it
**So that** I never tighten a schema blind

## Context

A revision that shortens a text limit may leave existing values invalid.

## Walkthrough

1. Engineer registers a revision shortening `Customer.name` to 20 characters.
2. System queries existing objects.
3. System finds three over the limit and rejects the revision, listing them.
4. Engineer fixes the three and registers again.
5. System accepts.

## Acceptance Criteria

- [ ] **US-005-AC1** — Given three objects over a tightened limit, when the revision is registered, then it is rejected and all three are listed.
- [ ] **US-005-AC2** — Given no violator, when the revision is registered, then it is accepted.
- [ ] **US-005-AC3** — Given a change of a property's type with a declared total transform, when it is registered, then the transform runs in the same acceptance and each changed value is journaled.
- [ ] **US-005-AC4** — Given a change of type with no transform, when it is registered, then it is rejected.

## Edge Cases

- **Many violators**: the list is complete, not truncated at the first.
- **A transform that cannot be total**: rejected.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| List | US-005-AC1 | 3 values over | Register | Rejected; 3 listed |
| Accept | US-005-AC2 | 0 over | Register | Accepted |
| Transform | US-005-AC3 | Type change + transform | Register | Values changed; transform rows journaled |
| No transform | US-005-AC4 | Type change | Register | Rejected |

## Dependencies

- **Stories**: US-001, US-007
- **Feature Spec**: FEAT-001
- **Feature Requirements**: CAT-05, CAT-06
- **PRD Requirements**: FR-5, FR-6
- **External**: CONTRACT-003 step 6.

## Out of Scope

None.
