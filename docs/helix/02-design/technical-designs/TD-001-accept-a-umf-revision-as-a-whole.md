---
ddx:
  id: TD-001
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-001
      kind: informed_by
    - id: SD-001
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# TD-001: Whole-revision acceptance

## Selected decision handoff — 2026-10-07

Implement selected immutable separate reports after original event production and before atomic head publication. Legacy report-column conversion and exact native report producer remain installer prerequisites.


## Technical Approach

Acceptance repeat detection follows CONTRACT-003's complete-input/current-head rule, not equality of derived rows. Retain exact compared document/binding/policy/profile/transform inputs and preserve the original report/origin on repeat. A changed source archive or historical match requires current acceptance validation. The complete acceptance-input schema and canonical/domain-frame proposal are authored in CONTRACT-003/009. Original profile adoption, bounded producer/decoder and persisted-input/archive realization remain unresolved; no inferred partial fingerprint may claim the repeat capability.

Validate all supplied document bytes with the pinned UMF pipeline, collect every available diagnostic across documents, then perform deterministic whole-set derivation/checks under the catalog head exclusive lock. Persist documents, definitions/history, origin, transforms/rebind journal, report and head advance atomically. Invalid input has no accepted revision. Caller-owned execution uses savepoint/pending semantics and never commits the host transaction.

## Report outcomes and original recovery

A verified exact current-head repeat returns the original immutable report and origin without another revision, report row, transform or index dispatch. A historically matching input after a different current head follows fresh acceptance rules; archive equality cannot bypass current catalog/data/authority validation. Pending execution in a caller-owned transaction may expose a provisional report only under the original transaction custody; successful savepoint release is not committed acceptance.

