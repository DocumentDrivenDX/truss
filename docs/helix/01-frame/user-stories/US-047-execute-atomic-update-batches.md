---
ddx:
  id: US-047
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

# US-047: Execute guarded atomic UPDATE batches

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


**Feature:** FEAT-003. **Feature Requirements:** PAP-TRS-01, PAP-TRS-03, PAP-TRS-04. **PRD Requirements:** PAP-TRS-01, PAP-TRS-03, PAP-TRS-04. **Priority:** First bulk UPDATE slice. **Status:** Draft.

## Story

As a Data platform engineer, I want to execute sealed work in bounded atomic batches, so that conflicts stop the job without partial batch writes or loss of earlier commits.

## Context

This is a bounded part of the owner-selected portable-action proof. Existing action/core meaning is authoritative; compilation, selection and native execution remain separate. Governing contracts are CONTRACT-013, CONTRACT-004, CONTRACT-007, CONTRACT-009, CONTRACT-012; upstream owner dependencies are pinned explicitly at build/admission.

## Walkthrough

1. Select the original model/action/plan and exact profiles.
2. Request this story's operation through its owned public boundary.
3. Inspect the retained result or source-qualified refusal.
4. Verify the appropriate portable or native evidence before claiming support.

## Acceptance Criteria

- [ ] **US-047-AC1** — Given an authorized original batch, when executed, then all required UMF set effects/verification, complete item outcomes, graph/journal and batch prefix receipt share one confirmed outer commit.
- [ ] **US-047-AC2** — Given a target edit, deletion, Key rebinding or restored epoch, when executing, then original identity/version/correspondence checks under held locks prevent redirect/lost update and all batch effects roll back.
- [ ] **US-047-AC3** — Given batch0 committed and batch1 conflicted/rejected, when the job settles, then the complete earlier prefix stays committed, batch1 has no business effect and no later batch is admitted.
- [ ] **US-047-AC4** — Given concurrent revocation/catalog retirement or an attempted out-of-frame/raw write, when executing, then original current-authority/invariant boundaries refuse before unauthorized effects and no privileged fixture path substitutes for the public gateway.
- [ ] **US-047-AC5** — Given unchanged assignments or retained equal intent, when executed/replayed, then exact no-op and complete original result vectors persist without fabricated changes/version increments or repeat effects.
- [ ] **US-047-AC6** — Given result reservation exhaustion or runtime/invariant failure, when execution fails, then complete rollback/stop or uncertainty is preserved without partial item outcomes, truncated receipts or lost original recovery custody.

- [ ] **US-047-AC7** — Given two registered job namespaces with the same job ID/action/principal and batch/item ordinals, when both execute/reconcile, then namespace-inclusive reserved item tokens remain distinct and cannot replay, conflict with or disclose the other job.

## Edge Cases

Relevant unknown meaning and mismatched pins refuse; missing native evidence cannot be replaced by shape validity. Uncertain commits require original reconciliation. Empty/no-op work never fabricates business changes.

## Test Scenarios

| Scenario | Criterion | State/action | Expected result |
| --- | --- | --- | --- |
| atomic_effects | US-047-AC1 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | all required UMF set effects/verification, complete item outcomes, graph/journal and batch prefix receipt share one confirmed outer commit. |
| identity_and_version | US-047-AC2 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | original identity/version/correspondence checks under held locks prevent redirect/lost update and all batch effects roll back. |
| stop_with_prefix | US-047-AC3 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | the complete earlier prefix stays committed, batch1 has no business effect and no later batch is admitted. |
| current_authority | US-047-AC4 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | original current-authority/invariant boundaries refuse before unauthorized effects and no privileged fixture path substitutes for the public gateway. |
| no_op_receipt | US-047-AC5 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | exact no-op and complete original result vectors persist without fabricated changes/version increments or repeat effects. |
| capacity_and_failure | US-047-AC6 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | complete rollback/stop or uncertainty is preserved without partial item outcomes, truncated receipts or lost original recovery custody. |

## Dependencies

US-046 and prerequisite US-049; qualified protected writer/invariant/action gateway and new control/outcome homes through shipped installer/migration. Parent solution design SD-003; contracts CONTRACT-013, CONTRACT-004, CONTRACT-007, CONTRACT-009, CONTRACT-012.

## Out of Scope

Live predicates, nullable/null mutation semantics, computed assignments, joins, key edits, whole-job atomicity, external business effects, compensation and a second native backend. Historical acceptance totals do not include this story.

US-049 is a required predecessor: the bounded Python action gateway/delegated human context must be implemented and qualified before atomic batches execute.
