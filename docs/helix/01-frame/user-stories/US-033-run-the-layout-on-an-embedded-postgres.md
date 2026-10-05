---
ddx:
  id: US-033
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-008
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-033: Run the layout on an embedded PostgreSQL

**Feature**: FEAT-008 — Host Integration
**Feature Requirements**: HST-04
**PRD Requirements**: FR-44
**Priority**: P1
**Status**: Draft

## Story

**As a** Implementer
**I want** run the layout, the corpus and my tests against an embedded PostgreSQL with no external server
**So that** tests are fast, isolated and use the same DDL as production

## Context

The spikes ran on embedded PostgreSQL 16.2 and 17.9 and each run used a fresh instance.

## Walkthrough

1. Implementer starts an embedded PostgreSQL.
2. Implementer runs the layout DDL and the check.
3. Implementer runs the corpus.
4. System reports pass.

## Acceptance Criteria

- [ ] **US-033-AC1** — Given an embedded PostgreSQL, when the layout DDL and its check run, then both pass without a separate server.
- [ ] **US-033-AC2** — Given the same DDL, when it runs on a server, then the result is the same objects.
- [ ] **US-033-AC3** — Given a fresh embedded instance per run, when two runs execute in parallel, then they do not interfere.

## Edge Cases

- **An embedded engine on a different major version than production**: reported by version.
- **Embedded engine limits**: documented where the corpus depends on a version.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| DDL | US-033-AC1 | Embedded 16.2 | Run | Pass |
| Same objects | US-033-AC2 | Server | Run | Same objects |
| Isolation | US-033-AC3 | Two runs | Parallel | No interference |

## Dependencies

- **Stories**: US-029
- **Feature Spec**: FEAT-008
- **Feature Requirements**: HST-04
- **PRD Requirements**: FR-44
- **External**: SPIKE-003 method.

## Out of Scope

None.
