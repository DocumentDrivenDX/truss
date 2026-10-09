# Language-neutral conformance case grammar — proposal 0.1

This proposal supplies interpretation rules for the existing conformance manifest's fixtures, inputs, expected and identityAliases artifacts. It does not replace that manifest, define new public Truss operations or certify a passing corpus. CONTRACT-004/011 remain governing; US-027/028 require independent fixtures and an implementer walkthrough. A closed machine-readable encoding and actual adapter registration remain follow-up outputs.

## Artifact roles

Every case's original procedure profile resolves exactly one grammar version before any effects. Decode complete exact artifact bytes under the registered bounded parser; unknown required grammar refuses the case, not a not-applicable pass. Artifact resolution never fetches arbitrary network content or chooses executable imports.

| Manifest artifact | Required interpretation |
| --- | --- |
| fixtures | Ordered setup steps, complete independently authored starting inventory and original installation/catalog/configuration/role/resource profiles. Setup labels are references, not credentials or database authority. |
| inputs | Ordered operation steps with unique step label, operation-family discriminator, exact existing input wire/profile, transaction scope reference and declared observation boundaries. |
| expected | Mandatory result, state, journal and report sections. Each contains explicit observation expectations or an explicitly empty complete inventory. Optional SQL section is always informative. No omitted section means empty. |
| identityAliases | Existing typed alias wire. Setup/result pointers resolve only in the selected operation/surface identity-path grammar. |

Expected sections identify the observation boundary by step label and original transaction outcome. State covers complete canonical and applicable derived/reservation/source/request effects for the case's selected operation profile. Journal covers original transaction grouping, event/order/version/payload/origin and completeness witnesses. Report covers complete applicable acceptance/import/enforcement/support output, including explicit absence when the operation emits none. The profile independently declares which report kind applies; the observed implementation cannot choose a smaller scope after execution.

## Operation and scope grammar

Each step invokes one registered contract operation, not SQL text or arbitrary callback code. The operation registry maps its discriminator to the exact existing input/result schema and semantic contract revision, required capability, observation surfaces and identity paths. The registry is an original trusted procedure artifact selected by the host; input cannot register an implementation.

Required families are catalog acceptance/enumeration; object/edge mutation; atomic group; request-bearing group replay; import; direct object/key/page reads; provenance/history; feed/checkpoint/freshness; installation/status/migration; and host transaction control. Family names here are grammar categories, not newly invented method names. A full registry must enumerate actual selected methods and wire versions, including unavailable profiles, before claiming execution readiness.

Host transaction steps explicitly begin, establish an earlier savepoint, commit, roll back or roll back to a declared savepoint under the trusted harness profile. They operate on harness-owned original scope handles. Truss operation steps reference owned or adopted scope separately; an adopted operation cannot end the host scope. Original live scope identity and generation are retained through each step. Scope ended or rolled back cannot be resurrected by reusing its label. Pending expectations are observed in that live scope; committed expectations require independent confirmed termination. Commit-unknown is an explicit recovery observation, never inferred rollback or success.

Concurrent cases use declared workers and named barriers in the trusted procedure, with explicit observed native conditions. A launch timestamp or sleep does not prove lock acquisition, commit visibility or watermark state. Barrier semantics and cleanup belong to the exact procedure profile; corpus strings cannot execute arbitrary host code. Single-worker sequential cases preserve submitted operation order.

## Identity paths and allocation bindings

The registry declares each identity occurrence by operation/surface and exact structural path, native identity kind and original namespace basis. Declaration is semantic: a field named id is not sufficient. Object/edge IDs, catalog type/property/key/revision identities, journal xid/sequence and feed source epoch/position retain their different domains. Not every identity is an opaque allocation eligible for alias substitution.

Expected generated identities use declared alias references in the case grammar; submitted literal property values remain ordinary exact data. An alias becomes available only after independently admitted setup or its declared successful result binding. Later steps may use it only in registered identity-input slots. Resolve such references before constructing the existing public input wire, while preserving original case bytes and the binding evidence. No alias object is added to a public API wire and no recursive string replacement is allowed.

