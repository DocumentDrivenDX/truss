# Truss-owned endpoint-intent representation candidate

Design input for US-002/003 and CONTRACT-003. Status: representation experiment;
not an adopted extension, accepted catalog or change to UMF core relationships.
This uses UMF's existing extension registry, rather than requiring CONTRACT-045
or reinterpreting its future generic reference syntax.

## Existing-owner evidence

The [probe](../../04-build/evidence/design-audit/check-truss-endpoint-intent-extension.ts)
executes committed UMF `1f7b5f5d2a355c4b476e3a96b289b9048f03f567`
`Registry.register` and `validateDocument` on clean archived source. It checks the
complete 1,342-member src/spec tree digest before imports, and retains the
[receipt](../../04-build/evidence/design-audit/truss-endpoint-intent-extension-probe.json).
Five controls pass: a registered document-scoped pending external intent is
valid/complete in the probe's declared extension language; without registration
it is valid but incomplete retained content; an invalid local Record source and
duplicate intent refuse; an unresolved core relationship still refuses unchanged.
The checker passes strict TypeScript. No native execution or Truss acceptance ran.

The extension owns *catalog endpoint intent*. Its external coordinate is data
in that language, not a core reference, resolved Record or instance edge. The
probe's semantic callback establishes local source ownership and intent identity
only. It intentionally does not claim the target exists. Valid/complete extension
validation means that its declared pending-intent syntax and local checks passed;
it does not mean a relationship can execute or any database assertion is enforced.

This supplies concrete evidence that current UMF can represent a Truss-owned
pending intent without fabricated target stubs or invalid-core validation bypass.
It does not supply the complete endpoint/dependency semantics required to close
US-002/003. The small probe schema omits full relationship bounds, keys, lifecycle,
inverse and heterogeneous endpoint sets and must not become a release vocabulary.

## Full candidate meaning and correspondence

The full vocabulary must separate stable declared endpoint lineage from selected
definition content. A lineage names the declaring document, module and element;
a definition selection additionally names the exact original revision/artifact.
Do not put a revision into the stable type identity or treat a bare display name
as a document qualifier. Absence of an exact definition is represented explicitly
as pending intent, never as an invented document, zero revision or resolved Record.

| Required semantic slot | Candidate contract |
| --- | --- |
| Intent identity and provenance | Relationship ID belongs to the referring document/module; retain its exact original payload pointer and bytes. Two documents with equal module/relationship names remain distinct under the pending catalog-ownership decision; no physical identity is assigned by this extension |
| Declared dependencies | Distinguish required exact document/revision selections from endpoint-only pending intent. Missing required dependency refuses package admission before unknown policy. A declared pending endpoint is not permission to fetch a document or substitute an incidental package member |
| Endpoint sets | Preserve all source/target alternatives with exact qualified lineage and separate definition selection. A valid local endpoint still resolves through the original UMF Record producer. External resolution uses whole-set or prior accepted custody, not global module/element search. Duplicate/conflicting alternatives refuse before endpoint cross-product derivation |
| Target keys | Retain whether a key is explicitly selected, explicitly absent under the admitted relation profile, or unresolved with its target definition. Resolve named keys only on their exact original owning Record. A provisional type has no invented key/property; unresolved key intent cannot produce a key number, key guarantee or identity-based import |
| Direction, bounds and lifecycle | Retain every declared source/target bound, directed/undirected meaning, ownership/composition intent, inverse and association Record correspondence. The extension owns their pending-intent meaning; core declaration APIs still require their own valid local targets. Unsupported required modifiers block complete derivation rather than receiving default behavior |
| Interpretation and enforcement | The original support/report procedure distinguishes validated intent, resolved model meaning and actual engine/database enforcement. Unknown registered-version content remains retained and cannot drive required semantics. Validation completeness is not a resolved endpoint or an enforcement claim |

