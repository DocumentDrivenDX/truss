---
ddx:
  id: TD-044
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-044
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# TD-044: Caller-owned transaction adoption

## Technical Approach

Adopt an active host transaction on its original connection. Execute each operation/group inside a Truss savepoint and return pending durability after release. Host retains commit/rollback and connection lifetime. Reads on that transaction see pending effects; another connection cannot observe them as committed. CONTRACT-007 is the sole execution authority; adapters must not invent their own transaction semantics.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/adapter-bun/src/transaction.ts`, `packages/adapter-pg/src/transaction.ts` | Active affine handle adoption and lifetime validation | US-044-AC1, US-044-AC4 |
| `packages/postgresql/src/mutation/scope.ts` | Savepoint containment, pending result and context restoration | US-044-AC1, US-044-AC2, US-044-AC3, US-044-AC4 |
| `tests/host/caller-transaction.test.ts` | Native host sentinel, rollback/commit and lifetime proofs | All criteria |

## Interface and Lifetime

Adopt asynchronously under the draft execution binding, verifying expected isolation/accessMode against actual connection-affine native state. Do not SET either property, begin a replacement transaction or clean up host failure implicitly. Concurrent host termination during verification invalidates adoption. A pre-established snapshot remains unchanged; ordinary observation may naturally establish the first snapshot when none exists, with no fabricated earlier-cut claim. STP-044 owns mismatch/failure/read-only and pooler proof.

Reject inactive/completed, cross-adapter or ambiguous concurrent use. Never issue whole-transaction BEGIN/COMMIT/ROLLBACK on an adopted handle, release its connection, change isolation or retry the host callback. Generated savepoint identifiers are trusted internal names. Role belongs to host context; origin is restored at call boundary. Several successful calls may share one host transaction and still have distinct per-call origins. Catalog/row locks survive savepoint release until transaction end.

## Failure and Rollback

Ordinary operation failure rolls back its savepoint and preserves earlier host work. Failed cleanup, connection loss or transaction-fatal state returns transaction_unusable and requires host rollback/discard. Serialization/deadlock retries restart the whole host transaction at host discretion. Sequence allocations are not rolled back; distinguish allowed id gaps from surviving records. Commit-unknown is a host durability problem, never a successful pending result promoted by Truss without evidence.

Native rollback removes canonical/derived/journal/tombstone/source and selected request evidence; no transaction-scoped advisory/catalog/row lock remains after end. Test lock release with a waiting independent transaction, not only absence of visible rows. Commit produces exactly one qualified journal owner and same graph effects as engine-owned execution. Pending results are never labelled committed before host commit.

## Testing, Sequence and Gates

STP-044 allocates four criteria. Finalize adapter adoption API/liveness/cancellation; write red native host sentinel tests; implement shared scopes and each adapter; qualify real connections and advertised pooler profiles. Receipt assertions depend on D-06 selected persistence but other rollback forms remain independently testable. Disabling library code does not end the host transaction or discard pending work without host action. All runtime files/tests remain planned.
