---
ddx:
  id: truss.temporal-current-baseline-plan
  type: implementation-plan
  activity: build
  authoring:
    home: repo
  links:
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
---

# Temporal integration against the current baseline

## Scope

Port the genuine temporal gap in snapshot
`8bc82edd270a0043cd48ef8073fb2ef755eb017b` onto current Truss, consuming the
existing UMF and Weft owners. The owner's clarified instruction is to integrate
real gaps and delete proven supersession. Original snapshot qualification is
not assumed. The published 0.0.53 fresh baseline remains separately qualified.

Governing artifacts:

- [Truss CONTRACT-010](../02-design/contracts/CONTRACT-010-exact-value-transport.md) and
  [CONTRACT-012](../02-design/contracts/CONTRACT-012-weft-storage-handoff.md).
- [Original source/guard contract](https://github.com/DocumentDrivenDX/truss/blob/8bc82edd270a0043cd48ef8073fb2ef755eb017b/docs/helix/02-design/contracts/temporal-query-source-guard.md),
  ID `truss.temporal-query-source-guard`, especially Authored source and native
  carrier, Prep2.1 acceptance transport, Explicit native ABI, and Compiler and
  host composition.
- [Original TX-0–TX-6 plan](https://github.com/DocumentDrivenDX/truss/blob/8bc82edd270a0043cd48ef8073fb2ef755eb017b/docs/helix/04-build/pws03-temporal-engine-plan.md),
  ID `truss.pws03-temporal-engine-plan`, including inverse descriptor coverage,
  string-Key paging and native security/snapshot validation.
- UMF `CONTRACT-070-access-extension.md` and
  `CONTRACT-075-access-temporal-profile.md` in the current owner's checkout.

The historical Truss contract's reference to UMF CONTRACT-082 is unresolved:
current CONTRACT-082 is Spark Delta 4 DDL realization, and the recorded
`f323a2dec16132c00eb1bc75c65c416f94804c26` tree has no CONTRACT-082.
It cannot qualify the proposed finite binding conversion. Preserve
CONTRACT-075's strict grammar; reconcile a separately named binding profile
with its owner before crediting the snapshot's 128-character/zero-residue route.

## Shared Constraints

- UMF owns authored FieldView semantics; Weft owns parsing, resolution,
  lowering, ordered parameters/results and compiler custody. Truss must not
  implement substitutes for missing owner surfaces.
- Current Truss already uses native release label `0.75-candidate` with ABI1.2.
  The old temporal snapshot also used that label for different bytes. Select
  and qualify a new native identity/digest rather than treating equal labels as
  compatibility. Do not rewrite frozen manifests or existing property meanings.
- No retired migration lineage, stale publisher pins, old dev5/dev6 receipts,
  non-release admission bundle, or caller-supplied capability boolean may
  establish temporal support. Native runtime, compiler and SDK profiles remain
  unavailable until real composition passes.
- Qualify locally on macOS and select hosted Linux only when the changed cohort
  is ready. Do not repeat successful 0.0.53 release gates for this investigation.

## Current Owner Comparison — 2026-11-02

`UMF — Rust port and V8 removal` is qualifying the unified 0.10.7 pack-generator
release. Observed source head: `bbe15fd4b1055db78adb5a4ac1b3a0c71db7398f` in
`/Users/erik/.codex/worktrees/rust-binding-spike/umf`; its resource/package
repairs are active, so this is an inspection of specific source, not a claim
that the owner's uncommitted work is absent or released.

`UMF/Weft — local migration qualification and releases` is qualifying migration
ingress and offline Access dev9 packaging with cached public Weft 0.4.56.
Observed UMF head: `dbdaa126151d5691ff18814ab4b652ccb3a685f1`. Its active
ingress/budget/connection fixtures do not expose temporal engine0.4. Weft
`origin/main` and tag `v0.4.56` both resolve to
`2f62e1148d1b2030558550e4f6f2ffe518bac62d`; the active ordinary-module branch
is `973d864c8d26b2bc173a411eac8368da5efc1ab3` and has no temporal guard/checker
surface. None of these owner checkouts was edited.

### UMF: existing semantics, missing public composition surface

Available now:

- Python `umf.rust_temporal.access_temporal_profile_version()` and
  `access_temporal_canonical_token(kind, year, month, day, hour, minute, second,
  microsecond, offset_microseconds)`. The installed 0.10.6 GitHub wheel returns
  `umf-access-temporal/0.1.0` and the exact local canonical sample.
- Node/WASM `accessTemporalProfileVersion()` and
  `executeAccessTemporalWire(wireJson)`; existing Rust token oracle and Python codecs.
- TypeScript source `src/compilation/admission/access/index.ts` already has
  `inspectAccessViews(document, selected, bindings=[], sourceId='logical')`.
  Rust `crates/umf-codegen/src/access/inspection.rs` already has the equivalent
  `pub(super) inspect_access_views` and resolved temporal fields. This is an
  exposure/composition gap, not missing authored semantic implementation.
- Public `CodegenEngine.generate_access_package` and `diff_access_packages`;
  generation uses the inspection internally. Its public result and manifest
  do not return the complete original `{records, diagnostics}` inspection.

Required owner surface: a supported public inspection operation, or an
owner-approved equivalent, returning the resolved Records/Fields, exact refs,
selected Key, row presence, selected instant/local meaning and ordered
diagnostics. It must preserve original document identity and distinguish
unsupported/refined/foreign/duplicate selections. Proposed smallest patch:
expose the existing Rust inspection through `CodegenEngine`, the shared
codegen wire dispatcher, Python and Node/WASM facades, using their existing
explicit resources and resource/cancellation controls. Truss then consumes
that pinned operation, rather than copying the historical JavaScript bundle.

Independent probe: installed `umf-core==0.10.6`
`CodegenEngine.call('inspectAccessViews', ...)` returns
`REQUEST: Unknown codegen operation`. The current 0.10.7 source's dispatcher
and facades also lack that operation; existing internal inspection is retained.

Second required owner surface: an explicitly selected inert temporal engine
descriptor/custody route. Current `umf_access.engine_catalog.EngineRead.build`
and `compile_original` support engine read/page0.1/0.2 and have no
`temporal_profile` argument. Extend descriptor, original-program checks and
typed decoder selection for engine0.4/profile0.2 (or a reconciled successor),
keeping all I/O in Truss. Existing canonical codecs can be reused, but they
do not establish current source/ABI/target authority.

Owner tests: parity of TypeScript/Rust inspection for local/instant/date,
wrong vocabulary/FieldView, unsupported refinements, duplicate/foreign refs,
temporal Key refusal, original-byte retention, budget/cancel limits, and actual
Python plus Node/WASM package exports. Inert catalogs must retain the whole
original artifact and refuse unknown/mixed profiles or generic targets.

### Weft: integrated temporal program and guarded source missing

Available now: `compile_engine_read_json(packet)`,
`compile_engine_page_json(packet)`, `check_engine_read_json(program, request)`
and `check_engine_page_json(program, request, after)`; public 0.4.56's Truss
backend selects ABI1.2 and backend interface0.2.9. Generic temporal operations
elsewhere do not qualify this integrated Truss source guard.

The snapshot requires these exact Python call shapes:

- `check_engine_temporal_read_shape_json(program, original_request)` and
  `check_engine_temporal_page_shape_json(program, original_request)` return a
  checked original program shape before native context capture.
- `check_engine_temporal_read_json(program, current_request)` returns
  `{status:'checked', program:<whole freshly checked program>}`.
- `check_engine_temporal_page_json(program, current_request, after_json)`
  returns the full compiled/checked page under the current continuation.

All four are absent in the installed public wheel and inspected active source.
The existing read compiler rejects an engine0.4 `truss-runtime-temporal` packet
with `WFT-ENGINE-READ: engine catalog version differs`. Renaming ordinary
checkers would not supply the missing semantics.

Minimal owner patch: extend the closed frontend request/profile selection and
`crates/weft-postgresql/src/truss_runtime.rs` with additive ABI1.3 guarded
source lowering; extend `crates/weft-runtime/src/engine_read.rs` custody and
`crates/weft-python/src/lib.rs` exports, plus the equivalent portable binding.
The snapshot's proposed versions are compile0.2.10/backend0.4.47, engine0.4,
`umf.weft-binding-temporal/0.2`; reconcile exact successor identities with the
owner before pinning a new Truss cohort. Legacy profiles retain their meaning.

Required artifact: `sourceDomainChecks` is closed
`{version, mode, queryAbi, maxScanRows, maxBytes, sources}`, with version
`weft.truss-temporal-domain-checks/0.2` and mode `native-validated-source`.
Each source binds the original Record identity, one-based binding and
requirements parameter positions, exact source function and selected Key.
The final SQL must invoke the complete guarded native source before user
filters/order/limit. Original parameters, outputs, SQL, caps and ABI pins all
participate in whole-program digest/recompilation custody.

Owner tests: real date/instant/local projection/filter/order/page compilation;
separate temporal parameter map and cross-kind refusal; tampered source packet,
SQL, parameter positions, outputs, caps or ABI refusal; string-Key full-tuple
continuation in both directions/null placements; numeric selected-Key refusal;
exact negative/pre-epoch instant comparisons; existing ABI1.2 regression; real
native and Chromium parity on the selected package bytes.

## Implementation Slices

### Current delivery and installation selection

The [embedder and temporal delivery plan](embedder-temporal-delivery-plan.md)
adds the current delivery gates. The temporal native release is fresh-only under
the current installation baseline policy. It does not ship a 0.0.54-to-new-native
migration. Use the real public 0.0.54 wheel to create a populated negative-control
installation and prove new-tool refusal without modifying any existing property,
cell, source, history, ACL or retained request. Keep retired 0.0.47/48 lineage
refused; no automatic startup migration, reset or clock manipulation is allowed.
The current-only six baseline controls remain; do not revive the retired matrix.

Truss 0.0.54 pins `weft-sql==0.4.51`; public Weft 0.4.56 uses `umf-weft` and
different selected envelopes. A new owner cohort requires authentic default
ABI1.2 capture/compiler/checker/decoder execution and native regression adoption
alongside all 62 original HF semantic assertions. Inventory distribution-name
assumptions in package, release and qualification tooling. Retain original inputs
and audit actual producer deltas before updating hashes. No version-only repin or
relabel supplies compatibility, native acceptance or archive migration evidence.
This adoption gate precedes TC-5/6 qualification and is tracked as T4A in the
delivery plan. Reserve `truss-catalog-runtime/0.76-temporal-candidate` as the
new native identity; compute its actual manifest and ABI digests from reviewed
source bytes. Both conflicting native0.75 inputs remain distinct and unchanged.

| Slice | Owner | Dependency | Required observable gate |
| --- | --- | --- | --- |
| TC-0 | Truss | None | Standalone immutable LocalTimestampValue and canonical26 validator; old ExactValue/import/native paths still refuse it. |
| TC-1 | UMF owner | Current inspection/codec implementation | Supported public admission and inert temporal descriptor/custody surfaces; exported installed/portable parity. |
| TC-2 | Truss | TC-1 | Prep2.1 original-byte/descriptor retention, inverse local coverage, native property/cache/value ingress and replay; stripped/foreign descriptors refuse atomically. |
| TC-3 | Truss | TC-2 | New native identity, explicit ABI1.3 capture and enrolled STABLE buffered source shims; original caller/ACL/role/limits and one READ COMMITTED statement snapshot. |
| TC-4 | Weft owner | Agreed TC-1/3 interfaces | Exact temporal lowering and whole-program check APIs above; real backend vectors and portable parity. |
| TC-5 | Truss | TC-1–4 | Current target capture/dispatch/decoder, final authority/deadline/settlement checks; genuine public all-three-kind execution. |
| TC-6 | All owners | TC-0–5 | Exact installed source/wheel/native tuple, security/snapshot/refusal controls and browser parity; then select release qualification. |

## Execution Contract

The owner has authorized integration and qualification. Work remains Truss-only;
route UMF/Weft patches to their existing owners. No additional human authority is
missing. No spending ceiling or reliable aggregate token meter was specified.
Do not publish or mark temporal support qualified from a carrier/parser pass.

## Continuation Evidence

TC-0 is implemented in `contracts.py` and exported from `truss`. Unlike the old
snapshot, it is deliberately excluded from the current `ExactValue` union:
current wire, container and native paths retain their closed acceptance scope.
Four carrier/refusal tests, six existing public-contract tests, ten record-schema
tests, eleven import-contract tests, and the updated 1739-import module boundary
check pass locally. The same 31 tests pass from a clean wheel in a fresh
installed environment, with all 450 wheel payload files matched to source.
[Linux run 41517549989](https://github.com/DocumentDrivenDX/truss/actions/runs/41517549989)
passes the actual map and all 23 positive/negative boundary controls. The slow
local duplicate of those controls was stopped after that unchanged-source pass;
it is not credited as a local success. [Original scoped receipt](evidence/temporal-current-baseline-20261102/receipt.json).
Full temporal support remains unqualified. Source/guard/compiler/target patches
are not applied speculatively.

## Validation Plan

For TC-2–6 reuse the original snapshot's native test modules, retargeted to the
new owner cohort: `test_temporal_catalog_transport_native.py`,
`test_local_timestamp_query_native.py`, `test_temporal_engine_native.py`,
`test_temporal_source_guard_native.py`, `test_temporal_source_security_native.py`,
`test_temporal_target_release_native.py`, and `test_access_temporal_codec.py`.
Actual public acceptance/apply must create the local property;
direct SQL seeds cannot substitute. Check descriptor removal, retained/replayed
summary2.1, existing timestamp fidelity, complete-source invalid rows excluded
by user filters, later invalid rows, source overflow, concurrent writer snapshot,
wrong roles/ACL/ABI, revoked final authority, deadlines and confirmed cleanup.
Record failed attempts and exact immutable input bytes. Only then select the
changed-cohort Linux release gates; earlier baseline passes do not transfer.

## Risks and Rollbacks

The historical native0.75 label and CONTRACT-082 reference collide with current
meaning; resolve actual source/profile identities before dependent captures.
An exposed owner helper without inverse native coverage could silently turn a
local field into timestamp; keep TC-2 refusal checks mandatory. Disable only
the new capability on failure. Preserve old source/property/cell meanings and
the 0.0.53 baseline; never patch historical evidence to qualify this work.

## Exit Criteria

TC-0 alone closes only the standalone carrier prerequisite. Temporal integration
closes after TC-1–6 pass with the exact owner/native cohort, original request
custody, native security/snapshot evidence and real browser parity. No migration
or managed-host support follows from fresh temporal installation evidence.
