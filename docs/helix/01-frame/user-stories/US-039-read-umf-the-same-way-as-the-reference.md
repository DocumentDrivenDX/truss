---
ddx:
  id: US-039
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

# US-039: Read UMF the same way as the reference validator

**Feature**: FEAT-007 — Conformance and Portability
**Feature Requirements**: CNF-06
**PRD Requirements**: FR-50
**Priority**: P0
**Status**: Draft

## Story

**As a** Implementer
**I want** check that my implementation accepts and rejects the same UMF documents, with the same diagnostics, as UMF's own validator
**So that** a document means the same thing to every implementation over one database

## Context

UMF owns document interpretation and validation. TypeScript consumes the pinned owner library; another-language implementation may consume the same qualified owner producer through an explicitly versioned integration rather than implement a competing checker. The host language does not waive validity, diagnostic, original-byte custody or subset conformance. Any independent reader still must match the pinned normative corpus, and shared producer use alone does not qualify its transport, losslessness, resource or Truss acceptance integration. Source-valid UMF and admissible Truss storage/execution support are separate verdicts: Truss can refuse an unsupported dependent profile without inventing UMF validation errors or silently dropping preserved unknown content.

## Walkthrough

1. Implementer loads the corpus's UMF cases: documents with their expected validity and diagnostics.
2. Implementer runs the selected pinned UMF reader/producer integration over each original document.
3. System compares validity and each diagnostic's severity, code and path.
4. Implementer reruns after fixing a difference.

## Acceptance Criteria

- [ ] **US-039-AC1** — Given a document the reference accepts, when the implementation reads it, then it accepts it.
- [ ] **US-039-AC2** — Given a document the reference rejects, when the implementation reads it, then it rejects it with the same set of diagnostics, each with the same severity, code and path.
- [ ] **US-039-AC3** — Given a document using a UMF feature the implementation does not support, when it is read, then the implementation rejects it and says so, never accepting it silently.
- [ ] **US-039-AC4** — Given a new UMF version, when the corpus is updated, then the cases name the UMF version they target and an implementation reports which versions it passes.

## Edge Cases

- **A warning-only document**: accepted, with the warning in the report.
- **Message text**: not compared; only severity, code and path are normative.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Accept | US-039-AC1 | Valid document | Read | Accepted |
| Reject | US-039-AC2 | Invalid document | Read | Same diagnostics |
| Unsupported | US-039-AC3 | Unsupported feature | Read | Rejected, said so |
| Versions | US-039-AC4 | New UMF version | Run corpus | Versions reported |

## Dependencies

- **Stories**: US-027
- **Feature Spec**: FEAT-007
- **Feature Requirements**: CNF-06
- **PRD Requirements**: FR-50
- **External**: CONTRACT-003, step 1; CONTRACT-004, corpus.

## Out of Scope

None.
