---
ddx:
  id: FEAT-004
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

# Feature Specification: FEAT-004 — Journal and History

**Feature ID**: FEAT-004
**Status**: Draft
**Priority**: P0
**Covered PRD Subsystem(s)**: Journal and history
**Covered PRD Requirements**: FR-22 to FR-27
**Cross-Subsystem Rationale**: None; single subsystem.

## Overview

The journal is the append-only record of every change, written in the transaction that made it. It is the audit trail, the source of as-of reads and the feed a consumer reads incrementally.

## Ideal Future State

An auditor sees who or what changed which property, from what to what, under which schema revision and as which database role. A consumer reads changes in a stable order and never misses one that committed late. Plain SQL changes are journaled too where the deployment requires it. Old partitions are dropped, never rows edited.

## Problem Statement

- **Current situation**: History is bolted on by triggers per table, written by the application, or absent; the acting role is whatever the caller says; incremental readers miss rows that commit out of order.
- **Pain points**: Unreliable audit trail; no as-of reads; fragile change feeds.
- **Desired outcome**: One journal, atomic with the change, with an origin the caller cannot forge and a feed that is complete.

## Functional Areas

| Area | User question or job | Feature responsibility |
|------|----------------------|------------------------|
| Writing | Is every change recorded? | Atomic rows per change, or by trigger for all changes |
| Origin | Who did it? | Asserted actor plus the database's own role |
| Reading | Can I replay or consume it? | Consumer watermark; as-of by version |
| Retention | How is it trimmed? | Whole partitions only |

## Requirements

### Functional Requirements by Area

#### Writing

JNL-01. Every change writes journal rows in the same transaction, and a journal failure fails the change (FR-22).
JNL-02. A deployment can require that every change, including plain SQL, is journaled by having the database write the journal (FR-24).

#### Origin

JNL-03. A row records entity, version, operation, property, old and new value, catalog revision and an origin carrying the asserted actor and the database role; the role is never taken from the caller (FR-23).

#### Reading

JNL-04. A consumer reads the journal incrementally in a stable order without missing a late-committing row (FR-25).
JNL-05. A record is reconstructed as of a version from its journal, with each value read under the definition in force when written (FR-26).

#### Retention

JNL-06. The journal is append-only, time-partitioned with no default partition, and trimmed only by dropping whole partitions (FR-27).

### Non-Functional Requirements

- **Correctness**: a committed row is withheld while an older transaction is open and both appear in order afterwards (verified on PostgreSQL 16.2 and 17.9).
- **Integrity**: the role is read from the database (`current_setting('role')`, else the session user), because inside a definer function `current_user` is the function's owner.
- **Operations**: a write with no covering partition fails and rolls back; a deployment creates partitions ahead.

## User Stories

- [US-015 — Journal every change atomically with its origin](../user-stories/US-015-journal-every-change-atomically.md)
- [US-016 — Journal plain SQL changes too](../user-stories/US-016-journal-plain-sql-changes-too.md)
- [US-017 — Read the journal incrementally without missing a change](../user-stories/US-017-read-the-journal-incrementally-without-missing-a-change.md)
- [US-018 — Reconstruct a record as of a version](../user-stories/US-018-reconstruct-a-record-as-of-a-version.md)
- [US-019 — Trim the journal by dropping partitions](../user-stories/US-019-trim-the-journal-by-dropping-partitions.md)

## Edge Cases and Error Handling

- **A write at a time no partition covers**: fails with a check violation; the change does not commit.
- **A change that alters nothing**: no row and no version increase.
- **A consumer's saved position is ahead of the safe watermark**: it reads nothing until the watermark passes it.
- **A delete**: one row holding the old record.
- **An as-of read of a version that was never written**: empty history, not an error.

## Success Metrics

- 0 changes without journal rows across the write-path tests, including forced failures.
- 100% of the journal-feed tests pass on every supported PostgreSQL version.

## Constraints and Assumptions

- `at` is the statement clock, not a commit time; as-of reads are by version.
- Retention periods and partition intervals belong to the deployment.

## Dependencies

- **Other features**: FEAT-002 (the changed records), FEAT-003 (the write protocol).
- **External services**: PostgreSQL transaction snapshots; interface in CONTRACT-002.

## Out of Scope

- Publishing the journal to a warehouse (P2).
- Reading as of a wall-clock time.
