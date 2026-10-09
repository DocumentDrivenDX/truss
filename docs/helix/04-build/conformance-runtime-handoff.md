# Conformance runtime implementation handoff

Status: existing contracts and carrier proposals are authored; runtime services
remain unimplemented. `packages/tooling/src` contains the layout migration planner
and private alias-substitution and case-link candidate helpers. The conformance constructors and runner/assessor
lifecycle currently exist as declarations and type witnesses, not executable
services. Governed inputs are CONTRACT-004/007/011, US/TD/STP-027/028, the case
grammar and operation registry proposals. Reuse those APIs; no second runner,
qualification authority or public transaction-by-ID service is needed.

The [combined schema receipt](evidence/design-audit/schema-inventory-runtime-handoff-2026-10-09.json)
records strict registration, reference resolution and compilation of all 155
top-level contract schemas, including the case argument and operation registry
descriptors added for this handoff. It reports zero errors. This verifies schema
composition only; it does not implement the runner, establish observer independence
or qualify an operation against PostgreSQL or another implementation.

The newer [159-schema receipt](evidence/design-audit/schema-inventory-performance-handoff-2026-10-09.json)
includes the performance expectation 0.2 envelope and supersedes the old count
for the current top-level contract inventory. It retains every original schema
identity and byte digest; zero strict compilation errors prove only that exact
registration/reference composition. Strict TypeScript also passes for the current
link/coverage helpers, their coverage test and the synthetic link controls. No
registered conformance host, complete corpus or native qualification follows.

## Implementation sequence and independent exits

C4 has a private `conformance-diagnostic-multiset.ts` comparator for bounded,
already admitted diagnostic projections. Four tests/ten assertions and strict
TypeScript preserve duplicate multiplicity, source/profile/classification,
severity/code and exact path content, including root versus empty-member and
escaped names. Input source/profile strings are original registry comparison
keys whose complete artifact correspondence must be admitted before projection;
they are not caller-minted identities or authority. The comparator does not
decode diagnostic artifacts, select normalization, validate pointer truth or
establish corpus completeness. C4 must still resolve the original expected and
observed diagnostic artifacts and their version-scoped comparator procedure.

C2 has a private `conformance-case-links.ts` component for shape-admitted bounded
case projections. Twenty-four synthetic controls now exercise that implementation, including
performance references;
strict TypeScript passes. It checks case/grammar/registry correspondence, exact
operation/observation profiles, declared scopes, separate setup/input label
inventories and duplicate/unknown observation references. Its boolean result is
structural consistency only: original artifact custody, live scope admission,
required observer/boundary coverage and complete semantic expectations still
belong to original preparation and C4. Empty observation arrays cannot by
themselves prove unchanged state or no journal/report effects.

C2 also has a private `conformance-observation-coverage.ts` component comparing
exact required and expected `(surface, step, boundary)` inventories, refusing
missing, extra and duplicate keys across result/state/journal/report/performance.
Six synthetic tests cover omitted empty inventories, boundary/surface/step
substitutions, duplicates, ordering and performance replaced by behavioral evidence. The
required inventory must be supplied by original registered procedures under the
[case grammar](../03-test/conformance-case-grammar.proposal.md), not inferred from
expected arrays. This helper neither issues that registration nor establishes
observer independence or native completeness. C2 must integrate original
procedure-derived coverage before claiming a prepared case; C4 must still run
each applicable observer and compare complete values, including explicit empty
journal/report artifacts. No public runner is activated by this component.

C5 has a reusable private `conformance-alias-substitution.ts` component over
already admitted bounded JSON/namespace/binding/scope projections. Seventeen
synthetic controls now exercise that implementation, and strict TypeScript
passes. It preserves literal data and exact integer text, uses only registered
slots, refuses invalid/forward/rolled-back/unknown or wrong-generation bindings
and returns a copied candidate input. It does not admit native issuer, visibility,
resource accounting or complete public-wire semantics. C5 still requires those
original runner procedures and independent native invariant comparison before
normalization; no public conformance factory or capability is activated.

C1 must consume the [private original-service construction port](../02-design/contracts/conformance-original-service-port.proposal.md).
Public method shapes and matching profile metadata do not prove original
registered service/build/function custody. Preserve the existing factory API
and host qualification authority; copied services or unavailable original
startup registration refuse before constructing a projection.

