---
ddx:
  id: US-048
  type: user-stories
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-003
      kind: informed_by
    - id: truss.prd
      kind: informed_by
---

# US-048: Recover and cancel queued UPDATE jobs

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


**Feature:** FEAT-003. **Feature Requirements:** PAP-TRS-04, PAP-TRS-05; supporting PAP-TRS-01–03. **PRD Requirements:** PAP-TRS-04, PAP-TRS-05. **Priority:** First bulk UPDATE slice. **Status:** Draft.

## Story

As a Data platform engineer, I want to restart workers and cancel jobs while retaining original outcomes, so that uncertain acknowledgements cannot duplicate queued changes.

## Context

This is a bounded part of the owner-selected portable-action proof. Existing action/core meaning is authoritative; compilation, selection and native execution remain separate. Governing contracts are CONTRACT-013, CONTRACT-007, CONTRACT-009; upstream owner dependencies are pinned explicitly at build/admission.

## Walkthrough

1. Select the original model/action/plan and exact profiles.
2. Request this story's operation through its owned public boundary.
3. Inspect the retained result or source-qualified refusal.
4. Verify the appropriate portable or native evidence before claiming support.

## Acceptance Criteria

- [ ] **US-048-AC1** — Given a crash/lost acknowledgement after original business or seal/submit/claim/cancel/reconcile control commit, when the worker recovers its original issued attempt, then full original atomic result is returned unchanged without repeated graph/control mutation; confirmed control noncommit has ControlFailure and unknown disposition retains ControlUnknown.
- [ ] **US-048-AC2** — Given competing/unauthorized workers and expired/stale claims, when claim/execute/reconcile races, then full refusal unions preserve the valid job, durable effect admission prevents blind takeover and no expired lease/not-found alone authorizes reexecution.
- [ ] **US-048-AC3** — Given cancel before dispatch or racing native execution, when control settles, then future admission is fenced, previously committed effects remain and an unresolved original transaction is reported reconciling rather than cancelled/rolled back.
- [ ] **US-048-AC4** — Given unequal submit intent, retirement, expiry, restore, revoked original human/delegation or denied outsider lookup, when original admission/review/reconcile runs, then valid original-subject loss stops future work while unauthorized outsiders cannot stop a valid job or disclose protected outcomes; no automatic new namespace/token/manifest is created.
- [ ] **US-048-AC5** — Given unchanged SQL and registered UMF action, when the packed Rust-Python compiler and public Truss host run selection, queue, batches and restart/conflict controls, then independent native graph/receipt/journal observations agree with the frozen manifest and all original dependency/runtime versions are retained.
- [ ] **US-048-AC6** — Given traced/untraced runs and diagnostic sink failure, when job attempts are captured through the existing real receiver, then trusted job/attempt correlation works, protected inputs are excluded before sinks and exporter outage cannot change commit/fence/recovery meaning.

- [ ] **US-048-AC7** — Given two workers and three targets in two batches with batch0 containing two targets, when the bounded original-admission/commit/fence/cancel/recovery model is checked, then atomic-batch and nonduplication properties have useful success/recovery witnesses and broken-fence/partial-commit controls fail; model transitions are mapped to native tests without claiming native proof.

- [ ] **US-048-AC8** — Given an admitted original batch that rolls back from an invariant failure and crashes before durable stopped persistence, when reconciliation observes confirmed original noncommit but no terminal disposition, then it stops as PAP_ABORT_DISPOSITION_UNKNOWN without retry; unavailable original termination evidence stays reconciling.

## Edge Cases

Relevant unknown meaning and mismatched pins refuse; missing native evidence cannot be replaced by shape validity. Uncertain commits require original reconciliation. Empty/no-op work never fabricates business changes.

## Test Scenarios

| Scenario | Criterion | State/action | Expected result |
| --- | --- | --- | --- |
| original_recovery | US-048-AC1 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | the complete original batch outcome is returned once and no graph effect is repeated. |
| fence_two_workers | US-048-AC2 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | only the serialized original fence can admit the next batch and lease expiry/not-found alone cannot authorize reexecution. |
| cancel_linearization | US-048-AC3 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | future admission is fenced, previously committed effects remain and an unresolved original transaction is reported reconciling rather than cancelled/rolled back. |
| retention_and_authority | US-048-AC4 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | original intent/nonreuse and current protected discovery authorization hold without automatic new namespace/token or receipt disclosure. |
| joint_update_proof | US-048-AC5 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | independent native graph/receipt/journal observations agree with the frozen manifest and all original dependency/runtime versions are retained. |
| diagnostic_privacy | US-048-AC6 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | trusted job/attempt correlation works, protected inputs are excluded before sinks and exporter outage cannot change commit/fence/recovery meaning. |

## Dependencies

US-046/047; original host recovery registry, admitted namespace lifecycle and diagnostic pipeline. Parent solution design SD-003; contracts CONTRACT-013, CONTRACT-007, CONTRACT-009.

## Out of Scope

Live predicates, nullable/null mutation semantics, computed assignments, joins, key edits, whole-job atomicity, external business effects, compensation and a second native backend. Historical acceptance totals do not include this story.
