---
ddx:
  id: STP-020
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-020
      kind: informed_by
    - id: TD-020
      kind: informed_by
    - id: SD-005
      kind: informed_by
---

# STP-020: Exact object lookup

## Story Reference

US-020, TD-020, SD-005, TP-001 and CONTRACT-001/004/007. Tests are planned.

## Scope and Objective

Row-home join qualification uses independently authored owner bags containing duplicate owner occurrences and optional absent, required absent, present-null, scalar and container properties. Optional absence preserves every owner occurrence; required absence refuses. A null root with no scalar payload returns present-null; a scalar root with no payload refuses. Extra null/container payload, duplicate state/root/payload, nonparentless root and wrong typed owner refuse without partial publication or accidental row multiplication. Place corruption behind an excluding predicate to test the stored-domain obligation rather than SQL evaluation order. Edge fixtures use unequal valid relationship/property-owner IDs and equal invalid IDs: only the original association proof decides ownership. Run both current authorized and incomplete/hidden observations; the latter cannot prove absence. These are planned native/Weft controls, not executed support evidence.

[Native comparator vectors](../../02-design/contracts/bindings/native-comparator-vectors.proposal.json) provide seventeen independent planned equality/order/refusal expectations. Qualify each under actual source facets/native domain/cast/operator/collation and original stored-domain enforcement; token pair spelling alone cannot establish admissibility. Exercise numerical rather than lexical order, adjacent large integers, decimal spelling/signed-zero equality with distinct readback, fractional/overflow/rounding/nonfinite refusal, exact Unicode/trailing-space distinctions and first/later tuple component ordering. Equality-only qualification cannot enable ordered pages. Seed an invalid numeric leaf behind an otherwise excluding predicate: no planner evaluation-order assumption may replace safe domain admission. Native pagination tests use the exact same typed comparators for filter, ORDER BY, boundary and lookahead, with independently expected membership and no duplicate/lost rows. All vectors remain planned; no production comparator/native execution is claimed.

Binding admission resource tests exercise every proposed ceiling exactly and one beyond, including base64 expansion, repeated artifact references, many short mapping entries, cyclic/repeated value graph references, deep original JSON, colliding lookup hashes and long UTF-8 comparisons. Count real repeated work and peak simultaneous source/decoded/index/result buffers; cached identities cannot erase charges. Inject cancel/expiry between each transport/parse/artifact/nested-decode/correspondence/publication phase and retain reservations until actual containment. No accepted binding, SQL submission or partial result follows overflow. Enclosing compiled-artifact limits independently apply. Current numerical ceilings are unadopted proposals, so these remain implementation/qualification controls.

Property-home controls decode the exact admitted homeDefinition artifact under its registered schema/profile and verify baseline catalog json to binding props translation. Reject wrong object/edge discriminator, wrong physical table/column owner, wrong layout inventory, mismatched catalog IDs/memberName or enclosing value/presence pins, invented nested paths/SQL and retained fallback. Independently test absent member, present JSON null, empty string and present exact numeric/structured carriers; text extraction alone cannot collapse them. Unsupported row homes refuse before lowering. Shape checks and schema compilation do not establish native accessor/presence/codec behavior.

Compiled lookup binding controls preserve original JSON bytes and reject duplicate members, invalid scalars, wrong original digests and reformatted substitutes. Independently seed duplicate/conflicting qualified identities, same-name wrong-document owners, signed native overflow, missing accepted definitions, incomplete selected coverage, unsupported row homes and changed key-component order/comparison/null profiles. Each yields pre-compiler/pre-SQL refusal without fallback or partial result. Relationship endpoint/component conflicts and unknown execution obligations refuse complete admission even when schema-valid. Storage migration with unchanged catalog revision invalidates stale physical binding; a live historical binding requires separately proven retained stores and current authority. Cyclic self-digest/compiler-result evidence is rejected. These are planned semantic/native controls; schema registration proves no such behavior.

Prove direct exact lookup and metadata, without duplicating Weft compilation or assuming key-text order supports paging.

## Acceptance Criteria Test Mapping

Private binary projection controls compare exact arbitrary bytes including zero and high-bit values through the fixed lowercase hex carrier. Reject odd length, uppercase, prefix/whitespace, empty required context and claimed byte-length/digest substitution before original artifact admission. Independently account twofold encoded expansion plus decoded copies at and beyond carrier/ownership bounds. Native text projection does not license raw context disclosure; runtime/browser decoding and native framing remain planned evidence.

JSONB-text projection controls use CONTRACT-010's bounded catalog-directed decoder proposal. Independently compare nested exact numeric token strings, literal numeric-looking strings, present null, SQL NULL retained, absent keys, empty collections and opaque artifacts. A legacy numeric-only row cannot acquire an authored lexical-exact claim by returning its native rendering. Driver preparse through host JSON numbers, missing definition correspondence, skipped unknown members or opaque hash mismatch refuses full record admission. Actual native framing/decoder/resource evidence remains planned; UMF source round-trip verifies the casts only.

Integral projection controls independently expect decimal-text IDs/version/revision/root values beyond JavaScript safe-number precision, signed native int/smallint boundaries and explicit SQL NULL root states. Parameter predicates and native sort remain numeric; reject a driver returning rounded host numbers, padded/noncanonical text or values outside the original alias domain. These projection casts do not qualify JSONB, temporal or bytea decoding. Current UMF source preservation records the revised casts only; native execution and descriptor evidence remain planned.

Lookup-resource controls distinguish small public records from oversized private matched context and transport framing. Independently account both visible native match rows, repeated key comparisons, exact source/owner archives, codec copies and coordinator work. An oversized second row cannot prove uniqueness or become not_found. Missing framing/preallocation producers blocks this resource profile; actual scan/work/cancellation limits require native qualification. Fault containment and require original recovery rather than falsely contained resource-unavailable. The larger lookup carrier budget does not enlarge the selected key codec's own ceiling.

Native direct lookup controls target CONTRACT-004’s fixed observation draft. Same numeric object ID under another type must not match; a signed legacy type/key number preserves exact lookup mapping. For baseline keys, independently verify both join components and exact admitted C key equality. Inject incompatible duplicate identity observation and require refusal, not an arbitrary row. Hidden key/visible-object and visible-key/hidden-object cases expose no elevated existence probe. Large-key bucket profiles cannot use the baseline statement as a fallback; missing complete guard/bucket/namespace observation is unavailable, never not_found. Complete row decoding and fresh authority checks remain mandatory; these are planned native controls, separate from Weft compiled-query evidence.


| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-020-AC1 | `id_lookup_preserves_written_revision` | Exact properties/version/last-written revision returned; newer read-context catalog pin does not overwrite record revision | `@covers US-020-AC1` | Native integration | `tests/reads/lookup.test.ts`; record followed by nonmutating revision |
| US-020-AC2 | `key_lookup_returns_holder` | Independently expected canonical scalar key retrieves exact holding object under qualified role | `@covers US-020-AC2` | Native integration | Same file; Customer account-code fixture |
| US-020-AC3 | `complete_composite_key_finds_object` | Ordered complete components map to expected canonical bytes and retrieve correct object | `@covers US-020-AC3` | Native integration | Same file; escaped two-component fixture |
| US-020-AC4 | `incomplete_key_refuses` | Missing component yields defined invalid-request outcome before storage access; no null/absence substitution | `@covers US-020-AC4` | Contract | `tests/reads/lookup.test.ts`; pure request-validation fixture |

## Executable Proof

