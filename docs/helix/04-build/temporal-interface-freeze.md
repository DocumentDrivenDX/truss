---
ddx:
  id: truss.temporal-interface-freeze
  type: implementation-plan
  activity: build
  authoring:
    home: repo
  links:
    - id: truss.temporal-current-baseline-plan
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
    - id: TP-001
      kind: informed_by
---

# Temporal interface freeze

## Scope

**Freeze identity: `truss.temporal-interface-freeze/1`, 2026-11-02.** The decisions
below are selected interfaces for implementation, not evidence of delivered
capability. Access and Weft workers may resume against this freeze immediately.
Sol owns planning/review; Luna owns code and qualification. Noether owns Truss
native implementation after the separate T4A CI harness is qualified. Human
authorization already includes reviewed completion, merge and release.

This freeze governs one-Record finite date/instant/local scalar read, filter,
order and authored-string-Key page composition. No joins, relationship traversal,
aggregates, temporal Keys, numeric selected-Key paging, temporal containers,
refined temporal Fields or temporal action/seed expressions are added. Retain
unknown extension content; unknown selected meaning refuses rather than disappearing.

Governing sources read:

- [Current baseline plan](temporal-current-baseline-plan.md),
  [delivery plan](embedder-temporal-delivery-plan.md),
  [CONTRACT-010](../02-design/contracts/CONTRACT-010-exact-value-transport.md),
  [CONTRACT-012](../02-design/contracts/CONTRACT-012-weft-storage-handoff.md),
  [TP-001](../03-test/test-plan.md) and current fresh-install policy.
- UMF CONTRACT-070 (access meaning/presence), CONTRACT-075 (strict temporal
  oracle), CONTRACT-069/071/072 (engine adapter/catalog/target custody), in
  `/private/tmp/umf-access-temporal/docs/helix/02-design/contracts/`.
- Weft `typed-sdk-engine-catalog.md`, `typed-sdk-engine-ordered-page-candidate.md`
  and current compile request schema in
  `/private/tmp/weft-temporal/docs/helix/02-design/contracts/`.
- Historical Truss `truss.temporal-query-source-guard` and TX-0–6 at
  `8bc82edd270a0043cd48ef8073fb2ef755eb017b` supply design input only. Their
  native0.75 identity, CONTRACT-082 reference, 128-character conversion,
  zero-residue rule and old Access/compiler receipts are NOT selected here.

Cross-repository references are explicit prose references, not invented local
`ddx.links` edges. No cross-flow graph is introduced. This user-selected build
freeze records the exact integration contract; the narrowly amended owner
contracts adopt it by freeze identity. Conflicting historical proposal text does
not override this selected cut. Inspection API ownership and shape are unchanged.

## Shared Constraints

### F1 — selected identities and compatibility

| Component | Frozen selector |
| --- | --- |
| Access token oracle | `umf-access-temporal/0.1.0`, CONTRACT-075 unchanged |
| Integrated binding temporal profile | `umf.weft-binding-temporal/0.2` |
| Engine wrappers | `weft.engine-read/0.4`, `weft.engine-page/0.4` |
| Compiler selector | `truss-runtime-temporal` |
| Compile interface / backend interface | `weft-compile/0.2.10` / `weft-backend/0.2.10` |
| Backend | `truss.postgresql.runtime`, backend version `0.4.47` |
| Target | `truss-runtime-pg18.6/0.7-temporal-candidate` |
| Captured binding | Existing `truss-runtime-binding/0.5` closed shape, explicit ABI1.3 pin; no field rename |
| Query ABI | identity `truss-postgresql-logical-query`, version `1.3`, actual descriptor SHA-256 |
| Native release | `truss-catalog-runtime/0.76-temporal-candidate` |
| Source requirements | `truss.temporal-source-guard/0.2` |
| Domain-check artifact | `weft.truss-temporal-domain-checks/0.2` |
| Inert Access wrapper | `umf.engine-catalog/0.4` |
| Exact temporal output decoder | `truss-temporal/0.2` |
| Temporal acceptance support | `truss-fresh-catalog-temporal-support/0.2` |
| Preparation / summary | `truss-registration-preparation/2.1` / `truss-registration-summary/2.1` |
| Native local capability / cell profile | `truss.native-temporal-scalars/0.1` / `truss.local-timestamp/0.1` |
| Explicit local transport | `truss-exact-value-temporal/0.1` |

