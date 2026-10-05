---
ddx:
  id: FEAT-008
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

# Feature Specification: FEAT-008 — Host Integration

**Feature ID**: FEAT-008
**Status**: Draft
**Priority**: P1
**Covered PRD Subsystem(s)**: Host integration
**Covered PRD Requirements**: FR-41 to FR-44
**Cross-Subsystem Rationale**: None; single subsystem.

## Overview

This feature is how an application that owns a database adds its own structure and policy around truss's tables without changing them.

## Ideal Future State

A host adds its own schema, triggers, row-level security and role grants. It assumes a role per transaction through a connection pool in transaction mode, with or without prepared statements, and the journal records the role. The same layout runs on an embedded PostgreSQL in its test suite.

## Problem Statement

- **Current situation**: A host that wants a stronger audit trail or per-role writes must fork the layout or wrap it blindly.
- **Pain points**: Unclear what a host may change; session state that breaks pooling; tests that need a real server.
- **Desired outcome**: A short list of permitted extensions and a layout that tolerates pools and embedded engines.

## Functional Areas

| Area | User question or job | Feature responsibility |
|------|----------------------|------------------------|
| Extension | What may a host add? | Its own objects, triggers, policies and roles |
| Roles | Can writes be governed by grants? | Role per transaction, recorded in the journal |
| Pooling | Does it work behind a pooler? | No session state; prepared statements optional |
| Embedded | Can tests run without a server? | Same DDL on an embedded PostgreSQL |

## Requirements

### Functional Requirements by Area

#### Extension

HST-01. A host may add its own tables, functions, roles, triggers and row-level security in its own schema, and may not change a truss column, key or constraint (FR-41).

#### Roles

HST-02. Writes can be governed by role grants: a host assumes a role per transaction and truss records it in the journal (FR-42).

#### Pooling

HST-03. truss keeps no session state and works through a transaction-mode pooler, with or without prepared statements (FR-43).

#### Embedded

HST-04. The layout and protocols work on an embedded PostgreSQL with the same DDL as a server (FR-44).

### Non-Functional Requirements

- **Pooling**: unprepared reads cost 0.01 to 0.05 ms more on the adopted layout (SPIKE-003).
- **Security**: foreign-key and unique checks run regardless of row-level security and can reveal that a hidden row exists; the host decides how to report it.
- **Portability**: tested on embedded PostgreSQL 16.2 and 17.9.

## User Stories

- [US-030 — Extend the layout from a host](../user-stories/US-030-extend-the-layout-from-a-host.md)
- [US-031 — Govern writes by role grants](../user-stories/US-031-govern-writes-by-role-grants.md)
- [US-032 — Work behind a transaction-mode pooler](../user-stories/US-032-work-behind-a-transaction-mode-pooler.md)
- [US-033 — Run the layout on an embedded PostgreSQL](../user-stories/US-033-run-the-layout-on-an-embedded-postgres.md)

## Edge Cases and Error Handling

- **A host trigger that writes the journal**: allowed; the engine then must not write journal rows or version columns itself.
- **A host assumes a role the caller named**: the host validates it; truss only records it.
- **A pooler that does not support session state**: nothing in truss needs it.

## Success Metrics

- 0 host extensions in the test host that require changing a truss table definition.
- The corpus passes on an embedded PostgreSQL.

## Constraints and Assumptions

- `SET LOCAL ROLE` with `INHERIT FALSE, SET TRUE` grants needs PostgreSQL 16 or later (proposed minimum).
- Managed PostgreSQL services are unverified.

## Dependencies

- **Other features**: FEAT-004 (journal modes), FEAT-007 (conformance on embedded engines).
- **External services**: PostgreSQL roles; interface in CONTRACT-001 (extension rules).

## Out of Scope

- Choosing a host's roles or policies.
- A hosted service.