Future command `bun test tests/reads/lookup.test.ts` requires test/harness creation. Each test cites its criterion and pins catalog/value/key/read profile plus adapter/server. Missing qualified meaning blocks support.

## Data and Setup

Expected values/canonical bytes are authored independently of production codecs. Include exact large numbers, absent/null, wrong type ID, missing key and Unicode/injection-looking key strings. Observer compares returned metadata to canonical rows. Current head and last-written revision are observed separately.

## Edge Cases and Failure Modes

Lookup-binding vectors omit/reorder/duplicate components, substitute property/key pins, select unsupported null/comparison and forge canonical hashes; require invalid/refusal rather than false absence. Join key/object under one actual role/snapshot with concurrent key changes/deletion. Wrong-type ID and hidden key/object never disclose another record. Found requires exact record/context; not_found cannot carry hidden payload. Last-written revision remains distinct after definition-only acceptance. Failed reads have no writes/checkpoint effects.

Unknown/hidden records use not-found policy rather than empty object. Concurrent key movement/deletion cannot produce an inconsistent joined result under the qualified snapshot. Incompatible historical encoding refuses. Key null/family/collation policies remain shared gates; no inferred fallback.

## Build Handoff

Write red native/contract cases, reuse codecs/key validation, implement parameterized templates and qualify policy/context behavior. All four criteria block closeout. No source compiler, keyset order or multi-page snapshot guarantee follows from this story.

## Compiled mapping admission across key-profile migration

These planned cases exercise CONTRACT-007's mapping admission boundary. Truss owns execution admission and original artifact custody; Weft owns compilation and any required compiler ABI field. They do not extend the SQL language or authorize a second compiler. Use independently authored legacy and bucket fixtures with the same accepted catalog revision, distinct physical bindings, and an explicit migration barrier. Capture submitted SQL, parameter bytes and decoder selection through the host adapter; a refusal must issue no graph SQL.

| Planned case | Independently expected observation |
| --- | --- |
| `current_mapping_stale_after_same_catalog_migration` | A legacy compiled artifact succeeds before the switch, then refuses against current bucket storage despite the unchanged catalog revision. No false not-found result, implicit recompilation or SQL dispatch occurs. |
| `new_mapping_requires_explicit_compilation_and_admission` | Host obtains a separate Weft artifact against the qualified target mapping. Admission checks its original catalog, layout, value, backend and native key-binding obligations against the actual installation before dispatch; successful lookup returns the independently selected holder. |
| `compiled_evidence_substitution_refuses` | Replacing the mapping profile, parameter encoding, SQL, decoder or artifact reference while retaining the original compilation claim refuses. Rejection cannot be repaired by mutating the original artifact in place. |
| `held_old_snapshot_preserves_old_binding` | A separately qualified retained snapshot executes the original artifact against its original stores and definitions after migration. The observer establishes snapshot, store and encoding correspondence; current storage cannot supply any part of that read. |
| `old_snapshot_requires_current_authority` | Revoking the acting role after the historical context was retained produces the qualified authorization outcome. Retained definitions and compiled evidence confer no enduring disclosure permission. |
| `held_old_snapshot_missing_retention_refuses` | Missing retained stores, incompatible adapter/pooler semantics or missing original definitions refuses before SQL. The caller cannot reinterpret old bytes under the current encoder. |
| `migration_cleanup_respects_held_execution_context` | Cleanup cannot remove stores or evidence protected by the old execution context. After qualified release, cleanup follows its separate dependency protocol; releasing one context cannot release another. |
| `migration_racing_mapping_admission_is_coherent` | Barrier schedules switch before admission, between admission and dispatch, and during execution. Each qualified execution observes one complete binding/snapshot or refuses/retries under its selected procedure; it cannot join legacy key evidence with current bucket rows. |

For every case record the original compiler artifact and mapping selection, actual installation binding/configuration generation, native snapshot/authority observations, adapter/server versions, dispatched SQL count and exact result. A shape-valid profile or same catalog revision alone is not admission evidence. The exact Weft ABI representation of the physical/encoding/namespace comparison obligations remains an upstream review dependency. Until that is resolved, these are authored design controls and proposed native scenarios, not passing implementation evidence.

Same-transaction state controls perform a separately qualified pending catalog/configuration change, then submit an original compiled artifact or cached admission metadata. Re-observe actual binding/generation/acting role and refuse incompatible selection before SQL. A newly selected compatible pending state must retain pending durability and original accepted artifact custody; no committed readiness is inferred. Roll back the admin savepoint and require re-admission rather than assumed cached lock survival. SET ROLE between calls invalidates old authority metadata while preserving original recovery role provenance. Mixed-operation profile/ordering qualification remains a prerequisite distinct from isolated migration.

Compiled mapping/obligation admission cases under CONTRACT-007: matching digest with missing/wrong original binding custody; unregistered backend despite plausible identity; 0.8.0 model offered to observed 0.7.0 artifact profile; unknown or ambiguous obligation; host/backend owner substitution; compiler conformance label without native evidence. Every case refuses before native query preparation. Current mapping drift refuses ordinary execution; qualified original held mapping/snapshot succeeds only with original store/archive cleanup exclusion and fresh current authority. Retire its original store or revoke an original owner and require refusal, not hash-only acceptance. Exact shared IDs/encoding are pending Weft-owner review, so fixtures cannot locally invent a production ABI.

Lookup-wire check: `bun docs/helix/04-build/evidence/design-audit/check-direct-lookup.ts <Ajv Draft 2020-12 module path>` passes eleven request and eleven result shape cases. Duplicate components, forged encoding, unsupported native ID spelling, wrong current revision and wrong returned identity intentionally remain shape-valid for semantic/native refusal. Required native cases independently supply key order/definition/type/profile disagreements, hidden/absent rows, resource exhaustion during key and full-record decoding, snapshot expiry and lost observation. Assert exact unavailable/invalid or protected absence outcomes, no partial record/log/callback disclosure and no writes/checkpoint changes. Strict binding checks pass after adding resource to lookup unavailability; no native lookup implementation is thereby qualified.

## Compiled parameter and result bridge scenarios

These scenarios consume original Weft artifacts under the jointly selected bridge profile; they do not define another compile-response schema. Expected values are independently authored and retain exact lexical tokens. Artifact/pin/obligation refusal means zero compiled-query SQL submissions and zero returned result payload; qualified native admission/authority observation is counted separately and is not forbidden by that assertion. Capture original slot order/value/origin, actual adapter parameters and decoder/output evidence.

| Scenario | Required independent outcome |
| --- | --- |
| `original_slots_are_single_value_source` | Integer beyond host safe-number range, decimal with retained scale, empty string and quote-containing string arrive at the driver as exact original ordered slot text. No request-side replacement bag, renumbering or backend discriminator override is accepted |
| `unprepared_still_binds_values` | Selected prepared-disabled profile sends the same exact slot values through parameterized transport; injection-like string remains data and never changes SQL text. Compare both modes to independent native expected values, not only to each other |
| `slot_origin_and_domain_admission` | Wrong origin/binding custody, noncontiguous slot, malformed typed value or unsupported native domain refuses before compiled SQL. Shape-valid artifact tampering does not bypass original producer/evidence admission |
| `recursive_result_decoder_is_original` | Whole entity/list/map numeric leaves remain exact strings through the selected original type-directed decoder; missing, explicit native null, empty list and present values stay distinct. Unassessed native-null or recursive representation refuses rather than using generic host JSON decoding |
| `output_order_alias_and_nullability` | Actual column count/order/output aliases and empty-aggregate nullability agree with the admitted original artifact and independent result expectations. Mismatch cannot return a successful partial or silently renamed result |
| `resource_refusal_has_no_partial_result` | Exact selected preallocation/result byte/row/native-buffer limits contain execution and refuse the complete result without an executed payload. Unknown native cancellation/termination uses outer execution recovery, not a successful resource refusal |

