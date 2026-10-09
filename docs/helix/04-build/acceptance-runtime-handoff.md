# Public acceptance runtime handoff

Status: execution sequence authored; public runtime unavailable. Governing inputs: CONTRACT-003/007/008/009, TD/STP-001–006/024/036/039/045 and the reference toolkit composition proposal. This handoff addresses the consumer integration request for actual accepted IDs, immutable reports and atomic active-head publication. It is not a fixture-acceptance workaround or support claim.

## Current implementation boundary

The public assembly in `packages/postgresql/src/index.ts` remains inert: catalog,
mutation and feed selectors return unavailable. The private preparation supports
new-only staging; it does not supply transform, retirement or provisional-endpoint
support. Immutable-report guard evidence covers byte-home mutation refusal, not
complete insert admission, installed privilege closure or accepted head publication.

The latest `verifyWithExecutionAndRegisteredReportProfile` path verifies ten
original producer fields plus the complete originalExecution candidate and
registered reportProfile bytes under one original preparation/connection basis.
Original candidate custody precedes parsing/profile resolution, and native context
is rechecked before return. Its explicit scope is
`twelve_original_report_candidate_fields_only`; registered bytes are not selected
report-profile semantic admission.

The current report suite passes 16 tests/142 assertions and strict TypeScript.
The [combined PostgreSQL 17.9 receipt](evidence/catalog-new-cohort-combined-report-correspondence.json)
records 183 component observations. Earlier
[execution-only](evidence/catalog-new-cohort-execution-correspondence.json) and
[registered-profile](evidence/catalog-new-cohort-report-profile-correspondence.json)
receipts retain their original narrower scopes. All owned probe databases were
removed; no live native run is pending.

Four dynamic fields remain: umf, rebinds, assertions and pending_indexes. The
interfaceVersion constant is checked by the pinned 0.1 codec; its selected
report-profile-to-schema mapping still requires semantic admission. Full report
insertion, original finalization, confirmed commit and public head admission remain
A3–A7 work. Keep unconditional deferred barriers until that complete path is
independently qualified.

## Ordered implementation work

### A2 UMF support producer before full report comparison

Source inspection of `catalog-umf-report-basis.ts` finds original source versions,
interpretation/support pins and support artifact custody, with scope explicitly
`original_umf_and_support_byte_basis_only`. It does not interpret the admitted
supported subset. Do not count that object as the report's complete umf field or
append it to the existing candidate verification merely because its pins match.

The next producer must resolve the original registered support artifact under
its selected semantic procedure, enumerate the supported versions/subsets and
interpretation/loss obligations for every accepted document, and compare an
independently authored complete expected umf value. Unknown or unavailable
support meaning refuses complete report admission; no empty/default supported
subset or inference from source version is allowed. Keep this separate from
assertion enforcement classification. Implement and test that producer through
the existing original preparation/correspondence path; do not add a second UMF
validator or reopen public admission before all seventeen fields compose.

The existing report schema represents umf as an array of closed entries with
exactly version, interpretationProfile and supportedSubset; supportedSubset is
an ExactArtifact, not a string label or inline claim. Version 0.2 reuses this
0.1 field definition. Bind each entry to original document-version inventory
and the selected interpretation profile, and resolve its subset artifact through
the original admitted support composition. The supportProfile pin or its whole
artifact cannot be substituted for every version's subset reference unless the
registered interpretation explicitly establishes that correspondence. Preserve
the selected entry ordering and complete version membership.

Independent controls must include two source versions with distinct subset
artifacts, omitted/duplicated versions, swapped subset references, changed
interpretation pins and an unavailable original subset artifact. A single-version
positive case cannot close multiple-version membership. Retained-only semantic
references remain distinct from required executable checks under CONTRACT-003;
resolving artifact bytes cannot classify a retained-only term as enforced.

### A2 remaining dynamic producer integration

| Field | Original producer inputs and ordering | Independent refusal controls |
| --- | --- | --- |
| rebinds | Observe actual insertion-generated history events after admitted effects, under the selected report/history version and original operation cut. Admit complete mutation-group start/final state and every sibling before projecting its rebind entries. Persist the complete immutable report afterward and before head publication | Missing/extra rebind, copied event from another operation/revision, changed native seq, omitted non-rebind sibling or wrong ordered group digest refuses; no preallocated fake event or version conversion |
| assertions | Complete original occurrence inventory and independently admitted engine/native enforcement evidence, including unsupported/opaque meanings | Missing or duplicate occurrence, substituted owner/source/pointer, unqualified database classification or truncated inventory refuses completeness; observation coverage alone cannot establish enforcement |
| pending_indexes | Complete accepted declaration inventory under the original layout/binding profile, original installation/revision, exact declaration definition and physical target. Capture pending declarations before report persistence; do not dispatch jobs within acceptance | Duplicate job identity, conflicting definitions for one target, swapped revision/installation, omitted declaration or a ready-name substitution refuses. Empty inventory requires complete original declaration-absence evidence |
| umf | Original document-version inventory, interpretation profile and admitted version-to-subset artifact correspondence | Multiple-version omission/duplication, exchanged subset artifacts or unavailable original semantic composition refuses complete admission |

