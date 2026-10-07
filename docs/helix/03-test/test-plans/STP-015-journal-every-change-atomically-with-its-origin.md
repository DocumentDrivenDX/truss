---
ddx:
  id: STP-015
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-015
      kind: informed_by
    - id: TD-015
      kind: informed_by
    - id: SD-004
      kind: informed_by
---

# STP-015: Atomic journal and origin

## Story Reference

US-015, TD-015, SD-004, TP-001 and CONTRACT-002/004/007. Tests are planned.

## Scope and Objective

Prove complete atomic event/origin behavior on qualified journal modes without treating actor assertion as verified identity.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-015-AC1 | `two_properties_share_version_and_origin` | Exactly two expected old/new property events share entity/version/transaction/revision and actor a/role w | `@covers US-015-AC1` | Native integration | `tests/journal/atomic.test.ts`; independently authored diff fixture |
| US-015-AC2 | `caller_cannot_forge_database_role` | Caller role field cannot change trusted stored role; definer execution retains qualified acting-role identity | `@covers US-015-AC2` | Native integration | Same file; ordinary writer and definer fixture |
| US-015-AC3 | `journal_failure_rolls_back_canonical_effects` | Real journal failure after canonical work leaves object/derived/journal state unchanged | `@covers US-015-AC3` | Native integration | Same file; missing partition or faulting journal path |
| US-015-AC4 | `operation_envelopes_retain_complete_state` | Create/update/delete payloads match finalized independent envelopes, including edge identity and presence semantics | `@covers US-015-AC4` | Native integration | Same file; object and edge lifecycle fixtures |

## Executable Proof

Future command `bun test tests/journal/atomic.test.ts` requires test/harness creation. Criterion citations and exact server/adapter/journal-mode/role pins are mandatory. AC4 requires adoption and native realization of the authored complete envelopes; the proposed metadata sibling also requires explicit US-015 row-count reconciliation.

## Data and Setup

Independent observers inspect native canonical/derived/journal state. Expected values do not use production event builders. Include absent/null changes, retained content, endpoints/order/composition and two caller calls with distinct origins. Run each configured writer mode; no duplicated events or context leakage.

## Edge Cases and Failure Modes

Caller host rollback removes events and effects. Missing partition, constraint failure and cancellation leave no partial commit. Definer owner is not assumed to be acting role. Untrusted actor assertion stays labeled as asserted. Mode changes require separate no-gap/no-duplicate qualification.

## Build Handoff

Resolve envelopes/trusted context, write red native tests, implement event planning and persistence, then qualify modes. All four criteria block closeout. No feed/watermark or full historical reconstruction support follows from this story alone.


Conditional lexical-profile case `lexical_numeric_change_is_one_property_event` cites `@covers US-015-AC1` and `@covers US-015-AC4`. With explicitly adopted ADR-006/home/codec/envelope profiles, update 1.0→1.00 and independently expect one exact old/new property event with the genuine new owner version and trusted original origin, despite equal mathematical value/qualified key identity. Identical selected stored-value input yields the existing no-op with no extra event. Run engine and trigger modes separately; ordinary normalized native numeric equality cannot suppress the change. Require the selected engine/trigger writer to preserve the same complete lexical event meaning; this test does not define a journal-disabled mode.

Fault journal persistence after canonical lexical replacement and require confirmed rollback of complete token/value/source/key/version/event state under `@covers US-015-AC3`; unresolved containment remains unknown. Old original lexical state must come from its actual selected source/carrier, never formatted legacy numeric output. These cases require the selected profiles/envelopes and actual native harness before execution; they do not accept ADR-006/007 or qualify compiler numeric lowering.

### Complete-profile journal count reconciliation gate

Keep the existing AC1 two-property-row observation explicit and also inspect the complete unfiltered journal sibling inventory. Under the currently proposed CONTRACT-002 snapshot procedure, independently expect two property events plus one metadata boundary witness with a single complete three-event manifest. The owner selected this three-event interpretation on 2026-10-07; US-015 now explicitly distinguishes property deltas from the metadata witness.

