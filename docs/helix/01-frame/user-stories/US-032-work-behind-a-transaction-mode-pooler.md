---
ddx:
  id: US-032
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-008
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-032: Work behind a transaction-mode pooler

**Feature**: FEAT-008 — Host Integration
**Feature Requirements**: HST-03
**PRD Requirements**: FR-43
**Priority**: P1
**Status**: Draft

## Story

**As a** Implementer
**I want** run through a pooler that gives a different connection each transaction, with or without prepared statements
**So that** I can use the connection infrastructure I already have

## Context

SPIKE-003 measured 0.01 to 0.05 ms extra for unprepared reads on its experimental layout; this is not qualification of a shipped layout or arbitrary pooler. Preparing is recommended where supported and not required for semantic correctness. Backend rotation is allowed between complete transactions, never inside one admitted live transaction. No Truss mutable session context, temporary-object dependency or cached backend identity may cross the transaction boundary. Native authenticated principal identity remains required and is independently admitted under the selected security profile; pooling cannot substitute a host role map for that authority.

## Walkthrough

1. Implementer points the engine at a transaction-mode pooler.
2. Each transaction may use a different backend connection.
3. System runs the corpus.
4. Implementer disables prepared statements and repeats.

## Acceptance Criteria

- [ ] **US-032-AC1** — Given a transaction-mode pooler, when the corpus runs, then every case passes with no session state kept.
- [ ] **US-032-AC2** — Given prepared statements disabled, when the corpus runs, then every case passes and the engine reports it is unprepared.
- [ ] **US-032-AC3** — Given unprepared execution, when point reads are measured at 1,000 types, then the extra cost is at most 0.05 ms.

## Edge Cases

- **A pooler that supports prepared statements**: the engine may use them only under its exact qualified driver/pooler protocol and lifetime rules; cached names alone cannot establish readiness after backend rotation.
- **Session-level settings**: no mutable Truss session setting is relied on across transactions. Transaction-local context is restored on success/refusal and independently checked after rollback/cancellation before safe pool reuse.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Pooled | US-032-AC1 | Pooler | Run corpus | Pass |
| Unprepared | US-032-AC2 | No prepares | Run corpus | Pass; reported |
| Cost | US-032-AC3 | 1,000 types | Measure | ≤ 0.05 ms extra |

## Dependencies

- **Stories**: US-012
- **Feature Spec**: FEAT-008
- **Feature Requirements**: HST-03
- **PRD Requirements**: FR-43
- **External**: SPIKE-003 F7.

## Out of Scope

Moving a live adopted transaction or held snapshot between backend connections. Installation and layout upgrades retain their separately qualified dedicated administrative transaction requirements; a pooled ordinary-operation pass does not qualify those deployment steps.
