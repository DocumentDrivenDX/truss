---
ddx:
  id: truss.temporal-public-values-addendum
  type: implementation-plan
  activity: build
  authoring:
    home: repo
  links:
    - id: truss.temporal-interface-freeze
      kind: informed_by
    - id: truss.temporal-native-qualification-plan
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
---

# Explicit public temporal value route

## Scope and decision

**Selected addendum: `truss.temporal-public-values/1`.** Close the public carrier
construction/dispatch gap in freeze1 F1/F8 and TN-06–12. Add one explicit bound
facade, `assembly.temporal_values()`, with value-bearing DTOs in `truss.temporal`.
Reuse the existing assembly's host, transaction custody, native operation guards,
public catalog, groups/import/history implementation and caches. This is an
additive route into those modules, not another engine, storage model or codec.
Luna implements; Sol only writes this decision. No source/tests/workflows edited.

Freeze1 profiles and strict CONTRACT-075 remain unchanged. ExactValue, TextValue,
SequenceValue/MapValue/RecordValue and ordinary AuthoredValue/CreateObject/
UpdateObject/GroupSemanticInput constructors remain CLOSED. Ordinary assembly
methods retain their ordinary profiles/refusals even on native0.76. Merely seeing
releaseId0.76, an authored temporal selector or a localTimestamp cell MUST NOT
switch an ordinary decoder/provider into this route. Current0.75 refuses it.

Storage scope is selected scalar local property CRUD/import/read/history with
admitted missing/null presence, plus existing ordinary scalar/container siblings.
Local temporal items/arrays/maps, temporal Keys, local edge properties and new
local action/seed meaning remain refused. Ordinary supported arrays/maps keep
existing absent/null/empty/item semantics; no new nullable-item domain is implied.
The query scope stays freeze1's narrow one-Record scalar engine0.4 route; this
facade does not turn containers/edges/history into temporal SQL/query support.
Fresh-only native0.76, explicit ABI1.3, package version deferred (not55).

## Actual boundary read and minimal construction change

Current source inspected: contracts.py uses exact-class `_Carrier._shape` and
ExactValue excludes LocalTimestampValue; groups.py closes AuthoredValue and
GroupOperation; `_group_runtime.apply_group` checks exact GroupSemanticInput and
ordinary operation classes. import_runtime.py constructs closed payloads;
`_import_runtime._cell/_payload` reconstruct ordinary AuthoredValue/CreateObject.
`_record_schema._wire_cell` is also ordinary and closed. Therefore changing only
serialization or adding LocalTimestampValue to an ordinary union is incorrect.

The namespace below supplies new exact classes at those construction boundaries.
Their wire shape/operation tags reuse existing meaning under a new explicit input
profile. Internal native/Python engines MAY factor shared code; old entrypoints
must retain old selection and refusal. No subclass or cast bypasses exact-class
validation. Current dirty `_object_result` releaseId-only local branch is not a
sufficient public selection: local decoding must be scoped to this explicit
route and typed result profile instead. This is a requirement for its owner,
not an edit to that source by this planning task.

## PV-1 — public types and facade selection

Export public module `truss.temporal`; expose
`CatalogReferenceAssembly.temporal_values() -> truss.temporal.TemporalValues`.
The call is inert, takes NO connection, bool, alternate host, selection dictionary
or user-supplied native pin. It binds the same parent assembly; disposal/lock and
transaction ownership remain shared. Each operation freshly verifies actual
installed capability/authority in its existing native admission interval. The
facade call itself never claims native availability or issues authorization.
Unknown/missing/stale native capability refuses before effects, not on a fallback.

Within truss.temporal:

```text
Value = truss.contracts.ExactValue | truss.contracts.LocalTimestampValue
AuthoredValue(*, name: str, value: Value)
CreateObject(*, type_definition_pin: str, values: tuple[AuthoredValue | ordinary.AuthoredValue,...],
             ownership: ordinary.OwnershipSelection, alias: str | Absent = ABSENT)
UpdateObject(*, target: ordinary.ObjectReference, set: tuple[AuthoredValue | ordinary.AuthoredValue,...],
             unset: tuple[str,...], expected_version: str | Absent = ABSENT,
             ownership_change: ordinary.OwnershipSelection | Absent = ABSENT)
PropertyEquals(*, id: str, reason: str, target: TypedIdentity, name: str, value: Value)
```

