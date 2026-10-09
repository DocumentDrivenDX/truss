---
ddx:
  id: STP-001
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-001
      kind: informed_by
    - id: TD-001
      kind: informed_by
    - id: SD-001
      kind: informed_by
---

# STP-001: Whole-revision acceptance

## Immutable report outcome schedules (planned)

RPSEL-03–06 supplement RPSEL-01–02: (03) verified exact current-head repeat returns byte-identical original report/origin with no new revision, report row, transform or index dispatch; (04) the same historical input after another accepted head requires fresh complete validation rather than historical equality bypass; (05) fail after original events and report insertion but before head publication and require full operation-local rollback with earlier adopted caller work preserved; (06) commit acceptance and lose the response, then observe original accepted report/head through recovery without duplicate insertion or another revision. Pending savepoint completion never supplies committed report evidence. Index-job completion leaves the original pending-job report inventory unchanged. Cases are not_run and require selected native producer/recovery and independent report/event inventories.


## Selected decision handoff — 2026-10-07

Planned report controls RPSEL-01–02: nonempty accepted report includes actual original generated event IDs, is immutable, and commits with catalog/journal/head; fail between report production and head publication and require whole-transaction rollback with no accepted report-less head. Fresh/retained legacy report conversion remains independently qualified. Cases are not_run.


## Story Reference and Scope

US-001, TD-001, SD-001, TP-001 and CONTRACT-003/007. Tests are planned. Complete expected diagnostics/assertions are authored independently of output enumeration.

## Acceptance Criteria Test Mapping

Additional acceptance-identity probes: identical verified full input at the current head returns its original report/origin without transforms or new index dispatch; changing raw document bytes or unknown extension content while leaving derived rows equal creates a separately auditable acceptance; changing binding, loss policy or transform profile cannot qualify as a repeat. A historical matching input after an intervening revision undergoes current candidate validation. A forged claimed fingerprint cannot bypass exact input verification. Canonical fingerprint/profile and complete persisted-input representation remain gates; these cases do not claim implemented replay.

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-001-AC1 | `valid_two_document_set_has_one_revision_and_exact_report` | Revision 1 contains expected catalog elements, exact UMF versions/subset and independently hashed document bytes | `@covers US-001-AC1` | Native integration | `tests/catalog/accept.test.ts`; valid independent documents |
| US-001-AC2 | `all_invalid_document_diagnostics_leave_no_revision` | Every available violation in every document is reported; no head/catalog/data/journal/origin/report candidate persists | `@covers US-001-AC2` | Native integration | Same file; multiple invalid documents and late failure |
| US-001-AC3 | `report_covers_independent_assertion_inventory` | Every authored assertion has exact source identity and honest enforcement layer, including unknown/residual content | `@covers US-001-AC3` | Contract | Same file; independent expected inventory and qualified profile |

## Data and Failure Probes

Current-core branch compatibility controls pin UMF source/API operation separately from document validation: operation 3.0.0 with core 0.8.0 is a candidate positive only after exact adoption; valid 0.9.0 semantic-type input requiring tuple encoding must refuse the unavailable selected combination without an upstream-invalid diagnostic or envelope rewrite. Older 0.6.0/0.7.0 inputs cannot inherit operation-3 compatibility. Exact vocabulary/version/term mismatch, unknown qualifiers, missing/malformed/thrown validators and caller replacement registration remain incomplete/unsupported under required interpretation. Permitted retained-unselected 0.9.0 annotations preserve all original bytes and their declared state with unknown/incomplete interpretation; any none/opaque enforcement label is explicitly Truss classification. Older-core same-named content remains opaque. A valid vocabulary check never upgrades native enforcement, Weft mapping/casts or other core validation. Change registry definition/validator release while source bytes remain equal and require new profile admission rather than reinterpreting an original report/repeat. These planned controls qualify no package/native support.

Semantic composition controls retain the literal vocabulary version while independently changing definition bytes, validator implementation or retained-only/required-check purpose: original supportProfile/hash/custody must fail correspondence or require a newly admitted profile. Two conjunctive references preserve full ordered diagnostics; neither registry ordering nor duplicate registration may suppress a check. Substitute source-provided validator authority, omit a protected archived definition/result or load an old report through today's registry: refuse without fabricated original evidence. An uncontained callback cannot run under the bounded pure-check profile; timeout/error preserves complete original failure/custody and no acceptance effects. These remain planned controls pending exact host execution/resource profile selection.

[Semantic admission vectors](../../04-build/evidence/design-audit/semantic-check-admission-vectors.proposal.json) independently specify six aggregate/admission expectations: absent declaration, all-complete-valid, valid-but-incomplete, invalid-plus-unknown, complete invalid and unknown-plus-valid. Compare actual complete original check inventory/order/status/completeness and permit required-check admission only for complete valid. Incomplete invalid cannot certify all-reasons coverage. Unknown qualifiers must retain the declared reference and prevent invocation/complete interpretation; malformed unknown/complete=true results must preserve the producer's unknown/incomplete diagnostic. Module/document annotations cannot become element declarations. These are authored expectations, not tests run against UMF or native Truss.