A rejected candidate returns complete admitted diagnostics and no accepted revision/report/head effects. Failure after event or report insertion rolls back the entire local acceptance operation while preserving earlier caller work. A successful native commit followed by a lost response leaves the original report immutable and enters original acceptance recovery; it cannot be repaired by inserting another report or advancing another head. Index-job completion updates its separate observation state and never edits the accepted report. These outcomes must retain exact original input/report/event/source pins and distinguish committed, pending and unknown transaction outcomes.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/catalog/validate.ts` | Exact document pins, complete validity/support diagnostics | US-001-AC1, US-001-AC2 |
| `packages/core/src/catalog/report.ts` | Complete source assertion inventory and enforcement allocation | US-001-AC1, US-001-AC3 |
| `packages/postgresql/src/catalog/accept.ts` | Head-first exclusion, final checks and atomic persistence | US-001-AC1, US-001-AC2 |
| `tests/catalog/accept.test.ts` | Independent accepted/rejected/report evidence | All criteria |

## Interfaces and Completeness

CONTRACT-003 owns import set/steps/report; TD-039 owns validator parity. Empty set refuses. Digest exact input bytes before parse without host numeric coercion. Preserve document-qualified diagnostic paths and unknown content. Validate every parseable document rather than short-circuit on first error. A malformed document can block dependent semantic checks: report blocked checks explicitly, never fabricate violations or claim unavailable analysis completed. Consume the shared deterministic diagnostic/report order and selected finite resource profile. Complete scan/report capacity exhaustion yields explicit incomplete/resource refusal, never a truncated complete verdict; spill/export is not a prerequisite invented by this design.

Assertion inventory is independent of enforcement results and includes unknown/unsupported/residual assertions with honest engine/database/none classification. It must identify source document/module/element/path and scope. Database classification requires actual unavoidable guards for the qualified role; key-row uniqueness is not property derivation correctness. An accepted report includes exact UMF versions/subsets and byte digests, additions/retirements/rebinds/losses and pending index obligations.

## Transaction and Report Lifecycle

CONTRACT-003's acceptance-persistence candidate selects one protected native function statement for parent revision insertion through actual parity/head publication. Keep pure UMF/transform planning outside it, retain exact candidate outputs and use the registered bounded native plan grammar; no database callback into schema-supplied code. Plan `packages/postgresql/src/catalog/persist.ts` for exact statement binding/result/containment integration and `models/native/catalog-acceptance` for the UMF-described function/dependency/privilege inventory once its grammar/body are authored. The wrapper cannot replace native phase encapsulation or original executor arbitration. Separate immutable report persistence is owner-selected. Construct immutable semantic expectations before effects, derive insertion-owned event metadata from actual P3/P4 producers, and insert the complete report once at P5 under RP01–RP05 before publishing the head. Current layout 0.11 omits the legacy schema_rev.report column and includes catalog_acceptance_report. Populated conversion must preserve original reports and reject unavailable conversion meaning; adding a report table or current marker alone cannot qualify it. Exact native body/parameter/resource/owner review remains a build-readiness gate.

Head lock precedes catalog/data mutation. Revalidate candidate against actual locked head and full administratively visible data; caller RLS projection cannot hide tightening violators. Late persistence/report/journal failure rolls back the entire revision. CONTRACT-003 now requires the report in the acceptance transaction and separates postcommit index readiness from the immutable accepted report. The existing index/statistics readiness schemas and physical-job tooling facade supply declaration/attempt/observation boundaries; original producer/fence/native inventory and actual admission-commit qualification remain implementation/adoption gates. Caller-owned acceptance cannot start independent index work before host commit confirmation.

## Security, Tests and Sequence

### Native acceptance implementation handoff

Implement CONTRACT-003's P0–P6 semantic sequence as one protected statement, not seven host-callable methods. Plan `packages/core/src/catalog/persistence-plan.ts` for the closed category-specific plan and source/precondition inventory, `packages/postgresql/src/catalog/plan-codec.ts` for its bounded registered native transport, and `models/native/catalog-acceptance` for fixed dispatch/phase/body/privilege definitions. The codec must not accept SQL text or arbitrary physical targets; these planned files do not establish a finished canonical parameter grammar. P1 captures original admitted inputs, semantic expectations and reservations; it cannot preassign insertion-owned journal seq/at or rewrite immutable admission carriers after events occur. Under the owner-selected separate immutable report strategy, P2 inserts the parent revision under the explicitly reconciled layout, P3/P4 produce actual events in the selected engine or trigger mode, and P5 checks complete semantic parity before encoding and inserting the full report. P6 publishes only the planned head transition, then checks actual head/report/effect correspondence before application finalization. The private plan can carry reserved-value references with defined earlier-phase resolution, but cannot resolve a future effect as proof of itself.

The report implementation order is:

1. Consume the selected separate immutable report strategy and authored complete report wire; reconcile its complete replacement layout and historical event consumers. The conditional source archive and eight allocated report-store identities prove source correspondence only; native dependencies, guards, grants and conversion remain required.
2. Select original report encoder/decoder, event producers, allowed class/event/invocation paths and resource profiles. Reuse the shared OC01–OC07 operation context; report/head effects are genuine non-row contributions, not fabricated property touches.
3. Author the protected acceptance body and complete observer/finalizer inventory for RP01–RP05. A head write changes the actual operation generation and invalidates any pre-head seal. Deferred commit checks all surviving operations and the complete current union.
4. Implement STP-001's independent expected-state, late report/head failure, forged context, later-ordinal rewrite, stale seal and exhausted-reservation cases. Include both governing journal modes and original-attempt rollback/unknown recovery; pending success cannot qualify commit or index dispatch.

Separate pure plan admission controls from native effect tests. Independent expected inventories cover all category targets and source archives; native P5 observes complete actual pending effects rather than merely calling the pure validator again. A native failure after parent insertion requires original-attempt containment/recovery. Only P6 may publish the head; only the outer executor may establish commitment. The report/readiness consumer cannot dispatch index work based on P6's pending result. Retain lifecycle, canonical codec, concrete producer and native profile gaps as gates rather than inventing defaults while implementing the planner.

Acceptance requires administrative authority; ordinary module writers cannot bypass it. Catalog read/report disclosure policy remains shared gate. STP-001 owns criteria. Consume the authored report schema/assertion inventory, diagnostic completeness and index lifecycle; select exact original producer/profile realization and write red multi-document/late-failure tests; implement pure validation/report and native atomic acceptance. No automatic DDL repair or per-document commits. Failed acceptance needs no schema rollback migration because no candidate effects commit.