These are immutable exact DTO classes, not aliases for the closed ordinary
classes. operation/condition discriminants remain create_object/update_object/
property_equals. PropertyEquals uses existing exact cell equality, not a new
timezone/comparator rule. Delete/ownership/references/ordinary nonlocal edge
operations and other preconditions reuse their original types unchanged.
`GroupOperation` is the union of ordinary GroupOperation and these new Create/
Update classes. `GroupPrecondition` adds only this new PropertyEquals. No new
local KeyAbsent, edge value or asserted-origin carrier is admitted.

LocalTimestampValue is the existing public54 immutable canonical26 carrier,
reexported by truss.temporal for convenience; NOT a new datetime parser.
`Value` permits old container objects whose descendants remain ExactValue.
No temporal SequenceValue/MapEntry/RecordField counterpart is introduced;
a nested LocalTimestampValue remains invalid. A top-level local value must bind
to an actual owner-admitted singular local Field; unknown retained fields cannot
acquire local meaning from this tag. Existing opaque/unknown source retention
and ordinary retained content remain unchanged.

## PV-2 — exact public operations

`TemporalValues` provides these methods. All unqualified DTO names in these
signatures refer to truss.temporal when defined here; other names are the existing
public types. Existing Outcome/Error/refusal/transaction semantics are retained.
There is no generic **kwargs forwarding or dynamic method fallback.

```python
prepare_catalog(self, documents: tuple[CatalogDocument, ...], *,
                bun_executable: str = 'bun', source_version: str | None = None
                ) -> PreparedAcceptance
# Explicitly selects temporal support0.2 and issued prep2.1/summary2.1;
# invokes the pinned public UMF inspector internally, not caller-provided output.

accept_in_transaction(self, transaction: TransactionHandle, prepared: PreparedAcceptance, *,
                      request_key: str, origin_bytes: bytes = b'{}', bun_executable: str = 'bun',
                      expected_revision: int | None = None,
                      expected_documents: tuple[CatalogDocumentExpectation, ...] = ()
                      ) -> Outcome[CatalogRegistration | CatalogUnchanged | CatalogAcceptanceRefused | CatalogCASConflict]

group_context_in_transaction(self, transaction: TransactionHandle
                             ) -> Outcome[GroupRuntimeContext | UnauthorizedPerson]
apply_in_transaction(self, transaction: TransactionHandle, input: GroupSemanticInput,
                     request: GroupRequestSelection, *, documents: tuple[CatalogDocument, ...] = (),
                     bun_executable: str = 'bun') -> Outcome[GroupApplicationResult]
dry_run_in_transaction(self, transaction: TransactionHandle, input: GroupSemanticInput, *,
                       documents: tuple[CatalogDocument, ...] = ())
# dry-run returns exactly the ordinary dry-run result union/settlement contract.
complete_in_transaction(self, transaction: TransactionHandle)
# Existing completion result union and deferred constraint checks, unchanged.

import_context_in_transaction(self, transaction: TransactionHandle
                              ) -> Outcome[ImportRuntimeContext | UnauthorizedPerson]
owned_import_context_in_transaction(self, transaction: TransactionHandle
                                    ) -> Outcome[OwnedImportRuntimeContext]
object_import_record_in_transaction(self, transaction: TransactionHandle, *, document_id: str,
    module_id: str, record_id: str, values: tuple[AuthoredValue | ordinary.AuthoredValue, ...],
    source: MapValue | None = None) -> Outcome[ObjectImportRecord]
owned_object_import_record_in_transaction(self, transaction: TransactionHandle, *, document_id: str,
    module_id: str, record_id: str, values: tuple[AuthoredValue | ordinary.AuthoredValue, ...],
    root: ObjectKeySelection | None = None, source: MapValue | None = None
    ) -> Outcome[OwnedObjectImportRecord]
import_in_transaction(self, transaction: TransactionHandle, input: ImportInput | OwnedImportInput, *,
    documents: tuple[CatalogDocument, ...], bun_executable: str = 'bun'
    ) -> ImportExecutionResult[Literal['host_adopted']]

get_object_in_transaction(self, transaction: TransactionHandle, *, document_id: str, module_id: str,
    record_id: str, object_id: int, maximum_bytes: int = 1048576
    ) -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadRefused | ObjectReadUnavailable]
page_objects_in_transaction(self, transaction: TransactionHandle, *, document_id: str, module_id: str,
    record_id: str, limit: int = 100, cursor: ObjectPageCursor | None = None,
    maximum_bytes: int = 1048576
    ) -> Outcome[ObjectPage | ObjectNotFound | ObjectReadInvalid | ObjectReadRefused | ObjectReadUnavailable]
lookup_key_in_transaction(self, transaction: TransactionHandle, *, document_id: str, module_id: str,
    record_id: str, key_id: str, values: tuple[str | TextValue | BooleanValue, ...],
    original_document: bytes | None = None, maximum_bytes: int = 1048576,
    bun_executable: str = 'bun'
    ) -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadRefused | ObjectReadUnavailable]

page_history_in_transaction(self, transaction: TransactionHandle, *, entity: HistoryEntity,
    cursor: HistoryCursor | None = None, maximum_events: int = 4096, maximum_bytes: int = 8388608
    ) -> Outcome[HistoryPage | HistoryUnavailable]
reconstruct_in_transaction(self, transaction: TransactionHandle, *, entity: HistoryEntity, version: int,
    maximum_events: int = 4096, maximum_bytes: int = 8388608
    ) -> Outcome[HistoricalRecord | HistoricalDeleted | HistoryUnavailable]
```

