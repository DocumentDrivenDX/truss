---
ddx:
  id: TD-048
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-048
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: CONTRACT-013
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# TD-048: Recover and cancel queued UPDATE jobs

## Consolidation scope amendment — 2026-10-16

This historical draft is preserved from the earlier authorized bulk-action work.
It does not claim that its planned tests or protected executor are complete.
Current owner amendments govern every requirement below: Python-first delivery,
basic functionality tests, stock PostgreSQL practical limits and the existing
native statement/operation deadlines. Owner decision (2026-11-08) scopes acceptance gates: when making bulk
recovery or diagnostics claims, the bounded model for US-048-AC7 and the
traced/untraced real-receiver correlation, privacy and outage tests for
STP-048 AC6 are required. Other receiver/exporter, custom tracing/metrics and
elaborate qualification prescriptions remain optional; these gates do not
extend to unrelated feature claims. A proposed
upstream60-second allowance cannot widen current native10-second SQL or30-second
operation limits. Host connection/transaction ownership and no hidden retries
remain unchanged. Existing `bulk_action_gateway.py`, action-store and authority
components on main must be reused and qualified; planned paths or statements
that no gateway exists describe the historical checkpoint, not current main.
Any cited evidence absent from main is **unverified historical evidence**, not
completion. Current public capability claims require their actual scoped tests.


**User Story:** [US-048](../../01-frame/user-stories/US-048-recover-queued-update.md). **Feature:** FEAT-003. **Solution Design:** SD-003.

## Scope

One vertical journey defined by US-048; inherit the [parent solution design](../solution-designs/SD-003-mutation-and-concurrency.md) and architecture's portable/compiler/native boundaries. Shared surfaces live in CONTRACT-013, CONTRACT-007, CONTRACT-009.

## Technical Approach

Reuse original UMF core/actions identity, input, declaration and assessment semantics. Select pinned artifacts/registries explicitly. Preserve original intent and use source-qualified refusal; never make a local dialect, key codec or authority substitute. Python-first protected adapter and engine-owned transactions; original current-authority and native admission remain prerequisites.

## Component Changes

Planned source files: `packages/python/src/truss/bulk_jobs.py; packages/python/src/truss/bulk_job_plan.py; packages/postgresql/src/bulk-jobs.ts`. These additions are not present implementations.

| AC | Component realization |
| --- | --- |
| US-048-AC1 | original recovery through the governing contract and focused test below |
| US-048-AC2 | fence two workers through the governing contract and focused test below |
| US-048-AC3 | cancel linearization through the governing contract and focused test below |
| US-048-AC4 | retention and authority through the governing contract and focused test below |
| US-048-AC5 | joint update proof through the governing contract and focused test below |
| US-048-AC6 | diagnostic privacy through the governing contract and focused test below |
| US-048-AC7 | formal_batch_model through the governing contract and focused independent witness |
| US-048-AC8 | rollback_stop_crash through the governing contract and focused independent witness |

## API/Interface Design

CONTRACT-013, CONTRACT-007, CONTRACT-009 define the exact shared shapes and methods. New exports follow those contracts; no signatures are independently defined here. Upstream schemas/fixtures are original owner inputs. Construct adapters only in the host registration boundary. Core cannot import native I/O/credentials; compiler cannot import Truss storage.

### Boundary realization

Boundary gate: `python3 scripts/check-module-boundaries.py` plus the existing TypeScript boundary inspection. Add the new pure/native module distinction to the checker allowlist before source wiring. Concrete native writer dependencies, native homes and privileged entry ACLs join the original complete installer inventory. Diagnostic wire authority is `docs/helix/02-design/contracts/diagnostics.proposal.md`, consumed unchanged.

## Data Model Changes

Fixed job/manifest/fence/outcome native homes require a shipped versioned migration and complete installer/admission inventory, not per-action tables. Use original accepted identity/value codecs and complete-result custody.

## Integration Points

US-046/047; original host recovery registry, admitted namespace lifecycle and diagnostic pipeline. Unsupported/unavailable original dependencies refuse, with no fallback to fixtures or another executor.

## Security

Artifacts never load code or authenticate principals. Current protected read/execution/discovery authority remains executor-owned. Raw source/inputs stay out of diagnostics; retained manifests/outcomes require separately enforced access. Unknown relevant meaning blocks eligibility.

## Performance

Use the exact finite item/byte/node/deadline/result-capacity bounds in the contracts. Test both exact boundary and first overflow. No throughput/latency claim is made from structural tests.

## Testing

