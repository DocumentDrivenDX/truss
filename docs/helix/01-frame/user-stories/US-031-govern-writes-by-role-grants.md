---
ddx:
  id: US-031
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

# US-031: Govern writes by role grants

**Feature**: FEAT-008 — Host Integration
**Feature Requirements**: HST-02
**PRD Requirements**: FR-42
**Priority**: P1
**Status**: Draft

## Story

**As a** Implementer
**I want** assume a database role for each transaction and have the journal record it
**So that** database grants decide who can write, and the audit shows the role

## Context

`SET LOCAL ROLE` with a grant that is settable but not inherited keeps the connecting identity powerless on its own.

## Walkthrough

1. Implementer grants role `w` with set but no inherit.
2. Implementer begins a transaction and sets the role.
3. Implementer writes.
4. Auditor reads the journal.

## Acceptance Criteria

- [ ] **US-031-AC1** — Given a connecting identity without a role, when it writes, then the database refuses.
- [ ] **US-031-AC2** — Given the identity assumed role `w` for one transaction, when it writes, then the change commits and the journal records `w`.
- [ ] **US-031-AC3** — Given the transaction ends, when the next one begins, then the role is not retained.

## Edge Cases

- **A pooler in transaction mode**: the role is set per transaction and lasts no longer.
- **A role the caller names but does not hold**: refused by the database.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| No role | US-031-AC1 | Identity only | Write | Refused |
| Role | US-031-AC2 | Role `w` | Write | Committed; role in journal |
| Reset | US-031-AC3 | Next transaction | Write | Refused |

## Dependencies

- **Stories**: US-015
- **Feature Spec**: FEAT-008
- **Feature Requirements**: HST-02
- **PRD Requirements**: FR-42
- **External**: CONTRACT-002, `db_role`.

## Out of Scope

None.
