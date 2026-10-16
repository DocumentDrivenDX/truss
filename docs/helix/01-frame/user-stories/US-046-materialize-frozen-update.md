---
ddx:
  id: US-046
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

# US-046: Materialize and seal frozen UPDATE work

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


**Feature:** FEAT-003. **Feature Requirements:** PAP-TRS-01, PAP-TRS-02, PAP-TRS-05. **PRD Requirements:** PAP-TRS-01, PAP-TRS-02, PAP-TRS-05. **Priority:** First bulk UPDATE slice. **Status:** Draft.

## Story

As a Data platform engineer, I want to select and seal the exact work requested by a compiled UPDATE, so that queued changes are reviewable and cannot expand or redirect while waiting.

## Context

This is a bounded part of the owner-selected portable-action proof. Existing action/core meaning is authoritative; compilation, selection and native execution remain separate. Governing contracts are CONTRACT-013, CONTRACT-003, CONTRACT-005, CONTRACT-010, CONTRACT-012; upstream owner dependencies are pinned explicitly at build/admission.

## Walkthrough

1. Select the original model/action/plan and exact profiles.
2. Request this story's operation through its owned public boundary.
3. Inspect the retained result or source-qualified refusal.
4. Verify the appropriate portable or native evidence before claiming support.

## Acceptance Criteria

- [ ] **US-046-AC1** — Given a qualified actor/read context and original compiled plan, when materialized, then Key, canonical identity, whole-row version and complete matching set come from one original native snapshot and the exact admitted Weft selection program.
- [ ] **US-046-AC2** — Given rows changed/inserted after sealing, when work is reviewed, then original target count/order/values/pins stay unchanged and new matches are absent; review reserves no execution rights.
- [ ] **US-046-AC3** — Given edited client manifest bytes with recomputed hashes, missing original seal/issuer/initiating human, wrong store/epoch, duplicate targets, noncanonical [1,2] partition, ambiguous Keys or missing issued guards, when sealing/submission is attempted, then no runnable job is admitted without exact retained authorized seal custody.
- [ ] **US-046-AC4** — Given empty, exact-limit, overflow and timeout selections, when materialized, then empty work seals explicitly, supported complete boundaries succeed and incomplete/exhausted work cannot be sealed or silently truncated.
- [ ] **US-046-AC5** — Given current read/review permission loss or hidden rows, when materialization/review is requested, then selection stays within the explicit authorized view and protected source/manifest data is withheld without permission.

## Edge Cases

Relevant unknown meaning and mismatched pins refuse; missing native evidence cannot be replaced by shape validity. Uncertain commits require original reconciliation. Empty/no-op work never fabricates business changes.

## Test Scenarios

| Scenario | Criterion | State/action | Expected result |
| --- | --- | --- | --- |
| coherent_cut | US-046-AC1 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | Key, canonical identity, whole-row version and complete matching set come from one original native snapshot and the exact admitted Weft selection program. |
| freeze_after_selection | US-046-AC2 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | original target count/order/values/pins stay unchanged and new matches are absent; review reserves no execution rights. |
| sealing_integrity | US-046-AC3 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | no runnable manifest/job is created. |
| bounded_complete_work | US-046-AC4 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | empty work seals explicitly, supported complete boundaries succeed and incomplete/exhausted work cannot be sealed or silently truncated. |
| authorized_review | US-046-AC5 | Owner fixture cases keyed by this test name; exact named negative mutation and expected outcome in the shared corpus | selection stays within the explicit authorized view and protected source/manifest data is withheld without permission. |

## Dependencies

UMF US-902/903, Weft US-008/009; original accepted catalog/security/selection-lowering admission and installed read runtime. Parent solution design SD-003; contracts CONTRACT-013, CONTRACT-003, CONTRACT-005, CONTRACT-010, CONTRACT-012.

## Out of Scope

Live predicates, nullable/null mutation semantics, computed assignments, joins, key edits, whole-job atomicity, external business effects, compensation and a second native backend. Historical acceptance totals do not include this story.