Immutable-report ordering controls for `truss-acceptance-persistence/0.1.0` compare complete pre-admitted expected report with independent actual pending/committed effects. Parent revision/source rows must exist before their immediate-FK dependants; report rows are inserted once and never rewritten after generated metadata/effects disagree. Inject failure after parent insertion, archive insertion, a subset of catalog/graph/journal writes and final parity; confirmed rollback leaves no new revision/doc/report/head/effects, while unknown termination retains original recovery. A host trigger producing unexpected report metadata, missing generated-value reservation or an attempt to commit between persistence phases must refuse the selected procedure/privilege profile. Pending report visibility is not committed success. Sequence gaps after refusal remain permitted, but no gap or preallocated event identity proves publication. These controls are planned and require the exact native producer/phase encapsulation profile.

Report-compatibility vectors retain an unknown optional nonsemantic member verbatim while a restricted display omits it, then inject an unknown required assertion/loss/diagnostic meaning and require full qualification blocked. An unrecognized unknown-endpoint policy refuses before effects; adding an enum value alone is not compatibility. Current upstream-invalid cross-document examples cannot pass by selecting provisional/skip. Positive future-package cases remain separately gated, with valid local-cycle controls.

Conversion-provenance vectors keep converted UMF bytes equal while changing original source bytes, adapter profile or exact loss report; each changed verified input must remain separately auditable rather than a current-head repeat. Missing source/loss artifacts, forged digests or unsupported adapter report semantics refuse admission. Native ingress has no fabricated conversion evidence. Schema fixtures cover nonempty documents, complete binding/ingress and exact transform parameters; separate semantic cases cover duplicate document identities/members, base64 pad bits, dependency order and source authority. These structural checks do not qualify conversion or native acceptance.

Include malformed first document plus later parseable invalid documents, empty set, warning-only input and exact source byte variations. Missing diagnostics/assertion entries fail even when counts look correct. Force complete parent/report insertion failure, then separately inject dependent journal/value persistence failure after tentative effects and inspect rollback independently. Transform evaluation failure occurs before persistence; it cannot be used to justify rerunning callbacks inside the native function. Caller rollback removes pending acceptance; concurrent acceptances serialize on actual head.

Verify report persisted before commit and postcommit pending-index readiness does not rewrite it. Incomplete blocked checks are explicit rather than silently omitted. Invalid local references follow pinned UMF rejection; no invented external dependency resolver.

Journal-mode composition controls independently run engine and trigger profiles. Trigger-mode acceptance must write no engine journal rows or trigger-owned version/time values; assert exactly the required rebind/transform payloads and version increments, including no-op cases. Observe actual insertion-assigned seq/at and reject plan-supplied producer claims. A report profile requiring unavailable future insertion metadata refuses composition before effects; it cannot omit the field, shift its clock or switch mode. These controls remain planned native/report evidence.

Semantic-operation controls for P0–P6 reject SQL/callable/table-name payloads, cross-category effects, repeated/skipped/reordered phases, forward references and mismatched expected target cardinality. Exact repeat allocates no new identities and inserts no archives. Inject an extra catalog row or journal event after planned writes and require independent P5 parity refusal with no P6 head publication. Attempt postcommit index dispatch through the plan and require admission refusal. These are planned decoder/native controls, not passing shape evidence.

## Acceptance result/provenance supplements

Source-collation controls select an insensitive database default and independently expect distinct case, accent and NFC/NFD document identities under the proposed explicit C columns. Uppercase or altered source-kind tokens must not satisfy the exact enum CHECK. Observe actual parent/source/FK/unique/index collations and full-byte source correspondence; a client cast or valid FK with different native equality is insufficient. Populated collation/dependency conversion remains a separate atomic migration, not execution of the fresh fragment.

Legacy pointer conversion controls preserve original since_rev and its creation FK while independently deriving actual later definition sources. Archive original doc_ord/source interpretations before retiring the three legacy homes; key_def has no doc_ord removal. Changed constraint names and unknown dependent host objects must not trigger guessed drops or CASCADE. Inject failure after staged assignment, new constraint validation and legacy retirement, requiring whole-original rollback/recovery and no published partial layout. A reverse copy of a new ordinal into the old since_rev pair must not qualify downgrade. Native context-drain and original archive evidence are separate required observations, not inferred from successful DDL.

Definition-source native constraint controls cover all four homes under the selected future layout: complete document tuple, complete binding tuple, missing source kind, unknown kind, every partial-null tuple, mixed document/binding members, empty binding bytes and wrong archived document/revision identity. Explicitly test SQL NULL CHECK behavior so missing kinds cannot pass as unknown. Only a provisional type may have complete absent source, and that native shape does not make upstream-invalid provisional acceptance valid. Check same original creation revision with a later actual definition source; native FK existence must not substitute for original artifact correspondence. The new fragment is fresh-layout-only source design, not populated conversion or native qualification.

