---
ddx:
  id: truss.temporal-native-qualification-plan
  type: implementation-plan
  activity: build
  authoring:
    home: repo
  links:
    - id: truss.temporal-interface-freeze
      kind: informed_by
    - id: truss.temporal-dependency-cohort-plan
      kind: informed_by
    - id: truss.temporal-current-baseline-plan
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
    - id: TP-001
      kind: informed_by
---

# Temporal native qualification plan

## Scope and strategy

**Qualification selection: `truss.temporal-native-qualification/1`.** Execute a
small helper selection first, a focused guard selection when callable sources
exist, then ONE coherent installed-candidate Linux campaign. This is planning
only: no implementation, workflow edits, tests or native processes by Sol.
Noether owns F8/F9 and native integration; the other Sol lead owns F7 review.

Governing authority is [freeze1 F1–F9](temporal-interface-freeze.md),
[dependency cohort2](temporal-dependency-cohort-plan.md),
[CONTRACT-010](../02-design/contracts/CONTRACT-010-exact-value-transport.md),
[CONTRACT-012](../02-design/contracts/CONTRACT-012-weft-storage-handoff.md),
[TP-001](../03-test/test-plan.md) and the current baseline plan. This matrix adds
quality controls, not semantics or API changes. Native is fresh-only0.76 with
explicit ABI1.3; ordinary ABI1.2 remains the default. Temporal package version is
next-available and deferred; preserve the other owner's installation-only55.
No retired153-case migration campaign, old native0.75 relabeling, clock changes,
unknown-metadata reinterpretation or large dirty bridge is an input.

The reviewed F7 source commit is `aa1a4e06` (not a1a4e06). Source review PASS,
UNENROLLED, is distinct from native qualification. Its five prepared native tests
are UNRUN. Required review additions are shared strict075 vector replay, negative
UTC boundary crossings, seven-zero-digit fraction refusal and ordinary-role
EXECUTE denial. This plan incorporates them without repeating source review.

## Framework selection and cost

Use existing Python unittest, psycopg and owned pgserver18.6.1/PostgreSQL18.6
fixtures; UMF's existing oracle corpus supplies independent expected semantic
values. Weft/UMF owners supply Rust/WASM/real Chromium parity receipts. No new
framework or database/platform/version cross-product. Cost is controlled by
explicit test IDs, bounded tiny data and one Linux job per selected stage;
no measured duration is claimed. Native initdb/shm/timeouts failed locally and
the other owner's Docker is unresponsive: do not repeatedly retry either as a
prerequisite. Use a selected hosted job when its source inputs are coherent.

## Evidence boundary and current fixture map