| Slice | Concrete implementation output | Required exit |
| --- | --- | --- |
| C1 original composition and inert binding | Implement existing createConformanceRunTooling/createConformanceEvidenceTooling projections over original host runner/assessor; capture immutable exact configuration and method/profile correspondence | Missing services, unknown required profiles, changed pin or empty approved manifests refuse construction; no artifact resolution, native acquisition or execution occurs at import/construction |
| C2 prepareRun and recovery custody | Admit original manifest/input inventory/environment reference/procedure/resource composition, full case/fixture/expectation/alias/registry artifact bytes and complete reservation before issuing the original prepared handle | Cross-artifact and original digest/parser/schema/method/observer independence admission pass; invalid input and cancellation before claim have zero native effects; copied handles/recovery strings cannot mint prepared authority |
| C3 original run claim and setup | Claim the original preparation at most once, acquire only its admitted isolated environment, verify actual native tuple, perform registered setup and compare full independent starting inventory | Native drift/unsupported capabilities record complete honest not-run inventory; failed/interrupted acquisition retains original recovery and cleanup evidence; setup mismatch cannot become replacement fixtures or skipped correctness |
| C4 registered operation and observation | Dispatch exact method arguments through existing capability/executor procedures, preserve business versus execution result layers, observe all normative surfaces at original transaction boundaries | No arbitrary SQL/import/callback from case content; unknown methods/profiles and invalid scope generations refuse before dependent effects; savepoint/callback return never proves commit; absent observer leaves the case unverified |
| C5 identity construction and comparison | Bind only original eligible typed result/setup occurrences, resolve aliases in exact registered input slots, validate the complete unchanged public wire and compare native invariants before normalization | Literal data stays exact; forward/rebound/unknown/rolled-back bindings, substituted namespace/profile and wrong endpoint/order/multiplicity fail; exact large IDs never pass through host-number conversion |
| C6 evidence settlement and assess | Preserve every required case and actual result/state/journal/report/performance verdict, original partial progress, termination and cleanup; emit immutable receipt and invoke separately bound assessor | A recorded run is not automatically qualified; omitted/not-run/interrupted cases, unavailable observers, malformed evidence and altered original pins cannot produce qualified; later reruns receive distinct evidence identities |
| C7 independent interchange | Run TypeScript writer/Python reader and Python writer/TypeScript reader against each direction's actual committed database state using the original writer's bindings | Readers inspect the same original state; no fixture replacement, shared writer serialization oracle or agreement-only correctness; Python ownership decision and independent packed-consumer/native evidence remain explicit gates |

Administrative and lifecycle/configuration operations belong to the same
complete required registry where selected. The twenty-two capability return
carriers do not establish that broader inventory. Keep pending traversal and
catalog-concurrency choices as original profile gates; the harness cannot pick
their behavior from an implementation's favorable result. The Python package
ownership decision does not prevent constructing language-neutral packets, but
it prevents claiming the supported Python delivery route settled.

## Performance expectation integration for C2/C4/C6

The separate [draft 0.2 expectation envelope](../02-design/contracts/conformance-case-expected-v0.2.proposal.schema.json)
requires an explicit performance surface. The original 0.1 envelope remains
unchanged and refuses that member. C2 selects one original registered grammar
version; it must not silently strip performance, downgrade the envelope or infer
an empty required inventory from an empty expected array. The private helpers
now compare the fifth surface, but original grammar/observer registration and
runtime execution remain unimplemented.

| Slice | Required performance handoff | Independent refusal/control |
| --- | --- | --- |
| C2 preparation | Resolve complete original benchmark packet and expectation artifact: workload, statistic/threshold, repetitions, strata, baseline procedure, timing boundaries and sample-admission rules. Derive required performance keys from registered procedures. Reserve complete workload, sample, observer and evidence-store resources before claim. | Missing or unsupported packet/profile, omitted performance, substituted behavioral result, changed baseline or unfrozen human statistic choice cannot issue a prepared benchmark handle. A nonperformance case explicitly has no required performance keys. |
| C4 observation | Execute only the frozen workload and registered observer. Retain raw samples with original case/step/boundary, repetition/stratum and actual native outcome correspondence; keep baseline and candidate observations distinct. | Cancellation, failed work, missing samples, exhausted observation budget and unavailable clock/source remain explicit incomplete observations. Do not replace samples, reduce repetitions, change workload or discard slow observations to obtain a passing statistic. |
| C6 assessment | Resolve the original complete expected packet and actual immutable sample artifacts, admit sample membership using the frozen rules, and independently apply its selected comparator. Preserve performance and behavioral verdicts separately in complete case evidence. | A behavioral pass, a summary without required raw samples or an aggregate derived from an incomplete set cannot qualify performance. A recorded partial run remains partial; a rerun receives distinct evidence identity rather than filling gaps in the original run. |

