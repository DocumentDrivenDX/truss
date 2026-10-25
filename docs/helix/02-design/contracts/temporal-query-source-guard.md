---
ddx:
  id: truss.temporal-query-source-guard
  type: contract
  activity: design
  authoring:
    home: repo
  links:
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-012
      kind: references
    - id: truss.typed-sdk-adoption
      kind: references
---

# Temporal graph source and query guard

**Version:** `truss.temporal-source-guard/0.1`. **Scope:** isolated PWS-03
PostgreSQL18.6 candidate; no release or managed-platform qualification.

## Purpose

Admit a distinct local civil timestamp and validate the complete selected finite
temporal source before business predicates, within the caller SQL statement
snapshot. Existing current-person authorization and READ COMMITTED stay required.

## Scope and Boundaries

UMF CONTRACT-070/075/082 owns authored date/instant/local meaning and finite
binding conversion. Weft owns logical query resolution, target SQL, ordered
parameters/results, typed requirements and whole-program custody. Truss owns
accepted native family correspondence, exact native value enforcement, source
enumeration, current-person security and buffering. Hosts own connections,
transaction settlement, deadlines and release of decoded results.

The candidate extends current Truss runtime0.74 to native
`truss-catalog-runtime/0.75-candidate`. It adds query ABI1.3 as an explicit
capability alongside existing ABI1.2. Existing ABI1.2 descriptors, entrypoint
meaning and source semantics MUST NOT be relabeled as1.3. Fresh bindings retain
the actual current installation/release/digest. Historical programs remain
bound to their old cohort; no old receipt establishes candidate support.

## Normative Surface

### Authored source and native carrier

The owner-produced `inspectAccessViews` result supplies selected temporal
meaning, original Record/Field refs, selected Key and row presence. Truss MUST
consume that existing UMF admission result through a pinned preparation bridge;
it MUST NOT implement another access semantic resolver. The prepared output
MUST retain exact original source bytes/digest and references. The source Field
declaration remains `scalarType:"timestamp"`; it is never rewritten to a new
core scalar. A separate derived native descriptor selects `localTimestamp`
only when the exact authored registered FieldView selects `temporal:"local"`.

This registration explicitly selects
`truss-fresh-catalog-temporal-support/0.1` and native capability
`truss.native-temporal-scalars/0.1`. The existing DATE10_PROFILE support selector,
its source bytes/hash, preparation2.0 evidence and ordinary timestamp support
remain exact. The new issued preparation output uses
`truss-registration-preparation/2.1` and retains the owner's resolved access
result alongside original declarations. Original declaration correspondence is
still byte-exact; the derived family is not written into that declaration.

The local property's separate native descriptor is
`{nativeScalarType:"localTimestamp",nativeTemporal:{profile:"truss.local-timestamp/0.1",kind:"local",source}}`,
where `source` is exactly
`{documentId,sha256,record:Ref,field:Ref,fieldViewPointer}`. Refs are exact
`{module,element}` pairs; fieldViewPointer is an RFC6901 pointer into those exact
original document bytes and selects the owner-admitted local FieldView. The
descriptor must agree with the pinned UMF-produced admission result, original
record membership, retained Field declaration and actual native family.
Missing owner output, changed hashes/pointers or a conflicting native type refuses.

Existing native properties keep their stored family and cell meaning across a
runtime upgrade, even if previously retained unknown access metadata now becomes
understood. A0.74 timestamp property MUST NOT become local by rediscovery of a
retained selector, cache regeneration or profile change. New local derivation is
limited to fresh selected-profile acceptance/new property identity; an existing
property with a conflicting family requires a separately reviewed semantic
catalog change and otherwise refuses. No automatic startup/runtime migration is
permitted. Any explicit0.74→0.75 installation route qualified in this cut must
demonstrate unchanged existing property/cell/retained-source meaning; a fresh
candidate installation alone does not qualify that route.

The new native cell is exactly `{kind:"localTimestamp",text:string}` under
`truss.local-timestamp/0.1` capability. Text is exactly26 ASCII characters
`YYYY-MM-DDTHH:MM:SS.ffffff`, valid Gregorian year0001–9999, hour00–23 and
minute/second00–59, without offset. It retains its original canonical text.
Existing `{kind:"timestamp",text:...}` keeps its original offset-bearing exact
instant meaning and retention; no naive value is attached to a timezone.

The issued2.1 preparation field entry carries this derived descriptor in an
optional `nativeDescriptor` sibling of `declaration`, never inside the original
Field declaration. It is present only for a selected local Field and has the
exact `{nativeScalarType,nativeTemporal}` shape specified above. Legacy2.0
entries do not acquire this member. Storage/support/projection must agree on
that placement and refuse malformed, foreign or source-mismatched descriptors.

The Python local carrier MUST be distinct from the old timestamp carrier.
Old timestamp constructors and existing exact-value wire profiles remain
unchanged; explicit local carrier construction selects the new capability.
The candidate exposes a `LocalTimestampValue` carrier whose serialization
is the new native cell. The selected carrier export is
`LocalTimestampValue(text=...)`, with fixed kind `localTimestamp`; it does not
broaden the existing TextValue timestamp constructor or historical closed wire
schemas. Local transport selects `truss-exact-value-temporal/0.1`. Exact schema,
bridge and capability bytes/hashes must be recorded in the source manifest
before installed qualification; old profile hashes are not overwritten.

