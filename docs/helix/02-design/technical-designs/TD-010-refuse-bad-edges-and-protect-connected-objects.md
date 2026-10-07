---
ddx:
  id: TD-010
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-010
      kind: informed_by
    - id: SD-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
---

# TD-010: Refuse bad edges and protect connected objects

**Story:** [[US-010]]. **Parent:** [[SD-002]]. **Feature:** FEAT-002.

## Technical Approach

Use CONTRACT-001's typed relationship endpoint constraints and restrictive object foreign keys as the unavoidable integrity boundary. Engine validation provides diagnostics but cannot replace native rejection. Edge creation binds relationship identity and both typed endpoint identities; caller-supplied discriminator values cannot evade the referenced catalog tuple. Deleting edges before an unowned object releases the native protection. Owned composition deletion remains a separate planned engine operation under CONTRACT-009.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/edges/write.ts` | Parameterized typed endpoint insert and constraint-to-domain error mapping | US-010-AC1, US-010-AC2 |
| `packages/postgresql/src/objects/delete.ts` | Restrictive delete; preserve host transaction on statement refusal through the call savepoint | US-010-AC3, US-010-AC4 |
| `tests/edges/integrity.test.ts` | Native engine and plain-SQL attacks, cleanup and forced races | All criteria |

No runtime components currently exist. Fixed constraints are installed by qualified bootstrap, not dynamically per type.

## API/Interface Design

CONTRACT-001 owns endpoint constraints and error mapping; CONTRACT-004 owns mutations; CONTRACT-007 owns savepoint/error durability; CONTRACT-009 owns shared lock planning. No new shared API is defined by this story.

## Data Model and Integration

No DDL beyond the fixed layout. Catalog acceptance populates allowed relationship endpoint tuples atomically. Actual object type must match its typed identity; tests forge endpoint discriminator combinations rather than merely call the engine with an obviously invalid type. Native object deletion must protect both source and target references, including self-edges. Journal mode changes cannot weaken endpoint integrity.

## Security and Performance

The ordinary writer principal must lack privileges to disable constraints or alter the catalog. Superuser/owner destructive administration is outside the writer guarantee and must not be used as the qualification principal. Parameterize values and apply acting-role policy. Record native plans/lock waits; retain the fixed endpoint indexes. Concurrency tests use explicit barriers and real clients, not mocked locks.

## Testing

STP-010 allocates the criteria. Supplement with wrong source, wrong target, nonexistent source/target, forged type discriminator, self-edge, both endpoint deletion directions and racing insert/delete. Observe committed state independently: no dangling edge can survive either outcome. Refused caller-owned operations roll back the call savepoint without erasing prior host work.

## Migration and Rollback

No schema migration. Constraint failures leave prior rows and journals unchanged. If installed constraints differ from the qualified inventory, refuse readiness rather than patch a live namespace. Engine deletes can be disabled while native integrity remains. Composition changes require their own governed design and cannot convert restrictive FKs to cascading deletes implicitly.

## Implementation Sequence

1. Add native bypass tests against the independent bootstrap baseline and generated candidate.
2. Implement endpoint insertion/error mapping and restrictive deletion using the executor.
3. Verify caller savepoint preservation and forced insert/delete races on each claimed target.

## Risks and Gates

Bootstrap native parity is a prerequisite. Cross-document endpoint meaning remains gated by UMF's versioned relationship support and D-04. Relationship variants not representable by current typed tuples refuse explicitly. Unique endpoint-pair restrictions are not a license to collapse parallel association instances. This story qualifies endpoint integrity, not cardinality, lifecycle or full model enforcement.