Import record identity types are the existing public types: their payload is an
ExactArtifact plus explicit payload_profile, not an ordinary decoded ExactValue.
History retains its existing original byte/image results; it does not create a
new Date/datetime decoding path. New ImportInput.records admit ObjectImportRecord
only; new OwnedImportInput.records admit OwnedObjectImportRecord only. Ordinary
edge imports remain on their existing route; mixed edge/object temporal import
inputs refuse rather than guessing a payload profile. Mixed GROUP operations may
reuse ordinary edge DTOs with ordinary exact values; local edge values refuse.
This route introduces no local edge API.
Batched/chunked import need not gain a separate temporal DTO in this cut: per-record
and existing atomic owned import above cover public local import. No old batching
method may accidentally accept a new payload/input profile.

## PV-3 — context, wire tags and replay

All selected profile hashes MUST be produced from actual reviewed definition
bytes and enrolled in the genuine0.76 manifest. No SHA is fabricated here.
Value profile is the already frozen `truss-exact-value-temporal/0.1` ProfilePin.
It composes unchanged ordinary value meanings with the singular local capability;
it does not reassign truss-scalar-string-values/0.6 or overwrite that definition.

| Selected wire | Exact identity |
| --- | --- |
| Group semantic input | `truss-group-temporal-input/0.1.0` |
| Request identity | Existing `truss-request-identity/0.1.0` framing, but inputProfile exactly `truss-group-temporal-input/0.1.0` |
| Per-record import input / payload | `truss-import-temporal-input/0.1.0` / `truss-import-temporal-payload/0.1.0` |
| Atomic owned import input / payload | `truss-owned-import-temporal-input/0.1.0` / `truss-owned-import-temporal-payload/0.1.0` |
| Rootless direct object result | `truss-python-temporal-scalar-object/0.1` |
| Owned direct object result | `truss-python-temporal-logical-object/0.1` |
| Direct object page / cursor route | `truss-python-temporal-object-page/0.1` |

Each new input retains exactly the corresponding ordinary envelope's fields,
ordering, bounds and camelCase spelling, changing only the selected interfaceVersion,
actual context-issued profile pins and permitted local VALUE occurrences.
The new mutation profile is `truss-owned-temporal-graph/0.1`, per-record import
profile `truss-temporal-object-import/0.1`, owned import profile
`truss-owned-temporal-object-import/0.1`; payload ProfilePin identities/versions
match their selected wire identities in the table (identity is the part before
slash). Preserve their ordinary object-operation/atomicity/policy definitions and add
only explicit selected local value transport. Old profile definitions/hashes
stay unchanged. Context-owned layout/adapter/policy pins retain actual current
values; they cannot be invented or taken from the old native0.75 tuple.
Payload local cell is EXACTLY `{kind:'localTimestamp',text:<canonical26>}`.
No temporal value is allowed in Keys, assertedOrigin, source facts, orderKey or
edge property values. ordinary NullValue/ABSENT semantics remain unchanged.
Group results and import reports retain original shapes and original selected
configuration/profile evidence; they contain no new local value carrier slots.

