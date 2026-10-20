---
ddx:
  id: truss.typed-api-host-adoption-plan
  type: implementation-plan
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.implementation-plan
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
    - id: ADR-005
      kind: informed_by
    - id: TP-001
      kind: informed_by
---

# Typed API host adoption execution plan

## Scope

Implement explicit synchronous `umf.access/1` registered action hosting and strict
native group receipt admission. Governing contracts are CONTRACT-004, CONTRACT-007
and CONTRACT-009; ADR-005 supplies complete request receipt recovery. US-040 and
US-043 supply atomicity and safe repeat requirements. The old `TrussTarget` read
surface remains available. Partial modes, generic query dispatch, protected-host
qualification and release publication are outside this slice.

## Implementation slices

| Order | Slice | Gate |
| --- | --- | --- |
| 1 | Close native result outcome/disposition/durability and replay-observation parsing | Unit adversarial controls and actual native malformed-result rollback preserving earlier caller work |
| 2 | Add explicit schema/action registrations and owned exclusive connection leases | Unsupported requests before dispatch; source mismatch; active foreign transaction untouched |
| 3 | Integrate original-source observation and registered native group handlers | Actual accepted document/action correspondence, native key mapping and complete canonical request custody |
| 4 | Validate complete staged wire response before settlement and receipt release | Exact original-backend COMMIT acknowledgement; malformed/lost responses unknown; original cancellation preserved; no retry |
| 5 | Qualify generated synchronous clients against installed native groups | Single, whole atomic batch, no-op, late refusal rollback, validation, replay/conflict and lost-ack recovery |
| 6 | Review source and HELIX, record evidence, commit and push a PR | Sol review resolved; local macOS tests pass; only scoped files staged |

Slice 1 can proceed independently; slices 2–4 precede native host qualification.
No stage promotes pending caller-owned group effects to committed durability.

## Execution contract

The user's instruction authorizes implementation, local tests, commit, push and
PR creation. Luna implements; latest Sol plans and reviews. No token spending
ceiling was supplied. Keep work isolated from the original checkout's unrelated
uncommitted changes. The implementation branch starts at Truss
`6158dbbc9e306cb85d5290a9af4d22189f893ea9`.

The selected generated-client source is UMF PR #40 at
`1231aea28a998a504fed941c11790c86b2f4f0cd`, CONTRACT-079 and its actual Python
generator. Generated client wire requirements are authoritative for this profile;
Truss does not invent another receipt ABI. Do not retry mutation callbacks,
reconstruct receipts from current state or create an adapter replay store.

## Validation plan

Use focused Python unittest controls, existing native group/receipt tests and new
actual generated-client/native integration. Reuse the repository's released
PostgreSQL18.6 runtime and ordinary-role fixture on macOS; record the exact
Python, driver and libpq versions. CI remains GitHub Actions Linux. No duplicate
platform runs or local Docker runner are required. Collect native object/journal
observations and owned-runtime cleanup proof. Independent effects distinguish
commit, rollback and unknown acknowledgement.

## Continuation evidence

