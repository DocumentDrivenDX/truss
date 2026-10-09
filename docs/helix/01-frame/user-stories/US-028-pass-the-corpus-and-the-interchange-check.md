---
ddx:
  id: US-028
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-007
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-028: Pass the corpus and the interchange check

**Feature**: FEAT-007 — Conformance and Portability
**Feature Requirements**: CNF-03
**PRD Requirements**: FR-38
**Priority**: P0
**Status**: Draft

## Story

**As a** Implementer
**I want** prove my implementation passes the corpus on a named PostgreSQL version and interoperates with another
**So that** two implementations can share one database

## Context

Interchange means each implementation reads what the other wrote in both directions on the exact shared installed layout/profile. Each direction must also match independently authored normative expectations: two implementations agreeing on the same wrong result do not pass. Shared protected PostgreSQL enforcement and the Weft compiler may be common dependencies, but host orchestration, original result observations and interchange evidence must identify their actual implementation/dependency boundaries. Two wrappers around the same host implementation are not a second implementation.

## Walkthrough

1. Implementer runs the corpus on PostgreSQL 16.
2. System reports pass or the failing cases.
3. Implementer runs the interchange check against the TypeScript engine.
4. System reports agreement.

## Acceptance Criteria

- [ ] **US-028-AC1** — Given a corpus version, when every case yields the expected results, state, journal and report, then the implementation passes on that engine version and the report names the versions.
- [ ] **US-028-AC2** — Given implementations A and B, when A runs a case and B reads the state and journal, then they agree, and the reverse.
- [ ] **US-028-AC3** — Given a divergence, when the check runs, then it reports it as a defect in an implementation or in the contract.

## Edge Cases

- **A host extension case**: tagged outside the base corpus pass rule, with any separately advertised extension qualification stated explicitly. Tags cannot remove required base semantics or turn a missing required case into a pass.
- **A newer corpus than the implementation**: reported, never silently passed.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Pass | US-028-AC1 | Corpus | Run | All cases pass; versions reported |
| Interchange | US-028-AC2 | A and B | Cross-run | Agree |
| Divergence | US-028-AC3 | Difference | Check | Reported |

## Dependencies

- **Stories**: US-027
- **Feature Spec**: FEAT-007
- **Feature Requirements**: CNF-03
- **PRD Requirements**: FR-38
- **External**: CONTRACT-004, Pass rule and Interchange check.

## Out of Scope

None.