Under the reconciled requirement, do not pass by filtering the third event, counting only schema-valid rows or dropping the metadata witness. Pin the exact requirement/profile version and independently verify both total inventory and property projection, original origin/version correspondence, complete snapshots and actual positions/digest. STP-018 owns reconstruction and native capture schedules; a correct property projection alone does not establish complete history.

### Multi-entity original snapshot custody controls

For the proposed registry-reuse profile, independently author one operation affecting object id 7/version 3, edge id 7/version 2 and object id 9/version 5. Give each distinct complete start/final values, definitions, owner contexts and original event sequences. Require one exact indexed boundary inventory for each affected typed entity/version under the original operation, despite coinciding native IDs. Inspect full event and snapshot membership in both directions; a total count of three cannot replace matching those three exact identities.

Refuse object/edge id-only matching, operation ordinal substituted for version, duplicated inventory masking a missing entity, an extra unrelated snapshot, candidate bytes relabeled as observed final state and original bytes changed after admission. Repeat two operations on the same entity in one host transaction: the second starts from the first's actual pending result, and snapshots cannot cross operation custody. A retry after savepoint rollback uses its newly admitted original tuple; rolled-back registry bytes and allocated positions do not become reusable history evidence.

Charge all original byte artifacts and simultaneously decoded start/candidate/final inventories before native collection. An oversized second entity refuses the operation under original containment rather than publishing the first entity's complete-looking group. Retention/cleanup must preserve unresolved original attempt and actual dependency evidence; phase finalized alone is not commit confirmation. These are conditional planned tests under US-015-AC1/AC3/AC4 and CONTRACT-002/007, requiring selected original-artifact grammar, native capture and profile adoption before execution.

### Snapshot versus append-clock controls

Independently author complete start/final record timestamps, then append their admitted events at a later physical journal time under the selected native clock profile. Require unchanged original record createdAt/updatedAt and corresponding semantic digest; separately observe actual at and partition identity. Refuse an append helper that overwrites metadata.after.updatedAt with its journal clock or a validator claiming digest equality establishes physical routing time. A physical partition boundary crossed between snapshot capture and append is governed by actual routing/atomic failure, not the record timestamp. No timestamp is treated as commit order. These planned controls require exact selected native clock/descriptor/source evidence.

### One-row complete-envelope carrier controls

Under the separately adopted carrier candidate, independently compare full envelope identity/kind/type/version/revision/xid/seq/property/origin with physical columns for every selected event variant. Alter each duplicated physical fact while retaining a valid envelope and digest: refuse before disclosure or complete-history admission. SQL NULL old_value does not remove delete.before or property.before inside the envelope. A metadata payload requires its explicitly admitted physical op, not a guessed NULL-property interpretation. Retain member count does not multiply event count or duplicate native seq.

Attempt baseline decoding of complete-envelope rows and complete-profile decoding of legacy rows: mismatched layout/encoding profiles refuse, rather than returning an envelope as application data or fabricating missing before images. Exact source/export/native constraint and migration qualification remains required; these are proposed tests and no current SQL or event schema was migrated.

### Historical physical domain boundary controls

Independently test signed-int8 maximum 9223372036854775807 and the next value 9223372036854775808 for record IDs/version/seq under the selected positive native profiles; separately test signed-int4 endpoints and one-beyond catalog IDs under their original allowed/reserved identity policy. Include values above host exact-number precision and a full-xid value valid for its selected wider domain but invalid as seq. Schema-valid strings cannot bypass native range admission. No lossy Number conversion, wrap or generic positive-catalog rule is permitted.

Attempt a mutation at exhausted record version: reject before effects and event allocation under its selected procedure, rather than returning a larger full metadata image. Native allocator exhaustion and uncertain response preserve prescribed outcome/containment. These planned cases require actual native type/descriptor/profile proof; structural schema acceptance alone does not qualify the boundary.

### Original assertion versus trusted-role projection controls

Independently author actor/load/reason, unknown x-* exact content and an asserted false db_role. Under the new carrier profile, preserve admitted original assertions in the envelope while databaseRole and physical db_role match independently captured original data-caller evidence. Definer owner and caller role text cannot overwrite that trusted role. Assert a request-shaped field during request-free execution: it remains assertion content under the selected input grammar and cannot trigger receipt lookup/storage, change group identity or authorize replay. If that input grammar forbids the field, refusal is explicit rather than synthetic request admission.

