---
ddx:
  id: STP-049
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-049
      kind: informed_by
    - id: TD-049
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: CONTRACT-013
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# STP-049: Qualify the bounded Python action gateway

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

US-049, TD-049, SD-003 and CONTRACT-013; exact shared values/actions/bulk profiles are the original UMF contracts.

## Scope and Objective

Qualify the bounded Python gateway needed by US-047. All mappings are planned; no existing runtime/TypeScript reference pass is reused as native Python evidence.

## Acceptance Criteria Test Mapping

| Criterion | Planned test | Asserted behavior | Canonical citation | Layer | Planned file |
| --- | --- | --- | --- | --- | --- |
| US-049-AC1 | `gateway_registration` | registry/current declaration/Field/Key/frame/role/effect inspection uses owner semantics and unsupported inputs/handlers/unknown obligations refuse without claiming a standalone general tx executor. | `@covers US-049-AC1` | Native integration | `packages/python/tests/test_bulk_action_gateway.py` |
| US-049-AC2 | `delegated_human` | person-required uses the original human with current membership/delegation checks; client-retained actor text and unauthorized workers cannot issue delegation or stop a valid job. | `@covers US-049-AC2` | Native integration | `packages/python/tests/test_bulk_action_gateway.py` |
| US-049-AC3 | `outer_transaction_gateway` | exact required set effects/attempted frame access/constraint/verification and original tx results compose under one outer transaction with no per-item commit/retry or independently callable reserved tokens. | `@covers US-049-AC3` | Native integration | `packages/python/tests/test_bulk_action_gateway.py` |
| US-049-AC4 | `native_attempt_custody` | actual installation/epoch/driver/xid custody, admission marker and immutable control result persistence are confirmed; lost registration/result acknowledgement or absent original termination cannot authorize dispatch, reclaim or invented rollback. | `@covers US-049-AC4` | Native integration | `packages/python/tests/test_bulk_action_gateway.py` |
| US-049-AC5 | `gateway_native_conformance` | exact value admission, authority/retirement/replay/no-op/rollback/outcome behavior agrees with the owner contract and cannot be replaced by the TypeScript reference consumer or privileged fixture writers. | `@covers US-049-AC5` | Native integration | `packages/python/tests/test_bulk_action_gateway.py` |

## Executable Proof

Planned command: python3 -m unittest discover -s packages/python/tests -p test_bulk_action_gateway.py. Run the native rows against the original installed candidate Python wheel on isolated PostgreSQL18.6 (`pgserver-pg18`18.6.1) ordinary-role instances, with exact adopted runtime/layout/source pins and independent observer connections; require complete installer/authority/dependency closure. Existing pure registration/value tests do not execute these native rows.

## Data and Setup

UMF owns docs/helix/03-test/fixtures/bulk-update/model.json and cases.json. Pin original schemas/preparation producer/version/complete source bytes. Mutation controls replace a human with service-only identity, alter a binding/effect, attempt raw out-of-frame writes, reacquire an earlier replay lock, lose control commit acknowledgement or mismatch original xid/session. Observe zero unauthorized effects, complete exact rollback/outcomes and safe custody.

## Edge Cases and Failure Modes

Unknown/unsupported registry callback or producer, wrong delegation/store/epoch, current revocation, retired revision, reserved outsider token, stale source, per-item retry and control-route deadlock all have independent rejection witnesses. Native termination uncertainty is not rollback.

## Build Handoff

### Native action-role and discovery controls

Use the unchanged original products `set-name` declaration, including `umf.actions.roles/1` role `bulk-editor` and `person-required` attribution. Install membership and discovery bindings through the original protected administrative boundary. Their absence in the RC catalog/data exporter is an explicit negative fixture, never positive action authorization.

| Mapped test / criterion | Setup or race | Independent assertion |
| --- | --- | --- |
| `gateway_registration` / US-049-AC1 | Missing, foreign or unknown action-role profile/binding; owner preparation reports interpreted authorization. | Execution registration/admission refuses; a checked declaration obligation cannot issue membership or native authority. |
| `delegated_human` / US-049-AC2 | Initiating human has module read/write permission but lacks the original `bulk-editor` membership. | No action effects or invocation rights; adding role names to request/manifest or using the worker's membership cannot authorize the human. |
| `delegated_human` / US-049-AC2 | Original qualified human holds one of multiple exact declared roles; another human has only a similar spelling. | At-least-one semantics authorize only the matching original human; role IDs are exact, without case folding or inferred native-name aliases. |
| `gateway_native_conformance` / US-049-AC5 | Revoke the human's matching role before admission; separately attempt revocation after native admission while the action commits. | Pre-admission revocation denies; admitted exclusion follows the qualified native ordering through commit. No earlier membership snapshot or worker role substitutes. |
| `gateway_native_conformance` / US-049-AC5 | Current action role exists but independently installed replay-discovery binding is absent/disabled; then change/retire the action revision. | Denial occurs before token presence observation; declaration or revision changes cannot install discovery permission. |
| `delegated_human` / US-049-AC2 | Service-only initiating context or lost original human/job/store/manifest delegation. | `person-required` refuses; separately authenticated authorized service remains a worker acting under the original binding, never the human principal. |
| `native_attempt_custody` / US-049-AC4 | Register one logical store through the original protected issuer, reopen connections and register another action revision; try caller-authored bytes, a foreign installation and a fenced namespace epoch. | Registry, Subject/roles, delegation, jobs and replay consume the same issued store boundary. Reopen/revision preserves its identity and token recognition; forged, foreign or fenced registrations refuse. Physical installation identity cannot substitute for logical store issuance. |
| `native_attempt_custody` / US-049-AC4 | Lose store-registration COMMIT acknowledgement, then inspect through the original native installation/registration attempt recovery under CONTRACT-007; separately restore an unverified store incarnation. | Unknown issuance cannot admit effects or mint a replacement namespace. Only confirmed original registration admits consumers; unverified restore correspondence refuses. Fencing or epoch replacement preserves original recovery custody and does not reset token recognition. CONTRACT-904 recoverControl cannot substitute for registration recovery. |

These controls compose with actual native group/frame/outcome tests. They do not reinterpret or replace CONTRACT-901 role, attribution or discovery semantics.

Deliver before US-047 batch effects. US-048-AC7 bounded model may precede the gateway as a separate modeling substep; original native dependencies remain prerequisites. Done requires every cited executed native witness and source/profile correspondence, not this allocation table.
