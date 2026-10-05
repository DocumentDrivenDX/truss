---
ddx:
  id: FEAT-003
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

# Feature Specification: FEAT-003 — Mutation and Concurrency

**Feature ID**: FEAT-003
**Status**: Draft
**Priority**: P0
**Covered PRD Subsystem(s)**: Mutation and concurrency
**Covered PRD Requirements**: FR-16 to FR-21, FR-51, FR-54
**Cross-Subsystem Rationale**: None; single subsystem.

## Overview

Every write, from any implementation, follows one protocol so that validation, locking, versioning and the journal agree and a catalog change that races with a write is detected.

## Ideal Future State

A writer sees all of its violations at once, a stale writer is told to retry, an expected version stops lost updates, and a revision accepted mid-write is never missed, under either isolation level. Two implementations over one database cannot disagree about what a write does.

## Problem Statement

- **Current situation**: Concurrent schema change and writes either block each other broadly or let a write validate against a schema that no longer applies.
- **Pain points**: Lost updates; a write that validated against an old schema; deadlocks from inconsistent lock order; the first-error-only validation loop.
- **Desired outcome**: One documented protocol, tested under both isolation levels, with error kinds each callable can act on.

## Functional Areas

| Area | User question or job | Feature responsibility |
|------|----------------------|------------------------|
| Protocol | What does a write do, in what order? | One transaction: head check, lock, version, validate, apply, journal |
| Catalog races | What if the schema changes under me? | Detect it and retry |
| Versions | Can I avoid overwriting someone else's change? | Expected version |
| Errors | What can fail, and what should I do? | A fixed set of error kinds with retry rules |

## Requirements

### Functional Requirements by Area

#### Protocol

MUT-01. Every write follows one protocol in one transaction (FR-16).
MUT-02. A writer may pass an expected version; the write is refused if it differs, and a change that alters no value writes nothing and does not raise the version (FR-19).

#### Catalog races

MUT-03. A revision accepted while a write runs is detected under READ COMMITTED and REPEATABLE READ and the write is not accepted against the old revision (FR-17).
MUT-04. An acceptance can wait for writers, sets a timeout, may retry, and may use a queue so it is not starved (FR-18).

#### Errors

MUT-05. Errors are of defined kinds, each with a stated retry rule (FR-20).

#### Cross-row rules

MUT-06. Cross-row rules lock the parent or run serializable; a deferred trigger under READ COMMITTED alone is never reported as database enforcement (FR-21).

#### Groups

MUT-07. A caller can apply several operations as one atomic group, with one origin and one catalog check, that commits or fails as a whole and names the failing operation (FR-51).
MUT-08. A caller can give a group a request identifier so that applying it again returns the original results and changes nothing, including when two identical requests arrive at once, and reuse with different inputs is refused (FR-54).

### Non-Functional Requirements

- **Correctness**: tested against the stale-write cases of SPIKE-003 (head row detects under both isolation levels; advisory-only and new-row-per-revision do not).
- **Throughput**: the head-row lock costs nothing measurable at 4 and 16 writers; the optional queue costs 6 to 25% (SPIKE-003).
- **Latency**: a write needs at most one extra round trip for the head check when issued as one call.

## User Stories

- [US-012 — Write with one protocol and report every violation](../user-stories/US-012-write-with-one-protocol-and-report-every-violation.md)
- [US-013 — Refuse a write against a stale catalog](../user-stories/US-013-refuse-a-write-against-a-stale-catalog.md)
- [US-014 — Keep cross-row rules honest](../user-stories/US-014-keep-cross-row-rules-honest.md)
- [US-040 — Apply several operations as one atomic group](../user-stories/US-040-apply-operations-as-one-atomic-group.md)
- [US-043 — Make a group safe to repeat](../user-stories/US-043-make-a-group-safe-to-repeat.md)

## Edge Cases and Error Handling

- **Two writers update one object**: one waits on the row lock; the second sees the new version and, if it passed one, is told of a version conflict.
- **Deadlock or serialization failure**: reported as retry; nothing was changed.
- **A revision accepted between validation and commit**: the write fails as catalog changed, never commits.
- **Journal write fails**: the whole write rolls back.

## Success Metrics

- 0 stale writes accepted across the isolation-level test matrix.
- Acceptance wait at most 5 s at the median under sixteen continuous writers without the queue; at most 50 ms with it.

## Constraints and Assumptions

- The protocol is CONTRACT-004; the lock rules are in CONTRACT-001.
- Exact error names are contract surface, not PRD.

## Dependencies

- **Other features**: FEAT-001 (the catalog being checked), FEAT-002 (the tables written), FEAT-004 (the journal rows).
- **External services**: PostgreSQL row locks and isolation levels; interface in CONTRACT-004.

## Out of Scope

- Query languages and bulk mutation.
- A distributed lock or cross-database transaction.
