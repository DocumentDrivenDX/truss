---
ddx:
  id: US-020
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-005
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-020: Read an object by identifier or key

**Feature**: FEAT-005 — Reads and Traversal
**Feature Requirements**: RD-01
**PRD Requirements**: FR-28
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** fetch one object by its identifier or by a key value and see its version and catalog revision
**So that** single reads are a fast, exact lookup

## Context

Both lookups are direct: by complete typed identity `(id, type)` or by the admitted qualified key definition, ordered exact components and encoding profile through the selected native key home. Caller-supplied canonical text or a route digest cannot bypass component/owner/domain admission or establish equality. Observe the key membership and object in one qualified coherent context. Read results distinguish the original last-written revision from the current read catalog revision; a definition-only acceptance cannot relabel an unchanged record as newly written.

## Walkthrough

1. Engineer reads Order 1043 by identifier.
2. System returns it with version and revision.
3. Engineer reads Customer by account code `C-100`.
4. System returns the same kind of result.

## Acceptance Criteria

- [ ] **US-020-AC1** — Given an Order, when it is read by identifier, then its properties, version and the revision it was last written under are returned.
- [ ] **US-020-AC2** — Given a key value, when the object is looked up by key, then the object holding it is returned.
- [ ] **US-020-AC3** — Given a key with several components, when it is looked up with all components, then the canonical text is built and the object is returned.
- [ ] **US-020-AC4** — Given an incomplete key, when it is looked up, then the request is refused as invalid.

## Edge Cases

- **Absent identifier or key under a complete admitted lookup**: not found, not an empty object, under the selected disclosure policy. Unsupported comparison/encoding, truncated native observation, stale mapping or unavailable authority cannot prove absence and returns the defined refusal/unavailable outcome without a record payload.
- **Values read**: complete logical values preserve exact carriers and distinguish absence, present null and empty content under original definition/presence pins. A current lookup is not historical business-key reconstruction under an arbitrary old catalog.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| By id | US-020-AC1 | Order 1043 | Read | Properties, version, revision |
| By key | US-020-AC2 | `C-100` | Look up | Customer returned |
| Composite | US-020-AC3 | 2-part key | Look up | Returned |
| Incomplete | US-020-AC4 | 1 of 2 parts | Look up | Invalid |

## Dependencies

- **Stories**: US-007, US-009
- **Feature Spec**: FEAT-005
- **Feature Requirements**: RD-01
- **PRD Requirements**: FR-28
- **External**: CONTRACT-004, `get_object` and `find_by_key`.

## Out of Scope

None.
