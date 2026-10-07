---
ddx:
  id: SD-003
  type: solution-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-003
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-005
      kind: informed_by
    - id: CONTRACT-006
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
---

# SD-003: Mutation and concurrency

**Feature:** FEAT-003. **Status:** draft. **Parent:** Truss architecture.

## Scope

Plan and validate mutations in the pure core, execute through one catalog/lock protocol, and use an operation savepoint when embedded in a caller transaction.

## Requirements Mapping

The table also owns feature-level traceability; exact per-criterion tests belong in story test plans.

| Requirement | Design capability | Verification strategy |
| --- | --- | --- |
| MUT-01 | Head pin, lock plan, validation, canonical writes and single journal owner | Fault at each persistence boundary leaves no partial operation |
| MUT-02 | Version-guarded writes and exact no-op comparison | Stale expected version fails; true no-op leaves version/journal unchanged |
| MUT-03 | Locked head comparison with isolation-aware retry | Barrier-controlled acceptance race under both specified isolation levels |
| MUT-04 | Explicit acceptance timeout and optional queue profile | Timeout rolls back; queue fairness measured without mandatory overhead |
| MUT-05 | Normalize by SQLSTATE/relation and preserve violation paths | Every declared error kind has deterministic retry scope |
| MUT-06 | Final invariant validation under root/parent locks or serializable profile | Concurrent participants cannot exceed max or violate minimum through engine |
| MUT-07 | Whole-group discovery/simulation and canonical hierarchy in CONTRACT-009 | Aliases, opposed-order groups, final participation and indexed failure |
| MUT-08 | Versioned request identity, validated input hash and durable ordered replay result | Concurrent duplicate, conflict, mixed/no-op replay and retention tests |
| MUT-09 | Adopted scope plus per-call savepoint in CONTRACT-007 | Host/Truss rollback together; no internal COMMIT; prior host work survives call error |

## Solution Approaches

A shared planned protocol is selected over per-method ad hoc SQL and automatic retries. It keeps independent implementations consistent and lets the host retain transaction authority.

## Domain Model

An operation plan names catalog revision, typed references, required locks and ordered effects. A group preserves aliases and ordered operation results while committing one atomic outcome.

## System Decomposition

Core operation planner computes proposed state and violation inventory. PostgreSQL protocol executor discovers/revalidates lock closure and applies effects. Runtime adapters own connection affinity, savepoints and transaction completion. Replay persistence is a separate gate from ordinary groups.

Every canonical row-home mutation participates in CONTRACT-001's original operation custody, dirty-generation touch and RH/RF finalization, with CONTRACT-005's complete producer/guard privilege inventory. Exact candidate/source/field/codec admission belongs to CONTRACT-010; engine validation alone cannot claim native unavoidable enforcement. When the selected history/feed profile requires it, the same original operation schedules CONTRACT-006 registration and complete write-free finalization; a producer omitting all feed rows must not escape checks because no feed-row trigger fires. All native bodies/account/role/profile selection remains explicit before qualification.

Exact shared surfaces belong to the referenced contracts. Story technical designs inherit these component boundaries and add files, per-criterion wiring and rollback steps without duplicating interface definitions.

## Quality Attributes and Concern Alignment

ADR-001 governs separate TypeScript core/adapters, Bun development and provisional Node support. ADR-002 governs fixed storage and measured/provisional choices. Values and documents remain exact within the explicitly qualified profile; unknown content is retained. Database claims require native evidence at the actual bypass/role boundary. Performance targets remain proposed and measured independently from correctness. Package changes keep PostgreSQL-specific I/O outside the pure core.

## Traceability and Gaps

Every functional feature requirement is assigned above. Governing story criteria remain in their US artifacts. These gaps are design/qualification dependencies, not permission to omit requirements:

D-06 still needs a request receipt decision; SPIKE-003 request lookup is not proof of complete result replay. Host code with earlier inconsistent lock acquisition can trigger retry and is outside the opposed-order fresh-transaction guarantee. Every writer implementation must adopt the same hierarchy before participating in shared deployment.

## Constraints, Risks and Rollback

A new layout/encoding/profile is explicit and versioned. An unsupported combination refuses before mutations or SQL emission. Keep the previous model/layout/profile artifacts for rollback; do not rewrite an installed database implicitly. New implementation code can be disabled/unregistered independently of stored data; a deployed breaking schema change needs its own reviewed migration. Before building, reconcile these references against current UMF/Weft interfaces and resolve the affected gates in the design coordination record.
