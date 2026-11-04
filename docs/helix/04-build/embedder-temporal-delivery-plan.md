---
ddx:
  id: truss.embedder-temporal-delivery-plan
  type: implementation-plan
  activity: build
  authoring:
    home: repo
  links:
    - id: truss.temporal-current-baseline-plan
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
---

# Embedder and temporal delivery plan

## Scope

Deliver the five Arras embedder corrections, the bounded legacy-read compatibility
in Arras issue 36, and genuine Truss temporal acceptance and execution. Merge
reviewed changes and publish each affected ready package. A standalone temporal
carrier or an owner handoff does not complete temporal delivery.

Governing sources:

- Arras `docs/helix/02-design/downstream-extensibility.md`, ADR-019, ADR-022,
  ADR-029, and CONTRACT-002/005/010; its project principles, test plan,
  integration plan and deployment checklist govern Arras qualification.
- [Current temporal plan](temporal-current-baseline-plan.md), Truss CONTRACT-010
  and CONTRACT-012, and the original temporal source/guard contract and TX-0–6
  plan referenced there govern native composition.
- UMF CONTRACT-070 and CONTRACT-075 govern selected access temporal meaning.
  Their current owner implementation must be reconciled before freezing exports.
- Truss release and PyPI workflows govern exact-tag and public artifact delivery.
- [Current installation policy](local-runtime-installation-migration-plan.md#current-baseline-direction--2026-11-02)
  and the published 0.0.54 scope govern the post-reset installation boundary.

## Shared Constraints

Sol 6.1 medium owns planning and review. Luna owns implementation, tests, CI,
merges and releases. The Arras primary checkout remains untouched; all Arras
writes use managed sibling worktrees with disjoint writer scopes. Truss uses the isolated checkout.
Existing UMF Rust and UMF/Weft owner checkouts are exclusive to their owners.

One issue per embedder item; reuse issue 36 for both view and graph read aliases.
Each fix has a changelog entry, failing-before/passing-after behavioral evidence,
and present-tense public documentation. Shared changelog, package versions,
lockfiles, generated acceptance inventories and release pins have one integrator.
Workers return patches for those files instead of concurrently modifying them.

## Implementation Slices

| Slice | Owner write scope | Dependency | Acceptance gate |
| --- | --- | --- | --- |
| A0 | Luna operations: sibling worktree, five issues and issue36 tracking | None | Current remote source and clean primary recorded; no design/code edits. |
| A1 | Luna Python: `src/arras/devhost.py`, focused help tests | A0 | Effective `main(operator_groups=...)` default appears in help and runtime; canonical defaults and CLI overrides agree. |
| A2 | Same Luna Python: devhost, distribution configuration, relevant UI tests | A1 | Explicit theme manifest reaches existing `create_app`; stock wheel UI serves verified theme assets, CLI takes precedence, inert configuration performs no I/O. |
| A3 | Same Luna Python: `ui/assets.py`, `ui/__main__.py`, manifest tests | A0 | Optional appearance light/dark round-trips through builder, CLI and loader; absent stays absent; invalid values refuse. |
| A4 | Separate Luna alias owner: `src/arras/alias.py`, `tests/test_alias.py`, API docstrings; changelog suggestions only | A0 | Local attributes/shims and original `__getattr__` win independent of import order; explicit closed `__main__` documented and tested. |
| A5 | Luna UI: `ui/e2e/host-isolation.spec.ts`, testkit docs and focused host fixtures | A0 | Bare synthetic assertions and host-owned appearance checks are separated; root and ancestor providers pass without disabling isolation/nonmutation assertions. |
| A6 | Luna compatibility: explicit policy plumbing in parser/view/graph/config/backend/browser code and focused tests | A1–3 shared distribution/config integration; policy review | Empty policy preserves refusals; alias/canonical parity, byte custody, collision refusal and native/browser round trips pass. |
| T0 | Sol and existing UMF/Weft owners: contracts and interface reconciliation | Current owner source inspection | Agreed public signatures, profiles, digests and native identity; no competing semantic implementation. |
| T1 | Existing owner Luna: UMF public inspection and inert Access engine custody | T0 | Installed Python and portable/browser exports match owner vectors and refuse unknown profiles. |
| T2 | Truss Luna: Prep2.1 catalog/value/import/cache transport and native local carrier | T0–1 | Original bytes and inverse descriptor coverage survive public accept/apply and replay; missing or foreign descriptors refuse atomically. |
| T3 | Truss Luna: new native ABI/source shims and security captures | T0, T2 | Complete bounded source validation precedes user filtering; same statement snapshot, caller/ACL/role/caps and cleanup proved. |
| T4 | Existing Weft owner Luna: guarded read/page lowering and whole-program checks | T0; shared T3 vectors | Date/instant/local operations, parameter separation, full continuation and tamper refusals pass. |
| T4A | Truss Luna with Weft owner: default compiler/cohort adoption | T0, T4 | New owner distribution/envelope passes authentic default ABI1.2, unchanged HF62 assertions and native regressions; original producer deltas audited. |
| T5 | Truss Luna: compiler dispatch, target capture, decoders and public integration | T1–4, T4A | Exact released owner/native tuple passes native temporal and existing ABI regressions. |
| R | Luna integrator/release worker, Sol review | Ready slices and exact candidate proof | Main merge, exact tag, distribution parity, public bytes and fresh consumers pass. |

Arras A1–5 can start immediately. Avicenna owns devhost/distribution/assets;
the independent alias owner owns alias.py and its tests; the UI owner owns
appearance acceptance files. Workers leave staging and commits to the integrator.
A6 starts after the Python worker yields and its shared distribution/config
changes are integrated, to avoid
concurrent distribution/parser/config edits. A6 may design policy and fixtures
while A1–5 execute. Each worker authors only its scoped contract/test-plan
sections; integrator serializes shared documentation changes.

## Interface Freeze Decisions

### Arras

1. Operator defaults remain the existing `devhost.main(operator_groups)` seam.
   Correct effective help text; do not move authorization policy into branding.
2. Add `DistributionConfig.theme_manifest: str | None = None` and
   `--theme-manifest` to devhost. Reject non-string, empty and NUL-containing
   configured references without touching the filesystem. CLI overrides
   configuration; omitted means existing behavior. Convert the effective
   reference to `Path` only at the host/UI seam. Use the current UI manifest
   loader, compatibility, containment, integrity and CSP controls.
   `DevHost(..., theme_manifest: Path | None = None)` permits an explicit host
   override. The existing devhost static handler is separate from UI creation:
   compose `arras.ui.create_app` for themed page/assets while preserving its
   existing API/control/explorer routing and unthemed/custom-directory behavior.
3. Builder `appearance: str | None = None` is exactly light/dark when supplied;
   CLI `--appearance` has those choices. Reject invalid values before output
   effects. Single-appearance
   themes declare it; dual-appearance themes omit it. No inference from CSS.
4. Alias resolution preserves local attributes, then the original getter, then
   genuine local modules before target fallback. Only the getter's
   `AttributeError` permits fallback; other errors and a real shim's import
   error propagate.
   Keep closed entrypoint lists explicit, including `conformance.__main__`.
5. Host appearance declarations select applicable assertions, never observed
   failure. Preserve real host switching, root/ancestor token behavior, contrast,
   outside-root isolation and nonmutation. No blanket skip of host tests.
6. Issue36 uses `DistributionConfig.view_vocabulary_aliases: tuple[str, ...] = ()`
   and `graph_format_aliases: tuple[str, ...] = ()`. The lists become immutable
   explicit per-instance policy; never infer them from brand. Aliases select
   exactly canonical version/semantics. New
   outputs are canonical; stored original document bytes remain unchanged.
   Refuse canonical-plus-alias and multiple-alias ambiguity, reserved/colliding
   names, unsupported versions and unknown terms. Diagnostics name source keys.
   Thread policy through existing server parse/read paths and explicit browser
   `parseGraphFile` per-call options (omitted options remain empty). The stock
   page exports only: no alias HTML metadata, page import control or global
   browser policy is required. Never recursively rewrite arbitrary keys.

Before A6 code, update ADR-022 and CONTRACT-002/005/010 for this selected
compatibility policy and review the exact API plumbing. Include graph aliases
because issue36 explicitly covers them. No parallel branded dialect is created.
These amendments now also cover CONTRACT-003 graph reads, ADR-019 precedence and
the naming inventory. CONTRACT-005 owns the exact bounds, immutable tuple
carrier, additive plumbing signatures and policy-aware cache identity. A6 must
read those sections rather than reconstructing the API from this plan's summary.

### Temporal

Freeze ownership and semantics now; freeze wire identities only after T0 owner
reconciliation. UMF supplies resolved access inspection and original-program
descriptor custody. Weft supplies compiler parsing/lowering/checking. Truss
supplies native transport, protected guarded source, target capture and execution.

Retain CONTRACT-075 strict grammar and separate instant/local/date selection.
Bare timestamp labels cannot infer selection. No temporal Keys or numeric
selected-Key paging are admitted by this scope. Preserve original token meaning,
unknown content and explicit unsupported refinements.

Historical proposed engine0.4/profile0.2, compile0.2.10 and ABI1.3 remain proposals.
The four proposed Weft shape/current read/page checker signatures in the current
temporal plan can be replaced only by a reviewed owner-equivalent contract.
The whole original program, SQL, parameters, outputs, caps and source guard
participate in custody. Source validation covers filtered-out and later rows.

Reserve new native release identity
`truss-catalog-runtime/0.76-temporal-candidate`. It is absent from the inspected
current main and retained snapshot source. Its actual manifest/descriptor digest
is computed from reviewed final bytes, never assigned in advance. Neither
conflicting `0.75-candidate` label establishes identity. Retain ABI1.2 meanings;
gate the additive temporal ABI explicitly.
Replace the stale CONTRACT-082 reference with the actual owner-approved binding
contract. No permissive conversion rule or old non-release bundle is inherited.

### Default compiler adoption and frozen evidence

Truss 0.0.54 selects `weft-sql==0.4.51` and `umf_access==0.1.0.dev5`, including distribution-name/version
assumptions in qualification/release tooling and the active HF cohort. Public
Weft 0.4.56 uses `umf-weft` and different selected envelope semantics. A version
or distribution-name substitution does not qualify compatibility.

T4A inventories every compiler dependency, import, interface/envelope selector,
embedded owner artifact, archive profile and release-producer binding. Preserve
the original 0.0.54 wheel, HF corpus, assertions and receipts as original inputs.
Exercise the new owner's ordinary ABI1.2 path independently of temporal ABI1.3:
default capture/compile/check/execute/decode, refusals, retained original program
and archive custody must pass real native behavior. Do not implement a second
compiler or translate away a refusal to reproduce an old observation.

All 62 HF semantic assertions remain. Audit every changed producer file against
its original bytes, explain each effect and bind actual new producer hashes only
after review. Distribution/profile binding controls must distinguish the real
old/new cohorts, not pretend a renamed distribution is the old artifact. Retain
failed attempts; changed native/compiler inputs require their own complete gates.

### Installation selection for the temporal release

Select **fresh-only publication** for this temporal cut, under the current
fresh-install baseline policy. This decision does not admit a 0.0.54-to-new-native
migration. No migration recipe or new recovery authority is published in this cut.
Do not replace the current-only six controls with the retired 153-case matrix.

The new runtime must use a collision-free release identity and authentic complete
native inventory; current 0.0.54 manifest `5ecb599f65d64e6656bf6c83c30cea6e2aefd488cb3fe821b749458d5e9b3522`
is native `0.75-candidate` with ABI1.2. The preserved temporal snapshot's different
bytes under the same label cannot be an admitted source or target identity.

Use the real public 0.0.54 wheel, with verified public digest, to produce a
populated current installation for negative compatibility controls. New tooling
must refuse that existing namespace/tuple without changing original properties,
cells, source documents, history, ACLs or retained requests. It must not reinterpret
previously retained temporal metadata, reset, import, upgrade or rewrite on startup.
The old installation's application/data remain untouched by the attempted new tool.
The fresh target independently proves the new temporal capability.

Release notes and machine-readable pins must explicitly say fresh-install-only
and no 0.0.54 installation upgrade. Retired 0.0.47/48 migration and receipt
lineage remain refused. Never alter clock or native inventories to gain admission.
Any later upgrade requires a separate explicitly qualified immutable current54
edge using this authentic public-wheel source, preservation/failure/settlement
tests and exact current source-to-target evidence; historical fixtures cannot
stand in for it. Fresh-only is an explicit support boundary, not a passed migration.

## Execution Contract

### T4A-P: approved authentic compatibility probe

This probe is immediately authorized independently of TC1/TC4 implementation.
It determines raw compatibility, not temporal acceptance or final cohort adoption.

Inputs: public `umf-truss==0.0.54` wheel
`4aebc56e92fdbde6714d9b811860707d2ffc9b0edbc63cc91e9dc3488c042b52`,
its original `weft-sql==0.4.51` dependency, its checksum-verified native package,
and current-main test fixtures at `aef15a9b`. Candidate replay environment:
`/private/tmp/truss-temporal-owner-probe`, with actual public `umf-weft==0.4.56`.
Use separate environments so their shared `weft` import namespace cannot collide.

Approved source producer:
`packages/python/tests/test_query_stream_abi12_native.py`,
`QueryStreamABI12Tests.original()`, using
`test_group_create_native.PublicCreateGroupTests.ready()` through its existing
fixture ancestry. It installs/accepts a real native catalog, configures real
consumer roles and creates three rows through public operations. Its query is
`SELECT a."A-label" FROM "A" a WHERE a."A-value"=:wanted`, `wanted='same'`,
page size 2, maximum scan rows 10. The actual compiler request contains the
fresh native binding, model bytes/pins and exact parameter inventories.

Allowed writes: new `scripts/probe-weft-abi12-cohort.py` and
`packages/python/tests/test_weft_abi12_cohort_probe_native.py`, plus scoped
evidence under `docs/helix/04-build/evidence/temporal-t4a/`. Adapt the original
helper's assembly/capture steps in the new harness; do not edit its original
assertions or synthesize a request. No production source, dependency pins,
compiler guards, HF corpus, native SQL/profile, publisher or owner source edits
are allowed in this first probe patch.

1. In an isolated old-cohort environment, load installed public54, not source
   Truss. Run only the existing
   `QueryStreamABI12Tests.test_actual_selected_cursor_decodes_all_batches_and_descriptors`
   baseline and the new capture case. Disable inherited unrelated test discovery.
2. Observe the real compiler-call boundary while forwarding its original
   callable, request string and page/continuation arguments unchanged. Persist
   the exact UTF-8 request string before parsing, original binding JSON string,
   actual compiler entrypoint/arguments, old compiler response, engine-page
   input/program and payload hashes. Retain normal result/descriptor assertions.
   An observational wrapper may record inputs/results; no guard or native
   binding may be replaced. Existing parsed `captured[-1]` alone does not retain
   exact compiler input bytes, so preserve the incoming string as well.
3. In the separate 0.4.56 environment, verify source/public54 Truss's unmodified
   `compiler()` returns None at its cohort guard. Record this guard refusal
   separately. Do not patch it to obtain capture or claim adoption.
4. Call the actual public 0.4.56 raw compiler on the unchanged captured request,
   and its page API using the actual captured arguments. Replay the original
   engine-page input and use the documented ordinary checker signatures on
   freshly produced or original whole programs, retaining input hashes. Do not
   repair version, binding, profile, SQL, output or parameter fields. If an API
   signature/format refuses, retain the exact error and stop that dependent call.
5. Classify each raw result as compiled/checked, structured refusal or exception;
   retain diagnostics without inventing an expected success. A raw refusal is
   a valid probe finding and blocks adoption; it is not a passed T4A gate.
   Raw compilation alone authorizes no execution of candidate SQL against a
   stale captured binding and no native acceptance claim.
6. Use one owned local native cluster with the existing statement/deadline limits;
   close handles/connections, confirm server stop/status and PID absence before
   deleting owned data. Keep failed original evidence. No hosted campaign or
   full HF matrix runs in this diagnostic slice.

Return the small patch, source/package/input hashes, original baseline outcome,
guard outcome, raw result bytes, cleanup proof and the concrete smallest next
compatibility change for Sol review. Then implement the reviewed boundary change
and run real default ABI1.2/HF62/native adoption on the final selected cohort.

Full implementation, qualification, merges and publication are human-authorized.
This lead authors plans and reviews; it does not implement or run qualification.
Existing owner chats retain their write ownership and frozen release inputs.
Queue needed additions behind those inputs or use their approved isolated branch.
Do not treat active migration ingress work as temporal implementation evidence.

Token range and total spending ceiling are unknown; no ceiling was supplied.
No dependable aggregate meter is available. Keep expensive qualification selected,
retain passing artifacts and rerun only failed jobs when source is unchanged.

## Validation Plan

- Before feature work, identify each repository's actual module-boundary command
  and keep its positive/negative controls: Truss uses
  `python scripts/check-module-boundaries.py`; Arras uses
  `python -m pytest -q tests/test_boundary.py` in its full test suite, exercising
  `arras.boundary` with explicit host/library inputs (an empty CLI check refuses).
  Do not expand baselines to hide new imports.
- Arras source: focused reproductions, full Python tests, lint/types/build,
  installed doctor, official UMF admission and generated actions, Truss adapter,
  source/sdist/wheel parity and packed browser acceptance with both host profiles.
- A6 native: register/read existing aliased documents without re-registration,
  compare exact stored/returned bytes, canonical generated graph output and
  views, simultaneous hosts with different policy, refusal with no mutation.
- Temporal: retarget all seven native/codec test modules named in the current
  temporal plan. Exercise public accept/apply, descriptor loss and replay,
  invalid excluded rows, overflow, concurrent writer snapshot, ACL/role/ABI
  mismatch, revoked final authority, deadlines and original cleanup.
- UMF/Weft: real installed exports and selected-profile native/Chromium parity;
  complete-program tampering and pre-epoch exactness controls. Helper tests or
  copied frozen inventory cannot establish integrated support.
- Compiler adoption: retain original HF62 assertions and prove new-cohort
  ordinary ABI1.2 native behavior before temporal dispatch qualification. Inspect
  actual envelope differences and preserve original program/archive custody.
- Fresh-only boundary: public54-populated namespace refusal is atomic and
  independently compared before/after; fresh target current-profile six controls
  remain explicit. Add targeted controls instead of reviving retired lineage.

## Release Gates

Select versions from current remote tags/registries at release time. A bounded
Arras patch may ship before temporal dependencies; do not delay ready fixes.
Temporal native support selects a new Truss version and exact owner cohort.
Release notes declare supported subsets and retained refusals explicitly.

1. Sol reviews contracts and implementation diff against the frozen interfaces,
   regression evidence and failure controls. Luna resolves findings before merge.
2. Luna freezes complete candidate inputs, builds wheel/sdist and Arras carried
   npm archive, verifies full payload/source correspondence, and runs required
   fresh installed candidate gates. Rebuild after any packaged change.
3. Arras follows its deployment checklist and schema3 assembly: exact SDK
   admission/actions on Linux/Mac, UI/native and downstream checks. Retain
   managed evidence only with reviewed unchanged-input correspondence; changed
   managed/adapter behavior requires affected native/managed checks.
4. Truss runs exact changed-cohort Linux qualification, including fresh baseline,
   carrier, unchanged HF62 assertions on the adopted compiler, ordinary ABI1.2,
   public54 no-effect refusal, managed-grant and required native/security
   controls. Prior 0.0.54 success cannot qualify a changed native/compiler tuple.
5. Merge reviewed candidate to main, verify final source/qualified inputs, tag
   exactly that source, and complete mandatory exact-tag workflow gates.
6. Publish immutable GitHub assets, then trusted registry uploads from those
   exact verified bytes: Truss PyPI; Arras PyPI and npm; owner packages through
   their release workflows. Preserve original failed attempts and immutable tags.
7. Independently download public assets/registry archives, verify hashes and
   provenance, install fresh consumers, exercise actual exported capabilities,
   compare complete payloads and record cleanup. Arras extras use its required
   public-index Linux/Mac cohort. No release claim from an upload alone.

## Risks and Rollbacks

| Risk | Response | Rollback |
| --- | --- | --- |
| Frozen UMF release conflicts with new exposure | Existing owner selects a follow-on branch/cohort | Keep temporal capability unavailable until qualified. |
| Root token test hides a production defect | Test explicit host profiles plus unchanged isolation controls | Revert harness correction rather than weaken assertions. |
| Alias policy leaks between hosts | Immutable explicit policy through all call paths; simultaneous-host test | Empty policy restores canonical-only acceptance. |
| New native identity aliases old bytes | Bind source, ABI and full inventory digest | Refuse unknown/mixed targets; preserve installations. |
| Time-derived fresh baseline changes native inventory | Capture authentic current initializer and qualify explicit identity | Do not alter clock, relabel inventory or restore retired lineage. |

## Continuation Evidence

Initial planning inspection only; no implementation or qualification claimed.
Remote Arras main is de4a88a2 and Truss main aef15a9b. Arras issue36 is open
and includes both alias families. Existing UMF Rust owner is qualifying frozen
0.10.7 artifacts; UMF/Weft owner is doing migration creator-birth/ingress work.
Both owners were contacted for current interface reconciliation. Luna operations
prepared clean detached sibling
`/Users/erik/.codex/worktrees/arras-embedder-fixes/arras` at the Arras source above;
the primary is unchanged. Arras issues 49 (help), 50 (devhost theme), 51 (builder
appearance), 52 (alias precedence/entrypoint) and 53 (appearance acceptance)
are filed; issue36 is reused. Agreed temporal wire/profile identities and source
receipts remain pending actual owner reconciliation. Provisional cached audit
claims after DNS failure are not freeze authority.

The completed current-owner audit verifies public 0.0.54 wheel
`4aebc56e92fdbde6714d9b811860707d2ffc9b0edbc63cc91e9dc3488c042b52`,
its Weft0.4.51/Accessdev5 metadata, the different public owner envelopes and
the unavailable temporal public surfaces at the observed source/cohort.
The read-only 25-file T4A inventory is
`/private/tmp/temporal-truss-t4a-inputs-20261102.json`, digest
`30c6a1c96f71705e0250d76806ed610ed15045c48bc2fc59d61b40f2de38cbf8`.
It is a review inventory, not blanket permission to refresh producer hashes.

## Exit Criteria

All A1–6, T0–5 and T4A behavioral gates pass; changes are reviewed, merged and released.
All affected delivered packages have matching public bytes and passing fresh
consumers. Temporal support is demonstrated through genuine owner acceptance,
native transport and guarded query execution, not merely a carrier or handoff.
No required qualification, cleanup, owner patch or publication remains pending.
