---
ddx:
  id: PLAN-EMBEDDER-E2-E8-001
  type: implementation-plan
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: PLAN-EMBEDDER-E0-E1-001
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-005
      kind: informed_by
    - id: CONTRACT-006
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# Remaining embedder delivery

## Scope

Complete the accepted remainder of the original Hohfeld feedback, then review,
qualify the exact installed package and release it. The owner authorizes all
these slices. The upstream UMF `truss-embedder-feedback-plan.md` supplies requests;
Truss's selected contract supplements own execution meaning. E0/E1 is already
published; it does not close the remaining import, catalog, registration,
preview, lifecycle, audit or consumer-workflow requirements.

Governing authorities are [architecture](../02-design/architecture.md),
[journal](../02-design/contracts/CONTRACT-002-journal.md),
[catalog](../02-design/contracts/CONTRACT-003-catalog-revision.md),
[mutations/import](../02-design/contracts/CONTRACT-004-mutation-and-conformance.md),
[module isolation](../02-design/contracts/CONTRACT-005-module-isolation.md),
[feed](../02-design/contracts/CONTRACT-006-change-feed.md),
[embedding](../02-design/contracts/CONTRACT-007-embedding-and-execution.md),
[installation](../02-design/contracts/CONTRACT-008-layout-bootstrap.md) and
[group locks](../02-design/contracts/CONTRACT-009-group-planning-and-locks.md).
The [E0/E1 plan](embedder-e0-e1-plan.md) retains the earlier exact evidence.

## Existing behavior and adopted variants

| Original ask | Existing selected behavior | Remaining completion criterion |
| --- | --- | --- |
| Import cost and cap | Legacy tagged reports, partial progress, source provenance and 128-record limit exist; owned atomic import is a separate route | Explicit batched builder/executor with fixed client count per chunk; qualify 1,024 records without changing legacy settlement |
| Reader overhead | Global/document revision probes and accepted-document source revision exist | One-call conditional visibility validator and module source acceptance revision |
| Group condition cap | E1 qualifies 3,072 conditions under the 1,024-operation profile | Retain exact bounds/precedence and regression gates |
| Name/alias/type/index issues | Valid nameless IDs, safe alias documentation, typed refusals/codes and collision attribution are qualified | Preserve these; unsupported executable input still refuses before publication |
| Delete and condition-only checks | Restrictive typed dependency refusal and separately selected owned cascade exist | Document/test that policy; add advisory condition-only preview with honest snapshot basis |
| Pending/rollback read token | Existing reached controls cover another connection before commit, after rollback and after commit | Repeat exact lifecycle controls; preview basis must never be a mutation receipt |
| Import result/value/origin/load | Tagged partial/durability report and immutable record provenance exist | Parity for eligible value/facet/source validation; exhaustive types; transactional zero-create load-attempt audit |
| Group journal grant/read | Per-entity history and replication feed exist | Separate audit grant and complete committed group/load pages including deleted entities |
| Install/status/grants | Fresh installation and module grants exist; role names initially returned; status is administrative | Serialized installer with typed outcomes, authorized role recovery, minimal person status and atomic indexed grant-batch errors |
| Registration evolution/revision | Core optional additions and catalog revision probes exist | Known paired DDD optional addition, document/global compare-and-set and cheap typed registrar probe |

The nameless-registration rejection request is superseded by valid stable-ID
execution. Unconditional cascade, automatic migration/reset, reusable authority
tokens and an invented commit timestamp/order remain rejected variants. A
conditions-only mutation is implemented as advisory preview, with no write or
receipt. These are explicit dispositions, not unreported dropped requirements.

## Shared Constraints

- Use Python 3.11+, PostgreSQL 18.6 and the selected exact UMF/Weft owner assets.
  UMF owns DDD meaning and validation; Weft owns SQL. Preserve unknown content,
  original bytes and complete typed outcomes.
- Retain current role/policy checks, complete historical owner unions, head/key/
  endpoint lock order, precondition precedence and source/replay identity.
- Caller transactions remain pending. Engine chunk commits require original
  acknowledgement; unknown outcome is never inferred rollback or retried.
