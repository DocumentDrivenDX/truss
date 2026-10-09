# Language-neutral conformance case grammar — proposal 0.1

## Combined carrier verification — 2026-10-09

The [fresh combined schema receipt](../04-build/evidence/design-audit/schema-inventory-conformance-2026-10-09.json)
records 147 top-level contract schemas with unique IDs, resolved references and
strict Draft 2020-12 compilation, including the input, expected, fixture,
identity-path and nested lookup-outcome proposals. The earlier 135-schema
receipt is preserved. Reproduction accepts a separate output receipt path:
`bun docs/helix/04-build/evidence/design-audit/check-schema-inventory.ts <installed-Ajv-2020-module-path> <new-receipt-path>`.

The focused input/expected/fixture/path/outcome checks pass 8/11/8/10/8 controls,
and the cross-artifact comparator passes eighteen controls. This establishes
carrier reference integration and the enumerated shape/link witnesses only.
Complete executable operation/profile registration, original artifact custody,
independent fixtures and observers, native scope/authority/resource admission,
and the contract-only independent implementer review remain required. A
compiled complete schema set is not a complete passing conformance corpus.

This proposal supplies interpretation rules for the existing conformance manifest's fixtures, inputs, expected and identityAliases artifacts. It does not replace that manifest, define new public Truss operations or certify a passing corpus. CONTRACT-004/011 remain governing; US-027/028 require independent fixtures and an implementer walkthrough. A closed machine-readable encoding and actual adapter registration remain follow-up outputs.

## Artifact roles

The [fixture envelope](../02-design/contracts/conformance-case-fixtures-v0.1.proposal.schema.json)
requires original installation, catalog, configuration, authority, resource,
setup and starting-inventory profile pins. Its `startingInventory` is the
independently authored full expected state at the boundary after setup and
before the first input step. It must explicitly describe applicable empty
surfaces; absent content is not evidence of emptiness. `steps: []` means no
setup operations, not an empty database. Setup uses the same registered step
encoding as inputs, with a separate label inventory. Operation-result alias
indexes refer to input steps; setup aliases resolve against the admitted setup
result tree under the selected setup profile. Starting inventory comparison
must pass before input effects; a mismatch records setup failure, not a case
pass or replacement fixture. Pins and byte shapes alone do not prove any of
these semantic obligations.

Run `bun docs/helix/04-build/evidence/design-audit/check-conformance-case-fixtures.ts <installed-Ajv-2020-module-path>`.
Eight shape controls check explicit no-setup, required state/authority and
refusal of executable/credential members. Exact artifact custody, complete
starting-state semantics and actual native setup remain separate required
outputs.

Every case's original procedure profile resolves exactly one grammar version before any effects. Decode complete exact artifact bytes under the registered bounded parser; unknown required grammar refuses the case, not a not-applicable pass. Artifact resolution never fetches arbitrary network content or chooses executable imports.

| Manifest artifact | Required interpretation |
| --- | --- |
| fixtures | Ordered setup steps, complete independently authored starting inventory and original installation/catalog/configuration/role/resource profiles. Setup labels are references, not credentials or database authority. |
| inputs | Ordered operation steps with unique step label, operation-family discriminator, exact existing input wire/profile, transaction scope reference and declared observation boundaries. |
| expected | Mandatory result, state, journal and report sections. Each contains explicit observation expectations or an explicitly empty complete inventory. Optional SQL section is always informative. No omitted section means empty. |
| identityAliases | Existing typed alias wire. Setup/result pointers resolve only in the selected operation/surface identity-path grammar. |

Expected sections identify the observation boundary by step label and original transaction outcome. State covers complete canonical and applicable derived/reservation/source/request effects for the case's selected operation profile. Journal covers original transaction grouping, event/order/version/payload/origin and completeness witnesses. Report covers complete applicable acceptance/import/enforcement/support output, including explicit absence when the operation emits none. The profile independently declares which report kind applies; the observed implementation cannot choose a smaller scope after execution.

Before execution, derive the required `(surface, step, boundary)` inventory from
the original registered operation, scope and observation procedures. Compare it
exactly with the expected artifact's observation keys: missing, extra or duplicate
keys refuse preparation. Do not derive requirements from the claimant's expected
arrays or from what the implementation happens to emit. The original procedures
must enumerate required success, rejection, rollback and uncertain-outcome
boundaries for the selected case; runtime outcome admission selects the applicable
branch without erasing its required observations.

An expected empty journal or report inventory is an independently authored empty
value artifact at a required observation key, compared with a complete native
observation. It is not an empty `observations` array. An empty observation array
is allowed only when the independently registered procedure explicitly requires
no observation on that surface for this case. The coverage check does not prove
observer provenance, native boundary truth, inventory completeness or comparison
success; those remain separate preparation and execution obligations.

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