Engine0.4/profile0.2/compile0.2.10/ABI1.3 are now selected for this cut, not a
claim that those interfaces are public. New strict guard/support/decoder0.2
separate this composition from historical broader-token proposals. No old
source/digest is reassigned these meanings. Actual descriptor, SQL inventory,
compiler, source and wheel hashes MUST come from implementation bytes; none is
fabricated by this freeze. Package versions are release-integrator outputs,
not substitutes for these exact capability identities.

Ordinary capture, `query_abi()`, compiler selectors, ABI1.2, old engine0.1/0.2,
old Access wrappers and their refusals/defaults stay unchanged. Explicit temporal
selection is required even for a date-only query in this route. An old generic
target, ordinary checker or mixed identity tuple MUST refuse before execution.
No caller-supplied boolean can advertise temporal capability. Ordinary ABI1.2
must still work against an authentic fresh capture of the candidate runtime;
never rewrite old runtime pins to obtain that result.

Public observed baseline UMF0.10.6 / `umf-weft`0.4.56 / Access dev8 / Truss0.0.54
has no qualified integrated temporal execution. Active owner source or dev9
packaging does not change that fact without new exact-cohort proof.

### F2 — strict values, presence and original identities

Apply CONTRACT-075 literally: at most32 ASCII characters; date exactly10;
local/instant optional fraction has1–6 digits, including zero-residue inputs.
Reject seventh digits even when zero, unknown `-00:00`, leap seconds, offset
seconds, invalid Gregorian days, year zero and UTC normalization outside1–9999.
No128-character path, truncation, Date parser, host timezone or float epoch.
Python fixed-offset carriers retain CONTRACT-075's canonical-token agreement;
this does not broaden source token grammar. Local is naive; instant is explicit
fixed-offset and normalizes to UTC. No instant/local cross-kind coercion.

Canonical output is date10, local26, instant27 ending `Z`. Native local storage
is exactly `{kind:"localTimestamp",text:<canonical26>}`. Existing timestamp
storage keeps its original token/instant meaning; this finite temporal route
refuses a broader stored token without rewriting it or broadening ordinary APIs.
Exact comparisons use canonical full-width text under C collation after strict
validation and exact offset normalization; this orders Gregorian dates/locals
and normalized UTC instants correctly across positive and negative epochs.
No PostgreSQL timestamp input rounding supplies validation.

Reuse UMF `Ref={module,element}`, KeyRef `{module,record,key}`, and full source
`Identity={documentId,revision,module,element}`. Each string is nonempty and
exact; no name-only, casefolded or cross-document identity substitution.
`Presence={missing:boolean,null:boolean}` comes from the admitted FieldView.row,
not core nullability alone. Missing, null and value stay distinct through native
cells, results and continuations; neither absent nor null has a text payload.

### F3 — inspection boundary already frozen elsewhere

Preserve exactly:

```text
inspectAccessViews(document, selected, bindings=[], sourceId='logical')
bindings: {sourceId,document}[]
wire: {operation:'inspectAccessViews',document,selected,bindings,sourceId}
result: {records,diagnostics}
Python: inspect_access_views(document, selected, bindings=(), source_id='logical')
```

Consume the existing resolved Records/Fields, refs, selected Key, temporal kind,
row presence and ordered diagnostics. Preserve budget/resource/cancellation
controls and diagnostic classification. No new inspection API or alternative
Truss semantic walker is authorized by this freeze.

## Normative Surface

### F4 — Access public builder, original custody and typed decode

File: `python/umf_access/src/umf_access/engine_catalog.py` in the isolated Access
worktree. Add keyword-only `temporal_profile: str | None = None` to
`EngineRead.build` and `EngineRead.compile_original`; all existing parameters,
defaults and return types remain. `None` retains the old route exactly.
`"umf.weft-binding-temporal/0.2"` requires `method="truss-runtime-temporal"`.
That method requires the explicit profile; all other pairings refuse.
Temporal `related_source`, `relationship`, `source_selected_key` and `order_key`
MUST be None. Page requires explicit `selected_key` equal to the admitted
RecordView.selectedKey and `page_size` integer1..999 (bool excluded). Read
requires `selected_key=None` and `page_size=None`. SQL owns ordering; no
`temporalKeys` member is accepted anywhere.

The unchanged compile methods `compile_engine_read_json(packet_json)` and
`compile_engine_page_json(packet_json)` select these closed envelopes:

```text
read: {version:'weft.engine-read/0.4',compiler:'truss-runtime-temporal',request}
page: {version:'weft.engine-page/0.4',compiler:'truss-runtime-temporal',request,
       selectedKey:KeyRef,pageSize:integer}
```

Compiled read program is closed
`{version,status:'compiled',compiler,request,artifact,outputs,structuralDigest}`.
Compiled page adds exactly `{pageSize,selectedKey,after,page}` to that inventory;
its version is engine-page0.4. `page` has the F6 shape. The complete guarded-source
packet is at `artifact.sourceDomainChecks`, never an ignored top-level copy.
Page compilation always produces an original first page with `after:null`.
Only the current page checker takes a continuation. No related/page alias route.

`EngineRead.compile_original` returns the EXACT compiler-returned JSON string.
`EngineRead.from_original(original, *, parameters, result)` retains its existing
signature and infers the explicit route only from an exact full engine0.4 tuple.
The wrapper is closed `{version,programJson,parameters,outputs,stageOne,catalogDigest}`
with version `umf.engine-catalog/0.4`; `programJson` is unchanged original text.
Wrapper catalogDigest uses existing Access canonical JSON/SHA-256 over the
wrapper minus catalogDigest. `originals()` returns byte-for-byte that string;
`artifact()` validates without discarding any owner member. Whole original
request, artifact, SQL, ordered parameters/outputs, source checks, caps and ABI
participate in custody. Unknown program members cannot be stripped to match.

Weft engine structuralDigest retains owners `weft-runtime-engine-read` or
`weft-runtime-engine-page`, version `0.4`; SHA-256 is over its entire owner
canonical program minus structuralDigest. Original compiler input strings inside
modules and bindingJson remain exact strings, including whitespace. Digest is
integrity, never authority. Access does not construct SQL, native requirements,
continuations or bindings. It validates the complete owner signature, not just
output names/families or a copied digest.

Temporal output descriptor is exactly:
`{name,carrier,nullable,missing,source,representation,modelPins,decoder}`.
`carrier` is `date|instant|local`; source is full Identity; representation and
modelPins are the unchanged complete compiler column representation/pins.
`decoder` is exactly `{profile:'truss-temporal/0.2',kind:carrier,
 temporalProfile:'umf.weft-binding-temporal/0.2'}`.
Boolean nullable/missing MUST match admitted row presence. Other supported
scalar outputs retain their existing complete descriptors. Hidden page outputs
also carry complete descriptors and participate in validation/digest.

The native representation selected for temporal Fields is the existing exact
property-cell representation, retaining absence/null states and original text;
Weft MUST emit its complete actual representation object rather than inventing
a generic string column. Truss decodes that envelope before the Access adapter
converts the value with UMF's existing strict oracle/carrier codecs. Date uses
exact `datetime.date`, instant aware fixed-offset `datetime.datetime`, local
naive `datetime.datetime`; use existing generated kind metadata to distinguish
the latter two. Reject annotation-only guesses, altered source, kind/presence
mismatch, unsupported selected refinements or partial typed output. MISSING
and None follow the existing generated carriers. Preserve complete raw native
column metadata alongside the original program. Generic targets refuse0.4.

### F5 — closed Weft request and lowering

Owner files: `crates/weft-core/src/compile.rs` and its request schema/resolver,
`crates/weft-postgresql/src/truss_runtime.rs`,
`crates/weft-runtime/src/engine_read.rs`, Python and WASM bindings. Extend in
separate internal modules as needed; no new JavaScript sidecar or Truss compiler.

Compile0.2.10 retains existing required `dialect`, `modules`, `sql`, `parameters`,
`exactParameters`, `options`, `target` members and their current rules, adding
REQUIRED `temporalProfile:'umf.weft-binding-temporal/0.2'` and REQUIRED
`temporalParameters:{name:{kind:'date'|'instant'|'local',value:string}}`.
`interfaceVersion` is compile0.2.10. `exactParameters` is exactly `{}` in this cut.
`parameters` retains existing non-temporal `{family,value}` entries and is
required even when empty. Names across both maps are unique under existing
compiler parameter-name normalization, at most1024 total, and match the complete
SQL placeholder inventory. No value inference from ordinary string parameters.
No timestampComparisonProfile, readProfile or security override is admitted in
this cut. All requests are closed; unknown selected fields refuse.