- Existing 8-MiB import envelope, 1-MiB individual payload, group/resource and
  10s SQL/30s operation limits remain independent. Count is not byte permission.
  New batch admission bounds 4,096 records and 256 MiB of original input plus
  source bytes. Native transaction counters bound retained pending work and
  roll back with it; host-local adopted-handle budgets count submitted work
  without rewinding on contained rollback. Detach/re-adoption has a new host
  scope while retaining any open native transaction's pending-work counter.
- Hosted CI is Linux only. Local native verification uses the development host's
  native platform by default. Historical cross-platform receipts remain historical.
  No complete protected-security or managed-service qualification is inferred.

## Implementation Slices

| Slice | Implementation boundary | Dependency | Required evidence |
| --- | --- | --- | --- |
| E2a | Map new source/API imports before runtime edits; keep existing legacy imports exact | E1 | Python module checker and all 18 allow/refusal controls pass; explicit new imports only |
| E2b | `BatchedImportInput`, `BatchedImportRuntimeContext` and batch builder; 1,024 input, declared chunks at most 128 initially | E2a | Source identity, exact authored values, original indices and all envelope limits; builder count independent of homogeneous record count |
| E2c | One guarded native chunk function with per-record containment and same-transaction provenance/load hook | E2b | Independent old/new parity at 128, then 1,024; no silent atomicization; complete outcomes and actual chunk settlement |
| E3 | Conditional reader snapshot/unchanged API, opaque validator and per-module `sourceCatalogRevision` | E2a | Warm hit one native call without full projection rebuild; authority/source race negatives and miss/hit parity |
| E4 | Document/global expected revisions, registrar probe and exact known DDD optional correspondence | E2a | Independent-document success, same-document conflict, exact replay; additive optional compatibility with unknown-content preservation |
| E5 | `GroupConditionPreviewInput` → `PreviewObserved`/`PreviewRefused`, with `PreviewObservationBasis` | E1 | One data snapshot, fresh authority, read-only compatibility, no row locks/reservations/effects/receipts; unchanged delete/token tests |
| E6 | `PersonRuntimeStatus`, `AdminInstallRecovery`, installer exclusion and atomic module-grant results | E2a | Concurrent installer, rollback/unknown acknowledgement, restricted role recovery and full invalid-batch rollback |
| E7 | `MutationGroupAuditPage`, `LoadAuditInvocationSummary` and separate per-chunk `LoadAuditPage`, typed continuations/refusals, independent grants and transactional load-attempt rows | E2c, E6 | Complete committed groups only, full owner-union authority, zero-created attempts, deleted-entity discovery and no fake commit order |
| E8 | Installed consumer replay, statement/latency evidence, review and publication | E2–E7 | Full original request checklist closed against exact source/wheel; Linux release CI and fresh artifact verification |

The conditional catalog facade is additive:
`reader_catalog_if_changed_in_transaction(tx, validator=None, maximum_count=65536,
maximum_bytes=1048576)` returns `ReaderCatalogSnapshot(catalog, validator)` or
`ReaderCatalogUnchanged(validator)` inside `Outcome`, plus existing typed catalog
invalid/refused/unavailable results. A validator is not an access credential.
Keep the unconditional interface intact. The new batched import routes return
`BatchedImportExecutionResult`, containing the complete original tagged import
result and an optional `EmptyLoadDisposition`. An admitted zero-record load has
its own pending/committed/rolled-back/commit-unknown/transaction-unresolved
settlement with evidence; it never fabricates a record index or changes legacy
nonempty batch accounting. Catalog acceptance adds optional
`expected_revision` and `expected_documents`, using
`CatalogDocumentExpectation(document_id, source_catalog_revision)` with zero for
required absence. Expectations cover exactly submitted documents when selected.

Preview uses `preview.py`/`_preview_runtime.py` and native
`preview_group_conditions(bytea,bytea,text,text)`. Snapshot-bound data/source/
predicate reads require the actual statement snapshot. The selected public wrapper
is VOLATILE: it invokes one private STABLE truth statement that captures its own
revision and snapshot, then performs a separate VOLATILE ordered authority pass
and fresh basis/person checks before publication. A STABLE outer wrapper cannot
establish that fresh release boundary. Require a native revocation committed
during the active observation to withhold all conditions, alongside a concurrent
data-update control proving one truth snapshot. Shared pure validation may be reused; mutation
locking/effect helpers must not execute in preview.

