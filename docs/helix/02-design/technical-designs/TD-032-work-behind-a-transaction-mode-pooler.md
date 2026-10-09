---
ddx:
  id: TD-032
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-032
      kind: informed_by
    - id: SD-008
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# TD-032: Transaction-mode pooling

## Technical Approach

Every operation uses one connection-affine transaction handle under CONTRACT-007. Acquire/release at transaction boundaries; never retain role, origin, catalog snapshot or a prepared-statement name as correctness-critical session state. Caller adoption preserves host ownership and does not release its connection. Parameterized unprepared execution remains a first-class mode.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/adapter-bun/src/executor.ts` (planned Bun), existing `packages/pg-runtime/src/index.ts` and original transport modules (Node/pg) | Affine execution and explicit prepared/unprepared capability | US-032-AC1, US-032-AC2 |
| `tests/host/pooler.test.ts` | Real pooler corpus and context-leak probes | US-032-AC1, US-032-AC2 |
| `tests/performance/unprepared.test.ts` | Paired 1,000-type point-read measurement | US-032-AC3 |

## API and Data Model

Execution profile reports selected preparation mode and exact adapter/server/pooler versions. Prepared mode requires explicit pooler/driver capability; unsupported combinations refuse or select a declared unprepared profile before execution. Disabling preparation must not interpolate values. No canonical DDL changes. Driver-managed unnamed parameterized statements must be distinguished from persistent named preparation in profile documentation.

## Security and Failure Handling

Transaction-local roles and origin are observed through native tests, including commit, rollback, cancellation and failed savepoint cleanup. Poisoned connections are discarded according to adapter ownership. No automatic replay after uncertain commit. Rotate physical backends between transactions and test reuse by a different principal; a stable backend during one transaction is mandatory. Host-owned prepared/cache/session settings are host obligations, not implicit Truss assumptions.

## Testing and Performance

STP-032 allocates all three criteria. Run the selected corpus through an actual transaction-mode pooler in both modes and compare independently expected results, not only prepared/unprepared agreement. Measure incremental point-read cost using matched plans, dataset, role, server, pooler, warmup and randomized paired samples. The story's 0.05 ms limit needs an agreed statistic and environment before acceptance; the historical spike does not establish end-to-end network/pooler cost.

## Sequence, Rollback and Gates

Finalize capability/profile and measurement protocol; write red native pooling tests; qualify/extend the existing Node/pg bridge and separately implement the selected Bun adapter; run correctness before performance. Disable an unqualified prepared profile without changing stored data. Pooler product/version/configuration, complete selected corpus manifest, timing statistic and target matrix remain unresolved. No direct-server or mocked-driver result qualifies pooling.

The executor handoff E01 in the implementation plan now requires original host transaction/generation recognition and one custody entry shared by compatible wrappers. CONTRACT-007 supplies adoption reservation, post-observation recheck, duplicate refusal, per-entry execution/containment serialization and unresolved retention. Exact driver recognition and host-side exclusion mechanism remain selected native profile outputs. Backend PID or adapter-only mutex is insufficient; pooling cannot rebind an old handle to a later transaction.


## Existing driver ownership

Consume [the package delivery boundary](../package-delivery.proposal.md): Node/pg uses the existing experimental pg-runtime `createPgConnectionSource` bridge, not a second adapter-pg package. Its original command-cycle, raw-cell, termination and transaction-custody procedures are the starting implementation; pooling requires its own exact driver/pooler/build/configuration and original backend-affinity evidence. Existing direct-server component passes cannot transfer to transaction-mode pooling. Other-agent driver/security changes remain independently owned and are not adopted by this source reconciliation. The proposed Bun adapter requires its own original producer evidence; common interface shape cannot qualify either driver or permit replacing a caller-owned connection.
