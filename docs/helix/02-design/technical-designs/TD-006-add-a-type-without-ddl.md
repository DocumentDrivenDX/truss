---
ddx:
  id: TD-006
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-006
      kind: informed_by
    - id: SD-001
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
---

# TD-006: Catalog-only type addition

## Technical Approach

Insert type/property/relationship/endpoint catalog rows into the fixed layout under head exclusion. No per-type table, column, partition, constraint or index is created. Optional binding indexes are separately declared postcommit jobs with pending readiness. Do not confuse absence of DDL with zero writer delay: acceptance intentionally waits on and holds the catalog head lock.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/catalog/derive.ts` | Fixed-table catalog inserts only | US-006-AC1 |
| `packages/postgresql/src/catalog/accept.ts` | Head exclusion and bounded acceptance work | US-006-AC2, US-006-AC3 |
| `tests/catalog/no-ddl.test.ts` | Independent physical inventory and native DDL trace | US-006-AC1 |
| `tests/concurrency/catalog-writers.test.ts` | Sixteen-writer acceptance barriers and outcomes | US-006-AC2 |
| `tests/performance/catalog-scale.test.ts` | Matched 10/1,000-type acceptance measurement | US-006-AC3 |

## Interfaces and Evidence

CONTRACT-003 owns acceptance/phases and pending indexes. Reuse bootstrap native inventory comparator rather than checking table count alone. Compare tables, columns, constraints, indexes, partitions and functions, with command tracing or independently observed catalog changes to detect temporary DDL that net inventory could hide. Use a no-index-binding fixture for AC1; explicit postcommit index jobs are a separate named exception, never hidden during acceptance.

Sixteen writers use current revision observation before shared-head acquisition under the admission protocol. Acceptance can otherwise make stale callers retry; AC2's none-fails requirement must distinguish successful admitted continuous workloads from deliberate stale-revision refusal. Define harness workload/retry and completed-operation reporting transparently; retries must not be erased from raw evidence. No claim that unrelated host locks or bypass writers avoid delays.

## Performance and Gates

Same-order-of-time needs a predeclared ratio/statistic/environment; it cannot be asserted from noisy comparable medians after the fact. Hold candidate size and instance data fixed while varying preexisting type count, measure validation/derivation/head wait separately and preserve plans/samples. A populated new key or total transform is data-proportional work, not the simple type-addition benchmark. Full immutable report enumeration may itself scale with catalog size; include it in end-to-end timing.

## Testing, Sequence and Rollback

STP-006 allocates three criteria. Finalize benchmark and admission/no-failure interpretation; write red inventory/writer/scale tests; implement fixed-table derivation and qualify native locks. Failed revision rolls back catalog/head; no DDL repair migration. Postcommit index job failure leaves explicit pending readiness and cannot retroactively masquerade as rejected acceptance. All runtime components/tests remain planned.
