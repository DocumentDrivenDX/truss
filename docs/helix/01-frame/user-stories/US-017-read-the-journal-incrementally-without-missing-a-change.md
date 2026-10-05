---
ddx:
  id: US-017
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

# US-017: Read the journal incrementally without missing a change

**Feature**: FEAT-004 — Journal and History
**Feature Requirements**: JNL-04
**PRD Requirements**: FR-25
**Priority**: P0
**Status**: Draft

## Story

**As a** Implementer
**I want** consume journal rows in a stable order and never miss a row that commits late
**So that** a downstream copy of the changes is complete

## Context

Sequence numbers are assigned at insert, not commit, so a later number can become visible first.

## Walkthrough

1. Transaction A writes a row and stays open.
2. Transaction B writes a later row and commits.
3. Consumer reads.
4. System withholds B's row.
5. A commits; the consumer reads again and gets both in order.

## Acceptance Criteria

- [ ] **US-017-AC1** — Given an older open transaction, when the consumer reads, then the newer committed row is withheld.
- [ ] **US-017-AC2** — Given the older transaction commits, when the consumer reads again, then both rows are returned in order.
- [ ] **US-017-AC3** — Given a saved position ahead of the safe watermark, when the consumer reads, then it receives nothing until the watermark passes it.

## Edge Cases

- **Using the sequence number or timestamp as a watermark**: unsafe and not permitted.
- **Long-running transaction**: delays the consumer; documented.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Withhold | US-017-AC1 | A open, B committed | Read | B withheld |
| Both | US-017-AC2 | A commits | Read | A and B in order |
| Ahead | US-017-AC3 | Position ahead | Read | Nothing |

## Dependencies

- **Stories**: US-015
- **Feature Spec**: FEAT-004
- **Feature Requirements**: JNL-04
- **PRD Requirements**: FR-25
- **External**: CONTRACT-002, Ordering and the consumer watermark.

## Out of Scope

None.
