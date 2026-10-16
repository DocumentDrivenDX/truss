---
ddx:
  id: STP-046
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-046
      kind: informed_by
    - id: TD-046
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: CONTRACT-013
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-005
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
---

# STP-046: Materialize and seal frozen UPDATE work

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

[US-046](../../01-frame/user-stories/US-046-materialize-frozen-update.md), [TD-046](../../02-design/technical-designs/TD-046-materialize-frozen-update.md), SD-003.

## Scope and Objective

Prove US-046's original portable or native outcomes under its contracted profile. All rows are planned; no existing historical pass is allocated to new criteria.

## Acceptance Criteria Test Mapping

| Criterion | Planned test | Asserted behavior | Canonical citation | Layer | Planned file |
| --- | --- | --- | --- | --- | --- |
| US-046-AC1 | `coherent_cut` | Key, canonical identity, whole-row version and complete matching set come from one original native snapshot and the exact admitted Weft selection program. | `@covers US-046-AC1` | Native integration | `packages/python/tests/test_bulk_manifest.py` |
| US-046-AC2 | `freeze_after_selection` | original target count/order/values/pins stay unchanged and new matches are absent; review reserves no execution rights. | `@covers US-046-AC2` | Native integration | `packages/python/tests/test_bulk_manifest.py` |
| US-046-AC3 | `sealing_integrity` | no runnable job is admitted without exact retained authorized seal custody. | `@covers US-046-AC3` | Native integration | `packages/python/tests/test_bulk_manifest.py` |
| US-046-AC4 | `bounded_complete_work` | empty work seals explicitly, supported complete boundaries succeed and incomplete/exhausted work cannot be sealed or silently truncated. | `@covers US-046-AC4` | Native integration | `packages/python/tests/test_bulk_manifest.py` |
| US-046-AC5 | `authorized_review` | selection stays within the explicit authorized view and protected source/manifest data is withheld without permission. | `@covers US-046-AC5` | Native integration | `packages/python/tests/test_bulk_manifest.py` |

## Executable Proof

Primary planned command: `python3 -m unittest discover -s packages/python/tests -p test_bulk_manifest.py`. Create the target before feature implementation; every test must cite its allocated AC and be capable of failing. Record results under `docs/helix/04-build/evidence/bulk-update/`, with actual source/profile/runtime versions, original owner hashes, negative controls and explicit residuals. Actual Chromium is required for the browser rows; pure/static checks cannot substitute for native or browser outcomes.

## Data and Setup

Original fixture owner/path: UMF `docs/helix/03-test/fixtures/bulk-update/cases.json` and `model.json`, owned by US-902; all consumers pin the originals. Shared language-neutral fixture: three matching Customer identities2/10/11, active true, integer last_seen below100, fourth identity12 above100; batchSize2 yields [2,1]; registered set-active recipe plus original model/action/source/selection pins. Negative controls mutate one pinned input/guard/fence/permission at a time. Runtime rows require isolated owned databases/roles and current source/installer closure; synthetic issuers cannot qualify protected ordinary-person admission.

## Edge Cases and Failure Modes

Empty/no-op, exact bound/overflow, Unicode/large-integer, duplicate/unknown fields, tampering, missing authority, drift and uncertainty must keep their distinct contract outcomes. Native concurrency controls use actual two-connection barriers and independent effect/outcome queries.

## Build Handoff

### Native preparation race matrix

Implement these cases inside the existing mapped tests, retaining their canonical AC citations. Use original ordinary-role installed APIs and two-client barriers; separately query graph/control outcomes through an independently admitted observer. Administrative fixtures or mocked authority tokens cannot qualify these rows.

| Mapped test / criterion | Schedule or mutation | Independent assertion |
| --- | --- | --- |
| `coherent_cut` / US-046-AC1 | Pause between preflight, selection, Key and guard reads; a second writer updates/inserts matching rows. | Every retained value/identity/version belongs to one actual fixed cut; no mixed population. Preparation reports REPEATABLE READ/read-write and its original data connection; exact manifest agrees with that cut. |
| `authorized_review` / US-046-AC5 | Establish a data snapshot, then commit permission revocation before current-authority admission. | Original stale snapshot cannot authorize selection/sealing; current denial or explicit unsupported refusal, with no durable seal or disclosed hidden rows. |
| `authorized_review` / US-046-AC5 | Admit authority and hold its protections; concurrently revoke policy/role membership through each registered writer path. | Revocation waits through confirmed preparation completion or forces refusal before publication according to the selected native protocol; no unprotected authorization window. |
| `coherent_cut` / US-046-AC1 | Change accepted catalog/epoch after snapshot creation and before protected admission, including a lock wait. | Stale cut/catalog correspondence refuses or produces the original native serialization outcome; acquiring a late lock cannot be reported as a refreshed snapshot. |
| `sealing_integrity` / US-046-AC3 | Swap actor, installation, epoch, connection incarnation, transaction or cut on separate authority/data sessions; replay expired or foreign bridge evidence. | Original owner bridge refuses before a runnable seal; recomputed digests and valid unrelated sessions cannot issue custody. |
| `bounded_complete_work` / US-046-AC4 | Authority acquisition times out/cancels, or authority connection is lost while data preparation remains live. | No new selection/seal admission; original connections/exclusions retain their actual bounded settlement/recovery custody. No fresh hidden retry. |
| `sealing_integrity` / US-046-AC3 | Fail protected seal persistence after successful selection. Separately lose native seal COMMIT acknowledgement. | Confirmed rollback leaves no durable seal; uncertain completion returns ControlUnknown and settles only through original recoverControl, without rematerialization. |
| `authorized_review` / US-046-AC5 | Successfully seal, then revoke review/submit or execution permission. | Retained intent stays frozen; subsequent protected disclosure/admission is denied under current policy. Seal conveys no lasting execution right. |

Also exercise the originally installed selection entrypoint directly from the enrolled native caller without a live preparation bridge. It must refuse; same login, forged scope/token or an ordinary RC query handle cannot establish preparation custody. Verify that procedure-owner/coordinator grants do not authorize a denied initiating caller, and that a selected unsupported advanced policy/field-protection profile refuses before data disclosure. Map these controls to `authorized_review` / `@covers US-046-AC5` and `sealing_integrity` / `@covers US-046-AC3`.

For `sealing_integrity` / `@covers US-046-AC3`, use the same original issued store registration as the action registry and role enrollment. Swap only the logical store or namespace epoch while retaining a valid physical installation and action ticket; protected selection/sealing must refuse. A durable seal must retain full correspondence to that original registration, and cannot be admitted using caller-authored store bytes or a preparation-specific namespace.

The security owner's native bridge tests establish source/writer exclusion and exact original issuance. These story tests must exercise the composed bulk path; a bridge component receipt alone cannot establish US-046 completion.

UMF US-902/903, Weft US-008/009; original accepted catalog/security/selection-lowering admission and installed read runtime. Create red tests first; implement the contracted boundary; then independently qualify effects/refusals and source correspondence. Done requires every allocated AC's executed cited test and expected outcome, current upstream pins and complete applicable dependency evidence. This plan allocates tests; it does not report executed coverage.

## Formal and Diagnostic Proof

TD names the applicable bounded state analysis and negative controls. US-048-AC6 requires real receiver correlation with/without spans, protected-value pre-sink absence and sink-outage safety. Both formal source correspondence and native races remain required; model results or telemetry parsing alone are insufficient.
