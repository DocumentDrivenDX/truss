---
ddx:
  id: US-035
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-002
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-035: Keep the source facts of an imported record

**Feature**: FEAT-002 — Storage, Identity and Exactness
**Feature Requirements**: STO-09
**PRD Requirements**: FR-46
**Priority**: P0
**Status**: Draft

## Story

**As a** Auditor
**I want** see which load brought a record in and what its source said about it
**So that** the person who ran the import is never mistaken for the original author

## Context

Journal origin already names the load and who initiated it; the source's own author and time are a separate fact.

## Walkthrough

1. Engineer imports a finding whose source says author `seed-author` and date `2026-08-14`.
2. System creates the finding and one source row.
3. Auditor reads the finding's source facts.
4. A user then edits the finding.

## Acceptance Criteria

- [ ] **US-035-AC1** — Given an imported record with a source author and time, when it is read, then the load id and those facts are returned.
- [ ] **US-035-AC2** — Given a record imported with no source author, when it is read, then the author is absent, not defaulted.
- [ ] **US-035-AC3** — Given a later edit, when the source facts are read again, then they are unchanged.
- [ ] **US-035-AC4** — Given a record created directly, not imported, when its source facts are requested, then there are none.

## Edge Cases

- **The operator who ran the import**: recorded in the journal origin as the initiator, never as the source author.
- **Source facts with unknown keys**: kept as given.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Present | US-035-AC1 | Source author `seed-author` | Read | Load id, author and time |
| Absent | US-035-AC2 | No author | Read | Author absent |
| Stable | US-035-AC3 | Edited | Read | Unchanged |
| Direct | US-035-AC4 | Direct create | Read | No source row |

## Dependencies

- **Stories**: US-034
- **Feature Spec**: FEAT-002
- **Feature Requirements**: STO-09
- **PRD Requirements**: FR-46
- **External**: CONTRACT-001, `record_source`.

## Out of Scope

None.
