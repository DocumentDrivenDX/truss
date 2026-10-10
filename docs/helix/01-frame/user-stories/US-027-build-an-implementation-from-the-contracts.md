---
ddx:
  id: US-027
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

# US-027: Build an implementation from the contracts

**Feature**: FEAT-007 — Conformance and Portability
**Feature Requirements**: CNF-01, CNF-02
**PRD Requirements**: FR-36, FR-37
**Priority**: P0
**Status**: Draft

## Story

**As a** Implementer
**I want** implement truss in another language from contracts and a corpus alone
**So that** my implementation matches the specification without reading anyone's code

## Context

The first implementation is TypeScript; the contracts are independent of it.

## Walkthrough

1. Implementer reads the layout, journal, catalog revision and mutation contracts.
2. Implementer loads the corpus manifest.
3. Implementer runs each case and compares results, state, journal and report.

## Acceptance Criteria

- [ ] **US-027-AC1** — Given the contracts, when an operation is implemented from them, then every behavior it needs is stated without reference to any language.
- [ ] **US-027-AC2** — Given the corpus, when a case is read, then it names setup, operations and normative expected results, state, journal and report, and informative expected SQL.
- [ ] **US-027-AC3** — Given aliases in a case, when it is run, then real identifiers are never compared.

## Edge Cases

- **An unknown case tag**: an unselected optional case may be outside the declared profile; unknown semantics in a required case refuse full-profile conformance and must not be counted as a pass.
- **A case contradicting an accepted decision**: a defect in the case.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Language-neutral | US-027-AC1 | Contracts | Review | No language dependency |
| Case shape | US-027-AC2 | A case | Read | All elements present |
| Aliases | US-027-AC3 | Case with aliases | Run | Ids not compared |

## Dependencies

- **Stories**: None
- **Feature Spec**: FEAT-007
- **Feature Requirements**: CNF-01, CNF-02
- **PRD Requirements**: FR-36, FR-37
- **External**: CONTRACT-004, Conformance corpus.

## Out of Scope

None.
