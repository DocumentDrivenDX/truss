---
ddx:
  id: STP-026
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-026
      kind: informed_by
    - id: TD-026
      kind: informed_by
    - id: SD-006
      kind: informed_by
---

# STP-026: Versioned support evidence

## Story Reference

US-026, TD-026, SD-006, TP-001 and CONTRACT-004. Tests are planned.

## Scope and Objective

Prove honest support-statement assembly and stale/missing/failure visibility; receipt structure alone does not attest runtime execution.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-026-AC1 | `statement_names_exact_versions_and_evidence` | PostgreSQL/UMF version/subset and required procedure/results links appear with exact source/contract profile | `@covers US-026-AC1` | Contract | `tests/evidence/support.test.ts`; independent valid receipt |
| US-026-AC2 | `missing_target_is_unverified` | Unrun target produces unverified statement without inferred pass from nearby versions | `@covers US-026-AC2` | Contract | Same file; absent target matrix entry |
| US-026-AC3 | `new_contract_requires_new_run` | Changed contract digest makes old run stale; regenerated matching run becomes current while preserving old evidence/failures | `@covers US-026-AC3` | Contract | Same file; two contract digests/run receipts |

## Executable Proof

Future command `bun test tests/evidence/support.test.ts` requires files/schema. Criterion citations and immutable fixture hashes are retained. Real runner integration independently verifies claimed procedures/results; no fabricated receipt counts as native support.

## Data and Setup

Fixtures include matching/mismatching contract hashes under identical display labels, failed target, skipped required cases, missing links and unknown receipt fields. Expected statuses are independently authored. Preserve all prior outcomes during regeneration.

## Edge Cases and Failure Modes

Fresh timestamp with stale digest remains stale. Broken links cannot substantiate support. Partial matrix never becomes full qualification. Untrusted receipt provenance is explicit. Regeneration failure remains visible rather than falling back silently to old green evidence.

## Build Handoff

Finalize receipt/support/trust schema, write red contract fixtures, implement assembly and integrate actual runners. All three criteria block statement support; native qualification remains per referenced executable evidence.

Index/statistics readiness wires now preserve separate original declaration/attempt, installed definition versus collection and unknown failure outcomes under CONTRACT-003. They are native observation inputs, not performance/integrity evidence. Exact inventory/current-attempt/collection producer admission remains mandatory.

Run `bun docs/helix/04-build/evidence/design-audit/check-optimization-readiness.ts <Ajv Draft 2020-12 module path>`: thirteen shape witnesses pass. Independently reject forged/stale generation/inventory/committed-acceptance and distinguish qualified empty collection from no collection. Latency assertions require separate predeclared measurements; failure unknown cannot authorize dropping an unrecognized object.

Optimization shape corpus now has nineteen cases including pending-only supplied-scope result, exact-integer budget, no partial refusal, and shape-valid overrun/inventory substitution requiring native refusal. Test actual transactional late-failure containment and unchanged host transaction; nontransactional requested operations refuse this scope rather than commit implicitly. Postcommit dispatch remains separate unimplemented callable/native design.

Explicit physical-job tooling now separates supplied-transaction pending admission from actual admission-commit observation and explicit original index/statistics execution. Accepted catalog commit alone cannot start a pending queue attempt. Original issuer/fence/native inventory and uncertain termination remain mandatory.

Strict consumers reject pending-as-run, index-as-statistics and forged committed custody. Native schedules commit acceptance, leave queue admission open and require run refusal; rollback queue admission; supersede generation during observation; repeat run after lost native reply; dispose with active nontransactional work. Require original custody/recovery without blind rerun/drop or host commit. Constructor callback/SQL/worker starts must be zero. Exact queue/service/fence/result profiles remain planned.

Optimization corpus now has 27 cases including closed pending/committed job metadata. Actual queue commit observation is mandatory and differs from accepted catalog commitment; wire data cannot manufacture callable issuer handles. Native controls substitute catalog commit proof for queue proof, reuse rolled-back/superseded admission and forge observation issuer. Require unavailable/contained refusal without DDL or a replacement queue attempt.

Physical service registration/factory probes count zero callbacks/SQL/worker activity; reject duplicate replacement, mismatched service configuration, wrong family and copied issuer objects. Race registration with disposal and retain old pending/active recovery. Use matching metadata through a different service to present old admission and require custody refusal; host service/resources remain owned after assembly disposal. Strict declaration controls pass; original native composition/queue/fence evidence remains open.

Optimization corpus now has 34 cases, including operation-bound physical-job responses: admit cannot report committed, run cannot return a new admission, and unavailable exposes no readiness. Native execution failure cannot parse as a successful operation response. The actual adapter must bind tags to the original invoked method and refuse kind/phase substitution before issuer projection. Actual native outcome/commit/profile admission remains open.
