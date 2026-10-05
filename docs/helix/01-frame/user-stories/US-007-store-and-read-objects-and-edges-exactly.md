---
ddx:
  id: US-007
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

# US-007: Store and read objects and edges exactly

**Feature**: FEAT-002 — Storage, Identity and Exactness
**Feature Requirements**: STO-01, STO-02, STO-07
**PRD Requirements**: FR-9, FR-10, FR-15
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** write values of every UMF scalar family and read them back exactly
**So that** no value is rounded, re-encoded or coerced on the way

## Context

Typical traps are integers beyond 2^53, decimals with trailing zeros, timestamp offsets and explicit null.

## Walkthrough

1. Engineer creates an Order with `total` 10.50, `placedAt` `2026-10-05T09:00:00+02:00`, `count` 9007199254740993 and `note` null.
2. System stores them in the property map.
3. Engineer reads the Order.
4. System returns each value exactly as written.

## Acceptance Criteria

- [ ] **US-007-AC1** — Given the value corpus, when each value is written and read back, then it is identical, including `10.50`, the `+02:00` offset and 9007199254740993.
- [ ] **US-007-AC2** — Given a property set to explicit null and another never set, when both are read, then they differ.
- [ ] **US-007-AC3** — Given a string containing U+0000, when it is written, then it is rejected with a reported rule.
- [ ] **US-007-AC4** — Given objects and edges created concurrently, when identifiers are compared, then no identifier repeats and none is reused after deletion.

## Edge Cases

- **Binary values**: stored as base64 text and read back identical.
- **A client that parses numbers to doubles**: a defect; values are read as text and parsed exactly.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Exact | US-007-AC1 | Value corpus | Write, read | Identical |
| Null | US-007-AC2 | null vs unset | Read both | Distinguished |
| U+0000 | US-007-AC3 | String with U+0000 | Write | Rejected, rule reported |
| Ids | US-007-AC4 | Concurrent creates, deletes | Compare ids | Unique, not reused |

## Dependencies

- **Stories**: US-001
- **Feature Spec**: FEAT-002
- **Feature Requirements**: STO-01, STO-02, STO-07
- **PRD Requirements**: FR-9, FR-10, FR-15
- **External**: CONTRACT-001, Values.

## Out of Scope

None.