The complete producer emits original source-qualified intents and dependencies
before allocation. A separate resolver classifies each target as an exact supplied
definition, exact previously accepted definition, valid pending lineage, conflicting
selection or unavailable interpretation. Preserve complete source membership and
all classifications; a resolved prefix cannot become an accepted relationship set.
Only the first two categories supply authoritative Record/key definitions. A valid
pending lineage can enter the existing unknown-policy path after original caller,
namespace and lifecycle admission. Claimed target coordinates alone confer no
target-owner grant or authority; consume the security owner's endpoint-owner
admission rather than introducing an extension-local policy resolver.

Under provisional policy, US-003-AC2 still requires both the stable placeholder
type and derived relationship, including complete endpoint membership and retained
intent. It is not satisfied by archiving an unresolved note. The selected native
mapping must represent the relationship's actual admitted state without invented
key rows; operations requiring unresolved key/value meaning remain unavailable.
Whether that full state fits the selected native tuple is an E4 composition exit,
not a reason to weaken the criterion. Under skip, omit the entire relationship and
retain explicit source-qualified loss. Under reject, collect every valid unresolved
endpoint/relationship diagnostic without any placeholder or positive revision.

Later definition admission resolves the same qualified lineage under the original
accepted source/definition mapping. It cannot silently choose a newer revision
than an explicitly selected one. Preserve type ID and creation provenance while
recording the actual new definition source separately. Recompute the complete
dependent relationship/key/retained-data and assertion inventory before publication.
Unchanged display names, matching numeric IDs or a newly nonprovisional flag do
not establish that correspondence. If native storage, definition compatibility or
security admission is unavailable, refuse the whole transition with prior accepted
state intact under the existing containment/recovery protocol.

Independent E1/E3/E4/E5 packets must cover required-missing dependency versus valid
pending endpoint, same names under different owners, mutual dependencies, wrong
revision, conflicting target keys, heterogeneous endpoint omission, unsupported
required modifier, duplicate intent, whole-relationship skip, provisional complete
derivation, and later same-ID definition with changed retained-data meaning. The
original invalid-core control remains required alongside every positive extension
case. No probe or packet assumes the pending catalog-ownership answer.

## Provisional storage and complete-report handoff

The existing reviewed storage declares `rel_endpoint` as the complete
`(rel_type_id, source_type, target_type)` membership, while `rel_def.target_key`
is nullable text. These declarations can represent typed endpoint membership;
they do not distinguish an explicitly absent key from an unresolved key selection
or establish heterogeneous target-key meaning. Consume the full original intent
and registered interpretation alongside native columns. A SQL NULL target_key
cannot turn unresolved required key semantics into an admitted key-free relation.
If the complete selected mapping needs additional storage, compose it through
the authoritative UMF physical model and CH-01; do not introduce a runtime
side table, implicit ALTER or alternate catalog outside installation inventory.

E4's provisional producer must independently compare all of the following before
report/head finalization:

- Every distinct valid unresolved lineage has exactly one admitted provisional
  type, no authored properties/keys and no invented definition source. Retained
  instance content remains exact under the selected provisional storage profile.
- Every non-skipped intent has its actual derived relationship and complete
  source/target endpoint cross-product. All original bounds/direction/lifecycle
  and key interpretation match the retained source, including explicitly
  unavailable operations; typed FK success proves only its structural scope.
- Each full report `provisional` member refers to the actual type and its complete
  `via` relationship inventory. Repeated references to one type do not multiply
  the type count; omitting one surviving referring relationship fails completeness.
- Skip creates no relationship/endpoints for the skipped intent and emits the
  existing `losses` carrier with original source, exact pointer, registered loss
  profile and complete loss artifact. An empty relationship count or retained
  source alone does not prove explicit skip reporting.

