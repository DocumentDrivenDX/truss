---
ddx:
  id: truss.journal-horizon-custody-plan
  type: implementation-plan
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.journal-horizon-initialization-custody
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: STP-045
      kind: informed_by
    - id: truss.temporal-native-qualification-plan
      kind: informed_by
---

# Journal horizon custody implementation plan

## Scope

Implement the private0.76 admission contract before either genuine timezone
capture. The new contract and schema own field shapes, authority, failure rules
and derivation. No evidence is produced by this planning change. Installation
remains explicit and fresh-only; preserve original initializer bytes, clocks,
source meanings and all published/frozen evidence.

## Shared constraints and design

The current finite pair of observed relation rows describes only those captures.
A timezone pair is not a calendar qualification. Replace that proposed new-target
finite admission with the contract's independently derived, protected witness;
retain each original capture literally. Do not modify native0.75 artifacts.

Instrument `CatalogReferenceAssembly.install_in_transaction` through a private
`_initialization_custody.py` helper. Split only the ordered source-unit list at
`groups.sql`: preceding units, pre-observation, unchanged whole groups unit,
post-observation, remaining units. Retain exact unit digests/order and execute
once through the original guarded cursor. `_installation_sql_batch.py` remains
an SQL-unit submitter, not a parser or clock interceptor. No global SQL rewrite.

Add a separate native `initialization-custody.sql` source unit for the private
relation and immutable trigger. Insert custody after original installation UUID
exists, before returning pending installation, within the same transaction.
Requalify source/manifest and every new table/type/routine/default ACL. Extend
existing installation-rights classification explicitly; no wildcard privileged
object exception. Support for nonempty managed policies requires exact ordinary
role denial and unchanged platform-trust classification.

Derive finite candidate pairs with PostgreSQL18.6 using only retained endpoint
parameters and retained zone. Native code is the calendar/timezone authority;
Python handles closed transport and exact bytes only. Keep old
`matches_inventory` literal behavior for old artifacts. The new verifier first
checks static definitions/ACLs with only boundIndex7 deferred, then validates
private custody and exact original row equality. It must not call unverified
installed routines or treat a Boolean from an ordinary caller as authority.

Add a new checksum-pinned initialization policy/schema in the new0.76 staging
artifacts. `assemble-temporal-native-baseline.py` must compare all static native
surfaces/ACLs exactly, validate each actual custody witness independently and
retain the two raw inventories unchanged. It must not emit a finite calendar
allowlist as the dynamic admission rule. Baseline source/policy hashes bind the
qualified helper and native derivation implementation. New storage/code changes
invalidate older compiled enrollment/source seals where those closures include
them; reissue genuine identities rather than edit a hash label.

## Exact source and test sites

- `packages/python/src/truss/catalog_runtime.py`: guarded installer preflight,
  original-unit bracket, contained post-DDL failure and pending installation.
- `packages/python/src/truss/_initialization_custody.py` (new private module):
  native observations, closed/schema-bound payload, window derivation and custody
  validation. `lifecycle.py` public shapes stay unchanged; reuse `incompatible`.
- `_catalog_runtime/initialization-custody.sql` (new): private row/immutability;
  `_installation_privileges.py`, `_runtime_admission.py` and native manifest/
  source-registration files: exact ownership/effective ACL and source closure.
  Preserve `_catalog_runtime/groups.sql` SHA-256
  `8d213c5b1243b2839c1ca6a465a709f20b5e03048da184bd58dea87d04ec95dc`.
- `_migration_recipe.py`, `_migration_verify.py`, `migrations.py`: closed new
  profile/schema loading, static-before-custody verification and backup /
  preservation behavior. No global reinterpretation of historical alternatives.
- `scripts/capture-temporal-native-inventory.py` and
  `scripts/assemble-temporal-native-baseline.py`: original full witness + literal
  inventory capture, independent policy qualification and new baseline staging.
- `packages/python/tests/test_current_baseline_native.py`, new focused
  `test_initialization_custody.py` and `test_initialization_custody_native.py`,
  existing installation-preflight/privileges/containment tests, and
  `test_temporal_baseline_staging.py`: JH-T01–09 source/native coverage.
- `scripts/qualify-temporal-native.py`, `scripts/temporal-native-case-ledger.json`
  and `scripts/temporal_qualification_support.py`: preserve every existing119
  case (39 temporal +1public54 +11ordinary +62HF +6baseline). Add exact new case
  IDs/count expectations with sensitivity controls; do not silently replace
  older cases to keep119. Keep existing default-OFF hosted selectors and leases.

