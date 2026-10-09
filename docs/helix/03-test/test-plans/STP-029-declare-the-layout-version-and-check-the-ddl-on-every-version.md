---
ddx:
  id: STP-029
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-029
      kind: informed_by
    - id: TD-029
      kind: informed_by
    - id: SD-007
      kind: informed_by
---

# STP-029: Native layout compatibility

## Story Reference

US-029, TD-029, SD-007, TP-001 and CONTRACT-001/004/008. Tests are planned.

## Scope and Objective

Prove fail-closed startup compatibility and complete native layout checks per supported target.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-029-AC1 | `incompatible_major_never_starts_writer` | Installed mismatched major refuses before any canonical/derived/journal or namespace change | `@covers US-029-AC1` | Native integration | `tests/layout/compatibility.test.ts`; marker and sentinel fixture |
| US-029-AC2 | `every_claimed_target_passes_layout_check` | Baseline/generated DDL and independent check pass on each advertised exact server target; missing target remains unverified | `@covers US-029-AC2` | Native integration | Same file; isolated native matrix |
| US-029-AC3 | `probe_manifest_covers_required_behavior` | Keys/endpoints/deletion/exact values/partition behavior/no-default checks detect deliberately corrupted fixtures | `@covers US-029-AC3` | Native integration | Same file; independent probes and corruption witnesses |

## Executable Proof

Future command `bun test tests/layout/compatibility.test.ts` requires harness/files. Receipts pin SQL/model/check/layout/server/runtime digests and exact outcomes. Historical spike passes do not substitute for current candidate runs.

## Data and Setup

Use disposable baseline/generated namespaces and independent catalog/behavior assertions. Corrupt constraints/default partition/marker individually to establish check sensitivity. Ordinary writer performs integrity probes; installer role is separately recorded. Sentinel state proves startup refusal is nonmutating.

## Edge Cases and Failure Modes

Missing/malformed marker, incompatible minor capability inventory, unsupported server and changed installed surfaces receive explicit refusal/unverified outcomes. Native numeric mathematical equality cannot prove lexical exactness. Startup never patches a namespace to obtain a green check.

## Build Handoff

Resolve marker/minor policy, define probe inventory/red fixtures, implement preflight and run complete matrix. All criteria block claimed compatibility. Existing-data migration remains separate governed work.


## Same-major inventory and explicit upgrade controls

Install an independently qualified source layout and record its complete original object/routine/privilege/codec inventory. Connect an implementation whose declared supported range includes that exact profile and expect admission only after native correspondence. Then retain the major version while independently changing a required routine body, grant or codec artifact: a same-major marker cannot authorize operations, and the read-only verifier must report drift/unavailable without repairing it. Separately test an intact same-major layout outside the implementation’s declared range; refuse before mutation.

Status inspection and ordinary connection/import must issue no installer or migration DDL. Only an explicitly invoked registered upgrade route may change the layout, under CONTRACT-008’s dedicated administrative ownership, preservation and original-attempt recovery protocol. Confirmed upgrade still requires fresh target parity before readiness; a ledger/version increment alone cannot satisfy it. Run every supported server/deployment tuple independently with the exact generated DDL and complete behavioral check. Historical spike success on a subset or version string is insufficient. These controls remain planned native/driver tests.
