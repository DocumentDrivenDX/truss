---
ddx:
  id: SD-006
  type: solution-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-006
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-005
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-011
      kind: informed_by
---

# SD-006: Enforcement reporting

**Feature:** FEAT-006. **Status:** draft. **Parent:** Truss architecture.

## Scope

Build an assertion inventory from retained UMF documents and attach evidence-qualified enforcement dispositions for the selected deployment/profile.

## Requirements Mapping

The table also owns feature-level traceability; exact per-criterion tests belong in story test plans.

| Requirement | Design capability | Verification strategy |
| --- | --- | --- |
| ENF-01 | Enumerate assertions, including opaque/unknown selected content | No source assertion omitted; unresolved meaning remains none/unknown |
| ENF-02 | Certify against raw SQL using each qualified bypass role | Omitted key/edge-limit maintenance cannot be labeled database guarantee |
| ENF-03 | Evidence manifest pins engine/model/layout/profile/source hashes | Stale or mismatched evidence cannot qualify a support claim |

## Solution Approaches

Per-assertion evidence is selected over a schema-wide supported flag. Primitive database constraints alone cannot certify end-to-end logical invariants.

## Domain Model

An assertion has source identity/path, meaning/version, enforcement owner and proof scope. A deployment profile pins roles, trigger set, encoding and adapter assumptions.

## System Decomposition

Core assertion extractor retains known/unknown paths. Catalog acceptance attaches dispositions. Native conformance runner supplies evidence; capability exporter presents qualified statuses to Weft without interpreting query language.

Enforcement reporting composes three independent inventories: original source assertions and uninterpreted selected content; installed native/engine responsibilities under CONTRACT-005; and exact required qualification cases/receipts under CONTRACT-011. Match full membership before deriving dispositions, retaining source rule names/paths and original codec/meaning scope from CONTRACT-010. A successful metadata selector, generated DDL or matching assertion count supplies no enforcement proof. Unknown selected meaning keeps its original source and explicit unavailable interpretation rather than inheriting a same-named known rule's evidence.

Support assessment uses immutable original execution receipts separately from current installed-policy observation. Bind both to exact original model/layout/codec/implementation/profile versions and actual deployment/role inventory; stale or unobservable guards/grants cannot silently retain a current database guarantee. Database versus engine versus none remains the existing enforcement vocabulary, distinct from qualified/failed/unverified/stale evidence assessment. Current observation is point-in-time and does not confer observer privileges on ordinary writers or authorize later mutations. Actual full native extraction/privilege/coherence and independent bypass cases remain selected implementation gates.

Exact shared surfaces belong to the referenced contracts. Story technical designs inherit these component boundaries and add files, per-criterion wiring and rollback steps without duplicating interface definitions.

## Quality Attributes and Concern Alignment

ADR-001 governs separate TypeScript core/adapters, Bun development and provisional Node support. ADR-002 governs fixed storage and measured/provisional choices. Values and documents remain exact within the explicitly qualified profile; unknown content is retained. Database claims require native evidence at the actual bypass/role boundary. Performance targets remain proposed and measured independently from correctness. Package changes keep PostgreSQL-specific I/O outside the pure core.

## Traceability and Gaps

Every functional feature requirement is assigned above. Governing story criteria remain in their US artifacts. These gaps are design/qualification dependencies, not permission to omit requirements:

No logical required/null/comparator meaning is inferred solely from a PostgreSQL column type or JSONB shape. Native relationship owned lifecycle does not by itself prescribe a cascade; Truss lifecycle policy must be separately declared. A read profile also needs stored-domain checks and must refuse selected semantics with no established representation.

## Constraints, Risks and Rollback

A new layout/encoding/profile is explicit and versioned. An unsupported combination refuses before mutations or SQL emission. Keep the previous model/layout/profile artifacts for rollback; do not rewrite an installed database implicitly. New implementation code can be disabled/unregistered independently of stored data; a deployed breaking schema change needs its own reviewed migration. Before building, reconcile these references against current UMF/Weft interfaces and resolve the affected gates in the design coordination record.