These are permitted implementation sites, not a demand to touch every file.
Native-storage source registration follows the existing owner model/export
pipeline; no hand-labelled generated capability or inventory is accepted.

## Implementation slices

| Slice | Luna owner/write scope | Dependency | Review/validation gate |
| --- | --- | --- | --- |
| JH-0 | Noether: map exact schema/helper/private SQL and ownership grant changes; align packaged schema to the governed source | Contract freeze | Record bounded implementation scope with first source packet; this freeze permits JH-1/2 work, not capture |
| JH-1 | Noether: private helper, installer wrapper, new private native storage/ACL/immutability and contained refusal; no original groups SQL edit | JH-0 | Original-source byte/order controls; trusted native endpoints; rollback/caller-work/ordinary-denial source review |
| JH-2 | Noether: new-profile loader/verifier, preservation and backup checks, baseline assembler/capture receipts | JH-1 | Closed schema/policy, source/context/digest and complete candidate checks; old artifact algorithms unchanged |
| JH-3 | Noether: STP-045 JH-T01–09 tests and exact coherent-driver selection update | JH-1/2 | Focused pure/native source review; include meaningful controls, not just case-count updates |
| JH-4 | Noether: genuine installed Linux source/cohort/native manifest/seal, two serial unchanged-clock UTC/NY observations | JH-3 + actual final dependency artifacts | Separate actual admission review, raw inventories/witnesses and confirmed cleanup; no synthetic rollover claim |
| JH-5 | Noether: stage new baseline, coherent native campaign and public consumer/release evidence | JH-4 | Full required TN/HF62/ordinary/old54 refusal plus JH controls, then exact-tag/public bytes and fresh consumer |

Allowed source includes existing runtime installer, private migration/profile
verification, capture/assembler/selection and their relevant tests. Packaging
identity integration remains coordinated with its current Luna owner. Other
owner worktrees, compiler semantics and released artifacts remain outside scope.

## Execution contract

Human implementation/release authority is already supplied. Noether implements,
tests and runs hosted operations; Sol authors governing docs and reviews source
and actual admissions. No PG capture is admitted by this plan. Existing shared
local/hosted resource limits, one-worker native serialization, deadlines and
cleanup requirements remain unchanged. No heavy local work is added. Token
cost is unknown; no additional spending ceiling or budget reset is authorized.
Use the existing project import-boundary checker and its positive/negative
controls; changed modules need declaration adoption without baseline bypass.

## Validation plan

Use actual unaltered time for the two fresh installation captures. Separately,
parameterized PostgreSQL derivation checks exercise calendar windows without
running the initializer under an invented date. Pure/SQL fixtures are labelled
as derivation controls, not future-month native installations. Retain authored
independent expected endpoints and deliberately wrong month/DST/order controls.
Fresh readback must use original witness bytes after reconnect, session-zone
changes and an artificial verifier-current-time control; only the latter's
unconsulted verifier clock is synthetic. No server clock injection is allowed.

Put new native controls in the existing coherent campaign on one owned Linux
worker; update its exact selection manifest honestly rather than preserving a
stale count. Small source controls precede builds. Do not repeat successful
unaffected dependency/SDK campaigns. Retain successful artifacts and retry failed
jobs only when source is unchanged and their original provenance remains valid.

## Continuation evidence

Starting state: no witness implementation, no new0.76 timezone captures and no
calendar qualification. Noether returns the JH-0 interface/ownership delta and
implementation packets through the coordinator; planning readiness is not native
PASS. Record original source/wheel/helper/policy/schema hashes, clock endpoints,
zone, backend/transaction context, full candidate pairs, original bound row,
static inventory/ACLs and cleanup in capture receipts.

## Risks and rollbacks

- Trusted installer/DB/OS compromise is outside this profile; never claim the
  digest authenticates an administrator. Ordinary witness-write routes are bugs.
- Clock reversal, oversized bracket or timezone-rule mismatch refuses. Do not
  retry or repair installation automatically; preserve honest transaction state.
- A new custody table changes native source identity and ACL closure. Freeze and
  recapture the genuine target after implementation; never relabel old captures.
- Original horizon expiry remains operationally real. Admission does not keep an
  old partition writable indefinitely or add maintenance behavior.
- Rollback uncommitted installation/custody atomically through existing host
  containment. A committed unsupported installation is not reset automatically.

## Exit criteria

Source review must close trust, exact shape and complete refusal controls before
capture admission. Completion requires genuine new-target captures, unchanged
initializer proof, passing STP-045 JH controls and the existing full temporal /
ordinary / security / snapshot / HF62 / baseline gates, complete cleanup and
exact-tag/public-byte/fresh-consumer evidence. No historical lineage is reopened.