New GroupRuntimeContext has the same original fields/methods as ordinary plus
immutable `query_abi: ProfilePin`, `release_id: str`, `release_sha256: str` from
native capture. `.input(operations, asserted_origin: MapValue, *, preconditions=())`
returns the new GroupSemanticInput; `.request(request_id: str)` returns new
namespace RequestPresent/RequestIdentity with the temporal inputProfile above.
All remaining RequestIdentity fields are identical to ordinary; RequestNone is
reused. The group input fields remain layout_profile, mutation_profile,
value_profile, catalog, operations, asserted_origin and preconditions. No caller
boolean is serialized as authority. Ordinary contexts never issue temporal pins.

New ImportRuntimeContext/OwnedImportRuntimeContext preserve ordinary field names
and `input(records, *, load_id, asserted_origin)` / `object_payload(values, *,
source=None)` / owned `object_payload(values, *, root=None, source=None)` signatures,
returning the new input/payload profiles. Their immutable capture also carries
the same query_abi/release_id/release_sha256 fields. Object keys/identity still
come from the existing accepted native key-selection machinery. Existing
per-record rejection/skip/partial-report and owned-import atomicity remain exact;
never turn the former into atomic all-or-nothing by accident.

`truss.temporal.freeze_group_request(input, request, *, documents)` preserves the
existing freeze_group_request Outcome contract and FrozenGroupRequest artifact
fields, but admits only the new exact input/request types/profiles. Existing
FrozenGroupRequest stores original bytes, so no additional frame fields are
needed. Add facade `recover_group_request_in_transaction(transaction, frame)`
with the existing Outcome[GroupApplicationResult] return contract, accepting only
frames whose original input/request bytes select this route. Ordinary recovery
refuses such frames. Preserve complete original bytes/digests/receipts through
repeat, changed-request conflict, restart and lost-reply recovery; no conversion
to ordinary0.1 input/profile to reuse a receipt. Original wire equality remains
independent of canonical value equality.

## PV-4 — native dispatch and capability checks

Use explicit native person entrypoints; factor shared private bodies without
changing ordinary selection. Enroll these exact NEW signatures in the actual
native0.76 invocation/capability/dependency inventory:

```text
truss.person_temporal_group_context(text,text) -> bytea
truss.person_apply_temporal_group(bytea,bytea,bytea,text,text) -> bytea
truss.person_apply_temporal_group_prepared(bytea,bytea,bytea,text,text,jsonb) -> bytea
truss.person_temporal_import_context(text,text) -> bytea
truss.person_temporal_import_key_selection(text,text,text,text,text) -> bytea
truss.person_temporal_import_object_identity(bytea,bytea,bytea,text,text) -> bytea
truss.person_temporal_writer_schema_basis(bytea,bytea,text,text) -> bytea
truss.person_get_temporal_object(text,text,text,bigint,int,text,text) -> bytea
truss.person_page_temporal_objects(text,text,text,int,int,bytea,text,text) -> bytea
```

Group application arguments retain original input, original documents, request,
expected_release, expected_digest; prepared adds the exact original prepared
schema packet. Context signatures take expected_release/expected_digest.
Get-object arguments follow ordinary get_object. Page arguments are
selected_document, selected_module, selected_record, page_limit, maximum_bytes,
original_cursor, expected_release, expected_digest, exactly as read from pages.sql
and person-entrypoints.sql. Import key-selection takes document/module/record and
expected release/digest; import object-identity takes original_identity,
original_document, tuple_bytes, expected_release, expected_digest. Writer schema
basis takes original_input, original_documents, expected_release, expected_digest.
Import still
uses the existing per-record/owned orchestrators and actual authority/identity/
source/report APIs, invoking the selected temporal group provider for local
records. No new arbitrary SQL gateway or direct table grant.

Each new context and execution validates the actual installed native release
`truss-catalog-runtime/0.76-temporal-candidate`, full release digest, exact
`truss.query_temporal_abi()` identity/version1.3/hash, enrolled temporal value/
input/payload profiles and original source-native descriptor coverage. Checks run
through original person/role/ACL/READ COMMITTED/current-authority/deadline guards,
not via an administrator supplied by the facade. ABI1.3 is checked as actual
installed capability, not by rewriting an ordinary ABI1.2 capture.

Nonlocal shape-only metadata/key-selection can reuse its ordinary native routine
under the same guarded operation; it cannot return an ordinary group/import
context and mutate its valueProfile in Python. Explicit new native contexts
produce the selected profile directly. Source-native validation still checks
accepted source/owner local descriptor iff correspondence; facade selection
alone cannot turn a timestamp/unknown property into localTimestamp.

