---
ddx:
  id: US-008
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

# US-008: Keep what the schema does not define

**Feature**: FEAT-002 — Storage, Identity and Exactness
**Feature Requirements**: STO-03
**PRD Requirements**: FR-11
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** import data with fields the schema does not know and have them kept and listed
**So that** an import never loses information quietly

## Context

Imported order data may carry fields no document defines. Retention preserves the exact original name, recursive value and presence under the admitted value profile; it does not authorize truncation or coercion to make unsupported content fit. Rebinding requires the complete qualified owning definition and unambiguous original name correspondence, a valid final candidate and an absent destination. Matching display text alone cannot cross owners or overwrite an existing defined value, including present null. Incompatible or ambiguous candidates refuse the whole revision and preserve retained data, prior definitions and head.

## Walkthrough

1. Engineer imports 100 Orders, three of which carry `giftWrap`.
2. System stores the three values under their original name.
3. System reports them as retained.
4. Engineer registers a revision defining `giftWrap`.
5. After complete correspondence, destination and final-state validation, system re-binds the three values atomically, journals each and stores the complete acceptance report before publishing the new head.

## Acceptance Criteria

- [ ] **US-008-AC1** — Given an object with an undefined field, when it is written, then the value is retained under its original name and appears in the retained-value report.
- [ ] **US-008-AC2** — Given retained values, when a revision defines the matching property, then each value is re-bound, one journal row each, and the report lists them.
- [ ] **US-008-AC3** — Given the import corpus, when it is imported, then 0 values are dropped.

## Edge Cases

- **Retained data matching nothing after a revision**: stays retained.
- **A retained value and a later write to the same name**: follows the protocol; the retained entry is replaced only by re-binding.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Retain | US-008-AC1 | Order with `giftWrap` | Write | Retained; reported |
| Re-bind | US-008-AC2 | 3 retained | Define `giftWrap` | 3 rebind rows |
| No loss | US-008-AC3 | Import corpus | Import | 0 dropped |

## Dependencies

- **Stories**: US-007, US-001
- **Feature Spec**: FEAT-002
- **Feature Requirements**: STO-03
- **PRD Requirements**: FR-11
- **External**: CONTRACT-001, Values; CONTRACT-003, Unknown entity types.

## Out of Scope

None.
