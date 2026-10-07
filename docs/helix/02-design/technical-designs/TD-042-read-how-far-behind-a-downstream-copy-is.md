---
ddx:
  id: TD-042
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-042
      kind: informed_by
    - id: SD-004
      kind: informed_by
    - id: CONTRACT-006
      kind: informed_by
---

# TD-042: Consumer freshness evidence

## Technical Approach

Expose consumer checkpoint/update time and a same-snapshot assessment of unapplied journal rows. Publishable lag is the age of the earliest unapplied row below the safe watermark, not the age of the consumer heartbeat or newest source write. Report committed rows held above the watermark separately. A statement cannot see uncommitted rows; do not claim to count their eventual changes. Host transport owns durable downstream application and its statement of reflected position.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/feed/consumers.ts` | Authorized monotonic applied checkpoint and update time | US-042-AC1 |
| `packages/postgresql/src/feed/freshness.ts` | Consistent watermark/backlog/held assessment | US-042-AC2, US-042-AC3 |
| `packages/core/src/feed/freshness.ts` | Exact versioned freshness envelope and reflected-position descriptor | US-042-AC2, US-042-AC3, US-042-AC4 |
| `tests/feed/freshness.test.ts` | Native snapshot, timing and checkpoint evidence | All criteria |

## Interface and Semantics

CONTRACT-006 now defines present/empty/unavailable publishable-backlog semantics, separate held backlog and observation-clock failure. Empty with zero lag is qualified scoped absence, not a global catch-up claim. Encode those states as a discriminated envelope; do not overload a null oldest timestamp for authorization, missing history and genuine emptiness.

Shared envelope must include consumer identity, feed scope/epoch, durable position, checkpoint updated_at, observed_at, safe watermark, publishable oldest_at/age and separately held oldest_at/count where qualified. Final field names/types and exact duration encoding belong in CONTRACT-006 before implementation. No consumer means no lag record. No publishable unapplied rows yields zero lag under the story, with explicit absence of oldest_at; ahead-of-watermark checkpoint does not imply source completeness. Retained-gap/unknown-consumer states must be errors or explicit unavailable states, never zero freshness.

Use server observation time consistently. now() is transaction-start time and can be stale in an adopted long transaction; choose a qualified observation-clock expression and one snapshot rather than silently returning negative/stale ages. Source at is write time, not commit time or delivery time. Same snapshot sees checkpoint, rows and watermark; separately queried values can describe an impossible state. No floating-point duration conversion.

## Security and Integration

Only authorized consumer owner/operator advances its checkpoint after durable apply. Acknowledgment and updated_at move atomically; define equal/reverse/future-position behavior and coupling to downstream transaction under the shared checkpoint gate. Readable freshness must respect scope/disclosure policy: global oldest timestamps/counts can reveal hidden activity. Role-filtered observations cannot assert global completeness. Revision-only/source/reservation lag requires the full envelope/checkpoint resolution from TD-041; journal-only lag is explicitly scoped.

## Testing and Handoff

STP-042 allocates four criteria. Finalize envelope/clock/scope and checkpoint authority; implement red snapshot/held/advance tests; reuse consumer protocol and qualify native queries. Independent observer verifies timestamps and positions; long-open transaction plus later committed row exercises held reporting. Copy freshness statements carry actual durable position, not source head or last attempted batch. Disabling publisher preserves positions; never synthesize catch-up acknowledgment.
