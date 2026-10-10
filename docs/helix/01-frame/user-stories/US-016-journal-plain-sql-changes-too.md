---
ddx:
  id: US-016
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-004
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-016: Journal plain SQL changes too

**Feature**: FEAT-004 — Journal and History
**Feature Requirements**: JNL-02
**PRD Requirements**: FR-24
**Priority**: P0
**Status**: Draft

## Story

**As a** Auditor
**I want** require that every change, even one made with plain SQL, is journaled
**So that** no change can bypass the audit trail through the engine

## Context

A deployment chooses between the engine writing the journal and the database doing it by trigger. Exactly one admitted producer owns journal rows, versions and update timestamps. Trigger-mode support applies to the qualified native writer/privilege/operation profile; arbitrary owner-level trigger disabling or unsupported native mutation paths are not silently advertised as audited. Changing mode is an explicit administrative transition with verified target readiness and writer exclusion, rather than a caller-set flag.

## Walkthrough

1. An authorized administrator confirms the explicit transition to the installed trigger profile.
2. A user updates an Order with plain SQL.
3. System writes journal rows.
4. After the original writer transaction ends, the administrator confirms the transition to the installed engine profile and the user repeats through its declared raw-SQL profile.

## Acceptance Criteria

- [ ] **US-016-AC1** — Given trigger mode, when a change is made by plain SQL, then journal rows are written.
- [ ] **US-016-AC2** — Given trigger mode, when the engine writes, then it does not also write journal rows or the version itself.
- [ ] **US-016-AC3** — Given engine mode, when a change is made by plain SQL, then it is not journaled and the enforcement report says so.

## Edge Cases

- **Mode changed mid-transaction**: the original admitted mode/profile is protected through the writer transaction’s actual end. An administrator waits for that exclusion to end before confirming a switch. Savepoint rollback that releases native admission invalidates its cached pin; later work re-admits rather than silently changing producers.
- **Origin in trigger mode**: passed with a transaction-local setting; any role in it is ignored.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Trigger | US-016-AC1 | Trigger mode | Plain SQL update | Row written |
| No duplicate | US-016-AC2 | Trigger mode | Engine write | One set of rows |
| Engine | US-016-AC3 | Engine mode | Plain SQL | Not journaled; reported |

## Dependencies

- **Stories**: US-015
- **Feature Spec**: FEAT-004
- **Feature Requirements**: JNL-02
- **PRD Requirements**: FR-24
- **External**: CONTRACT-002, Who writes what.

## Out of Scope

None.