Modules retain original documentJson strings, exact document/revision/hash pins
and selected module inventory, including authored registered umf.access meaning.
Resolve the selected Record/Fields against those exact documents using the owner
model/access machinery. Binding JSON is original exact captured text plus its
SHA-256; exact actual installation/native release/catalog/document mappings,
resource caps and ABI1.3 descriptor MUST agree with resolved source meaning.
No request-supplied duplicate access view can replace authored semantics.

Support same-kind date/instant/local projection, `=`, `<>`, `<`, `<=`, `>`, `>=`,
existing boolean predicate composition, and ASC/DESC with explicit NULLS
FIRST/LAST. Omitted direction is ASC and omitted null placement is LAST in this
profile. Null/missing have the same ordering rank but retain distinct state.
Unsupported expressions/refinements refuse. Ordinary admitted scalar siblings
remain supported; no binary/collection capability is inferred by this profile.

Emit a complete bounded guarded source BEFORE every business predicate, user
order, generated continuation predicate, offset/limit or projection. No ABI1.2
indexed selected/seek source, candidate filter pushdown, unguarded source or
separate preflight statement is permitted in this temporal route. All selected
source rows, including excluded and later rows, validate before the first row
can escape. Guard requirements cover ALL temporal members of the selected
RecordView, not only projected or filtered members, in original member order.

`sourceDomainChecks` is closed:
`{version:'weft.truss-temporal-domain-checks/0.2',mode:'native-validated-source',
 queryAbi,maxScanRows,maxBytes,sources}`. In this cut sources has exactly one:
`{record:Identity,bindingParameter:integer,requirementsParameter:integer,
 sourceFunction:string,selectedKey:null|KeyRef}`.
Both parameter positions are ONE-BASED into artifact.parameters; bindingParameter
contains exact original bindingJson text; requirementsParameter contains the
compiler-generated complete requirements JSON string. They are distinct slots
with original types, values and origins preserved. Caps equal captured
maximumScanRows/maximumBytes, not the page/result limit. sourceFunction is the
exact qualified signature in F7; selectedKey is null for read and authored KeyRef
for page. SQL, native selected key_id argument, source inventory, ABI pin,
parameter slots and actual referenced function MUST agree on recompilation.

### F6 — four checker signatures and continuation custody

Python public names and WASM js_name exports are identical:

```python
check_engine_temporal_read_shape_json(program: str, original_request: str) -> str
check_engine_temporal_page_shape_json(program: str, original_request: str) -> str
check_engine_temporal_read_json(program: str, current_request: str) -> str
check_engine_temporal_page_json(program: str, current_request: str, after_json: str) -> str
```

All arguments and results are JSON TEXT STRINGS, not parsed objects. All four
succeed with exactly `{status:'checked',program:<whole checked engine program>}`.
Shape returns the unchanged original compiled read/initial-page program after
strict parsing, full original-request equality and independent whole-program
recompilation. Current read returns a whole freshly compiled current read;
current page returns a whole freshly compiled current page including after.
Hosts execute ONLY the returned program.artifact after comparing its full pins
with the current native capture. A shape success grants no execution authority.

Original program MUST be status compiled, exact engine0.4 selector/tuple and
original page after:null; first recompile and compare EVERY member against its
own original request. Shape's supplied original_request must equal that request
entirely. Current request may change ONLY declared values in parameters and
temporalParameters: names, kinds/families and map membership remain identical.
Every other member/string, binding, source pin, SQL, cap and ABI stays exact.
Reject changed binding/context; do not repair a catalog from fresh capture.
Validate current tokens again before lowering. Recompute full program/digest.

Checker failure is `{status:'blocked',diagnostics:[<original diagnostics>]}`;
when an underlying compile returns blocked, add `original:<whole blocked compile
response>` and retain ordered diagnostics. No partial program/artifact on failure.
Use existing WFT-ENGINE-READ / WFT-ENGINE-PAGE categories and preserve original
parse/limit/source/compile diagnostics. No boolean-only success or empty rows.
Python/WASM share the Rust checker; duplicate-member/nonfinite/invalid Unicode
framing and existing cancellation/resource rules remain in force. Maximum UTF-8
program and request are4,194,304 bytes each; after_json1,048,576; stricter existing
limits still apply. Check before parsing/allocation.

`after_json` is JSON null for first page, otherwise closed:
`{version:'weft.engine-temporal-after/0.2',selectedKey:KeyRef,
 sortValues:SortState[],keyValues:string[]}`.