Retiring or skipping the last referring relationship does not silently define,
delete or recycle its placeholder. Preserve the original type identity and any
retained objects/recovery obligations. Continue reporting an active provisional
type; its complete `via` may be empty only after independently proving no active
referring relationships remain. An explicit type retirement still follows the
selected original lifecycle/data-preservation procedure and admitted owner scope.
An orphan is not permission to invent an authoritative target document or apply
an implicit cleanup policy. Later legitimate definition can claim the preserved
lineage under the same promotion checks, rather than allocating a fresh type.

Independent cases seed two relationships to one unknown and another same-name
unknown under a different declared owner. Compare actual counts, complete typed
endpoints and full report references, then retire one relationship and later the
last. Retain objects for the orphan and verify continued reporting and stable
later promotion. Separately alter only target-key interpretation while preserving
the same nullable native cell: complete source/profile correspondence must refuse
the substitution. Fail after placeholder/relationship allocation and before full
report insertion; confirmed rollback removes all new effects and preserves the
prior orphan/data state. Unknown commit follows original acceptance recovery.

These are E4/E5 design obligations, not native results. The existing report wire
already has `provisional`/`via` and source-qualified `losses`; use those carriers
without inventing another report format or treating shape-valid empty arrays as
complete semantic evidence.

## Remaining representation-to-policy handoff

The [full closed carrier schema](truss-endpoint-intent-v0.1.proposal.schema.json)
now authors explicit pending/selected definition selection, original source references,
required dependency declarations, complete endpoint sets and key state, exact
integer-text bounds, direction/lifecycle/composition, inverse and association
Record intent. A pending definition carries an explicit expected revision or
explicit null; it never inherits latest. Selected definition/source fields are
claims requiring original resolution, not a schema-issued resolved capability.

The [shape checker](../../04-build/evidence/design-audit/check-truss-endpoint-intent-shapes.ts)
strictly compiles this schema with the existing acceptance-input artifact schema.
[Thirty-one current controls](../../04-build/evidence/design-audit/truss-endpoint-intent-acyclic-shapes.json)
pass, including missing complete fields, mixed definition states, empty endpoints,
numeric/noncanonical bounds and unknown modifiers. Deliberately shape-valid
reversed bounds, duplicate intent IDs and foreign source references still require
semantic/original-byte refusal; their shape acceptance is not support. The checker
uses synthetic source-reference claims and does not establish valid UMF source output.

For full `Registry.register` adoption, retain the original closed schema bytes
and semantic procedure through the existing composition procedure. The minimal
probe's manifest cannot qualify the full carrier's semantic validator. The schema
selects no native range, operation resource limit or automatic storage migration.

### Acyclic source inventory references

The first unadopted full schema embedded exact source artifacts in selected
definitions/dependencies. That is unsuitable for local references or mutually
dependent source documents: embedded self bytes, or reciprocal source digests,
would create circular byte dependencies. The corrected candidate carries only
`sourceReference`, an opaque original source-inventory entry identity. Original
full bytes and verified digest stay in the already admitted acceptance input or
prior accepted archive, outside the referring document. Preserve the earlier
shape/inventory receipts at their original historical scope.

Resolve each reference against the original complete source inventory and require
exact declared document/revision/entry correspondence. Duplicate or ambiguous
entry identities, wrong revision, missing original bytes, changed content and
foreign accepted-source context refuse; reference spelling cannot confer custody
or request external loading. Local selections resolve to their actual containing
source member and its original Truss document revision. External selected targets
and required dependencies resolve to exact supplied or admitted prior members.
Pending selections retain explicit absence without a fabricated source entry.

Logical dependency cycles still use the existing SCC order. Their inner source
documents refer to stable opaque inventory names; the outer admitted inventory
hashes each complete document independently. It does not embed its own bytes in
those documents. Complete membership/definition checks precede graph ordering;
successful reference lookup alone does not establish valid target semantics.

