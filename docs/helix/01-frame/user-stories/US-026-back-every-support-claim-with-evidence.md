---
ddx:
  id: US-026
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-006
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-026: Back every support claim with evidence

**Feature**: FEAT-006 — Enforcement Reporting
**Feature Requirements**: ENF-03
**PRD Requirements**: FR-34
**Priority**: P0
**Status**: Draft

## Story

**As a** Implementer
**I want** read a support statement that names the versions it was tested on and links the test
**So that** I do not rely on a claim nobody ran

## Context

A support claim requires evidence of the behavior actually advertised under its exact tested implementation/build, layout, UMF subset, driver, security/resource and deployment profiles. Source/schema/type checks and component-native tests retain their limited scope; they cannot establish complete engine support. Historical evidence remains immutable and linked to its original artifacts, while current installed drift or changed dependencies invalidate its use as a current guarantee until the required qualification is repeated. Missing evidence is unverified, not a successful optional omission.

## Walkthrough

1. Implementer opens the support statement for PostgreSQL 17.
2. System shows the PostgreSQL version, the UMF version and subset, and links each test.
3. Implementer opens the statement for a version not tested.

## Acceptance Criteria

- [ ] **US-026-AC1** — Given a support statement, when it is read, then it names the PostgreSQL version and the UMF version and links the executable evidence.
- [ ] **US-026-AC2** — Given a version with no evidence, when its statement is read, then it says unverified.
- [ ] **US-026-AC3** — Given a changed contract, when the evidence is regenerated, then the statement shows the new run.

## Edge Cases

- **A test that fails on one version**: the statement shows the failure.
- **Evidence older than the contract**: determine correspondence against exact original artifact/profile pins; changed governing behavior makes the affected claim stale. Regenerating an index or hash receipt without rerunning the required behavioral tests does not refresh qualification.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Named | US-026-AC1 | Statement | Read | Versions and links |
| Unverified | US-026-AC2 | PostgreSQL 18 | Read | Unverified |
| Stale | US-026-AC3 | Contract changed | Read | Flagged |

## Dependencies

- **Stories**: US-025
- **Feature Spec**: FEAT-006
- **Feature Requirements**: ENF-03
- **PRD Requirements**: FR-34
- **External**: Evidence index.

## Out of Scope

None.
