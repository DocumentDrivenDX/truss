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

A deployment chooses between the engine writing the journal and the database doing it by trigger.

## Walkthrough

1. Auditor sets the journal mode to trigger.
2. A user updates an Order with plain SQL.
3. System writes journal rows.
4. Auditor sets the mode to engine and repeats.

## Acceptance Criteria

- [ ] **US-016-AC1** — Given trigger mode, when a change is made by plain SQL, then journal rows are written.
- [ ] **US-016-AC2** — Given trigger mode, when the engine writes, then it does not also write journal rows or the version itself.
- [ ] **US-016-AC3** — Given engine mode, when a change is made by plain SQL, then it is not journaled and the enforcement report says so.

## Edge Cases

- **Mode changed mid-transaction**: not allowed; the mode is read before the write begins.
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
