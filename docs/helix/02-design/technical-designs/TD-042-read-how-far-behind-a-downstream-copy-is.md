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

Expose confirmed source checkpoint/update time and a coherent assessment of complete retained unapplied producer transactions across the required feed fact kinds. Publishable lag is the age of the earliest qualified unapplied fact in transactions strictly below the exclusive safe watermark, not the age of the consumer heartbeat or newest source write. Report complete committed transactions at or above the watermark separately as held. A statement cannot see uncommitted rows; do not claim to count their eventual changes. Host transport owns durable downstream application and its statement of reflected position.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/feed/consumers.ts` | Authorized monotonic applied checkpoint and update time | US-042-AC1 |
| `packages/postgresql/src/feed/freshness.ts` | Consistent watermark/backlog/held assessment | US-042-AC2, US-042-AC3 |
| `packages/core/src/feed/freshness.ts` | Exact versioned freshness envelope and reflected-position descriptor | US-042-AC2, US-042-AC3, US-042-AC4 |
| `tests/feed/freshness.test.ts` | Native snapshot, timing and checkpoint evidence | All criteria |

## Interface and Semantics

CONTRACT-006 now defines present/empty/unavailable publishable-backlog semantics, separate held backlog and observation-clock failure. Empty with zero lag is qualified scoped absence, not a global catch-up claim. Encode those states as a discriminated envelope; do not overload a null oldest timestamp for authorization, missing history and genuine emptiness.

Use CONTRACT-006’s [complete freshness v0.2 wire](../contracts/complete-feed-freshness-v0.2.schema.json) and CompleteFeedFreshnessRequestV02/ResultV02 in the [existing declaration](../contracts/bindings/truss-feed-key-transition-v0.2.d.ts). They already select serialization fields and exact backlog states; do not invent a parallel envelope or downgrade to the historical v0.1 declaration. Remaining clock text/range, native coherent observation and original profile admission are implementation prerequisites, rather than missing wire design. No consumer means no lag record. Qualified empty publishable backlog has zero age and no oldest fact time; retained gaps, missing original timing, unavailable authority and incompatible observations cannot become empty. An ahead confirmed source boundary can be retained only in a qualified observed envelope with affected backlog unavailable; failed scope admission exposes no boundary/time.

Use server observation time consistently. now() is transaction-start time and can be stale in an adopted long transaction; choose a qualified observation-clock expression and one snapshot rather than silently returning negative/stale ages. Source at is write time, not commit time or delivery time. Same snapshot sees checkpoint, rows and watermark; separately queried values can describe an impossible state. No floating-point duration conversion.

## Security and Integration

Only authorized consumer owner/operator advances its checkpoint after durable apply. Acknowledgment and updated_at move atomically; define equal/reverse/future-position behavior and coupling to downstream transaction under the shared checkpoint gate. Readable freshness must respect scope/disclosure policy: global oldest timestamps/counts can reveal hidden activity. Role-filtered observations cannot assert global completeness. Revision-only/source/reservation changes contribute their original retained fact times through the complete membership/classifier protocol in CONTRACT-006 and TD-041. A journal-only implementation remains explicitly partial and cannot satisfy complete-feed freshness. Confirmed source acknowledgment is distinct from possibly ahead durable downstream application; pending acknowledgment visible in an adopted transaction cannot become confirmed progress.

## Testing and Handoff

STP-042 allocates four criteria. Reuse the existing versioned envelope and finalize exact native clock/snapshot/authority producers; implement red snapshot/held/advance tests; reuse consumer protocol and qualify native queries. Independent observer verifies timestamps and positions; long-open transaction plus later committed row exercises held reporting. Copy freshness statements carry actual durable position, not source head or last attempted batch. Disabling publisher preserves positions; never synthesize catch-up acknowledgment.