Local storage is limited to singular scalar Fields, required or absent-allowed,
with no facets, allowedValues, default, item or record refinements. Temporal
Keys, local containers, local aggregates and new action/seed expression meaning
MUST refuse. Existing accepted-schema correspondence, native property-definition,
value, catalog-cache, write/apply, read and retained-source checks MUST agree on
the derived family. Read-only compiler acceptance alone is insufficient.

### Prep2.1 acceptance transport and retained requests

The temporal registration transport retains the original
`truss-acceptance-input/0.2.0` input bytes. Its exact selected
`truss-fresh-catalog-temporal-support/0.1` profile, issued
`truss-registration-preparation/2.1` and
`truss-registration-summary/2.1` select an explicit declaration transport.
This combination MUST use noncompact native acceptance, retention and replay;
the input envelope version alone MUST NOT select compact reconstruction.
The legacy selected support profile with summary2.0 retains its existing compact
source-only transport. Mixed profile/preparation/summary combinations refuse.
This decision adds no new UMF semantics or acceptance-input version.

Prep2.1 MUST supply the original issued descriptor-bearing declarations alongside
original document bytes and the full owner admission result/profile. Empty
declarations, compact reconstruction, or substitution of a source-only
projection MUST refuse before catalog publication. Retained requests MUST keep
the exact declaration bytes, original document bytes and summary2.1 bytes with
owner admission custody. Replays, unchanged-request comparisons, report recovery
and definition-source reconstruction MUST use those retained bytes. They MUST
NOT relabel the request as summary2.0, discard its descriptors or reconstruct
its declarations through the legacy compact path.

Native validation MUST enforce both directions of local correspondence. For
each original accepted Record member, `nativeDescriptor` is required if and
only if the exact retained normative owner admission selects `temporal:"local"`.
The declaration-level owner admission and profile MUST equal the full pinned
owner result retained with that original document, including when a descriptor
is absent. Each selected local Field MUST occur exactly once in its original
Record's declaration members with its descriptor sibling. Existing descriptor
validation MUST bind original document hash, Record/Field refs, FieldView
pointer, selected native family and exact capability/profile. Missing,
duplicated, foreign, conflicting or stripped entries refuse atomically; an
admitted local Field MUST NOT become an ordinary timestamp by omission.

This inverse coverage check consumes the existing UMF-produced admission
result; Truss MUST NOT add another authored access selector resolver or a custom
source semantic walker. Legacy2.0 retained unknown access remains under its
original timestamp meaning. The explicit fresh-profile rule above does not
reinterpret existing property identities or qualify a runtime migration.

### Explicit native ABI

Existing `query_abi()` and ordinary binding capture retain ABI1.2. The candidate
adds `query_temporal_abi()` returning exact descriptor
`{identity:"truss-postgresql-logical-query",version:"1.3",sha256:<descriptor hash>}`
and an explicit `query_temporal_binding(...)` capture with the same source/cap
arguments and result shape as ordinary binding capture. Their public person
shims use the existing invocation enrollment/owner/EXECUTE checks. Shared capture
implementation MAY be factored internally; hosts MUST NOT rewrite an ABI pin.
Native scope verifies the exact selected supported descriptor and actual
runtime tuple. ABI1.2 MUST refuse a selected local carrier it does not describe.

New STABLE public source shims are:

- `person_query_temporal_objects(binding jsonb, selected_type integer, requirements jsonb)`.
- `person_query_temporal_page_objects(binding jsonb, selected_type integer, selected_key text, requirements jsonb)`.

They return the existing `(id bigint, props jsonb)` source shape. Each invokes
the existing current-person enrollment and original internal-source authority
checks. No guard is disabled, no owner role is substituted for the caller, and
no direct registry/table grants are added to obtain a pass. Original source
scope, complete root visibility, selected Key integrity and row/byte caps apply.

`requirements` is closed:
`{version:"truss.temporal-source-guard/0.1",record:Identity,fields:FieldRequirement[]}`.
`Identity` is `{documentId,revision,module,element}`, all nonempty exact strings.
Each FieldRequirement is exactly
`{field:Identity,kind:"date"|"instant"|"local",presence:{missing:boolean,null:boolean}}`.
Fields are unique and must match the selected original accepted Record members,
native property mapping/family and UMF-produced selected meaning/presence.
Missing, foreign, duplicated, unsupported or conflicting requirements refuse.
The packet cannot confer authority or override a source presence rule.

Date/instant/local finite validation follows CONTRACT-082. The selected original
instant token capacity is128 ASCII characters; only zero residue beyond six
fraction digits may be removed exactly. Unknown offsets, leap seconds, UTC range
overflow and nonzero residue refuse. Legacy timestamp storage remains broader;
the guarded read explicitly refuses nonrepresentable selected stored values.

