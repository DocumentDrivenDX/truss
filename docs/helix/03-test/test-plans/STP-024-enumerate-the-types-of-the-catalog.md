---
ddx:
  id: STP-024
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-024
      kind: informed_by
    - id: TD-024
      kind: informed_by
    - id: SD-005
      kind: informed_by
---

# STP-024: Consistent catalog enumeration

## Story Reference

US-024, TD-024, SD-005, TP-001 and CONTRACT-001/003/007. Tests are planned.

## Scope and Objective

Prove complete one-revision catalog views and measure the proposed latency target independently.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-024-AC1 | `complete_catalog_matches_inventory` | All 1,000 types plus every expected property/key/endpoint/flag appear under one revision | `@covers US-024-AC1` | Native integration | `tests/catalog/enumerate.test.ts`; independent manifest |
| US-024-AC2 | `concurrent_acceptance_never_mixes_view` | Acceptance between component reads yields exactly old or new inventory, never a hybrid | `@covers US-024-AC2` | Native integration | Same file; two clients/barriers and distinct manifests |
| US-024-AC3 | `hundred_call_p95_meets_proposed_target` | 100 sequential complete enumerations produce retained distribution and p95 at most proposed 20 ms | `@covers US-024-AC3` | Native performance integration | `tests/benchmarks/catalog-enumeration.ts`; pinned measurement boundary |

## Executable Proof

Future commands `bun test tests/catalog/enumerate.test.ts` and `bun tests/benchmarks/catalog-enumeration.ts` require harness/files. Criterion citations and actual server/runtime/model/view profiles are recorded. Proposed target is not claimed achieved.

## Data and Setup

Storage-binding provenance fixtures use accepted_binding, exact accepted binding/vocabulary/pointer, and separate owning-Record document provenance. Reject a missing/unaccepted binding archive, wrong vocabulary, wrong owning Record/component closure or a fabricated UMF key pointer. accepted_document remains the core-Key source path. Unknown binding meaning is preserved but cannot become an interpreted key entry without a selected extraction profile. Compare full accepted archives independently; schema-valid hash syntax does not prove provenance.

Core-Key identity fixtures rename and reorder a key while retaining its stable authored ID and independently assert the same local number. Changing fields under that ID rejects through UMF validation; a new ID cannot inherit an old mapping by equal name/position. Equal opaque key IDs in different owning Records remain separately scoped. Verify reference.authoredIdentity resolves the exact archived key ID and owning Record rather than its authored pointer ordinal. Legacy/native profiles without stable authored key identity cannot claim core-Key identity by substituting a constraint name. Historical mapping survives current retirement/revision according to the selected lifecycle profile.

Provenance fixtures retain an original definition accepted at revision 1, then accept revision 2 with an unrelated change: enumeration at revision 2 still resolves the definition's original archive tuple. Update that definition in place at revision 3 and independently resolve both old and new pins to their exact document revision/bytes. Wrong document ordinal, mismatched digest, nonexistent authored pointer, incompatible extraction profile and a key resolving another Record all refuse. Unknown extension bytes survive the pinned extraction/derivation procedure. Schema-valid archive metadata does not satisfy these native/semantic probes.

Request-side fixtures distinguish current selection captured before concurrent acceptance from explicit historical selection. Missing historical definition refuses without current-head fallback. Duplicate owner requests, zero/negative/noncanonical limits and hidden dependency expansion refuse; exact-bound output succeeds and one-byte/one-definition overflow publishes no partial view. Include archived definition bytes in size accounting, not only reference rows. Caller-selected owners never confer authority.

Include two types with keyNumber 1 and independent authored key identities: both must survive enumeration and resolve to their own ordered components. Wrong property owning-type references refuse even when propertyId exists. Numeric IDs 2 and 10 sort numerically, not lexically; key definitions sort by the complete (typeId,keyNumber) tuple without changing component order.

Independently validate the [catalog view declaration](../../02-design/contracts/bindings/truss-catalog-view-v0.1.d.ts): duplicate reference, missing composite-key component, wrong owner/pin, corrupt archived definition bytes and conflicting retirement/provisional flags refuse. A zero-row restricted projection cannot become an empty complete catalog. Hidden required dependency closure refuses without revealing its identity. Shuffle native row arrival order and compare deterministic inventory output while preserving authored key/member order. Unknown extension bytes survive unchanged.

Independent inventory includes retired/provisional types, composite keys and cross-module endpoint cases. Compare every definition/member identity rather than counts. Empty catalog is revision zero/no types. Concurrency setup observes actual head update and snapshot/lock boundaries. Benchmark includes decode/assembly at the public-call boundary.