Author red controls before the runner: remove one required repetition, duplicate
another, swap baseline/candidate identities, change a stratum or timing boundary,
retain an actual failed/cancelled operation with a timing value, and substitute a
precomputed favorable summary for the original samples. The frozen profile decides
whether a failed operation is an admitted measured outcome; the assessor cannot
make that choice after inspecting results. Include a complete independent positive
packet and explicit no-performance case. Native plans, clock validity, isolation,
managed-target execution and sample collection remain later qualification evidence.
Pending pooler statistic and concurrency choices stay pending; this handoff supplies
no threshold or default answer to those product questions.

## Original lifecycle and containment

Keep prepareRun, run, abandonPreparedRun and reconcileRun under their existing
issuer/custody contract. Preparation does not acquire native resources. Run
cannot accept a replacement request or remint a preparation after an unknown
claim. Abandonment closes only still-prepared work; it cannot free a claimed
native operation. Reconciliation observes the original run and returns its
actual prepared/abandoned/recorded/interrupted state without replaying cases.
Separate case result, execution outcome, native termination and evidence-store
settlement. Unknown native work or cleanup retains custody across caller loss,
deadline and disposal; cancellation delivery alone never establishes rollback.

Resolve scope and cancellation references through original trusted harness
registration, not JSON-shaped handles. Security-read, subject/principal,
verified-application and publication procedures remain under their owners.
The latest security working-source review is component input only; host method
shape and matching profile strings cannot confer native authority. Reserve the
complete parser/copy/constructed-input/observer/archive and recovery budget
under the existing selected resource contract, including simultaneous copies;
do not infer a heap bound from individual schema maxima.

## Red-first execution packet

### Shared security correspondence fixture boundary

Read-only coordination with “Assess security control support” on 2026-10-09
(thread 01a11b8b-06bb-7091-a11a-b7eba0a432eb, revision 12) reports an active
Staff/Project graph-selector correspondence harness using qualified Relationships
and directed endpoints. Its authored semantic fixture is distinct from evidence
about Truss's physical representation. This observation selects neither an
owner API nor a native Truss security profile.

C4/C7 should consume the owner's eventual original fixture and independently
specified semantic expectations rather than author another policy resolver or
compiler oracle. Truss's separate packet must map each qualified entity/key,
relationship direction and participant to its admitted actual native storage
under one protected cut, then compare actual allowed/denied/disclosed results.
Include reversed endpoints, equal local names in distinct qualified owners,
empty associations, current-principal change and unavailable source collection.
An empty projected graph cannot bypass metadata/authority admission. Owner
logical agreement alone cannot qualify the mapping, current native facts,
compiled enforcement or host publication; each needs its original observation.
Do not copy the owner's working fixture into a release until its source/profile
and complete expectations are published and admitted. These integration cases
remain `not_run` and preserve security interpretation/lowering ownership.

The owner's revision-13 continuation now drafts policy 0.2.0. Read-only source
inspection of `docs/helix/02-design/spikes/security/policy-v0.2.schema.json`
confirms its title explicitly excludes public admission; `exists.association`
distinguishes full Record references from qualified Relationship references
using relationshipId. This changes a candidate source meaning, not Truss's
selected compiler/security registration. Existing policy 0.1 and Weft's draft
security request must not inherit 0.2 support by matching a local identifier.

Before adoption, C2/C4 require owner-supplied original transition/source artifacts
and independent cases for preserved 0.1 content, explicit 0.2 relationship
selection, ambiguous/mixed reference kinds, unknown required semantics and
unsupported compiler/backend interpretation. Preserve complete authored unknown
content and the owner's loss/incomplete report; never strip a relationship
selector, rewrite it to a Record or fallback to an older policy to obtain SQL.
Unsupported selected meaning refuses before native execution. Positive lowering
and native enforcement remain independently qualified against the same original
versioned source/profile. No policy migration implementation belongs in Truss.

