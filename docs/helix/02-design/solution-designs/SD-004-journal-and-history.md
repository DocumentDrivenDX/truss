---
ddx:
  id: SD-004
  type: solution-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-004
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-006
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-011
      kind: informed_by
---

# SD-004: Journal and history

**Feature:** FEAT-004. **Status:** draft. **Parent:** Truss architecture.

## Scope

Keep canonical instance rows and append transactional history. Separate internal journal order, at-least-once transport and downstream durable application.

## Requirements Mapping

The table also owns feature-level traceability; exact per-criterion tests belong in story test plans.

| Requirement | Design capability | Verification strategy |
| --- | --- | --- |
| JNL-01 | Single journaling owner and same-transaction append | Missing partition/forced append failure undoes instance change |
| JNL-02 | Generic journal triggers with bypass-tested grants and origin handling | Plain SQL insert/update/delete produce one complete history effect |
| JNL-03 | Presence-aware history envelopes and actual-role origin | Set-null/unset, retained update, edge endpoints/order and delete reconstruction |
| JNL-04 | Safe transaction watermark and ordered bounded reader | Late commit is withheld then delivered exactly at its stable position |
| JNL-05 | Replay versioned envelopes using definition history | Each historical object/edge version reconstructs independently |
| JNL-06 | Ahead-of-time range partitions and append-only roles | Recognized writer cannot update/delete/truncate history; missing range fails writes |
| JNL-07 | Revision-before-change packaging, side-record identity and resumable snapshot/feed protocol | Crash/replay and initial snapshot yield complete downstream state |
| JNL-08 | Durable consumer position and separate publishable/withheld lag observations | Slow transaction, idle reader and unavailable source remain distinguishable |

## Solution Approaches

Canonical rows plus history are selected by ADR-002. Journal-canonical execution and a transport-specific publisher are deferred because they would add storage/hosting authority not required by this feature.

## Domain Model

Changes are grouped by record/version and database transaction. Revisions retain interpretation sources. Feed consumers hold durable positions; partition retention is constrained by all registered consumers and the separately advertised history/replay horizons and their original dependency closure.

## System Decomposition

Journal writer/trigger profile provides atomic history. History reader interprets old definitions. Feed reader assembles complete transaction records and positions; host publisher supplies transport. The separately injected downstream application adapter and proof verifier produce/admit original committed application evidence, and source acknowledgment consumes that evidence under CONTRACT-006. Transport delivery or publisher success alone cannot authorize durable progress. Administrative retention checks every consumer plus preserved reconstruction/replay dependencies before removing partitions. Time partitions do not define mutation boundaries; a group spanning partitions remains protected unless an explicitly qualified replacement checkpoint preserves the declared horizon.

Exact shared surfaces belong to the referenced contracts. Story technical designs inherit these component boundaries and add files, per-criterion wiring and rollback steps without duplicating interface definitions.

## Quality Attributes and Concern Alignment

ADR-001 governs separate TypeScript core/adapters, Bun development and provisional Node support. ADR-002 governs fixed storage and measured/provisional choices. Values and documents remain exact within the explicitly qualified profile; unknown content is retained. Database claims require native evidence at the actual bypass/role boundary. Performance targets remain proposed and measured independently from correctness. Package changes keep PostgreSQL-specific I/O outside the pure core.

## Traceability and Gaps

Every functional feature requirement is assigned above. Governing story criteria remain in their US artifacts. These gaps are design/qualification dependencies, not permission to omit requirements:

D-07 now has authored complete history/feed/side-record envelopes, seed extraction/staging/activation/confirmation boundaries, transaction-complete delivery/application/acknowledgment wires and unknown-record refusal procedures. Remaining gates are ADR-007 adoption, exact original archive/clock/codec/authority/account/native fact/closure producers, complete write-free finalizer/retention composition and independently qualified source/downstream/host behavior. Source/wire checks do not establish those native meanings. Bare journal tuples cannot position every side record/revision safely without an explicit protocol. Administrative superusers are outside ordinary role tamper guarantees; retention can make as-of reconstruction unavailable and must report the retained horizon.

### Current journal/history closure allocation

| Surface | Authored design/evidence | Required closure |
| --- | --- | --- |
| Non-create/delete reconstruction | CONTRACT-002 group-start/group-final metadata witness and independently required ordered deltas; TD-018; sixteen scoped synthetic correspondence vectors | Resolve US-015 two-row versus additional metadata-witness interpretation; adopt exact profile; complete native capture/staging and committed loader/definition/horizon producers |
| Complete manifest publication | Original positions remain in the digest; protected prepublication reservation is the recommended candidate | Reconcile baseline insertion-assigned timing; select native allocation/append/serialization/resource procedures and complete installation effects; do not repair committed rows |
| Journal mode transition | Transaction-wide shared writer/exclusive administrator algorithm; mode-only changes separated from dispatcher DDL; TD-016/STP-016 | Exact native exclusion/current-setting/savepoint/trigger timing and complete writer/admin/DDL wait matrix, then independent qualification |
| Bounded journal pages | TD-017 preserves row fragments and exact exclusive xid/seq continuation independently from feed acknowledgment | Native watermark/context/descriptor/retention/current-authority evidence; full mutation and transaction accumulation remain separate obligations |
| Historical disclosure and retention | Full original owner union across before/after/intermediate prerequisites; complete sibling/partition/definition dependency closure; TD-018/019 supplements | Native owner resolver/authority coordinator and checkpoint/archive/retention procedures; no implicit seed from metadata.after or current canonical state |

These are authored candidate procedures, not installed capabilities. The row-count clarification is pending; no answer is inferred from elapsed time or ongoing design work. Existing UMF is sufficient and Truss owns these producers. Weft continues to own compilation; no history design here adds a compiler or changes its ABI. The first integration checkpoint can be prepared independently where its selected scope does not require unresolved complete-profile behavior, while complete product history requirements remain mandatory for full closeout.

## Constraints, Risks and Rollback

A new layout/encoding/profile is explicit and versioned. An unsupported combination refuses before mutations or SQL emission. Keep the previous model/layout/profile artifacts for rollback; do not rewrite an installed database implicitly. New implementation code can be disabled/unregistered independently of stored data; a deployed breaking schema change needs its own reviewed migration. Before building, reconcile these references against current UMF/Weft interfaces and resolve the affected gates in the design coordination record.