SortState is exactly `{state:'present',value:string}`, `{state:'null'}` or
`{state:'missing'}`. Present temporal values are canonical F2 tokens; string
values are exact unnormalized strings. Effective ordering in this cut supports
temporal and string slots only. keyValues are the complete required non-null
string Key components in declared order, never a numeric or temporal Key.

The engine page program adds closed `page` metadata:
`{version:'weft.engine-temporal-page/0.2',selectedKey:KeyRef,
 visibleOutputPositions:integer[],keyOutputPositions:integer[],sort:SortSlot[]}`.
SortSlot is `{field:Identity,direction:'asc'|'desc',nulls:'first'|'last',
 kind:'string'|'date'|'instant'|'local',outputPosition:integer}`.
Positions are one-based in whole program.outputs; hidden outputs are included.
Derive sort solely from original SQL, appending the complete selected Key ASC
suffix unless already the exact complete terminating suffix. Preserve repeated
slots with different direction. sortValues contains the COMPLETE effective sort
(including suffix); keyValues must agree with corresponding suffix values.
Each position, source identity, kind and presence is checked. Refuse duplicates
in position inventories where semantically disallowed, wrong arity or foreign
Key/kind. Use null-safe prefix equality, explicit null rank and exact canonical
value comparator for strictly-after full-tuple continuation. DESC reverses value
comparison only. No client-side pagination or SQL text rewriting.

The Truss ReadContinuation remains its existing carrier; its original native
opaque token (maximum65,536 bytes) binds actor, query/noncursor arguments,
installation/release/ABI/catalog/documents, selected Key and full tuple. The
host verifies exact token/tuple agreement before passing after_json to Weft.
The JSON tuple is never authorization. Every page receives fresh native/final
authority checks; live pages make no cross-page snapshot guarantee. Temporal
stream/export is outside this cut; existing ordinary streams remain unchanged.

Direct object paging follows PV-5 in the
[public-values addendum](temporal-public-values-addendum.md), decision
`truss.temporal-public-values/pv5-cursor-custody/1`. Its existing temporal
ObjectPageCursor adds REQUIRED keyword-only `original_bytes: bytes` (repr=False,
exact immutable bytes1..65,536, no default). Native continuation metadata adds
`originalCursorBase64`; the adapter retains and submits exact native-issued
bytes rather than serializing DTO fields into a new cursor. Native seals bind
the direct-page route/person/release/source/profile/ABI/afterId context and
reject altered metadata, unsigned cursors and cross-route substitution. Keep
ordinary/public54 cursor contracts and the F6 Weft tuple route unchanged.

PV-5 also selects prepared temporal writer completion for this delivery while
preserving the original optional-optimization fallback contract. Use existing
temporal schema-basis/prepared entrypoints and shared patch/cache machinery;
native original-source/descriptor/ordinal correspondence and current authority
remain mandatory. Ineligible preparation may choose unprepared TEMPORAL before
dispatch; supplied invalid/stale patches refuse without fallback. The addendum
owns these details and same-campaign controls; no new owner API or semantic
profile is introduced by this trace amendment.

### F7 — Truss native ABI, transport and capture

Keep `query_abi()` ABI1.2. Add `truss.query_temporal_abi() RETURNS jsonb` with
`{identity:'truss-postgresql-logical-query',version:'1.3',sha256:<actual descriptor>}`.
Add explicit `truss.query_temporal_binding(...)` with ordinary query_binding's
same SQL argument types/order/result, and enrolled public person capture:
`truss.person_query_temporal_binding(jsonb,int,int,int,text,text) RETURNS bytea`.
No host may replace the pin on an ordinary capture. The native descriptor must
inventory actual owner/ACL/dependency signatures and source semantics.

New enrolled STABLE public data sources are exactly:

```sql
truss.person_query_temporal_objects(binding jsonb, selected_type integer,
                                  requirements jsonb)
  RETURNS TABLE(id bigint, props jsonb)
truss.person_query_temporal_page_objects(binding jsonb, selected_type integer,
                                       selected_key text, requirements jsonb)
  RETURNS TABLE(id bigint, props jsonb)
```

sourceFunction strings in F5 are exactly
`truss.person_query_temporal_objects(jsonb,int,jsonb)` or
`truss.person_query_temporal_page_objects(jsonb,int,text,jsonb)` respectively.
selected_key SQL argument is the actual captured native key_id corresponding
exactly to selectedKey; never the first/primary Key guessed from inventory.

