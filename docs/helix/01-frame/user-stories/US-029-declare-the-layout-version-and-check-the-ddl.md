---
ddx:
  id: US-029
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

# US-029: Declare the layout version and check the DDL on every version

**Feature**: FEAT-007 — Conformance and Portability
**Feature Requirements**: CNF-04, CNF-05
**PRD Requirements**: FR-39, FR-40
**Priority**: P0
**Status**: Draft

## Story

**As a** Implementer
**I want** have the layout declare a version, refuse a different major version, and pass its DDL check on every supported PostgreSQL
**So that** I never run against a layout I do not understand

## Context

The installed schema marker carries the normative layout version; SQL comments document it. The check script and independent native probes exercise constraints and behavior. Version compatibility also requires the implementation’s declared supported layout/runtime/profile range and independently verified installed inventory. A marker or matching major alone cannot establish complete routines, grants, codecs or data conversion. Physical upgrades use the explicit Truss migration system; connecting or inspecting status never performs an upgrade. The listed PostgreSQL versions are qualification targets inherited from the spikes, not evidence that the complete release installer already passes.

## Walkthrough

1. Implementer connects to a database with layout major version 2.
2. System refuses.
3. Implementer runs the DDL and check on 16.2 and 17.9.
4. System passes both.

## Acceptance Criteria

- [ ] **US-029-AC1** — Given a database with a different major layout version, when an implementation starts, then it refuses.
- [ ] **US-029-AC2** — Given the layout DDL, when it and its check run on each supported version, then both pass.
- [ ] **US-029-AC3** — Given the check, when it runs, then it exercises keys, endpoints, deletion, exact values, the journal partitions and the absence of a default partition.

## Edge Cases

- **An unsupported PostgreSQL version**: reported unverified.
- **A minor version difference**: accepted only within the declared compatible range and after complete required installed correspondence. Unknown or drifted same-major state refuses admission; it is never automatically repaired or migrated.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Refuse | US-029-AC1 | Major 2 | Start | Refused |
| Versions | US-029-AC2 | 16.2, 17.9 | Run DDL and check | Pass |
| Coverage | US-029-AC3 | Check | Review | Covers listed behaviors |

## Dependencies

- **Stories**: US-007
- **Feature Spec**: FEAT-007
- **Feature Requirements**: CNF-04, CNF-05
- **PRD Requirements**: FR-39, FR-40
- **External**: `storage-layout.sql`, `storage-layout.check.sql`.

## Out of Scope

None.