Record each actual original artifact/profile/version/native deployment and the complete obligations discharged. A compiler's candidate/conformance label does not prove native correctness. Weft's ordered slot limit remains compiler-owned and separate from Truss group operation count; parameter/result resource limits and actual transport/native representation belong to the selected Truss bridge profile. These schedules remain not_run until original shared mapping/obligation/decoder profiles and actual runtime adapters are admitted.

Truss compiled wrapper check: `bun docs/helix/04-build/evidence/design-audit/check-compiled-execution.ts <Ajv Draft 2020-12 module path>` passes 11 request/result cases. Replacement parameters/arbitrary SQL, refusal with result, execution without observation and commit uncertainty as normal refusal reject. Wrong digest, forged observation and unknown nested ABI deliberately pass wrapper shape and must refuse through original artifact/digest/owner/native admission. This command tests no compiler schema or native execution.

Artifact provenance schedules submit schema-valid authored compile responses with copied compiler/backend/conformance pins, modified SQL/value/decoder under refreshed digest, and original response with substituted model/binding archives. Every case lacks original capture correspondence and refuses before compiled-query submission. A valid host-invoked original Weft response may pass capture admission but still fails stale mapping/current authority/native obligation gates independently. Restart/offline replay must use its separately qualified original archive profile; a process-custody fixture proves no offline authenticity. Execution refusal cannot invoke the compiler or patch original bytes.


## Synthesized composition mapping review controls

Planned joint-owner cases distinguish a supported authored Relationship from a Truss-derived composition_field with the same rendered identity/native ID. Unregistered composition logical capability refuses without compiler model fabrication or native query execution. A reviewed mapping must carry original qualified owner Record/Field provenance and exact category/derivation/definition/endpoint pins through the existing registered binding; no top-level Truss ABI field or SQL patch is permitted.

After mapping adoption, compare independently expected traversal results/cardinality against native storage, including Field/Record in different modules, changed target definitions, inverse access and hidden endpoints. A stale original compiled artifact refuses after an incompatible definition/binding change; execution never recompiles it implicitly. UMF record-type author receipt alone cannot establish owned lifecycle or current disclosure. These are pending review cases, not current Weft capability or passing native tests.


Compiled JSON property-address controls use object-member keys "-1", "0" and a native int extreme, with distinct absent/JSON-null/present states. A typed integer array operator is the wrong-access negative control; an array/scalar props root must fail stored-domain admission instead of reporting absence. Require exact native range and property owner/pin admission before member addressing. Verify returned compiler parameter type/value/order remain unchanged; SQL/operator/cast repair belongs to the original registered Weft backend, never the Truss bridge. A backend lacking this selected mapping/domain capability remains unavailable until owner adoption. Native cases are planned; official operator documentation is substrate evidence only.

Single-statement bucket-read controls require a read-only data transaction, zero guard mutations and exact namespace/key bytea comparison despite intentional routing-digest collisions. Independently expect distinct full-byte keys and domains, signed mapped IDs, typed object join and complete original match/context correspondence. A duplicate visible full match refuses; a stale or missing selected layout/projection/profile is unavailable before lookup, not absent. Native query/transport work remains bounded separately; no multi-statement bucket observation or reservation probe is licensed by this candidate. Writer collision/snapshot enforcement remains its own guard protocol.

Private bucket context controls inspect effective raw column grants and public/helper execution paths under CONTRACT-005. An object-visible caller lacking complete required context-owner authority receives no raw context, candidate count, decoder detail or public record bypass. The protected read owner cannot inherit integrity-observer membership or call its hidden-scope helpers. Original acting caller differs from definer owner; role/caller swaps and unqualified context-returning subhelpers invalidate the profile. The public DirectRecord excludes matched context/digests; tracing/callback controls independently verify no disclosure. These are planned native privilege/policy tests, not a function-name qualification.

Native metadata controls vary DateStyle and TimeZone while preserving the original data transaction and compare admitted native instants with microsecond precision. Reject driver Date rounding, stale/missing format observations, unregistered calendar/range/special families and host connection/role swaps. Extended-year/era and infinity expectations must be explicitly selected, not normalized to null or a current date. Authored timestamp offset/spelling vectors remain separate and cannot pass from native metadata rendering. The read changes no caller session setting; source preservation does not qualify temporal parsing or current native formatting.


## Direct decoder sequence controls (planned)

Exercise CONTRACT-004 D0–D7 through the actual selected bounded transport and original executor, with independent expected values and a publication spy. Missing/extra/duplicate aliases and wrong native format refuse before value interpretation. A text-projected bigint carries its pinned positive domain; an arbitrary text alias cannot acquire that meaning. Verify descriptor replacement, wrong original executor and unqualified driver coercion do not reach dispatch/publication.

Split every relevant field boundary, UTF-8 sequence, JSON escape, numeric token and SQL NULL framing marker across native chunks. Exact content must survive supported splits; truncated field/result and zero rows without successful complete native termination are unavailable/observation, never not_found. Charge the producer's maximum next allocation before reception and separately verify simultaneous raw/decoded/output copies. Fault exactly-at/one-over row/result/owned limits; unknown termination retains CONTRACT-007 recovery rather than claiming contained resource failure. These transport controls require actual producer evidence, not a mock that allocates all input first.

A valid first lookup row followed by a duplicate, malformed or oversized second row must publish nothing. Test full private bucket match/context mismatch with an otherwise valid public object. Trace/callback inspection must show no context, digest, hidden owner/value or candidate count. Compare original written revision independently from readCatalogRevision. Cancellation/disposal/context replacement/authority expiration between complete private serialization and D7 wins publication arbitration; no public record, host commit or automatic query retry occurs.


Direct props-member controls use canonical `-2147483648`, `0` and `2147483647` with independently pinned owner/definition meanings. Reject `01`, `+1`, `-0`, whitespace, decimals/exponents and out-of-range spellings instead of aliasing a valid property. An ID valid under another record owner/category and a missing original retired-definition mapping refuse complete observation. Decode JSON escapes before duplicate-key checks; no integer array operator or host-number coercion is allowed. Retained names `1`, `01`, case-distinct/Unicode-distinct names and `__proto__` remain exact separate names in inert storage, without prototype mutation or migration into props. Count all members and nested decoder work even when a convenience caller would not select them. These are planned actual decoder/native-mapping controls; legacy discarded lexical source is not recovered by passing them.


## Recursive result parity across selected homes

For each independently admitted JSONB and complete row-tree profile, run direct lookup and compiled whole-entity projection against independently authored semantic fixtures. Use the same authored entity/value descriptors and independently expected presence/value tree, while preserving each home's distinct original layout and decoder pins. Compare both paths independently to expectations before comparing them to each other: two implementations sharing an error cannot establish conformance. Qualification of one home does not enable the other or authorize a fallback.