### Selected identity-path grammar and alias references

The [identity-path schema](../02-design/contracts/conformance-identity-paths-v0.1.proposal.schema.json)
closes each declaration's operation discriminator, surface/profile, exact
pointer, namespace, identity profile and alias-eligible entity kind. Its
registry artifact must match the original selected operation registry. The
existing alias artifact's `identityPathGrammar` pin resolves this registered
path artifact under the selected grammar; it is not an arbitrary file lookup.
Semantic admission rejects duplicate operation/surface/profile/pointer tuples
even when the competing entries have different namespaces. The declared
namespace kind/profile must match the original alias namespace basis.
An explicitly empty entries list supports only a case with no eligible
identity occurrences or alias uses, established independently; it cannot
erase required generated identities. Non-alias identity domains such as
journal sequences retain their exact native comparisons outside this schema.

Run `bun docs/helix/04-build/evidence/design-audit/check-conformance-identity-paths.ts <installed-Ajv-2020-module-path>`.
Ten shape controls include escaped pointers, missing profiles/namespaces and
closed entity kinds. `/*` is a syntactically valid pointer to a literal member
named `*`; it never means wildcard. Duplicate path entries and actual identity
eligibility remain semantic refusal obligations. These controls do not qualify
the complete registered path inventory or a native comparator.

Run `bun docs/helix/04-build/evidence/design-audit/check-conformance-identity-links.ts`
for nineteen synthetic declaration/binding controls. The comparator checks
unique namespaces/symbols/occurrences, exact kind/profile/source-basis links,
registered setup/result pointers, explicit eligible-surface projections and
exact string identities. Pointer resolution preserves escaped members and
object-versus-array index meaning; profile object-member ordering cannot hide
a duplicate occurrence. Result indexes are parsed exactly and bounded by the
original result array before conversion to a host index. No alias spelling is
used to infer allocation order or identity equality.

The surface eligibility flag and namespace basis in these witnesses represent
already-admitted harness observations, not fields callers can submit to obtain
authority. Native identity-domain validation, original issuer custody,
transaction generation/rollback/visibility and equality/inequality/order checks
remain independent prerequisites. This comparator does not implement input
alias substitution or prove a complete native binding inventory.

The existing `conformance-aliases-v0.1.proposal.schema.json` supplies binding
declarations, not a path registry or substitution algorithm. Its
`operationIndex` is the zero-based position in the original ordered input steps,
parsed as an exact unsigned decimal integer; never a JavaScript floating-point
number. A setup pointer resolves against the complete admitted setup result,
and an operation-result pointer resolves against that step's entire public
result wire. It does not resolve against a runner-created projection. Failed or
unavailable outcomes bind nothing unless the registered result contract
explicitly declares the referenced identity present and eligible.

Each registered identity-path entry selects one operation, input/result or
expected observation surface, exact profile pin, RFC 6901 pointer and namespace
identity. Pointers are exact occurrences: no wildcard, recursive descent,
field-name heuristic or substring match. Array indexes use their canonical
unsigned decimal spelling and must resolve within the actual array. Decode
`~1` and `~0` once; distinguish an object member named `0` from array index zero
using the resolved container. Missing members and out-of-range indexes refuse
resolution. Paths into ordinary property payloads are ineligible even when the
value looks like an ID. A variable-length surface requires its registered
procedure to enumerate concrete eligible paths before comparison; the observed
writer cannot define that enumeration.

For this case grammar, an alias reference is the closed object
`{"identityAlias":"$a"}` in a registered identity slot of the case's input or
expected artifact. The adapter resolves input references into the unchanged
existing public wire before invocation. In an expected artifact it resolves
them to the original bound identity for comparison. The string `"$a"` remains
literal data everywhere. The reference object is not interpreted outside
registered identity slots, including inside JSON-valued properties. A
reference's symbol and namespace must match exactly one admitted declaration
and path entry. Duplicate symbols, duplicate namespace identities, unknown
namespaces and a binding whose identity kind/profile differs from its path
entry refuse the case before dependent effects.

Bindings become usable only after the original setup/result and applicable
pending or committed boundary have been independently admitted. Preserve the
binding's original scope generation and transaction outcome. A rolled-back
pending allocation cannot supply a later committed identity; cross-scope use
requires the selected operation contract's committed visibility, not a reused
scope label. Aliases are comparison aids and do not authorize access or retry.
Two aliases resolving to the same identity must still satisfy the case's
independent equality/inequality requirements; normalization cannot turn an
actual collision into distinct symbols.

