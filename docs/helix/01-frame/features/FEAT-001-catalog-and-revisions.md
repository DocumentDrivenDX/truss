---
ddx:
  id: FEAT-001
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

# Feature Specification: FEAT-001 — Catalog and Revisions

**Feature ID**: FEAT-001
**Status**: Draft
**Priority**: P0
**Covered PRD Subsystem(s)**: Catalog and revisions
**Covered PRD Requirements**: FR-1 to FR-8
**Cross-Subsystem Rationale**: None; single subsystem.

## Overview

The catalog is where UMF documents become types, properties, keys and relationships that the rest of truss reads. It accepts a set of documents as one revision or rejects the set with every reason, and it never changes a table to do so.

## Ideal Future State

A platform engineer publishes a UMF revision that adds an entity, a property and a relationship, and a report says what was added, what is provisional and which rules are enforced by which layer. A revision that would break stored data is refused before it is accepted, with every offending object listed. Nothing about the database's tables changes, and writes in flight are not disturbed beyond a short wait.

## Problem Statement

- **Current situation**: Adding an entity or relationship to connected PostgreSQL data means a migration, a table lock and a new index, and the schema the team already maintains in UMF is a second model to keep in step.
- **Pain points**: Migration churn; no way to see before acceptance which stored values break a tightened rule; relationships to entities defined elsewhere cannot be imported.
- **Desired outcome**: A revision is accepted in catalog rows only, at a cost independent of the number of types, with a report the engineer can read before go-live.

## Functional Areas

| Area | User question or job | Feature responsibility |
|------|----------------------|------------------------|
| Import | Can I load my UMF documents, in whatever order they arrive? | Verify, order, derive and persist a set as one revision |
| Unknown references | What if a relationship names an entity nobody defined yet? | Reject, provisional type or skip, by policy, always reported |
| Identity | Do my identifiers survive a revision? | Stable, never-reused catalog identifiers |
| Tightening | Will this revision break my data? | List every violator before accepting |
| Report | What did the revision do, and what is enforced? | One report per acceptance |

## Requirements

### Functional Requirements by Area

#### Import

CAT-01. A set of UMF documents is accepted as one catalog revision, or rejected as a whole with every reason reported (FR-1).
CAT-02. Documents are ordered deterministically so each follows those it depends on; documents that depend on each other are accepted together (FR-2).

#### Unknown references

CAT-03. A relationship naming an entity type no document defines is handled by policy: reject, create a provisional type reported until defined, or skip and report the loss (FR-3).

#### Identity

CAT-04. A type, property, key or relationship keeps its identifier while its UMF identity is unchanged; identifiers are never reused, even after retirement (FR-4).

#### Tightening

CAT-05. A revision that tightens or adds a rule lists every stored object that would violate it and is rejected if any does (FR-5).
CAT-06. A change of a property's type or cardinality is accepted only with a declared total transform applied in the same acceptance (FR-6).

#### No DDL

CAT-07. Accepting a revision creates no table, partition, column or index (FR-7).

#### Report

CAT-08. Every acceptance produces a report of the UMF versions seen, elements added, retired and provisional, data re-bound, and the enforcement layer of every assertion (FR-8).

### Non-Functional Requirements

- **Performance**: acceptance cost is catalog rows; adding five types took 0 to 3 ms on the adopted layout against 6 to 163 ms on partitioned layouts (SPIKE-003).
- **Reliability**: acceptance is atomic; an interrupted acceptance leaves the previous revision in force.
- **Concurrency**: acceptance waits for running writers and sets a lock timeout; an optional queue prevents starvation under constant write load (SPIKE-003).
- **Exactness**: documents are retained verbatim with a content digest, so a revision can be audited later.

## User Stories

- [US-001 — Accept a UMF revision as a whole or reject it with every reason](../user-stories/US-001-accept-a-umf-revision-as-a-whole.md)
- [US-002 — Import documents in dependency order](../user-stories/US-002-import-documents-that-depend-on-each-other.md)
- [US-003 — Decide what happens to an unknown entity type](../user-stories/US-003-decide-what-happens-to-an-unknown-entity-type.md)
- [US-004 — Keep identifiers stable across revisions](../user-stories/US-004-keep-identifiers-stable-across-revisions.md)
- [US-005 — See every violator before a tightening is accepted](../user-stories/US-005-see-every-violator-before-a-tightening-is-accepted.md)
- [US-006 — Add a type without DDL](../user-stories/US-006-add-a-type-without-ddl.md)

## Edge Cases and Error Handling

- **Two documents define the same element with different content**: rejected as a duplicate definition.
- **The same documents accepted twice**: no new revision.
- **A dependency cycle between documents**: accepted together, ordered by document identifier.
- **Retained data matches a newly defined property**: re-bound, journaled and reported, not dropped.
- **The lock is not granted in time**: the acceptance rolls back and may be retried.

## Success Metrics

- Every acceptance in the corpus produces a report with no unclassified assertion.
- 0 DDL statements during any acceptance.
- 100% of rejected sets name every reason.

## Constraints and Assumptions

- UMF semantics are UMF's; truss never defines them.
- Documents are UMF core 0.7.0 at the time of writing; other dialects arrive through an adapter with a loss report.

## Dependencies

- **Other features**: FEAT-002 (the rows a revision writes), FEAT-003 (the catalog lock), FEAT-006 (the enforcement report).
- **External services**: UMF's validator and library; interface in CONTRACT-003.

## Out of Scope

- Defining or extending UMF.
- Converting other schema dialects beyond the adapter boundary.
- A user interface for reviewing revisions.