Required fixtures combine nested object, ordered sequence and map members; adjacent integers beyond host safe-number precision; decimal spellings with sign/scale/exponent under the selected exact carrier; numeric-looking literal strings; missing optional members; explicit null; empty objects/maps/lists; repeated equal sequence items and opaque extension content. Include descriptor variants distinguishing absent from null and scalar from container, plus depth/resource boundary cases. Preserve list order and multiplicity; use the selected map/property identity semantics rather than assuming an ordering shared with sequences. Each selected capability needs its own observed exact expected output; unsupported meanings refuse explicitly without silently narrowing whole-entity projection.

Negative fixtures independently corrupt native numeric/presence carriers, substitute a wrong descriptor/decoder pin, add orphan or unreachable nodes, connect children to a scalar and duplicate a property identity. Require complete original graph validation before successful record publication, even when the corrupt subtree is outside a convenient selected leaf. Exercise disconnected cycles without indefinite traversal, repeated-node/resource accounting and loss of original native completion mid-result. Direct and compiled error/disclosure expectations follow their governing contracts; no shared generic host JSON parser or compiler-owned traversal is copied into Truss. Weft owns compiled recursive decoding; Truss owns its direct decoder, mapping admission and independent parity harness. All cases remain planned until exact selected profile/producer and native evidence exist.


Native descriptor parity controls prepare a text-looking descriptor but independently select/observe a different actual result format; no preparation-time zero can qualify text decoding. Exercise equal aliases with differing type OID/modifier, computed-expression zero provenance, missing descriptor for a row-returning template, legitimate non-row completion, empty bytes versus native null sentinel and truncated field lengths. Validate correspondence to the original Weft artifact or direct descriptor independently before semantic decoding. Actual driver capture/native events and bounds remain unqualified; public compiler/result ABI is unchanged.

### Original comparator admission and result-domain integration

These supplementary compiled-read cases implement CONTRACT-010's current Weft handoff without adding a new public Truss query surface. Independently author original query/type/profile inputs and expected operation requirements; do not derive expected registrations from the production collector.

| Planned case | Required observation |
| --- | --- |
| `projection_requires_codec_without_comparator` | A plain projection needs exact leaf/read-context admission but no fabricated equality/order/key/SUM registration. Missing codec still refuses. |
| `equality_does_not_authorize_ordering` | An equality-only registered field supports its qualified equality use; adding order/page/cursor use requires independently registered ordering and applicable key semantics. Refusal occurs before lowering or native preparation. |
| `resolved_identity_and_facets_cannot_substitute` | Equal display names, foreign owner/type, narrowed integer width, changed decimal facets or foreign original bytes cannot reuse another field's selection. Complete authored identities remain distinct. |
| `nullable_candidate_is_explicitly_unsupported` | Current Weft nullable-comparator admission refuses its unsupported use while retaining original null/presence metadata. Removing nullable metadata or substituting a sentinel is a failing control. A future selected nullable profile needs its own original corpus. |
| `sum_result_domain_is_independent` | Under an explicitly selected numeric aggregate profile, test empty input, admitted NULL handling, cancellation to mathematical zero, exact large totals, result-domain boundaries and overflow/precision refusal. Operand validity alone cannot prove the result domain or decoder. String/boolean SUM remains unsupported. |
| `recursive_scalar_codec_membership_is_complete` | Every required scalar node has its exact original leaf selection; missing/unrelated codecs or foreign representation/profile bytes refuse. Projection and comparison claims remain separate. |

The independently selected aggregate profile supplies concrete expected empty/NULL and result-type outcomes; these tests cannot choose that policy by accepting whatever the server returns. Retain original requirement set, selected registry evidence, compiler artifact or pre-lowering refusal, native dispatch count and exact raw/decoded result observations. Current Weft source records static tests, not integrated lowering or native success. Until original profiles and bridge integration are selected, these cases are planned/not_run and cannot close US-020 or full compiler conformance.

Original property admission integration cases pair complete UMF/frontend closure with independently selected storage graphs: omitted recursive member, substituted owning source document, same property index in a foreign binding, missing record-member presence/leaf codec, unrelated native inventory and object/edge association substitution all refuse. A registered native selector needs original inventory correspondence, not merely matching names. Preserve full inputs and prove zero native preparation on unsupported extra obligations. Positive real-definition compilation requires the owner-integrated wrapper path and actual Truss obligation producers; synthetic candidate/native corpus passes cannot substitute.

### Root prerequisite custody and native cut schedules

These cases refine the existing row-home corruption controls for CONTRACT-007's separate structural-prerequisite handoff. Use independently authored object and edge owner bags, including duplicate owner occurrences, and seed corrupt states through the isolated qualification authority rather than weakening production writer privileges. Retain original pre-state, emitted prerequisite and logical artifact bytes, complete owner inventory, actual transaction/authority/cut observations, submitted statement order and publication count. Expected storage facts must come from the fixture specification, not from the predicate being tested.

| Planned case | Independent expectation |
| --- | --- |
| `root_prerequisite_excluded_owner` | A malformed owner excluded by user predicate, page boundary or LIMIT still refuses when inside the original obligation scope; filtering it away cannot produce successful partial records. |
| `root_prerequisite_optional_absence` | Qualified optional state absence preserves each duplicate owner occurrence; the same absence under required presence refuses through its separate obligation. |
| `root_prerequisite_incomplete_visibility` | Hidden state/root/payload or incomplete observation cannot qualify absence/integrity; no elevated probe discloses hidden payload. |
| `root_prerequisite_payload_semantics` | Null/container with extra scalar payload and scalar with missing payload refuse despite root-count success; complete subtree/source/codec admission remains necessary. |
| `root_prerequisite_between_statements` | Pause after a successful prerequisite and before logical dispatch. Inject a conflicting change from another transaction. The selected native guarantee must exclude the change, preserve one qualified cut, or refuse/re-admit; success combining the earlier proof with later malformed storage is forbidden. Same-transaction identity alone is insufficient. |
| `root_prerequisite_local_write_or_role_change` | Intervening caller write, role change or savepoint rollback invalidates affected cached proof under the selected procedure; original recovery survives, with no silent SQL patch or implicit compiler invocation. |
| `root_prerequisite_alias_collision` | Each reserved join/probe alias collision refuses before altering original parameter slots; a subsequent valid compile has exactly its independently expected slot positions. |
| `root_prerequisite_failed_observation` | Missing completion, cancellation, unknown outcome or bounded-resource failure produces no public record; containment/recovery follows the original executor rather than treating missing rows as absence. |

For the between-statements schedule, record whether the actual qualified profile uses a protected invariant, retained coherent snapshot or reviewed exclusion; do not generate an isolation guarantee from the test's expected result. Run a deliberate unqualified independently changing-cut control and require admission refusal, rather than advertising that deployment as supported. The current Weft source emitter and owner component tests are not these native outcomes. All cases remain planned until original profile selection and independent native execution evidence exist.

## Decoder metadata and occurrence custody cases

The following cases are planned against the selected original public Weft bridge. Current internal metadata source is prerequisite evidence, not an adopted ABI. Fixtures author expected values independently of the decoder layout and retain original compiler inputs/artifact, binding, raw positional observations, obligations, resource accounting and final publication disposition.

