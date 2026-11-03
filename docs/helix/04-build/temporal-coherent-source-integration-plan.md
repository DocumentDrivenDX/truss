---
ddx:
  id: truss.temporal-coherent-source-integration-plan
  type: implementation-plan
  activity: build
  authoring:
    home: repo
  links:
    - id: truss.temporal-dependency-cohort-plan
      kind: informed_by
    - id: truss.temporal-interface-freeze
      kind: informed_by
    - id: truss.temporal-native-qualification-plan
      kind: informed_by
---

# Coherent temporal source integration

## Scope and decision

**Decision `truss.temporal-coherent-source/1`: isolated SOURCE preparation is
authorized; final main merge, qualification and publication follow the promotion
decision below.** The existing Root42/Access89 parent retains ownership of the
combined integration/qualification queue. Use that parent's single integration
lane; do not start a competing owner, release branch or qualification campaign.
No code/build/test/worktree/branch/PR creation is performed by this planning task.

Decision `truss.temporal-coherent-source/1-promotion` (2026-11-03) applies the
human-authorized [cohort promotion decision](temporal-dependency-cohort-plan.md#ordering-and-gates).
It supersedes this plan's earlier owner-completion/publication ordering hold:
Core0.10.7 PUBLICATION is not a contractual prerequisite for the qualified
successor. Frozen owner `722b1e5484ca5e1558bb364ebdac22c995e140f9` source
reconciliation is MET in reviewed assembly `576adc8ee5be92fc560fa4ae72b3ab09dd2b03cf`
and canonical coherent source `e3f38ef6f05ae636d2837f9d69f8d6805222664b`.
Use the existing Root42/Access89 parent lane: qualified Core0.10.8 coupled release
and public-byte/fresh-consumer proof, then Access0.1.0.dev10/umf-weft0.4.57, then
umf-truss0.0.56. Each successor retains its actual source/artifact, installed,
native/browser and public delivery gates under shared admission. Preserve the
0.10.7 reservation, owner chat/worktree and immutable assets; do not publish
0.10.7 on its owner's behalf or create a competing integration stream.

Read-only canonical inventory found no already-materialized combined temporal
branch/PR. The parent is staged at Root42 and Access89, not yet combined with
inspection95 and Access97 or the complete frozen Core source. The necessary
handoff is an exact SOURCE-ONLY assembly request to that parent, using the pins
and sequence below. Prepare a NEW isolated worktree, not its active db96 tree.
Creating a local private integration branch is allowed now; draft-PR creation
must not auto-launch an unadmitted campaign. PR97 previously auto-started Saga
qualification despite being draft, and it was cancelled under the resource hold.
Keep preparation local until PR-event resource behavior is admitted/controlled.
This is scheduling/CI containment, not missing human implementation authority.

Governing inputs: [dependency cohort2](temporal-dependency-cohort-plan.md),
[interface freeze1](temporal-interface-freeze.md), owner/staging PR bodies,
retained source-review/failure packets and the shared resource ledger. New source
integration is not a substitution for settled Core0.10.7 owner source, package,
publication or final installed/native qualification. Arras repair is independent.

## Current exact inputs and ownership

Fresh canonical remote main was `381ac3c9788f704201df0b9e16193e85802ef34e`
(PR98 site evidence merge). All five PRs below were OPEN/unmerged. This is an
observation, not permission to follow their branches after the recorded heads.

| Input | Canonical ref / exact SHA | Scope and review boundary |
| --- | --- | --- |
| Root42 parent | PR42, feat/dashboard-profile; `9cac8566c080f45eb8e13a7978a74315fea0f25c` | Parent writer uses protected `/Users/erik/.codex/worktrees/db96/umf`, local branch codex/lakeview-family-integration-20261102. Contains shared publication fix and authoritative Saga Registry corrections. Latest staging/evidence head, not final artifact acceptance. |
| Root42 Saga Registry API | `e798259a17fd98f8ea7d4f6a76140f2e7c650a24`, then `2c35caead9f131bc0610afa48ee87673d3aac93f` | Explicit Registry facade correction plus typed fixtures. Preserve both, full consumers and CONTRACT-908 semantics. Both ancestors of Root42 and89. |
| Root42 completed-resource publication | `d59b59f6ad9c004d4267010958eb661564a33a3f`, inherited by Root42/89 | Shared resource_cache::publish_completed and all31 adopted sites; retain immutable sharing AND per-context resource/control admission. Do not graft only three failing-test sites. |
| Access89 parent staging | PR89, codex/access-runtime-identity-integration-20261102; `3dd73680e93cac18d867c708ca970d7995eaef43` | Inherits Root42 Registry fixes and runtime identity mechanism. Access package source unchanged relative to passing `0b9523e726d410842415665c56dd542886f71bb4`; git diff under python/umf_access is empty. Old dev9/Core0.10.4/Weft0.4.56 package receipt does not qualify temporal composition. |
| Frozen Core owner | PR88, codex/umf-0107-release; `9d92e38c39c35c598faeea8abbd2262760c8cb34` | Protected `/Users/erik/.codex/worktrees/rust-binding-spike/umf`. Full frozen Core/codegen/pack-tools/resource/source-custody closure; owner completion/publication/approval pending. Do not modify its source, manifests, tests, resource pins or release inputs. |
| Core resource repair | ancestor `bbe15fd4b1055db78adb5a4ac1b3a0c71db7398f` within9d92 | Includes action-runtime manifest/canonical resource and companion closure plus related package/build changes. Consume through whole owner head, not a detached ten-line hash transplant. |
| Core private Action/Saga repair | authoritative original `8d377a471e91e4a85aa2c395037115be8bdf1df8`; frozen-owner equivalent `4f21dfe17b65abf7cc2c645278c5e2d50b8908fe` | Important ancestry distinction below. Preserve dedicated Saga/full-schema validation and private diagnostic isolation. |
| Inspection95 | PR95, codex/umf-temporal-inspection; `f629cda829223fb889d1faf25a2543e40689146d` | Conditional source PASS; three approved ordered commits below. Standalone graph resolves, but whole-core3 cache tests and Python1 version test failed on stale base. Feature-union/final packaging remain open. |
| Access97 | PR97, codex/umf-access-temporal; `8c4d97e2fb74a7ec4f3bb151f349aea911eb0f50` | Approved `c65342b5bcf507b8f592a3472c25dd450dcfd396` then8c4d97e availability/presence correction. Six-file frozen handoff; its base still has dev8 metadata/dev0 runtime mismatch, fixed by inheriting89. |

All source refs belong to `https://github.com/DocumentDrivenDX/umf.git`.
No worktree writes to rust-binding-spike, eb69, db96, primary, inspection95 or
Access97 are authorized to the integration worker by this plan. Read frozen
objects/handoffs; work only in the parent's new isolated integration worktree.
Do not copy an active owner's dirty filesystem or temporary engine installation.

### Core Saga equivalence is not ancestry

Read-only ancestry shows8d377 IS in Root42/89 but is NOT an ancestor of frozen
9d92. The latter contains4f21dfe instead. Exact git comparisons found NO changes
between8d377,4f21dfe and9d92 for these repair-bearing files:
`crates/umf-codegen/src/resources.rs` and `tests/saga/portable-oracle.test.ts`.
Thus the semantic repair is already in the owner source under a different commit;
do NOT cherry-pick8d377 a second time over9d92 or claim false ancestry. Retain the
full frozen owner's source-custody/metamodel/plan-identity follow-ups as well.
Equivalence of these two files does not equate entire commits, resources or
qualification receipts. Final integration proves the preserved private repair
and public guards together with Root42's distinct public Registry facade fix.

## Integration sequence — parent Luna, source only

First refresh remote heads and compare to this inventory. If any reviewed head
changed, obtain the exact new changed-file/review handoff; do not silently follow
it. Recheck for a combined branch/PR owned by the parent; if now present, use that
lane and this plan as a gap map, not a reason to duplicate its worktree or PR.

Use the host's managed worktree facility to create a new isolated worktree from
Access89 staging3dd73680, branch `codex/temporal-coherent-source` (or an existing
parent-selected equivalent). Canonical repository, no fork/vendor engine. The
following are ordered operations, not commands executed by Sol:

```text
BASE exact3dd73680e93cac18d867c708ca970d7995eaef43 (Access89 plus inherited Root42)
MERGE --no-ff --no-commit exact9cac8566c080f45eb8e13a7978a74315fea0f25c (latest Root42)
  inspect merge; commit reviewed source-only merge
MERGE --no-ff --no-commit exact381ac3c9788f704201df0b9e16193e85802ef34e (observed canonical main)
  inspect merge; preserve incoming current main and staged identity/source work
MERGE --no-ff --no-commit exact9d92e38c39c35c598faeea8abbd2262760c8cb34 (full frozen Core owner)
  inspect all conflicts and incoming resource/build/source-custody closure
CHERRY-PICK -x ba702cc948f17eb4539f7e06e9fd9b02ba2a4b3d
CHERRY-PICK -x 01151c1915392a7d1e85e78c500b95e326c5265a
CHERRY-PICK -x f629cda829223fb889d1faf25a2543e40689146d
CHERRY-PICK -x c65342b5bcf507b8f592a3472c25dd450dcfd396
CHERRY-PICK -x 8c4d97e2fb74a7ec4f3bb151f349aea911eb0f50
```

Verify the five cherry-pick source commits are not already present/equivalent
before applying. Preserve source-history provenance with original SHAs; do not
copy files out of an old installed wheel. Source-only commits must not trigger
unadmitted automatic native/browser/Saga/artifact jobs. Use existing repository
CI-skip discipline only to enforce the admitted source-only stage, not to waive
final qualification. Do not create/push a draft PR that starts a second campaign.

Ordering rationale:89 supplies the single Access runtime identity and inherits
the Root42 cache/Registry repairs; current Root42/main are retained; full Core
owner supplies canonical resources/pack-tools/private Saga closure;95 adds public
inspection and manifest compatibility over that coherent base;97 adds the inert
selected temporal catalog after the runtime identity mechanism is present.
No intermediate full build or expensive failed-base retry is required to prepare
that source. The original heads and receipts remain unchanged.

## Conflict policy and required source admissions

Mechanical non-overlapping merges are allowed. NEVER use wholesale ours/theirs,
re-sign a manifest to fit current bytes, drop an owner test, delete a newer main
change or infer semantic precedence from commit date. Conflicts in resources,
registry/validation, cache publication, source custody, profiles, package identity,
Cargo features/lock or generated artifacts require an explicit reviewed resolution
patch. Parent Luna prepares the exact conflict diff and source references; Sol
reviews before it is accepted as the coherent handoff. This is code review, not
a fresh request for human authorization.

| Gate | Source-readiness admission criterion | Later executed evidence, NOT run here |
| --- | --- | --- |
| CS-1 source/owner closure | Exact source map and resolved merge diff retain Root42,89,95,97 and whole9d92 closure; no active-owner dirty files. Inspector semantic kernel remains the reviewed implementation; original refs/unknown content retained. | Final source/build correspondence and official owner release receipts. |
| CS-2 three cache failures | All31 Root42 publication sites and shared primitive retained, including avro_cardinality, avro_document and avro_field_classifier; do not bypass Arc identity assertions or control/budget checks. | Three exact failed tests listed below, plus independent old-publication countercontrol, then full admitted coherent workspace. |
| CS-3 public/private Saga | e798+2c35 Registry mechanism and frozen-owner4f21/8d equivalent private isolation both retained; public/full-schema Saga validation and source-custody constructor expectations intact. | Unchanged public TS consumer, Registry/diagnostic/source-custody controls and all19 portable vectors on actual coherent source. |
| CS-4 runtime identity | Access89 `_version.py` is one inert version source; Hatch dynamic metadata and types.RUNTIME_IDENTITY import it.97 temporal routes inherit this, never restore dev0/dev8 constants. | Existing wheel identity controls on final selected version; old0b9523 receipt supports mechanism only. |
| CS-5 dependency/feature graph |95's eight Cargo manifests and genuine lock carry serde_json1.0.145, sha2.10.9, serde/derive/core1.0.228; UMF jsonschema0.29.1 and Weft0.56.0 remain distinct. Preserve deterministic patches/default feature closure. Resolve package-version edits against Core's actual manifests, not an old lockfile replacement. | Actual locked standalone and Weft feature-union/native/WASM proof; no local paths/engine copies. |
| CS-6 distribution-version failure | Repair stale hardcoded test expectation as described below in the isolated integration source; semantic core remains exactly0.10.0. No invented final distribution version. | Pure selected-version mismatch negatives, then actual installed metadata/runtime/companion agreement after final version selection. |
| CS-7 canonical resources | Whole owner canonical resource/action-manifest/companion/source-custody inputs retained; inspect any Root42/main conflicts. No naked hash regeneration to turn failed stale inventory into success. | Authentic generated-resource freshness, WASM source inventory, official wheel/sdist and SDK/source archive checks under owner-reviewed final closure. |
| CS-8 temporal subset | Engine read/page0.4, binding-temporal0.2, decoder truss-temporal0.2, strict075, explicit native ABI1.3 and ordinary ABI1.2 defaults/refusals unchanged. | Compiled Weft, real installed Access/Truss native/browser qualification; source tests alone do not enroll support. |

### Exact known failure closure

Retain PR95's original failed packets at
`/private/tmp/umf-temporal-inspection-evidence/dependency-cohort-v2/`:
`standalone-failure-review.json`, `python-component-failure-review.json` and
`review-packet.json`. Source inclusion is not a claim these failures now pass.
The targeted future checks are:

```text
avro_cardinality::tests::ordinary_resources_reuse_preserves_controls_and_custom_limits
avro_document::resource_tests::ordinary_resource_reuse_still_admits_each_document_and_host_control
avro_field_classifier::tests::immutable_resources_are_shared_between_ordinary_contexts
python/tests/test_core.py::test_distribution_version_is_distinct_from_semantic_core_version
```

For the fourth case, source95 hardcodes0.11.0 while its installation is0.10.6;
frozen9d92 still has the same test but runtime0.10.7. Therefore merely merging
Core0.10.7 does NOT close that failure. Do NOT pick0.10.8 or0.11.0 to satisfy a
test literal. In the isolated integration candidate, make this test enforce
runtime distribution version equals the authoritative selected Python project
metadata, and independently semantic current_core_version()==0.10.0. For source
mode read the exact current python/pyproject.toml; for installed mode compare
actual distribution metadata and the exact admitted artifact expectation. Add
wrong-distribution and wrong-semantic-version negative controls so it cannot
pass merely because two stale labels happen to agree. Do not weaken to nonempty
version or inequality-only. Review this small new test correction explicitly;
it was not part of the already-approved95 patch. Frozen owner files stay intact.

Final Core/codegen/SDK/Access versions are selected afresh after the0.10.7 owner
settles, with public tag/registry collisions rechecked. Access89's dev9/Core0.10.4
pins and Core9d92's reserved0.10.7 metadata are staging inputs, not the final
cohort declaration. Preserve `_version.py` mechanism while setting its eventual
value through the release owner. Stage source can retain provisional inherited
versions with an UNRELEASED/SOURCE-ONLY record; no build/publication under a
colliding released/reserved version. Update all actual version/dependency/SDK/
companion/Cargo metadata together before final artifact admission. No semantic
core version bump follows from any distribution-version choice.

## Feature-union and global admission limits

No new full artifact campaign is authorized. The parent owns the globally
admitted SINGLE native/browser worker slot and its existing campaign budget.
The relayed10038s/461-of500 snapshot is stale: read-only state inspection observed
allowance79506s, spent70401.80357488157s, attempts475/500, active=null. These are
ledger observations, not transferable/available authorization; scope reservations
and current owner admission still govern. Do not change caps, attempts, active
state, ledger, held coordinators, foreign allocations or infer an idle slot grants
permission. This planning task did not reserve or launch anything.

The next owner first reconciles that ledger via its existing runner/control
workflow. Source merges, diffs, inventories and review can proceed without a new
build. Any focused test, Cargo resolution that executes build tooling, native/
WASM build or artifact work waits for its existing admitted operation; no parallel
subcampaign, CI dispatch, stale-base rerun or two-platform matrix. When admitted,
run source-targeted failed cases once, then the ONE coherent final campaign,
repeating only failures/affected closure.

Record actual Weft Cargo root patches and source IDs, not just version strings.
Weft serde_json arbitrary_precision/raw_value plus transitive features can differ
from standalone UMF; umf-codegen may enable embedded-adapters through additive
default features. Reconcile actual locked feature graphs in both modes without
turning off source/domain/clock/entropy controls. Preserve canonical publicly
fetchable Git revision dependencies and upstream deterministic patch closure;
no Weft-vendored UMF engine, temporary sibling/file:// dependency or generated
resource rehash as a dependency fix. Existing component/partial-remainder logs
remain partial; they cannot close these feature-union or artifact gates.

## Required handoff to Noether and final hold

Parent returns ONE source integration handoff: isolated path/branch and exact
commit/tree SHA, original input ancestry/patch-equivalence map, reviewed conflict
resolution diff, Access runtime identity mechanism, manifest/lock and resource
inventory deltas, CS-1–8 readiness disposition and known unexecuted checks. If a
parent combined lane appears during preparation, return its actual path/SHA and
remaining gaps instead of building another lane.

Noether can use that exact reviewed coherent source for preparation/inspection
integration work, labeled SOURCE-ONLY. It is not an actual installed/enrolled
owner capability receipt, final public pin or native acceptance proof. Successor
source reconciliation, qualification and exact public artifact
verification remain mandatory before claiming completed successor delivery;
Core0.10.7 publication does not gate its main merge or release.
If owner source changes, compare it explicitly, integrate reviewed deltas in this
same isolated lane and re-admit affected proof; never alter frozen9d92 receipts.

Keep source readiness, completed focused results, full feature-union/workspace
qualification, official artifact/source equality, installed/native/browser and
public delivery as separate claims. No new API/semantic profile is introduced.
Arras immutable0.7.1 failure and E's0.7.2 repair remain outside this plan.

## Exit criteria

Planning closes with exact inputs/sequence and single-parent ownership identified.
Source readiness requires the reviewed coherent tree and explicit CS dispositions,
including the cache mechanism and distribution-test correction; executed pass
claims require actual admitted receipts. Final merge/release require frozen Core
source reconciliation and the admitted qualification gates at their respective
stages; completed delivery requires public-byte and fresh-consumer proof.
No code/build/test/branch/PR/owner-state change was made
by this plan author.
