---
ddx:
  id: FEAT-005
  type: feature-specification
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.prd
      kind: informed_by
    - id: truss.concerns
      kind: informed_by
---

# Feature Specification: FEAT-005 — Reads and Traversal

**Feature ID**: FEAT-005
**Status**: Draft
**Priority**: P0
**Covered PRD Subsystem(s)**: Reads and traversal
**Covered PRD Requirements**: FR-28 to FR-32
**Cross-Subsystem Rationale**: None; single subsystem.

## Overview

This feature is how stored data is read: one object by identifier or key, a type's objects in pages, an object's edges, a short traversal, and the catalog's own types.

## Ideal Future State

An engineer fetches an object in a fraction of a millisecond, pages through any type at the same cost however many types exist, follows relationships one to three hops, and lists the catalog's types in one call from a single consistent revision.

## Problem Statement

- **Current situation**: Generic storage is the classic performance trap; list and traversal costs depend on how many types and indexes the layout carries.
- **Pain points**: Planning time that grows with the number of types; unbounded edge lists; type listings assembled from inconsistent reads.
- **Desired outcome**: Latency independent of the number of types, with bounded and marked results.

## Functional Areas

| Area | User question or job | Feature responsibility |
|------|----------------------|------------------------|
| Point reads | Fetch by id or key | Direct lookups returning version and revision |
| Listing | Page through a type | Keyset pages with a required limit |
| Edges | What is connected to this? | Bounded edge lists in a stable order |
| Traversal | Two hops away | One to three hops within the target |
| Enumeration | What types exist? | One revision's types, properties, keys and endpoints |

## Requirements

### Functional Requirements by Area

#### Point reads

RD-01. An object is read by identifier or by key, with its version and catalog revision (FR-28).

#### Listing

RD-02. Objects of one type are listed in keyset pages with a required limit and a marker saying whether more remain; page cost does not depend on the number of other types (FR-29).

#### Edges

RD-03. The edges of one object are listed, bounded, in stable order, with the same marker (FR-30, P1).

#### Traversal

RD-04. A traversal of one to three hops returns related objects within the latency target (FR-31, P1).

#### Enumeration

RD-05. The catalog's types are enumerated with properties, keys and endpoints, from one revision (FR-32).

### Non-Functional Requirements

- **Performance** (proposed, PRD): p95 read by id or key at most 1 ms; type enumeration at most 20 ms at 1,000 types; traversal within 2× of a hand-designed schema. Measured: 0.02 ms reads and 0.03 to 0.04 ms one-hop at 1,000 types.
- **Planning**: planning cost does not change with the number of types (0.02 and 0.04 ms at 10 and at 1,000).
- **Consistency**: an enumeration is read from one catalog revision.

## User Stories

- [US-020 — Read an object by identifier or key](../user-stories/US-020-read-an-object-by-id-or-key.md)
- [US-021 — List a type's objects in pages](../user-stories/US-021-list-a-types-objects-in-pages.md)
- [US-022 — List an object's edges, bounded](../user-stories/US-022-list-an-objects-edges-bounded.md)
- [US-023 — Traverse one to three hops](../user-stories/US-023-traverse-one-to-three-hops.md)
- [US-024 — Enumerate the types of the catalog](../user-stories/US-024-enumerate-the-types-of-the-catalog.md)

## Edge Cases and Error Handling

- **A page of a small type**: costs the same as a page of a large one; an index on `(type_id, id)` serves it, where without it a small type took 1.2 to 1.6 ms.
- **A limit above the deployment maximum**: refused as invalid.
- **An object with many edges**: the list is bounded and marked truncated.
- **A key that is incomplete**: refused as invalid.

## Success Metrics

- p95 targets met at the benchmark size on every supported PostgreSQL version (targets proposed).
- 0 reads that return values parsed inexactly.

## Constraints and Assumptions

- The traversal query language is later; this feature fixes only the storage-level reads.
- Listing order is by identifier, not by property.

## Dependencies

- **Other features**: FEAT-001 (types), FEAT-002 (the tables read).
- **External services**: PostgreSQL; interface in CONTRACT-004 (operations) and CONTRACT-001 (indexes).

## Out of Scope

- A query language and filters on properties.
- Full-text or analytic queries.
