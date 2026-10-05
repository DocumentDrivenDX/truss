---
ddx:
  id: US-037
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-008
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-037: Give roles access to modules and nothing else

**Feature**: FEAT-008 — Host Integration
**Feature Requirements**: HST-05
**PRD Requirements**: FR-48
**Priority**: P1
**Status**: Draft

## Story

**As a** Implementer
**I want** let a role read and write only the UMF modules it is given, enforced by the database
**So that** teams own their modules and cannot see or change another team's

## Context

Modules `sales` and `billing` each have a reader and a writer role. A role may read several modules by being named as their reader.

## Walkthrough

1. Implementer adds `module_access` rows for `sales` and `billing` and applies the policy set.
2. Implementer calls the grant helper for each module.
3. The `sales` writer reads and writes.
4. The `billing` writer does the same.
5. A role with no module reads.

## Acceptance Criteria

- [ ] **US-037-AC1** — Given the `sales` writer role, when it reads, then it sees only `sales` objects, edges, keys, journal rows, tombstones and catalog definitions.
- [ ] **US-037-AC2** — Given the `sales` writer role, when it writes a `billing` object, then the database refuses it.
- [ ] **US-037-AC3** — Given a reader role named for a module, when it writes, then the database refuses it.
- [ ] **US-037-AC4** — Given a role with no module, when it reads, then it sees no rows.
- [ ] **US-037-AC5** — Given the acting role is set for the transaction, when a function owned by another role reads on its behalf, then the policies apply to the acting role, not the owner.
- [ ] **US-037-AC6** — Given 1,000 types and 10 modules, when a read by id runs with the policies on, then it costs at most 0.01 ms more than with the role alone.

## Edge Cases

- **A superuser or `BYPASSRLS` role**: not subject to the policies.
- **Schema documents and settings**: never granted to module roles.
- **The layer not applied**: truss behaves as without it.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Own module | US-037-AC1 | `sales` writer | Read | `sales` rows only |
| Other module | US-037-AC2 | `sales` writer | Write `billing` | Refused |
| Reader | US-037-AC3 | Reader role | Write | Refused |
| No module | US-037-AC4 | No row | Read | Nothing |
| Acting role | US-037-AC5 | Function owned by another role | Read | Acting role's view |
| Cost | US-037-AC6 | Benchmark | Read by id | ≤ 0.01 ms extra |

## Dependencies

- **Stories**: US-031
- **Feature Spec**: FEAT-008
- **Feature Requirements**: HST-05
- **PRD Requirements**: FR-48
- **External**: CONTRACT-005; SPIKE-003 F8.

## Out of Scope

None.
