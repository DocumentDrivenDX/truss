---
ddx:
  id: US-012
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

# US-012: Write with one protocol and report every violation

**Feature**: FEAT-003 — Mutation and Concurrency
**Feature Requirements**: MUT-01, MUT-02, MUT-05
**PRD Requirements**: FR-16, FR-19, FR-20
**Priority**: P0
**Status**: Draft

## Story

**As a** Implementer
**I want** run every write through one documented protocol and receive every violation and a defined error kind
**So that** my implementation behaves the same as any other over one database

## Context

The protocol: check the catalog head, lock the target, check the expected version, validate, apply, journal, commit.

## Walkthrough

1. Implementer writes an Order with two invalid properties.
2. System validates against the catalog.
3. System refuses and reports both violations with rule, path and message.
4. Implementer writes a valid change with the wrong expected version.
5. System refuses as a version conflict.

## Acceptance Criteria

- [ ] **US-012-AC1** — Given a write with two violations, when it runs, then both are reported and nothing is stored.
- [ ] **US-012-AC2** — Given an expected version that differs from the stored one, when the write runs, then it fails as a version conflict with no change.
- [ ] **US-012-AC3** — Given a write that changes no value, when it runs, then it writes nothing and does not raise the version.
- [ ] **US-012-AC4** — Given each failure kind, when it occurs, then the error kind and its retry rule are as defined.

## Edge Cases

- **Unknown values**: retained and reported, not an error.
- **Deadlock**: reported as retry; nothing changed.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| All violations | US-012-AC1 | Two invalid props | Write | Both reported; nothing stored |
| Version | US-012-AC2 | Stored v3, expected v2 | Write | Version conflict |
| No-op | US-012-AC3 | Same value | Write | No rows; no version change |
| Kinds | US-012-AC4 | Each failure | Trigger | Defined kind, retry rule |

## Dependencies

- **Stories**: None
- **Feature Spec**: FEAT-003
- **Feature Requirements**: MUT-01, MUT-02, MUT-05
- **PRD Requirements**: FR-16, FR-19, FR-20
- **External**: CONTRACT-004, Write protocol and Error kinds.

## Out of Scope

None.