[Linux T4A41547057318](https://github.com/DocumentDrivenDX/truss/actions/runs/41547057318)
and its checked-in receipt at
`evidence/temporal-t4a/linux-41547057318-attempt1/receipt.json` prove authentic
public54/Weft051 baseline capture, four raw Weft056 compile/check calls, identical
page/whole-program bytes, unchanged guard refusal and confirmed cleanup.
They do NOT qualify candidate native execution, ABI1.3, ordinary adoption on new
native bytes, HF62, temporal acceptance or release. Do not rerun that unchanged
raw probe for this campaign or promote its claim.

All paths below are relative to the Truss repository unless prefixed otherwise:

| Input | Exact existing path/helper | Reuse boundary |
| --- | --- | --- |
| F7 quick component | `packages/python/tests/test_temporal_canonical_text_native.py`, class `TemporalCanonicalTextNativeTests`; `packages/python/src/truss/_catalog_runtime/query-temporal.sql` | Installs only the helper into a disposable schema; not a candidate installer/enrollment test. |
| Owned worker | `scripts/native_fixture.py`: `WorkerCluster`, `DatabaseFixture`, inventory/verify_clean | Fresh databases/roles, one lease, poison on cleanup drift. Respect helper's evidence destination restriction to docs/helix/04-build/evidence/design-audit. |
| Public model and writes | `test_group_create_native.PublicCreateGroupTests.ready`, `create`, `consumer`, `run_group`; `test_catalog_relational_support.relational_document` | Real accepted model, module roles and public group APIs; subclass helpers without rediscovering inherited tests. |
| Public CRUD/history | `test_object_mutations_native.ObjectMutationTests.test_create_update_read_dryrun_delete_and_durable_retry` | Existing exact writes, dry-run, delete and replay assertions. |
| Imports | `test_import_runtime_native.ImportRuntimeTests.test_create_skip_invalid_replacement_reject_source_commit_and_retry`; `test_import_chunk_closure_native.py` | Use public record builder/import; no direct-SQL happy-path local property/cell seeds. |
| Scalar/array regression | `test_scalar_containers_native.ScalarContainerTests.test_public_accept_write_read_import_history_and_map_equality`; `test_recursive_containers_native.RecursiveContainerTests.test_create_commit_read_and_reconstruct` | Ordinary arrays/maps: absent/null/empty, item and exact numeric behavior. Temporal containers remain refused. |
| Cache / read-only | `test_schema_cache_native.SchemaCacheTests`, `test_schema_memory_cache.SchemaMemoryCacheTests`; `test_read_only_public_native.ReadOnlyPublicTests` | Real revision rollback, person/permission isolation, read-only transaction and policy-replacement controls. |
| Snapshot schedule precedent | `test_query_selective_sources_native.QuerySelectiveSourcesTests.test_data_wrapper_preserves_statement_snapshot_with_volatile_countercontrol` | Barrier/event/writer coordination technique, not an ABI1.3 source or inherited temporal pass. |
| Ordinary ABI1.2 | `test_query_stream_abi12_native.QueryStreamABI12Tests.original` and its two owned methods; `test_compiled_query_native.CompiledQueryTests`; `test_query_selective_sources_native.QuerySelectiveSourcesTests` | Authentic fresh candidate binding, native execution/decoder and original guard controls. |
| Baseline six | `test_current_baseline.py` and `test_current_baseline_native.py`; baseline branch of `scripts/qualify-runtime-migrations.py` | Two pure plus four current-native controls only; assert baseline=true/sources=[] before selecting the runner. |
| Independent HF62 | `docs/helix/03-test/fixtures/hohfeld-followup-0.1.json`; `scripts/build-hf-conformance-archive.py`, `scripts/run-hf-conformance.py --installed-package` | All original semantic assertions, outside-checkout archive, exact reviewed cohort/producer pins. |
| Current module boundary gate | `scripts/check-module-boundaries.py`, controls `scripts/check-module-boundaries-controls.py` | Run existing gates; do not invent a new module checker or weaken private import rules. |

Archived source ONLY: commit `8bc82edd270a0043cd48ef8073fb2ef755eb017b` has the
seven temporal modules named below. Read with git show. They are NOT current
runnable tests and no old wheel, expected ABI hash, native identity, API argument,
128-character/zero-residue vector or token decoder is adopted by copying them.
Current method selectors marked PLANNED must be authored/retargeted by Noether;
missing collection is a failed readiness check, never a skipped passed gate.

## Critical paths and primary gate matrix

Every gate is P0. A row has one primary proof boundary; owner portable evidence
supports native proof rather than multiplying the whole native matrix.
A refusal must assert its specific original class/SQLSTATE and ZERO released
rows/effects, never merely any exception or an infrastructure error.

| Gate / freeze | Primary case owner and target selector | Required pass and fail-before control |
| --- | --- | --- |
| TN-00 / F2,F7 | Existing `TemporalCanonicalTextNativeTests` plus shared-vector/EXECUTE additions | Strict075 date/local/instant expected canonical text and unchanged raw token. Domain invalid raises22023. Required corpus/details below. A permissive seven-zero-digit parser or implicit UTC attachment must fail these assertions. |
| TN-01 / F1,F7 | PLANNED `test_temporal_source_security_native.TemporalSourceSecurityNativeTests.test_installed_temporal_abi13_shims_have_exact_owner_acl_and_stability` | Real installer enrolls exact source/ABI/helper bytes, actual0.76 release digest, owners, ACL/dependency closure, STABLE sources, immutable invoker helper and current person shims. Ordinary query_abi remains1.2; explicit capture1.3. Missing helper enrollment, wrong owner/EXECUTE, VOLATILE shim or a patched ABI pin fails. |
| TN-02 / F5,F7 | PLANNED `test_temporal_source_guard_native.TemporalSourceGuardNativeTests.test_invalid_source_is_not_hidden_by_outer_filter_or_limit` | Named-cursor first fetch returns NO row when an excluded row is invalid, then when a later row is invalid behind an earlier valid match/LIMIT1. Repeat read/page source and an unprojected temporal member. Streaming-before-validation or selected/seek prefilter source fails. |
| TN-03 / F2,F5,F7 | PLANNED same class `.test_scan_and_byte_caps_refuse_complete_source` and `.test_wrong_provenance_kind_and_presence_requirements_refuse` | Exact all-temporal-member requirements, original source refs/presence and scan/byte bounds. Omit an unprojected member, empty/duplicate/foreign/refined/wrong-kind/wrong-presence requirement, source-size or byte cap overflow: refuse before first row, no truncated success. |
| TN-04 / F7 | PLANNED same class `.test_buffered_source_uses_statement_snapshot_before_outer_gate` and `.test_stable_source_keeps_statement_snapshot_across_concurrent_public_update` | Two concrete schedules below, actual READ COMMITTED and installed STABLE routines. A deliberately refreshed-statement countercontrol observes the committed new value, proving sensitivity; metadata or a sleep alone does not pass. |
| TN-05 / F7 | PLANNED `TemporalSourceSecurityNativeTests.test_temporal_shim_refuses_abi_owner_acl_source_and_context_drift`, `.test_temporal_person_admission_needs_module_role_even_for_registrar`, `.test_temporal_source_requires_current_reader_for_aggregate_root` | Original session person, inherited/NOINHERIT/SET ROLE boundaries, module/root rights, private body owner/EXECUTE, source/ABI/runtime drift and installed RLS/policy inventory unchanged. Capture→revoke before call and buffered→revoke before release both withhold data. Privileged fixture identity cannot supply ordinary read authority. |
| TN-06 / F8 | PLANNED `test_temporal_catalog_transport_native.TemporalCatalogTransportTests.test_public_accept_atomically_refuses_stripped_temporal_owner_declarations` and both mixed-summary tests | Real public Prep2.1/support0.2 uses NONCOMPACT declarations and full inspection result. Strip descriptor/owner entry, duplicate/foreign/hash/pointer entry, send empty declarations or downgrade/mix summary: no catalog head/property/cache/request/journal effects. Source-only compact fallback must fail. |
| TN-07 / F8 | PLANNED same class `.test_temporal_replay_preserves_original_preparation_and_report_bytes` and `.test_legacy_timestamp_family_refuses_temporal_reinterpretation_atomically` | Exact original source/declaration/descriptor/summary2.1/owner/report bytes survive durable replay, recovery and reopen. Original core timestamp and actual local native family remain distinct. Old timestamp property rediscovery/rename never changes family/cells. A lost descriptor reconstructed through2.0 must fail. |
| TN-08 / F2,F8 | PLANNED `test_local_timestamp_query_native.LocalTimestampQueryTests.test_public_accept_apply_read_all_temporal_families_and_presence`, `.test_public_local_crud_import_cache_history_and_readonly` | Actual selected local property created by public acceptance, then public create/update/unset/null/dry-run/delete/import/replay/read/history. Required and optional local/instant/date, committed/reopened/read-only visibility; valid_property_definition/value and stored/cache family/source correspondence observed. Direct-SQL local seeds cannot pass. Invalid local text/kind/presence/import leaves no partial effects. |
| TN-09 / F4–F7 | PLANNED `test_temporal_engine_native.TemporalEngineNativeTests.test_typed_temporal_model_read_filter_verify_and_full_ordered_pages`; `test_access_temporal_codec.NativeTemporalCodecTests` retargeted to freeze1 | Actual current TrussTarget emits exact request, all four Weft shape/current checks, current explicit native capture and strict envelope/typed decoder; three kinds project/filter/order/page end to end. SQL, request strings, slots/origins, outputs/hidden metadata, cap/ABI/model/binding/program tamper each refuses BEFORE data dispatch. No Python result repair or generic target fallback. |
| TN-10 / F6 | PLANNED same engine class `.test_full_tuple_hidden_alternate_key_pages` and `.test_native_temporal_numeric_selected_key_is_explicitly_refused` | Independent complete ordered bags, hidden full composite alternate string Key, repeated first components, duplicate temporal sort values, null/missing states, both directions and FIRST/LAST. Forged state/type/arity/Key/actor/binding/noncursor arguments/native-token agreement or hidden-output position refuses; numeric and temporal selected Keys refuse. |
| TN-11 / F7 | PLANNED `test_temporal_target_release_native.TemporalTargetReleaseTests.test_revoked_current_authority_withholds_native_temporal_result_and_cleans_up` and `.test_expired_native_temporal_deadline_cancels_and_rolls_back_owned_transaction` | Real bounded native wait triggers deadline/cancel; no early results, actual backend stopped/transaction contained, caller-owned prior work preserved and uncertain cleanup never returned to pool. Final revocation after buffering withholds all data. A timeout exception alone does not establish rollback. |
| TN-12 / F1,F9 | Existing six baseline controls plus PLANNED `test_temporal_catalog_transport_native.TemporalCatalogTransportTests.test_public54_populated_installation_refuses_candidate_without_effects` | Fresh0.76 verifies authentic initializer/inventory; real public54 wheel creates populated old installation. Candidate tooling refuses its tuple without changing data/properties/source/history/ACLs/retained requests. Unknown/retired sources remain refused. No migration/recovery success claim. |
| TN-13 / F1 | Explicit ordinary regression manifest and independent HF62 below | Candidate's authentic default ABI1.2 compiles/checks/EXECUTES/decodes original queries/pages, exact timestamp/numeric/container semantics, cache/read-only/security controls, and ALL unchanged62 HF assertions. Old T4A raw responses alone fail this gate. |
| TN-14 / F1–F9 | Installed-candidate/owner Chromium receipts and final public-consumer receipt | Exact reviewed source/UMF/Access/Weft/native tuple, archive→installed payload equality, actual exports, fresh schema/install, all native gates, full original program and typed rows; final tag/public bytes/consumer cleanup below. Wheel import or upload alone fails. |

## TN-00 exact oracle additions

Use canonical UMF `fixtures/access/golden-vectors/temporal-profile.json` (profile
umf-access-temporal/0.1.0), consumed by `tests/access-temporal-profile.test.ts`.
Retain its source/revision/hash and case IDs; replay ALL cases with the native
helper and compare complete canonical expectations/refusals. Do not substitute
Python datetime.fromisoformat as admission. Python exact fixed-offset arithmetic
is a supplemental independent oracle after admitted construction.

Positive boundaries: valid leap2000 vs nonleap1900; years0001/9999; local missing
fraction and1/6 digits; instant Z, positive/negative minute offset and day/year
rollover within range; pre-epoch whole seconds and microseconds; width32 instant
`2024-01-01T00:00:00.123456+01:00`; identical instant with different original
offset spelling. Canonical date10/local26/UTC27, original source remains exact.

Negative controls include `0001-01-01T00:00:00+00:01` underflow and
`9999-12-31T23:59:59-00:01` overflow, and exact
`2024-01-01T00:00:00.0000000Z` / local equivalent (seven ZERO digits).
Also unknown -00:00, offset seconds, leap seconds, year0, invalid calendar/clock,
lowercase separators, ASCII trailing newline/space, non-ASCII digits, empty
fraction, wrong kind/null input and33-byte input. Null INPUT is invalid helper
input; admitted nullable FIELD state bypasses token parsing explicitly.

Use an ordinary nonowner role: direct helper call without grant MUST raise42501
(no PUBLIC EXECUTE). Its approved person-source call must still succeed through
the installed authorized path, proving denial was not a broken installation.
Helper source-only INVOKER permissions and final enrolled execution are different
boundaries; do not grant the ordinary test role direct helper rights to get green.

## TN-02–05 real source/snapshot/security schedules

Create a tiny six-row accepted source through public operations: duplicate UTC
values with different offsets, instant9/10 and negative epochs; two equal locals;
optional date/local null and absent. Use a composite alternate string Key with
shared first component and unique second. No scan-order assumption: record actual
native object IDs and deliberately place the later invalid row after the earlier
match in that deterministic source enumeration. Never claim source count bound
from result/page size. pageSize2 suffices; no large-scale data is needed.

For adversarial invalid stored-value tests ONLY, record public valid baseline,
then mutate one cell administratively in the disposable test database and verify
its actual corruption. This is a named fault injection, not valid ingress proof.
Try malformed values for EACH kind, excluded/later row and unprojected Field;
reuse the same tiny fixture with rollback/restoration between variations. Assert
first named-cursor fetch raises domain22023 with no rows made available. Both
source shims must obey the same complete-source rule. Scan6 succeeds, cap5 fails;
byte boundary uses actual captured charge: just sufficient succeeds, one byte
below the complete charge fails54000. Changed cap in a compiled program is a
custody refusal; source-cap tests use authentic selected capture values.

TN-04 has TWO complementary observations, not one metadata assertion:

1. **Statement begins before source access.** Reader uses actual READ COMMITTED.
   A fixture-owned VOLATILE INVOKER barrier returns the unchanged binding after
   waiting on an advisory lock and is an argument to the REAL UNMODIFIED source
   call. Verify reader backend wait_event/advisory and that it has reached this
   dependency before writer proceeds. A second ordinary authorized connection
   commits a VALID public update; unlock and fetch reader's complete result.
   Installed STABLE sources must observe the old outer-statement values. Next
   READ COMMITTED statement sees new values. Use a separate fixture-only refreshed
   inner-SPI/statement countercontrol (or the existing volatility countercontrol
   technique) which MUST see new values; it is harness sensitivity evidence,
   never certification of an administratively modified installation.
2. **Source completely buffered before consumption.** MATERIALIZED guarded CTE
   feeds a count-dependent MATERIALIZED advisory gate, then user filter/LIMIT.
   Wait for the post-source gate, commit a second-connection public update, then
   release. Reader retains its pre-update complete source, next statement sees
   update. A separate named late-invalid-row fault variant must refuse on the
   next statement, proving the whole source was validated and no prefix escaped.

Barriers are external fixture objects only; never insert hooks into installed
candidate source/functions for its passing proof. Each reader/writer has its
own connection; writer commit completes before unlock; verify pg_proc STABLE
through the wrapper/internal-source chain. Record server isolation/settings,
backend IDs, ordered events/observed waits, writer outcome, original/final rows,
final function definitions and cleanup. No sleep-only scheduling, separate
production preflight, stronger isolation, fake clock or changed source body can
stand in for this proof. Always release locks/cancel readers in finally before
joining threads; bound waits and assert cleanup.

TN-05 records original role/session actor versus effective DEFINER owner, exact
EXECUTE and dependency owner inventory, source/table grants and native RLS flags/
policies. Existing routines use pinned row_security=off plus original-person
checks; do not assert new RLS policy support or change that security model. Test
current supported inventory, denied direct table/registry access, SET ROLE and
registrar-without-reader negatives. Unexpected RLS/policy/owner/ACL drift must
retain current guard's exact refusal without granting bypassrls or suppressing
native errors. Expected classifications: authorization P1403, missing EXECUTE
42501, stale source55P03, unsupported ABI/context0A000, installed owner drift55000,
domain22023, cap54000 where the governing current guard specifies them. Capture
original diagnostics; do not turn any into empty rows or a generic success.

## TN-06–10 transport, data, cursor and original custody specifics

Persist before/after inventories for every failed acceptance: schema head,
prop_def/key definitions, runtime schema cache, source/request/report and journal
counts/bytes. Verify inverse descriptor coverage, not just descriptor validity
when present. Reopen/replay a genuine retained2.1 request; compare exact complete
source/declarations/summary/owner/report bytes and actual local property family.

Extend public CRUD/import fixture with required and optional scalar Fields.
Observe value→null→unset transitions only where admitted; required null/absence
refuse. Import a valid local value, then invalid kind/precision/presence in a
separate record/batch and assert existing import outcome/atomicity rules (do not
invent whole-batch atomicity where the import contract reports per-record
outcomes). Dry-run/failed update must preserve prior local cell/history/version.
Compare fresh instance after commit, rollback visibility, history and cache hit
against cache miss using complete source/native descriptor basis. Read-only
snapshot means the existing caller statement/transaction read-only semantics;
it does not add repeatable-read or cross-page snapshot guarantees.

Nullable ARRAY coverage is ordinary container regression: outer absent/null/
empty/nonempty and current declared item-null domain. Existing scalar-container
fixture has REQUIRED items: null item MUST refuse, not gain support. If a
separately supported fixture declares nullable items, retain its existing scope;
no new item semantics. Selected temporal arrays/maps and refinements MUST refuse
before acceptance/execution. No extension of scalar-only temporal scope.

For full-tuple pages, pair all ASC/DESC with FIRST/LAST over the SAME tiny data,
pageSize2; independently author expected row order for each kind including exact
normalized instant9/10/negative order. Keep user projection free of Key fields
in at least one case so hidden Key/state disclosure/custody is exercised. Page
until exhausted; compare full bag/order with no duplicates/omissions. Change
sort/state/hidden output slot, alternate Key, token tuple/native token or current
actor/noncursor parameter: refusal before dispatch. Null and missing rank equal
but retain separate state markers. Live pages may see later writes; no snapshot
claim spans pages. Numeric/temporal selected Keys are separate negative cases.

Whole-program tamper cases retain original JSON STRING evidence and owner
recompilation: original request strings/documentJson/bindingJson whitespace,
SQL, selectedKey/order, sourceDomainChecks, parameter positions/origins, outputs,
hidden metadata, caps and ABI. Change one at a time; shape checker refuses before
native capture, current checker before data execution, as appropriate. Native
context drift is not repaired by editing original pins. Instrumentation counts
actual capture/data-call boundaries while forwarding original calls unchanged.

## TN-13 bounded ordinary preservation selection

Run these exact existing owned methods once on the final candidate tuple, not
whole inherited classes:

```text
test_query_stream_abi12_native.QueryStreamABI12Tests.test_actual_selected_cursor_decodes_all_batches_and_descriptors
test_query_stream_abi12_native.QueryStreamABI12Tests.test_cursor_current_person_revocation_preserves_caller_work
test_query_selective_sources_native.QuerySelectiveSourcesTests.test_selected_source_and_ordered_seek_retain_native_refusals
test_compiled_query_native.CompiledQueryTests.test_exact_integer_decimal_projection_and_parameters
test_compiled_query_native.CompiledQueryTests.test_supported_projection_on_mixed_scalar_catalog
test_compiled_query_native.CompiledQueryTests.test_authored_composite_key_pages_and_count_profile
test_scalar_containers_native.ScalarContainerTests.test_public_accept_write_read_import_history_and_map_equality
test_recursive_containers_native.RecursiveContainerTests.test_create_commit_read_and_reconstruct
test_schema_cache_native.SchemaCacheTests.test_query_binding_validator_misses_rolled_back_reused_revision
test_schema_cache_native.SchemaCacheTests.test_query_binding_cache_isolated_by_current_person
test_schema_cache_native.SchemaCacheTests.test_cached_query_schema_cannot_cache_permission_grants
test_schema_memory_cache.SchemaMemoryCacheTests.test_reused_revision_with_different_basis_source_invalidates_view
test_read_only_public_native.ReadOnlyPublicTests.test_create_commit_and_public_reads_in_actual_read_only_transaction
test_read_only_public_native.ReadOnlyPublicTests.test_policy_replaced_while_object_buffered_uses_current_roles
```

Then ALL62 original HF case IDs/assertions from the independent archive, with
reviewed exact candidate producer/cohort admission. If a selected ordinary method
also is an HF case, execute once and link the same exact observation to both gates
only when the independent runner's original expectations and complete receipt
are preserved. Do not drop/alter HF assertions or silently rewrite its hashes.
Current baseline six execute once; its runner must remain on baseline branch.
Never select RuntimeMigrationNativeTests/SubsequentRuntimeMigrationTests as a
replacement. Additional mandatory existing final release gates remain mandatory;
this focused campaign does not waive their exact-tag requirements.

## CI selection and build commands

### Earliest raw initializer observation admission

Decision `truss.temporal-native-qualification/1-observation-admission` (2026-11-03):
the two serial `UTC` and `America/New_York` raw initializer observations may precede
Core3.13/source-rebuilt consumers and Weft WASM/browser completion. They observe
one exact installed Linux initializer; they do not qualify a baseline, native
composition, owner release or public package. No execution is admitted by this
plan amendment alone.

Final-source selection follows the
[Weft R_W production decision](temporal-coherent-source-integration-plan.md#weft-final-production-source-and-current-artifact-inventory).
Prepare reusable enrollment/intake code now, but select only the incoming genuine
final R_W Linux release wheel and module. Retained d526 component proofs remain
valid at their original source; no d526 PostgreSQL captures or combined campaign
are selected because the expected final wheel/enrollment seal would invalidate
them. Final R_W Linux component qualification may support early observations
while its WASM/browser release gates remain open, once the complete actual input
and enrollment admission below passes review.

Before PostgreSQL starts, Sol reviews ONE actual artifact/enrollment admission:

- Actual Linux Core0.10.8 wheel/source/module identity at canonical S; fresh
  installed Python3.11 inspection17/51 calls, resource/source/payload checks,
  Saga19 and lifecycle results. Preserve the original SDK/browser custody proofs
  and their separate controller/source identities.
- Actual Linux umf-weft0.4.57 wheel/module at reviewed Weft source, frozen lock
  and canonical S dependency/resource closure; installed14 temporal boundary and
  five padded-routing controls, callable four-checker APIs and repaired installed
  SDK compatibility/custody controls green. A produced wheel or metadata alone
  is insufficient. macOS proof cannot substitute for this Linux boundary.
- Exact Accessdev10/Truss0.0.56 installed wheel bytes, normal-resolver/pip-check
  closure, runtime versions/origins, and a clean actual Truss commit/tree. Genuine
  Core/Weft binary enrollments and their actual installed hashes, all canonical
  resources, source seal and native0.76 manifest must be complete before capture.
  Existing source/installed-payload, enrollment and producer refusal checks stay
  enabled, including `load_cohort(require_qualified=True)`; no placeholder or
  ambient-source fallback is permitted.

The identity seal and admission must label their evidence scope as installed
Linux component admission for inventory observation. They must list actual
Core3.13/rebuilt and Weft WASM/browser outcomes and all pending full-cohort/TN/release gates explicitly;
do not invent a full-qualified status to satisfy an identity field. Use only the
reviewed default-OFF inventory phase, one hosted Linux job, exactly two serial
fresh initializers, unchanged initialization/clocks and original owned cleanup.

Record each gate's actual outcome and original receipt identity. The coordinator's
reported green Core continuation41626678514 must be reconciled with its final
artifact packet; do not keep a completed gate labelled pending or use that report
alone as promotion/capture admission. Source PASS for dd59 intake preparation
admits no resolver, build, enrollment apply, capture or hosted execution. Its
actual final-R_W input packet and clean committed Truss source/tree require
separate review; intake outputs remain `ready:false` until that later admission.

Retain original capture commit/tree/producer, wheel/module/native digests and raw
inventories. Later tests over identical bytes do not require recapture. Changed
selected non-migration payload, compiled enrollment, source seal or native
manifest requires fresh captures; only the reviewed migration-artifact descendant
rule permits baseline incorporation without them. Baseline assembly still needs
review, and final119 execution remains gated on the full reviewed baseline and
cohort admission. No remaining owner, native or public release gate is waived.

Noether implements selectors; Sol does not edit its workflow. Required behavior
is default-OFF explicit selection with exclusive job routing. Suggested internal
inputs are `temporal_native:boolean=false`, `temporal_selection:choice=none`
(options none/f7-helper/guard-smoke/candidate); do not dispatch on push/PR or run
other released-runtime/T4A/stress jobs as a side effect. Map existing owner's
input names to these semantics if already implemented. One Ubuntu24.04/Python3.11
job, no OS/Python/server matrix, no capacity/stress/public1000 workload by default.
`capacity_statistics=false`, `public_workflows=false`, `stress_case=none` stay so
unless the coordinator explicitly selects a separate necessary existing gate.
Current release.yml also enables the public1000 workload automatically for tags;
therefore dispatching that workflow/tag is NOT the focused campaign selector.
Before final release, its integrator must reconcile that automatic trigger with
the required explicit expensive-run selection. Required exact-tag gates retain
their obligations and must be explicitly selected; optional large/stress work
must not silently start because a tag exists. This plan edits no workflow and
waives no required release assertions.

| Selection | Readiness | Exact scope / retry rule |
| --- | --- | --- |
| f7-helper | Source-review PASS; helper/vector/ordinary-EXECUTE additions collected | ONE hosted component job: the five existing owned methods below plus review additions. No full release workflow/native installation claim. |
| guard-smoke | Actual enrolled source and public acceptance fixture callable | TN-01 plus TN-02 excluded/later/unprojected read/page, TN-03 one missing-member and scan-cap control, TN-04 both schedules, TN-05 ordinary EXECUTE/module denial. One focused job only if it resolves an implementation risk before coherent campaign; omit separate smoke dispatch if candidate is already ready. |
| candidate | F7–F9, owner packages/compiler/typed target and exact native inventory coherent | ONE installed-candidate campaign job: all TN gates plus ordinary14/HF62/current six; build/download exact inputs once and reuse. No red prerequisite runs against missing APIs. |

Exact existing f7-helper command (PLANNED execution, not run here):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/python/tests:scripts python -m unittest -v \
 test_temporal_canonical_text_native.TemporalCanonicalTextNativeTests.test_contract075_canonical_vectors_and_original_text \
 test_temporal_canonical_text_native.TemporalCanonicalTextNativeTests.test_exact_integer_offset_normalization_against_fixed_offset_carriers \
 test_temporal_canonical_text_native.TemporalCanonicalTextNativeTests.test_strict_grammar_calendar_kind_and_normalized_range_refusals \
 test_temporal_canonical_text_native.TemporalCanonicalTextNativeTests.test_host_timezone_datestyle_and_collation_do_not_change_tokens \
 test_temporal_canonical_text_native.TemporalCanonicalTextNativeTests.test_helper_is_immutable_invoker_and_has_no_public_execute
```

Luna adds explicit owned selectors for shared-vector replay/ordinary-role denial
or includes them in these existing methods, then records the exact collected case
manifest. Five prepared methods alone do NOT satisfy the review additions.
For quick-helper source SQL loading is intentional and explicitly component-only.
Candidate proof must inspect/execute the actually installed enrolled helper/source
bytes, not CREATE FUNCTION from checkout SQL over a supposedly installed target.

For candidate campaign use a reviewed explicit unittest case manifest mapping each
TN gate to owned method IDs. All PLANNED names must exist before dispatch. Collect
without native setup first, reject duplicates/missing/unknown IDs and inherited
suite expansion. Record expected IDs and actual subcase results; required skips,
zero tests, unavailable compiler or failed initdb are failed/unqualified gates.
Use one owned socket-only WorkerCluster with fresh DatabaseFixture per serial
case/class where supported; lifecycle/public54 controls retain separate owned
clusters as required. Reuse runtime binaries, not dirty databases/connections.
Do not change an existing helper's isolation just to share a cluster.

Run module gates once. Baseline runner command remains:
`python scripts/qualify-runtime-migrations.py --installed-package --download --wheelhouse <verified wheelhouse> --output <receipt>`;
assert baseline=true/sources=[] and selected current-only six. HF command from the
unpacked independent archive is
`python scripts/run-hf-conformance.py --installed-package --output <receipt>`.
Placeholders are run-specific destinations, not fabricated runnable existing
receipts. Existing exact package/producer guards must pass before native work.

Do not rerun a successful unchanged helper job, T4A probe, full old release,
retired migrations or platform matrix to fill a new receipt. A changed helper,
owner/compiler/native tuple or relevant assertion invalidates affected earlier
proof: rerun its necessary gate. Source helper component evidence may be reused
only by exact hashes; final candidate still needs actual installer/enrollment
and integrated guarded execution. Later exact-tag/public consumer work is a
separate required provenance boundary, not redundant candidate testing.

## Test data, security and cleanup evidence

Before each negative perturbation capture authentic baseline; require a paired
valid call before and after restored state. This distinguishes a refused fault
from an unusable fixture. Administrative corruption is confined to fresh owned
test databases, never used as ordinary authority or happy-path source creation.
No production source hook, grant bypass, fake source binding, repaired result or
relabelled inventory. Use installed real public54 bytes for TN-12 and separate
venv from candidate; preserve its old application/data and verify candidate
refusal at SQL/native effect boundary.

Every attempt uploads even on failure: run/attempt/SHA, source/installer/native
inventory and ABI hashes, owner wheel/distribution/native-module hashes, original
compiler strings/whole programs/params/outputs/source checks, case/subcase IDs,
row/state observations, native errors/SQLSTATE, waits/transaction settlement and
cleanup. Helpers restrict evidence roots; store native inventory evidence beneath
existing design-audit path and reference/copy verified receipts into
`evidence/temporal-native/<fresh-attempt>/` without modifying originals.

Confirm connections/cursors/futures closed, advisory locks released, worker
role/database/member inventory restored and original postmaster PID absent plus
pg_ctl status3 before deleting owned runtime directories. Uncertain shutdown or
inventory drift poisons the worker, retains diagnostics/data and fails cleanup;
never remove a directory to manufacture proof. No secret connection strings or
application data in public artifacts. Bounded per-wait and overall job deadlines
must leave time for finally cleanup/upload; exact budgets are declared runner
limits, not measured performance claims.

## TN-14 final provenance and public consumer

Bind one reviewed source/cohort manifest to the exact candidate wheel/SQL/ABI and
installed observations, with no ambient editable packages or sibling dependencies.
Public workflow must genuinely accept a model/create a local property, public
write/import and typed query all three kinds, replay retained2.1 and traverse a
hidden-Key temporal page, plus ordinary ABI1.2 read. The consumer uses unchanged
public APIs and actual strict decoder—no patching envelopes/carriers.

After reviewed merge, select the next available package version (not55), tag
exact source, pass mandatory exact-tag gates, publish immutable assets/registry
through existing trusted workflows, independently fetch public archives and
verify full payload hashes/provenance, then run that fresh installed consumer
and confirm native cleanup. Published-only byte checks do not replace execution;
local source successes do not replace public artifact identity. UMF/Access/Weft
source, packaging and real browser receipts must match the claimed tuple. Scope
is PostgreSQL18.6/Linux and any separately run local platform, not an automatic
managed-service/all-platform claim.

## Risks, known gaps and continuation

All new native/transport/target gates remain UNQUALIFIED until real receipts.
Current archived tests include obsolete support0.1, old hashes/native0.75,
zero-residue/128-character expectations and old EngineRead arguments: retarget
case intent only, using freeze1 APIs and strict075 source. No old snapshot pass
transfers. F7's source-only PASS and syntax/boundary checks remain narrow.
Local initdb/shm/timeout and Docker availability are infrastructure failures,
not semantic pass evidence or authorization to weaken guards. One selected
hosted job is the next execution path; no tests run by this planning task.

## Exit criteria

Plan readiness requires exact selected gate/case mapping and coherent inputs.
Candidate qualification requires TN-00–14 at their appropriate native/owner/
artifact boundaries with no required skips and confirmed cleanup. Full delivery
requires reviewed exact-tag/public bytes plus genuine fresh consumer execution.
No release/migration/temporal-array claim follows from a green helper job.
