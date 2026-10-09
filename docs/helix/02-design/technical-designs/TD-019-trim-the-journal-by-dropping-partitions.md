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

CONTRACT-002 owns partition/audit behavior; CONTRACT-006 owns feed retention obligations; CONTRACT-008 owns fresh bootstrap inventory. CONTRACT-006 now requires shared administrative serialization for eligibility/drop and consumer lifecycle, with atomic retained-horizon publication. Consume the existing [retention tooling declaration](../contracts/bindings/truss-retention-tooling-v0.1.d.ts): exact original candidate inventory, expected retained horizon and registered procedure profile enter an explicitly adopted transaction; successful removal is pending until independently confirmed original settlement. Select actual administrative exclusion, native horizon/eligibility producers and complete artifact grammars before execution. A shape-valid request or retained observation is not a reusable drop permit. No live schema mutation is performed by this design work.

## Data Model and Integration

Partition boundaries and time zone interpretation are explicit configuration, not inferred from host locale. Verify inclusive/exclusive boundaries and no default partition. Protect the parent and children against UPDATE/DELETE/TRUNCATE by the recognized writer profile; do not assume parent grants alone cover direct child access. DDL administration is separately authorized. Dropping history changes availability, not canonical object state, and must publish the new retained horizon to consumers.

## Security and Performance

Host owns administrative credentials and retention approval. Writer roles cannot detach/drop partitions or remove audit protection. Owner/superuser administrative power must be excluded explicitly from immutable-writer guarantees; the selected security-owned principal/privilege inventory must identify every admitted recognized writer route and demonstrate mandatory row-edit refusal there. Do not reinterpret trigger recommendation as permission for an admitted writer to edit history, or claim protection against arbitrary privileged DDL from ordinary-writer tests. Partition preparation and removal use validated identifiers/ranges and bounded locks. Measure DDL blocking of active writers; no maintenance action bypasses audit on contention.

## Testing

STP-019 owns criteria. Native observations identify actual tableoid partition routing, compare canonical/derived/journal state after missing-range failure, attack parent and child row edits, and digest neighboring partitions before/after removal. Consume the authored complete-feed acknowledgment and durable request-receipt protection protocols in separate eligibility fixtures. Qualified archive handoff and short/zero local-window controls in STP-019 preserve full original dependency closure; no new retention policy choice is implied by unfinished native producers.

## Migration and Rollback

Fresh bootstrap installs protection and initial declared ranges. Existing-data maintenance requires its own reviewed procedure. Failed transactional creation/drop leaves inventory intact. Successfully dropped history cannot be undone by recreating an empty partition: restoration requires archived evidence and an explicit recovery process. Never describe destructive retention as reversibly restoring prior history.

## Implementation Sequence

1. Bind the security-owned recognized writer/admin inventory and existing protected retention/horizon protocol to exact original installation, procedure, resource and authority profiles.
2. Add red native boundary/tamper/missing-partition tests.
3. Implement inventory/planning and protection; execute only against disposable targets for qualification.
4. Qualify eligible partition removal, neighbor integrity and consumer horizon reporting.

## Risks and Gates

CONTRACT-002 mandates append-only behavior and recommends a refusing trigger as one realization. US-019-AC3 requires actual refusal through every admitted recognized writer path; no additional product choice between mandatory behavior and optional behavior remains. Select and qualify the actual mechanism, including parent/child access, helper privileges, replication/trigger state and installed drift observation, before advertising support. D-06 replay and D-07 history/feed horizons may forbid an otherwise old partition drop. Clock/timezone mistakes can strand writes. Admin owner powers cannot be hidden behind an absolute all-role guarantee.