Add pure deterministic helper
`truss.query_temporal_canonical_text(kind text, token text) RETURNS text` to the
ABI1.3 inventory. It validates F2 before returning canonicalText; invalid input
raises a domain refusal, never NULL. Weft uses it for temporal comparison/order
under explicit C collation. It MUST NOT use timestamp casts that round, floats,
host timezone or broader old timestamp-key semantics. Raw projections retain
original cell text. Null/missing bypass this helper only via admitted state logic.

Requirements is closed `{version:'truss.temporal-source-guard/0.2',record:Identity,
 fields:FieldRequirement[]}`; each field is exactly
`{field:Identity,kind:'date'|'instant'|'local',presence:Presence}`. Coverage is all
temporal members of the original selected Record, exactly once in member order,
matching retained UMF inspection and actual accepted native property families.
No caller field/presence overrides. Missing/foreign/duplicate/incomplete packets
refuse atomically even when the affected Field is unprojected.

A native buffered SRF (or equivalent fully materialized source) validates the
COMPLETE original bounded source before first yield, under ONE caller statement
snapshot and READ COMMITTED. Include own pending writes. Overflow refuses the
whole source rather than truncating it. Recheck original person enrollment,
owner/EXECUTE, root/module visibility, selected-Key integrity, binding tuple,
scan/byte limits and deadlines; do not substitute a privileged caller, relax
guards or add direct registry grants. Current-authority final checks remain
separate and mandatory before releasing decoded results. Separate preflight and
data statements cannot establish the required common source snapshot.

Public Python method on the existing catalog runtime:

```python
query_temporal_catalog_sources_in_transaction(
    self, transaction: TransactionHandle, *, sql: str,
    document_ids: tuple[str, ...],
    parameters: Mapping[str, str | int | bool | Decimal] | None = None,
    temporal_parameters: Mapping[str, Mapping[str, str]] | None = None,
    maximum_rows: int = 1000, maximum_scan_rows: int = 10000,
    maximum_bytes: int = 1048576,
) -> Outcome[QueryCatalogSources | QueryRefused | QueryUnavailable]
```

The temporal_parameters values are exactly F5 `{kind,value}`; None means `{}`.
This explicit method selects profile0.2/ABI1.3 without another capability flag,
captures original sources/binding and emits the F5 compiler request. The result
shape is unchanged. Ordinary capture signature/defaults stay unchanged. All I/O
and supported TrussTarget read/page dispatch remain in `truss/access.py` and
existing query runtime; Access stays inert. TrussTarget detects only the exact
engine0.4 tuple, shape-checks before native capture, freshly captures temporal
context, current-checks, validates returned complete program against that native
context, executes the guarded statement, decodes and performs existing final
authority/deadline/cleanup/settlement checks before publication. Never fallback.

### F8 — Prep2.1 original-source custody and inverse coverage

Acceptance-input stays `truss-acceptance-input/0.2.0`. Only the exact new support
profile0.2 plus prep2.1/summary2.1 selects NONCOMPACT descriptor-bearing transport.
Legacy summary2.0 compact source transport retains its meaning. Mixed profiles,
empty declarations or compact reconstruction of2.1 refuse before publication.

Core Field declaration remains `scalarType:'timestamp'`. Derive a separate
sibling nativeDescriptor ONLY for selected local Fields:

```text
{nativeScalarType:'localTimestamp',nativeTemporal:{
 profile:'truss.local-timestamp/0.1',kind:'local',source:{
 documentId,sha256,record:Ref,field:Ref,fieldViewPointer}}}
```

fieldViewPointer identifies the exact admitted local FieldView in the original
source bytes. Retain document revision in the complete document pin/admission
custody; do not infer it from a display name. Exact source bytes/hash, pointer,
Record membership, owner inspection/presence, declaration and native mapping
must agree. Prep2.1 retains the COMPLETE owner `{records,diagnostics}` result
and exact invocation/profile/version with original declarations/document bytes.
Do not discard diagnostic/unknown content or manufacture an owner result.

Native inverse coverage enforces descriptor iff the retained owner result
selects local, exactly once for each original accepted member. A removed owner
entry, stripped descriptor, foreign pointer/ref, altered hash or duplicate must
refuse before any catalog/property/cache publication. Native consumes the pinned
owner result; it does not implement another access resolver. New local property
family must survive acceptance/apply, native property/cache validation, value
write/import, read, history, retained requests, replay, report recovery and
definition-source reconstruction. Canonical26 local value ingress uses the
separate immutable LocalTimestampValue carrier; old exact-value APIs do not
silently accept it. Supported typed codecs convert through the explicit route.