Exact-repeat archive controls deliberately substitute equal claimed digests with different framed bytes, equal canonical trees under different domains/profiles, incomplete original source archives and a historical matching input after a newer head. Each must fail repeat admission or require ordinary current-state acceptance as specified; resource exhaustion cannot take a hash-only fallback. Outer transport member order/whitespace is a semantic equality control, while changed embedded document bytes, conversion source/loss artifacts, pins, explicit binding presence or transform parameters remain distinct. Independently compare the returned original report/origin and assert no transform callback, new revision or index dispatch on verified repeat; revoked current disclosure authority still withholds the result.

Catalog-mask controls attempt retained property owner/name changes, type kind/creation changes, key component/number reassignment, relationship composition/association changes and an arbitrary endpoint-pair edit through ordinary acceptance. Reject fields outside the selected category/profile mask; required migrations or new compatibility profiles cannot be bypassed by an upsert. Native tests compare complete original definitions, not ID-only matches, and inject zero/multiple affected-row results. Independently verify exact schema_change before/after and immutable source/lineage retention; baseline and proposed-layout masks require separate inventory qualification.

Effect-inventory controls distinguish two changed properties of one record from two record changes: require complete admitted grouping and independent actual version/event correspondence. Add one representation-identical transformed property, one lexical-only changed value with mathematically equal key, an unmatched retained entry and a value-preserving retained-to-property rebind. Compare exact member sets and maps; equal totals with swapped property IDs must fail. Reject duplicate members, implicit mixed same-property attribution and trigger-induced extra version increments. Mixed transform/rebind native support remains profile-gated until intermediate-state/grouping/dispatch semantics are selected. No-op and grouping controls do not resolve the separate report-persistence conflict.

Genesis control compares installed revision 0 with the baseline `{}` report and the positive-revision accepted-report wire. It must not decode as an accepted empty document set or fabricate source/actor/validator provenance. A registered genesis interpretation is tested separately from positive acceptance; unsupported interpretation remains explicit. Empty UMF acceptance still refuses, independently of a valid empty installation. Future report-storage conversion preserves original genesis bytes and independently qualifies its selected initialization/lookup semantics.

Current-wire reconciliation control: one valid existing defined type gains a field matching retained data, producing at least one rebind. Independently require its full report event, actual native seq and complete mutation-group digest. Under the unreconciled parent-before-effects proposal this composition is unsupported; an empty rebind array, fabricated event, omitted required member or silently changed journal mode cannot satisfy acceptance. A separately valid no-rebind case is only a control and cannot qualify the rebind path. Once the report/storage/event design is adopted, replace the unsupported expectation with independent complete report-to-actual-history parity under both journal modes and whole-attempt fault containment.

Independently expect complete rejection to contain every qualified document violation and no accepted revision/report. Stop one scan at its resource limit: preserve available diagnostics with incomplete/resource, without claiming all violations. An empty complete refusal fails semantic report admission. Native rollback uncertainty is an execution failure, not rejected/unchanged. An accepted result inside an adopted transaction remains uncommitted until host outcome; outer commit failure cannot be hidden. Repeat exact input under a different asserted origin/acting role and require the original report/capture receipt, with current disclosure authorization separately checked. Forged role text or capture digest refuses provenance qualification.

## Catalog facade supplements

Inert selection performs zero I/O. Reject read-only/foreign/dead transaction handles before native acceptance effects, preserve earlier host work on operation-local refusal and never commit from acceptInTransaction. Confirm outer rollback removes new report/head/data while exact repeat retains original provenance. Report lookup distinguishes permitted absent revision from missing archive/unsupported profile/failed observation, with no fabricated complete report. A current index-ready observation cannot rewrite the original pending-index list. Revoked report authority prevents payload disclosure despite a retained facade handle.

## Declaration consumer evidence

`truss-catalog-capability-v0.1.typecheck.ts` independently consumes the public assembly/catalog declarations and verifies four forbidden shapes: rejected plus accepted report, rejection plus revision, projection as complete assertions and semantic acceptance plus committed durability. Run the combined strict declaration check from the implementation plan. These witnesses prove type distinctions only; runtime forged inventories, exact diagnostics, origin conversion and native atomicity remain separate cases.

## Declared-job inventory supplements

Accept exact index declarations and independently compare the report inventory to the accepted layout/binding/revision/target closure. Duplicate job identity or conflicting same-target definitions refuse before report/head persistence. Existing same-name physical indexes provide no readiness proof. Move a later attempt through failed/ready/stale observations and require identical original report bytes and pending inventory. A statistics declaration cannot be reported as an index job. Qualified cross-revision physical reuse requires separate current inventory/compatibility evidence.

## Rejection shape evidence

Run `bun docs/helix/04-build/evidence/design-audit/check-acceptance-rejection.ts <installed-Ajv-2020-module-path>`. Ten closed-shape probes exercise complete/incomplete diagnostics and exclusion of accepted revisions. Empty complete refusals and forged diagnostic bytes/digests deliberately remain shape-valid controls requiring semantic refusal. This command supplies no all-violations, disclosure or rollback proof.

Diagnostic-classification witnesses pair an upstream-valid newer envelope with unavailable selected encoding: preserve validator success/warnings and emit truss_admission unsupported-profile diagnostics. A true validator refusal remains upstream_validation with exact producer codes/paths/bytes. Forged stage labels fail semantic admission even when schema-valid. Conversion and transform failures retain their producer/source pins instead of impersonating UMF validity.

