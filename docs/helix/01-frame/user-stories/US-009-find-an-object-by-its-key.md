---
ddx:
  id: US-009
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

# US-009: Find an object by its key

**Feature**: FEAT-002 — Storage, Identity and Exactness
**Feature Requirements**: STO-04
**PRD Requirements**: FR-12
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** declare a key on a type and have the database refuse a second object with the same value
**So that** my business identifier is unique without me writing a check

## Context

Customer has an `account-code` key.

## Walkthrough

1. Engineer creates a Customer with account code `C-100`.
2. Engineer creates a second Customer with `C-100`.
3. System refuses the second.
4. Engineer looks up `C-100`.

## Acceptance Criteria

- [ ] **US-009-AC1** — Given a key on Customer, when a second Customer with the same value is created, then the database refuses it.
- [ ] **US-009-AC2** — Given two decimal key values `1.0` and `1.00`, when both are stored as keys of one type, then the second is refused as equal.
- [ ] **US-009-AC3** — Given two timestamps that differ only in offset, when both are stored as keys, then both are accepted as different keys.
- [ ] **US-009-AC4** — Given an object missing a key component, when it is stored, then it has no key row and the engine reports it.

## Edge Cases

- **A key on a type with existing objects**: key rows are built in the revision; duplicates reject it, all listed.
- **A plain SQL insert of a duplicate key**: refused by the database.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Unique | US-009-AC1 | `C-100` exists | Create another | Refused |
| Decimal | US-009-AC2 | `1.0` stored | Store `1.00` | Refused |
| Offset | US-009-AC3 | `...Z` stored | Store `...+02:00` same instant | Accepted |
| Missing | US-009-AC4 | No component | Store | No key row; reported |

## Dependencies

- **Stories**: US-007
- **Feature Spec**: FEAT-002
- **Feature Requirements**: STO-04
- **PRD Requirements**: FR-12
- **External**: CONTRACT-001, Key identity.

## Out of Scope

None.
