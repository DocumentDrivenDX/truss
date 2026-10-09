---
ddx:
  id: STP-006
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-006
      kind: informed_by
    - id: TD-006
      kind: informed_by
    - id: SD-001
      kind: informed_by
---

# STP-006: Type addition without DDL

## Story Reference and Scope

US-006, TD-006, SD-001, TP-001 and CONTRACT-003. Tests are planned. Fixed physical inventory, actual writer overlap and predeclared scaling protocol are independent proof dimensions.

## Acceptance Criteria Test Mapping

Separate postcommit readiness probes under CONTRACT-003: pending caller acceptance never dispatches; confirmed commit permits one fenced job attempt; exact acceptance repeat does not redispatch. Same index name/different definition refuses. Failure/cancellation preserves committed acceptance and records actual inventory/cleanup outcome; only matching valid native inventory yields ready. Drift produces stale qualification. Optional optimization failure cannot change correctness; any required path must check readiness or use a separately qualified fallback. These are planned job-profile cases, not evidence of acceptance-time DDL.

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-006-AC1 | `type_property_relationship_addition_has_no_ddl` | Complete physical inventory identical and trace contains no transient per-type DDL; catalog rows added correctly | `@covers US-006-AC1` | Native integration | `tests/catalog/no-ddl.test.ts`; no-index-binding fixture |
| US-006-AC2 | `sixteen_continuous_writers_only_wait_on_head` | Admitted workload completes without failure; observed acceptance overlap shows catalog-head wait and preserves every write | `@covers US-006-AC2` | Native concurrency | `tests/concurrency/catalog-writers.test.ts`; 16 connections/barriers |
| US-006-AC3 | `matched_type_addition_scale_meets_declared_comparison` | 10 versus 1,000 existing types satisfies predeclared end-to-end time statistic/ratio with raw samples | `@covers US-006-AC3` | Performance integration | `tests/performance/catalog-scale.test.ts`; matched candidates/data |

## Data and Additional Probes

Statistics lifecycle vectors create a definition without collecting data and require defined/not_confirmed rather than collected. Test qualified empty dataset versus unavailable collection observation, failed collection leaving the original definition, changed collection profile and competing refresh/replacement. Current data drift cannot turn a historical collection receipt into a guaranteed fresh/performance result. Unsupported native definition meaning refuses; exact generated artifacts and actual native observations are required. Acceptance report remains unchanged through every later outcome.

Postcommit job vectors verify pending adopted acceptance cannot dispatch, exact repeat does not duplicate jobs, two dispatchers serialize and a generation change cannot permit overlapping unresolved DDL. Lose the connection around native completion and require observed outcome before retry. A stale attempt cannot publish ready after declaration/profile change; a same-name wrong-definition or host-owned index cannot be dropped as cleanup. Ready requires native validity and full definition/target match, with immutable acceptance/attempt evidence. Statistics jobs are a separate unresolved profile rather than assumed covered by index state.

Independent inventory includes indexes/columns/constraints/functions/partitions; table count alone is insufficient. Binding-index control must remain pending until separate job completes. Native lock traces prove writers really overlap acceptance, not finish before it. Record retries/stale refusals separately and reconcile AC2 admission semantics before passing. Assert exact committed writer count/data/journal, not only zero exceptions.

Pin native target/adapter/role/isolation and hardware/load. Benchmark candidate size, data and report scope stay fixed; key-on-populated-type and transforms are separately measured data-dependent work. Missing predefined scale threshold cannot yield a pass.

## Executable Proof and Handoff

Future commands `bun test tests/catalog/no-ddl.test.ts tests/concurrency/catalog-writers.test.ts tests/performance/catalog-scale.test.ts` require actual files, harness and finalized measurement/admission interpretation. All three criteria block closeout. Historical spike evidence does not qualify changed runtime automatically.


## Original writer admission schedules

Use sixteen ordinary-role connections, independently identifiable operation inputs and one acceptance connection. The fixture adds only a new type/property/relationship; existing writer definitions, values, keys and ownership are unchanged. Disable optional index jobs for this schedule. Native observation must establish real overlap and complete original operation custody; wall-clock overlap or sixteen launched promises is insufficient.

- CW-01: Admit and hold one existing-type write on each connection under the current shared-head protocol. Start acceptance and independently observe it waiting for the writers' shared custody. Complete the original writes and confirm their actual outer outcomes, then allow acceptance to acquire exclusion. Independently verify all sixteen graph/journal results and the complete accepted head/report. No writer may be reissued merely because acceptance waited.
- CW-02: Hold acceptance's exclusive head after complete candidate validation but before finalization. Start sixteen current writer admission attempts; observe their actual head wait and release acceptance with confirmed commit. Classify each attempt against its original observed revision and current native head. Successful admission must preserve its exact original input; stale admission must refuse before write/journal/report effects. The owner selected exposing the pre-effect refusal on 2026-10-09; the public facade must not retry it automatically. Neither path may silently refresh a transaction-pinned capability or reinterpret an input against changed definitions.
- CW-03: Deliberately pause one writer after its original revision observation and before shared-head acquisition. Commit the add-only acceptance, then resume admission. This is a deterministic stale-catalog control, not an unexpected write failure to erase from the results. Retain the original refusal, any separately authorized new admission and its actual outcome as distinct attempt evidence.
- CW-04: Roll back acceptance while sixteen writers wait. Confirm they resume under the unchanged original head and preserve complete original writes. If acceptance termination is unknown, keep original custody and classification; a new connection or later head cannot stand in for its outcome.

Report every submitted operation, admission attempt, stale refusal, retry, wait and confirmed/unknown outer outcome. Reconcile full original graph and journal membership, not only aggregate counts. Measure catalog-head waiting separately from declared fixed-work processing; unexpected data-table/DDL locks, missing operations or unrelated refusals cannot be relabeled as expected catalog delay. Host deadlines, pool pressure and arbitrary competing workloads remain separate profiles.

CW-01–04 are planned, not_run. They provide concrete independent fault/overlap schedules under the selected public pre-effect refusal policy. US-006-AC2 cannot pass until a finite workload/deadline profile is selected and every original submitted operation is accounted for. There is no automatic pre-effect retry loop; effects-started, adopted transaction restart and uncertain commit recovery retain their existing separate classifications.