The private `packages/umf-bun/src/catalog-endpoint-source-references.ts` now
implements supplied-source correspondence over the original validated catalog
preparation. It refuses reconstructed preparations, ambiguous inventory names,
wrong document/revision/reference/context and over-limit occurrence lists. Local
and reciprocal supplied references retain the actual archived source artifact,
text and source UMF version rather than transitioned interpretation bytes.
Repeated reference occurrences remain ordered and distinct; they do not dedupe
original membership. Five Bun tests/21 assertions and strict TypeScript pass.

Its scope is `original_supplied_source_reference_correspondence_only`. It accepts
no caller-made accepted archive, resolves no Record/key, validates no extension
meaning and supplies no acceptance authority. Previously accepted sources still
require their original admitted archive/head context and a separate composition
with that resolver; unavailable prior custody refuses without a supplied-source
fallback. Required dependency coverage, full occurrence collection from the
registered carrier and endpoint/lifecycle/namespace admission remain E2–E5 work.
The explicit maximum reference count is an admitted caller profile argument, not
a selected release default or whole-operation allocation proof.

The private `catalog-endpoint-intent-basis.ts` now validates the exact pinned
full candidate schema against original source payloads and collects every
dependency, selected/pending endpoint and association-Record occurrence. It
rejects duplicate dependency selections, qualified intent IDs and endpoint
lineages, undeclared selected external definitions, absent declaring modules and
reversed exact integer-text bounds. Selected references resolve through the
original supplied-source component; pending references retain their full declared
lineage/expected revision without fabricated source members. One explicit bound
counts all reference occurrences across the whole original input.

Six focused tests/18 assertions, together with the five source-reference tests,
pass as eleven tests/39 assertions; both implementation/test pairs pass strict
TypeScript. The positive test explicitly preserves UMF's incomplete validation
status for the unregistered candidate extension. Thus the scope remains
`original_endpoint_intent_shape_and_supplied_source_basis_only`, not registered
endpoint interpretation, prior accepted-source admission, native definition/key
resolution, policy execution or a positive accepted revision. The factory adds
no public export or extension authority. Its current original-source subset is
UMF 0.7; source transition to 0.8 never substitutes the archived source payload.

Reproduce shape controls from the repository root with
`bun docs/helix/04-build/evidence/design-audit/check-truss-endpoint-intent-shapes.ts /absolute/path/to/dependency/package.json`,
using the admitted Ajv2020 dependency package.

The [current combined inventory receipt](../../04-build/evidence/design-audit/schema-inventory-acyclic-endpoints-2026-10-09.json)
strictly registers and compiles all 156 current top-level contract schemas with
zero errors. This adds the endpoint-intent candidate to the prior 155-schema
composition check and corrects the intervening embedded-source candidate; it preserves the earlier receipts and grants no semantic or
runtime qualification.

| Stage | Required authored output and independent exit |
| --- | --- |
| E1 full extension meaning | Independently review the authored full carrier/meaning, admit its original closed schema bundle and register the complete Truss semantic producer. Distinguish declared document dependencies from unresolved endpoint intent; never borrow the probe's minimal coordinate as a complete relation |
| E2 source and package custody | Capture exact original document/revision/bytes and complete supplied or previously accepted membership. A revision string is a selection claim, not authority. Validate core content unchanged and validate registered extension semantics; unregistered content remains retained-only and cannot drive required policy |
| E3 resolution and dependency graph | Resolve qualified definitions and keys through original owner producers and accepted catalog custody. Derive dependency edges only under E1's explicit semantics, then use the existing SCC/byte-order algorithm. Independently test mutual dependencies, permutation invariance, missing/wrong revisions and duplicate membership; do not flatten source documents or resolve bare names globally |
| E4 unknown policy | Apply reject/provisional/skip to valid admitted intents only. Provisional allocation requires complete qualified lineage and absent-definition provenance; skip records exact original source-qualified loss. Multiple equal unknowns share only their admitted identity, and unrelated owners remain distinct. Invalid core input refuses before every branch |
| E5 later definition and publication | Match the authoritative later definition to the original pending lineage, preserve stable type identity, validate/rebind retained data, and publish full lifecycle/report/history effects atomically. Independent occupied-home, changed owner/revision, failed rebind and rollback cases precede activation |