Retain exact declarations, descriptor bytes, original document bytes, summary2.1
and owner admission in the original durable request. Exact-repeat/replay uses
those bytes, never source-only reconstruction or relabeling as2.0. Existing
property identities/families and retained unknown metadata never become local
through rediscovery, cache regeneration or an ordinary profile upgrade.

### F9 — installation decision: fresh-only, no current54 migration

Select fresh-only release of native0.76-temporal-candidate. No public54-to-
candidate preservation migration is shipped or claimed. This resolves the
migration/fresh-only choice; workers need no further human approval for it.

Public54 native0.75 and historical temporal native0.75 have different bytes.
Neither may be relabeled as the new target. Compute a new complete authentic
inventory/digest. Never alter system time, initializer results, inventory labels,
old manifests or source receipts to admit it. No resurrection of retired153-case
lineage or0.0.47/48 recovery. Preserve current-only six baseline controls.

Use the real public54 wheel to create a populated negative-control installation.
New tooling MUST refuse its existing namespace/tuple before effects, preserving
properties, cells, original source, history, ACLs, retained requests and data.
No startup migration, reset, reimport or metadata reinterpretation. Fresh target
installation proves temporal behavior separately. Any later54 migration needs
its own explicit immutable source-to-target preservation/failure qualification;
fresh-only evidence is not a successful migration.

## Implementation Slices

| Slice / owner | Exact writable source boundary | Prerequisite / required outcome |
| --- | --- | --- |
| IF-A / Access Luna | `/private/tmp/umf-access-temporal`, engine_catalog.py, existing generated temporal codecs/types and focused owner contracts | F4 is ready now; implement explicit profile, full original custody and typed signature checks; no Truss I/O. Base a5e24d17017a3de0ee701837d9c99c3dad27d0a5. |
| IF-I / existing inspection Luna | `/private/tmp/umf-temporal-inspection`, existing Rust codegen dispatcher and Python/Node/WASM facades | Consume unchanged F3; preserve ordered diagnostics/limits/cancellation. Same UMF base. No new inspection signature. |
| IF-W / Weft Luna | `/private/tmp/weft-temporal`, compiler/schema/resolver, truss_runtime, engine_read and Python/WASM bindings | F5/F6 are ready now; separate repository at2f62e1148d1b2030558550e4f6f2ffe518bac62d. Rust owns all lowering/checking; no copied older backend. |
| IF-N / Noether | Isolated Truss native/preparation/query/access owner scope | After independent T4A harness qualification, implement F7–9 end to end, including transport/security/snapshot; not another owner handoff. |
| IF-Q / Luna integrator + Sol review | Exact candidate evidence and release inputs | All owner slices, ordinary ABI1.2 adoption and qualification below; then reviewed merge/release and public consumers. |

Existing owner boundary checks remain required; implementation workers identify
and run their repository's real module gates, rather than inventing success from
these module names. Allowed boundary is UMF semantics → Weft pure compiler →
Truss native execution. Forbidden dependencies include Access native I/O, Truss
semantic resolution/SQL generation and a Python JavaScript compiler sidecar.
Active owner worktrees under `/Users/erik/.codex/worktrees/` and all primary
checkouts remain untouched. No Arras files or other owner's delivery plan edits.

## Execution Contract

This task is PLAN/FREEZE ONLY: no implementation or tests were run by the freeze
author. Implementation, CI, merges and releases remain authorized to Luna by the
human request. No new agents or thread messages are authorized here. Interface
changes require an explicit revision of this freeze and affected owner contracts
before consumers adopt changed bytes. Code workers may resolve private layout
choices within these interfaces. No token budget/spending ceiling or reliable
aggregate meter was supplied; no numeric usage claim is made.

## Validation Plan

The following are REQUIRED FUTURE gates, not asserted passes:

1. Owner pure/native/WASM/real Chromium agree on strict32/1–6 grammar, all three
   kinds, original source/program strings, source/kind/presence/refinement and
   tampered SQL/parameter-position/output/cap/ABI/program refusals. Real package
   exports must exist; a source helper is insufficient.
