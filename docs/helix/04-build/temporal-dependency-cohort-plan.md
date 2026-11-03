---
ddx:
  id: truss.temporal-dependency-cohort-plan
  type: implementation-plan
  activity: build
  authoring:
    home: repo
  links:
    - id: truss.temporal-interface-freeze
      kind: informed_by
    - id: truss.temporal-current-baseline-plan
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
---

# Temporal dependency cohort plan

## Scope

**Decision: `truss.temporal-dependency-cohort/2`.** Select an additive, reviewed
UPSTREAM UMF Cargo compatibility change. Preserve Weft's original dependency
versions; align UMF's exact serde_json/sha2 requirements upward once, in a separate
isolated integration candidate. Qualify that candidate, then merge and publish
the selected successor under the promotion decision below. Weft consumes the exact reviewed publicly fetchable
canonical UMF revision. Do not create a Weft-owned UMF engine source bundle.

This revision supersedes the initial source-bundle selection in this file. The
existing temporal-interface-freeze/1 API, semantic profiles, grammar, ABI and
native identity remain unchanged. No worker Cargo/source, inspection worktree,
active Rust owner, G11 checkout, resource manifest or delivery plan is edited by
this planning task. Luna implements and tests; Sol plans/reviews. Inspector review
and official resource packaging repair stay with their existing owners.

## Shared Constraints

### D1 — decision comparison and authority

| Strategy | Correctness / qualification cost | Maintenance | Decision |
| --- | --- | --- | --- |
| Upstream UMF compatibility patch | Explicit new dependency/feature cohort; full UMF workspace plus embedded Weft/native/WASM parity required. Inspection already needs renewed qualification, but that does not waive these additional checks. | One canonical source, lockfile and dependency update; consumers pin reviewed immutable upstream bytes. | SELECTED. |
| Weft-vendored UMF engine plus manifest overlay | Could be correct only with complete canonical provenance, unchanged source/resource bytes, source/patch closure and equal native/WASM qualification. No automatic qualification saving; creates a second adapted engine build. | Reimport, overlay, resource drift, security-update and sync obligations fall on Weft in addition to upstream maintenance. | REJECTED for this cut: no necessary upstream obstacle established. |
| Downward alignment or source-splitting tricks | Observed downgrade breaks jsonschema; attempted root Git patches still resolver-fail. Separate source identities would need additional manifests, feature/type boundaries and equivalent validation. | Additional divergence without a demonstrated benefit. | REJECTED. |

UMF's exact Cargo pins are declared build requirements, not definitions of
CONTRACT-075 grammar, inspector shape or metamodel meaning. They cannot be
silently overridden or called unchanged. A deliberate reviewed manifest/lockfile
update is authorized; no new human approval is missing. The existing owner freeze
constrains WHERE/WHEN integration occurs, not whether compatibility may be fixed.
Keep the0.10.7 source/resources/release intact. Develop on a new isolated candidate
and serialize merge after that owner finishes; never edit the active owner under
its feet or reissue changed0.10.7 bytes.

### D2 — exact dependency selection

| Package | Canonical source | Selected exact version / original registry checksum |
| --- | --- | --- |
| serde_json | crates.io | `=1.0.145`; `402a6f66d8c709116cf22f558eab210f5a50187f702eb4d7e5ef38d9a7f1c79c` |
| sha2 | crates.io | `=0.10.9`; `a7507d819769d01a365ab707794a4084392c824f54a7a6a7862f8c3d0892b283` |
| Weft jsonschema | crates.io | `=0.56.0`; `b6a806f80c1f5560431009ce5ec29b59d38f950e0cd7db5f1b8925e6d8104e21` |
| Weft serde | crates.io | Existing `=1.0.228`, derive retained |
| Weft sqlparser | crates.io | Existing `=0.63.0`, std/visitor retained |
| Toolchain | Existing Rust toolchain | `1.90.0`, native/WASM target and release settings retained |

