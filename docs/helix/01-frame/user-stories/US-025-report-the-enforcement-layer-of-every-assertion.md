---
ddx:
  id: US-025
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

# US-025: Report the enforcement layer of every assertion

**Feature**: FEAT-006 — Enforcement Reporting
**Feature Requirements**: ENF-01, ENF-02
**PRD Requirements**: FR-33, FR-35
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** see, for every UMF assertion, whether PostgreSQL, truss or nothing enforces it
**So that** I know what to rely on before go-live

## Context

SPIKE-002's model had 19 assertions, all enforced; the model carries rules of every kind.

## Walkthrough

1. Engineer registers the sales model.
2. System reports each assertion with a layer and rule name.
3. Engineer checks a key, a maximum length, a cross-row rule and an opaque text rule.

## Acceptance Criteria

- [ ] **US-025-AC1** — Given the sales model, when it is accepted, then every assertion has a status of database, engine or none, with its rule name.
- [ ] **US-025-AC2** — Given a key, when the report is read, then it is database enforcement and a test that attempts a duplicate by plain SQL fails.
- [ ] **US-025-AC3** — Given a rule enforced only by the engine, when the report is read, then it is not database enforcement.
- [ ] **US-025-AC4** — Given a rule UMF carries as opaque text, when the report is read, then it is none.

## Edge Cases

- **A status that differs between PostgreSQL versions**: reported per version.
- **A rule with no test**: not reported as enforced.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| All classified | US-025-AC1 | Sales model | Accept | No unclassified assertion |
| Key | US-025-AC2 | Key | Bypass attempt | Fails; status database |
| Engine rule | US-025-AC3 | Cross-row rule | Report | Engine |
| Opaque | US-025-AC4 | Text rule | Report | None |

## Dependencies

- **Stories**: US-001
- **Feature Spec**: FEAT-006
- **Feature Requirements**: ENF-01, ENF-02
- **PRD Requirements**: FR-33, FR-35
- **External**: CONTRACT-003, Report; SPIKE-002 enforcement matrix.

## Out of Scope

None.
