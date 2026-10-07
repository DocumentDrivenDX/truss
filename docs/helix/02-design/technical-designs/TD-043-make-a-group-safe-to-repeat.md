---
ddx:
  id: TD-043
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-043
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# TD-043: Request identity and exact replay

## Technical Approach

Admit the head, complete policy owner guards and trusted namespace lifecycle before serializing identical full request identities, then acquire business/root/row locks only for new application under CONTRACT-009. Receipt provisional discovery grants neither disclosure nor final absence; reobserve complete original state/owner closure after the full ordered guards. New earlier scope requires containment/restart. Verify canonical input/digest and retained input integrity, then compare the complete compatible semantic input before either applying once or returning an immutable original ordered result. Equal digest alone cannot establish equality; conflicting complete inputs produce no graph effects or receipt replacement. A caller-supplied hash is a claim to verify, not authority to identify different inputs as equal. Transaction rollback removes all pending replay evidence; uncertain commit requires lookup through the same qualified identity protocol.

## Material Decision Gate

The journal-only design cannot recover mixed no-op result entries, original results after later changes, or all-no-op request identity. US-043 now states complete verified-input replay without selecting persistence, consistent with FR-54. Its longer while-journal-retained replay window still requires explicit reconciliation with ADR-005. D-06 requires a concrete decision between a complete journal receipt envelope and a fixed receipt table, with scope/retention/privilege changes reconciled in governing ADR/contracts/layout. Do not implement a partial replay profile and claim full FR-54. This design defines required behavior while leaving persistence unselected.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/mutation/request.ts` | Versioned exact canonical digest, identity scope and input verification | US-043-AC1, US-043-AC3 |
| `packages/postgresql/src/mutation/replay.ts` | Receipt lookup/persist under lock, atomic ordered results | US-043-AC1, US-043-AC2, US-043-AC4 |
| `packages/postgresql/src/mutation/locks.ts` | Request identity serialization before business locks | US-043-AC2, US-043-AC3 |
| `tests/mutation/replay.test.ts` | Mixed results, concurrent repeats, conflicts and retention | All criteria |

## Interface and Security

The [complete group input wire](../contracts/group-input-v0.1.schema.json) is the exact candidate tree for `truss-canonical/0.1.0` in domain `truss-group-input/0.1.0`; [byte fixtures](../contracts/bindings/group-canonical-v0.1.vectors.json) cover selected equality/difference cases. Preserve every admitted member, optional absence, array order, exact numeric lexical token and asserted origin. No effect-equivalence optimization or unspecified nonsemantic normalization is permitted. Runtime current head/configuration/role, request selection and transport remain outside the semantic tree. These are authored candidates; production canonicalizer and resource/source admission remain unqualified.

[Host namespace authority](../contracts/bindings/truss-request-namespace-v0.1.d.ts) supplies original opaque actual-caller custody, fresh namespace generation and distinct lookup/replay/new permissions. Asserted scope text, matching artifact hashes or a deserialized grant never supply authority. Namespace lifecycle and current owner-policy guards precede request serialization; current authorized replay checks include the complete original owner union. Request-free groups remain independent of replay setup. Empty/ambiguous identities and malformed claimed hashes refuse under the selected identity profile.

Use CONTRACT-009's replay decision order before business planning. Caller-selected pins belong to semantic input; the observed current head belongs to execution context. After catalog advancement, an authorized compatible repeat returns the original result without rerunning old expected-version or endpoint checks. An explicitly changed caller pin conflicts. Incompatible, unauthorized or snapshot-invisible evidence cannot be treated as a missing request eligible for new effects. Do not expose receipt existence across unauthorized scopes.

## Persistence, Retention and Failure

Original results include every operation in input order, aliases/resolved ids, no-op versions and pending/committed durability rules. A committed receipt cannot preserve a stale pending flag as replay durability. Store only after final group validation in the same transaction as effects. On concurrent duplicate, waiter reads committed receipt after winner commit; rollback permits new application. Fixed-snapshot waiter may need a transaction retry to observe winner. Never return partial in-progress results.

At least 24-hour replay must be proven with retention eligibility, not a timestamp label. Journal partition boundaries can split a group's evidence; protect complete receipt dependencies or use an independently retained complete envelope. A complete retained receipt contains immutable full input/result/configuration/owner/definition provenance, with no committed flag. Separate qualified original observation determines replay durability. Compact expired identity yields authorized receipt_expired for equal or changed inputs, never new execution; unavailable original evidence cannot be classified as absence. Namespace rotation requires trusted administrative admission and never caller-selected scope text. [Lifecycle wire](../contracts/request-receipt-lifecycle-v0.1.schema.json) and [protection tooling](../contracts/receipt-protection-tooling-v0.1.schema.json) separate payload expiry, pending compare-and-update and fresh current-committed observation. Time protection begins at actual trusted original committed observation and preserves its original evidence; extension is monotonic and purge rechecks latest protection plus complete event dependencies under serialization. Exact native clock, lifecycle storage/procedure and namespace profiles remain unresolved. Native request-index spike does not qualify mixed no-op recovery.

## Selected Resource Admission

CONTRACT-009 defines the [bounded reference candidate](../contracts/bindings/group-resource-v0.1.candidate.json). Resolve its exact original artifact through the registered group capability profile before invocation; counters/limits are execution admission, never additions to submitted semantic input. Native work/buffer/decoder/cancellation realization needs separate evidence. Complete planning/result/receipt exceeds bounds as a whole; never trim closure or replay results. Exhaustion after pending effects requires confirmed local rollback. Operation deadline and the separate containment-observation allowance cannot grant implicit commit, whole host rollback, pool release or automatic reexecution. Unresolved containment preserves original recovery custody and quarantines handles. A changed current resource profile cannot turn incompatible retained replay into absent/new execution.

## Testing and Handoff

STP-043 allocates four criteria. Resolve D-06 persistence/ADR and select exact native canonical/resource, namespace/authority, receipt/protection/expiry and commit-observation profiles against the authored declarations/wires; author red mixed-result/concurrency/retention tests; implement shared request protocol. Rollback must not erase committed replay evidence or reuse retained ids. Request-free groups remain separately buildable.
