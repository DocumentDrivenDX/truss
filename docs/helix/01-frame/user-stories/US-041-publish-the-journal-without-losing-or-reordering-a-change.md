---
ddx:
  id: US-041
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

# US-041: Publish the journal without losing or reordering a change

**Feature**: FEAT-004 — Journal and History
**Feature Requirements**: JNL-07
**PRD Requirements**: FR-52
**Priority**: P1
**Status**: Draft

## Story

**As a** Implementer
**I want** feed a downstream copy that gets every change once, in order, including deletes and schema revisions
**So that** the copy is complete and can be rebuilt after a failure

## Context

A publisher may be a custom reader or a database-native synchronization; the contract states what either must preserve.

## Walkthrough

1. Implementer registers a consumer and starts publishing.
2. A record is created, changed and deleted; a catalog revision is accepted.
3. The consumer applies each record by its key.
4. The consumer is stopped and restarted from an earlier position.

## Acceptance Criteria

- [ ] **US-041-AC1** — Given the feed, when changes commit, then each is delivered exactly once in position order and only below the safe watermark.
- [ ] **US-041-AC2** — Given a delete, when it is delivered, then it carries the record as it was.
- [ ] **US-041-AC3** — Given a revision that a change depends on, when the change is delivered, then the revision was delivered first.
- [ ] **US-041-AC4** — Given a restart from an earlier position, when the feed resumes, then it delivers the same records in the same order and applying them again changes nothing.
- [ ] **US-041-AC5** — Given a consumer registered at position P, when retention runs, then no journal partition holding rows past P is dropped.
- [ ] **US-041-AC6** — Given a document in an unsupported UMF version, when the consumer reaches its revision, then it stops and reports it.

## Edge Cases

- **An older open transaction**: later changes are held back until it ends.
- **A position older than the retained journal**: the consumer reports it must re-seed.

## Test Scenarios

| Scenario | AC ID | Input / State | Action | Expected Result |
|----------|-------|---------------|--------|-----------------|
| Once, in order | US-041-AC1 | Commits | Read feed | Each once, ordered |
| Delete | US-041-AC2 | Delete | Read feed | Old record carried |
| Revision first | US-041-AC3 | Revision then change | Read feed | Revision first |
| Replay | US-041-AC4 | Restart | Resume | Same records; idempotent |
| Retention | US-041-AC5 | Consumer at P | Drop partitions | Held back |
| Unsupported | US-041-AC6 | Unsupported version | Reach revision | Stops, reports |

## Dependencies

- **Stories**: US-017
- **Feature Spec**: FEAT-004
- **Feature Requirements**: JNL-07
- **PRD Requirements**: FR-52
- **External**: CONTRACT-006.

## Out of Scope

None.