Before C3 native work, assemble one immutable independent case packet for each
required operation/boundary family plus the selected full corpus manifest.
Include forbidden overload results, wrong input/result profile, changed native
tuple, copied prepared handle, duplicate run claim, setup mismatch, missing
observer, false committed boundary, rejected-result alias, forward alias,
rolled-back scope, wrong current authority, omitted case, malformed receipt
and interrupted cleanup. Preserve deliberately failing fixtures and raw
observations. An independent implementer must review the packet without
importing writer helpers and record contract ambiguities before qualification.

The current shape/link/arithmetic/substitution scripts are reproducible design
witnesses for C1/C2/C4/C5/C6 constraints. They are not host services or proof of
native scope, authority, observer independence, resource containment or C7
interchange. Do not replace any native exit above with their green output.
Package exports, original runtime/driver/target tuples and actual runner
commands are selected and pinned during implementation; no command pointing
to absent harness files is a current executable success claim.

## C3/C6 interrupted-operation and evidence-store settlement packet

Runner implementation must track native outcome and immutable evidence-store
settlement separately. A completed database operation followed by an interrupted
evidence write cannot become an unexecuted case eligible for automatic rerun.
The original claim, actual operation/input/namespace and retained raw observation
remain bound to the original run. The registered evidence-store procedure must
reconcile the same original evidence identity and full bytes before any repeated
write; it may not regenerate observations from later database state.

| Fault boundary | Required preserved disposition | Independent continuation control |
| --- | --- | --- |
| Before original run claim | Preparation remains prepared or actually abandoned; no native acquisition | Observe claim registry and environment independently; cancellation does not invent a claim. |
| After claim, before acquired-environment acknowledgment | Original acquisition may be unknown; retain exact recovery and resource custody | Reconcile the same acquisition identity; no second environment or duplicate setup until original settlement is admitted. |
| After case operation dispatch, before native outcome | Operation remains unknown even if callback/process/transport ended | Resolve original transaction/attempt through registered recovery; no operation replay merely to obtain a result. Unexecuted dependent cases remain explicitly not_run. |
| After confirmed native outcome, before complete observers | Preserve actual commit/rollback independently from unavailable case verification | Missing original-cut observations keep the case unverified. Later current-state reads cannot impersonate its original boundary. |
| After complete raw observations, before evidence-store acknowledgment | Preserve original full observations and native settlement; evidence persistence is separately unknown | Reconcile original immutable evidence identity/bytes. A timeout cannot authorize another operation, changed evidence or a second run claim. |
| After evidence commit, before assessor delivery | Original receipt is recorded; qualification remains unavailable until admitted assessment | Re-read exact original receipt and invoke only the separately registered assessment protocol; runner success cannot self-qualify. |

Freeze independent expected claim/environment/attempt/evidence inventories for
these boundaries before adding faults. For each boundary, terminate the actual
runner process or interrupt the selected transport after an independently
observed dispatch barrier; a thrown mock callback alone cannot establish native
uncertainty. Keep fault-induced process/session handles and inspect their real
terminal state before reconciliation, preserving live original work when an
observation merely times out. Repeated reconciliation must not issue setup,
mutation, COMMIT, rollback or cleanup beyond the original registered recovery
procedure. Compare complete original graph/history/receipt/feed inventories,
claim count, environment identity and immutable evidence bytes after settlement.

Inject an evidence-store identity collision with different complete bytes and
require integrity refusal, not overwrite or a qualified receipt. Inject partial
receipt storage and independently show no complete recorded result is admitted.
A fresh explicitly requested rerun uses a new claim/evidence identity and its
own original environment/expectations; it preserves the failed run's partial
inventory and cannot fill that historical run's not_run cases. These are planned
C3/C6 native/service controls; evidence storage, recovery procedures and the
actual host services remain to select and implement.


The [migration inspection contract walkthrough](../03-test/migration-inspection-contract-walkthrough.proposal.md)
now gives C4 an explicit administrative example: original registered request,
complete independent starting inventory, same-version native drift, unavailable
observation and no-effects comparison. It uses the actual draft status/verify
methods and direct result schemas, preserving original historical reconciliation
as a separate operation. Like the lookup/group walkthroughs, this is author
case design; independent implementer review and real service/native execution
remain required.