Truss owns the extension's catalog-policy semantics and registered producer.
UMF owns core validation, extension registration and original Record/Field/key
meaning. Weft must separately register any selected extension-derived relation
mapping before compiling it; valid pending content cannot expand its subset.
Security retains original administrative/read/publication admission. This proposal
adds no second compiler, dependency fetcher, authority registry or ACL resolver.

E1–E5 remain design/implementation work. Keep positive cross-document,
provisional/skip/promotion acceptance unavailable until complete original
representation, producer and policy correspondence is admitted. Existing core
relationship behavior and prior invalid-input refusals remain governing.

For reproduction, archive `src`, `spec` and `package.json` from that exact UMF
commit into a clean directory with its admitted dependencies, then run the probe
with the directory path. The checked tree digest refuses changed source members;
the receipt scopes library source correspondence only, not dependency installation
or native security/transport qualification.

### Original supplied Record/key correspondence checkpoint

The private supplied-endpoint resolver now resolves every selected source, target
and association Record against the exact original owning document/module/element
inventory after full source-reference correspondence. Candidate `key.name` selects
the exact authored UMF key `name` within that Record; it does not select the key
`id`, a field, another Record's key or a name in another owner. Missing or ambiguous
name correspondence refuses. The original key object retains its distinct ID,
name, field order and modifiers without claiming native enforcement. Pending
Record/key states retain the complete original intent and do not manufacture a
resolved key. This is a candidate-language clarification, not a change to UMF core.

The combined original-source/graph/Record suite passes 27 tests/604 assertions and
strict TypeScript. It demonstrates source-qualified correspondence only. E1's full
original semantic registration, E3 accepted-history custody and E4/E5 native
provisional/promotion/report effects still remain required; no public activation
or security-owner admission follows from these private results.

The follow-up negative suite passes 30 combined tests/609 assertions. Its decoy
Record owns a distinct Field under original UMF's member-ownership rule; it has
the requested key name while the selected target Record has no key. Resolution
refuses instead of borrowing that key or the same-name key in another document.
A later invalid selected endpoint and an association Field each refuse the complete
result, with no resolved-prefix output. Duplicate authored key names are rejected
by the original UMF validator (`KEY_DUPLICATE_NAME`) before Truss correspondence;
this is not a new Truss override. These remain pure pre-native observations.

### Full document-language registry checkpoint

The [full registry checker](../../04-build/evidence/design-audit/check-truss-endpoint-intent-full-extension.ts)
now registers the complete unchanged candidate schema through committed UMF's
original `Registry.register`. It verifies all 1,342 original src/spec members
before imports, checks the exact schema digest, retains its own checker digest,
and records the [seventeen-control receipt](../../04-build/evidence/design-audit/truss-endpoint-intent-full-extension.json).
Original document bytes remain unchanged in every control. Strict TypeScript passes.
The earlier five-control minimal-probe receipt remains historical evidence.

Its semantic callback validates declaring module and qualified intent identity,
exact lower/upper-bound ordering, endpoint-set lineage uniqueness, unique required
dependency selections and external selected endpoint/dependency correspondence.
Local selected source/target/association endpoints require original Records;
selected local keys match the owning Record's exact authored key name. Invalid
core relationships still refuse unchanged. Unsupported full-carrier shape refuses
in the original registry's schema validator before this callback.

