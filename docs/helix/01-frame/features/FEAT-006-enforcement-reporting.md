---
ddx:
  id: FEAT-006
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

# Feature Specification: FEAT-006 — Enforcement Reporting

**Feature ID**: FEAT-006
**Status**: Draft
**Priority**: P0
**Covered PRD Subsystem(s)**: Enforcement reporting
**Covered PRD Requirements**: FR-33 to FR-35
**Cross-Subsystem Rationale**: None; single subsystem.

## Overview

This feature makes enforcement a visible, verified fact: for every UMF assertion, who enforces it, with the evidence, and no overclaiming.

## Ideal Future State

Before go-live an engineer opens the report and sees, per assertion, whether PostgreSQL enforces it, truss enforces it, or nothing does. A guarantee is called a database guarantee only if it holds for a caller that bypasses the engine. Every support statement names the versions it was tested on and links the test.

## Problem Statement

- **Current situation**: Teams assume constraints hold because a schema says so; engine-enforced rules are reported as database guarantees.
- **Pain points**: Unverified claims; a rule enforced only in application code that someone bypasses.
- **Desired outcome**: A machine-readable status per assertion, tested against a real PostgreSQL.

## Functional Areas

| Area | User question or job | Feature responsibility |
|------|----------------------|------------------------|
| Status | Who enforces this rule? | Database, engine or none, per assertion |
| Honesty | Does the database guarantee survive a bypass? | Reported as database only if a bypass fails |
| Evidence | Where is the proof? | Versioned support statements linking tests |

## Requirements

### Functional Requirements by Area

#### Status

ENF-01. Every UMF assertion has an enforcement status, a rule name and its evidence (FR-33).

#### Honesty

ENF-02. A guarantee is reported as database enforcement only if it holds for a caller that bypasses the engine; otherwise it is engine enforcement (FR-35).

#### Evidence

ENF-03. Every support statement names the PostgreSQL and UMF versions and links executable evidence (FR-34).

### Non-Functional Requirements

- **Verification**: statuses are checked by tests that attempt the violation through plain SQL and through the engine.
- **Currency**: the report is regenerated on every acceptance.

## User Stories

- [US-025 — Report the enforcement layer of every assertion](../user-stories/US-025-report-the-enforcement-layer-of-every-assertion.md)
- [US-026 — Back every support claim with evidence](../user-stories/US-026-back-every-support-claim-with-evidence.md)

## Edge Cases and Error Handling

- **An assertion UMF carries as opaque text**: reported as none.
- **A rule enforced by a deferred trigger under READ COMMITTED**: reported as engine, because concurrent transactions can violate it.
- **A status that changes between PostgreSQL versions**: reported per version.

## Success Metrics

- 100% of assertions in the corpus classified; 0 status claims without a test.

## Constraints and Assumptions

- The enforcement matrix of SPIKE-002 is the seed: 19 of 19 assertions enforced in its model.

## Dependencies

- **Other features**: FEAT-001 (the acceptance report), FEAT-002 (the constraints), FEAT-003 (cross-row rules).

## Out of Scope

- Fixing unenforced rules; the report only states them.
