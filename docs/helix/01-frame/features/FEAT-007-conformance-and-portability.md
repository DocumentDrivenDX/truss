---
ddx:
  id: FEAT-007
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

# Feature Specification: FEAT-007 — Conformance and Portability

**Feature ID**: FEAT-007
**Status**: Draft
**Priority**: P0
**Covered PRD Subsystem(s)**: Conformance and portability
**Covered PRD Requirements**: FR-36 to FR-40, FR-50, FR-56
**Cross-Subsystem Rationale**: None; single subsystem.

## Overview

This feature makes truss a specification as well as a program: contracts and a corpus that let another implementation share the same tables and prove it.

## Ideal Future State

An implementer in another language reads the contracts, runs the corpus on a named PostgreSQL version and passes. Two implementations are pointed at one database and each reads what the other wrote. A database of a different major layout version is refused, and the layout DDL and its check pass on every supported PostgreSQL.

## Problem Statement

- **Current situation**: Prose descriptions of a storage layout drift between implementations; there is no neutral test.
- **Pain points**: A second implementation guesses; divergence is found in production.
- **Desired outcome**: Behavior fixed by data, not by reading code.

## Functional Areas

| Area | User question or job | Feature responsibility |
|------|----------------------|------------------------|
| Contracts | Is the behavior written down? | Layout, journal, catalog revision and mutation contracts |
| Corpus | Can I test against it? | Language-neutral cases with normative expectations |
| Interchange | Do two implementations agree? | Cross-read check |
| Versioning | Which layout is this database? | A declared version, refused on major mismatch |
| UMF reading | Does my reader agree with UMF's? | Corpus cases of documents and expected diagnostics |

## Requirements

### Functional Requirements by Area

#### Contracts

CNF-01. The layout, journal, catalog revision and mutation protocol are specified as contracts independent of any language (FR-36).

#### Corpus

CNF-02. A conformance corpus held as data gives expected results, state, journal and report per case; expected SQL is informative (FR-37).

#### Interchange

CNF-03. An implementation passes a corpus version on a named PostgreSQL version, and an interchange check shows two implementations read each other's writes (FR-38).

#### Versioning

CNF-04. The layout declares a version and an implementation refuses a database of a different major version (FR-39).
CNF-05. The layout DDL and its check pass on every supported PostgreSQL version (FR-40).

#### UMF reading

CNF-06. An implementation reads UMF so that it accepts and rejects the same documents, with the same diagnostics (severity, code and path), as the reference validator; the corpus carries documents and their expected diagnostics (FR-50).

#### Bootstrap from UMF

CNF-07. The internal physical layout is a versioned UMF artifact that generates reproducible bootstrap SQL. Every physical object is accounted for, unsupported generation is reported, and catalog/behavior parity must pass before it replaces the SQL baseline (FR-56).

### Non-Functional Requirements

- **Reproducibility**: the DDL and its check run on PostgreSQL 16.2 and 17.9 today.
- **Completeness**: the corpus covers catalog acceptance, the value corpus, the enforcement matrix, the write protocol and the journal.
- **Stability**: a case that contradicts an accepted decision is a defect in the case.

## User Stories

- [US-045 — Bootstrap the internal layout from UMF](../user-stories/US-045-bootstrap-the-internal-layout-from-umf.md)

- [US-039 — Read UMF the same way as the reference validator](../user-stories/US-039-read-umf-the-same-way-as-the-reference.md)
- [US-027 — Build an implementation from the contracts](../user-stories/US-027-build-an-implementation-from-the-contracts.md)
- [US-028 — Pass the corpus and the interchange check](../user-stories/US-028-pass-the-corpus-and-the-interchange-check.md)
- [US-029 — Declare the layout version and check the DDL on every version](../user-stories/US-029-declare-the-layout-version-and-check-the-ddl.md)

## Edge Cases and Error Handling

- **An unknown normative error kind or required case tag**: the corpus version is unsupported; no full conformance pass may be reported. Optional host-specific cases remain separately qualified.
- **A host-specific case**: tagged and outside the pass rule.
- **A corpus version newer than the implementation**: reported, not silently passed.

## Success Metrics

- The seed corpus exists and one implementation passes it; a second passes it and the interchange check.
- The DDL check passes on every supported version.

## Constraints and Assumptions

- The seed corpus is built from SPIKE-002's inputs; it does not exist yet.
- Minimum PostgreSQL version 16 is proposed.

## Dependencies

- **Other features**: all features, whose behavior the corpus tests.
- **External services**: PostgreSQL versions under test; interfaces in CONTRACT-001 to CONTRACT-004.

## Out of Scope

- Certifying third-party implementations.
- A reference implementation in every language.
