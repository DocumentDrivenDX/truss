---
ddx:
  id: US-049
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

# US-049: Qualify the bounded Python action gateway

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


**Feature:** FEAT-003. **Requirements:** PAP-TRS-01, PAP-TRS-04, PAP-TRS-05. **Priority:** Required predecessor to US-047. **Status:** Draft.

## Story

As a Data platform engineer, I want a qualified bounded Python UMF-action gateway and trusted delegated human context, so queued UPDATE batches execute the original declared action semantics through Truss's protected boundary.

## Context

Ordinary Truss mutation APIs and the separate UMF TypeScript reference consumer are not a Python action gateway. This story supplies the exact bounded subset consumed by CONTRACT-013, including native attempt/control composition; it does not require a complete standalone general action executor.

## Walkthrough

1. Install original owner schemas/preparation and complete native/authority dependency pins.
2. Register the bounded action gateway and executor-controlled action revisions.
3. Admit a job-scoped original human/service context and native attempt before effects.
4. Execute under the existing protected outer transaction and inspect original outcomes.

## Acceptance Criteria

- [ ] **US-049-AC1** — Given original UMF model/action/preparation and native source pins, when the bounded Python set-action gateway registers, then registry/current declaration/Field/Key/frame/role/effect inspection uses owner semantics and unsupported inputs/handlers/unknown obligations refuse without claiming a standalone general tx executor.
- [ ] **US-049-AC2** — Given an authenticated initiator, trusted job-scoped delegation and separately authenticated worker, when gateway admission/commit runs, then person-required uses the original human with current membership/delegation checks; client-retained actor text and unauthorized workers cannot issue delegation or stop a valid job.
- [ ] **US-049-AC3** — Given a prepared atomic batch with all item replay locks preheld, when each internal action executes, then exact required set effects/attempted frame access/constraint/verification and original tx results compose under one outer transaction with no per-item commit/retry or independently callable reserved tokens.
- [ ] **US-049-AC4** — Given the opened original effect/control transaction and connection incarnation, when independent original attempt registration precedes job/business locks and dispatch, then actual installation/epoch/driver/xid custody, admission marker and immutable control result persistence are confirmed; lost registration/result acknowledgement or absent original termination cannot authorize dispatch, reclaim or invented rollback.
- [ ] **US-049-AC5** — Given independent ordinary-role PostgreSQL witnesses and owner-authored conformance fixtures, when the Python gateway is qualified, then exact value admission, authority/retirement/replay/no-op/rollback/outcome behavior agrees with the owner contract and cannot be replaced by the TypeScript reference consumer or privileged fixture writers.

## Edge Cases

Spoofed initiator, unknown callback/profile, reserved outsider token, crossed namespace, stale source, unsupported effect and uncertain original native custody all refuse without granting ordinary consumer registry writes.

## Test Scenarios

| Scenario | Criterion | Input/state | Expected result |
| --- | --- | --- | --- |
| gateway_registration | US-049-AC1 | Original owner bulk fixture with the named role/registry/control mutation | registry/current declaration/Field/Key/frame/role/effect inspection uses owner semantics and unsupported inputs/handlers/unknown obligations refuse without claiming a standalone general tx executor. |
| delegated_human | US-049-AC2 | Original owner bulk fixture with the named role/registry/control mutation | person-required uses the original human with current membership/delegation checks; client-retained actor text and unauthorized workers cannot issue delegation or stop a valid job. |
| outer_transaction_gateway | US-049-AC3 | Original owner bulk fixture with the named role/registry/control mutation | exact required set effects/attempted frame access/constraint/verification and original tx results compose under one outer transaction with no per-item commit/retry or independently callable reserved tokens. |
| native_attempt_custody | US-049-AC4 | Original owner bulk fixture with the named role/registry/control mutation | its original installation/epoch/driver/xid correspondence and admission marker commit are confirmed before any effects; deadlock, unknown control commit or absent original termination evidence cannot authorize execution or reclaim. |
| gateway_native_conformance | US-049-AC5 | Original owner bulk fixture with the named role/registry/control mutation | exact value admission, authority/retirement/replay/no-op/rollback/outcome behavior agrees with the owner contract and cannot be replaced by the TypeScript reference consumer or privileged fixture writers. |

## Dependencies

UMF US-902/903, original CONTRACT-900/901/902/903/904 schemas and corpus; Truss CONTRACT-013, original protected installation/current-authority/catalog/value/Key and connection-lifetime/native observation dependencies. US-046 supplies manifest sealing; its pure/control preparation can proceed independently. SD-003 governs ownership and ADR-003 Python-first implementation.

## Out of Scope

General handler/create/delete/relationship execution, actor-profile change, JavaScript sidecar, native support without original evidence, distributed effects and automatically resumed/retried failed jobs.
