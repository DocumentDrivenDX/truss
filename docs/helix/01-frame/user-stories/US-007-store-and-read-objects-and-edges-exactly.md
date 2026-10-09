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

## Selected decision handoff — 2026-10-07

Safe number convenience is permitted only at a lossless public boundary. Unsafe integer numbers and decimal number conversions requiring rounding refuse; exact integer/decimal carriers preserve original spelling and declared domains. Committed IDs are never reused; pending IDs remain usable only within their original transaction and are not durably published before outer commit. Internal stored numeric/time custody remains exact text/token rather than JavaScript number/Date.


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

Typical traps are integers beyond 2^53, decimals with trailing zeros, timestamp offsets and explicit null. Exact authored numeric spelling enters through the selected exact-token wire, not an ordinary JSON number that may already be rounded. Safe JavaScript number convenience requires lossless admission against the original field domain and does not invent original authored spelling. Logical readback preserves the admitted token and presence independently of native typed comparison/key witnesses.

## Walkthrough

1. Engineer creates an Order with exact decimal token `10.50`, `placedAt` `2026-10-05T09:00:00+02:00`, exact integer token `9007199254740993` and `note` null under their admitted original definitions.
2. System stores them through the selected exact-value/presence codec and qualified native homes, preserving the original numeric/time carriers.
3. Engineer reads the Order.
4. System returns each value exactly as written.

## Acceptance Criteria

- [ ] **US-007-AC1** — Given the value corpus, when each value is written and read back, then it is identical, including `10.50`, the `+02:00` offset and 9007199254740993.
- [ ] **US-007-AC2** — Given a property set to explicit null and another never set, when both are read, then they differ.
- [ ] **US-007-AC3** — Given a string containing U+0000, when it is written, then it is rejected with a reported rule.
- [ ] **US-007-AC4** — Given objects and edges created concurrently, when identifiers are compared, then no identifier repeats and none is reused after deletion.

## Edge Cases

- **Binary values**: stored as base64 text and read back identical.
- **A client that parses exact numeric tokens to doubles**: unsupported precision loss. An explicit lossless number view is permitted only after exact representability checks and retains the original token; default exact readback cannot silently discard it.

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