Run `bun docs/helix/04-build/evidence/design-audit/check-conformance-alias-substitution.ts`
for seventeen synthetic substitution controls over registered non-root public
identity slots. The procedure copies original input, replaces only a closed
reference object at a selected slot, and preserves literal strings and
alias-shaped JSON outside those slots. Input mutation, forward references,
unknown symbols, wrong namespaces, rolled-back/unknown bindings, ended scopes
and changed pending scope generations refuse. Committed cross-scope use still
requires independently admitted visibility. The exact identity remains string
data, including values beyond the JavaScript safe-integer range.

These fixtures supply admitted binding/scope projections, not native proof.
The actual runner must obtain those facts through original issuer/namespace
and transaction procedures, reserve complete parse/copy/constructed-wire
capacity before substitution, and validate the whole constructed public wire
under the exact registered schema and semantic profile before invocation.
Literal `$a` in an identity slot remains literal and may fail that domain's
native validation; it is never silently interpreted as an alias. Root identity
inputs, if a selected original method permits them, require a separately
registered root construction procedure rather than truncation or fallback.
This witness does not qualify a complete production runner or native authority.

Required independent controls include an escaped member pointer, an object
member named `0`, a missing array index, a literal `$a` property, an alias-shaped
JSON property that remains unchanged, a result binding from a rejected step,
a forward input reference and a rolled-back pending binding used after commit
of another scope. These supplement the earlier grammar controls; they remain
unexecuted until the closed path registry and runner are implemented.

Each surface expectation selects its exact comparator/profile and complete observation boundary. Compare ordered operation results and journal/feed semantic order as sequences. A collection is order-insensitive only when its declared contract says so; compare full membership and multiplicity, never just counts or hashes. Exact source/numeric token/presence/definition content stays exact under its governing codec. JSON object-member ordering may follow the selected canonical grammar; it cannot erase absent versus null or normalize decimal spellings where lexical custody is required.

Diagnostic expectations compare the governing severity/code/path multiset with multiplicity; message text is informative unless the selected contract explicitly makes it normative. Expected failure names the actual permitted error family and required unchanged/rolled-back/unknown state. Resource or executor failure cannot stand in for a planned semantic rejection. Every required expectation must be checked; one unavailable observer makes that case unverified, not passed from its other surfaces.

## Adapter handshake and original execution

The [missing-object lookup walkthrough](direct-lookup-contract-walkthrough.proposal.md)
applies these rules to the actual direct-read and executor declarations,
including nested execution/business results, adopted termination and complete
unchanged state/journal/report observations. It is an author review and
implementation handoff, not the required independent implementer review or a
passing native case. Exact semantic fixture/schema/observer registration
remains required before execution.

Before effects the trusted runner admits exact implementation/build, operation registry/corpus/contract, native target/layout, selected capabilities, observer independence, transport/executor, authority, resource and cleanup profiles. Adapter reports supported registered operations; missing mandatory operation refuses full-profile qualification. It cannot supply expected fixtures, revise required surfaces or nominate an observer that shares writer serialization without disclosed independence review.

Each invocation records original case/worker/step/scope/attempt, complete constructed input and actual outcome/termination evidence. No automatic replay hides failures. Original partial progress and unresolved cleanup retain recovery custody under CONTRACT-011. Interchange retains writer's original committed alias bindings and has the independently admitted other reader inspect that same actual state; reverse direction uses fresh isolated setup.

## Required grammar controls

### Handshake placement and admission result

Use the existing `HostConformanceRunner.prepareRun` / `run` lifecycle in
`truss-conformance-tooling-v0.1.d.ts`; do not add a second public start or
registration API. The handshake is an admission procedure selected by the
original composition and procedure profiles, not an implementation-supplied
callback or executable corpus artifact.

During preparation, resolve the complete original manifest, input inventory,
case grammar, operation registry, aliases and independently authored expected
artifacts. Verify their exact bytes and cross-artifact membership. Admit the
configured adapter's exact build, declared operation/profile map, observer
procedures, environment reference, cleanup/recovery custody and complete
resource reservation. This is configuration/artifact admission only:
`prepareRun` must not open a native connection, create an environment or execute
a case to discover capabilities. A copied prepared handle cannot substitute
for original runner issuance.

After the original at-most-once run claim, obtain the native environment under
that admitted reference and verify its actual layout, installation, server,
authority and capability tuple before setup effects. Record declared support
and actual admitted availability separately. A same-named adapter operation
with a changed profile hash, legacy feed wire, wrong transaction ownership or
missing observer is not compatible. Drift cannot be repaired by changing the
required manifest or switching profiles during the run.

Required case membership is fixed by the original manifest. Missing mandatory
capabilities prevent full qualification; the runner may produce an honest
diagnostic receipt with affected cases not run under CONTRACT-011, retaining
the complete required inventory and reason. It cannot relabel them optional,
skip their normative surfaces or pass from the remaining cases. An invalid
artifact/registration prevents preparation; a native incompatibility found
after claim retains original run and cleanup evidence. Interrupted acquisition
or uncertain cleanup follows the existing interrupted/reconciliation path,
rather than returning a fresh preparation or assuming no effects.

