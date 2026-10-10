---
ddx:
  id: US-006
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-001
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-006: Add a type without DDL

**Feature**: FEAT-001 — Catalog and Revisions
**Feature Requirements**: CAT-07
**PRD Requirements**: FR-7
**Priority**: P0
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** add an entity type, a property and a relationship with no table, column or index change
**So that** schema evolution never needs a migration or a lock on my data tables

## Context

The fixed shared layout avoids per-type physical DDL. Adding the fixture’s type/property/relationship uses catalog rows and complete acceptance/report/head effects; other revisions may also perform validated backfill, rebind or transforms under their separate atomic protocols. DDL-free does not mean lock-free: acceptance intentionally holds catalog exclusion and any required validation/data locks. The continuous-writer criterion concerns the declared add-only workload and admission profile, not arbitrary long host transactions or data-changing revisions. Physical layout/runtime upgrades remain explicit, infrequent Truss migrations.

## Walkthrough

1. Engineer registers a revision adding `Shipment` and a relationship to `Order`.
2. System inserts catalog rows.
3. Writers obey catalog admission and resume after the acceptance’s qualified exclusion ends.
4. Engineer lists the database's tables and indexes before and after.

## Acceptance Criteria

- [ ] **US-006-AC1** — Given the table and index list before a revision, when the revision adds a type, a property and a relationship, then the list is identical afterward.
- [ ] **US-006-AC2** — Given sixteen continuous writers, when a revision is accepted, then the writers are delayed only by the catalog head wait and none fails.
- [ ] **US-006-AC3** — Given 1,000 existing types, when a type is added, then acceptance completes within the same order of time as with 10.

## Edge Cases

- **An index declared by a binding**: retained as an exact pending declaration in the immutable acceptance report. Separately authorized postcommit tooling may build it after confirmed acceptance; no DDL occurs inside acceptance, and current readiness is reported separately without rewriting the original report. The unchanged physical-inventory fixture uses no index declaration.
- **A revision that adds a key to a populated type**: builds its key rows in the acceptance and reports the count.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| No DDL | US-006-AC1 | Tables listed | Add type, property, relationship | No change to the list |
| Writers | US-006-AC2 | 16 writers | Accept a revision | No failure; short wait |
| Scale | US-006-AC3 | 10 vs 1,000 types | Add a type | Comparable time |

## Dependencies

- **Stories**: US-001
- **Feature Spec**: FEAT-001
- **Feature Requirements**: CAT-07
- **PRD Requirements**: FR-7
- **External**: SPIKE-003 F2.

## Out of Scope

None.