| Case | Independent perturbation | Required observation |
| --- | --- | --- |
| Q04-L01 | Same owning property in two self-join scans, with different values and one absent required member | Independent aliases/slots and per-occurrence validation; entire result refuses, with no good-side partial publication |
| Q04-L02 | Literal stored names containing `01`, dots, brackets and quotes | Exact original member lookup; no path splitting, numeric index conversion or display-name substitution |
| Q04-L03 | Finite cyclic metadata and two different candidate runtime subtrees using the same graph node | Bounded per-value traversal; metadata reuse cannot suppress validation or resource charges |
| Q04-L04 | Equal-shaped replacement codec/presence definition from another original artifact | Original custody substitution refuses before decoder invocation/publication |
| Q04-L05 | Optional absence, required absence, explicit null, empty scalar and missing row root | Original distinct presence/null/home meanings; JSONB extraction is not reused for native row decoding |
| Q04-L06 | Reorder duplicate-named columns or exchange self-join slot assignments | Complete ordered descriptor/artifact correspondence refuses; name-keyed reconstruction cannot pass |
| Q04-L07 | Last occurrence exceeds remaining decode budget after earlier occurrences succeed | One enclosing ledger includes every occurrence and simultaneous buffers; no partial success or fresh per-occurrence budget |
| Q04-L08 | Decoder throws after confirmed SQL execution, or native completion remains unknown | Preserve original containment/recovery and caller ownership; no implicit retry/recompile/commit |
| Q04-L09 | Decoder returns complete values but an original owner obligation or current authority is invalid | No publication; attached metadata/result shape cannot satisfy missing pre-query authority/obligations |

Implement through the actual selected original decoder entrypoint once available. Test-only alternate decoder/layout serialization cannot qualify the production bridge. Capture owner-side component evidence separately from Truss's actual adapter/native/result qualification.

## Original expression parameter custody

Planned bridge controls compile an admitted expression with multiple original property/literal slots, then deliberately refuse a later unregistered native operator or unsupported literal domain. No partial parameter collection or SQL artifact may become an admitted execution request. Existing slots in the enclosing compilation retain exact positions/origins/bytes; successful subsequent compilation cannot inherit failed-attempt slots. Independently check native meanings against the selected original backend, not the fixed synthetic candidate's JSONB casts.

Use asymmetric operands and differently named self-join owners to detect operand/owner substitution. Preserve beyond-safe-number integers, decimal lexical carriers and literal member names without host conversion. Render traversal order cannot authorize SQL side effects or promise runtime short-circuit order; selected operator procedure meanings must qualify these separately. Whole-call budgets include staging copies, pending traversal, rendered SQL and original slots before allocation, not only the final parameter count. These native/resource tests remain planned until original registered backend/bridge producer selection.

## Original owner-source and comparator coverage

Planned original-backend cases include a fieldless COUNT with independently admitted Record mapping; a self-join with equal owning Record but distinct occurrence source parameters; two properties whose physical owner mappings/catalog IDs disagree; and a selected expression whose second exact occurrence access is missing after first-side parameter staging. Refuse missing/mismatched mappings without fabricated Field requests, borrowed aliases or leaked slots. A discriminator predicate cannot discharge independent malformed-owner/property integrity obligations.

Programmatic lexicographic comparison controls require both sides' full original owner-qualified equality/order admission, exact nonempty arity and logical types. Missing right-side admission, unequal lengths and family-only type substitution refuse; these controls add no SQL syntax support claim. Independently verify grouping/filter/source assembly against the original compiler artifact, keeping V01 relational and V02 application/native evidence separate. Original native backend/adapter/resource/publication qualification remains required.

### Combined Record/property preparation acceptance

These planned controls consume the owner-integrated preparation boundary observed at Weft eed3886; they do not expose internal Rust structs as a new Truss ABI. Original source correspondence is recorded in the [committed refresh receipt](../../04-build/evidence/design-audit/weft-combined-record-source-refresh.json). Each test starts with an independently authored existing parameter ledger whose ordered origins, domains and exact bytes are preserved for comparison, including a text value that resembles SQL and an integral token beyond host safe-number precision. Parameter staging and compilation are separate from native execution.

| Case | Independently arranged input | Required observation |
| --- | --- | --- |
| Q04-P01 | One admitted Record, zero property reads, fieldless count | Original Record source survives preparation; no invented property integrity check or Field admission. Native count uses the original owner discriminator and independently expected empty/two-row membership. |
| Q04-P02 | Two original Record scans, second admission omitted | Complete preparation refuses; existing parameter ledger is byte-for-byte unchanged and no executable artifact reaches the Truss executor. |
| Q04-P03 | One scan with two properties from its original Record | Both accesses use that occurrence's original source; no second discriminator slot is introduced for the second property. Do not hardcode absolute slot numbers; compare original parameter origins and references. |
| Q04-P04 | Two self-join occurrences of the same Record, each with two properties | Two distinct source occurrences remain; each pair reuses its own source. Independent asymmetric rows detect exchanged aliases or source slots; result multiplicity remains the expected bag. |
| Q04-P05 | Correct Record source but a property pinned to a different model, owner or binding cut | Full preparation refuses before execution; matching rendered names and numeric catalog IDs cannot repair original provenance. Existing slots remain unchanged. |
| Q04-P06 | Both sources staged, then a required comparator admission fails | No staged source/property/literal slot leaks. A later independent successful preparation starts from the original ledger, with no gaps or reused failed-attempt origins. No query SQL is submitted for the refused attempt. |
| Q04-P07 | Fieldless query over a Record that also has malformed stored properties | Do not infer complete integrity from the absence of selected properties. Discharge every obligation in the original admitted artifact/profile; refuse unsupported required coverage rather than manufacturing property checks or silently reducing the profile. |

The success oracle combines independently authored source occurrence/parameter membership with logical expected records, not equality between two compiler-produced SQL strings. Native execution additionally requires the selected complete visibility, same-cut, raw transport/completion, finite resource and result-decoder procedures. Synthetic owner tests do not close these Truss acceptance cases. All Q04-P cases remain not_run until the selected joint artifact and host profile exist.

## Owner-wide preflight result admission

The [fifteen original raw-result vectors](owner-preflight-result-vectors.proposal.json) use the existing StatementResult carrier with one `violations` cell, original SELECT completion metadata and an independently arranged test context. Zero admits only structural integrity; positive exact int8 text refuses without host number conversion. Missing/extra rows, wrong aliases, SQL NULL, noncanonical counts and inconsistent native completion metadata refuse. Zero from an incomplete RLS view, missing original check, exhausted account or unknown completion cannot permit query execution/publication. Test setup labels are not credentials or serialized authority.

Native harness qualification must execute the original artifact's check SQL with unchanged parameters and selected raw descriptor/encoding. Truss cannot append casts, filters or limits to make transport convenient. Counts and malformed-owner diagnostics remain private admitted evidence until complete current disclosure authority; ordinary result/logging/progress callbacks receive no provisional values. Same-cut/current-authority and independent presence/codec/domain/full-tree obligations remain required even when every structural count is zero. Lost native completion follows original recovery, not a synthetic pre-native refusal or transparent retry.

### Original projection metadata qualification controls

Planned joint cases retain two self-join output positions with the same Field identity but different aliases and asymmetric values; swap raw column positions/names or substitute one original source identity and refuse publication. Required exact integer/decimal text metadata does not admit rounded native values. Optional/nullable/compound Value metadata must receive its selected original carrier and absence/null procedure; native SQL NULL cannot stand in for semantic null merely because the logical descriptor is nullable. Independently qualify nullable aggregate results, exact precision/scale and their native descriptor domains; synthetic string projection headers cannot qualify them. Missing projected comparator admission or altered resolved Field type refuses before any executable artifact is admitted. These cases consume existing Weft Column metadata and add no public decoder wire; native conversion and all Q03/Q04 obligations remain prerequisites.


