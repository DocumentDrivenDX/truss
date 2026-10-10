---
ddx:
  id: SD-001
  type: solution-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-001
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# SD-001: Catalog and revisions

**Feature:** FEAT-001. **Status:** draft. **Parent:** Truss architecture.

## Scope

Accept one revision through a staged, exact document pipeline and a catalog-head exclusion transaction. UMF validity is authoritative; Truss-derived storage validity is checked separately.

## Requirements Mapping

The table also owns feature-level traceability; exact per-criterion tests belong in story test plans.

| Requirement | Design capability | Verification strategy |
| --- | --- | --- |
| CAT-01 | Parse/validate before persistence; all derivation/checks/head update in one transaction | Invalid second document leaves zero new rows and unchanged head |
| CAT-02 | Dependency graph with deterministic strongly connected component ordering | Permutation of input documents yields equal ordinals; cycles retain all documents |
| CAT-03 | Separate UMF bundle-validity gate from Truss unknown-endpoint policy | Each policy reports exact unresolved endpoint; invalid UMF never bypassed |
| CAT-04 | Identity index and allocation under head lock; retirement never reuses identifiers | Rename preserves ids; replacement/retirement does not; ownership collisions refuse |
| CAT-05 | Precommit violator scan over the locked data domain | Several violators all appear; none of the candidate persists |
| CAT-06 | Trusted host-supplied deterministic transform plan, validated for every affected value | Transform fault or non-total case undoes catalog and instance changes |
| CAT-07 | Persist catalog rows only; index jobs staged after acceptance | Native DDL-event/catalog comparison shows no per-type object creation |
| CAT-08 | Assertion inventory plus derive/rebind/retire report | Every source assertion is represented, including unknown/residual semantics |
| CAT-09 | Origin assembled from asserted actor and actual PostgreSQL role | Spoofed role is ignored in definer and assumed-role contexts |

## Solution Approaches

Catalog-head row locking with deterministic whole-set derivation preserves fixed-table acceptance. Per-document incremental commits are rejected because partial references and partial revisions would become visible.

## Domain Model

Schema revisions own immutable source documents and acceptance report correspondence; derived type/property/key/relationship rows retain logical identity and definition history. CONTRACT-003 retains alternative report persistence designs. A separate immutable report home is recommended but unadopted; this domain relationship does not choose its physical store.

## System Decomposition

Core resolves/validates supplied documents. PostgreSQL catalog executor performs exclusion, scans and atomic persistence. Tooling performs separately declared index construction and records readiness without mutating an immutable accepted report.

Exact shared surfaces belong to the referenced contracts. Story technical designs inherit these component boundaries and add files, per-criterion wiring and rollback steps without duplicating interface definitions.

## Quality Attributes and Concern Alignment

ADR-001 governs separate TypeScript core/adapters, Bun development and provisional Node support. ADR-002 governs fixed storage and measured/provisional choices. Values and documents remain exact within the explicitly qualified profile; unknown content is retained. Database claims require native evidence at the actual bypass/role boundary. Performance targets remain proposed and measured independently from correctness. Package changes keep PostgreSQL-specific I/O outside the pure core.

## Traceability and Gaps

Every functional feature requirement is assigned above. Governing story criteria remain in their US artifacts. These gaps are design/qualification dependencies, not permission to omit requirements:

Document-qualified identity versus catalog namespace uniqueness and cross-document validity need D-04 resolution. Record-valued Fields are value containment in UMF, not implicitly authored graph relationships; any object/composition storage realization requires a Truss binding and explicit reconstruction meaning. Transform callbacks are registered trusted host code, never model-loaded code.

## Constraints, Risks and Rollback

A new layout/encoding/profile is explicit and versioned. An unsupported combination refuses before mutations or SQL emission. Keep the previous model/layout/profile artifacts for rollback; do not rewrite an installed database implicitly. New implementation code can be disabled/unregistered independently of stored data; a deployed breaking schema change needs its own reviewed migration. Before building, reconcile these references against current UMF/Weft interfaces and resolve the affected gates in the design coordination record.

### Catalog lifecycle and persistence closure

Consume the available selected UMF validator and original document/definition identities; preserve its exact validity, completeness and diagnostic facts separately from Truss-selected storage support. Document-qualified lineage and synthesized composition proposals are authored under CONTRACT-001/003, but owner adoption and retired-identity reactivation remain open. Same names or equal payloads cannot silently merge original document owners. A recursive value-definition graph is distinct from a graph relationship and from a concrete cyclic stored value.

CONTRACT-003 owns complete candidate-before-persistence transforms, original source/assertion inventories, immutable report correspondence and native pending-effect verification. Select report persistence before implementing the acceptance writer: the baseline parent report, separate immutable home and changed public/event producer alternatives have different ordering and migration obligations. Never insert a placeholder report, mutate an accepted report to append later effects, or replay a transform to recover unknown completion. Revision-zero installation evidence is separate from positive acceptance reports. Existing report bytes cannot be promoted to a complete new representation without original evidence and an admitted conversion policy.

Remaining acceptance outputs are the exact registered native candidate/encoder grammar, generated metadata producers, complete effect/privilege/resource inventory and postcommit index readiness procedure. Native pending parity and head publication do not prove outer commit. These outputs use existing UMF capabilities and the original executor custody; they do not authorize model-loaded callbacks or a second operation registry.
