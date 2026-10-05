---
ddx:
  id: US-034
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

# US-034: Repeat an import and change nothing

**Feature**: FEAT-002 — Storage, Identity and Exactness
**Feature Requirements**: STO-08
**PRD Requirements**: FR-45
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** import records so that running the same import again, even after I deleted or corrected some, changes nothing
**So that** an import can be re-run safely and never brings back what I removed

## Context

The deployment's `key_reuse` setting is `forbid`. Customers are keyed by account code; an order line is related to its order by an edge.

## Walkthrough

1. Engineer imports 51 Customers and their relationships as load `load-1`.
2. System creates each record and reports 51 created.
3. A user corrects one Customer and deletes another.
4. Engineer runs the same import as load `load-2`.
5. System skips every record and reports 51 skipped.

## Acceptance Criteria

- [ ] **US-034-AC1** — Given an import that completed, when the same records are imported again, then no record changes and the report shows all skipped.
- [ ] **US-034-AC2** — Given a Customer corrected after the first import, when the import is repeated, then the correction remains.
- [ ] **US-034-AC3** — Given a Customer deleted after the first import, when the import is repeated, then it stays deleted, because its key is in the tombstone table.
- [ ] **US-034-AC4** — Given an imported edge that was deleted, when the import is repeated, then the edge is not recreated.
- [ ] **US-034-AC5** — Given a type with no primary key, when its records are imported, then they are rejected with that reason.
- [ ] **US-034-AC6** — Given `key_reuse` is `allow`, when the deleted Customer's key is imported again, then it is created and the earlier tombstone remains.

## Edge Cases

- **An interrupted import**: running it again creates only the missing records.
- **A direct create of a reserved key under `forbid`**: refused as `key_reserved`.
- **A change of a key component**: the old value is tombstoned too.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Repeat | US-034-AC1 | 51 imported | Import again | 51 skipped; no change |
| Correction | US-034-AC2 | Customer corrected | Import again | Correction kept |
| Deleted | US-034-AC3 | Customer deleted | Import again | Stays deleted |
| Edge | US-034-AC4 | Imported edge deleted | Import again | Not recreated |
| No key | US-034-AC5 | Type without primary key | Import | Rejected |
| Allow | US-034-AC6 | `allow` | Import deleted key | Created |

## Dependencies

- **Stories**: US-009
- **Feature Spec**: FEAT-002
- **Feature Requirements**: STO-08
- **PRD Requirements**: FR-45
- **External**: CONTRACT-004, `import_batch`; CONTRACT-001, Key identity.

## Out of Scope

None.
