---
ddx:
  id: STP-047
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-047
      kind: informed_by
    - id: TD-047
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: CONTRACT-013
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
---

# STP-047: Execute guarded atomic UPDATE batches

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

[US-047](../../01-frame/user-stories/US-047-execute-atomic-update-batches.md), [TD-047](../../02-design/technical-designs/TD-047-execute-atomic-update-batches.md), SD-003.

## Scope and Objective

Prove US-047's original portable or native outcomes under its contracted profile. All rows are planned; no existing historical pass is allocated to new criteria.

## Acceptance Criteria Test Mapping

| Criterion | Planned test | Asserted behavior | Canonical citation | Layer | Planned file |
| --- | --- | --- | --- | --- | --- |
| US-047-AC1 | `atomic_effects` | all required UMF set effects/verification, complete item outcomes, graph/journal and batch prefix receipt share one confirmed outer commit. | `@covers US-047-AC1` | Native integration | `packages/python/tests/test_bulk_executor.py` |
| US-047-AC2 | `identity_and_version` | original identity/version/correspondence checks under held locks prevent redirect/lost update and all batch effects roll back. | `@covers US-047-AC2` | Native integration | `packages/python/tests/test_bulk_executor.py` |
| US-047-AC3 | `stop_with_prefix` | the complete earlier prefix stays committed, batch1 has no business effect and no later batch is admitted. | `@covers US-047-AC3` | Native integration | `packages/python/tests/test_bulk_executor.py` |
| US-047-AC4 | `current_authority` | original current-authority/invariant boundaries refuse before unauthorized effects and no privileged fixture path substitutes for the public gateway. | `@covers US-047-AC4` | Native integration | `packages/python/tests/test_bulk_executor.py` |
| US-047-AC5 | `no_op_receipt` | exact no-op and complete original result vectors persist without fabricated changes/version increments or repeat effects. | `@covers US-047-AC5` | Native integration | `packages/python/tests/test_bulk_executor.py` |
| US-047-AC6 | `capacity_and_failure` | complete rollback/stop or uncertainty is preserved without partial item outcomes, truncated receipts or lost original recovery custody. | `@covers US-047-AC6` | Native integration | `packages/python/tests/test_bulk_executor.py` |
| US-047-AC7 | `namespace_token_collision` | namespace-inclusive reserved item tokens remain distinct and cannot replay, conflict with or disclose the other job. | `@covers US-047-AC7` | Native integration | `packages/python/tests/test_bulk_executor.py` |

## Executable Proof

Primary planned command: `python3 -m unittest discover -s packages/python/tests -p test_bulk_executor.py`. Create the target before feature implementation; every test must cite its allocated AC and be capable of failing. Record results under `docs/helix/04-build/evidence/bulk-update/`, with actual source/profile/runtime versions, original owner hashes, negative controls and explicit residuals. Actual Chromium is required for the browser rows; pure/static checks cannot substitute for native or browser outcomes.

## Data and Setup

Original fixture owner/path: UMF `docs/helix/03-test/fixtures/bulk-update/cases.json` and `model.json`, owned by US-902; all consumers pin the originals. Shared language-neutral fixture: three matching Customer identities2/10/11, active true, integer last_seen below100, fourth identity12 above100; batchSize2 yields [2,1]; registered set-active recipe plus original model/action/source/selection pins. Negative controls mutate one pinned input/guard/fence/permission at a time. Runtime rows require isolated owned databases/roles and current source/installer closure; synthetic issuers cannot qualify protected ordinary-person admission.

## Edge Cases and Failure Modes

Empty/no-op, exact bound/overflow, Unicode/large-integer, duplicate/unknown fields, tampering, missing authority, drift and uncertainty must keep their distinct contract outcomes. Native concurrency controls use actual two-connection barriers and independent effect/outcome queries.

## Build Handoff

US-046 and prerequisite US-049; qualified protected writer/invariant/action gateway and new control/outcome homes through shipped installer/migration. Create red tests first; implement the contracted boundary; then independently qualify effects/refusals and source correspondence. Done requires every allocated AC's executed cited test and expected outcome, current upstream pins and complete applicable dependency evidence. This plan allocates tests; it does not report executed coverage.

## Formal and Diagnostic Proof

TD names the applicable bounded state analysis and negative controls. US-048-AC6 requires real receiver correlation with/without spans, protected-value pre-sink absence and sink-outage safety. Both formal source correspondence and native races remain required; model results or telemetry parsing alone are insufficient.