Observe and validate required native equality, inequality, exact numeric order, linkage and committed nonreuse before normalization. A rollback gap is permitted where selected; ordering cannot be inferred from alias spelling. Wrong endpoints, duplicate identities, altered epochs and row multiplicity remain failures. Invalid/rejected/unavailable results cannot bind an allocation absent from their admitted result schema. Rebinding or forward references refuse interpretation. Shared namespaces must be independently established, not invented to conceal a collision.

## Expected comparison grammar

Each surface expectation selects its exact comparator/profile and complete observation boundary. Compare ordered operation results and journal/feed semantic order as sequences. A collection is order-insensitive only when its declared contract says so; compare full membership and multiplicity, never just counts or hashes. Exact source/numeric token/presence/definition content stays exact under its governing codec. JSON object-member ordering may follow the selected canonical grammar; it cannot erase absent versus null or normalize decimal spellings where lexical custody is required.

Diagnostic expectations compare the governing severity/code/path multiset with multiplicity; message text is informative unless the selected contract explicitly makes it normative. Expected failure names the actual permitted error family and required unchanged/rolled-back/unknown state. Resource or executor failure cannot stand in for a planned semantic rejection. Every required expectation must be checked; one unavailable observer makes that case unverified, not passed from its other surfaces.

## Adapter handshake and original execution

Before effects the trusted runner admits exact implementation/build, operation registry/corpus/contract, native target/layout, selected capabilities, observer independence, transport/executor, authority, resource and cleanup profiles. Adapter reports supported registered operations; missing mandatory operation refuses full-profile qualification. It cannot supply expected fixtures, revise required surfaces or nominate an observer that shares writer serialization without disclosed independence review.

Each invocation records original case/worker/step/scope/attempt, complete constructed input and actual outcome/termination evidence. No automatic replay hides failures. Original partial progress and unresolved cleanup retain recovery custody under CONTRACT-011. Interchange retains writer's original committed alias bindings and has the independently admitted other reader inspect that same actual state; reverse direction uses fresh isolated setup.

## Required grammar controls

The eventual schema/parser/runner must refuse missing normative sections, duplicate step labels, unknown mandatory operation, unsupported input wire, out-of-scope transaction reference, alias pointing into literal data, forward/rebound alias and omitted required observation. Independent controls must preserve literal "$a", distinguish absent/null, retain duplicate diagnostics, detect wrong endpoint despite equal final counts, reject hidden partial inventories and prohibit informative SQL mismatch from overriding normative success/failure. A selected empty report inventory is distinct from a missing report section.

These are design controls, not executed tests. Closeout requires a complete closed registry/encoding, independently authored complete cases, red controls and a contract-only walkthrough that identifies remaining behavior gaps. Runtime/native conformance and bidirectional Python interchange remain separate evidence obligations.


The [ordered-input schema](../02-design/contracts/conformance-case-inputs-v0.1.proposal.schema.json) now closes the inputs artifact envelope and step members while retaining exact registered input bytes. Run `bun docs/helix/04-build/evidence/design-audit/check-conformance-case-inputs.ts <installed-Ajv-2020-module-path>` from the repository root. Eight controls cover missing/empty inputs, prohibited executable members and scope shape, with deliberately shape-valid duplicate labels/unknown operations requiring semantic refusal. This is input-envelope evidence only; full fixture/expectation/identity-path grammar and actual registry remain unfinished.

The [expected-observation schema](../02-design/contracts/conformance-case-expected-v0.1.proposal.schema.json) now requires all four normative sections and closes observation step/boundary/comparator/artifact fields. Optional SQL must explicitly be nonnormative. Run `bun docs/helix/04-build/evidence/design-audit/check-conformance-case-expected.ts <installed-Ajv-2020-module-path>`; eleven shape controls distinguish explicit empty inventories from omission and reject callback-returned as a durability boundary. Actual empty-surface completeness, boundary truth and comparator custody remain semantic obligations.

Dependency sync for this authoring pass fetched UMF origin/master at 1f7b5f5d2a355c4b476e3a96b289b9048f03f567 and Weft origin/main at 5856c73db0342363e64802905a94abb96209d757; both remain at the previously reviewed heads. No changed owner API was inferred or adopted.