## Accepted diagnostics preservation supplements

Use independently expected upstream-valid input with warnings and partial unknown-extension interpretation. Accepted report retains exact source/profile diagnostic artifacts and per-document interpretation evidence, while assertions remain a complete inventory with opaque entries honestly classified. Remove one warning, substitute another document digest/profile, or change partial to complete without producer evidence: report admission fails. A complete assertion inventory cannot erase partial producer interpretation. Required unsupported interpretation still refuses; permitted unselected unknown bytes remain retained under the declared subset.

Run `bun docs/helix/04-build/evidence/design-audit/check-acceptance-report.ts <installed-Ajv-2020-module-path>` for nine accepted-report shape cases. Missing document inventory and forged evidence deliberately remain schema-valid controls for semantic rejection. Accepted warning/partial evidence is a positive shape case, not a claim of producer/native qualification.

## Ordered source inventory supplements

Use two dependency-ordered documents with distinct IDs/revisions/bytes. Independently expect ord 0/1 and matching ordered interpretation summaries. Duplicate/missing/extra entries, swapped ordinals and cross-document digest/profile substitutions fail semantic admission. Accept a later separately qualified order change and require prior definition provenance still resolves against its original acceptance archive. An unsupported legacy ordinal convention refuses rather than silently renumbering historical definitions.

## Executable Proof and Handoff

Future command `bun test tests/catalog/accept.test.ts` requires implemented harness and finalized report/diagnostic/index lifecycle. Pin validator/model/layout/role/server/adapter and retain full expected diagnostic/assertion sets plus native state. All three criteria block closeout. An existence/reference audit is not evidence of acceptance behavior.


Separate immutable report-home controls implement the owner-selected direction; native profile adoption remains required. In a complete selected replacement layout, independently observe actual rebind events before final report construction, then require exact report/event/source parity and one immutable report per positive accepted revision before head publication. Inject report encoder/storage/parity failure after graph/journal effects and prove whole-attempt rollback or retained original uncertainty. Ordinary parent/report/head insertion, report rewrite/delete and partial-phase calls cannot bypass the protected profile. Genesis has no positive accepted report; exact repeat with missing/corrupt report custody refuses without repair/effect replay. Baseline parent-report NOT NULL cannot be satisfied by a placeholder to simulate this profile. Populated conversion preserves old archives and refuses unavailable full original report/source correspondence. These are planned cases for the selected persistence direction, not evidence of installed native support.


Complete report byte-profile controls compare independently authored complete report bytes across object-member order permutations while preserving event/array order and nested exact value/source tokens. Stored bytes, feed ExactArtifact and repeat report custody must be identical. Direct artifact SHA-256 hashes only canonical JSON bytes; a framed input fingerprint is the wrong-hash negative control. BOM, trailing LF, whitespace, alternate escapes, duplicate members, host numeric tokens and reordered events cannot silently load as the same original artifact. Exact hash/canonical shape with wrong original event/group/source/profile custody still refuses semantic admission. Native report encoder exhaustion or mismatch after effects retains whole-acceptance rollback/recovery; it never invokes a host callback, drops members or repairs original bytes. These planned controls do not qualify an encoder from existing generic canonical vectors.


Report context controls run an acceptance assembly without compiler/feed-worker registration and require the independently admitted installed-context producer, with no optional service startup. Reject bootstrap candidate IDs, fabricated/default epochs, self-hashed context JSON and definer-owner substitution before effects. Preserve an originally unassigned xid capture unchanged while correlating actual later event xid through original native transaction custody. Future commit/report/feed artifacts cannot become context-evidence prerequisites. A repeat under a different authorized caller/context returns the original report without rewriting originalExecution; current disclosure/recovery remains independently admitted. These are planned producer-dependency controls, not runtime qualification.


Report encoding controls include original diagnostics with numeric native path components and unknown extension content inside their ExactArtifact payload. The outer canonical report preserves artifact bytes/base64/hash and diagnostic/source profiles exactly; a convenience adapter that expands the diagnostic into a host-number-bearing or renamed report object refuses the current wire. Independent artifact semantic admission may inspect those bytes under its own bounded profile without replacing them. A source payload containing JSON numbers is not automatically invalid merely because the outer report tree forbids host numbers. Complete diagnostic coverage and disclosure remain separately tested.


Rejection controls distinguish valid UMF input with unsupported selected encoding/transform/export capability from actual upstream invalidity, preserving native artifacts/classification and incomplete coverage reason. One error or skipped phase cannot certify complete all-violator coverage. Use a hidden stored violator/collision/endpoint to test diagnostic disclosure independently of submitted-document authority; no original artifact is edited under its old hash, and an unqualified projection cannot enter the complete rejection wire. Exhaust diagnostic/output capacity before persistence and assert no truncated complete result. After P2, injected parity/transport/encoder faults preserve original attempt/recovery rather than pure validation rejection; commit uncertainty never becomes proof of rollback. Trace/callback inspection verifies hidden facts remain private.