Alter only physical origin, swap staged groups' origins, change transaction-local origin after capture or normalize exact numeric/unknown content: refuse correspondence or preserve the separately declared limited-projection scope. Verify same selected behavior in engine and trigger modes, rollback/context restoration and no leakage into later host calls. Actual native capture/encoder and lossless input grammar remain prerequisites; schema strings or assertion-shaped objects prove no authentication.

### Complete-producer simultaneous resource controls

Use the complete required fixture and independently account original start, candidate, observed final, event envelopes/siblings, canonical/digest/native parameter/result copies and pending/uncertain evidence. Keep the start alive through final admission so releasing it prematurely cannot produce a false peak measurement. One-over peak/spent/path admission refuses under prescribed containment; a successful direct-read resource receipt is not producer admission. A single retain event with many members and a full metadata witness cannot be charged as two small rows. Verify occupancy release separately from spent work and unresolved recovery retention, including failure during cleanup. Actual native/account source and selected ceilings are prerequisites for execution.

### Original byte custody cannot become mutable history staging

Independently retain original prestate/candidate/group bytes through native effects and collect final snapshot/actual positions separately. Attempt to rewrite an original byte slot or fill application_result_bytes at readiness/seal: refuse under the selected phase/native privilege profile. Verify original bytes unchanged through successful publication/finalization and rollback. A lost/unqualified private staging buffer cannot be repaired from current state or by premature application completion. Test the explicitly selected native scratch or versioned store lifetime/resource/recovery design; existing phase shape/source checks alone do not establish that staging.

## Complete snapshot collector composition controls

Extend `tests/journal/atomic.test.ts` for TD-015's collector procedure under the exact selected native profile. These planned controls supplement existing criteria and remain not_run:

- Independently expect a complete object and edge image containing defined, optional absent, null, nested and retained content; compare header, full membership, original source and definition/owner correspondence together.
- Inject a missing/duplicate header, foreign owner state, omitted required tree node, duplicate shadow home, unclassified extra property, missing retained home and changed temporal descriptor separately. Every case withholds the whole snapshot and journal group; no convenient valid subset passes.
- Pause between collector components while a competing writer changes the same record, endpoint or active definition. Require the selected native protection/revalidation to retain one qualified operation boundary or refuse; mixed-cut images cannot receive a valid witness.
- Run two operations on one identity in one host transaction, then roll back the second savepoint and separately the outer transaction. Independently verify each original start/final pair, immutable prior custody and the complete surviving/rolled-back event inventory.
- Exhaust each selected resource dimension before header/property/retained/final materialization and interrupt each phase. Assert complete containment or original unresolved recovery classification, no partial publication and no spent-work refund used to force success.

A parser round trip, mocked collector, public direct-read result or schema-valid assembled object is insufficient native evidence for these controls.

For the metadata retained-column branch, independently check the exact twelve-column object and fifteen-column edge descriptors, original typed parameter domains and both retained carriers. Select it against baseline-only, missing-column, foreign same-name-column and wrong-type layouts separately: no effects, no fallback query and no empty-image publication may occur. Corrupt the edge retained value while preserving all other projected fields and require full candidate/final parity refusal. Source capture evidence alone cannot pass these native tests.

## Exact event/origin byte carrier controls

For the separately selected component carrier, independently author complete events/origins containing admitted embedded NUL, Unicode, exact numeric-token spelling and ordered member arrays. Compare original decoded canonical bytes and every native identity/op/property/origin fact before and after publication; do not use production encoding as the sole expected-byte oracle. Corrupt base64 padding/pad bits, UTF-8, decoded hash, component/profile/version, duplicate JSON members, canonical-byte ordering and independently captured database role separately. A recomputed attacker-supplied hash cannot legitimize substituted original context or physical columns. Exhaust before decode/parser/allocation and interrupt during each stage; withhold all events and preserve existing contained/uncertain recovery meaning.

