---
ddx:
  id: US-045
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-007
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-045: Bootstrap the internal layout from UMF

**Feature:** FEAT-007 — Conformance and Portability
**Feature Requirements:** CNF-07
**PRD Requirements:** FR-56
**Priority:** P0
**Status:** Draft

## Story

**As a** Implementer
**I want** generate Truss's internal database layout from its versioned UMF description
**So that** the model, installed database and verification scenarios describe the same physical contract

## Context

Application-model acceptance adds catalog rows and its required atomic data/report effects without physical DDL. This separate bootstrap creates Truss’s fixed system tables and administrative objects once. UMF owns SQL representation and generic generation; Truss owns the physical model, complete required-object/effect inventory and protected installer/parity protocol. Native PostgreSQL meaning and generator gaps must remain inspectable rather than being hidden in handwritten patches. A generated source artifact or structural schema-browser diagram is not an installed-ready system: readiness requires all selected callable, privilege, dependency, initializer and behavioral obligations plus independently confirmed installation settlement. Fresh genesis records installation provenance, not a fabricated accepted catalog or layout migration receipt. Existing installations use the separately shipped explicit migration system rather than fresh-bootstrap repair.

## Walkthrough

1. The implementer selects a layout model, generator profile and target PostgreSQL version.
2. The toolkit generates a complete bootstrap candidate and coverage report under CONTRACT-008.
3. The implementer reviews the report and installs the candidate into a disposable database.
4. Catalog comparison and behavior probes verify the candidate against the checked layout baseline.

## Acceptance Criteria

- [ ] **US-045-AC1** — Given the pinned model and generator inputs, when generation is repeated, then bootstrap bytes and the ordered coverage report are identical.
- [ ] **US-045-AC2** — Given generated and baseline layouts, when installed in separate disposable databases on each qualified version, then the declared catalog surfaces and behavior probes match.
- [ ] **US-045-AC3** — Given a required unsupported or omitted object, when generation is attempted, then installation readiness is refused with a source-qualified diagnostic and no hidden patch.
- [ ] **US-045-AC4** — Given an edited native layout model, when SQL is regenerated, then it reflects the current model, while the original source remains retained and is not substituted.
- [ ] **US-045-AC5** — Given a nonempty incompatible database, when fresh bootstrap is requested, then it is refused without changing existing objects.

## Edge Cases

Unknown native content survives in the model; inability to export selected meaning blocks generation. A native parse-tree check does not certify server execution. An accepted application catalog revision never invokes bootstrap DDL.

## Test Scenarios

| Scenario | AC ID | Input | Expected |
| --- | --- | --- | --- |
| Repeat | US-045-AC1 | Same model/profile/name policy twice | Equal SQL/report bytes |
| Parity | US-045-AC2 | Two fresh databases per pinned server | Equal normalized catalog and probe outcomes |
| Missing sequence | US-045-AC3 | Coverage excludes journal sequence | Refused with its source identity |
| Edited default | US-045-AC4 | Change a default in copied native AST | New SQL reflects edit; old source retained |
| Existing layout | US-045-AC5 | Database with incompatible layout marker | No change |

## Dependencies

FEAT-007, CNF-07, FR-56; CONTRACT-001 and CONTRACT-008. UMF PostgreSQL representation/export and the native server oracle require their own pinned profile evidence.

## Out of Scope

Application-model per-type tables, automatic migrations of deployed databases and a new general UMF DDL compiler.
