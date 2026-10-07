---
ddx:
  id: TD-019
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-019
      kind: informed_by
    - id: SD-004
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
---

# TD-019: Partition-only journal retention

**Story:** [[US-019]]. **Parent:** [[SD-004]]. **Feature:** FEAT-004.

## Technical Approach

Use the fixed RANGE-partitioned journal without a default partition. Host-controlled tooling prepares explicit time ranges ahead of writes. Missing coverage fails the journal write and therefore the entire mutation. Retention removes a whole eligible partition; ordinary application writers cannot edit audit rows. Eligibility must respect protected feed/history/request horizons and CONTRACT-002's complete-group sibling/partition/definition dependency closure before a partition is removed; time range alone does not align with a mutation boundary.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/tooling/src/journal/partitions.ts` | Inventory/preflight explicit nonoverlapping ranges and prospective partition plan | US-019-AC1, US-019-AC4 |
| `packages/tooling/src/journal/retention.ts` | Check protected horizons before explicit whole-partition removal | US-019-AC4 |
| `packages/tooling/src/journal/append-only.ts` | Install/check writer grants and unavoidable row-edit protection | US-019-AC3 |
| `packages/postgresql/src/journal/write.ts` | Propagate missing-partition check violation through atomic rollback, never persist an unaudited mutation | US-019-AC2 |
| `tests/journal/retention.test.ts` | Routing, missing-range rollback, tamper refusal and neighboring partition checks | All criteria |

Runtime tooling is new and outside pure core. No background job is implicitly scheduled by the library.

## API/Interface Design

CONTRACT-002 owns partition/audit behavior; CONTRACT-006 owns feed retention obligations; CONTRACT-008 owns fresh bootstrap inventory. CONTRACT-006 now requires shared administrative serialization for eligibility/drop and consumer lifecycle, with atomic retained-horizon publication. Exact lock/horizon/command schemas remain required before execution. No live schema mutation is performed by this design work.

## Data Model and Integration

Partition boundaries and time zone interpretation are explicit configuration, not inferred from host locale. Verify inclusive/exclusive boundaries and no default partition. Protect the parent and children against UPDATE/DELETE/TRUNCATE by the recognized writer profile; do not assume parent grants alone cover direct child access. DDL administration is separately authorized. Dropping history changes availability, not canonical object state, and must publish the new retained horizon to consumers.

## Security and Performance

Host owns administrative credentials and retention approval. Writer roles cannot detach/drop partitions or remove audit protection. Owner/superuser administrative power must be excluded explicitly from immutable-writer guarantees; the story's recognized-role set needs this distinction resolved in CONTRACT-002. Partition preparation and removal use validated identifiers/ranges and bounded locks. Measure DDL blocking of active writers; no maintenance action bypasses audit on contention.

## Testing

STP-019 owns criteria. Native observations identify actual tableoid partition routing, compare canonical/derived/journal state after missing-range failure, attack parent and child row edits, and digest neighboring partitions before/after removal. Feed acknowledgements and request replay protection receive separate eligibility fixtures once their policies settle.

## Migration and Rollback

Fresh bootstrap installs protection and initial declared ranges. Existing-data maintenance requires its own reviewed procedure. Failed transactional creation/drop leaves inventory intact. Successfully dropped history cannot be undone by recreating an empty partition: restoration requires archived evidence and an explicit recovery process. Never describe destructive retention as reversibly restoring prior history.

## Implementation Sequence

1. Define recognized writer/admin roles and protected retention horizon contract.
2. Add red native boundary/tamper/missing-partition tests.
3. Implement inventory/planning and protection; execute only against disposable targets for qualification.
4. Qualify eligible partition removal, neighbor integrity and consumer horizon reporting.

## Risks and Gates

CONTRACT-002 recommends append-only protection while US-019-AC3 requires refusal; reconcile the mandatory qualified profile before implementation. D-06 replay and D-07 history/feed horizons may forbid an otherwise old partition drop. Clock/timezone mistakes can strand writes. Admin owner powers cannot be hidden behind an absolute all-role guarantee.
