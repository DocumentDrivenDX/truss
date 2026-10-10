---
ddx:
  id: SD-005
  type: solution-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-005
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
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
---

# SD-005: Reads and traversal

**Feature:** FEAT-005. **Status:** draft. **Parent:** Truss architecture.

## Scope

Provide exact low-level storage reads and a versioned mapping/read context for Weft. Weft supplies SQL language, logical planning and registered backend lowering.

## Requirements Mapping

### Compiled-artifact admission and execution

Before execution, validate the exact Weft interface/backend/frontend version, model/source pins, Truss layout/encoding/mapping profile and declared output/parameter descriptors. Reconcile them against the live qualified read context; compilation at an earlier compatible context is not authority to ignore a changed catalog. A mismatch or unsupported declared obligation refuses before issuing artifact SQL. Artifact data cannot choose credentials, role escalation, connection replacement or an administrative statement path.

Discharge each declared read obligation through the actual adapter/transaction profile: fixed snapshot or catalog stability, current acting role, exact parameter carriers and output decoding. Establish context checks and query observation in a qualified shared snapshot/barrier rather than check pins on one connection then execute on another. Preserve connection affinity under poolers. Result decoding validates the declared shape/carriers and never silently rounds numeric values or confuses absent/null. A backend-produced SQL string alone is insufficient evidence of any obligation.

Treat compiled artifacts as trusted compiler output only after host-authorized provenance validation; arbitrary caller-provided SQL is not this integration surface. Truss does not parse/recompile SQL to manufacture compatibility. It validates the artifact contract and executes through qualified transport; Weft retains language/planning/lowering ownership. Unknown required obligation/decoder meaning blocks, while optional nonsemantic metadata follows negotiated compatibility. Exact admission API, profile matching and provenance policy require joint owner review before publication.

Native probes must alter catalog/role/encoding pins between compilation and execution, submit unknown obligations and malformed result carriers, and vary pooler connection context. Require refusal or qualified preserved semantics, never an accidental execution pass. Compiler fixture success remains separate from native Truss execution evidence.

The table also owns feature-level traceability; exact per-criterion tests belong in story test plans.

| Requirement | Design capability | Verification strategy |
| --- | --- | --- |
| RD-01 | Parameterized id/key read plus exact decoder | Key/id identify same record with exact values, revision and version |
| RD-02 | Type/id index and limit-plus-lookahead storage paging | No omission/duplicate at unchanged state; limit guard and exact more marker |
| RD-03 | Qualified order-key/id tuple paging with native collation | Null order keys, equal keys and bounded edges have stable continuation |
| RD-04 | Weft backend mapping and native traversal execution corpus | One-to-three hops match independent identity/multiplicity and performance oracle |
| RD-05 | Catalog enumeration inside one consistent revision context | Concurrent acceptance cannot mix definitions in one enumeration |

## Solution Approaches

Direct id/key/list statements remain useful without Weft. General logical SQL is delegated to Weft; a second Truss parser/optimizer is rejected to avoid divergent query meaning.

## Domain Model

Rows retain storage reference, version and last-write revision. A read context separately pins the accepted catalog and snapshot. Cursors carry order/profile context without inventing snapshot stability.

## System Decomposition

PostgreSQL read executor owns direct storage APIs and snapshot checks. Mapping exporter provides catalog/storage facts. Weft backend owns target plan/SQL/decoder declarations under its registered backend contract; runtime adapters enforce obligations and decode actual rows.

Exact shared surfaces belong to the referenced contracts. Story technical designs inherit these component boundaries and add files, per-criterion wiring and rollback steps without duplicating interface definitions.

## Quality Attributes and Concern Alignment

ADR-001 governs separate TypeScript core/adapters, Bun development and provisional Node support. ADR-002 governs fixed storage and measured/provisional choices. Values and documents remain exact within the explicitly qualified profile; unknown content is retained. Database claims require native evidence at the actual bypass/role boundary. Performance targets remain proposed and measured independently from correctness. Package changes keep PostgreSQL-specific I/O outside the pure core.

## Traceability and Gaps

Every functional feature requirement is assigned above. Governing story criteria remain in their US artifacts. These gaps are design/qualification dependencies, not permission to omit requirements:

D-08 must finalize storage profile/mapping, stale-cache guards and Weft 0.1 versus application-read 0.2 capabilities. Storage-id paging is distinct from authored-key entity paging; neither cursor can substitute for the other. Weft compiler evidence does not establish Truss execution support. No per-query auto-index creation.

## Constraints, Risks and Rollback

A new layout/encoding/profile is explicit and versioned. An unsupported combination refuses before mutations or SQL emission. Keep the previous model/layout/profile artifacts for rollback; do not rewrite an installed database implicitly. New implementation code can be disabled/unregistered independently of stored data; a deployed breaking schema change needs its own reviewed migration. Before building, reconcile these references against current UMF/Weft interfaces and resolve the affected gates in the design coordination record.