2. Genuine public accept/apply/value APIs create date, instant and native local
   property/cells; original core timestamp declaration and unknown content stay
   exact. Strip a local descriptor/owner member, foreign a pointer/hash, remove
   declarations and mix summary profiles: each refuses atomically. Durable2.1
   replay/recovery retains complete original bytes and native local family.
3. Native guarded execution validates invalid rows excluded by filters and late
   invalid rows, including an unprojected temporal member; overflow and deadlines
   refuse without partial rows. Wrong person/role/root/module, owner/ACL/ABI,
   native tuple and revoked final authority retain genuine failure classes.
4. Native concurrency independently establishes a single statement snapshot
   across full-source validation and data consumption. No clock manipulation or
   separate preflight qualifies it. Cancellation/settlement/cleanup remain real.
5. Independent complete-row/page oracles cover date/local/offset/UTC range,
   instant order across negative epochs and9/10 boundaries, duplicate temporal
   sort values, repeated string composite-Key prefixes, alternate Keys,
   ASC/DESC/FIRST/LAST and distinct missing/null. Temporal/numeric selected Keys
   and forged tuple/native-token disagreement refuse. No client result repair.
6. T4A authentic ordinary ABI1.2 capture/compile/check/execute/decode, unchanged
   HF62 assertions and affected native/security regressions pass on the adopted
   owner tuple. Retain failed initdb/capture attempts; no inferred test success.
   One genuine hosted Linux capture/replay job remains required after local
   initdb failure. Worker harness commit885d3867 is under independent Sol review;
   it is not an already successful hosted or native receipt.
7. Fresh target and populated real-public54 no-effect refusal, current six
   baseline controls, new complete native inventory and exact installed wheel/
   source/registry byte correspondence pass. Qualify local macOS and hosted
   Linux in their actual runs; native/browser parity and snapshot/replay/security
   are mandatory. Managed platforms require their own evidence or refuse.
8. Reviewed merge, exact-tag workflows, immutable assets, trusted public upload,
   independent public download/hash/install and fresh exported-capability
   consumers complete the human delivery scope. Never infer release from a
   carrier, signature, upload or this freeze.

## Risks and Rollbacks

| Risk | Required response |
| --- | --- |
| Broader historical token route silently admitted | Strict F2 guard/support/decoder0.2; reject unchanged broad source in temporal query, retain original storage. |
| Source guard optimized away or partial row escapes | Buffered complete native source, native late/excluded-row and concurrency evidence. |
| Profile/version/digest mistaken for authority | Exact fresh native capture, whole recompilation and final original-person checks. |
| Native identity collision or inherited receipt claim | New0.76-temporal-candidate inventory; old conflicting0.75 bytes unchanged. |
| Existing installation reinterpreted | Fresh-only boundary and public54 preservation refusal; no automatic upgrade. |

On failure disable/refuse only the new capability; retain original documents,
programs, requests, installations and evidence. Do not weaken ordinary guards or
rewrite historical manifests to create apparent support.

## Continuation Evidence

Planning inputs are current isolated source and governing documents; no tests,
implementation, native support, source/wheel hash selection or public release is
credited to this freeze. T4A proceeds independently with its existing owner and
Sol reviewer. Other delivery plans and protected worker files are not amended.
Unresolved implementation receipts are exact ABI/manifest/compiler/wheel digests,
actual native/installed/browser outcomes and final release version/bytes; these
are production outputs, not unresolved interface choices blocking Access/Weft.

## Exit Criteria

The interface freeze is ready when F1–F9 and owner contract adoption are written
and cross-checked for internal agreement. Full temporal delivery remains open
until every applicable future gate above passes for the same exact cohort and
reviewed merge/release/public consumer verification complete. The frozen scope
contains no implicit current54 migration, temporal Key or numeric-Key page claim.


## Public value route addendum — selected PV1

[Explicit public temporal value route](temporal-public-values-addendum.md),
ID `truss.temporal-public-values-addendum`, freezes the missing PUBLIC construction
and dispatch boundary for F1/F8 and TN-06–12: `assembly.temporal_values()` with
new value-bearing DTOs in `truss.temporal`, new selected input/payload/native
context/result profiles and actual native0.76/ABI1.3 admission. Ordinary ExactValue
and constructors/providers/decoders stay closed, including on0.76. A releaseId-only
local decoder branch does not select the explicit route. Prep2.1 acceptance and
TrussTarget engine0.4 remain their existing distinct explicit paths. This addendum
adds no temporal container, Key, edge-property or query semantic domain.