Native report encoder controls use independently authored complete expected bytes and split scalar/escape/container boundaries around the proposed 65,536-byte sink chunks. Verify exact controls/quotes/backslashes/slashes/non-ASCII spelling, object-key UTF-8 order and unchanged arrays. Reject numeric/cyclic/duplicate/invalid scalar producers without convenience coercion or callback execution. Fault allocations for frames, key sorting, next sink chunk, simultaneous final contiguous copy, SHA/base64 and actual storage; every post-effect failure preserves whole-acceptance rollback/recovery and exposes no partial artifact. Independently account raw producer/native intermediate memory and simultaneous chunks/full report, not only output length. These planned native tests must exercise the selected real producer/encoder; a host mock allocating the entire report before a size check cannot qualify the procedure.


Report ExactArtifact base64 controls independently expect empty, one-, two- and three-byte encodings plus complete report data spanning 65,536-byte boundaries and all modulo-three final lengths. Carry bytes across chunks and pad only at actual final completion. Reject MIME line breaks/whitespace, alternate alphabet, interior/excess padding and nonzero unused final bits; a permissive decoder cannot expand the admitted grammar. Verify exact widened output length and simultaneous source/base64/native-storage allocations, with one-over or conversion fault retaining original post-effect recovery. Artifact hash remains over complete report bytes, not base64 text or a domain-framed input fingerprint. Generic base64 vectors alone cannot qualify complete report production/custody.


Native report hash controls compare pg_catalog.sha256 over the actual final bytea allocation against an independent hash of retained original complete report bytes. Check 32-byte intermediate/64-digit lowercase hex and exact stored-byte correspondence. Base64 text, JSONB rendering, per-chunk digest concatenation and framed input fingerprints are wrong-source negatives. Shadowed names or substituted algorithm/build/profile cannot qualify the registered native producer. Capture actual functions/server/build and charge native inspection/detoast/digest/hex allocation separately; unknown termination remains original recovery. Planned native evidence is distinct from documentation of available functions.


RP01–RP05 conditional custody controls preserve immutable initial semantic expectations while later actual seq/at/group/report bytes are produced. Require complete expected/actual event matching before one report insert; original expectation carriers must not be rewritten to fit native output. Reject an extra graph/key/rebind effect after report construction, a missing planned head effect, stale pre-head generation seal, wrong report revision/context/class, report rewrite under a later ordinal and ordinary report/head helper bypass. Actual final report/head/event/registry/capacity state must correspond before application finalization and original commit. Force producer/observer/resource failure after report insertion and require whole-acceptance rollback or original unresolved recovery. These are planned native controls for the unadopted separate-report option; source allocation counts do not execute them.


Conditional replacement-layout controls use separate independent fresh-install and retained-baseline fixtures. The latter includes revision zero, multiple positive revisions with original complete report artifacts, an incomplete legacy JSONB-only report and a rejected/rolled-back candidate. Verify exact one-report-per-positive-accepted-revision correspondence, no acceptance report for the seed, unchanged earlier artifact bytes and current-authority exact-repeat lookup. Refuse missing original artifacts, lossy JSONB reconstruction, orphan/wrong-parent/duplicate reports, retained required parent-report columns, placeholders and conflicting old/new report authority. Fault conversion after archive/store changes and verify original containment or unresolved recovery without regenerating reports/events. Fresh-install success cannot qualify retained-state conversion. These are planned tests for the conditional replacement boundary, not adopted migration support.

### Rebind report subset and full journal correspondence

Independently author one catalog rebind whose complete entity/version group additionally contains its required metadata witness under the selected profile. Expect one report.rebinds entry but the full original group manifest count/digest over both events. Report list length must not replace group count. Refuse omitted/duplicate/foreign reported rebinds, a manifest recomputed over only report entries, and a schema-valid rebind with no complete original sibling evidence. Inspect property/metadata siblings separately; inserting them into rebinds is a shape violation, not a completeness repair.

Test original event-position/report association under the selected events-before-report/head-last ordering and finalization profile. A report's filtered list cannot qualify a full historical archive, native transaction manifest or feed acknowledgment. Native producer/source and original independent expected evidence remain prerequisites; existing report shape controls do not discharge them.

### Reserved positions do not prove early report completeness

Present purported reserved rebind positions before complete effects/final snapshot/sibling admission. Under the selected reference algorithm these are invalid phase custody, even if their integer values are in range; observe refusal before a reservation phase call or append. Reject the claim that these numbers alone make the current complete HistoricalEvent report ready for immutable parent insertion. Rebind reports require actual selected group/context correspondence, while physical journal at is not a current top-level envelope member. A producer that invents future native final state or computes digest over rebind-only entries cannot qualify the report. Verify the explicitly selected report persistence order and actual native whole-group evidence; no timestamp allocation or empty-rebind fixture substitutes for the full case.


## Logical Record producer and native acceptance separation (planned)