For pending_indexes, preserve the original declaration when a later worker becomes
ready, fails or loses its outcome. Physical-job admission/commit/run/observation
uses its separate existing administrative tooling. Statistics jobs retain their
distinct declaration/profile and cannot be inserted into the index array.
Compiler/native index existence does not prove pending declaration completeness
or grant execution authority. Exact-repeat acceptance returns original job
declarations without submitting a new attempt.

The full acceptance test must combine all four producers with the same original
input, profiles, revision and operation context, including an input that actually
requires rebind and an input that declares an index. Fresh empty-schema fixtures
cannot close those branches. Independently expected full report bytes, effects,
late-failure rollback and public head visibility remain A2–A7 exits. Preserve
the current source-exact 0.1 codec refusal until a separately selected compatible
report/history composition is implemented.

### A2 assertion inventory closure

Inspection of `catalog-core-assertion-identities.ts` and
`catalog-observation-coverage.ts` establishes two different boundaries: the
coverage assessor checks the ordered owner-observation requests and their exact
evidence; the identity collector deliberately returns `complete: false`.
Neither result is an enforcement report. Do not change that flag merely because
all requested observations are available or the deferred array is empty.

Implement the report assertion producer in this order:

1. Select and register the assertion-inventory profile alongside the exact UMF
   inspection and support profiles. Its enumerated rule families must cover the
   entire accepted input, including retained opaque assertions. The present
   core collector selects kind, nullability, cardinality, facets, keys,
   relationships and only allowedValues/default/facets schema properties; its
   request list is not a proof that those are every authored assertion.
2. Reconcile every original document occurrence with a disposition: assertion,
   explicitly non-assertive metadata, absence, or unavailable interpretation.
   Preserve source digest, qualified owner and original pointer. Reversible
   target observations require original-to-target correspondence before they
   can establish original identities; a target pointer alone is insufficient.
   Known unsupported or opaque assertions remain visible with qualified
   non-enforcement reasons. Unavailable inventory interpretation must prevent a
   complete report when it leaves occurrence membership unresolved.
3. Join each inventoried assertion to independently admitted enforcement
   evidence. Database classification requires the installed native mechanism
   and ordinary-writer coverage; engine classification requires the selected
   executable validator and its covered write paths. Leave classification as
   none where neither is qualified. Coordinate these joins with the security
   owner's key, privilege and write-path work rather than inventing another
   resolver. An inventory can be complete while enforcement remains none.
4. Compare the whole produced report against an independently enumerated
   expected occurrence set, then admit it to the existing seventeen-field
   correspondence. Omission, duplication, substituted source/owner/pointer,
   fabricated database enforcement, unavailable interpretation, and converted
   source misbinding must each have a refusal control. Include an opaque rule
   that is retained and reported as unenforced, plus absent declarations that
   produce no invented assertion. Independently count inventories; never use
   the producer's own entries as the expected set.

This closes the implementation sequence without adopting a new UMF semantic
API or weakening the report's complete-scope requirement. The full producer,
native enforcement joins and these controls remain unimplemented.

