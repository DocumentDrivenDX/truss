---
ddx:
  id: TD-014
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-014
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# TD-014: Keep cross-row rules honest

**Story:** [[US-014]]. **Parent:** [[SD-003]]. **Feature:** FEAT-003.

## Technical Approach

Inherit parent-lock validation and final group-state checking from CONTRACT-004/009. Every participating edge removal obtains the same parent lock before counting. At READ COMMITTED, read current committed participation after lock acquisition, combine planned effects and validate the final state. Never count from a stale pre-lock snapshot and then apply effects under the lock. Engine-only lock checks remain explicitly engine enforcement.

Deferred trigger existence alone does not establish database enforcement. Reports combine rule/profile identity, mandatory execution path and qualified evidence, preserving unsupported/unverified distinctions. A SERIALIZABLE variant needs its own transaction-wide retry and native evidence before classification changes.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/core/src/mutations/participation.ts` | Final-state minimum and aggregate rule validation | US-014-AC1 |
| `packages/postgresql/src/mutations/participation.ts` | Complete parent lock set, post-lock reads and stale-plan revalidation | US-014-AC1 |
| `packages/core/src/reports/enforcement.ts` | Evidence/path-aware classification without trigger-name inference | US-014-AC2, US-014-AC3 |
| `tests/mutations/cross-row.test.ts`, `tests/reports/enforcement.test.ts` | Forced concurrency, bypass and independent classification expectations | All criteria |

These are new components. Pure validators/reports have no database imports.

## API/Interface Design

CONTRACT-004 owns cross-row checks/reports; CONTRACT-009 owns lock order and simulation; CONTRACT-007 owns transaction/retry scope. Extend the shared report evidence schema before publication if needed; this story does not invent an independent guarantee vocabulary.

## Data Model and Integration

No new tables. Minimum participation is derived from accepted catalog rules and canonical edge state under the relevant parent lock. Both endpoint orientations and inverse presentation map to the authored rule identity. Group replacement may remove then add an edge if final participation is valid. Arbitrary aggregate predicates require a complete declared lock scope; unsupported scope refuses rather than relying on an accidental parent lock.

## Security and Performance

Authenticated host role determines visibility. Validation must not undercount hidden participating edges: rule checking needs a qualified authorized integrity path without leaking hidden rows in diagnostics. Lock acquisition follows the global hierarchy; measure contention separately from pure validation. No broad aggregate safety claim follows from this bounded relationship rule.

## Testing

STP-014 allocates the three criteria. Two clients start with two lines and concurrently remove one each; barriers prove contention and final count remains at least one. Raw SQL demonstrates the engine-only boundary. A trigger-only fixture is not relabeled database enforcement, regardless of one sequential successful run. Report expectations are independently authored.

## Migration and Rollback

No layout migration. Failed validation rolls back call effects/journal; caller earlier work remains only when its transaction is usable. A tightened minimum requires catalog acceptance validation of existing state. Withdrawing the qualified engine path withdraws its guarantee; do not preserve an obsolete report claim after disabling enforcement.

## Implementation Sequence

1. Create red forced-race and report-classification cases.
2. Implement final-state validator and post-lock native participation reads.
3. Wire qualified evidence/path classification and raw-bypass observations.
4. Review lock scope for each selected rule family before advertising support.

## Risks and Gates

Role visibility and integrity-check authority need explicit shared policy. REPEATABLE READ/SERIALIZABLE behavior requires fresh-snapshot/conflict qualification rather than extrapolation from READ COMMITTED. Report schema must distinguish tested database enforcement, tested engine enforcement and unverified paths. General aggregate invariants remain gated on complete lock-set design.