Preserve Weft serde_json arbitrary_precision/raw_value and jsonschema macros/
arbitrary-precision features. Record actual transitive float_roundtrip and full
feature union. Keep UMF's other declared versions, including its own separate
jsonschema0.29.1 dev dependency; do not downgrade Weft's validator to match it.
Retain deterministic vendor patches, WASM entropy refusal and native loadability
settings. No unrelated update-to-latest lockfile sweep.

The additive UMF patch updates EVERY exact serde_json1.0.140 and sha2.10.8 pin in
the selected UMF workspace to the versions above, then produces its genuine new
lockfile. At inspected ba702cc the affected manifests are:

```text
crates/umf-core/Cargo.toml           serde_json, sha2
crates/umf-codegen/Cargo.toml        sha2
crates/umf-core-wire/Cargo.toml      serde_json, sha2
crates/umf-tagged-wire/Cargo.toml    serde_json
crates/umf-graphql/Cargo.toml        serde_json
crates/umf-cli/Cargo.toml            serde_json (including dev), sha2
crates/umf-metamodel/Cargo.toml      sha2
crates/umf-metamodel-cli/Cargo.toml  sha2
```

Reconcile that exact list against the post0.10.7 integration base. Updating only
umf-core/codegen while leaving conflicting workspace pins is not a complete
upstream patch. Preserve semantic .rs implementations, resources, public APIs and
refusal meaning. Record the reviewed manifest/lockfile delta and any additional
actual compatibility failure; a dependency patch is not permission to alter
semantics, drop tests or regenerate failed resource hashes.

### D3 — canonical source and consuming graph

Upstream inspection candidate:
`https://github.com/DocumentDrivenDX/umf.git`,
`ba702cc948f17eb4539f7e06e9fd9b02ba2a4b3d`, based on
`a5e24d17017a3de0ee701837d9c99c3dad27d0a5`. It remains unreviewed here. The other
Sol lead reviews the inspector operation; this dependency decision does not
supply that approval. The compatibility candidate must contain the accepted
inspection delta and the explicit dependency patch, integrated against the
settled owner source without regressing newer work.

The release-consumed UMF SHA is the future reviewed canonical integration commit,
not ba702cc with an invisible overlay. No future SHA is invented here. Weft's two
Rust dependencies must use the SAME canonical Git URL and exact full rev:

```toml
umf-core = { git = "https://github.com/DocumentDrivenDX/umf.git", rev = "<reviewed integration SHA>", default-features = false, features = ["full-core"] }
umf-codegen = { git = "https://github.com/DocumentDrivenDX/umf.git", rev = "<same reviewed integration SHA>" }
```

The placeholders describe mandatory implementation outputs, not usable release
pins. Record the publicly fetched commit, reviewed source/lockfile hashes and
actual compiled payload identity before declaring a cohort. A reviewed public
integration commit can support compiler qualification before the UMF package
upload, but cannot establish official installed UMF/Access/Truss delivery.
No local Git URL, external sibling path, floating main/tag or unpublished local
crate may remain in canonical Weft manifests, source archives or release builds.

Cargo does not apply a dependency workspace's root patches to the consumer.
Therefore Weft MUST explicitly retain UMF's deterministic transitive patch
closure at its consuming root, pinned to the SAME canonical UMF revision:

```text
hashbrown-012: package hashbrown =0.12.3
hashbrown-013: package hashbrown =0.13.2
json-ld-core =0.21.4
json-ld-syntax =0.21.4
json-syntax =0.12.5
xsd-types =0.9.6
```

Use root patch entries selecting those exact packages from the canonical UMF Git
repository/rev, with version constraints; retain Weft's existing vendor/ahash
entry. These upstream-maintained third-party packages are not UMF engine copies.
UMF's direct saphyr-parser/oxttl/oxrdf path dependencies must resolve inside the
same fetched upstream repository. Verify the actual locked package/source IDs
and complete path closure; do not assume patches survive by name. An actual Cargo
package-discovery conflict requires a concrete follow-up decision, not an
unreviewed local-path/vendor engine workaround.