Lifecycle uses `lifecycle.py`/`_lifecycle_runtime.py`; `InstallRefused` names
known contained installer preflight outcomes, without absorbing transport/retry
or unknown transaction outcomes. Authorized native role
recovery is `admin_install_recovery()`. Load/audit uses
`load_audit.py`/`_load_audit_runtime.py` and the owned load-audit SQL sources.
Mutation audit uses `MutationGroupAuditPage`/`MutationGroupAuditListingCursor`;
`page_mutation_group_audit` and `page_import_load_audit` provide qualified
module-scoped discovery with whole mutation groups or one import-invocation
summary per page, exact filters and a frozen
committed frontier. Pages show newest retained observations first, with stable
descending continuations; transaction IDs are eligibility/tie facts, never a
substitute for commit time or the primary display order. Asserted action is the
original exact `x-action` entry. The load companion exposes load ID, authenticated
initiator, retained observation time and explicit created/skipped/rejected counts. Test
`LoadAuditInvocationSummary` independently of per-chunk `LoadAuditPage` details,
including the 1,024-chunk boundary and privately retained asserted origin for
zero-created loads. Test
continuations through the public Python adapters, including historical business
keys over compact plans and deleted entities, rather than only native SQL bytes.
Parent facade integration owns exports, selected native function/grant inventories,
installation/manifest regeneration and the import same-transaction hook. New
private helper EXECUTE is revoked from PUBLIC; no direct-store privilege shortcut.

The selected audit page is metadata-only and independently granted: a journal-only
actor with complete current auditor membership can read it without ordinary data
read access. A trusted installer/administrator configures the separate NOLOGIN
per-document/module auditor role; module writers cannot self-enable audit. Require
fresh audit authority for the complete retained historical owner union. Expose
IDs, operation kind, actor, explicit action, observation time and counts. Cover
all selected operation groups, unchanged operations and cascade descendants in
addition to load attempts; a load-only reader cannot close R20. Qualify filters
for qualified module independently of entity, retained type/entity key, person,
original `x-action`, observed time and group identity;
a member match selects the whole group. Historical business keys require original
revision/key interpretation, never a live lookup. Exclude raw origin and input/key/property/before-after/source values. Any future
value-bearing projection additionally requires ordinary read authority. Minimal
person status recognizes audit-only enrollment without exposing catalog data.

## Required Validation

The cases below are mandatory acceptance gates. New test method/module names
are recorded with execution evidence; a listed gate is not a claim it ran.

