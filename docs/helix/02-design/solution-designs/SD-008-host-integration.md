---
ddx:
  id: SD-008
  type: solution-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-008
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: CONTRACT-005
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
    - id: CONTRACT-011
      kind: informed_by
---

# SD-008: Host integration

**Feature:** FEAT-008. **Status:** draft. **Parent:** Truss architecture.

## Scope

Let hosts add their own schema/policy around an invariant fixed layout and use caller-owned transactions through runtime adapters.

## Requirements Mapping

The table also owns feature-level traceability; exact per-criterion tests belong in story test plans.

| Requirement | Design capability | Verification strategy |
| --- | --- | --- |
| HST-01 | Extension inventory and compatibility checks | Host tables/functions allowed; altered Truss constraints/layout refused |
| HST-02 | Transaction-local role assumed by host and database-derived origin | Definer/role/default-session cases record actual role without trusting actor |
| HST-03 | Connection-affine scopes, local context cleanup and unprepared equivalence | Pool borrower/context reuse has no leaked origin/role; prepared/unprepared same results |
| HST-04 | Same layout on qualified embedded/server engines | Identical catalog/behavior corpus; adapter qualification remains distinct |
| HST-05 | Optional module policy layer over catalog and all dependent tables | Direct SELECT/write matrix including keys, history and provenance |
| HST-06 | Edge policy tests relationship and both endpoint modules | One/two/three-module roles and inverse reads cannot elevate visibility |

## Solution Approaches

Explicit extension and execution contracts are selected over modifying Truss columns per consumer. Optional module isolation is database policy, while authentication and application authorization remain host responsibilities.

## Domain Model

Host schema objects coexist with Truss objects. Module grants map actual roles to visibility. Cross-module edges require the relationship module and both endpoint modules.

## System Decomposition

CONTRACT-007 now governs reference assembly lifetime: construction is inert configuration, capability verification is explicit and independent, and disposal releases only owned resources. Administrative installation and background feed/index workers require explicit host invocation. The reference application supplies connection, authentication and shutdown policies through the same public package surfaces available to another consumer; it has no privileged internal mutation path. Package-consumer qualification must omit Weft registration and still exercise direct read/write/import/history capabilities, then separately register Weft for compiled execution.

Transaction adoption retains original executor issuer/generation, native affine connection/transaction, operation arbitration, host-control inventory and shared resource account from CONTRACT-007. A caller-supplied xid/status flag or copied context object cannot establish that custody. Truss uses its operation savepoint within the host transaction; it cannot commit/roll back the whole caller transaction, retry callbacks or report a pending group result as committed before actual original commit acknowledgment. CONTRACT-009 owns complete ordered group/replay outcomes; host sentinel writes and nested failures must remain independently observable.

Disposal closes future admissions but preserves original in-flight containment, pending results and recovery evidence until actual owned resource termination/transfer. It cannot erase an unknown commit, close a caller-owned pool/transaction or restart work under replacement configuration. Recovery observes the original attempt through the separately injected original registry/service, with current authorization; matching names/profile pins cannot mint a successor's custody. Readiness, compatibility and support assessment follow CONTRACT-011's complete profile/receipt and current-policy procedures rather than constructor success or declared facade availability. Missing producers keep the affected capability unverified, while optional Weft registration remains independent from direct toolkit operation.

Runtime adapters adopt transactions without credentials in core. Host tooling installs policies/functions under a reviewed role plan. Module-isolation profile declares every protected relation and lookup privilege; backend execution relies on actual effective role checks.

Exact shared surfaces belong to the referenced contracts. Story technical designs inherit these component boundaries and add files, per-criterion wiring and rollback steps without duplicating interface definitions.

## Quality Attributes and Concern Alignment

ADR-001 governs separate TypeScript core/adapters, Bun development and provisional Node support. ADR-002 governs fixed storage and measured/provisional choices. Values and documents remain exact within the explicitly qualified profile; unknown content is retained. Database claims require native evidence at the actual bypass/role boundary. Performance targets remain proposed and measured independently from correctness. Package changes keep PostgreSQL-specific I/O outside the pure core.

## Traceability and Gaps

Every functional feature requirement is assigned above. Governing story criteria remain in their US artifacts. These gaps are design/qualification dependencies, not permission to omit requirements:

Complete module-isolation cost and indirect lookup exposure remain qualification work. Unique/FK conflict existence leakage is explicit. Catalog acceptance requires a qualified administrative role while catalog reads obey caller policy. Host-owned triggers must declare journal ownership and lock hierarchy; they cannot silently replace canonical behavior.

## Constraints, Risks and Rollback

A new layout/encoding/profile is explicit and versioned. An unsupported combination refuses before mutations or SQL emission. Keep the previous model/layout/profile artifacts for rollback; do not rewrite an installed database implicitly. New implementation code can be disabled/unregistered independently of stored data; a deployed breaking schema change needs its own reviewed migration. Before building, reconcile these references against current UMF/Weft interfaces and resolve the affected gates in the design coordination record.