[STP-048](../../03-test/test-plans/STP-048-recover-queued-update.md) allocates each criterion once to a planned test with canonical citation. Command: `python3 -m unittest discover -s packages/python/tests -p test_bulk_jobs.py`. The command/test target is planned, not currently passing evidence. Independent exact effects/refusals are the oracle, not generated output snapshots alone.

## Formal Specification

The selected formal-methods concern applies to guard-to-write races (US-047) and fence/commit/recovery/cancel (US-048); US-046 uses snapshot/guard provenance premises rather than claiming a temporal proof from shape checks. Plan a bounded executable state model under `docs/helix/02-design/experiments/bulk-actions/` with two workers, two batches, three targets (batch0 has two targets; batch1 has one), fences, native transaction state, cancel and receipt state. Initialize no effects/outcomes and one sealed manifest; model claim/admit/write/commit/ack-loss/known-abort/lookup/reconcile/cancel/restore. Safety: one effect per original item, atomic batch outcomes, no stale-fence write, unchanged frozen target identity and no later batch while unresolved/stopped/cancelled. Liveness assumes fair scheduling, eventually terminating native transaction and available authorized lookup; no liveness promise during permanent partition/revocation. US-048-AC7 owns the model and maps admission markers, original rollback-before-stop (AC8), namespace token scope (US-047-AC7) and cancellation transitions to actual native witnesses. Model files: `BulkUpdate.tla`, `BulkUpdate.cfg`, `check_model.py`; planned command `python3 docs/helix/02-design/experiments/bulk-actions/check_model.py`. Require useful commit/recovery traces and broken-fence/recovery controls. Map model transitions to the actual adapter/lock/outcome tests before completion; bounded analysis does not qualify native PostgreSQL enforcement.

## Diagnostic Wiring

Reuse selected existing diagnostic/capture contracts and construction pipeline. US-048-AC6/STP-048 owns real receiver, traced/untraced correlation, pre-sink privacy and exporter failure proof. Other stories consume the same pipeline without inventing a wire format. Admission/refusal and native completion emit only safe attempt/result references.

## Migration & Rollback

New profiles are opt-in; existing action/read/group behavior remains intact. Disable new admission while retaining all original manifests, terminal outcomes/tombstones and unresolved recovery custody. Do not reverse committed batches or drop native homes to simulate rollback.

## Implementation Sequence

1. Create the planned red tests in `packages/python/tests/test_bulk_jobs.py` with canonical citations.
2. Implement contract-owned pure/component behavior in the named source files.
3. Integrate original dependency boundaries and run portable/native witnesses.
4. Retain exact versions, failed attempts, residual gaps and verified source correspondence.

## Risks

Incomplete upstream/native admission must block dependent execution without blocking independent pure work. Namespace/guard changes require new reviewed intent; they cannot migrate pending work silently. Architecture boundary check and concrete dependency closure must be current before public source readiness.

## Bounded model implementation (2026-10-13)

Historical checkpoint: the earlier PR51 candidate at `da63eaf6043bf7f3f78d71d4f3768102f43d39eb` retains Python and TLC receipts reporting 604,852 reachable states (Python receipt SHA-256 `b70c5d3861ed50f4fe721443b17a65155427f20dd91d779282875cf518df8752`; TLC receipt SHA-256 `aead37c3fb594799f134f8066eafdd01b976287f2802323740bc308a312f188c`). That historical source/result pairing remains intact and was not rerun against the current runtime. At this source revision, the retained Python and TLC result JSONs report 607,102 reachable states ([Python result](../../04-build/evidence/bulk-update/batch-model-results.json), SHA-256 `1e8e524b6955bb8a0a1086f6a40bdc43d98bd26a8aa1947f0245cb8e92672b63`; [TLC result](../../04-build/evidence/bulk-update/tlc-model-results.json), SHA-256 `aed6c0a4b21853c0f97c1758096c0d99a9e82963a001279a86831ff574a085d8`), and the TLC result records five negative controls. However, the retained `python-model.log` reports 604,852 and pins the earlier `check_model.py` source hash `3610bd0e4f04b829ac35c73e48cfd67ec907c10617dc2662ecac597fb62d2c4f`, not the current source hash recorded by the result JSON. Therefore the 607,102 Python result is receipt-reported but not corroborated by a matching retained execution log; the discrepancy remains unresolved and no model was rerun here. The [job-table refinement receipt](../../04-build/evidence/bulk-update/job-refinement-results.json) reports 607,102, but its fixture remains `planned` and still needs UMF owner review. These retained records do not establish liveness, current runtime behavior or native qualification. AC7 and dependent native stories remain open until actual adapter/native correspondence is exercised.