The [eleven-case byte transport experiment](../../04-build/evidence/design-audit/journal-exact-bytes-experiment.json), reproduced with normal/optimized `python3 docs/helix/04-build/evidence/design-audit/check-journal-exact-bytes.py`, proves only scoped byte round trips and canonical-base64/strict-UTF8 refusals. It does not execute JSONB, validate complete event JSON/canonicalization, resolve original semantics or qualify native producer/resource/authority behavior. Its 4096-byte experiment guard is not the production resource profile.

The [journal JSON canonicalization experiment](../../04-build/evidence/design-audit/journal-json-canonical-experiment.json) adds eight independently authored expected-byte cases and twelve refusal cases, passing under normal/optimized Python. Cases preserve control/NUL escapes, Unicode scalar and decomposed spelling, original token text and domain-member order, and reject duplicate keys, alternative escapes/order/whitespace, raw numeric/nonfinite nodes, invalid UTF-8, trailing data and unpaired surrogate behavior. Reproduce `python3 docs/helix/04-build/evidence/design-audit/check-journal-json-canonical.py`. Native and host implementations must match independently expected complete component bytes while still admitting original semantic profiles and pre-materialization resources. The experiment's Python parser/depth/byte guards are not a qualified production parser or native capacity producer; opaque unsupported meaning cannot be repaired through its refusal path.

For the coarse complete-carrier constraints, plan native cases with SQL NULL/missing/incorrect new_value and origin wrapper members, non-NULL old_value, wrong op/property NULL classification and zero/negative graph/version/sequence values. Missing wrapper keys must refuse rather than pass via CHECK unknown. Independently attempt a shape-valid wrapper with forged hash/component bytes/origin/physical identity: protected full producer/finalizer admission must still refuse; coarse CHECK success is not qualification. Confirm metadata op admission only in the explicitly selected proposal layout and no automatic baseline/profile conversion. Native cases remain not_run.

## Protected producer callable phase controls

Plan independent native calls to each proposed capture/transition/final/reserve/append boundary with original live context and with substituted operation/role/epoch/profile/generation/typed scope, expired savepoint and wrong phase. Capture-after-effects, caller-invented transition bytes/count/positions, reserve-before-full-final inventory and append-before-original reservation must refuse. Exercise engine/trigger double-dispatch, early full seal followed by another raw write, recursive same-operation invocation and uncertain reservation/append responses. Inspect complete native custody/publication and original generation through the independent privileged observer; private return bytes cannot count as commit or producer authority. Repeat complete rollback/resource/authority schedules and verify immutable original registry slots/application-result phase remain unchanged. Exact signatures and expected phase behavior are design candidates; all native cases remain not_run until actual grammars/bodies/guards and selected deployment are available.

## Producer phase native supplement allocation

These five stable supplements implement the full phase controls above in `tests/journal/atomic.test.ts` after the selected protected producer/staging/native account/guard profile exists. They add no acceptance criteria; qualifying AC1 requires the complete owner-selected three-event inventory and actual native producer evidence. All are not_run; eighty-two proposal shape controls are supplementary evidence only.

| Case | Planned function | Existing criteria | Independent native observation |
| --- | --- | --- | --- |
| JP-01 | `capture_complete_original_scope_before_effects` | US-015-AC1, US-015-AC4 | Full original object/edge boundary and source/home/owner inventory under the actual protected cut; wrong context/phase and incomplete visibility refuse before effects. |
| JP-02 | `observe_original_ordered_semantic_transitions` | US-015-AC1, US-015-AC4 | Actual native before/after and original effect order/membership, including retained additions and later rebind; physical row changes cannot manufacture semantic sibling counts. |
| JP-03 | `prepare_independent_complete_final_boundaries` | US-015-AC1, US-015-AC3, US-015-AC4 | Independently collected full candidate/final parity and complete original group scope; missing/foreign/duplicate states or failed finalization restore prescribed effects and preserve consumed-allocation semantics. |
| JP-04 | `reserve_original_complete_sibling_positions` | US-015-AC1, US-015-AC3 | Actual native allocator range/order/uniqueness and original prepared correspondence with legal gaps; exhaustion, rollback and uncertain response cannot authorize duplicate allocation/publication. |
| JP-05 | `append_complete_native_semantic_origin_correspondence` | US-015-AC1, US-015-AC2, US-015-AC3, US-015-AC4 | Complete actual physical rows/clock/descriptors versus event/origin/canonical component/manifest and independent native role; append failure rolls back graph/derived/publication together, while commit/application remain separately observed. |