| Step | Implementation output | Independent exit before proceeding |
| --- | --- | --- |
| A1 | Pin one coherent installation/authority/executor/resource and catalog/value/key/profile composition; resolve selected model/generated/native correspondence. | Original native required inventory, grants/callable coverage and descriptor/domain correspondence match the selected composition. Component 0.15 does not imply a complete installation. |
| A2 | Assemble all seventeen report fields from original producers, including admitted interfaceVersion, reportProfile, umf, rebinds, assertions and pending_indexes beyond the eleven-field candidate path; the existing extensions and originalExecution comparisons still require their complete semantic profile admission. | Complete independently expected field membership/content; no caller-filled or constant-empty substitute for applicable inventories. Full report input/resource capacity reserved before effects. |
| A3 | Implement original catalog lifecycle: complete current-head repeat, additive declarations, retirement/reactivation, valid unresolved-endpoint policy and existing transform semantics. | Independently authored actual UMF-valid sources and resulting identity/definition/data/report expectations. Unsupported representations refuse explicitly, while required broader behavior stays open. Actual native IDs come from observed allocation, not fixtures. |
| A4 | Produce exact immutable full report bytes and insert them in the same original transaction as accepted source/definitions, data transformations and new revision. | Report byte equality, native immutable guards, complete original revision parent/seed and report-row correspondence; late report failure rolls back every effect. |
| A5 | Implement complete protected original operation finalization and atomic active-head publication. | Complete report/definition/history/feed prerequisites, final invariants and effect generations revalidated under original exclusion. Deferred safety barrier may be replaced only by the fully qualified selected finalizer, never bypassed. |
| A6 | Connect public catalog selector and acceptInTransaction/report to original capability registration, executor custody and current-authority publication. | Import/construction remains inert; wrong profile/disposed/stale/unauthorized selection refuses. Host transaction result is pending; public committed result requires actual owned commit observation. |
| A7 | Qualify native additive/repeat/lifecycle/late-failure/concurrency and caller commit/rollback cases through the public assembly. | Retain exact public invocation/input/result, actual IDs, native final inventory/report/head/journal and original commit/termination evidence; test at least one successful acceptance and every required refusal/rollback path. |

A2 can progress through independent producer work before A1's complete native installation qualifies, but no public activation follows partial correspondence. A3 cannot silently reduce acceptance to new-only operations while presenting full catalog support. Original source-level validity remains UMF-owned; Truss stores the selected complete interpretation and qualified local identities.

## Consumer sequencing after acceptance

Public mutations/groups must use the same selected accepted IDs/definition profiles and shared planner, producing the selected exact journal/history/feed facts. Request-bearing network groups require full durable original-result receipts and confirmed commit before acknowledgment. Complete feed/discovery/fragment/application/ACK and freshness use the explicitly registered v0.2 boundary, not the legacy assembly accessor by coercion. These are separate implementation exits; an executable acceptance path alone does not unblock the full demonstration.

Python orchestration can consume this shared public/native contract without duplicating Weft compilation or the security resolver. Package ownership remains pending. Actual independently implemented bidirectional interchange is required later; language or package names do not establish independence.

## Runtime reporting rule

For every delivered slice, report the exact public methods that execute, selected subset/profile and original native evidence, separately from unavailable methods. Until A6/A7 close, public catalog acceptance remains unavailable. Until their own full exits close, mutations/journal and complete feed/ACK remain unavailable. Source checks, mock connections, report shape and immutable-trigger-only observations cannot change those conclusions.

A2 now has an implemented original UMF/support byte-basis collector at `packages/umf-bun/src/catalog-umf-report-basis.ts`. It recognizes original prepared input, requires the registered support artifact and preserves distinct original source versions in input order plus exact interpretation/support pins and bytes. It intentionally emits no supportedSubset assertion: registered byte custody is not semantic support admission. Real pinned UMF producer tests reject copied/unregistered preparation and compare original 0.7 source versus reversible 0.8 interpretation, with exact retained support bytes. Fourteen input-preparation tests/45 assertions pass using the original Record producer built by `scripts/build-umf-runtime.ts`; this is producer-basis evidence, not a completed report, accepted revision or public capability.

Report correspondence now independently derives and checks the complete original extension-artifact array, bringing its explicit compared field count to ten. Missing, duplicate and substituted occurrences refuse. Sixteen report/extension tests with 165 assertions pass against the pinned original UMF Record/declaration/Field producers. Extension payloads remain retained uninterpreted with full original source custody; this comparison supplies neither extension semantic support nor native report insertion/head publication. The other seven report fields still require their original full producers/admission.

## Remaining report field admission

| Field | Existing basis | Required producer/admission work |
| --- | --- | --- |
| interfaceVersion | Closed report schema's exact literal | Bind the selected report codec version; reject any different wire before native publication. This constant is not installed qualification. |
| reportProfile | Report schema ProfilePin | Resolve exact host-registered report procedure bytes and original installed/profile correspondence; input acceptanceProfile is not automatically this profile. |
| originalExecution | Native actor, captured/asserted origin, epoch and configuration collectors | Compose exact original installation/epoch/origin/journal-origin/mapping/capture/context evidence under one admitted operation cut and recheck; individual collector outputs are not a complete artifact. |
| umf | Original UMF/support byte-basis collector | Interpret and admit the complete declared supported-subset artifact against actual original source versions and selected interpretation; registered bytes alone supply no support claim. |
| rebinds | Selected shared mutation/history protocol | Observe complete original accepted rebind events, or prove complete qualified absence. No new-only count or empty fixture array can establish broader lifecycle absence. |
| assertions | Core assertion identities and owner observations | Complete all selected source/opaque assertion inventory and evidence-qualified enforcement classifications; complete scope cannot be inferred from a partial eleven-entry source inventory. |
| pending_indexes | Existing index/statistics job admission/readiness contracts | Collect complete original acceptance-associated jobs with declaration/attempt/profile state and pending/committed distinction; an empty fixture is not proof no jobs were requested. |