| Gate | Concrete expected result |
| --- | --- |
| Import parity | Compare graph, key/reservation, source, journal/feed, original-index report and durability against legacy behavior at 128; duplicate identical/conflicting payloads, existing live and committed-deleted identities, invalid first/middle/last and mixed object/edge inputs |
| Import limits and scale | 32/64/128/1,024 records on the same schema/transport; 1,025 count refusal; byte/individual value and cumulative transaction limits; no effects on refused envelope |
| Import correctness | Required/scalar/container/facet and source timestamp profiles, malformed identity versus skip precedence, unknown-property retention/refusal, endpoint/multiplicity finalization, failed provenance insert, cancellation and lost chunk COMMIT acknowledgement |
| Import cost | Separate complete builder+chunk client statement count, BEGIN/COMMIT/adoption, network round trips, elapsed distribution, server work and memory; no whole-schema copy or decode per record; no unmeasured tenfold speed claim |
| Conditional catalog | First snapshot, exact unchanged hit, new source, retirement/reactivation, grant/revoke/recursive role changes, hidden declaration/item/key/endpoint dependency changes, different caller/installation/release token, malformed/oversized token, byte/count limit, read-only caller, authority drift before release |
| Registration compare-and-set | Two unrelated documents succeed with separate expectations; concurrent same-document updates give one conflict; zero expectation creates only absent document; stale dependency/global expectation rejects before effects; exact replay returns original result and changed expectation conflicts |
| DDD evolution | Original UMF known `umf.ddd` 0.1.0 validation; paired core optional Field/member append; previous IDs/data/unknown bytes preserved; missing pair, wrong scope/version/type, changed prior field, required addition and unrelated extension changes refuse without head/data/history effects |
| Registrar and lifecycle | Registrar/nonregistrar advisory answers; current reauthorization on accept; admin/person/outsider status with head zero/absent/current/incompatible/tampered install; no person role names/install ID; concurrent installer busy, committed already-installed, rollback/recovery and unknown acknowledgement |
| Module grant batch | Valid multi-module atomic batch; mixed valid/invalid collects original indexed permitted errors and changes nothing; unknown roles/modules and duplicate selections refuse; no protected activation bypass |
| Preview | All five predicates including 153 and 3,072 condition profiles, count/byte refusal, original ordered failures, missing/null distinction, read-only native execution, concurrent data change between predicates, source-basis drift and revocation, no durable rows/markers/receipts or graph/key mutation locks even on failure |
| Delete/token regressions | Existing restrictive dependency typed leaf, no hidden edge identity/count, owned cascade complete closure; originating/other connection pending token before commit, after rollback, after commit and unknown commit; preview basis never accepted as receipt |
| Audit/load | Audit-only actor with complete owner-union grant succeeds with metadata only; ordinary reader without audit grant denied; incomplete audit owner union or revoked dependency denies whole page; raw origin and all input/key/property/source values excluded; writer cannot self-grant; all-operation groups including unchanged operations and cascades; independent qualified-module, type/entity key, person, original x-action, observation-time and group filters; newest-observed-first pages/ties/descending continuation; load initiator/observed-time/explicit created-skipped-rejected counts; complete multi-entity and deleted groups, concurrent commits below safe frontier, deterministic pagination, oversized group refusal, zero-created/skipped/rejected loads, multiple engine chunks, caller rollback and unknown durability |
| Consumer replay | Exact installed Hohfeld catalog/Northwind/Pizza register, seed, list, open, edit and graph import with Bun/Node absent from deployment PATH; typed audit/status/preview/CAS results and complete import reports; persistent data is never reset as an upgrade shortcut |

Run `python3 scripts/check-module-boundaries.py` and
`python3 scripts/check-module-boundaries-controls.py` locally and in the existing
Linux boundary workflow. No active precommit hook is claimed. Regenerate owned
SQL/installation artifacts through existing producers and run
`python3 scripts/build-owned-runtime.py --check` plus exact manifest checks.

Required focused native suites include existing `test_import_runtime_native`,
`test_engine_import_native`, `test_owned_import_native`,
`test_import_rejection_practical_native`, `test_import_chunk_closure_native`,
`test_reader_catalog_native`, `test_catalog_rebind_native`,
`test_required_catalog_rebind_native`, `test_group_preconditions_native`,
`test_receipt_visibility_native`, `test_action_transport_native` and strict result
wire/containment tests. New E5–E7 suites are `test_group_preview_wire`,
`test_group_preview_native`, `test_lifecycle_native` and `test_load_audit_native`.
E2/E3/E4 new selectors must be named in the execution receipt and selected in
Linux installed-wheel CI; do not count skipped opt-in integration as passed.
Native lifecycle/cluster management has one owner with fresh databases/roles and
explicit cleanup; local native tests stay on the host's native platform.

## Execution Contract

Implementation, review, documentation and release are authorized. Sol owns
contract/planning/review; Luna implementation and parent facade/integration
ownership are coordinated through the active task. No additional tracker is
selected. Token/cost/calendar estimates are unknown; no spending ceiling or
runtime usage meter was supplied. Tests and review are part of completion.

Preserve original native errors and source identities. A test/environment failure
is recorded and corrected, not transformed into a skip, increased deadline or
weaker admission. Fresh-install delivery remains selected; no reset or unqualified
migration of existing persistent data. Additional platform/security support is
not inferred from an ordinary-profile component pass.

## Continuation Evidence

Contracts adopt the remaining interfaces and explicit compatibility boundaries.
The following are local development checkpoints on intermediate source snapshots,
not qualification of the final release wheel or Linux CI. Final receipts must bind
their exact source, native manifest, installed wheel and test inputs.

