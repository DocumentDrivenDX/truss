---
ddx:
  id: SD-002
  type: solution-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-002
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
---

# SD-002: Storage identity and exactness

**Feature:** FEAT-002. **Status:** draft. **Parent:** Truss architecture.

## Scope

Use the accepted fixed object/key/edge layout and a typed lossless codec. The catalog selects meaning; JSON types never establish a logical type by themselves.

## Requirements Mapping

The table also owns feature-level traceability; exact per-criterion tests belong in story test plans.

| Requirement | Design capability | Verification strategy |
| --- | --- | --- |
| STO-01 | Fixed object/key/edge statement templates and property-id map | Create multiple types without schema changes; record decoding uses catalog revision |
| STO-02 | Lossless text transport and recursive scalar/container codec | Independent large integer/decimal/offset/binary/presence corpus on both adapters |
| STO-03 | Separate retained map and explicit rebind plan | Unknown numeric/structured content retained; later binding reported and journaled |
| STO-04 | Canonical comparator policy and key maintenance in transaction | Equal decimal keys conflict; offset/text distinctions retain declared meaning |
| STO-05 | Endpoint FKs, unique edge pair and owned/unowned deletion plan | Direct SQL cannot create invalid endpoints or duplicate pairs; external edges protect objects |
| STO-06 | Catalog-driven limit-marker integrity guard plus larger-max parent-lock validation | Bypass insert cannot omit required marker; concurrent maximum-one/three cases |
| STO-07 | Shared database sequence with no caller-selected ids | Concurrent creates and rollback gaps preserve identity allocation |
| STO-08 | Primary-key/pair lookup and persistent deletion reservations | Repeat after correction/deletion creates nothing; partial import resumes |
| STO-09 | Insert-once source metadata in creation transaction | Repeated import does not rewrite source facts; failed creation has no source row |

## Solution Approaches

Generic object maps plus canonical key rows are selected by ADR-002 evidence. Per-type tables and indexes are rejected as default storage because they reintroduce revision DDL and type-count planning cost.

## Domain Model

Objects have typed identities, property maps and retained content. Keys reference objects; edges reference typed endpoints; provenance and reservations survive deletion.

## System Decomposition

Core owns encoding/canonicalization. PostgreSQL storage executor owns canonical rows and derived-row synchronization. Native integrity guards and role grants supply only their proven database guarantees; full property/key consistency remains separately classified.

For portable authored keys, core consumes UMF's public `umf-key-tuple-v1` profile rather than duplicating its encoder; Truss owns selected native transport and explicit stable-key/local-number mapping. CONTRACT-001 now separates legacy full-value index capacity from the proposed full-byte/digest-bucket large-key profile. Both keep generic fixed storage; neither introduces per-type DDL. The codec ceiling is not a native index guarantee. Complete bytes, collision-safe exact comparison and current guard admission govern the large-key candidate; independent native qualification and migration still block activation.

Exact shared surfaces belong to the referenced contracts. Story technical designs inherit these component boundaries and add files, per-criterion wiring and rollback steps without duplicating interface definitions.

## Quality Attributes and Concern Alignment

ADR-001 governs separate TypeScript core/adapters, Bun development and provisional Node support. ADR-002 governs fixed storage and measured/provisional choices. Values and documents remain exact within the explicitly qualified profile; unknown content is retained. Database claims require native evidence at the actual bypass/role boundary. Performance targets remain proposed and measured independently from correctness. Package changes keep PostgreSQL-specific I/O outside the pure core.

## Traceability and Gaps

Every functional feature requirement is assigned above. Governing story criteria remain in their US artifacts. These gaps are design/qualification dependencies, not permission to omit requirements:

D-05 must pin the exact scalar, null, list/map and structured-value encoding. JSONB does not preserve arbitrary numeric spelling, so the lexical promise needs a receipt/encoding decision rather than a broad source-token claim. Maximum-one is not database enforcement unless marker insertion is unavoidable for the qualified bypass role. Key-row uniqueness and property-derived key correctness are separate assertions. Parallel keyed association instances/undirected native semantics cannot silently collapse into the unique-pair layout; explicit qualified support/refusal is required.

## Constraints, Risks and Rollback

A new layout/encoding/profile is explicit and versioned. An unsupported combination refuses before mutations or SQL emission. Keep the previous model/layout/profile artifacts for rollback; do not rewrite an installed database implicitly. New implementation code can be disabled/unregistered independently of stored data; a deployed breaking schema change needs its own reviewed migration. Before building, reconcile these references against current UMF/Weft interfaces and resolve the affected gates in the design coordination record.

### Row-home and exact-value implementation boundary

The accepted generic layout remains the baseline; proposed state/node/scalar row homes are additive, unadopted storage profiles. CONTRACT-001 owns complete candidate admission and atomic canonical/derived finalization. CONTRACT-010 owns original codec registration, complete state/node/payload correlation, original record-field identity and authored order. The existence of captured SQL fragments is neither a complete installer nor native enforcement evidence. Select the exact replacement/additive layout and migration policy before activation.

Validate the complete original definition inventory and source values before allocation or canonical effects. Optional absence, present null, empty containers and missing payloads remain distinct. Readback observes both complete node and scalar streams, including orphan or unreachable content; a root-only traversal cannot establish integrity. Correlate record fields using full original qualified identity bytes, not display names, native node ordering or a hash alone. Unknown retained content requires its admitted preservation profile rather than silent omission.

Storage/readback, equality, ordering, key participation, predicates and aggregates have separate capability evidence. Native numeric projection does not prove lexical/source-facet equality. Registered codecs and field encoding must retain their original versions and exact bytes across writer, reader and Weft binding. Complete producer/finalizer bodies, privilege closure, bounded native transport and independent source/native parity remain implementation and qualification outputs; no further UMF capability is assumed.