## Edge Cases and Failure Modes

Restricted role projection must be labeled and have explicit endpoint closure policy. Missing selected definitions, incompatible pins or resource overflow cannot silently truncate. READ COMMITTED transaction without consistent context must fail the mixed-view fixture. Historical enumeration requires its separately qualified definition source.

## Build Handoff

Key binding admission probes follow the contract's ordered phases and independently validate accepted archive/source ownership, stable IDs, ordered fields and registered comparator/null/encoding profile before native backfill. A malformed binding cannot cause comparator registration, DDL or partial mapping writes. Source-valid/unsupported storage profile refuses explicitly without extra UMF invalidity diagnostics. Backfill collision/resource failure leaves the old head, exact mappings, reservations and reports unchanged. A schema-valid binding/view cannot bypass this semantic inventory gate.

Finalize view/context policy, write red native inventory/race cases, implement reads/assembly and qualify visibility/latency. All criteria block complete-profile closeout; proposed performance is reported separately from correctness.


### Concrete 100-call experiment handoff

The proposed benchmark fixture is an independently authored complete current catalog of 1,000 defined types. Each has four properties (two text, one integer and one boolean), two named keys (one text component; one ordered text/integer composite) and one directed relationship to the next type, wrapping the final type to the first. Expected membership is 1,000 types, 4,000 properties, 2,000 owner-qualified keys, 3,000 ordered key components and 1,000 relationship definitions with 2,000 endpoint references. Stable authored identities and source archives define membership; local numeric identities are resolved through the selected accepted catalog rather than guessed from generation order. This is a proposed semantic dataset, not a UMF support claim: its exact source and selected key/value/relationship profiles must be admitted before execution. Missing representability blocks this experiment rather than reducing its shape. Separate retired/provisional/empty/historical/disclosure and concurrent-revision correctness fixtures remain required by the rest of this plan.

Freeze exact original fixture bytes, complete independently expected membership/order and accepted source/profile pins before the run. Require the public complete-view operation; no projection, type-count-only query, private SQL shortcut or mapping cache can replace enumeration. If an admitted cache is part of the selected public implementation, preregister its state/invalidation profile and report the configuration separately; the 100-call series cannot silently change into a different cold-cache experiment. Fix index/statistics inventory, explicit selected context lifecycle and connection reuse policy before measuring; record transaction/context acquisition within the public operation boundary it actually uses. Setup and warm-up are separate from the exactly 100 sequential measured calls.

For every measured call, start the monotonic clock immediately before public invocation and stop only after the complete validated public view resolves. Then compare its full original identity/member/archive/revision result to the independent fixture, outside the latency boundary. Correctness failure still fails the measured series and retains that sample, even if its duration meets the threshold. Concurrent acceptance belongs to the separately barrier-driven AC2 experiment; do not fold unexplained revision changes into the stable latency dataset. Archive all 100 original ordinal/duration/outcome/result-fingerprint records and the complete expected/actual result correspondence, plus original environment/configuration pins and warm-up observations.

Compute p95 as rank 95 of the 100 ascending exact duration values; ties retain all samples and no sample is dropped. Equality to proposed 20 ms passes the proposed numerical comparison, subject to correctness and original profile evidence. A 99-sample series, duplicate/missing ordinal, negative/noncanonical duration, nonmonotonic clock observation, timeout, incomplete result, wrong revision, hidden key component or changed configuration is a failing/unverified experiment rather than a latency pass. Native diagnostics and server-only timings may accompany the receipt but cannot replace the public measurement. Include synthetic 100-sample cases with rank 95 below/equal/above the threshold and one extreme slow final sample to verify the assessor independently; these controls qualify assessment only. The 20 ms product target remains proposed until owner adoption.


The [authored benchmark UMF fixture](../../02-design/contracts/bindings/catalog-enumeration-benchmark-v0.1.proposal.umf.json) now realizes this full proposed shape. All 1,000 relationships have module-unique names; the initial repeated next name was rejected by the pinned owner validator and corrected without reducing the ring or workload. [Source receipt](../../04-build/evidence/design-audit/catalog-enumeration-benchmark-source.json) records UMF 16c35e8d validation valid=true/complete=false, exact serialization/reload tree, complete independently specified type/field/member/key/ring identity correspondence and four refused endpoint/key/bound/duplicate-name variants. Existing experimental metadata warnings remain preserved. Run `bun docs/helix/04-build/evidence/design-audit/check-catalog-enumeration-benchmark-source.ts` from the Truss root. This proves proposed source validity/shape only; exact native catalog/codec/key binding, accepted local IDs, public enumeration and latency remain unqualified.