| Selected slice | Observed checkpoint | Remaining release evidence |
| --- | --- | --- |
| E0/E1 | Published v0.0.43 evidence remains in the earlier plan | Preserve its regressions; do not relabel historical platform receipts |
| E2 | Ten batched-import native controls; two legacy-parity/performance controls, including mixed edges, original source, reserved identity and 32/64/128-record comparisons plus 1,024 capacity | Repeat against the final audit-writer/source bundle; retain complete reports and exact timing/count samples |
| E3/E4 | Conditional hit/miss authority controls, document CAS/replay and original UMF DDD optional-field controls have local native checkpoints | Final installed selection and exact original owner-asset correspondence |
| E5 | Six native preview controls, including an actual revocation during observation and a concurrent data update under one truth snapshot; six wire controls | Final source/wheel binding and Linux execution; catalog-basis drift remains a typed observation refusal |
| E6/E7 | Installer/status, module-grant, load-summary and mutation-audit controls pass locally; independent journal-only, module/type/deleted-entity and descending continuation cases are selected; marker/protected-configuration findings are fixed | Final Linux qualification repeats the committed audit/lifecycle selection |
| E8 | Installed iteration-2 consumer corpus: 63 passed, nine declared limits, seven replica-only exclusions; original sample workflow suite: 21 passed with Python-only PATH | Repeat exact final wheel; retain the original limit declarations and sample workload identity |

The iteration-2 original consumer trace reports 29 `Cursor.execute` calls plus two
connection rollbacks for a read with facts, and 31 `Cursor.execute` calls plus one
connection rollback and one connection commit for a single-object update. These instrumented driver counts
are not a universal statement budget: the final trace must retain public-call,
transaction-adoption, setup and settlement categories, sample distribution and
transport. A separately adopted conditional catalog call retains its three-client-
statement wrapper. `prepare_group_in_transaction` bundles current revision, group
context and named type/relationship references. Neither fixed client counts nor
the local import samples establish a tenfold end-to-end speedup or managed/TCP
performance.

Existing tagged import reports/provenance, selected delete behavior, receipt
lifecycle and core optional-field compatibility remain regressions. The nine
consumer limits include projection/relationship limits and adapter replay/preview
limitations outside the selected asks; they must remain explicit rather than
becoming an unqualified whole-provider conformance claim.

The [final implementation review and disposition receipt](evidence/embedder-e2-e8-20261020/review.md)
reviews implementation commit `4a442f337c7f2508bd5a9064489f49d1b842cb79` and the
installed v0.0.44 runtime manifest. Retained local evidence records 74 API/wire
tests, 70 regressions, two additional actual read-only/owned-audit controls and 44
host-guard/fault controls passing. All 428 current runtime source hashes match
the package receipt. Source review identifies no remaining blocking defect.
Linux candidate/release CI and fresh public-artifact verification remain pending;
the local result is not a publication claim.

## Risks and Rollbacks

| Risk | Required response |
| --- | --- |
| Faster imports erase partial progress or duplicate provenance | Keep legacy route exact; select new chunk profile explicitly and compare complete outcomes/effects |
| Catalog validator reuses stale authority | Fresh complete policy/dependency checks before both unchanged and snapshot release; fail closed on drift |
| DDD shortcut invents meaning | Use original known UMF validator/correspondence; unsupported edits retain explicit incompatibility |
| Preview observes multiple data cuts | Separate actual snapshot-bound truth from current authority; concurrency test before exposure |
| Audit leaks hidden history or invents commit order | Whole-group current owner union plus separate grant, safe visibility frontier and honest ordering |
| Install/lost commit damages existing namespace | Original exclusion/reconciliation, typed outcomes and no repair/reset/retry |

## Exit Criteria

- [ ] Every original accepted ask has a delivered API/documentation result and
  required native/consumer evidence, or its explicit adopted variant above.
- [ ] E2–E7 required cases pass against exact installed source/wheel; no selected
  opt-in case is counted passed when skipped.
- [ ] Complete workflow statement budgets are measured for the actual consumer
  read/write/import paths, with setup/settlement and server work separated.
- [ ] E8 original consumer replay, current authority negatives, strict response,
  cancellation/rollback/replay and cleanup controls pass.
- [ ] Focused independent review has no unresolved findings on the exact release
  source; Linux CI and source/wheel/sdist/RECORD/metadata checks pass.
- [ ] Fresh public artifacts and checksums/release pins match the qualified source;
  canonical consumer docs state bounds, typed unions, durability and limitations.

No slice is complete merely because its design is written or its budget is nearly
used. Completion requires the selected behavior and retained evidence.
