---
ddx:
  id: truss-legacy-catalog-removal-20261019
  type: implementation-plan
  activity: build
  status: draft
  links:
    - id: ADR-008
      kind: informed_by
    - id: truss-operation-statement-audit-20261019
      kind: informed_by
---

# Bounded legacy catalog removal review

This records the initial static removal review and its explicitly authorized
caller-cleanup follow-up. The initial review deleted no files; implementation
and focused verification are recorded below. It is not release qualification. The owner selected UMF
`0.10.0` exclusively and withdrew old-format admission and old-installation
upgrades; live revisions within the current catalog remain supported. The
[current release scope](releases/v0.0.40.md) and [ADR-008](../02-design/adr/ADR-008-trusted-embedding-host.md)
retain actual source bytes, diagnostics, history and ordinary caller authority.

Automatic approval review rejected the earlier broad deletion because its scope
was not sufficiently bounded to old-format compatibility and could remove current
functionality. The proposal contained 37 source modules, **23 tests** (the earlier
22 count omitted `acceptance-profiles.test.ts`) and six scripts. This review narrows
the source removal to 20 old-inspector consumers and their reverse dependency
closure. It does not infer obsolescence from an unused filename or an old fixture.

## Current roots and reachability

The inspected checkout is `/private/tmp/truss-performance-release-20261018`.
Relative static imports/re-exports and literal dynamic imports were resolved over
`packages`, `scripts` and `tests`, excluding dependencies and generated `dist`.
Both runtime and type-only import edges count as dependencies. Nonliteral host
paths, subprocess commands, source inventories and generated bundle markers were
also checked separately. This is source analysis; no build, browser or PostgreSQL
execution was performed.

| Current root | Required UMF-Bun source closure |
| --- | --- |
| `python-preparation-core10.ts` | `catalog-input.ts`, `acceptance-input.ts`, `index.ts`, `catalog-declarations.ts` |
| `index.ts` package export | `UMF_CORE10_CATALOG_SOURCE`, `loadCore10CatalogOwner`; neither exports an old inspector loader |
| `python-keys.mjs` | actual core10 producer `readJsonValue`, `validateSemanticTypesDocument`, `encodeCoreKeyTupleBody` |
| Browser `packages/browser/store.ts` through `catalog.ts` | `catalog-declarations.ts` and actual core10 producer |
| Portable `packages/postgresql/src/index.ts` | no proposed old transcript module |
| Portable `packages/weft/src/index.ts` | no proposed old transcript module |

`scripts/build-core10-catalog-producer.py` builds only the current preparation
entrypoint, copies the current key bridge, and packages the actual core10 producer.
`scripts/build-python-embedded.ts` selects `_umf_core10`, current query/disclosure
owners and preparation sources. The generated `_umf_core10/preparation.mjs` source
markers independently show only acceptance/input/index/declaration/current-prep
modules. `packages/browser/build-assets.ts` explicitly inventories the declaration
projection and core10 producer and builds `store.ts`. **None of the 20 source
candidates below is reachable from these current roots.**

An import from a candidate into a retained utility is not a reason to remove the
utility: dependency direction matters. Conversely, every source module importing
one of the old-only seed modules is included in the 20-module reverse closure.

## Proposed source removal: 20 modules only

The old-only seeds are `catalog-assertion-observations`,
`catalog-core-assertion-identities`, `catalog-observation-coverage`,
`catalog-type-receipts`, `catalog-type-journals`, and
`catalog-endpoint-intent-basis`.

| Seed | Concrete old-format dependency |
| --- | --- |
| Assertion observations | imports removed `loadUmfDeclarationProducer`, field/scalar/member/reference inspector loaders and loader recognition |
| Core assertion identities | hardcoded 0.7/0.8 source/result versions and reconstructed old inspector meanings |
| Observation coverage | imports removed `UMF_CORE08_CATALOG_SOURCE` and old inspector profiles |
| Type receipts | removed `loadUmfRecordTypeReceiptProducer`/recognition; composes old inspector receipt evidence |
| Type journals | explicitly requires document/base `umf === '0.7.0'` and old journal producer |
| Endpoint intent | explicitly requires `umfVersion === '0.7.0'` candidate extension source |

The remaining entries consume those seeds directly or through report/origin/context
assembly. They are old report-path wrappers, not shared numeric or byte primitives.
Exact source hashes bind this review to the inspected files:

