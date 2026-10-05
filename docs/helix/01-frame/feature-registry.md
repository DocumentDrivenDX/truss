---
ddx:
  id: feature-registry
  type: feature-registry
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.prd
      kind: informed_by
---

# Feature Registry

**Status**: Active
**Last Updated**: 5 October 2026

## Active Features

| ID | Name | Description | Status | Priority | Owner | Source | Updated |
|----|------|-------------|--------|----------|-------|--------|---------|
| FEAT-001 | Catalog and Revisions | The catalog is where UMF documents become types, properties, keys and relationships that the rest of truss reads | Draft | P0 | Project owner | PRD: Catalog and revisions (FR-1–FR-8) | 2026-10-05 |
| FEAT-002 | Storage, Identity and Exactness | This feature is the fixed table set: how objects, edges and keys are stored so that every value is exact, nothing is dropped, and the database itself enforces keys and endpoints | Draft | P0 | Project owner | PRD: Storage, identity and exactness (FR-9–FR-15) | 2026-10-05 |
| FEAT-003 | Mutation and Concurrency | Every write, from any implementation, follows one protocol so that validation, locking, versioning and the journal agree and a catalog change that races with a write is detected | Draft | P0 | Project owner | PRD: Mutation and concurrency (FR-16–FR-21) | 2026-10-05 |
| FEAT-004 | Journal and History | The journal is the append-only record of every change, written in the transaction that made it | Draft | P0 | Project owner | PRD: Journal and history (FR-22–FR-27) | 2026-10-05 |
| FEAT-005 | Reads and Traversal | This feature is how stored data is read: one object by identifier or key, a type's objects in pages, an object's edges, a short traversal, and the catalog's own types | Draft | P0 | Project owner | PRD: Reads and traversal (FR-28–FR-32) | 2026-10-05 |
| FEAT-006 | Enforcement Reporting | This feature makes enforcement a visible, verified fact: for every UMF assertion, who enforces it, with the evidence, and no overclaiming | Draft | P0 | Project owner | PRD: Enforcement reporting (FR-33–FR-35) | 2026-10-05 |
| FEAT-007 | Conformance and Portability | This feature makes truss a specification as well as a program: contracts and a corpus that let another implementation share the same tables and prove it | Draft | P0 | Project owner | PRD: Conformance and portability (FR-36–FR-40) | 2026-10-05 |
| FEAT-008 | Host Integration | This feature is how an application that owns a database adds its own structure and policy around truss's tables without changing them | Draft | P1 | Project owner | PRD: Host integration (FR-41–FR-44) | 2026-10-05 |

## Dependencies

| From | To | Type | Notes |
|------|----|------|-------|
| FEAT-002 | FEAT-001 | Required | Objects are typed by the catalog |
| FEAT-003 | FEAT-001 | Required | Writes are checked against the catalog and its head revision |
| FEAT-003 | FEAT-002 | Required | Writes fill the table set |
| FEAT-004 | FEAT-003 | Required | The journal is written by the write protocol |
| FEAT-005 | FEAT-002 | Required | Reads use the table set |
| FEAT-006 | FEAT-001 | Required | The report is part of acceptance |
| FEAT-007 | FEAT-001, FEAT-002, FEAT-003, FEAT-004 | Required | The corpus tests their behavior |
| FEAT-008 | FEAT-004 | Required | Journal modes and the recorded role |