Local text input uses existing canonical26 constructor and the strict F7 native
helper: require canonical_text('local',text)=text before publication. UMF's strict075
remains semantic owner. No Date parser, host timezone, rounding, guessed codec,
expanded token grammar or datetime constructor is added. Date/instant direct
storage retains its original admitted exact spelling; the narrow temporal query
route independently enforces strict075 on selected source values.

Native schema/property/cache/value checks must accept canonical local only under
its actual selected property family/capability. Shared validators must be able to
verify legitimately stored local properties, but ordinary ingress/wire providers
still refuse local input and ordinary result decoders refuse local output. Reject
local data through an ordinary request tag even on0.76; no manifest-only switch.
On0.75/new capability mismatch return the existing relevant profile-unavailable/
unsupported refusal before effects. Preserve original errors and settlement, not
empty reads or fallback conversion.

## PV-5 — decoding, caches and public acceptance

New namespace ScalarObject/LogicalObject/ObjectFound/ObjectPage DTOs retain
ordinary fields/properties and admitted primitive/ordinary-container values,
adding LocalTimestampValue only in selected top-level object values. Their profile
tags are PV-3; retained unknown values do not gain local semantics. Native result
must bind valueProfile, queryAbi and actual release tuple before local decoding.
Missing stays omitted, null stays the existing direct-read None, value becomes
the standalone immutable LocalTimestampValue. Do not send localTimestamp through
TextValue(kind=...). No local descendant in ordinary SequenceValue/MapValue. The closed new native
object result envelope is the ordinary corresponding envelope with its new
profile and added `valueProfile` and `queryAbi` pins. The closed new native page
envelope is its ordinary counterpart with new profile and the same two added
pins, containing the new object envelopes. Existing releaseId/releaseSha256 and
all other original fields remain. Native cursor opaque contents bind the route
without exposing or inventing another cursor decoder.

Namespace ObjectPageCursor retains ordinary immutable cursor fields plus
value_profile:ProfilePin and query_abi:ProfilePin. Decision
`truss.temporal-public-values/pv5-cursor-custody/1` selects one additional REQUIRED
keyword-only field on this frozen temporal DTO:

```python
original_bytes: bytes = field(repr=False)
```

Construction requires exact immutable bytes of length1..65,536; no default,
implicit encoding, I/O or constructor-issued authority. This corrects the
unreleased temporal DTO only. Ordinary cursors and public54 remain unchanged;
identity, source_epoch and other fields keep their original meanings.

The closed native temporal continuation retains its existing metadata and adds
exactly `originalCursorBase64`, a canonical base64 encoding of the native-issued
sealed bytes. Decode it losslessly into original_bytes; account for the complete
encoded continuation in the page's existing byte budget. Pass original_bytes
UNCHANGED as original_cursor to the existing person_page_temporal_objects
signature. Never rebuild an authoritative cursor from the DTO metadata.

The native seal uses the installation-owned secret and existing checked sealing
mechanism, with a distinct DIRECT-PAGE route discriminator. Bind current person,
installation/source epoch, release digest, document/module/record/type,
definition pin/catalog revision, value profile, ABI and afterId. Verify exact
closed framing, seal and current selection/authority before obtaining page rows;
require agreement between returned metadata and the sealed original context.
Python neither owns a seal codec nor gains a secret. Unsigned earlier temporal
cursor objects, missing bytes, changed metadata/token, wrong person, and
ordinary/Weft-query cursor substitution refuse; never patch the native token.
Retain live paging and existing per-call limit/byte semantics, with no held
cross-page snapshot. This is direct object paging, distinct from the frozen
Weft full-sort-tuple continuation contract.
Lookup Keys remain the ordinary supported non-temporal domain; no numeric
selected-Key temporal QUERY paging is added by ordinary direct key lookup.