Features are additive. umf-codegen's default umf-core dependency may enable
embedded-adapters despite default-features=false on Weft's direct edge. Record
that union, including shared serde_json features; qualify both UMF standalone
and Weft-integrated configurations. Do not disable features, deterministic hash
patches, clock/entropy refusals or resource controls just to obtain a WASM pass.

Cargo references: [dependency resolution](https://doc.rust-lang.org/cargo/reference/resolver.html),
[patch behavior](https://doc.rust-lang.org/cargo/reference/overriding-dependencies.html),
[dependency locations/revisions](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html).
These support the strategy, not a claim that this candidate has built.

### D4 — evidence, failed routes and provisional local fixture

Read-only failure records:
`/private/tmp/weft-temporal-dependency.log`,
`/private/tmp/weft-temporal-downgrade-failure.log`,
`/private/tmp/weft-temporal-green.log`, and the worker receipt.

Original Weft exact1.0.145/0.10.9 and UMF exact1.0.140/0.10.8 fail same-source
Cargo resolution. Renaming dependencies or resolver2 does not solve incompatible
exact constraints. Downgrade log lines491–505 reports E0277: jsonschema0.56.0's
canonical/json.rs derives Default over CompactFormatter, which1.0.140 lacks;
1.0.145 contains the Default implementation. This is a real compile failure,
not a native temporal refusal that can be waived.

The attempted root patches point to serde-rs/json
762783414e6c4f8d670c9d87eb04913efb80d3be (manifest1.0.140) and RustCrypto/hashes
28a7b0da94a581e71e85d264836e1c3f8343338e (sha2 manifest0.10.8). The recorded
attempt still resolver-fails. Do not freeze these as a successful separated graph.

At inspection, Weft restored its original modern pins and uses
`/private/tmp/weft-umf-semantic-fixture` with three manifest edits aligning UMF
upward. This is a local proof-of-concept of the version direction, NOT exact
unchanged UMF manifests, independent dependency graphs or a release candidate.
Luna may continue bounded compiler development there, keeping explicit provenance
and temporary status. Do not commit the engine copy into canonical Weft or
publish artifacts from it as the final cohort. Replace the fixture dependency
with the reviewed upstream rev and rerun qualification; fixture receipts cannot
be promoted to the integrated release by changing labels/hashes.

### D5 — independent resource packaging blockers remain

Read packets:
`/private/tmp/umf-temporal-inspection-evidence/verification.json`,
`packaging-review.json`, `wasm-source-review.json`.
They record public-operation SOURCE qualification, reviewer pending, no published
inspector and no qualified official wheel. The unchanged semantic inspector hash
is `2f5066a771f4fe9a9e1aabc0eeec17dbb2f69ff72693c6a591b1d4d1efa4b5bc`.

The existing official action-runtime manifest has five resource mismatches:
constraints, coreSchema, domainPolicy, packageSchema and referenceSchema. WASM
shared-source inventory disagrees for native-family.js although listed source
copies match. Public main observed4e747cefafe6d90da91e2b48f8983be724a3c791 does
not establish a fix; owner0.10.7 is still an unpublished build. Preserve frozen
resources, original manifests and failures. This plan authorizes no hash
regeneration, resource replacement or declaration that mismatched inputs pass.

Full-core compatibility qualification is required in addition to inspector tests;
its receipt cannot repair or bypass the packaging block. The existing owner must
resolve packaging under its own scope. Preserve exact current compiler resource
copies/provenance meanwhile; any resource change on the eventual integration
base requires an explicit reviewed delta and renewed qualification, never an
assumption of byte equality. Source compiler work can proceed; official installed
UMF/Access/Truss delivery remains held until its real packaging gates pass.

## Implementation Slices

| Slice / owner | Scope and prerequisite | Required outcome |
| --- | --- | --- |
| DC-1 / Luna integration, coordinator | New isolated UMF compatibility candidate; no active owner/inspection/G11 edits | Reviewable workspace manifest/lockfile alignment to D2 plus accepted inspector delta. Record source/resource equality and feature graph. Development need not wait for owner release completion. |
| DC-2 / same Luna, Sol review | Candidate full workspace and Weft integration fixture | Full UMF standalone/native/WASM tests, inspection/refusal parity and Weft feature-union proof; packaging blocks remain separate. No weaker validators. |
| DC-3 / owner/integrator | AFTER settled0.10.7 owner completion, inspector approval and compatibility qualification | Reconcile with final canonical base, rerun affected/full gates, reviewed merge and immutable publicly fetchable integration SHA. Select next UMF release through owner. |
| DC-4 / existing Weft Luna | Replace temporary fixture with exact canonical Git dependency/patch closure | Clean reproducible source archive/native/WASM builds; ordinary ABI1.2/HF62 and frozen temporal gates on final inputs. No fixture evidence relabeling. |
| DC-5 / release integrator | All exact source/official package gates | Public artifact/hash/install consumers and native/security/snapshot/replay proof for the actual final tuple. |

## Execution Contract

This is planning only; no implementation, builds or tests by Sol. The existing
Luna writer applies the plan; no new agents, app/ancestor tools or thread messages.
The other Sol lead owns inspector/Arras review; Noether continues T4A correction/CI
and later native work. This plan does not divert their work or alter their files.
No further human permission is required to prepare the isolated upstream patch.

Truss application versions are DEFERRED: preserve Ashlar's installation-only
Truss0.0.55 candidate/source; never reserve55 for temporal. Recheck available
versions at release freeze. Native0.76 and semantic profile identities remain
independent. No aggregate token budget or reliable meter was supplied.

## Validation Plan

1. Record all UMF manifest/lock changes, exact registry checksums, full Cargo
   metadata/features/patches and toolchain. Qualify the whole affected UMF
   workspace, not only core/codegen or inspector export tests. Preserve diagnostic,
   cancellation, duplicate/nonfinite, exact-number, raw JSON/Unicode, canonical
   formatting/digest and source-resource behavior under the new versions.
2. Run standalone UMF and actual Weft feature-union configurations, Rust native,
   Python and real Chromium WASM. Verify integrated inspector/token results and
   ordered diagnostics against independent existing corpora. No engine copy,
   JavaScript sidecar, reduced resource controls or silently disabled adapters.
3. From a fresh public canonical checkout/source archive and empty Cargo home,
   fetch exact reviewed UMF source, resolve locked graph including all patches,
   and build with no sibling source directories or hidden environment overrides.
   Verify actual installed wheel/WASM/source payload correspondence and official
   UMF packaging gates separately. Preserve failed attempts and cleanup evidence.
4. Qualify authentic ordinary ABI1.2 capture/compile/check/execute/decode, all
   unchanged HF62 assertions, affected native/security regressions and the frozen
   temporal engine0.4/profile0.2 native0.76 transport/source-guard/custody,
   security/snapshot/replay/browser/public54 refusal gates. Prior or fixture cohort
   passes do not transfer to changed final inputs.
5. Complete reviewed merge, exact immutable source/tag/artifacts, official
   publication and independently fetched fresh public consumers. Local macOS,
   hosted Linux and managed claims stay scoped to their actual receipts.

## Risks and Rollbacks

| Risk | Required response |
| --- | --- |
| Compatibility patch overruns owner freeze | Separate candidate; serialize merge after0.10.7; preserve frozen source/resources. |
| Shared JSON features alter semantics | Full standalone and embedded feature-union parity; no assumption that a version bump is harmless. |
| Upstream root patches disappear in Weft | Explicit canonical pinned consuming-root patch closure plus locked metadata/build proof. |
| Local fixture becomes a permanent engine fork | No canonical Weft engine bundle; replace with reviewed upstream SHA and requalify. |
| Successful compile masks packaging failures | Separate full-core, inspector, official-resource, native and public artifact gates. |

If additional compatibility failures arise, record their exact source/diagnostic
and bounded proposed change for review. Do not fall back to downgrade, engine
vendoring, source-identity tricks, weakened refusal or unavailable temporal APIs.
Keep the new capability unqualified while preserving old supported behavior.

## Continuation Evidence

Read-only inspection confirmed a real resolver failure, the concrete
CompactFormatter compile error, original pins restored and a temporary upward-
aligned fixture. The last inspected green log showed ongoing compilation; the
worker receipt still marked native temporal, ABI1.2, HF62, Sol review and release
false. No new pass is claimed by this plan. Inspector approval, exact future
canonical compatibility SHA, owner release selection and behavioral/package
receipts remain implementation outputs, not missing policy decisions.

## Exit Criteria

Planning closes with upstream alignment selected and vendoring rejected.
Dependency implementation closes after canonical reviewed/public exact source,
complete compatible feature/patch graph and full standalone/embedded native/WASM
qualification pass. Full temporal release still requires official resource/
package repair, ordinary ABI1.2/HF62, all frozen native/security/snapshot/replay
and independent public-consumer gates. No Truss package version is allocated.

## Resolver and release identity addendum

Decision `truss.temporal-dependency-cohort/2-resolver`: retain the v2 upstream
strategy and existing parent integration lane. Select exact distribution
identities only after frozen owner reconciliation and live tag, release,
registry and reservation checks. Use C for the coherent UMF successor, A for
Access, W for Weft and T for Truss below; these symbols are planning outputs,
not usable versions or pins. The earlier expected0.10.8 is not an allocation.

### Identity and normal resolver choice

- Core owner's reserved0.10.7 stays its own release. The combined temporal
  successor receives a distinct available C selected under UMF's coupled
  artifact release contract. Core model semantics remain0.10.0. Access has its
  own A; Weft its own W. T must be available and must exclude the separately
  reserved0.0.55. Do not assign any of these from cached public-version facts.
- Access `python/umf_access/pyproject.toml` changes its inherited
  `umf-core==0.10.4` to exactly C. Preserve its authoritative
  `src/umf_access/_version.py` mechanism and runtime identity import. Set A
  through that source, with matching built metadata, rather than adding a
  second version constant. Retain unrelated declared constraints.
- Truss `packages/python/pyproject.toml` selects `query=["umf-weft==W"]` and
  `typed-sdk=["umf_access==A"]`. The installed inspector is supplied by that
  explicit typed-SDK dependency closure. The qualified temporal install selects
  both extras plus its actual native/local requirements. Keep ordinary minimal
  installation behavior and refusal when optional owners are unavailable.
- The candidate environment contains ONE distribution owning import `weft`:
  umf-weft W. Legacy weft-sql and umf-weft must not coexist. Adoption includes
  authentic ordinary ABI1.2/HF62 qualification and audited semantic differences;
  changing distribution labels or guards alone cannot establish compatibility.
- Before final identities are selected, inherited0.10.7/dev9/0.4.56/0.0.54
  identify source staging only. Any private diagnostic artifact must record its
  exact source/hash and remain isolated from public indexes/caches. Final
  candidate qualification uses the actual selected C/A/W/T metadata together.
  A private wheelhouse may supply those explicit candidates to the normal
  resolver, with declared transitive dependencies satisfied and pip check clean.
  Require installed metadata/runtime/module origins and wheel hashes to match
  the candidate manifest; reject substitution by same-version public artifacts.
  No forced dependencies, --no-deps or installed-package suppression is allowed.

### Exact integration surfaces

In the isolated UMF parent, update `spec/release.json`, root `package.json` and
its lock metadata, first-party Cargo package manifests and `Cargo.lock`,
`python/pyproject.toml`, `python/umf_codegen/pyproject.toml` and the associated
runtime/binding package versions as enumerated by
`scripts/check-release-versions.py`. The companion requires exactly Core C.
Preserve the release contract's single first-party artifact identity and its
separate model/vocabulary versions. Existing dispatcher/publisher exact-version
allowlists and tests need a deliberately reviewed C entry; preserve historical
entries and all source/tag/wheel/archive guards. Access A remains independent.

In Weft, replace the DEV f629 revision in `crates/weft-core/Cargo.toml` and all
six consuming-root patches in `Cargo.toml` with ONE reviewed publicly fetchable
canonical coherent UMF revision; regenerate the actual consuming lock and
record features/source IDs. Set W in `crates/weft-python/pyproject.toml` and
`crates/weft-python/Cargo.toml`, plus actual release-coupled metadata selected
by its packaging checks. Do not indiscriminately bump unrelated workspace crate
versions. Preserve the existing Python module name and native/WASM feature gates.

In Truss, review `_query_runtime.py`'s ordinary publisher guard, release and
qualification dependency installation paths, `scripts/verify-weft-release-wheel.py`,
HF archive/runner producer metadata, and `.github/workflows/release.yml`'s
weft-sql name parsing, installed-version assertions and release-pins generation.
Adopt the real W distribution/assets/checksums and A/C installed tuple. Preserve
original frozen HF semantic assertions and historical T4A/051 fixtures; new
producer metadata changes require an actual delta receipt. Issue
`_temporal_owner/manifest.json` and `compiler.json` only from qualified actual
Core/Weft installed files, enroll their real hashes, and derive the new native
inventory from that complete source. Package T remains separate from native0.76
and ABI1.3 capability identities.

### Ordering and gates

Decision `truss.temporal-dependency-cohort/2-promotion` (2026-11-03): the human
supersedes this plan's earlier requirement to finish/publish Core0.10.7 before
promoting the qualified successor. Core0.10.7 publication is not a contractual
predecessor requirement. Frozen owner source reconciliation is MET: reviewed
owner `722b1e5484ca5e1558bb364ebdac22c995e140f9` is integrated through reviewed
assembly `576adc8ee5be92fc560fa4ae72b3ab09dd2b03cf` into canonical coherent source
`e3f38ef6f05ae636d2837f9d69f8d6805222664b` in the existing Root42/Access89 parent
lane. This decision governs contrary owner-completion/publication sequencing
clauses elsewhere in this plan and the linked integration plan.

Preserve the0.10.7 reservation, owner chat/worktree and all immutable tags,
assets and receipts. Do not publish0.10.7 for that owner. No additional external
approval is required; successor source/artifact qualification, normal resolver
closure, collision checks and public-byte/fresh-consumer gates remain mandatory.

1. Reconcile the frozen Core owner repair in the existing parent lane. Freeze
   C/A/W/T and all coupled metadata before final artifact admission. Private
   builds and installed qualification do not require owner package publication.
2. Publish the reviewed canonical coherent UMF source through that existing
   parent lane after frozen-source reconciliation. Weft
   pins the actual resulting full commit, never a predicted merge SHA. A public
   canonical source commit can precede its package upload.
3. Qualify one coherent locked/source/resource/feature cohort, then actual
   installed inspector/Access/Weft/Truss composition under the existing single
   admitted worker. Retain artifacts and successful receipts; repeat affected
   proof only when source, metadata, features or bytes change.
4. Release selected C=Core0.10.8 through UMF's existing coupled
   SDK/Core/companion/native/browser process and verify its public bytes and
   fresh consumers. Then release A=Access0.1.0.dev10 requiring public C and
   W=umf-weft0.4.57 built against the exact canonical source. A and W have no new mutual
   package dependency and may be delivered in either order when their own gates
   pass; serialize actual work through shared admission. Then release
   T=umf-truss0.0.56 after A/W are publicly available and T's own gates pass.
5. Final T public-only fresh installation must resolve the selected tuple
   normally and prove installed origins, pip check, enrolled hashes, ordinary
   ABI1.2/HF62, temporal TN gates and public-byte correspondence. Private
   wheelhouse success is not public dependency availability. A collision before
   publication selects another available identity and repeats affected metadata,
   package and consumer gates; preserve immutable tags/assets/receipts.

This addendum introduces no public integration stream or additional approval
flow. Exact identities, canonical merge SHA, compiled manifests and execution
results remain implementation outputs. Sol authored only this plan amendment;
no production metadata, source, tests, builds, ledger or owner checkout changed.