Implementation and local qualification are complete for the bounded ordinary-ACL
transport and registered create-action fixture. Latest Sol review found no
remaining actionable source issue after its corrections. The source-pinned
[verification receipt](evidence/typed-api-host-adoption/verification.json) records
executed checks; this plan does not qualify a general action interpreter or every
possible host callback registration.
The [Praxis consumer review](https://github.com/DocumentDrivenDX/umf/pull/40#issuecomment-6300376302)
was supplied during implementation. Its eight findings are reconciled on the UMF
PR. Truss follows its relevant host obligations: return definite refusals as wire
envelopes, preserve original cancellation for application-owned recovery capture,
use action-declared precondition identities, enforce the published batch cap, and
represent unknown atomic settlement as a whole-response uncertainty envelope.
The experimental client profile does not qualify native Truss execution without
the independent tests in this plan.

### Executed parser checkpoint — 2026-10-20

The strict parser component suite passed eight tests; actual native malformed
output containment passed one; existing receipt visibility/replay passed two;
and the existing changed-origin/request-none regression passed one. These are
focused source-tree checks, not complete host transport qualification.

Tuple: macOS27.0.1 ARM64, CPython3.11.17, psycopg3.3.6, libpq180006,
`pgserver-pg18==18.6.1`, PostgreSQL18.6. Source base is recorded above; the PR's
final commit identifies this patch. Native teardown removed the owned
`truss-public-catalog-*` data directories; no `postmaster.pid` remained in the
scoped runtime directory.

Component command:

```sh
PYTHONPATH=packages/python/src:packages/python/tests \
  /private/tmp/truss041-final-env-20261020/bin/python -m unittest -v test_group_result_wire
```

Native selectors: `test_group_result_wire_native.GroupResultWireNativeContainmentTests`,
`test_receipt_visibility_native.ReceiptVisibilityTests`, and
`test_group_create_native.PublicCreateGroupTests.test_changed_request_origin_and_none_has_no_cache`.
They used the same Python/PYTHONPATH and unittest loader, with the process-local
pgserver runtime/lock redirected to
`/private/tmp/truss-group-result-wire-pgserver-runtime` and a fresh
`fasteners.InterProcessLock` there. Scoped native execution required sandbox
escalation for pgserver's macOS process enumeration. This changes no committed
runtime policy. The new native test discovers Bun from `TRUSS_BUN_EXECUTABLE`,
then PATH; this local run selected `/opt/homebrew/bin/bun`.

### Executed transport checkpoint — 2026-10-20

| Gate | Executed result |
| --- | --- |
| Source transport/parser component controls |28 passed:20 transport controls plus8 strict wire controls |
| Unpublished local wheel | Builds offline; packaged runtime source bytes match; the same28 component controls pass against the installed wheel |
| Actual generated SyncClient/SyncActions + native ordinary-role groups | Passed one integrated create-action scenario: fresh accepted source, decoder snapshots, native advisory apply/rollback then fresh apply, single create, original committed replay, unequal-request conflict, whole atomic batch, exact ordered replay and changed-flag conflict, unsupported partial mode before leasing, late-failure rollback, actual COMMIT followed by injected acknowledgement loss and explicit replay, original postdispatch cancellation plus rollback |
| Native malformed-result containment | Passed; earlier caller temp-table work survives, malformed attempt/receipt rolls back, same request freshly applies and commits once |
| Native replay compatibility | Existing receipt visibility/replay controls pass |
| Native no-op compatibility | Existing bulk-update no-op test preserves versions, timestamps and journal through strict result decoding; component empty receipt/counts admission passes |
| Python dependency gate | Final source checker passes;18 permitted/forbidden import/cycle/dynamic-hook controls complete as expected |
| Owned-runtime cleanup | No owned test roots, postmaster PID files or matching PostgreSQL processes remain |

The final aggregate ran six native cases in69.185s against the final source;
[its log](evidence/typed-api-host-adoption/native-tests.log) retains exact selectors
and results. The source-pinned verification receipt records the installed-wheel
checksum, dependency checker and runtime/source identities. PostgreSQL's SQL
version is18.6;18.6.1 identifies the pgserver wheel.

Native generated-action commands use the parser checkpoint's scoped pgserver
runtime override and Python/PYTHONPATH, plus `TRUSS_UMF_SOURCE_ROOT` pointing to
UMF commit1231aea28 and `TRUSS_BUN_EXECUTABLE` on PATH. Selectors:

- `test_action_transport_native.NativeGeneratedActionTransportTests.test_generated_sync_actions_use_owned_native_group_and_exact_receipts`
- `test_bulk_create_sql_native.BulkUpdateSqlTests.test_noop_batch_preserves_versions_timestamps_and_journals`

Local native host limits were statement10000ms and whole invocation30000ms.
The installed wheel is an unpublished0.0.41 source candidate; its checksum does
not relabel the public0.0.41 release. CI adds the two focused component selectors
to the existing Linux runtime job; no second OS job is introduced.

Native generated no-op/update/delete/link action mappings, complete protected
execution, partial batches, generic query dispatch, exhaustive host/resource and
platform qualification remain outside this tested create-action registration.
The native no-op regression and component empty-counts control do not imply a
qualified generated touch/update handler. Every additional registration must
qualify its original source/native result mapping under the same contract.

## Exit criteria

All implemented public operations conform to their registered bounded profile.
Actual generated-client/native scenarios pass, strict parser controls pass, Sol
review findings are resolved or explicitly deferred with justified scope, and the
PR documents unsupported modes and tested tuple. No claim of full engine,
protected security or release qualification follows from this slice.

## Risks and rollback

A lease or settlement failure can leave effects uncertain: retain the original
request identity, do not retry, and discard unsafe connection admission. A wrong
source or callback registration can mis-map meaning: refuse before effects and
require exact native/source correspondence. Rollback of this code change removes
the new transport; existing native receipts and historical evidence retain their
meaning and must not be rewritten. The original caller-owned transaction API
continues to report pending results.
