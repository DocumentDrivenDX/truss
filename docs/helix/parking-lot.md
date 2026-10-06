---
ddx:
  id: truss.parking-lot
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.prd
      kind: informed_by
    - id: ADR-001
      kind: informed_by
    - id: ADR-002
      kind: informed_by
---

# Parking Lot

Work that has been deliberately deferred. The [PRD](01-frame/prd.md) points
here for its deferred items. Each entry names where it was deferred and what
would bring it back. An entry here is not a commitment. Pick one up only
through a framed requirement or an ADR.

Permanent non-goals are not listed here. They stay in the PRD's Non-Goals:
defining UMF semantics, authenticating people, a user interface or hosted
service, a document as the unit of storage, and choosing journal retention for a
deployment.

## Deferred capabilities

| Item | Deferred by | Revisit when |
|------|-------------|--------------|
| Query language: ISO GQL, SQL/PGQ or a subset, compiled to SQL | PRD Technical Context ("the query and mutation engines are later"); [FEAT-005](01-frame/features/FEAT-005-reads-and-traversal.md) out of scope | The storage-level reads (FR-28 to FR-32) pass the corpus. The language choice needs its own ADR |
| Filters on properties, variable-length paths and traversals beyond three hops | FEAT-005 out of scope; [US-023](01-frame/user-stories/US-023-traverse-one-to-three-hops.md) | With the query language. Variable-length paths need an explicit depth bound (SPIKE-001: the variable-length cache cost 577 ms p95 under writes) |
| Full-text and analytic queries | FEAT-005 out of scope | A framed user need |
| Bulk mutation | [FEAT-003](01-frame/features/FEAT-003-mutation-and-concurrency.md) out of scope | With the query language, or an import need that FR-45 does not meet |
| Reading as of a wall-clock time | [FEAT-004](01-frame/features/FEAT-004-journal-and-history.md) out of scope | A framed need beyond as-of-version reads (FR-26) |
| Journal consumer that publishes to a warehouse | PRD Nice to Have (P2) 2; FEAT-004 out of scope | P0 and P1 are met |
| Declared indexes and extended statistics, within a reported budget | PRD Nice to Have (P2) 1; [ADR-002](02-design/adr/ADR-002-storage-strategy.md) D11 | Filters on properties are framed, or planner estimates are measured as a problem (storage layout review §11) |
| Typed views over the graph for tools that expect tables | PRD Nice to Have (P2) 3 | A framed consumer that reads with plain SQL |
| Per-type ("shaped") tables for hot types, behind differential tests | ADR-002 (later, measured optimization); FEAT-002 out of scope | A reversal condition in ADR-002 fires, such as missing the 2× bar at the committed scale |
| Journal-canonical storage, with current state as a projection | ADR-002 D7 | A need for exact replay or rebuild that the object row cannot meet |
| A second backing engine, such as SQL Server | PRD Non-Goals ("in this version") | A named consumer that cannot use PostgreSQL. Needs an ADR and the `area:dialects` boundary |
| A Rust core with Python and Node bindings | [ADR-001](02-design/adr/ADR-001-language-and-portable-core.md) D6 and D7 | A D6 trigger fires and a new ADR records the evidence |
| Converting other schema dialects beyond the adapter boundary | [FEAT-001](01-frame/features/FEAT-001-catalog-and-revisions.md) out of scope | A framed need for a dialect UMF does not already cover |
| Certifying third-party implementations | [FEAT-007](01-frame/features/FEAT-007-conformance-and-portability.md) out of scope | A second implementation passes the corpus and the interchange check (FR-38) |

## Upstream items (UMF)

These are not truss work. They are gaps passed to UMF, listed so they are not
lost. See the [discovery input](00-discover/vision-input.md) and
[SPIKE-002](02-design/spikes/SPIKE-002-storage-bake-off.md) Next Steps.

| Gap | Effect on truss until UMF resolves it |
|-----|---------------------------------------|
| Representation of `json`-like properties in UMF core | Not bound; values are retained and reported (PRD open question) |
| Schema evolution operations between revisions | Revisions use truss-local transforms (FR-6) |
| Temporal semantics: instant versus civil time, offset retention | Timestamps are kept as the author's RFC 3339 text (ADR-002 D3) |
| Record-level invariants and value constraints | Carried as opaque text and reported, not enforced |
| A generic storage strategy in `umf-binding-1` | Carried as a truss-owned extension vocabulary (ADR-002 D12) |