Compiled execution admission now explicitly consumes Weft-owned identifier/ordered typed-slot profiles under CONTRACT-007. Truss validates original registered artifact/target/adapter obligations and executes actual prepared bindings; it does not re-emit frontend SQL or normalize slots. Identifier settings, per-query slots and exact transport are separate from direct-read/group resource limits. Committed Weft source now includes Truss-coupled physical checks and original property/home admission. This source evidence supersedes the earlier primitive-only observation; it does not establish accepted Truss runtime integration. Complete mapping/value/authority/snapshot/corpus qualification remains B012/B014 work.

### Whole-value reconstruction and complete-result publication

CONTRACT-007 owns the private original scan-occurrence bridge; CONTRACT-010 owns full state/tree/scalar membership, original field identity, authored order, presence and codec admission. Name-addressed compiled JSON projection is a separate capability: it cannot establish original source-token retention or authored record order. Exact whole-value outputs require the admitted original owner/property/state/root observations for every result occurrence under the same cut, authority and cumulative resource account. Repeated rows preserve bag multiplicity; equal displayed keys or numeric IDs do not merge occurrence provenance. Computed outputs without an admitted original observation derivation refuse this capability.

Stage the complete result and all required observations before publication. A later malformed tree, missing original definition or failed containment withholds the entire result; no retry under a new context or partial publication repairs it. The selected-state batch source and larger lookup resource candidate remain unadopted alternatives with separate transport, partition-completeness and resource qualification. Exact compiler occurrence handoff, native producers and bridge adoption remain concrete integration outputs, rather than another SQL compiler or additional UMF feature work.


### Original artifact custody across asynchronous execution

Admission, obligation discharge, native submission and decoding must use one bounded retained original artifact byte inventory and original bridge selection. Capture the admitted request data before asynchronous host/compiler/provenance callbacks can change caller-owned containers. Verify exact artifact integrity and complete registered bytes under the existing resource profile; reserve capture/decoding copies before allocation. Never validate one artifact then reread SQL, parameter/output descriptors or obligations from a subsequently changed caller object. Capture does not establish provenance, current authority or actual native context: those remain independently admitted at their required boundaries.

An asynchronous provenance provider's answer must correspond to those exact original bytes/backend/source pins. A valid answer for another artifact, matching SQL text or a cached digest alone cannot authorize execution. Retain the same original artifact identity through private scan bridges, native result decoding and the public executed/refused observation. Context changes require the existing refusal/revalidation protocol, not recompilation, descriptor substitution or automatic retry. This is Truss consumer custody; it introduces no Weft compiler API, decoder ABI or new UMF capability.


### Refusal stage versus native execution settlement

The compiled facade's domain refused result is not evidence that no SQL was submitted. Admission failure before submission must retain verified zero-submission evidence; result/authority/resource refusal after a command must retain that command's original termination and containment observation. Keep full private native/decoder evidence under current disclosure policy, with no partial result publication or artifact rewriting. The domain reason alone cannot distinguish these stages or release a quarantined resource.

If native termination, containment or executor state is unresolved, use CONTRACT-007's existing outer Outcome execution-failure/recovery protocol rather than packaging unresolved execution as a clean domain refusal. Select the exact already-registered execution failure according to actual native evidence; do not invent a new error code, claim commit_unknown solely because a read result failed validation, or automatically retry. A confirmed read command followed by malformed result carriers can refuse result publication without asserting rollback or ending a supplied host transaction. Transaction-fatal errors still follow executor containment rules. An executed domain result requires full original row/descriptor/obligation admission and confirmed native completion, not a decoded prefix.


### Registered backend changes during admitted execution

The original bridge selection binds the exact registered frontend/backend/decoder/obligation meanings and their evidence, not merely a mutable host registry key. Capture those original references and verify their availability/qualification at the required admission boundaries. Host replacement of a registration affects subsequent admissions under its new selection; it cannot substitute decoder, obligation verifier or provenance meaning for an already admitted artifact. A replacement claiming the same identifier/version with different original bytes/evidence is a compatibility conflict, not a transparent upgrade.

If an original required implementation or qualification becomes unavailable while execution is pending, follow the existing contained refusal or unresolved executor recovery according to actual submission/termination state. Never fall back to another registered backend or reinterpret original rows with a newer decoder. Changes to current authority/catalog/readiness still follow their independently required revalidation; retaining the original decoder does not preserve obsolete permission. This describes consumer selection behavior without adding a registry/hot-reload API or promising that host implementations support replacement. The host owns compiler lifetime; Truss retains only the original registered evidence and services necessary for its admitted operation/recovery subset.