The guarded source MUST enumerate and validate the full original bounded source
before yielding its first row. Invalid values outside the user's filter still
refuse the whole read. A source overflow refuses, never qualifies a truncated
prefix. The source data and its checks use one caller statement snapshot through
STABLE functions under READ COMMITTED. A buffered native SRF or equivalent
materialized implementation must establish that no row escapes before complete
validation. Separate READ COMMITTED statements do not meet this contract.

### Compiler and host composition

The successor engine selects frontend `weft-compile/0.2.10`, backend
`truss.postgresql.runtime` version `0.4.47`, target
`truss-runtime-pg18.6/0.7-temporal-candidate`, engine read/page0.4 and
`temporalProfile:"umf.weft-binding-temporal/0.2"`. Exact query ABI1.3 and actual
native0.75 source/release pins are required. The old0.3/profile0.1 checkpoint
remains distinct and retains its explicit unsupported-host/local refusals.

The first successor scope is one Record, no joined/related source or aggregates,
complete non-temporal selected Key and bounded live reads/pages. Weft emits the
new guarded source scan with a typed requirements parameter derived from its
original resolved source graph. User predicates/order/limit apply only after
that source validation. Indexed candidate prefilters MUST NOT hide invalid
selected source rows in this profile; ordinary ABI1.2 optimizations remain exact.

The owner artifact's closed `sourceDomainChecks` successor is
`{version:"weft.truss-temporal-domain-checks/0.2",mode:"native-validated-source",queryAbi,maxScanRows,maxBytes,sources}`.
Each source is exactly
`{record:Identity,bindingParameter:integer,requirementsParameter:integer,sourceFunction:string,selectedKey:null|KeyRef}`.
Parameter positions are one-based into original `artifact.parameters`, retain
their exact typed values/origins, and refer to the original binding and generated
requirements JSON. The sourceFunction is the exact selected ABI signature above;
page sources retain the original authored KeyRef. Caps equal the original native
binding. The packet, final SQL, source/target pins, outputs and parameter inventory
participate in owner structural digest/recompilation custody.

The current successor public engine page route admits complete required-string
selected Keys only, retaining the existing page-Key admission boundary. Numeric
or other non-string selected-Key paging remains an explicit refusal and is not
qualified by this profile. This clarifies the non-temporal Key scope above;
it does not broaden compiler admission. Isolated numeric cursor-lowering vectors
do not establish integrated numeric-Key paging. Actual temporal sort values
still require exact numeric instant comparisons, including positive/negative
epoch boundaries, independently of the selected Key family.

This packet describes integrated execution, not separately executable host SQL.
The supporting Truss typed target MUST freshly capture the explicit temporal
binding, recompile/check the whole original engine program against the actual
current context and execute the guarded statement through the public Truss
runtime. Its existing final current-authority, deadline, cleanup and settlement
checks remain required before releasing results. Generic targets without this
exact capability refuse. No boolean supplied by a caller grants host support.
The supporting adapter belongs to Truss's existing typed-target owner; all I/O
stays there. UMF's inert catalog changes only descriptor/decoder/profile custody
and capability refusal. The candidate explicitly pins a fresh UMF access dev6
artifact by source/wheel hash; the older dev5 pin or previous dev6 checkpoint
receipt cannot qualify changed guard semantics.
All three temporal outputs pass the actual native envelope decoder, UMF exact
binding converter and typed result validation; a harness must not repair them.

The public capture method is
`query_temporal_catalog_sources_in_transaction`, with the same SQL, document,
parameter and cap arguments and `QueryCatalogSources` result shape as ordinary
`query_catalog_sources_in_transaction`. It captures ABI1.3 explicitly and emits
the matching successor compiler request. Checked engine0.4/profile0.2 selects
integrated temporal execution within the existing read/page dispatch; ordinary
calls keep their prior profile. The UMF `EngineRead` builder uses explicit
`temporal_profile` selection, defaulting to the prior profile0.1. Profile0.2
selects engine0.4; unknown combinations refuse. The output decoder stays
`truss-temporal/0.1` because finite date/instant/local value meanings are unchanged.

## Precedence and Compatibility

CONTRACT-007/010/012 security, retained source and exact transport obligations
remain governing. Existing default ABI1.2/default compiler captures remain
usable for supported ordinary schemas on the candidate's actual runtime tuple;
ABI1.3 is explicitly selected for temporal reads. Fresh source acceptance/capture
is required; prior catalog or runtime pins cannot be substituted. Publication,
managed-host adoption and a shipped migration route are separate qualification.

## Error Semantics

Unsupported ABI/carrier, source/profile drift, incomplete requirements, invalid
stored values, source limits or unsupported host execution refuse the whole
read before result publication. Native permission failures retain their original
classification. No automatic retry, fallback SQL, timezone guessing or partial
successful page is allowed. Missing and explicit null stay distinct in results
and cursor state.

## Examples

`{kind:"localTimestamp",text:"2024-11-03T01:30:00.123456"}` is civil local time.
`{kind:"timestamp",text:"2024-11-03T01:30:00.123456-04:00"}` retains an instant.
The guarded source may compare the latter exactly by UTC, while preserving its
authored text for Truss direct read/history. Neither may become a temporal Key.