| Path under `packages/umf-bun/src/` | SHA-256 |
| --- | --- |
| `catalog-admission-configuration-basis.ts` | `851e6fb7adf138a81b057a959a60e426bcdc0fe50e9313abe367e5518d3da020` |
| `catalog-asserted-origin-basis.ts` | `7b0f3b206a83bd9a9cdf16e6249118e70ba115eca86ff2e417d2b4849e8e705a` |
| `catalog-assertion-observations.ts` | `653ec4bb3b14e7dddc92daba7d1ba48e9fb544edafafd2f02220785b74d696f2` |
| `catalog-captured-origin-basis.ts` | `1a6e7e166c836db6b0ad0a6f1a5b27fd362a65f9abc9a7cd955edb25e64e03d4` |
| `catalog-configuration-basis.ts` | `28817be4e758600c3dfe9eddc399a678663a4f754a69fd3ba6b9d634d453e912` |
| `catalog-core-assertion-identities.ts` | `8e26b39365daedde304410f6e591e6b5430a9c5251792ffb404b5799fd885f10` |
| `catalog-endpoint-document-order.ts` | `29ace48b761f10e3c2efcf22f072c219ed201bd2c20ee5fda15a378a5493a07a` |
| `catalog-endpoint-intent-basis.ts` | `145a7c89f689c3bbe04094f69c0584000d1e4b7ed4cd2ee83b9549e7487be2ce` |
| `catalog-endpoint-records.ts` | `667c59a81da72837cc16a22f6fe8eb300e46f50dbef84c0023ebbc46ba750ce1` |
| `catalog-epoch-context-basis.ts` | `6facb1d0e919ea6500a6ff20f7b3dd894dcdded7cfc3eee8d7cb4317661591a6` |
| `catalog-execution-report-candidate.ts` | `853775e600eb34a16d433822d17e16d7f89d025ee235b2bdcc58f54d52ec9c1d` |
| `catalog-facet-rule-families.ts` | `fae5993d3158b95255331278d2a92166a5ec8250ddaa4ec92c33babb9c4ea6fb` |
| `catalog-observation-coverage.ts` | `bbc6b8d6ecc05e2739bb4120c0e05a4f62dbe0a1424ba19fea2616c561175eb6` |
| `catalog-original-execution-basis.ts` | `f8ef3b4d5ab546e0a3ef41a518222b4aeaff8a4c9039c7ae1116e0489a2f64c8` |
| `catalog-original-occurrence-inventory.ts` | `6af7c476eb6d61f085b4192a686925da024e4f475c82ad44f5c636fb6144c7ec` |
| `catalog-record-type-rule-families.ts` | `7cacf010800021101d198ef7f5e56a7d1d82475069876c77d5692d14371d5c58` |
| `catalog-report-correspondence.ts` | `9f61ef14fd976528a5c0006785052625bf1352d75fa1ea27e9a39e901eec0eda` |
| `catalog-report-preparation.ts` | `77a6aec62efb160b89eb7faf7fdd303ab6e54f479fb20fe0347e74b7ca031683` |
| `catalog-type-journals.ts` | `10ad6464ecc70956ba354e3e66316eff1981cabf43fa1f7036394b508f47a55f` |
| `catalog-type-receipts.ts` | `3e49476e58c15c40885cb35bda993d4ecc68c1255192b14a6e8e8ae0a1879441` |

## Caller disposition required with that removal

The following 12 test files exclusively exercise the removed transcript/report
or old-inspector composition. Retire these with the source closure; their retained
historical evidence stays in Git and governed evidence files. This does not remove
current source-validation/key/history or browser tests.

- `tests/catalog-core-assertion-identities.test.ts`
- `tests/catalog-endpoint-intent-basis.test.ts`
- `tests/catalog-execution-report-custody.test.ts`
- `tests/catalog-field-shape-correspondence.test.ts`
- `tests/catalog-nullability-correspondence.test.ts`
- `tests/catalog-record-members-correspondence.test.ts`
- `tests/catalog-reference-links-correspondence.test.ts`
- `tests/catalog-report-preparation.test.ts`
- `tests/catalog-scalar-type-correspondence.test.ts`
- `tests/catalog-type-journals.test.ts`
- `tests/catalog-type-receipts.test.ts`
- `tests/umf-declaration-producer.test.ts`

Two direct script entrypoints likewise belong to the retired composition:

- `scripts/check-catalog-new-cohort.ts`
- `scripts/check-catalog-umf-membership.ts`

Seven historical Python cohort runners invoke `check-catalog-new-cohort.ts`:
`check-type-journals-native-cohort.py`, `check-scalar-native-cohort.py`,
`check-type-receipts-native-cohort.py`, `check-record-type-occurrences-native-cohort.py`,
`check-reference-links-native-cohort.py`, `check-record-type-duties-native-cohort.py`,
and `check-record-members-native-cohort.py`. They are additional dependent callers,
not a current runtime dependency. They must either be explicitly retired in the
same cleanup or retain an honest historical-only non-runnable status. Do not claim
there are no remaining callers while leaving these commands apparently runnable.

