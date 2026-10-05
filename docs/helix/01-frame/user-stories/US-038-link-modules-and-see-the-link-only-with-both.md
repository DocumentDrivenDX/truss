---
ddx:
  id: US-038
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

# US-038: Link modules and see the link only with access to both

**Feature**: FEAT-008 — Host Integration
**Feature Requirements**: HST-06
**PRD Requirements**: FR-49
**Priority**: P1
**Status**: Draft

## Story

**As a** Data platform engineer
**I want** declare a relationship from a type in one module to a type in another and have it seen only by a role that can read both
**So that** a link never reveals another team's objects to a role that cannot read them

## Context

UMF allows a relationship in one module to name a type defined in another; the relationship's own module is the one that declares it.

## Walkthrough

1. Engineer registers `billing` with a relationship `bills` whose source type is in `sales`.
2. System accepts it; the relationship's module is `billing`.
3. An edge is created between a `sales` order and a `billing` invoice.
4. A `sales` reader and a role that reads both look at the edge.

## Acceptance Criteria

- [ ] **US-038-AC1** — Given a relationship in `billing` naming a `sales` type, when it is registered, then it is accepted and its module is `billing`.
- [ ] **US-038-AC2** — Given an edge across the two modules, when a role that reads only `sales` lists edges, then the edge is absent.
- [ ] **US-038-AC3** — Given the same edge, when a role that reads both modules lists edges, then it is present.
- [ ] **US-038-AC4** — Given a writer of `billing` that cannot read `sales`, when it creates the edge, then the database refuses it.

## Edge Cases

- **The target module not yet declared**: the unknown-endpoint policy applies (US-003).
- **Existence leaks through foreign-key and unique checks**: documented; the host decides how to report them.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Register | US-038-AC1 | Relationship across modules | Register | Accepted |
| Hidden | US-038-AC2 | `sales` reader | List edges | Absent |
| Both | US-038-AC3 | Reads both | List edges | Present |
| Writer | US-038-AC4 | `billing` writer, no `sales` | Create edge | Refused |

## Dependencies

- **Stories**: US-037, US-003
- **Feature Spec**: FEAT-008
- **Feature Requirements**: HST-06
- **PRD Requirements**: FR-49
- **External**: CONTRACT-005, Cross-module edges.

## Out of Scope

None.
