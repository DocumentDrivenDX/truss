---
ddx:
  id: US-030
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

# US-030: Extend the layout from a host

**Feature**: FEAT-008 — Host Integration
**Feature Requirements**: HST-01
**PRD Requirements**: FR-41
**Priority**: P1
**Status**: Draft

## Story

**As a** Implementer
**I want** add my own schema, triggers and row-level security around truss's tables without changing them
**So that** my application's policy and audit needs are met without forking the layout

## Context

The extension rules list what a host may and may not do. Support names an exact trusted extension/installation/security profile tested against the required corpus; arbitrary host code cannot silently change canonical values, enforcement or journal ownership. A separate host ledger remains distinct from Truss’s complete semantic journal.

## Walkthrough

1. Implementer creates a schema with a ledger table and a trigger on `object`.
2. Implementer enables and forces row-level security with a policy on `object`.
3. Implementer attempts to add a column to `object`.

## Acceptance Criteria

- [ ] **US-030-AC1** — Given a host schema, when it adds tables, functions, roles and triggers, then truss operations continue to pass the corpus.
- [ ] **US-030-AC2** — Given row-level security forced on `object`, `object_key` and `edge`, when a role reads, then it sees only what the policy allows.
- [ ] **US-030-AC3** — Given an attempt to add, drop or alter a truss column or constraint, when it is made, then it violates the contract and the layout check reports it.

## Edge Cases

- **Foreign-key and unique checks under row-level security**: can reveal a hidden row exists; the host decides how to report it.
- **Host triggers writing the journal**: allowed only as the selected qualified trigger-mode producer under CONTRACT-002’s exclusive ownership, full event/version and native admission rules. An additional independent journal writer is not admitted by trigger mode; a separate host ledger does not become a second Truss journal.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Host objects | US-030-AC1 | Host schema | Add | Corpus passes |
| RLS | US-030-AC2 | Forced RLS | Read | Policy applied |
| No alter | US-030-AC3 | Add column | Run check | Reported |

## Dependencies

- **Stories**: US-016
- **Feature Spec**: FEAT-008
- **Feature Requirements**: HST-01
- **PRD Requirements**: FR-41
- **External**: CONTRACT-001, Extension rules.

## Out of Scope

None.