`check-original-occurrence-inventory.py` and `check-original-byte-custody.py` have
mixed source/test inventory lists containing retired files. Update only those
lists/old-composition invocations; preserve their version-neutral checks. The
first script's old record-duty inventory needs separate disposition; it is not
implicitly authorized for deletion by this manifest.

The additional `umf-runtime.test.ts` and `umf-field-assertion-producer.test.ts`
exercise only 0.7 upgrade/rollback or old field-inspector loading; they can be
retired with the withdrawn API. `check-umf-current-assertion-inspection.ts` is also
an old-source/old-loader probe despite its name. These are not part of the 20
source modules and must be named explicitly in any deletion action.

## Retain from the broader proposal

These 17 source files are **not approved for removal by this bounded review**.
Some may have only historical callers, but that alone does not establish that
their version-neutral meaning or tests should disappear.

- `packages/umf-bun/src/catalog-default-homes.ts`
- `packages/umf-bun/src/catalog-document-order.ts`
- `packages/umf-bun/src/catalog-endpoint-source-references.ts`
- `packages/umf-bun/src/catalog-extension-artifacts.ts`
- `packages/umf-bun/src/catalog-extension-inventory.ts`
- `packages/umf-bun/src/catalog-ingress-report-basis.ts`
- `packages/umf-bun/src/catalog-new-stage.ts`
- `packages/umf-bun/src/catalog-pending-report-basis.ts`
- `packages/umf-bun/src/catalog-receipt-json.ts`
- `packages/umf-bun/src/catalog-report-document-basis.ts`
- `packages/umf-bun/src/catalog-source-reference.ts`
- `packages/umf-bun/src/catalog-transition-correspondence.ts`
- `packages/umf-bun/src/catalog-type-journal-evidence-budget.ts`
- `packages/umf-bun/src/catalog-umf-membership-candidate.ts`
- `packages/umf-bun/src/catalog-umf-report-basis.ts`
- `packages/umf-bun/src/catalog-validation-evidence.ts`
- `packages/umf-bun/src/acceptance-profiles.ts`

In particular, `catalog-document-order.ts` is a bounded graph/SCC ordering utility;
`catalog-receipt-json.ts` is a guarded JSON decoder; `catalog-type-journal-evidence-budget.ts`
is a byte budget; `catalog-transition-correspondence.ts` compares supplied values;
and `acceptance-profiles.ts` is registered profile-byte custody. Preserve their
unit tests. `canonical-report-handoff.ts`, outside the proposed 37-source list,
and `canonical-report-handoff.test.ts`, `composed-report-handoff.test.ts`,
`original-byte-custody.test.ts`, canonical-wire/JSON/scanner tests must remain.

Preserve `umf-numeric-runtime.test.ts`'s context-free exact-number tests. Its old
field-context test and loader imports require current-owner migration or a split;
deleting the whole file would lose lossless-conversion coverage. Similarly,
`umf-source-numeric-admission.test.ts` tests number-loss and opaque-content
preservation, and `umf-value-runtime.test.ts` tests canonical key bytes/value
boundaries. Port these purposes to actual current core10 validation/key realization
rather than deleting them solely because their fixtures/loaders are old.

Keep `check-umf-numeric-browser.ts`'s context-free browser numeric checks and
`check-umf-value-browser.ts`'s canonical-byte/browser coverage; replace only withdrawn
source-specific loaders/fixtures. `check-operation-admission.ts` mixes retired
preparation with native issuer/custody behavior, so it requires a scoped update,
not automatic deletion. Preserve current browser acceptance-JSON, canonical-wire,
original-byte and current-numeric scripts.

The other tests from the original 23-file proposal—document order, endpoint source
references, extension inventory, report document basis, transition correspondence,
acceptance profiles—remain until their independent purpose is specifically reviewed.

## Completion checks and limits

Before removing the narrowed set, name every affected path in the action, account
for the historical subprocess callers above, and confirm no new current import
has appeared. After removal, check source resolution/build boundaries and run the
retained current validation, numeric/key and browser tests. A static graph does
not establish behavior by itself. The installed current producer and actual
0.10 source validation still need their normal final qualification.

This document neither grants publication approval nor authorizes removing
version-neutral modules, live catalog history, actual diagnostics or current
protected query/disclosure functionality. It supplies the bounded evidence for
the narrower cleanup, not the rejected broad deletion.

## Follow-up caller cleanup, 2026-10-19