### Prepared read and private row custody integration controls

The selected Weft/Truss bridge must preserve physical preflight obligations for fields used only in predicates, joins, grouping or aggregates. Corrupt a nonprojected owned field and require refusal before publication; unrelated-owner corruption remains separately scoped. Change the ordered parameter inventory or original binding after preparation and require refusal without callback effects or committed parameter additions.

For native row decoding, independently supply NULL, empty text/bytes, false, Unicode/trailing spaces, uint64, negative-zero tokens and a numeric/token mismatch. Compare all eight private custody positions and native descriptors against original expected inputs. Preserve native numeric text and lexical token separately; observable mismatch must reach semantic refusal, not become successful normalization. Swapped columns, omitted source bytes, native NULL converted to empty and private aliases substituted for public result metadata fail. These planned controls extend owner synthetic custody evidence to Truss's actual selected storage/codec/host bridge; no native qualification follows from the source refresh.


The [twelve independent scalar custody vectors](private-scalar-custody-vectors.proposal.json) specify scalar-stage positive/refusal outcomes, including uint64, lexical negative zero, hidden conflicting payload and a binary family unavailable through the eight-column bridge. Symbolic codec bytes must be replaced by explicitly reviewed fixture registrations, retaining each original expected meaning. Positive cases require full-slot and structural preflight; they are not complete-record publication expectations. Actual decoder execution remains not_run.

The [fixture audit](../../04-build/evidence/design-audit/private-scalar-custody-vectors-audit.json) pins the original vector file and checks authored UTF-8 source bytes, uint64 maximum, zero mathematical versus lexical facts, mismatch and distinct NULL/empty/hidden-payload cases. Reproduce with `python3 docs/helix/04-build/evidence/design-audit/check-private-scalar-custody-vectors.py`; normal and optimized Python executions pass. This audits fixture facts only and executes no decoder or native deployment.


Each SC vector now records its independent physical-stage expectation separately from complete scalar semantic admission. SC06 and SC12 intentionally pass eight-cell physical admission while failing numeric correspondence and complete hidden-slot preflight respectively. SC10 returns only physical absence; SC11 never enters an invented binary Family dispatch. No scalar-stage success permits complete result publication. Execute these checkpoints separately through the selected Weft helper and Truss bridge; shared output-derived expectations cannot test the boundary.


## Full-slot direct-reader native matrix FS01–FS08

Execute the fixed CONTRACT-010 full-scalar source unchanged under its fifteen-position manifest. Each case supplies independently authored original state/node/codec/source facts and a selected complete owner/tree/read/transport profile. These tests extend direct-reader coverage, not Weft's eight-cell ABI. Every family must independently qualify its source grammar/domain before logical acceptance.

| Case | Independent native setup | Required observation and refusal control |
| --- | --- | --- |
| FS01 | Binary payload with exact bytes `00 ff 5c`, then a present zero-length binary payload | Observe `00ff5c` and empty hex respectively with every unused slot native NULL; neither can become absent or UTF-8 text. Missing required binary payload refuses. |
| FS02 | Temporal lexical source with an authored offset and a separately qualified equivalent native instant | Retain exact temporal spelling and independently expected instant/settings; equivalent instants never replace lexical source. Changed TimeZone/DateStyle or instant mismatch requires explicit selected interpretation or refusal. |
| FS03 | Selected lexical-only temporal family with no admitted instant projection | Preserve temporal text and native NULL instant; reading lexical meaning cannot grant instant comparison/query support. Date-only or offsetless meaning cannot be silently coerced into the selected instant family. |
| FS04 | Exact recognized opaque bytes, including zero-length content when its selected definition permits it | Preserve full bytes/source/codec; no UTF-8 conversion, evaluation or comparator registration follows. Arbitrary binary content lacking a permitted public wire must remain unavailable for that publication. |
| FS05 | Present scalar with a conflicting non-NULL unused binary, temporal or opaque slot | Full-slot validation refuses even when the eight-cell projection appears valid. Exercise each hidden slot independently. |
| FS06 | Zero rows, then a corrupt duplicate original state/node identity | Zero requires complete independent node/presence classification. Two observed rows refuse before any winner/value publication; never reduce LIMIT to one. Ordinary selected constraints must independently prevent the duplicate setup in valid installations. |
| FS07 | Correct payload under foreign state/node or codec/source custody | Match complete original identities and bytes; same value, name or digest cannot repair the mismatch. Unauthorized context refuses disclosure before private payload diagnostics. |
| FS08 | Large carrier beyond selected pre-materialization allowance, partial row or lost SELECT completion | Refuse or preserve original unresolved recovery before logical/public success. A host decoder's post-allocation limit cannot qualify the transport bound; valid surviving cells do not complete the row. |

Native corruption setup uses a separately isolated conformance installation, with its invalidity explicitly retained; it cannot be advertised as the production profile. After a contained decode failure, independent observations verify source/graph state unchanged and cumulative processing work still charged. Actual fixtures, selected codecs/temporal domains, raw descriptor producer and native driver remain prerequisites; FS01–FS08 are not_run.


### Complete-tree two-stream controls

Use independently authored tree sets with an unreachable node, orphan scalar row, missing scalar payload, duplicate full identity, payload on a null/container node, cycle and cross-state parent respectively. Require full-set refusal even where the root subtree decodes successfully. Compare zero-scalar valid container/null trees with invalid zero-node present state; no scalar stream alone determines absence. Interleave a native mutation between the two SELECTs and require selected coherent-cut/exclusion behavior, not mixed successful reconstruction. Lose or truncate either stream and preserve original recovery/refusal with no partial publication. Native row collection order must not reorder logical sequence ordinals, literal map keys or qualified record identities. Complete visibility/resource/transport/descriptor profiles and actual decoder remain not_run prerequisites.


The [thirteen independent tree-correlation vectors](private-tree-correlation-vectors.proposal.json) fix structural expectations for the two-stream boundary, including count-preserving duplicate substitution, orphan/missing payloads, unreachable/cyclic nodes, ordinal gaps, null-node payload and adjacent exact IDs beyond JavaScript safe integer. TC01/TC09/TC11/TC12 admit structure only; no vector grants codec/source or whole-record publication. Map these symbolic original facts to the selected complete native fixture before execution. The candidate correlator may not generate its own expected membership or overwrite duplicates while building a map.


Selected compiled-row integration controls substitute another valid property/home binding with equal display name or scalar type, alter original root codec bytes and replace original presence metadata while keeping returned cells unchanged. Require original coupling/custody refusal; cells cannot repair missing admission. A physical NoScalar result must retain original presence semantics until separately interpreted. Releasing or invalidating the originating property/context before host decoding must not leave borrowed bytes as a reusable publication credential. Positive original-property/native-row fixtures require complete Truss source/domain/visibility/host profiles beyond owner synthetic two-case evidence; tests remain not_run.


TC06 now isolates the disconnected cycle using container nodes with valid local sequence slots and no scalar payloads, avoiding an unrelated scalar-parent/payload failure. TC11/TC12 positively admit null and empty-sequence root structure with zero scalar rows; TC13 refuses a present state with zero nodes. Complete original definition/source/presence validation remains required after these structural outcomes. All thirteen vectors remain planned, with no logical publication permitted from structure alone.


