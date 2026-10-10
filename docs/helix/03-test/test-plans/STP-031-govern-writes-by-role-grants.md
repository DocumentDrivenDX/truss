---
ddx:
  id: STP-031
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-031
      kind: informed_by
    - id: TD-031
      kind: informed_by
    - id: SD-008
      kind: informed_by
---

# STP-031: Transaction-local roles

## Story Reference

US-031, TD-031, SD-008, TP-001 and CONTRACT-002/005/007. Tests are planned.

## Scope and Objective

Prove native grants and trusted role capture with transaction reset on every advertised connection profile.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-031-AC1 | `powerless_connector_cannot_write` | Direct/inherited write attempt fails and leaves canonical/journal effects absent | `@covers US-031-AC1` | Native integration | `tests/host/roles.test.ts`; explicit connector/membership grants |
| US-031-AC2 | `local_writer_role_commits_and_is_audited` | Authorized local w role writes; journal trusted db_role is w despite forged origin or definer owner | `@covers US-031-AC2` | Native integration | Same file; writer/definer profile |
| US-031-AC3 | `next_transaction_has_no_leaked_role` | Same connection's next transaction is powerless after commit/rollback; unauthorized role selection refuses | `@covers US-031-AC3` | Native integration | Same file; reused connection and separately qualified pooler |

## Executable Proof

Future command `bun test tests/host/roles.test.ts` requires harness/files and finalized role profile. Tests cite IDs and pin server/adapter/pooler/grants/capture mechanism. Missing pooler matrix is unverified, not implied by direct connection success.

## Data and Setup

Independent observer checks role, canonical/journal state and reset. Use distinct connector/writer/unauthorized identities. Caller adoption fixture preserves an existing authorized context without broadening grants. Actual transaction boundaries are observed.

## Edge Cases and Failure Modes

Cancellation/rollback reset, pooled reuse, definer search path and origin spoofing. Session-global setup cannot satisfy transaction-local isolation. Grant changes invalidate matching support receipts. Ordinary writers cannot modify trusted role capture.

## Build Handoff

Finalize context/grants/capture contract, write red native tests, implement adapters and qualify actual connection profiles. All criteria block role-profile closeout. Host administration remains separately authorized work.
