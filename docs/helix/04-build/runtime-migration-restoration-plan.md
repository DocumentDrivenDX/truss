---
ddx:
  id: PLAN-RUNTIME-MIGRATIONS-001
  type: implementation-plan
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.prd
      kind: informed_by
    - id: ADR-008
      kind: informed_by
    - id: FEAT-007
      kind: informed_by
    - id: US-045
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
    - id: TD-045
      kind: informed_by
    - id: TP-001
      kind: informed_by
    - id: STP-045
      kind: informed_by
---

# Restore forward runtime migrations

## Scope

Support one runtime: latest. Preserve older databases by migrating forward to it.
The owner decision of 2026-10-21 restores migrations for UMF 0.10 and supersedes
the predecessor-upgrade withdrawal. Old application runtimes and pre-0.10 source
adapters stay retired. Historical manifests, recipes and test fixtures serve
migration only. The owner subsequently authorized implementation in this chat. The v0.0.47
release implements the bounded routes below; native qualification is reported
from original run evidence. Final installed migration qualification passes 52 cases
without skips on macOS ARM64 and Linux x86_64. The complete Linux release/public-
workload workflow also passes. Merge, tag publication and public clean-install
verification are complete;
the released delivery record below binds their original evidence.

Governing behavior: [PRD](../01-frame/prd.md#owner-decision--forward-migrations-to-the-latest-release-2026-10-21),
[ADR-008](../02-design/adr/ADR-008-trusted-embedding-host.md),
[FEAT-007](../01-frame/features/FEAT-007-conformance-and-portability.md) CNF-08,
[US-045](../01-frame/user-stories/US-045-bootstrap-the-internal-layout-from-umf.md) AC6–08,
[architecture](../02-design/architecture.md#latest-runtime-and-migration-boundary--2026-10-21),
[CONTRACT-008](../02-design/contracts/CONTRACT-008-layout-bootstrap.md) RM-01–07,
[TD-045](../02-design/technical-designs/TD-045-bootstrap-the-internal-layout-from-umf.md),
[TP-001](../03-test/test-plan.md) and
[STP-045](../03-test/test-plans/STP-045-bootstrap-the-internal-layout-from-umf.md) RM-T01–08.
CONTRACT-001/002/003/004/005/006/007/009 retain storage, journal, catalog,
mutation, authority, feed, host and lock obligations. Their selected current
interfaces must be checked before implementing each dependent slice.

## First route and inspected baseline

| Role | Exact starting evidence | Meaning |
| --- | --- | --- |
| Source | v0.0.44; runtime manifest SHA-256 `9f6aab31802e9bebcd886f735ba9fe0bb405e69d3501a32f36cee8827b544d00` | Initial populated UMF 0.10 predecessor; create fixture using its real released wheel |
| Current runtime baseline | v0.0.45 and locally available v0.0.46 tag; manifest SHA-256 `71c4c3d4c05a2229c4cdec1643cabe0da7055965f0b0d23195e83ad780042a2e` | Same native bytes despite different SDK labels; this candidate adopts v0.0.46 local runtime isolation and CLI fixes |
| Shared labels | `truss-catalog-runtime/0.72-candidate`, layout `1.0`, PostgreSQL 18.6 | Labels are shared across changed manifests and cannot establish compatibility |
| Target | v0.0.47; native `0.73-candidate`; manifest SHA-256 `7ac989147f22d437b1ce0d814ebbfaa25aa868ab5495de125aa5e2bda7b963ea` | Frozen native inventory, ordered recipes and UMF receipt model are packaged under `truss/_migrations/`; original published assets remain unchanged |

The first delivery is v0.0.44 → that exact target. Include admission from existing
v0.0.45/46 databases when their identical installed tuple is verified; their
ledger initialization/transition is a separate explicit source case, not an
inferred no-op. Do not extend support to every historical UMF 0.10 release without
source qualification. Inventory any additional existing installations in RM-S1;
unknown sources remain intact and explicitly unsupported until a route is added.

After a source joins this lineage, every subsequent release must keep a path to
latest. Retain immutable conversion recipes or compose them in the latest tool;
never require intermediate application versions. Migration-only compatibility
has no age-based expiry. This does not require maintaining older application
APIs, compilers or live execution profiles.

## Shared constraints

- Use Python 3.11+, stock psycopg 3.3.6, PostgreSQL 18.6 and the selected exact
  embedded UMF/Weft assets. Qualify any changed dependency tuple separately.
- Initial upgrade is explicit, offline, administrative and fully transactional.
  The migration session owns its transaction. Reuse the existing host recovery
  registry and installed target; choose one settlement owner, not competing
  caller-owned and tooling-owned commit paths. Existing draft bindings own the
  outcome meanings; update the public facade deliberately before implementation.
- Verify installed definitions and effective grants under exclusion. No marker
  rewrite, version-only success, regex-based replacement of all current routines,
  startup migration, automatic reset or implicit data import/export.
- Preserve every RM-03 inventory, exact scalar meaning, unknown content and
  original evidence. Bound scan/copy work; record fixture size and statement counts.
  Keep existing workload limits unless measurements justify explicit migration
  limits. Large-database runtime and disk bounds are measurements, not promises.
- A migration recipe is immutable after publication. Future destructive changes
  use expand/backfill/contract with preservation and forward recovery. Downgrades
  are excluded. Before commit, transaction rollback restores source; after commit,
  use a forward fix or a tested backup restore followed by migration to latest.
- Activated optional profiles require qualified transitions or pre-effect refusal.
  Ordinary unprotected-profile support does not qualify protected installations.
  Reuse current trusted-host/security services; unrelated security redesign,
  custom driver instrumentation and formal proof are not prerequisites.
- Hosted CI is Linux only. Local native tests use the development platform.
  Migration support claims name the exact database, dependencies, subset and
  platforms actually exercised. No new managed-service or cross-platform claim.

## Implementation slices

| Slice | Deliverable and dependency | Validation gate |
| --- | --- | --- |
| RM-S1 | Freeze v0.0.44 source, current target and exact SQL/ACL/encoding delta. Check current contracts, enumerate supported optional profiles, define receipt initializer, old-wheel admission fence and preservation inventory. No dependencies | Real source wheel installed and populated; full digest/definition correspondence; approved ordered recipe and explicit required conversions; source/target IDs never inferred from shared labels |
| RM-S2 | Map private recipe loader, verifier and executor behind public tooling/facade; update exact binding and host settlement ownership. Depends S1 | Existing module checker and controls gain explicit allowed/forbidden migration imports and pass before feature code. Actual old wheel's tuple checks prove fence design; otherwise add necessary entry-point fencing to the recipe |
| RM-S3 | Package immutable manifests/recipes and read-only status/verify/planning. Depends S2 | Fast tests reject missing/modified artifacts, malformed routes, unknown/pre-0.10 sources and downgrade; native verifier catches same-label routine/grant drift without writes |
| RM-S4 | Apply first route under administrator/source/writer exclusion, including missing-ledger initialization and target receipt publication. Depends S3 | RM-T01/02/03/05: real populated upgrade, independent preservation and latest API read/write/replay/feed checks, first-step/later-failure rollback and no intermediate readiness |
| RM-S5 | Complete original-attempt settlement, repeat and read-only reconciliation, durable restart recovery. Depends S4 | RM-T04/06: actual lost COMMIT response, confirmed commit plus failed verification, restart, changed recipe and exact-repeat behavior; no duplicate effects or blind retry |
| RM-S6 | Expose explicit public migration CLI and clean consumer deployment example; classify identical current tuples. Depends S5 | RM-T08: install exact packaged artifacts, backup, quiesce, inspect, apply, reconcile/verify, restart latest and reject old wheel; fresh install still refuses existing namespace. Existing v0.0.45/46 source cases verified separately |
| RM-S7 | Make migration lineage qualification a release gate and update current documentation. Depends S6 | RM-T07/08 plus existing release gates pass in clean installed packages. Retain every admitted source fixture. First real subsequent release demonstrates skip-release chain with latest tool only; absence of a future real edge is explicitly pending, not fabricated coverage |

S1–S2 are bounded design/adoption work. Do not let historical draft protected
profiles silently expand this route's scope. Do not reintroduce the removed
monolithic executor or pre-0.10 runtime branches. Use existing UMF models/exports
when storage adjuncts are required; no new semantic compiler is authorized.

## Module boundaries and commands

Private `_migration_recipe`, `_migration_verify` and `_migration_execute` own
recipe loading, verification and effects separately. `truss.migrations.RuntimeMigrations`
is the public administrative interface; CLI delegates to it. `catalog_runtime.py`
directs caller-owned upgrade requests to the separately owned boundary. Current application query/group/catalog execution cannot depend on
version-specific migration implementations. Existing host recovery and verifier
ports are shared dependencies; do not create a parallel registry/ledger authority.

Run `python3 scripts/check-module-boundaries.py` and
`python3 scripts/check-module-boundaries-controls.py` locally and in the existing
Linux boundary workflow; wire the same command into pre-commit when configured.
Review native SQL, dynamic loading, authorization and settlement semantically.

Fast suite: `PYTHONPATH=packages/python/src:packages/python/tests python3 -m unittest discover -s packages/python/tests -p test_runtime_migrations.py`.
Native suite uses the same command with `test_runtime_migrations_native.py`
inside an owned PostgreSQL 18.6 environment. The installed qualification command
below runs both plus all real lineage-source fixtures. The release workflow runs
this same gate before publishing; failed or skipped cases block release. Keep
historical receipts scoped to their original run.

## Validation plan and release policy

STP-045 is the acceptance matrix. Seed exact values, unknown extension content,
retained data, graph ownership, keys, catalog revisions/source/reports, mutation
receipts/history, import provenance/audits, feed enrollment/positions/ACK and
unresolved recovery custody before migration. Assert behavior as well as bytes:
latest reads/writes, request replay, key lookup, history reconstruction and feed
continuation must agree with independently authored expectations. Old runtime
application operations must refuse after commit before any effect.

Every release classifies its installed inventory and retained meaning. A change
requiring migration ships its immutable edge and source-to-latest tests; an
unchanged tuple ships explicit no-change evidence. Test all admitted paths with
the latest migrator. Historical runtime wheels are fixture producers and refusal
controls only. A failed route blocks release; removing its source from the matrix
or extending old runtime support is not an acceptable workaround.

## Risks and recovery

| Risk | Mitigation and recovery |
| --- | --- |
| Source and target reuse release/layout labels | Compare complete hashes and native definitions; publish new immutable target artifacts |
| Previously accepted data violates new validation | Census and declare semantic conversion before apply; preserve evidence; refuse unexplained loss |
| Old runtime still writes through retained facades | Execute actual predecessor-wheel controls under the recipe's admission fence; do not publish mixed readiness |
| COMMIT response lost or process dies | Durable original attempt and read-only reconciliation; no replacement transaction on uncertainty |
| Migration fails after installation changes | Single initial transaction; confirm complete rollback. Post-commit failure stays committed with readiness closed; forward fix or verified backup restore |
| Protected registrations or old cache/query handles become stale | Explicit transition/recapture or pre-effect refusal; do not silently disable protection |
| Historical compatibility accumulates in hot runtime | Isolate conversion code and enforce import boundary; latest-only application execution |

## Execution contract and continuation evidence

Implementation is authorized by the owner's explicit 2026-10-21 request.
RM-S1–S6 are implemented; RM-S7's blocking gate is wired and locally exercised.
The candidate remains unpublished. The owner subsequently required full Linux
qualification, review, PR merge, release publication and public-asset verification.
PR #27 on `codex/runtime-migration-restoration` carries only this tranche. No
production database was changed. Hosted attempts and current status follow below.
Unrelated Hohfeld planning files already present in the checkout are outside this
change. No extra agents, tracker items or external services were created.

| Slice | Concrete result and evidence |
| --- | --- |
| RM-S1 | Real published v0.0.44/v0.0.46 wheel fixtures, exact source/target inventories/configuration/ACLs and explicit routine delta; shared v0.0.45/46 tuple is one native source |
| RM-S2 | Separate public tool/private loader/verifier/executor, existing privilege port and CONTRACT-007 installed-target custody; checker passes 1,693 imports and 20 positive/negative controls |
| RM-S3 | Packaged exact manifests, immutable forward recipes, read-only status/verify, unknown/drift refusal, current metadata-owner configuration pin and two narrowly qualified native deparse alternatives |
| RM-S4 | Single administrative transaction/exclusion; complete original table/sequence fingerprints; original documents/unknown content, keys, object/edge/history/import/feed/replay state preserved; latest read/write and actual old-wheel rejection |
| RM-S5 | Durable original intent before BEGIN, actual lost COMMIT reply/restart reconciliation, live-backend dispatch-gap and cleanup controls, immutable native receipt, no blind resubmission |
| RM-S6 | Separate-process prepare/apply/verify/reconcile/receipt CLI; latest fresh install has empty ledger; logical dump/new-identity restore plus explicit original ACL companion then latest migration |
| RM-S7 | Installed all-source gate in `.github/workflows/release.yml`, exact wheel checksums, skipped-case failure, immutable-history/removal negative controls and explicit unchanged-tuple case. Hosted Linux is pending; native two-edge proof is required when a real subsequent edge exists |

The native storage receipt adjunct is authored through
[UMF 0.10](../02-design/models/truss-runtime-migrations-0.1.umf.json) with
[owner correspondence](evidence/runtime-migrations-20261021/receipt-model.json).
Business layout `1.0` and genesis/replay identities remain unchanged; full native
release identity changes. The exact administrative binding, bounded resources,
receipt custody, admission fence and restore limitations are specified in
[TD-045](../02-design/technical-designs/TD-045-bootstrap-the-internal-layout-from-umf.md#selected-python-runtime-migration-profile).

Original evidence is under
[evidence/runtime-migrations-20261021](evidence/runtime-migrations-20261021/validation.json):
installed qualification, package payload/hashes, focused regressions, module
controls, owner model/deparse proof and source/test producer pins. The actual
populated fixture is synthetic non-PII: two keyed record types, two objects,
retained unknown/null content, one edge, committed update/history, one import,
replayable mutation and committed non-genesis feed acknowledgment. Complete native
row and sequence fingerprints cover every original Truss table, not just API
assertions. This is not an exhaustive populated corpus for every supported scalar,
container, ownership variant or optional profile, nor a scale qualification.

Reproduction (use the exact owned Python/PG/psycopg/V8 environment, install the
built wheel and pinned Weft first):

```sh
python -m build --outdir dist packages/python
python scripts/qualify-runtime-migrations.py --installed-package --download \
  --wheelhouse /tmp/truss-migration-wheels --output /tmp/migration-qualification.json
python scripts/check-module-boundaries.py
python scripts/check-module-boundaries-controls.py
```

The installed gate imports the installed wheel, never source fallback, and seeds
sources in subprocesses importing exact checksum-pinned original wheels. The
latest tool alone executes migration. The fixed recipe is explicit native DDL
from reviewed changed routine inventories, not runtime regex inference. Fresh
current and package-only unchanged-tuple cases cannot fabricate receipts.

No spending ceiling was supplied. Token/cost metering was unavailable; none is
inferred. Local evidence is macOS ARM64, CPython 3.11.17, PostgreSQL 18.6
(`pgserver-pg18==18.6.1`), psycopg 3.3.6, mini-racer 0.14.1, Weft 0.4.49 and
UMF 0.10. Hosted Linux x86_64 remains a release-time requirement. No protected,
pre-0.10, downgrade, physical restore/incarnation, managed-service or large-data
migration claim is made. The pure two-edge graph test establishes planning only;
first real subsequent native edge supplies skip-release execution proof.

## Hosted Linux continuation and review

The original local-only qualification remains archived unchanged. Hosted runs
[39690997485](https://github.com/DocumentDrivenDX/truss/actions/runs/39690997485)
and [39691446206](https://github.com/DocumentDrivenDX/truss/actions/runs/39691446206)
refused native bounds before migration. Original initializer date literals produce
distinct native instants under UTC and America/New_York. Fixed UTC inventory
observation plus independently reproduced exact initializer profiles preserve both;
a migration that substitutes the other qualified horizon must roll back. Source
wheel hashes, native target `7ac989…b963ea`, SQL and business layout remain unchanged.
The corrected recipe manifest is `5f6e099b8a315fdfabae99b41df86383cf78c9cf6a8afc8e1cd11d16ee7f3f80`.

[39692489622](https://github.com/DocumentDrivenDX/truss/actions/runs/39692489622)
passed the corrected native admission/preservation checks but its fault-only TCP
relay hit the ordinary operation deadline before COMMIT on Linux. TCP_NODELAY in
the test relay removes artificial frame delay; actual lost COMMIT evidence and
production deadlines stay unchanged. The installed migration gate then passed all
48 cases in [39692999225](https://github.com/DocumentDrivenDX/truss/actions/runs/39692999225).
That run subsequently found a raw-native ceiling fixture without the latest cohort
stamp. Ceiling and second-reader raw fixtures now adopt latest host transactions;
explicit unstamped refusal, authority separation and original no-effect checks stay.
A superseded run is canceled rather than presented as passing the full workflow.

[Review](evidence/runtime-migrations-20261021/review.json),
[local corrected qualification](evidence/runtime-migrations-20261021/initialization-fix/receipt.json),
[original failed attempts and Linux migration receipt](evidence/runtime-migrations-20261021/hosted-linux/39692999225/qualification.json)
and its package-correspondence record retain exact source/proof/artifact bindings.
Local corrected installed qualification passes 48 cases; 23 real atomic-capacity
checks and the isolated 1,000-type case pass. A broader parallel local sweep hit an
administrator shutdown and the stale second-reader fixture; it is retained as
incomplete, with no full-suite claim. These earlier results are superseded for
delivery by the final Linux workflow below; they remain original scoped evidence.
Native future multi-edge execution remains deferred until a real subsequent edge.

Final review adds exact table/index inheritance (including external parents) and
partition-key observation. The source wheels, native target and converter SQL
remain unchanged; independently recaptured pre-publication profiles produce
migration manifest `132526a7d5429a8cd40ccb7d6ebc16a2448ed0ea3b8bcd75aec89d65403a32d0`.
The native corruption control starts from an admitted source, adds an external
ancestor without changing any previously observed facts, then requires pre-effect
refusal. Review also moves confirmed rollback resource release after actual
connection close and replaces truncated preview-race observation with a test-only
marker on the real SQL statement. No production deadline or admission condition is
weakened. Final installed migration matrix now has 52 cases.

The complete [Linux release workflow 39699389717](https://github.com/DocumentDrivenDX/truss/actions/runs/39699389717)
passes at source `885faa77397cbaa997b8e189638d630173f8ba3c`, including the original
1,000-object/1,000-edge public workload under unchanged limits. The installed
migration matrix passes all 52 cases without skips on Linux x86_64 and local
macOS ARM64. [Hosted evidence](evidence/runtime-migrations-20261021/hosted-linux/39699389717/run.json),
[package correspondence](evidence/runtime-migrations-20261021/hosted-linux/39699389717/package-correspondence.json)
and [local installed evidence](evidence/runtime-migrations-20261021/final-installed-local/qualification.json)
bind the final artifacts. All 445 runtime payload files in both wheel and source
archive match source. Optional stress/large-capacity jobs and broad discovery
are outside this result. The released delivery below completes the remaining gates.

## Released delivery — 2026-10-22 UTC

[PR #27](https://github.com/DocumentDrivenDX/truss/pull/27) merged at
`6c9365c8be60b55602fe4e7bd4e45b4b5040ec74`. [v0.0.47](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.47)
was published after the complete [tag workflow](https://github.com/DocumentDrivenDX/truss/actions/runs/39702368076)
passed its package, Linux native and publication jobs. The tag repeats the 52-case
installed migration matrix without skips and the original public workload.

The [public verification](evidence/runtime-migrations-20261021/published-0.0.47/validation.json)
checks all 12 checksummed assets and byte equality with the tag's tested packages,
constraints and original native evidence. All 445 runtime payload files in wheel
and source archive match the released source. A fresh Python 3.11.17 environment
installed the public wheel and passed all 52 migration cases without skips on
macOS ARM64. The published `uvx` command also passed outside the checkout with two
independent local instances retaining their data and installation identities
across restart. Original receipts, logs, pins, checksum list and native archive
remain alongside that record. No production database was used.

Only the latest application runtime is supported. Every admitted database source
retains a migration path to latest without age-based expiry. The release does not
maintain old application runtimes or extend the tested subset/platform claims.

## Exit criteria

- [x] First populated v0.0.44 → frozen v0.0.47 route and v0.0.45/46 exact tuple pass local installed qualification.
- [x] Latest-only admission, preservation, rollback, actual lost-ack recovery and public packaged tooling pass locally.
- [x] Future-release lineage/removal/immutability gate is blocking; latest tooling retains every admitted source path.
- [x] Package guidance, public binding and current HELIX specifications capture latest-only runtime support and forward database migration.
- [x] Local boundaries, package payload and focused regression checks pass for the recorded exact artifacts.
- [x] Complete hosted Linux release/public-workload workflow passes for the final migration candidate.
- [x] Reviewed PR is merged, v0.0.47 is published and its public checksums/assets/clean installed migration gates are verified.

## Next release gate

The first real subsequent native edge must supply native skip-release-chain
execution proof. This remains blocking when that edge exists; the first release
does not fabricate a future native edge or claim that proof has already passed.
