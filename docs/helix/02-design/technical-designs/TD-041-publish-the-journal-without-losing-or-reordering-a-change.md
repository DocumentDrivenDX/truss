---
ddx:
  id: TD-041
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-041
      kind: informed_by
    - id: SD-004
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: CONTRACT-006
      kind: informed_by
---

# TD-041: Ordered resumable change feed

## Technical Approach

Truss exposes a transport-neutral reader and consumer-position protocol, while the host owns delivery and downstream application. Read ordered journal rows strictly below a safe watermark observed in the same consistent snapshot. Emit required catalog revisions before dependent changes. Preserve complete deleted-record envelopes and creation-time source/reservation facts; never reconstruct them from current mutable rows alone.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/feed/read.ts` | Consistent snapshot/watermark, ordered pages and prerequisite revisions | US-041-AC1, US-041-AC3 |
| `packages/core/src/feed/records.ts` | Versioned exact change/delete/revision/source/reservation envelopes | US-041-AC2, US-041-AC6 |
| `packages/postgresql/src/feed/consumers.ts` | Authorized monotonic durable acknowledgment and retention coordination | US-041-AC4, US-041-AC5 |
| `packages/conformance/src/feed/replica.ts` | Independent idempotent downstream fixture | US-041-AC4, US-041-AC6 |

## Delivery and Identity Decisions

CONTRACT-006 distinguishes ordered unique records in one forward scan from at-least-once delivery after restart. US-041-AC1 and CONTRACT-006 now explicitly require at-least-once transport with durable idempotent application; scan uniqueness alone cannot qualify network exactly-once effects. CONTRACT-006 now rejects property-tuple deduplication and proposes sourceEpoch/feedProfile/recordKind/xid/seq for change identity, with same-identity/different-payload corruption refusal. Epoch issuance, sequence nonreuse and exact payload hashing remain design outputs; side-record/checkpoint identity is still unresolved. Do not certify complete replay from change identity alone.

Source/reservation records have no independent journal position in current storage, and revisions may contain no data changes. Their immutable ordering, resume boundaries and acknowledgments therefore need a shared envelope/checkpoint protocol; attaching invented sequence positions is not allowed. Include revision-only acceptance and data transaction split across page limits. A batch must not acknowledge beyond unapplied sibling effects or prerequisite revisions. CONTRACT-006 now blocks unknown required record kinds/semantics; its required-kind profile manifest remains to be specified.

## Retention, Authorization and Recovery

Retain original configuration artifacts separately from catalog prerequisites under CONTRACT-006's proposed fixed configuration-prerequisite store. The finalizer verifies exact epoch/installation/generation/value/profile correspondence and deterministic byte/numeric order; current settings never fill missing original admission. Include configuration dependencies in dirty-generation refresh, protected retention, canonical manifest bytes, fragment resource limits and downstream staging. Qualify the store's ordinary-writer bypass guards independently. Configuration-only administration requires its own explicit replicated profile if advertised; adding a prerequisite is not that event design.

CONTRACT-006 now proposes immutable per-transaction member manifests and ordinal-addressed fragments, preserving native change sequences separately. Consume that candidate before designing page/acknowledgment APIs: missing members, prerequisites or authorization cannot become a complete boundary. Original atomic manifest production and storage are still gated; reader-side counting cannot backfill completeness. Revision-only transactions must have a distinct complete boundary even with no journal change row.

Coordinate acknowledgment/consumer registration with retention under a shared exclusion protocol so a partition cannot disappear between horizon check and read. Validate future positions and monotonic updates under the chosen scope; existing ahead-of-watermark behavior is retained but cannot authorize skipping unacknowledged work. Consumer removal is explicit operator consent with audited consequences. Exact retained horizon/epoch and initial snapshot cut are required; journal gaps cannot be mistaken for empty successful feed. Re-seed snapshot and checkpoint must share a proven consistency boundary.

Global completeness requires an authorized global feed profile; role-filtered feeds need explicit scope/horizon and cannot claim every committed row. Preserve historical module authorization for deleted envelopes. Source assertions remain distinct from trusted journal origin. No credentials or arbitrary host SQL enter envelopes.

## Testing and Handoff

STP-041 allocates six criteria. Finalize envelopes/dedup/checkpoints/revision-only behavior/retention locking and snapshot cut; author red native reader and replica crash tests; implement reader and host-neutral checkpoint surface. No transport service or broker is selected. Disabling a publisher preserves consumer positions and retention protection; never silently remove a slow consumer as rollback. All full-feed support remains gated by D-07, not only watermark correctness.
