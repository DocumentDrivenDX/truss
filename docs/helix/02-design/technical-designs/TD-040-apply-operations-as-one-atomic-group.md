---
ddx:
  id: TD-040
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-040
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# TD-040: Atomic ordered groups

## Technical Approach

Use one shared planner for groups and single writes. CONTRACT-009 owns whole-input discovery, identity reservation, sorted strongest-first locks, post-lock revalidation and ordered simulation. CONTRACT-007 owns caller/engine transaction lifetime and savepoint containment. Persist only a fully validated plan; return results in input order regardless of lock/persistence order. Request-free atomicity does not depend on the unresolved request-receipt decision.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/mutation/group.ts` | Alias validation, ordered simulation/results and operation-index errors | US-040-AC1, US-040-AC2 |
| `packages/postgresql/src/mutation/plan.ts` | Full closure/key/root discovery and post-lock revalidation | US-040-AC2, US-040-AC3 |
| `packages/postgresql/src/mutation/locks.ts` | Shared versioned hierarchy and strongest mode before effects | US-040-AC3, US-040-AC4 |
| `packages/postgresql/src/mutation/apply.ts` | One savepoint/origin/journal owner and durability envelope | US-040-AC1, US-040-AC2, US-040-AC4 |

## Catalog Race Semantics

US-040-AC4 now states both legal schedules. Acceptance cannot commit after the group holds its catalog share lock: acceptance waits until the group/caller transaction ends. Test both legal schedules. If acceptance wins before the group acquires the lock, an old expected revision refuses before effects. If the group wins, its old revision is valid until commit and acceptance proceeds afterward. Do not invent a last-minute unlocked head check or imply acceptance bypasses the share lock. This refines stale-revision protection without changing catalog lock ownership.

## Validation, Security and Persistence

Immediate field/type/version rules apply per operation; cross-row participation validates final simulated state. A final invariant names the last affecting operation and preserves all paths. Native deferred guards or qualified persistence ordering must enforce the valid final state without publishing an invalid committed graph. Alias references are typed and backward-only; empty/duplicate/forward aliases fail. Exact ordered no-op results remain present without version/journal mutation. Actual effective-role predicates constrain every operation; simulation cannot grant hidden endpoint authority.

The selected lock plan follows CONTRACT-009: head, complete current-authority policy guards, trusted namespace guards when request-bearing, request identity, complete old/new business keys, roots, other objects, edges, then derived effects. Request-free groups omit namespace/request levels without omitting current-authority admission. Complete owner/key/root discovery is provisional until fresh post-lock revalidation; new earlier owners, namespaces, buckets or roots cause contained retry rather than growing an earlier lock level after lower acquisition. Advisory and protected native bucket profiles require separate identities, snapshot and unavoidable-writer procedures. Reserve new ids before effects; rollback permits gaps. Arbitrary earlier host locks and external triggers are outside the constrained no-deadlock proof and may yield retry. Owned-deletion, mixed key changes and group/single-write overlap remain required forms, not silently refused shortcuts.

## Selected Resource Admission

CONTRACT-009 defines the [bounded reference candidate](../contracts/bindings/group-resource-v0.1.candidate.json). Resolve its exact original artifact through the registered group capability profile before invocation; counters/limits are execution admission, never additions to submitted semantic input. Native work/buffer/decoder/cancellation realization needs separate evidence. Complete planning/result/receipt exceeds bounds as a whole; never trim closure or replay results. Exhaustion after pending effects requires confirmed local rollback. Operation deadline and the separate containment-observation allowance cannot grant implicit commit, whole host rollback, pool release or automatic reexecution. Unresolved containment preserves original recovery custody and quarantines handles. A changed current resource profile cannot turn incompatible retained replay into absent/new execution.

## Testing and Handoff

STP-040 allocates four criteria with native barriers. Complete [group input](../contracts/group-input-v0.1.schema.json), [result](../contracts/group-result-v0.1.schema.json) and [facade](../contracts/bindings/truss-group-capability-v0.1.d.ts) candidates exist; wire/type evidence does not establish plan correctness. Remaining implementation prerequisites are selected native lock identity/modes and writer coverage, bounded complete closure/simulation, final-invariant realization, adapter rollback/retry and current-authority procedures. Write red native tests before implementing the shared planner and executor; test both catalog-race schedules above. Caller rollback removes pending group effects; failed cleanup marks transaction unusable. Disabling group code changes no stored layout; incompatible lock profiles cannot coexist unnoticed. All runtime files/tests remain planned.