The independent handshake controls must cover changed adapter build/profile,
missing required operation, missing observer, observer sharing the writer's
serialization without admitted independence, copied prepared handle, native
drift after preparation, acquisition interrupted after claim and a diagnostic
receipt that attempts to omit not-run cases. Run each admission refusal against
an effect counter to prove preparation performed no native work. Native drift,
acquisition and cleanup controls additionally need the actual selected native
procedure; a mock counter cannot qualify those boundaries. These remain
implementation/test outputs, not executed evidence.

The eventual schema/parser/runner must refuse missing normative sections, duplicate step labels, unknown mandatory operation, unsupported input wire, out-of-scope transaction reference, alias pointing into literal data, forward/rebound alias and omitted required observation. Independent controls must preserve literal "$a", distinguish absent/null, retain duplicate diagnostics, detect wrong endpoint despite equal final counts, reject hidden partial inventories and prohibit informative SQL mismatch from overriding normative success/failure. A selected empty report inventory is distinct from a missing report section.

These are design controls, not executed tests. Closeout requires a complete closed registry/encoding, independently authored complete cases, red controls and a contract-only walkthrough that identifies remaining behavior gaps. Runtime/native conformance and bidirectional Python interchange remain separate evidence obligations.


The [ordered-input schema](../02-design/contracts/conformance-case-inputs-v0.1.proposal.schema.json) now closes the inputs artifact envelope and step members while retaining exact registered input bytes. Run `bun docs/helix/04-build/evidence/design-audit/check-conformance-case-inputs.ts <installed-Ajv-2020-module-path>` from the repository root. Eight controls cover missing/empty inputs, prohibited executable members and scope shape, with deliberately shape-valid duplicate labels/unknown operations requiring semantic refusal. This is input-envelope evidence only; full fixture/expectation/identity-path grammar and actual registry remain unfinished.

The [expected-observation schema](../02-design/contracts/conformance-case-expected-v0.1.proposal.schema.json) now requires all four normative sections and closes observation step/boundary/comparator/artifact fields. Optional SQL must explicitly be nonnormative. Run `bun docs/helix/04-build/evidence/design-audit/check-conformance-case-expected.ts <installed-Ajv-2020-module-path>`; eleven shape controls distinguish explicit empty inventories from omission and reject callback-returned as a durability boundary. Actual empty-surface completeness, boundary truth and comparator custody remain semantic obligations.

Dependency sync for this authoring pass fetched UMF origin/master at 1f7b5f5d2a355c4b476e3a96b289b9048f03f567 and Weft origin/main at 5856c73db0342363e64802905a94abb96209d757; both remain at the previously reviewed heads. No changed owner API was inferred or adopted.

## Cross-artifact admission controls

After closed shape admission and original artifact/registry custody, require matching original case identity across manifest/input/expectation artifacts. Each input step label is unique; each operation resolves uniquely to a registered exact identity/version/hash and permitted scope kind. Non-none scope labels resolve to the original admitted harness scope inventory. Every observation references an existing input step; duplicate surface/step/boundary expectations refuse rather than masking contradictory results. Scope existence is not native liveness: actual original transaction generation, rollback cut and authority must still be admitted at invocation.

Run `bun docs/helix/04-build/evidence/design-audit/check-conformance-case-links.ts`. Eleven independent authored controls cover mismatched case, duplicate labels/registry/boundaries, unknown operation/scope/observation and changed version/hash. The small design comparator assumes shape-admitted inputs and does not resolve artifact bytes, verify live scopes or prove complete observation coverage. It is not a production runner or native acceptance evidence. Full required observation membership and original registry/parser/resource/authority composition remain unfinished.

The comparator now also admits fixture links, bringing the total to eighteen
controls. Fixtures and inputs must share exact registry identity/bytes/digest
and grammar pin, and both must match the manifest case. Setup operations use
registered profiles and admitted scope labels; duplicate setup labels refuse.
Setup and input labels have separate namespaces, so the same spelling may
occur in both, but an expected input observation cannot resolve through a
setup-only label. These checks still assume prior closed shape admission;
matching supplied bytes does not establish digest truth, registered custody or
native starting-state completeness.

The descriptor reconciliation now compares the entry's actual operationProfile
and observationProfile fields and the expectation artifact's grammarProfile,
bringing link controls to twenty. Changed observation-procedure and expected
grammar pins refuse. Operation and observation negative controls replace only
the selected pin object, avoiding shared fixture-object mutation that could
otherwise fail an unrelated grammar check first. This verifies those explicit
links; actual procedure custody and native observation independence remain
required.