The fixture checker now compares every complete authored field, record/key and relationship definition against an independent expected grammar, including scalar/presence/cardinality, names, primary designation, ordered components, exact ring endpoints and multiplicity/lifecycle/direction. Object-key spelling order is excluded from comparison; authored arrays retain order. Six separately UMF-valid variants (changed scalar family, presence, composite-key order, relationship bound, ring endpoint and record name) are all rejected as changed workloads. These are fixture-profile refusals, not upstream-invalidity claims. The receipt retains their UMF validity/completeness and distinct expected refusal classification; they supplement the four genuinely invalid upstream controls. No live enumeration, native decoder or performance assessor was executed.


The [p95 mathematical witnesses](../../02-design/contracts/bindings/catalog-p95-math-v0.1.vectors.json) now provide eleven independently authored cases: five exact Decimal rank/comparison outcomes (below/equal/above, tied values and a retained huge slow outlier), plus six sample-count/ordinal/domain refusals. [Independent receipt](../../04-build/evidence/design-audit/catalog-p95-math.json) checks exact complete witness membership and the governing 100/rank-95/proposed-20-ms tuple. Reproduce with `python3 docs/helix/04-build/evidence/design-audit/check-catalog-p95-math.py`. Compact run descriptions expand to all original samples; the outlier remains retained even though rank 95 excludes it from that statistic. The oracle qualifies mathematical expectations only. The actual runner/assessor must additionally reject malformed duration grammar, native clock uncertainty, failed/incomplete view outcomes and configuration/result mismatches under the registered experiment; a mathematical within-threshold result cannot override any such failure.


Benchmark key-shape handoff now has [six independently authored byte witnesses](../../04-build/evidence/design-audit/catalog-benchmark-key-tuples.json) using the existing UMF operation 2.0.0 on this exact core-0.7 fixture. They cover Unicode single keys on first/last owning Records, ordered text/integer composites, integer magnitude beyond host safe-number range, alternate exact exponent spelling, zero and negative values. Four typed arity/wrapper/missing-key/fractional-integer controls refuse through the owner's expected error codes. Run `bun docs/helix/04-build/evidence/design-audit/check-catalog-benchmark-key-tuples.ts`. Identical payload bytes under different owners remain distinct qualified key identities; equal integer mathematical values may encode equally despite distinct original tokens. These selected examples do not qualify all native key registrations, storage uniqueness, catalog acceptance or Weft binding. The full 2,000-key source membership remains separately verified by the fixture checker; production integration consumes the UMF operation instead of copying this byte oracle as an encoder.


### Equal-membership revision race fixture

The [second authored revision](../../02-design/contracts/bindings/catalog-enumeration-race-revision-two-v0.1.proposal.umf.json) retains the same document/module/element/key/relationship identities, member/component order, endpoints, bounds and 1,000-type counts while changing every field, record, key and relationship display name. [Source receipt](../../04-build/evidence/design-audit/catalog-enumeration-race-source.json) proves both sources UMF-valid/incomplete, exact second-source serialization, complete display-name-only delta and three separately UMF-valid hybrid-source refusals. Reproduce with `bun docs/helix/04-build/evidence/design-audit/check-catalog-enumeration-race-source.ts`; also retain the independent first-fixture check. Source hybrid comparison is not the production native-view oracle.

The native AC2 harness first accepts the original fixture through public acceptance and observes commit. Client A begins enumeration under the exact selected consistent context; barriers pause after actual context/revision capture and between each component collector. Client B publicly accepts the second original source under normal catalog authority. Snapshot profiles may allow B to commit while A retains the old view; a selected head-exclusion profile instead requires B's observed wait until A releases its context. Do not force an impossible mid-lock commit or turn an unobserved wait into evidence. After original completion/release, a new enumeration returns the second committed view. Each answer compares every original definition/member/source pin and all display names with independently authored expected old or new catalog state; equal counts and matching revision headers cannot hide a hybrid.

Independently assert stable local identities for every admitted unchanged lineage and key owner under the selected lifecycle profile, plus exact changed original archive/definition provenance. Never derive expected local IDs from the returned answer. Missing source, publication, current authority or context proof remains unavailable. Lost writer completion or reader cancellation uses original transaction/containment recovery and is not a successful race result. This race is separate from the stable 100-call latency experiment and does not select retired reactivation, change key component semantics or qualify Weft mapping.
