---
ddx:
  id: TD-017
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-017
      kind: informed_by
    - id: SD-004
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
---

# TD-017: Safe incremental journal reads

**Story:** [[US-017]]. **Parent:** [[SD-004]]. **Feature:** FEAT-004.

## Technical Approach

Use CONTRACT-002's snapshot minimum and ordered `(xid,seq)` position. Select only rows below the safe transaction boundary in the same qualified read snapshot. Sequence/time order alone is forbidden. An older open transaction delays publication of later committed rows; once it finishes, ordering remains transaction-assignment order rather than commit order.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/journal/read.ts` | Snapshot-bound safe selection and complete ordered position comparison | US-017-AC1, US-017-AC2, US-017-AC3 |
| `packages/core/src/journal/position.ts` | Exact position parsing/comparison without host-number coercion | US-017-AC3 |
| `tests/journal/watermark.test.ts` | Explicit late-commit and ahead-position interleavings | All criteria |

All runtime components are new. Core position handling remains I/O-free.

## API/Interface Design

CONTRACT-002 owns safe boundary and position; CONTRACT-006 owns feed delivery and transaction completeness; CONTRACT-007 owns read context. Do not create an incompatible cursor or infer snapshot stability across calls. Public pagination must use the complete position, not just xid or seq.

## Data Model and Integration

No DDL. Read exact native xid/seq text and retain both components. Multiple events in one transaction preserve sequence order and continuation. CONTRACT-002 row pages may split a mutation version or host transaction and certify only the complete bounded eligible row page under their admitted context. They do not certify a completed mutation, reconstruction or feed transaction. CONTRACT-006 separately accumulates and validates its complete transaction/fact inventory before application or acknowledgment; do not force its batching semantics into the raw journal cursor. Retention and restored-database cursor identity remain shared gates: a stale cursor must not be interpreted as proof that missing history never existed.

## Security and Performance

Apply qualified role visibility to journal records without treating filtered rows as global feed completeness. Host controls publication/acknowledgement. Parameterize position bounds; reject malformed/out-of-profile positions. Measure lag from oldest open transaction and explain it in diagnostics; do not bypass the watermark to improve apparent freshness. Query/index evidence is qualified per native server and journal layout.

## Testing

STP-017 owns criteria. Force A's xid assignment before B, commit B while A remains open, and inspect returned rows/boundary. After A commits, independently expected ordering contains both without gaps. Test A rollback too: B becomes eligible without a phantom A row. Exact position comparison includes several events per xid and large values beyond host-double precision.

## Migration and Rollback

No layout migration. Keep cursors tied to qualified database/feed identity. An incompatible position version refuses rather than converting to sequence-only order. Read failure advances no durable host acknowledgement. Retention gaps require explicit recovery, not silent cursor jump.

## Implementation Sequence

1. Add red native late-commit/rollback and ahead-position fixtures with observed xid order.
2. Implement exact position codec and same-snapshot safe selection.
3. Implement the authored CONTRACT-002 page/context/retention admission, preserving fragment semantics; separately integrate CONTRACT-006 completeness before feed acknowledgment.
4. Qualify native target/isolation/role matrix and document long-transaction lag.

## Risks and Gates

Snapshot watermark proof is native-version qualified; parser/unit evidence cannot prove it. Wraparound/restoration/retention and global versus role-filtered completeness need explicit feed profile semantics. Long-running transactions intentionally delay progress. This story does not assert commit-time order or exactly-once downstream application.

### Complete-profile fragment controls

Reserved-position allocation, if adopted, does not change xid watermark or exclusive cursor meaning. Numeric sequence gaps are allowed and cannot prove a missing event; the independent complete mutation manifest establishes sibling membership. A page ending after one property event may precede a later property or metadata witness of the same version. Return its exact admitted continuation without promoting that prefix to a reconstructed version or completed feed transaction. Unknown required event meaning refuses under the selected decoder rather than being skipped to advance the cursor. These rules do not resolve the pending US-015 total-row interpretation.