Direct-tree identity controls independently send canonical native boundary values and malformed carriers to the selected raw decoder: positive int8 `9223372036854775807`, one above that bound, signed int32 extrema, `+1`, `01`, `-0`, whitespace, `1e0`, `1.0`, zero storage identity and NULL parent. Native-range success still needs original owner/mapping/slot semantics. Adjacent `9007199254740992`/`9007199254740993` must remain distinct; uint64 maximum may be an admitted scalar value but must refuse as a storage ID. Overlong decimal text refuses before exact-integer allocation. Cases remain planned and do not qualify descriptors or original disclosure.


### Inert literal-map reconstruction controls

Under an admitted original map-of-string definition, independently author seven distinct keys: empty string, `__proto__`, `constructor`, `toString`, `hasOwnProperty`, U+00E9 and U+0065 U+0301. Use distinct marker values for every entry. Complete native tree decoding must preserve all seven exact key/value pairs without normalization, inherited-member lookup or host prototype mutation. Keys resembling native signed property IDs remain map keys, not authored property references.

Insert a duplicate exact literal key and require full-key refusal; equal routing hashes for different full keys remain distinct. Reverse native collection IDs while preserving actual map slots and require the selected original map serialization/order semantics rather than invented ID order. Reuse the same keys as retained unknown names and verify their separate carrier without changing map/record meaning. Source/profile/authority and containing resource bounds remain prerequisites, and all cases are planned. Native content cannot supply getters, coercion functions or document-selected code during decoding/serialization.


### Whole-record home membership controls

Under a selected complete mixed-home fixture, add an extra original-owner property state outside the decoder's requested field list, omit a required state's observation, duplicate a full owner/property state and place a defined property in a forbidden props/row shadow pair. Complete direct-record decoding must refuse each discrepancy rather than return the surviving fields. An optional absent property is a positive control only with complete owner-state visibility. RLS-hide the extra state and require completeness refusal; empty selected-property lookups cannot prove no extras.

Keep prior definition/home/source bytes for a property no longer in the active field list: require explicit retained/migration meaning or unavailable interpretation, never guessed retained names or automatic removal. Independently compare the full original observed/expected membership and all preserved unknown content. Hidden-owner errors/logs/callbacks must not reveal extra state identity/counts/private bytes before disclosure admission. Cases remain planned and require the actual complete-owner enumeration/native composition.


### Equal NoScalar cells with different original contexts

Independently arrange the same eight cells (`false` followed by seven native NULLs) under five distinct original per-occurrence contexts: absent optional state, present permitted null root, present scalar root with missing payload, present state with missing root, and present container root. The physical helper's identical NoScalar result is expected; the complete bridge must classify them differently using actual state/root/kind/source and original presence evidence. Required-but-absent state is a separate refusal control.

Qualified optional absence and present permitted null need their selected original logical bridge, preserving bag multiplicity. Missing scalar/root refuses integrity. A container requires complete-tree interpretation and must not become a scalar NULL. Remove the contextual observation, replace it with caller booleans or swap two self-join occurrences' state evidence: interpretation refuses rather than borrowing another row's valid presence facts. Owner-wide zero violation counts alone cannot supply missing per-row state/root observations. Current owner native NoScalar fixture is physical custody evidence, not a passing required-string semantic result. All cases remain not_run.


The [eight NoScalar context vectors](compiled-noscalar-context-vectors.proposal.json) retain one common eight-cell input and independently specify optional absence, present null, missing payload/root, compound root, required absence, caller flags and foreign occurrence. NP01/NP02 are conditional complete-bridge expectations, not passing current helper/publication cases. NP05 requires the selected tree bridge: current `admit_property` refuses compound roots before raw scalar admission, so the test must not invent a scalar family to force it through. Counts/context labels are fixture oracle facts, never serialized native credentials. All vectors remain planned.


#### Original record-field correlation controls

Plan a nested record fixture with two same-display-name fields having different original qualified identities and distinct values. Where the selected original record definition admits this identity shape, the direct exact field-entry carrier must preserve both identities. The committed Weft recursive name-addressed object encoder instead rejects duplicate authored names with WFT-CAPABILITY before SQL; independently expect that scoped refusal, not a successful object projection. Neither route may invent unique names or overwrite a field. Allocate child node IDs in reverse authored order; independently expect output field order from the original definition. Exercise duplicate full field identities, an unmatched child identity, missing required versus missing optional fields, nullable versus nonnullable present-null children, and an unavailable original identity encoder. Include a forced routing collision with different complete identity bytes and a public output-name collision; the former must retain both distinct fields and the latter must refuse before publication. An explicitly admitted retained-content profile gets a separate positive case; unmatched fields without that profile must never disappear. Observe whole-value refusal and bounded inventory/output accounting, not just scalar admission. These are planned native/consumer cases, not executed qualification.


For the selected Weft record-identity bridge, add independent original qualified-identity byte witnesses with reordered JSON members, Unicode and escaping. Compare actual Truss storage bytes to the pinned compiler parameter bytes, retaining full expected bytes outside either implementation. Equivalent parsed objects with differing serialization must refuse a mismatched selected encoding rather than silently match or rename the field. Exact identity profile selection precedes the positive test; this is a bridge-specific requirement, not a new UMF portable encoding.


For compiled recursive output, select a record authored in field order `z`, then `a`, with original source carriers and independent full identity/value expectations. Compare the separately declared name-addressed SQL result and exact ordered Truss carrier without treating JSONB object iteration as authored order. Include original lexical numeric source distinct from equal native numeric meaning and admitted retained unknown content. A matching projected value alone must not certify exact whole-value/source capability; missing bridge facts produce explicit refusal of that requested capability. The original independent expected carrier remains separate from both compiler output and Truss reconstruction.


#### Compiled exact whole-value occurrence bridge controls

Plan a self-join selecting the same original nested property twice from distinct scan occurrences, plus duplicate owner rows whose bag multiplicity must survive. Independently expect each full ordered value and original owner/field context. Swap the two occurrence contexts, supply a same-number foreign typed owner, change catalog/home between staged result and tree observation, and attempt a follow-up read on another executor transaction. All must refuse before publication. For a complete staged result, corrupt the final occurrence's tree and verify that no earlier occurrence was released. Add computed/aggregate output lacking an admitted original observation derivation and an over-budget repeated-owner batch; neither can fall back to business-key lookup, reset the account or silently collapse duplicate result rows. Positive shared-value reuse retains multiplicity and original custody while releasing only actually transferred buffers. Native barriers, selected occurrence bridge and independent expected values remain prerequisites to execution.


[FI01–FI04 byte witnesses](record-field-identity-byte-vectors.proposal.json) supply explicit UTF-8 hex for identical identity text, reordered equivalent JSON members, literal versus escaped Unicode, and a changed revision. Fixture text order is an input, not a universal encoding selection or an observed compiler output. Full byte comparison differs from parsed identity equality in FI02/FI03. All scalar/identity-only publication flags remain false: actual original producer/consumer correspondence, value admission and complete custody are still required. Fixture JSON/UTF-8 transcription was checked independently of the Truss decoder and Weft compiler.


#### Complete-tree composed resource controls

Under the selected 64-submission direct-lookup candidate, supply a completely observed owner with 32 present row-home states. Independently expect refusal of the one-header-plus-64-stream plan, even before additional authority/containment submissions; reserve before beginning its unfinishable stream plan. A smaller positive fixture derives its full allowed count including all actual producer/containment paths, rather than assuming 31 states always fit. Include hex inputs whose native encoded sizes fit individually but whose input/decoded/table/output simultaneous ownership exceeds the containing peak, and repeated released batches whose cumulative work exceeds the original account. Observe no partial publication, no per-property counter reset and correct original containment. Native/host allocation producers remain prerequisites; byte arithmetic is a lower-bound witness, not heap qualification.