Each supplement includes resource reservation/exhaustion and authority/phase invalidation at its actual materialization/publication boundary. Run both qualified engine and trigger modes, actual savepoint/outer transaction schedules and current acting-role/owner contexts; unsupported mode/profile prerequisites remain unavailable/not_run. Record exact native/adapter/codec/body/resource builds and original independent fixture/case membership. A copied producer result, schema-valid placeholder artifact or mocked driver cannot pass these observations.

### Producer supplement schedules for bytes, prefixes and private rights

The following schedules refine JP-01–JP-05 rather than adding criteria or declaring selected deployment support. Use independently retained original bytes and privileged native observations; record actual phase entry, reserved/spent resources, complete stage headers/bodies, journal rows and host settlement separately. Every schedule remains not_run.

| Schedule | Existing supplements | Controlled action and required observation |
| --- | --- | --- |
| Exact phase bytes | JP-01–JP-05 | Independently author one complete canonical body for each selected phase, then inject duplicate members, reordered keys, alternate escapes, BOM/trailing data, raw number nodes and malformed UTF-8 separately. Require whole-body refusal before stage/allocator/publication effects; original nested component and operation-context bytes remain unchanged. Shape-only success cannot pass canonical admission. |
| Resource admission | JP-01–JP-05 | Exhaust input, parser/member/depth, sort/regeneration and cumulative native/host copy budgets at each boundary. Independent account observation must show reservation before materialization, contained failure or retained unknown custody, and no refunded spent work permitting a later success. Profile finite limits are fixture inputs, not experiment constants. |
| Complete empty operation | JP-01, JP-03–JP-05 | Admit an independently proven empty scope and progress through start/final/empty mapping/empty pending publication. Observe no allocator invocation and no journal event rows. Missing visibility or unresolved effects cannot be treated as empty; neither empty stages nor the parent phase proves commit. |
| Frozen final generation | JP-02–JP-05 | Pause after final, attempt a new engine effect and separately a deferred trigger effect. Pre-effect guard refuses where possible; any discovered later effect invalidates full finalization and successful settlement qualification. Verify no reopening/replacement of final/reserved/publication and no second group under the original operation. Earlier transition generations remain admitted original evidence. |
| Lost response at each phase | JP-01–JP-05 | Suppress the actual response after the native stage/effect boundary. The host must not reinvoke the producer; resolve only through qualified original observation. Distinguish committed, rolled back, still active and unavailable original custody. Preserve actual position gaps and immutable pending durability; no automatic replay or generic callback-result reconstruction. |
| Private rights closure | JP-01–JP-05 | Attempt ordinary direct/inherited stage read/write, public/default helper execution, nested definer role substitution, malicious namespace resolution and elevated wrappers accepting arbitrary bytes. All paths refuse without private body/count leakage. Independently test incompatible filtered observer policy as unavailable complete scope, rather than accepting a partial inventory. |
| Recovery/retention crossover | JP-04–JP-05 | Attempt unqualified original recovery and active/unknown-settlement child deletion through producer or administrator paths. No body disclosure or deletion occurs without complete original authority/settlement/dependency proof. Qualified cleanup cannot rewrite pending bodies, orphan recovery custody or refund spent work. |

Interleave competing participating commands with barriers while each prefix is read and extended. Verify original command exclusion and exactly one immutable phase extension; coarse SQL EXISTS/PK success does not establish this property. Repeat relevant schedules for every selected producer mode and staging branch. The qualified-prestate-reuse branch needs its independently authored equivalent start/prefix fixtures; do not reuse explicit-start-slot expectations by omitting a row without reviewing custody semantics.

