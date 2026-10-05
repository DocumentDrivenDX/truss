---
ddx:
  id: US-014
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

# US-014: Keep cross-row rules honest

**Feature**: FEAT-003 — Mutation and Concurrency
**Feature Requirements**: MUT-06
**PRD Requirements**: FR-21
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** have rules such as every Order has at least one OrderLine enforced safely under concurrency and reported for what they are
**So that** I do not mistake an engine check for a database guarantee

## Context

A deferred trigger under READ COMMITTED can be violated by two concurrent transactions.

## Walkthrough

1. Engineer declares minimum multiplicity one for Order to OrderLine.
2. The write protocol locks the parent Order and checks the count.
3. Two transactions try to remove the last two lines.
4. One succeeds; the other fails.
5. The report classifies the rule as engine enforcement.

## Acceptance Criteria

- [ ] **US-014-AC1** — Given a minimum multiplicity, when two transactions concurrently remove the last two lines, then at most one commits.
- [ ] **US-014-AC2** — Given the same rule enforced by a deferred trigger alone under READ COMMITTED, when the report is generated, then it is not classified as database enforcement.
- [ ] **US-014-AC3** — Given the rule enforced under a parent lock, when the report is generated, then it is classified as engine enforcement.

## Edge Cases

- **SERIALIZABLE instead of a lock**: allowed; classification follows what was tested.
- **A caller that bypasses the engine**: the rule can be violated; the report says so.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Race | US-014-AC1 | 2 lines | Remove both concurrently | Only one commits |
| Trigger only | US-014-AC2 | Deferred trigger | Report | Not database |
| Parent lock | US-014-AC3 | Parent lock | Report | Engine |

## Dependencies

- **Stories**: US-012
- **Feature Spec**: FEAT-003
- **Feature Requirements**: MUT-06
- **PRD Requirements**: FR-21
- **External**: CONTRACT-004, Cross-row rules.

## Out of Scope

None.