#### Selected-state batch native controls

Plan positive complete-owner fixtures with 32 states in one batch and 257 states partitioned as 256 plus one, preserving independently expected complete values. Include duplicate/null/zero/foreign original array elements, missing state from the partition union, overlapping batches, different arrays for node/scalar statements, a foreign-state observation, orphan payload and late stream interruption. Invalid parameters/partition refuse before their submissions; native corruption or incomplete termination refuses before whole-result publication. Verify the same original cut/account across batches and count all context/authority/containment work, not just data queries. Compare single-state and batch observations against independently authored expected state/node/payload membership, never use one implementation output as the other's oracle. Array parameter transport and pre-materialization bounds require selected driver/native qualification.


Batch parameter transport controls preserve `9007199254740992`, `9007199254740993` and `9223372036854775807` as distinct exact admitted strings and observe the selected server's full interpreted array. Verify the 5121-byte upper bound with 256 distinct nineteen-digit positive int8 IDs, plus actual driver framing and simultaneous copies. Reject unadmitted quoted/whitespace/dimension-prefixed/nested/NULL array text without using PostgreSQL's broader parser as original membership admission. A Number-based conversion, changed second-stream parameter or generic driver conversion must not silently pass. These are native transport tests under CONTRACT-007, not new public executor types.


Batch lifecycle controls include a fully admitted zero-present-state owner: submit no empty-array tree queries, preserve optional absence and still refuse any required missing field. With nonempty inventory, exhaust submission/containment reservation after header collection and prove no batch stream starts. Complete both streams but omit one reconstructed-state completion entry; whole-result membership must refuse despite matching row counts. Interrupt after an earlier batch has transferred admitted values and prove no partial publication or spent-work refund. Independently track completed-state set, retained output ownership and original recovery; query termination is not reconstruction completion.


Plan the same complete 10000-present-state fixture under both lookup resource candidates. The original 64-submission profile refuses the 81-data-submission plan before streams. The separately selected 128-submission batched candidate admits only if the full original observation/containment plan fits the remaining 47 submissions and every byte/work/time ceiling; use an independently fixed required-path inventory rather than counts reported by the implementation. Add one-over total submissions and exhausted containment reservation controls. Record the profile selected before the operation; rejection cannot trigger automatic escalation or restart. Neither fixture is qualified until its selected native producers and complete expected values exist.


For the larger batched lookup candidate, use multiple individually under-limit native result sets whose combined original encoded result exceeds 134217728 bytes; require whole-result resource refusal without batch-counter reset. Separately saturate the per-row 67108864-byte limit, final-record 4194304-byte limit, cumulative charged-byte 536870912 ceiling and owned peak 268435456 ceiling with independently sized fixtures and actual framing/copy measurements. Do not infer success at all simultaneous maxima. Complete property/retained owner entries and present tree states are independently expected inventories; equal counts cannot substitute for their distinct meanings. Native receipt/resource producer and containment qualification remain required.


#### Field-identity encoder candidate qualification

Select the proposed four-component compact-JSON profile explicitly, then compare actual Truss writer bytes, compiler parameter bytes and native stored/readback bytes against independently authored witnesses. Cover reordered input object members, quotes/backslashes, each admitted short/control escape, literal non-ASCII and supplementary Unicode, composed versus decomposed spelling, exact 4096-byte component boundaries and one-over refusal, NUL/unpaired surrogate and unknown-member refusal. Preserve the 98360-byte conservative encoded ceiling without interpreting it as valid original identity grammar. Observe preallocation reservation and original repeated-copy/work charges. Inspect the effective compiler dependency feature graph: enabling serde_json preserve_order invalidates this candidate unless separately qualified original byte correspondence proves the selected procedure. Legacy stored encoding retains its original profile; no read-side normalization or in-place reinterpretation is permitted. These tests qualify a selected native bridge, not a universal UMF identity encoding.


The [Rust serializer oracle](../../04-build/evidence/design-audit/record-identity-oracle/Cargo.toml) uses Weft's actual Identity type and pinned serde_json features with [three independent byte fixtures](../../04-build/evidence/design-audit/record-identity-oracle/fixtures.json). Its original manifest references the owner working checkout and must not be used to qualify dirty owner work. The [executed frozen-source receipt](../../04-build/evidence/design-audit/record-identity-f05-explicit-toolchain-oracle.json) instead selects adopted f05f2df in an isolated harness, explicit Rust1.90.0 and offline dependencies; all three original byte fixtures pass. The receipt retains the selected manifest, actual core source hashes, complete command/output and [resolved standalone lock](../../04-build/evidence/design-audit/record-identity-oracle/frozen-f05.Cargo.lock). An earlier launch without explicit toolchain failed before compilation and remains in record-identity-f05-oracle.json; it is not a fixture failure. Reproduction uses the retained selected manifest and lock with --locked --offline on the same admitted frozen source. The standalone feature composition is not the actual compiler's complete effective feature graph; that graph and writer/native correspondence remain separate adoption evidence. No native storage or complete identity-encoding support claim follows from this pass.

### Cast boolean payload controls

Under the fixed full-slot text-cast source, independently admit true/false payloads and preserve SQL NULL separately. Refuse t/f, TRUE/FALSE, 1/0, whitespace, empty text and a host Boolean value substituted for the original text carrier. Change the source to project raw bool or change the original result descriptor/cast identity while retaining familiar column aliases: refuse the selected decoder before publication. Swap a payload true cell with a presence/integrity cell; full original slot/context correlation must refuse despite identical literal grammar. Native producer tests pin the actual cast/output-function/server profile; source review alone cannot qualify them.


Retired-state classification controls use the concrete STP-004 R-A/R-B/R-C sources. Preserve the complete typed-owner header including retired Item.note states; independently derive active projection and original retained custody. Valid null/empty retired states are classified privately before active-member omission, not treated as absent/foreign or moved into unknown-name content. Corrupt a retired root, remove its original definition/home, add a duplicate or misowned state and require complete integrity-qualified read refusal. Introduce a fresh same-name Field and prove its own absence cannot consume the original retired state. Reintroduce the exact original lineage and require its preserved original values after admitted acceptance. Explicit complete DirectRecord versus active-schema projection meanings and disclosure authority remain profile-bound; these planned controls do not change the public result wire or grant compiler lifecycle support.


### Frozen Python compiler serializer feature graph

The [actual cargo feature observation](../../04-build/evidence/design-audit/weft-f05-python-serde-feature-graph.json)
uses frozen f05f2df, explicit installed Rust1.90.0, --locked --offline and the
actual weft-python/truss-postgresql-qualified build selection. Effective
serde_json features include arbitrary_precision and raw_value and exclude
preserve_order. Original dependency manifests, Cargo.lock and Identity source
hashes plus complete command/output are retained. This closes the effective
Python build-feature observation separately from the three standalone byte
fixtures; it does not qualify a different CLI/TypeScript/WASM feature graph,
writer/native identity storage or the complete selected codec profile.

The initial implicit rustup invocation attempted channel synchronization and
failed DNS before Cargo inspected dependencies. Explicit installed toolchain
selection then completed offline; no dependency upgrade, download or owner
working-source adoption was needed. Recheck this feature closure after any
selected feature, dependency, source or build tuple change. Native writer/read
byte correspondence and full Unicode/boundary/refusal cases remain not_run.