The registered language explicitly describes external coordinates as intent.
A declared external selection can therefore be valid/complete in this document
language without being a present or accepted package definition. The required
source-inventory resolver still refuses missing/wrong document/revision/reference
membership before acceptance; registration does not waive that check. Likewise,
local Truss revision/sourceReference claims require containing-source correspondence
outside UMF's document-only callback. Complete declaration of direction, lifecycle,
inverse and composition preserves those meanings for later interpretation; schema
or callback success cannot classify their native enforcement or derivability.

The probe selects an occurrence bound of 100 for callback work and checks overflow.
It does not precharge the original registry's schema traversal, source decoder or
complete retained heap. Full original bounded transport/registration composition
remains an adoption dependency. This checker is an experiment, not a release
registration or callback exported by the runtime package. E1 still needs a pinned
original full registration in the coherent interpretation/resource tuple, and
E2–E5 still need complete package/accepted-history, security and native/report
composition. No vocabulary support claim or public activation follows.

### E2/E3 previously accepted source construction and independent exit

Extend the existing original acceptance composition rather than adding a public
archive-fetch callback or a second source registry. The supplied-source resolver
remains supplied-only until this complete prior-source path exists. Retain the
original prior accepted closure and complete source membership under the admitted
installation, catalog revision, layout/report/interpretation and security/resource
context; a caller's copied view or arbitrary archive bytes cannot provide it.

1. Before effects, capture the complete required dependency and selected endpoint
   inventory from all original incoming documents. Reserve capacity for source
   bytes, interpretation, definition/key correspondence and diagnostics. Distinguish
   references to supplied members from references requiring original accepted
   custody; do not resolve a successful supplied prefix as the whole package.
2. Under the original acceptance transaction/snapshot and exclusion order, resolve
   each prior selection through the protected accepted source/archive producer.
   Match exact document, Truss revision and source-inventory identity, original
   bytes/digest and accepted membership. Compare full artifact identity and bytes
   after any hash routing. Ambiguous membership, missing bytes, wrong incarnation
   or an unavailable original interpretation refuses before allocations.
3. Admit that exact definition in the selected final closure. Merely retaining
   bytes from an old report does not make a retired or superseded definition active.
   A required lifecycle/reactivation/rebind transition uses its existing complete
   producer; source lookup cannot perform that transition implicitly. If incoming
   and prior selections conflict under one qualified lineage, refuse or require
   the original explicit compatible transition; never select latest or prioritize
   one input source by iteration order.
4. Interpret original source through its admitted original UMF/profile producer,
   retaining any explicit version transition as separate evidence. Resolve the
   exact owning Record and authored key. Candidate key names are source-version
   lookup inputs; after resolution preserve `Record.keys[].id` and complete
   definition/provenance under CONTRACT-003. A later rename cannot remap by current
   name or allocate a new native key number for the unchanged authored key ID.
5. Bind resolved definitions to the original accepted mapping and current
   security-owner admission. A found source, Record or key conveys no grant.
   Recheck original context before native effects/publication; changed head,
   interpretation, lifecycle or authority cannot reuse a stale resolution result.
   Feed/report publication and backend-loss custody follow the security owner's
   shared protocol, without a new endpoint-specific ACL or drain mechanism.
6. Derive all types/properties/keys before complete relationship endpoint sets.
   Preserve source-qualified pending/loss inventories and compare the complete
   independently expected report before original immutable insertion and head
   publication. Confirmed rollback preserves prior accepted source/mapping state;
   unknown commit uses the original acceptance attempt and recovery gate.

Independent schedules require a supplied source plus a previously accepted target,
wrong source revision with a newer version present, same names under different
owners, retained historical bytes whose definition is retired, source identity/hash
routing collisions, omitted accepted member, changed source/profile/head, and
changed authority after lookup. Include a key rename with unchanged authored ID,
a conflicting changed key tuple under that ID, and a late failure after endpoint
allocation. Independently compare complete original bytes, resolved identities,
active lifecycle and prior-state preservation; source row counts or matching key
names are insufficient. These are authored implementation/test obligations, not
an implemented archive service or a new acceptance capability.