`_record_schema`, `_record_preparation` and `_schema_memory` may share their
compiled representation, with an explicit selected value-profile discriminator.
The new prepared patch packet selects
`truss-python-temporal-record-patch/0.1`; its fields equal the existing record
patch packet fields plus exact `valueProfile` and `queryAbi` pins. Original
input/documents/schema/operation digests and native patch validation remain
mandatory; no rename of a cached ordinary packet. If the prepared optimization
is unavailable, dispatch only the validated UNPREPARED TEMPORAL provider, never
the ordinary provider. A missing whole temporal capability still refuses.
Cache identity includes native release/digest, value/input profile and ABI pin,
original document/declaration/nativeDescriptor/owner/presence digest, catalog
revision and existing person/authority basis. Cached schema permission is never
cached grant authority. No cache hit reinterprets a2.0 timestamp as2.1 local or
admits stripped descriptors. A temporal miss is not retried through ordinary
codec. Existing compiled ordinary container/item semantics and limits remain.

Decision `truss.temporal-public-values/pv5-prepared-completion/1` selects completing
the temporal prepared writer in this delivery. The original contract permits
optimization unavailability; that remains the safe fallback for ineligible
operations while implementation proceeds, not a completed optimization claim.
Use the existing person_temporal_writer_schema_basis and prepared temporal
entrypoints, shared record-schema/patch/cache and protected native writer. Add
an explicit temporal discriminator and the selected profile/pins; do not add an
ordinary-packet relabel, separate semantic validator or new public method.

Preparation must bind exact original input/documents, current native schema,
Prep2.1 declarations/owner/nativeDescriptor/presence and operation ordinals.
Native admission rechecks original correspondence, current revision and person
authority before using the patch. A cache hit cannot supply authorization.
Ineligible preparation may choose the validated unprepared TEMPORAL provider
before dispatch. A supplied malformed/stale/wrong-profile or altered patch must
refuse before effects; never discard it silently or catch refusal to retry an
ordinary/unprepared write. Eligibility does not broaden local values, Keys,
containers, ownership or retained-content semantics.

Facade prepare_catalog is the explicit PUBLIC entry to Noether's existing
Prep2.1/noncompact machinery; build the exact owner inspector invocation/result
internally, retain original bytes/unknown content, reject error/fatal diagnostics
and enforce inverse local coverage. accept requires a genuine issued preparation
selecting support0.2/prep2.1/summary2.1 and preserves original acceptance-input0.2.0
bytes; it may reuse existing protected accept machinery after native capability
admission. No caller-forged inspection or new acceptance envelope version.
Prepare itself is inert/source work; acceptance and data operations verify the
real installed capability. Existing ordinary preparation/acceptance defaults
remain exact and cannot infer this profile.

TrussTarget query execution remains the explicit frozen EngineRead temporal
profile route in truss/access.py, not a method of TemporalValues. It reuses the
same selected low-level local-cell decoder after original engine/native custody
checks. Do not change owner inspection or Access EngineRead APIs to implement
this public data facade.

## Execution and qualification

Noether may implement PV-1–5 now in the existing isolated writer scope. No
additional human approval is missing; retain fresh-only0.76 and unassigned package
version. Keep helper/source/snapshot/security/fresh-install work independent.
Actual new profile/ABI/inventory digests and canonical source commits remain
implementation outputs; no current native support or test pass is asserted here.

TN-06–12 must use the NEW public facade/DTOs for happy-path local acceptance,
group CRUD, imports, cache hit/miss, read-only read, history and replay; they may
not bypass _Carrier or privately manufacture cells/contexts. Add paired negatives:
ordinary AuthoredValue/SequenceValue/MapValue rejects local; ordinary group/import/
read rejects temporal input/output even on0.76; facade operations refuse0.75;
forged/mixed profile/ABI/native descriptor/cursor/frame refuses before effects.
Preserve ordinary date/instant/container/nullable regressions and HF62 unchanged.
This addendum grants no new temporal container, Key, edge-property or query domain.

Include PV5 direct-page and prepared-writer controls in the SAME coherent
candidate campaign: public multi-page local reads with exact opaque-byte custody;
wrong actor, source/revision/release/profile/ABI/selection, altered seal/metadata,
unsigned cursor and ordinary/query-route negatives; current module/root
revocation, complete-result byte limits, read-only access and confirmed cleanup.
Prepared controls must observe the actual eligible prepared entrypoint on cold
and warm paths, preserve outcomes/effects/diagnostics and original request bytes
against independent expectations, exercise safe ineligible temporal fallback,
and refuse altered source/descriptor/presence/ordinal/patch/revision/authority
without partial effects. Reuse existing rollback, dry-run, replay/import and
ordinary/HF62 controls where their input closure matches. Authored scope and
collection are not native qualification; no separate campaign is selected.