The native new-cohort script now constructs extension artifacts from original preparation and expects the ten-field correspondence scope. Bun bundles its 29 modules successfully; the full native script has not been rerun in this change and no historical native receipt is rewritten. This caller repair preserves the unconditional commit barrier and the script's explicit component-only scope.

The repaired native check has now run in a freshly created database on the dedicated truss-runtime-admission PostgreSQL 17.9 container. All 171 original component observations pass, including the ten-field correspondence and original-cut/rollback controls. The separate catalog-new-cohort-extension-report.json receipt preserves previous receipts. The owned test database was removed after completion. This remains private new-cohort/collector evidence with report/head/finalizer/public admission explicitly unqualified; no safety barrier was removed.

The originalExecution field now has an implemented candidate composer in catalog-execution-report-candidate.ts. It requires original epoch collector issuance, checks exact capture/mapping bytes and pins, rechecks native cut before/after remapping original asserted origin, and preserves original installation/epoch/context evidence. It returns an explicitly unqualified candidate; component profile labels/bytes do not supply installed authority or registered semantic procedure admission. The fresh PostgreSQL17.9 run adds correct composition and substituted capture/mapping refusals, for 174 component observations in separate catalog-new-cohort-execution-candidate.json. The owned database was cleaned up and earlier receipts remain preserved. This field is not yet added to the full accepted-report correspondence or publicly activated.

Execution candidate issuance now binds the original connection/preparation/report/epoch through private provenance, with separate fresh native recheck. Copied/unissued candidates refuse before native I/O. One five-assertion unit case passes, and the separate fresh PostgreSQL17.9 custody run passes 176 component observations, including original issuance/recheck and copied candidate refusal. catalog-new-cohort-execution-custody.json retains that run without rewriting earlier evidence; the owned test database was cleaned up. Candidate provenance still supplies neither profile-semantic admission nor public acceptance authority.

Report correspondence now exposes a separate private verifyWithExecutionCandidate path. It first requires original candidate issuance, verifies the existing ten producer fields, compares the entire originalExecution object and freshly rechecks original native context. Its result explicitly says eleven_original_report_candidate_fields_only, not full accepted-report authority. Fifteen report/custody tests with 131 assertions pass, including refusal of an unissued candidate before parsing/native I/O. Positive native invocation of this new report-comparison path remains not_run; earlier native candidate-composition evidence cannot substitute for it. No public selector or finalization barrier changes.

Positive verifyWithExecutionCandidate has now run on fresh PostgreSQL17.9. Its eleven-field result matches actual original epoch/origin/report collectors; modified databaseRole refuses and ended native operation cannot verify retained candidate bytes. All 179 component observations pass in separate catalog-new-cohort-execution-correspondence.json, preserving earlier receipts. The owned database was removed. OriginalExecution field comparison is now native-observed at this private component scope; selected profile meaning, complete seventeen-field admission, immutable report insertion and head/public activation remain unfinished.

Report profile byte resolution now has a distinct report role and resolveReport operation on the existing trusted startup resolver. It cannot borrow an acceptance-role registration even with matching pins; it preserves frozen original bytes and refuses unknown/changed or duplicate registrations. Seven profile tests/30 assertions pass. This role is selected separately by host report composition and is not a new AcceptanceInput member or inferred semantic-input change. Exact report procedure meaning, installed/native correspondence and original producer admission remain required before its pin can support full report publication; byte resolution alone is explicitly original_registered_report_bytes_only.

The pinned canonical report codec explicitly refuses 0.2/0.3 proposal tags,
guessed 0.1 spelling and unknown versions without conversion. Five focused codec
tests pass. Adopting a later report/history profile needs an explicit new codec
schema/pin/producer composition; the combined candidate path cannot infer it
from matching field names or a registered report artifact.

An asynchronous custody control mutates the caller's report buffer during the
native observation in the registered-profile path. Returned original wire
evidence remains byte-exact to the pre-observation checked copy. The current
report suite passes sixteen tests/142 assertions and strict TypeScript; this
controlled observation test adds no native support claim or new verified field.