RCSEL-01–10 follow CONTRACT-003 and the [selected example coverage boundary](../../02-design/contracts/ashlar-core-acceptance-profile-gap.proposal.md#implementation-ready-acceptance-coverage-boundary). Pin actual UMF c45c72a2 validateCoreRecordValues 1.0.0 and its explicit core0.7→0.8 transition only after dependency/profile adoption. Independently authored inputs and expected inventories must not be copied from production output. All cases remain not_run; the three candidate positive records do not establish these controls or native readiness.

| Case | Independent input or fault | Required observation |
| --- | --- | --- |
| RCSEL-01 | Required label present, absent-allowed caption omitted; repeat with explicit absent caption, present null and present empty string | Logical result preserves each original state; absent and null remain distinguishable. Native round-trip under the admitted binding preserves absence/null/empty independently; a single SQL NULL representation fails. |
| RCSEL-02 | Required label omitted or explicitly absent; include a default declaration | Refuse required absence without inserting the default. No native catalog/data/report/head effects. Original per-field and aggregate diagnostics retained. |
| RCSEL-03 | Duplicate qualified label, undeclared member, same element ID in a different module | Refuse duplicate/undeclared or mismatched membership; names and fixture integer mappings never repair identity. |
| RCSEL-04 | Present integer literal for string label; malformed presence object or unknown input member | Actual UMF scalar refusal or input error retained distinctly; no host coercion or accepted check reconstructed from a thrown exception. |
| RCSEL-05 | V2 unknown availability; unknown top-level assertion affecting otherwise valid label | Complete label success cannot override incomplete Record result. Preserve exact document and selected diagnostics; refuse affected writable profile before native effects. |
| RCSEL-06 | Original core0.7 source passed directly; substituted core0.8 version; altered transition receipt/target/residual | Direct unsupported dispatch refuses. Unverified conversion or substituted profile refuses; retained original bytes and approved transition remain independently verifiable. |
| RCSEL-07 | Add a declared key or relationship while retaining a value-only input | Dataset-context obligation stays incomplete until its separately admitted full producer runs. No-declaration exclusion from the small fixture cannot waive the newly declared obligation. |
| RCSEL-08 | Logical result passes; existing retained native data violates current equality/ownership/endpoints or required availability | Full native Validate under catalog exclusion refuses; no new revision/report/head or partial transform persists. Inspect original data, reservations, groups and head independently. |
| RCSEL-09 | Exact current-head retry after changing current validator registry; alternate retry changes producer/transition/profile composition | Exact verified original input returns byte-identical original report without today's registry execution. Different immutable composition cannot masquerade as repeat; requires fresh complete validation or refusal. |
| RCSEL-10 | Inject failure after catalog allocations/effects or immutable report insertion, before head; separately lose acknowledgment after confirmed commit | Precommit fault rolls back all operation effects, preserving earlier adopted caller work where applicable. Postcommit recovery finds original real IDs/report/head and complete groups without reallocation, duplicate effects or fabricated fixture feed. |

Containment controls supplement RCSEL-04/05: malformed/thrown/nonterminating producer, attempted code registration from input, source-size overflow and unavailable account/termination evidence refuse within the admitted bounded profile. Inspect actual preallocation/isolation/cleanup evidence; a timeout after allocations or a description of a pure callback does not qualify containment. Keep original producer failure distinct from invalid UMF document status.

The native runner must capture actual installation/layout/profile/body/security revisions, original transaction/role/source custody, logical inputs/results, independent before/after catalog and report inventories, true complete journal/feed membership and observed outer commit. Component Bun/Chromium parity remains separate evidence; neither a green logical checker nor matching stored readiness flags proves protected-chain installation.


## Accepted catalog binding custody (planned)

WCB-01–04 and WCB-07 from the [accepted catalog producer](../../02-design/contracts/weft-accepted-catalog-producer.proposal.md) supplement RCSEL-01–10: independently verify qualified original IDs/documents/report bytes, substitution/incomplete-report refusal, exact revision/evolution context and provisional versus confirmed outer-commit publication. Native acceptance must precede owner binding production; a positive serializer revision or hash check cannot supply acceptance. Inspect original catalog/report/head and recovery effects independently. All cases remain not_run.

## Original input to report-document bijection (planned)

RPDOC-01–06 qualify CONTRACT-003's complete input/archive projection. All are `not_run` at the full protected acceptance boundary; the private archive collector does not pass these cases. Expected submitted input/artifact bytes, native archive members, interpretation evidence and report members are independently authored before execution.

| Case | Setup / corruption | Required outcome |
| --- | --- | --- |
| RPDOC-01 | Two original native documents with different revisions, Unicode identities and preserved noncanonical document whitespace; original order differs from lexical identity order | Complete input/archive/report bijection; exact source bytes/hash, metadata and ordinal strings, with no sorting or normalization |
| RPDOC-02 | Equal counts but swapped document IDs/order; separately substitute different original bytes under an equal claimed digest | Refuse complete report admission before head publication; full byte comparison and original order independently detect the mismatch |
| RPDOC-03 | Missing/extra/duplicate member, ordinal gap, wrong document revision, native UMF version or interpretation evidence/profile | Refuse; no inferred empty interpretation, deduplication, metadata repair or partial document report |
| RPDOC-04 | Original converted ingress with accepted UMF artifact plus distinct source/adapter/loss artifacts; repeat with only upstream source or loss changed while accepted UMF stays equal | Preserve all original artifacts; valid first acceptance uses accepted UMF bytes for the archive; changed upstream provenance cannot qualify as a current-head repeat |
| RPDOC-05 | Opaque registry fixture, wrong framed domain/profile, duplicate outer JSON member, invalid Unicode/base64 or unsupported original parser; separately replace original input with a caller documents-only list | Refuse original input interpretation; never interpret a fingerprint digest as a document source or accept the replacement list |
| RPDOC-06 | Exceed original native decoding/accounting budget; inject failure after complete archive matching but before report persistence; change surviving effect generation after matching | Preserve original execution/recovery evidence and earlier adopted caller work; publish no partial report/head; invalidate stale readiness and require complete recollection |

Compare complete original input/archive/report sets and bytes, not counts alone. Converted-source fidelity requires the exact adapter qualification; an invented loss report is a refusal control. Tests must exercise ordinary protected entry points and effective role closure, not grant access to private collectors as a substitute. Existing RPSEL-01–06 still govern report persistence, repeat and unknown commit outcomes.

### RPDOC-06 complete-input capacity schedules

Use the [capacity fixture](../../02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json)
as independent wire/sizing evidence only. Its synthetic pins and empty UMF
objects must refuse semantic acceptance. For native execution, substitute
original valid documents and actual registered profile/adapter/binding/transform
artifacts, then independently freeze the complete expected bytes and lengths
before invoking the public entry. Record which raw/tree/framed carrier the
original installed producer retains; those representations have different
lengths and are not interchangeable.

| Subcase | Independent input basis | Expected evidence |
| --- | --- | --- |
| RPDOC-06a | One 1,048,576-byte original source within the archive collector allowance; its canonical base64 alone is 1,398,104 bytes, before envelope/profile/provenance | Under the current one-MiB artifact component, refuse before effects; observe zero revision/report/head/journal changes and no digest-only or documents-only fallback. A future selected profile may accept only with compatible complete original custody and precharged bounds. |
| RPDOC-06b | Six original artifacts individually within one MiB with lengths 1,048,576 four times plus 1 and 1, totaling 4,194,306 | Under the current aggregate bound 4,194,304, refuse the complete operation; individual admissibility cannot permit partial persistence. Preserve earlier adopted caller sentinel work. |
| RPDOC-06c | Complete original input exactly at the selected inclusive per-artifact and aggregate boundaries, with native and converted branches and all required provenance | Accept only under actual registered parser/semantic/authority/resource profiles; independently compare full artifact/source/report inventories. Boundary arithmetic or JSON-schema validity alone is insufficient. |
| RPDOC-06d | The same complete valid input, but remaining original operation work/peak allowance is smaller than the conservative required decoder/verification/copy charge | Refuse before producer invocation/allocation under the qualified account; inspect producer invocation counts and native state independently. Increasing a caller-supplied budget cannot repair the original account. |

Run owned and adopted transaction forms separately. For refusal, inspect
independent complete before/after state and original transaction liveness;
a thrown exception is not rollback proof. Inject cancellation between
reservation and decode, and failure after bijection but before report insertion.
Retain original recovery custody whenever containment/settlement is uncertain.
These are planned full-boundary controls (`not_run`); the existing arithmetic
checker establishes only fixture shape/artifact integrity and sizing.

## Surviving report effect-count scenarios

RPCOUNT-01–06 exercise CONTRACT-003's complete count extraction under the
full protected acceptance entry. Freeze independently expected qualified
identity sets, endpoint tuples and before/after retirement states before
execution. Actual native IDs come from original accepted mapping custody;
fixture labels and allocator maxima are not expected installed identities.
All six cases remain `not_run`.

| Case | Independent effect basis | Required outcome |
| --- | --- | --- |
| RPCOUNT-01 | Exactly one genuinely new type, two properties, one owner-local key, one relationship, two distinct endpoint tuples and one active-to-retired property | Exact canonical count strings `1`, `2`, `1`, `1`, `2`, `1` in their respective members; complete source/native identity correspondence and report/head atomicity |
| RPCOUNT-02 | Retained active definitions update; one originally retired identity reactivates with the same ID; no genuinely new identities or endpoint tuples | Addition and retirement counts are zero, with the complete actual reactivation in its own inventory; no fresh-ID allocation or fabricated addition |
| RPCOUNT-03 | Same six totals as RPCOUNT-01 but substitute one unexpected property/owner or swap an endpoint target | Refuse complete effect/report correspondence despite equal counts; neither count equality nor digest routing repairs wrong membership |
| RPCOUNT-04 | Duplicate candidate endpoint occurrences, already-retired definitions and a tentative contribution rolled back to its original savepoint | Count only distinct actual surviving tuples and real active-to-retired transitions; no attempted/rolled-back/duplicate contributions survive |
| RPCOUNT-05 | True empty new/retirement sets, then separately omit a producer or hide one member from integrity visibility | Complete empty original inventory permits zero; omitted producer or filtered scope refuses, never manufactures zero |
| RPCOUNT-06 | Add an effect or change retirement state after count collection but before encoding/persistence/head transition; separately exceed collector resource bounds | Invalidate original readiness and require complete recollection or refuse under the original account. No stale report/head publication; preserve earlier adopted caller work after confirmed containment |

Independently inspect complete catalog, journal, report and operation-generation
inventories before/after both failure and outer settlement. Include ordinary
role direct-helper/write bypass attempts; private collector access granted to
a test actor cannot substitute for protected-entry qualification. Source stage
row counts and successful encoder output do not establish these scenarios.

## Outer input decoder qualification (planned)

JPAR-01–07 qualify CONTRACT-003's selected reference numeric-free byte decoder
before it issues the private complete-input basis. All remain `not_run`.

| Case | Independent byte input | Required observation |
| --- | --- | --- |
| JPAR-01 | Complete capacity fixture with legal whitespace/member permutation; include literal and escaped Unicode equivalents | Same admitted semantic tree with exact distinct original transport custody; no embedded artifact rewrite |
| JPAR-02 | Duplicate name using literal versus escaped spelling, including nested converted provenance | Refuse before duplicate insertion; no last-member-wins tree reaches schema/semantic admission |
| JPAR-03 | Overlong/malformed UTF-8, surrogate UTF-8, unpaired surrogate escapes; valid paired escape as separate positive control | Invalid originals refuse; valid pair preserves its exact decoded scalar and retained source bytes |
| JPAR-04 | Raw numeric outer value, comments, BOM, trailing data/comma, incomplete token and non-JSON whitespace | Explicit grammar refusal without owner metadata interpretation or fallback decoder |
| JPAR-05 | `__proto__`, repeated independent array elements, empty containers and embedded base64 whose decoded artifact contains numeric tokens | Inert own member data, original occurrence/order and opaque artifact custody; outer numeric prohibition cannot reinterpret embedded bytes |
| JPAR-06 | Exact selected depth/node/string/member/byte/work/peak boundaries and one-over variants; collision-heavy full-name comparisons | Inclusive admitted boundaries; refuse before over-limit frame/slot/string work; independently inspect precharged original account and no partial output |
| JPAR-07 | Raw/tree/framed representation substitution, wrong prefix/domain and cancellation while decoding | Refuse or preserve original unresolved custody; no alternate grammar, issued admission, native effect or committed-success claim |

Run actual packed browser and selected host decoder code on the same original
byte corpus, with independently authored expected scalars, source bytes and
refusal phase. Agreement between implementations is not the independent oracle.
Complete input semantics and native acceptance remain separate later gates.

The [outer-byte oracle](../acceptance-outer-json-expected.proposal.json)
now supplies eighteen manually specified input-byte/value/refusal cases for
JPAR-01–05/07, including escaped-equivalent duplicate keys, paired/unpaired
surrogates, malformed/overlong/out-of-range UTF-8, numeric outer nodes,
normalization-distinct names, prototype-name data and opaque artifact base64.
Every case retains exact input hex and direct source SHA-256; expected values
were authored independently of a decoder. Successful decoding is not complete
AcceptanceInput validity. Decoder/resource execution remains not_run; JPAR-06
requires the actual selected finite registration and boundary corpus separately.

JPAR-06 now has [four exact byte-boundary recipes](../acceptance-outer-json-boundaries.proposal.json):
ASCII exact-frame/one-over and supplementary-scalar within/next-occurrence
controls. Their independently specified UTF-8 sizes agree with the selected
canonical/framed profile by checked integer arithmetic. Generate the original
recipe bytes in the actual runner, retaining expected byte counts; host UTF-16
length is not the oracle. These recipes exercise byte admission only, not
complete wire validity or simultaneous work/peak qualification. Structural
and original-account fault boundaries remain separate planned controls.


## Admission-time configuration custody — IC-T01–06

The [installed-context temporal handoff](../../02-design/contracts/installed-context-admission.proposal.md#configuration-capture-time-and-immutable-operation-custody) governs these planned native schedules. The current late-collection witness is component evidence; full public acceptance/report publication remains required. Retain independently authored old/new configuration, binding and inventory bytes.

| Case | Independent required observation |
| --- | --- |
| IC-T01 late collector boundary | Change configuration in the same operation before first collection; current collector returns changed bytes and scope current_configuration_byte_basis_under_original_operation_only, never an admission-time success claim |
| IC-T02 original capture and changed use | Qualified pre-effect admission captures old complete capsule; same-transaction generation/scalar/artifact change leaves capsule unchanged and blocks publication, with full effect rollback after observed failure |
| IC-T03 atomic siblings and bounds | Remove/corrupt a required capsule sibling or exceed admitted aggregate/encoding capacity before capture; no admitted operation/report/head effects or substitute default/profile appears |
| IC-T04 adopted rollback | Savepoint rollback removes operation/capsule/effects while earlier caller work survives; copied/stale host issuance cannot be used after rollback; unresolved termination retains original recovery custody |
| IC-T05 concurrent transition | Original protected writer and configuration transition race under selected exclusion order; no mixed old/new capsule and no same-transaction lock-upgrade bypass; independently observe complete committed outcomes |
| IC-T06 historical replay | Retry a committed request after a compatible configuration change; return original result/context under independently admitted current invocation/disclosure, without rewriting historical capsule/report or reapplying effects |