The owner additionally authorized retiring the seven historical Python cohort
runners, the old `umf-runtime`/`umf-field-assertion-producer` tests, and the
`check-umf-current-assertion-inspection` probe listed above.
`check-operation-admission.ts` is also retired: it hardcodes a PostgreSQL17.9
pre-install component endpoint, layout0.15 and old-format owner/checkRecord/key
receipt APIs. It is not the current installation path. Current installed-native
custody, history, rollback and key tests remain the corresponding functional gates.
The owner explicitly rejected maintaining that withdrawn experimental harness by
porting its source to 0.10. Git retains the old source and evidence.

Neutral numeric and key coverage is migrated to actual current owner source,
context-free exact-number APIs and the shared key-body primitive. This is not a
claim that the upstream version-specific old public key receipt API supports0.10.
The numeric browser corpus retains all cases; field-context cases use actual
0.10 validation plus key-field constraints and preserve their boundary categories.
Mixed byte/occurrence script inventories are updated to retained current tests.

## Focused follow-up verification

The explicit narrowed removal and follow-up retirements now total **45 files**:
20 old-only source modules, 14 dedicated old-API tests and 11 scripts. No neutral
source module was removed. Current preparation, source-number loss/opaque-content,
canonical-key, graph-order, declaration, JSON, wire, custody and profile-resolver
coverage remains.

- Bun1.4.3: **143/143 tests passed**, 1,123 assertions across19 retained files.
- Strict TypeScript: all current UMF-Bun modules and those19 test modules pass.
- Chromium153.0.8010.12:16 exact-number/field-boundary corpus cases pass.
- Chromium: actual010 validation, unchanged expected UMFK1 bytes and scale,
  precision, width and component-order refusal pass.

The [bounded cleanup receipt](evidence/legacy-catalog-removal-20261019.json)
records every retired path, exact commands, source hashes and raw-log hashes.
Browser runs use a loopback-only server; the sandbox initially prevented listening,
then the authorized loopback execution succeeded. No PostgreSQL or installed
Python-asset rebuild occurred. Native/full-package release qualification remains
separate. The final type-only annotations and removal of an unused old producer-mode
fallback followed the passing Bun run; strict checking followed those edits.


## Additional fixed-format utility disposition

`export-current-security-native-binding.py` was a one-packet probe bound to
source SHA `2216a7ad3093c90437db035fb337d21ac67589dee5eb148b0eb4d7fd1ff75059`
and a matching fixed scenario SHA. A repository-wide source/caller search found no
workflow or module caller outside the script and retained historical evidence.
The current 0.10 initialize/request fixtures have a different envelope and do not
contain the old owner/fact-scenario payload; changing the hard-coded version or
checksum would misstate provenance. The stale runnable entrypoint is therefore
retired; historical evidence remains unchanged. Current preparation utilities
accept only actual UMF 0.10 inputs and derive `source_version` from those
validated documents.

## Retired publisher recovery

Removed `.github/workflows/promote-python-release.yml` and its sole helper
`scripts/check-python-release-promotion.py`. They exclusively recover a fixed
predecessor publisher recipe and 15-minute post-success cancellation, refer to
the removed date08 policy and cannot accept the current publisher recipe.
No live workflow or package script calls the helper. Current releases use the
normal tested tag publisher; no replacement recovery machinery is added.

## Preparation-program fixture disposition

The current `packages/browser/fixtures/local-products-model.json` is the actual
UMF 0.10.0 source used by the retained action-store and seal-storage workflows.
It contains no separate compiler configuration or request. The old positive
program-registration, binding, selection, data-claim, bridge-inventory, and
compiler-replay tests depended on a different predecessor packet with those
fields and its pinned compiler artifacts. They are retired rather than
relabelled or given fabricated compiler output. A current-source refusal test
remains and confirms that requesting registration without a current compiler
request fails before creating workflow output. This does not claim a current
compiler-registration workflow is qualified.

## Current driver fixture

Retired the stale `test_psycopg_pg17_native.py` prerequisite-fixture wrapper
after its withdrawn component fixture was removed. Its three current PG18.6
profile/timeout controls now use the ordinary native fixture in
`test_psycopg_profile_native.py`; inherited tests are not repeated. The old
prerequisite-export and uncertain-startup harness tests are retired with that
harness. This preserves the current driver behavior checks without retaining an
obsolete fixture chain.

## Generic private program components

The proposed removal of the generic private program/literal-permit implementation
and SQL assets was not applied. Those interfaces are version-neutral; lack of a
current compiler fixture does not establish that their implementation is solely
legacy. Their storage and custody code remains separate from supported source
formats. The compiler input boundary now rejects every source/pin other than
actual UMF 0.10.0 before invoking the configured compiler. A forged 0.10 pin on
an older source also refuses. Two offline tests cover the unavailable current
exporter request and this format boundary; a 0.10 request reaches the configured
compiler without claiming that its external implementation supports it.