JP-02 additionally checks the selected request/result reuse grammar: pass a valid closed transition body with foreign original operation context, stale copied ordinal, forged native evidence and substituted before/after delta separately. Actual protected native effect/prestate observation must refuse each despite shape/canonical-byte validity. Verify independent original request/result custody and derived ordinal rather than blind request insertion, then lose the reply and observe original stage recovery without reinvocation. Creation/deletion/metadata effects cannot enter by relabeling themselves as property deltas.

### Selected journal phase resource boundary schedules

JP-01–JP-05 additionally use the separate journal-phase resource proposal and the original enclosing operation/group/transaction/retention allowance. Independently author and count source bytes, container depth (root object is depth one), token/member occurrences, source-string escape bytes, sort comparisons, regenerated output, actual native/host/stage copies and retained cleanup footprint. The earlier Python canonicalization experiment starts its local recursion counter differently and is not a production boundary oracle; do not reuse its success as evidence for depth 64.

For each selected dimension, construct an original fixture at the limit and one beyond while independently ensuring all other applicable limits fit. Where the selected complete schema/native meaning cannot realize that isolated maximum, record the exact unavailable combination and qualify its conservative admission/refusal instead; never weaken another bound or replace the full body with a synthetic unsupported tree to report success. Observe native pre-materialization reservation and actual complete result membership, not only post-allocation errors.

Repeat equivalent original parse/encode observations until cumulative work/allocation or the original deadline is exhausted. A new phase name, reentry, separately serialized artifact or equal request/result hash cannot reset the account. Interrupt during member sorting/regeneration and native decode, then independently verify containment or retained original unresolved reservations. Nested event/origin base64 decoding charges its own actual copies within the same remaining allowance.

Construct a body within the per-envelope cap whose complete parent/stage/cleanup closure cannot fit the retained cohort bounds; refuse capture/growth under the governing original operation containment, preserving earlier obligations. Run both engine/trigger modes and every selected staging branch. Profiles with unknown native detoast/parser/sort/copy upper bounds remain unavailable before materialization. These tests remain not_run until actual native resource and codec/build realization is selected.

JP-03/JP-05 qualify nonsealing final observation separately from full readiness: observe native final values while the original parent remains admitted, with readiness/sealed/application proofs NULL. Full RF sealing before complete publication refuses; successful collector output cannot set any seal. After actual append and selected dependent report/group effects, independently verify readiness, RF seals and application finalization in order. A dependent effect changing frozen generation/image must invalidate the candidate rather than trigger header repair or skipped accounting.

JP-02/JP-03 additionally attempt the general OC04 reset through stale body, alternate overload and elevated wrapper after a frozen stage exists. Original stage-enabled tuple recognition must refuse before generation/canonical effects, with no fallback on missing stage visibility. Independently verify complete effective native paths and exact original body/profile pins; merely choosing the correct SQL in a host mock cannot qualify this guard.


JP-03/JP-05 additionally distinguish whole-operation membership from per-entity/version manifests. Independently author one operation containing two changed typed entities with different sibling counts and one unchanged entity. Include interleaved source positions for the changed boundaries; verify separate original ordered digests/counts, exact once-only global ordinal assignment, no unchanged-entity manifest and complete whole-operation append parity. Substitute an operation-wide manifest, duplicate a boundary declaration, omit/double-assign an ordinal or substitute kind/source/version and require whole-operation refusal. Include a deletion whose prior envelope version differs from its event mutation version, and two operations in one host transaction affecting successive versions of the same entity. The latter must retain distinct historical groups and still require the separate complete transaction manifest. A failed boundary cannot leave a successful published prefix; observe actual rollback/unknown settlement separately. These native schedules remain not_run.


For TD-015's five-sibling allocation schedule, JP-03–JP-05 independently expect A membership [0,2], B [1,3,4], unchanged C [] and position sequence [101,104,109,113,120]. Preserve original strings; these allocated gaps cannot be replaced by ordinal-derived positions. At preparation, reservation and stored publication separately inject a missing member, repeated member, extra member and identity/kind/version substitution. Require whole-boundary and whole-operation refusal with no rewritten original custody. Before native execution, pin complete original event/origin bytes and an independently authored per-boundary digest expectation; the symbolic table alone is not a digest oracle or a native pass.
