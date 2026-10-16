---
ddx:
  id: STP-048
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-048
      kind: informed_by
    - id: TD-048
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: CONTRACT-013
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# STP-048: Recover and cancel queued UPDATE jobs

## Consolidation scope amendment — 2026-10-16

This historical draft is preserved from the earlier authorized bulk-action work.
It does not claim that its planned tests or protected executor are complete.
Current owner amendments govern every requirement below: Python-first delivery,
basic functionality tests, stock PostgreSQL practical limits and the existing
native statement/operation deadlines. Receiver/exporter, custom tracing/metrics,
formal-model and elaborate qualification prescriptions below are historical
optional proposals, not required implementation or release gates. A proposed
upstream60-second allowance cannot widen current native10-second SQL or30-second
operation limits. Host connection/transaction ownership and no hidden retries
remain unchanged. Existing `bulk_action_gateway.py`, action-store and authority
components on main must be reused and qualified; planned paths or statements
that no gateway exists describe the historical checkpoint, not current main.
Any cited evidence absent from main is **unverified historical evidence**, not
completion. Current public capability claims require their actual scoped tests.


## Story Reference

[US-048](../../01-frame/user-stories/US-048-recover-queued-update.md), [TD-048](../../02-design/technical-designs/TD-048-recover-queued-update.md), SD-003.

## Scope and Objective

Prove US-048's original portable or native outcomes under its contracted profile. All rows are planned; no existing historical pass is allocated to new criteria.

## Acceptance Criteria Test Mapping

| Criterion | Planned test | Asserted behavior | Canonical citation | Layer | Planned file |
| --- | --- | --- | --- | --- | --- |
| US-048-AC1 | `original_recovery` | full original atomic result is returned unchanged without repeated graph/control mutation; confirmed control noncommit has ControlFailure and unknown disposition retains ControlUnknown. | `@covers US-048-AC1` | Native integration | `packages/python/tests/test_bulk_jobs.py` |
| US-048-AC2 | `fence_two_workers` | full refusal unions preserve the valid job, durable effect admission prevents blind takeover and no expired lease/not-found alone authorizes reexecution. | `@covers US-048-AC2` | Native integration | `packages/python/tests/test_bulk_jobs.py` |
| US-048-AC3 | `cancel_linearization` | future admission is fenced, previously committed effects remain and an unresolved original transaction is reported reconciling rather than cancelled/rolled back. | `@covers US-048-AC3` | Native integration | `packages/python/tests/test_bulk_jobs.py` |
| US-048-AC4 | `retention_and_authority` | valid original-subject loss stops future work while unauthorized outsiders cannot stop a valid job or disclose protected outcomes; no automatic new namespace/token/manifest is created. | `@covers US-048-AC4` | Native integration | `packages/python/tests/test_bulk_jobs.py` |
| US-048-AC5 | `joint_update_proof` | independent native graph/receipt/journal observations agree with the frozen manifest and all original dependency/runtime versions are retained. | `@covers US-048-AC5` | Native integration | `packages/python/tests/test_bulk_jobs.py` |
| US-048-AC6 | `diagnostic_privacy` | trusted job/attempt correlation works, protected inputs are excluded before sinks and exporter outage cannot change commit/fence/recovery meaning. | `@covers US-048-AC6` | Native integration | `packages/python/tests/test_bulk_jobs.py` |
| US-048-AC7 | `formal_batch_model` | atomic-batch and nonduplication properties have useful success/recovery witnesses and broken-fence/partial-commit controls fail; model transitions are mapped to native tests without claiming native proof. | `@covers US-048-AC7` | Contract | `docs/helix/02-design/experiments/bulk-actions/check_model.py` |
| US-048-AC8 | `rollback_stop_crash` | it stops as PAP_ABORT_DISPOSITION_UNKNOWN without retry; unavailable original termination evidence stays reconciling. | `@covers US-048-AC8` | Native integration | `packages/python/tests/test_bulk_jobs.py` |

## Executable Proof

Primary planned command: `python3 -m unittest discover -s packages/python/tests -p test_bulk_jobs.py`. Create the target before feature implementation; every test must cite its allocated AC and be capable of failing. Record results under `docs/helix/04-build/evidence/bulk-update/`, with actual source/profile/runtime versions, original owner hashes, negative controls and explicit residuals. Actual Chromium is required for the browser rows; pure/static checks cannot substitute for native or browser outcomes.

## Data and Setup

Original fixture owner/path: UMF `docs/helix/03-test/fixtures/bulk-update/cases.json` and `model.json`, owned by US-902; all consumers pin the originals. Shared language-neutral fixture: three matching Customer identities2/10/11, active true, integer last_seen below100, fourth identity12 above100; batchSize2 yields [2,1]; registered set-active recipe plus original model/action/source/selection pins. Negative controls mutate one pinned input/guard/fence/permission at a time. Runtime rows require isolated owned databases/roles and current source/installer closure; synthetic issuers cannot qualify protected ordinary-person admission.

## Edge Cases and Failure Modes

Empty/no-op, exact bound/overflow, Unicode/large-integer, duplicate/unknown fields, tampering, missing authority, drift and uncertainty must keep their distinct contract outcomes. Native concurrency controls use actual two-connection barriers and independent effect/outcome queries.

## Build Handoff

US-046/047; original host recovery registry, admitted namespace lifecycle and diagnostic pipeline. Create red tests first; implement the contracted boundary; then independently qualify effects/refusals and source correspondence. Done requires every allocated AC's executed cited test and expected outcome, current upstream pins and complete applicable dependency evidence. This plan allocates tests; it does not report executed coverage.

## Formal and Diagnostic Proof

TD names the applicable bounded state analysis and negative controls. US-048-AC6 requires real receiver correlation with/without spans, protected-value pre-sink absence and sink-outage safety. Both formal source correspondence and native races remain required; model results or telemetry parsing alone are insufficient.

Formal gate: `python3 docs/helix/02-design/experiments/bulk-actions/check_model.py` (planned runner owns pinned TLC setup, configurations, reachable witnesses and broken-mechanism controls). Native crash test must kill after original ROLLBACK confirmation and before stop-control persistence; receipt absence alone cannot prove this premise.

Control-loss cases under US-048-AC1: lose original seal/submit/claim/cancel/reconcile control COMMIT acknowledgement, recover the same immutable original result; independently confirm control rollback before result persistence and observe ControlFailure; never infer rollback from absent outcome. A subsequent job-state change must not alter recovered original sampled submit/claim output.
