---
ddx:
  id: US-001
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

# US-001: Accept a UMF revision as a whole or reject it with every reason

**Feature**: FEAT-001 — Catalog and Revisions
**Feature Requirements**: CAT-01, CAT-08
**PRD Requirements**: FR-1, FR-8
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** register a set of UMF documents and get either one accepted revision with a full report or a rejection that lists every reason
**So that** I can trust that a revision never half-applies and I can read exactly what it did

## Context

The running example is a sales model of Customer, Order and OrderLine records
and their relationships. Acceptance includes a separate complete immutable
report in the same transaction as catalog/history effects, with active-head
publication only after report completion. Staged catalog IDs or document rows
alone are not an accepted revision. In a caller-owned transaction, results remain
pending until its original outer commit is confirmed.

Every violation is reported only from a complete admitted scan. Controlled-work
exhaustion reports incomplete/resource and refuses acceptance; it cannot label
an available diagnostic prefix complete. Uncertain native termination is an
execution/recovery outcome, not rejected/unchanged.

## Walkthrough

1. Engineer registers two UMF documents, `sales` and `orders`.
2. System verifies each document and derives types, properties, keys and relationships.
3. System completes validation and original effects, persists the immutable full report, and publishes revision 1 atomically; durable acceptance is returned after confirmed commit.
4. Engineer registers a second set in which one document is invalid.
5. System rejects the whole set, reports every violation, and changes nothing.

## Acceptance Criteria

- [ ] **US-001-AC1** — Given two valid documents, when they are registered, then revision 1 exists and the report lists the elements added, the UMF versions seen and the document digests.
- [ ] **US-001-AC2** — Given a set in which one document fails validation, when it is registered, then no revision is created and the report names every violation in every document.
- [ ] **US-001-AC3** — Given an accepted revision, when its report is read, then every UMF assertion appears with an enforcement layer.

## Edge Cases

- **Empty set**: rejected as invalid.
- **A document accepted before with identical bytes**: no new revision only when the complete verified acceptance input also matches the current head (US-004). Historical matches or changed bindings/policies/profiles require current acceptance validation.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Accept | US-001-AC1 | Valid `sales` and `orders` | Register | Revision 1; report lists added elements |
| Reject | US-001-AC2 | One invalid document | Register the set | No revision; all violations named |
| Report | US-001-AC3 | Revision 1 | Read the report | Each assertion has a layer |

## Dependencies

- **Stories**: None
- **Feature Spec**: FEAT-001
- **Feature Requirements**: CAT-01, CAT-08
- **PRD Requirements**: FR-1, FR-8
- **External**: CONTRACT-003 steps 1 to 9.

## Out of Scope

None.
