---
ddx:
  id: FEAT-002
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

# Feature Specification: FEAT-002 — Storage, Identity and Exactness

**Feature ID**: FEAT-002
**Status**: Draft
**Priority**: P0
**Covered PRD Subsystem(s)**: Storage, identity and exactness
**Covered PRD Requirements**: FR-9 to FR-15, FR-45, FR-46
**Cross-Subsystem Rationale**: None; single subsystem.

## Overview

This feature is the fixed table set: how objects, edges and keys are stored so that every value is exact, nothing is dropped, and the database itself enforces keys and endpoints.

## Ideal Future State

An engineer writes values of every UMF scalar family and reads them back unchanged, including the awkward ones. A value the schema does not define is kept and listed. A second object with the same key is refused by the database, an edge to the wrong type of object is refused by the database, and an object that is still connected cannot be deleted.

## Problem Statement

- **Current situation**: Per-type tables change shape with the schema; JSONB conflates absent and null and loses precision in JavaScript numbers; keys and endpoints are enforced, if at all, by application code.
- **Pain points**: Silent value loss and silent coercion; integrity that depends on caller discipline.
- **Desired outcome**: One table set whose guarantees do not depend on the number or kind of types, with every enforcement claim backed by a test that bypasses the engine.

## Functional Areas

| Area | User question or job | Feature responsibility |
|------|----------------------|------------------------|
| Objects and edges | Where does my data live? | One object table, one edge table, typed property maps |
| Exact values | Is what I read what I wrote? | Canonical encodings and exact parsing |
| Retained data | What happens to data the schema does not know? | Retain, report, re-bind later |
| Keys | Can I find an object by its business key? | Database-enforced keys per type |
| Edges | Can a relationship be wrong? | Typed endpoints, protected deletion, multiplicity |
| Import | Can I re-run an import safely? | Idempotent import, reserved keys, source facts |

## Requirements

### Functional Requirements by Area

#### Objects and edges

STO-01. Objects of every type live in one fixed table set and edges in their own table, with typed properties in a map keyed by property identifier (FR-9).

#### Exact values

STO-02. Values round-trip exactly: integers beyond 2^53, decimals with trailing zeros, timestamps with offset, binary, explicit null versus absent, and any string except U+0000 (FR-10).

#### Retained data

STO-03. A value matching no definition is retained under its original name and reported; a later revision that defines it re-binds it, journaled and reported (FR-11).

#### Keys

STO-04. A key value is unique within its type, enforced by the database, and found by its canonical text, which is equal for equal values of the declared type (FR-12).

#### Edges

STO-05. An edge joins two existing objects of types its relationship allows; the database refuses anything else, and an object that still has edges cannot be deleted (FR-13).
STO-06. A maximum multiplicity of one is enforced by the database without a per-relationship index; larger maxima are enforced in the write protocol (FR-14).
STO-07. Object and edge identifiers come from one sequence and are never reused (FR-15).

#### Import

STO-08. Importing the same records again changes nothing: a record is identified by its type and primary key (an edge by its relationship and endpoints), a record already held or deleted is skipped, and what was created, skipped and rejected is reported (FR-45).
STO-09. An imported record keeps the load it came from and the source's own facts (author, time, system), recorded once and never changed (FR-46).

### Non-Functional Requirements

- **Performance**: point reads by id or key and one-hop reads stay at 0.02 to 0.04 ms at 1,000 types because the plans do not depend on the number of types (SPIKE-003).
- **Storage**: the key table costs about 70% more disk than a partitioned layout; accepted for the planning and lock results (SPIKE-003).
- **Exactness**: values are read as text and parsed exactly; a client that parses to a double is a defect.

## User Stories

- [US-007 — Store and read objects and edges exactly](../user-stories/US-007-store-and-read-objects-and-edges-exactly.md)
- [US-008 — Keep what the schema does not define](../user-stories/US-008-keep-what-the-schema-does-not-define.md)
- [US-009 — Find an object by its key](../user-stories/US-009-find-an-object-by-its-key.md)
- [US-010 — Refuse bad edges and protect connected objects](../user-stories/US-010-refuse-bad-edges-and-protect-connected-objects.md)
- [US-011 — Limit an edge's multiplicity without an index per relationship](../user-stories/US-011-limit-an-edges-multiplicity.md)
- [US-034 — Repeat an import and change nothing](../user-stories/US-034-repeat-an-import-and-change-nothing.md)
- [US-035 — Keep the source facts of an imported record](../user-stories/US-035-keep-the-source-facts-of-an-imported-record.md)

## Edge Cases and Error Handling

- **An object lacks a key component**: it has no key row, is not reachable by that key, and the engine reports it.
- **Two timestamps differ only in offset**: different keys.
- **`1.0` and `1.00` as a decimal key**: the same key.
- **Delete of an object with an edge**: refused by the database.
- **A deleted key and a later import or create**: the value is reserved while `key_reuse` is `forbid`; an import skips it and a direct create is refused.
- **A type with no primary key**: its records cannot be imported idempotently and are rejected with that reason.
- **Explicit null written to a property**: stored as null, distinct from absent.

## Success Metrics

- 100% of the value corpus round-trips exactly on every supported PostgreSQL version.
- 0 plain-SQL attempts succeed in creating a duplicate key, a bad endpoint or a dangling edge.

## Constraints and Assumptions

- The layout is fixed by CONTRACT-001; changes are layout versions.
- Per-type CHECK constraints are not used; per-type rules are engine- or catalog-trigger-enforced.

## Dependencies

- **Other features**: FEAT-001 (types and keys), FEAT-003 (writes that fill the tables), FEAT-004 (the journal).
- **External services**: PostgreSQL; interface in CONTRACT-001.

## Out of Scope

- Per-type tables or views.
- Choosing storage homes beyond the thresholds ADR-002 marks provisional.
