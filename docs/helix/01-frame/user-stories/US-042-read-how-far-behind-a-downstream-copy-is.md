---
ddx:
  id: US-042
  type: user-story
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-004
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-042: Read how far behind a downstream copy is

**Feature**: FEAT-004 — Journal and History
**Feature Requirements**: JNL-08
**PRD Requirements**: FR-53
**Priority**: P1
**Status**: Draft

## Story

**As a** Auditor
**I want** see, for each registered consumer, how old the oldest change it has not applied is
**So that** anyone relying on the copy can say how current it is

## Context

Lag depends on the transport and on long-running transactions; it has to be observable, not assumed.

## Walkthrough

1. A consumer reports its position after applying a batch.
2. Auditor reads its lag.
3. A long transaction holds the safe watermark back.
4. Auditor reads lag again.

## Acceptance Criteria

- [ ] **US-042-AC1** — Given a registered consumer, when it applies changes, then its recorded position and update time advance.
- [ ] **US-042-AC2** — Given unapplied changes below the safe watermark, when lag is read, then it is the age of the earliest one.
- [ ] **US-042-AC3** — Given a long-running transaction holding the watermark, when lag is read, then changes above the watermark are reported separately as not yet publishable.
- [ ] **US-042-AC4** — Given a copy built from the feed, when it states how current it is, then it names the position it reflects.

## Edge Cases

- **No registered consumer**: no lag is reported.
- **A consumer ahead of the watermark**: nothing to read; lag is zero.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Position | US-042-AC1 | Applied batch | Read consumer | Advanced |
| Lag | US-042-AC2 | Unapplied changes | Read lag | Earliest age |
| Held back | US-042-AC3 | Long transaction | Read lag | Reported separately |
| States position | US-042-AC4 | Copy | Read | Position named |

## Dependencies

- **Stories**: US-041
- **Feature Spec**: FEAT-004
- **Feature Requirements**: JNL-08
- **PRD Requirements**: FR-53
- **External**: CONTRACT-006, Freshness evidence.

## Out of Scope

None.
