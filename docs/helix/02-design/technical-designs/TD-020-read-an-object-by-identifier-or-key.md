---
ddx:
  id: TD-020
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-020
      kind: informed_by
    - id: SD-005
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
---

# TD-020: Exact object lookup

**Story:** [[US-020]]. **Parent:** [[SD-005]]. **Feature:** FEAT-005.

## Technical Approach

Implement the contract's direct identifier and canonical-key lookup templates. This is storage access, not a second SQL compiler: Weft retains source query parsing/planning. Use US-009 canonicalization for complete ordered key components and US-007 exact decoding. Return the record's last-written revision separately from the catalog/read-context pin; they need not be equal after a revision that did not change the record.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/reads/object.ts` | Typed ID lookup and native record metadata | US-020-AC1 |
| `packages/postgresql/src/reads/key.ts` | Parameterized key-to-object lookup in one read context | US-020-AC2, US-020-AC3 |
| `packages/core/src/keys/request.ts` | Exact component completeness/order validation | US-020-AC4 |
| `tests/reads/lookup.test.ts` | Independent native ID/key/content/revision fixtures | All criteria |

Components are new and reuse shared codecs instead of duplicating query semantics.

## API/Interface Design

CONTRACT-004's draft direct-read binding supplies lookup request/result shapes and ordered key pins. Consume its validation, role/snapshot and non-disclosure rules; typing is not native qualification. Unsupported old/current value or key interpretation refuses explicitly.

CONTRACT-004 owns get_object/find_by_key and invalid/not-found behavior; CONTRACT-001 owns key/record representation; CONTRACT-007 owns read context and exact transport. The authored closed result wire preserves record revision versus read-context revision; complete native decoder/profile adoption remains required before publication. No new SQL dialect or compiler interface is defined here.

## Data Model and Integration

No DDL. ID reads include type identity to avoid wrong-type matches. Baseline key lookup joins the fixed canonical key row to its object under one consistent snapshot/role; the selected full-byte bucket candidate uses exact namespace/key bytea plus a typed object join, with no baseline or digest-only fallback. Composite keys preserve declared component order; missing components refuse before database effects. Historical last-written revision identifies the encoding/meaning needed to interpret existing values; current catalog changes cannot silently coerce them. Document-qualified catalog identity is selected by accepted ADR-004; complete installed mapping/authority remains unqualified.

## Security and Performance

Host authentication/policy controls both key and object visibility. An invisible record cannot leak through key existence or its ID. Parameterize key text, including quote/injection-looking strings. Baseline primary/key indexes and proposed bucket routing have distinct native capacity/work obligations; exact full-byte equality remains required after bucket routing. Capture native plans and latency per qualified target rather than inventing a new SLA. No prepared-statement requirement is inferred.

### Python preview key-profile selection

Select the existing full-byte bucket candidate as the P2 reference key-read
implementation target. Use its fixed read-only lookup descriptor with original
namespace/key bytes, qualified key definition and typed object join. Digest routing
narrows candidates only; complete byte equality and original context/source
correspondence determine the result. This is an engineering target selection,
not native profile admission or a released layout claim.

Do not fall back to baseline text lookup when bucket mapping, index readiness,
source interpretation, authority or resource admission is unavailable. Return the
existing unavailable/refusal outcome once. Baseline text remains a separately
qualified legacy route requiring its own explicit installation/profile binding;
it is not another encoding of this selected bucket request. Embedded callers
cannot choose the physical store with a request field or unregistered SQL.

Before preview qualification, compose complete bucket writer/guard/read privileges,
original UMF key encoding and document-qualified catalog mapping, selected decoder,
finite native candidate/work bounds and final security publication drain. Run
STP-020's exact-key/collision/hidden-holder/duplicate-row controls and compare
original key bytes, typed holders and native plans independently. Missing selected
support blocks the key capability; it cannot return not_found from an incomplete
scan. All complete installed cases remain not_run. ADR-004 already settles
document qualification; no D-04 product decision remains pending.

## Testing

STP-020 owns allocation. Independently seed metadata/values, exercise scalar/composite keys and exact large numerics/null/absence. Accept a new catalog revision without modifying the record and assert the returned last-written revision remains old while read pin is new. Missing and hidden records return qualified not-found behavior, never fabricated empty records. Supplement with concurrent key update/deletion in a consistent read snapshot.

## Migration and Rollback

No schema migration. Incompatible codec/catalog pins refuse rather than guess old meaning. Read failures change no data or durable acknowledgement. A rollback to prior qualified package/profile preserves stored content; changed key canonicalization requires its separate migration.

## Shared direct decoder handoff

CONTRACT-004 now owns D0–D7 for both lookup and page paths. lookup.ts/pages.ts select the exact registered fixed statement descriptor and original admitted slots. decode-record.ts consumes bounded field carriers, exact source-domain/definition interpretation and private match/context correspondence. The original executor owns dispatch, framing/termination, cancellation and resource custody; the existing authority coordinator owns current-authority closure/publication validity. Complete output is prepared privately and published once only after successful result closure and final operation arbitration.

Implement one shared sequence with category-specific descriptors. A text-projected native ID retains its pinned source domain; a driver's text result type does not supply that domain. Complete native termination is required for not_found. A malformed/duplicate second lookup row cannot leave a successful first row. Missing, extra or duplicate result aliases refuse; unknown native meaning remains explicit. Actual descriptor/transport/parser/codec/coordinator producers are selected-profile dependencies, not inferred capabilities. No private observations enter DirectRecord or diagnostics. STP-020 carries the actual framing/fault/publication controls; STP-021/022 apply the same sequence to page lookahead.

## Implementation Sequence

1. Create red native lookup and component-validation fixtures.
2. Reuse exact codec/key validation, implement single-context templates.
3. Resolve metadata/policy schema gates and qualify concurrent/visibility behavior.
4. Keep source-language integration in the separate Weft slice.

## Risks and Gates

Current/last-written catalog interpretation must be explicit for in-place meaning changes. Key family/null policy inherits TD-009 gates; numeric preservation inherits TD-007. Visibility/report errors and document identity remain shared policy dependencies. This bounded lookup does not establish Weft key ordering, paging or arbitrary query support.

Use CONTRACT-004's closed [lookup request](../contracts/direct-lookup-request-v0.1.schema.json) and [result](../contracts/direct-lookup-result-v0.1.schema.json) wires. Exact qualified ownership, authored local key mapping, component order/facets/encoding and returned selection/current revision are semantic admission obligations. Resource exhaustion refuses the whole lookup as unavailable/resource; it cannot produce not_found or partially disclose a record. Reuse UMF's selected encoder and the existing native binding; no duplicated comparator/SQL compiler. Native/resource profile selection remains open.

### Native lookup design handoff

CONTRACT-004's direct-lookup-observation-v0.1.proposal.sql authors four fixed statements: typed object ID, read-only full-byte bucket key, global edge ID and baseline key text. object.ts/key.ts handle selection; shared lookup.ts owns exact statement binding, while decode-record.ts owns complete category projection. keys/read.ts in TD-009 delegates here rather than reproducing queries or a second decoder. Native second-row observation refuses incompatible identity; only a complete qualified empty observation may return not_found.

CONTRACT-005's protected bucket-read boundary restricts complete original context to registered private observation/owner admission; the read owner cannot inherit hidden integrity-observer privileges. Native protected entrypoint signatures/bodies, original-context registry/caller linkage, current-authority coordinator and exact value/metadata/codec profiles remain concrete authoring outputs. Ordinary app grants cannot expose matched context by treating the draft as public SQL.

The named direct-lookup resource candidate bounds request, full namespace/key/context carriers, native/public bytes, both observed rows, owner/submission/allocation/time dimensions. These values are proposals, not producer/feasibility evidence. Sixteen pinned UMF source drafts pass preservation/reload/export; the lookup's four SELECT statements remain unhandled by partial DDL extraction. Neither source preservation nor future native test names closes these design/adoption gaps. STP-020 now contains the fixed-query, collision, read-only, private-context, resource and current-authority controls.


### Protected disclosure and complete source admission — 2026-10-12

CONTRACT-005 already separates public read ownership from private integrity
observation; shared UMF CONTRACT-063 requires complete admitted facts, original
source correspondence and held current authority. The current Python get routine
is a complete-read candidate: its non-bypass definer owner and row_security=off
refuse forced RLS. It is not the protected-disclosure owner realization.

A disposable native experiment changes only that routine's setting to on.
Public get then returns the eligible object and hides the denied object, but
still returns the eligible object after a hidden required field is removed.
Excluded complete-source validity returns false. This is a counterexample to
using filtered success as source admission, not a proposed production setting
change. Original settings are restored. Twenty-eight native observations, five
conditional Z3 checks/replays and an independent64-assignment Boolean oracle are
retained in `../../04-build/evidence/security-filtered-read-completeness-20261012/receipt.json`.
The model is exactly two rows/two validity cuts; it proves no native guard or
implementation refinement. Old preflight with a changed cut admits a modeled
malformation; coherent complete preflight excludes it under the stated premises.

Implement the existing contract boundary in this order:

1. The protected collector owns complete selected catalog/object/property/key/
   edge coverage, original native mapping and exact codecs. Capture invalid or
   hidden carriers before filtering. It emits no public row, count or raw fact.
2. Bind complete validation to the disclosure's actual source/data cut. Select
   and qualify native exclusion or integrity-preserving writer participation;
   a preceding statement, catalog revision or unchanged counts is insufficient.
   READ COMMITTED statements may observe different data cuts. Original schema/
   policy/role/fact changes remain covered by the authority protocol as well.
3. Install a separate narrowly privileged read owner and its exact registered
   original-person capture/check path under CONTRACT-005. The current runtime
   person helper requires the installation owner: granting a new read role alone
   cannot compose that helper. Adopt and qualify the role/context transition
   before exposing the protected entrypoint; preserve rejection of direct native
   grants on ordinary API callers. No caller-selected elevation is admitted.
4. Apply native row policy to disclosure under that read owner and original
   caller, preserving business keys and current module/policy authority. Keep
   complete collector/integrity owners and callbacks outside filtered visibility.
5. Decode privately, revalidate the held source/authority/context through final
   publication and return the contract's found/not-found/refusal outcomes.
   Missing complete admission cannot become not_found or a partial success.

Reuse the existing coordinator, mapping and decoder contracts; no additional
SQL dialect, policy evaluator or request-supplied trusted evidence is introduced.
Exact installed owner/capture/collector/coherent-cut profile realization remains
unimplemented. Test key, page, count, traversal, retained carriers and hidden
authorization facts separately before qualifying their surfaces. Row RLS does
not provide property masking. Keep the existing complete-read profile available
and reject unsupported protected composition rather than changing all routines
to row_security=on. Activation and rollback preserve prior qualified protection.


Selected-source exclusion feasibility now has an executable native regression
in `packages/python/tests/test_security_graph_source_cut_native.py`. In the
disposable on-setting experiment, the excluded assessor holds SHARE table locks
on object/prop_def/type_def before complete preflight. An independent writer's
RowExclusiveLock is observed ungranted in pg_locks. The actual public read returns
while that writer is blocked; releasing the guard lets its hidden-row corruption
commit, and the next preflight detects the incomplete source. Thirty-four total
observations are retained in
`../../04-build/evidence/security-native-source-exclusion-20261012/receipt.json`.
This is a candidate native mechanism for the selected row/property/type cut, not
an admitted security guard. It blocks all writers to those relations, even other
types; performance and finite contention outcomes must be qualified before
adoption. Role/policy/routine/private-fact changes and buffered release are not
covered by these table locks. Preserve their separate authority/coordinator gates.


### Narrow native read-owner feasibility — 2026-10-12

The same native regression now instantiates a distinct nonlogin/noninherit/
nonbypass read owner for an isolated fixed business-key lookup. It has SELECT
only on object id/type_id/props, no table-wide SELECT and no retained/journal/
mutation/sequence/schema-create rights. Its routine uses qualified dependencies,
fixed search_path and row_security=on; ordinary callers get EXECUTE only. Native
policy verifies the original session caller while current_user is the read owner.
Authorized exact-key lookup returns the eligible label; denied/missing/injection-
looking keys return no rows. Caller SET ROLE and raw bag/retained/journal reads
refuse42501. An independently owned nested definer wrapper keeps the original
authorized caller and cannot replace an unauthorized original caller with its
own execution privilege. Fifty-six total observations and failed attempts are
retained in
`../../04-build/evidence/security-narrow-read-owner-20261012/receipt.json`.

This realizes the native privilege transition in a test entrypoint, not the
Python public get API. That API still requires installation-owner context under
runtime_person. Production adoption must implement its registered read-role/
original-person check, current module and ontology authority, complete source
enrollment and held publication protocol before selecting this owner. Never
change the existing helper to accept an arbitrary current_user or caller role.
Selected props column access is row protection only; field masking and decoder
privacy require separate faithful projection. Policy installation must drain
earlier read transactions; native policy DDL cannot be inserted into their held
read transaction. Rollback must retain the prior registered protected profile.


### Selected native policy correspondence — 2026-10-12

The native regression now retains71 observations. Independent fixture inventory
includes native object owner/RLS/FORCE flags, every policy on object, selected
original caller/read/wrapper role attributes and every overload/definition/owner/
configuration/ACL for its three routines. An added permissive policy leaves
source validity true while exposing the denied row. Changing only the predicate
helper body also exposes it. Changing read-owner BYPASSRLS exposes it on fresh
connections and defeats the nested original-caller restriction. Each mutation
invalidates exact retained correspondence; originals restore exactly. A reused
transaction still hid the row after role drift; retain that observation without
inferring a cache/freshness mechanism or using it as authority.

Four conditional Boolean policy-composition checks/replays and an independent
16-assignment oracle distinguish permissive widening from restrictive narrowing.
Sources, formulas, failed expectation and native outputs reside in
`../../04-build/evidence/security-native-policy-correspondence-20261012/receipt.json`.
The inventory comparator is still a fixture primitive. Production adoption must
authenticate its original installation closure, observe the complete reachable
call/role/ACL/dependency inventory and hold authority exclusion through release.
Checking only known policy names, source row validity or old successful plans
cannot discharge these obligations. Unknown additional policy or callable
dependency blocks the selected closed profile; no capability is inferred from
a successful label-only lookup. Current public runtime code remains unchanged.


### Public-created ontology membership realization — 2026-10-12

A separate repository regression creates13 objects and12 edges through the
actual public catalog/group API: Clients, Projects, Staff, Resources and keyed
Assignments with active flags. Assignment remains a Record; staff-assignment,
assignment-project and resource-project remain opaque Relationships. Candidate
condition/fold lowering consumes actual Record Key witnesses and typed incidence
carriers, without inventing a Record or field for an edge. Private views project
real native graph rows with typed locator joins to original business keys.
Original subject binding comes from SESSION_USER inside the private definer;
ordinary callers cannot execute the two-argument binding helper or adopt the
fact owner. No storage ID substitutes for a business key.

Forty-four native observations pass on PostgreSQL18.6/runtime0.17-candidate.
Alice seesRA/RAB, Bob seesRB/RAB, outsider seesnone; common Client C does not
widen visibility, inactive assignments grant none, multiple owners grant only
through a matching Project and ownerless data stays hidden. Private Assignment
view/native edge reads refuse and Assignment object counts remain zero. Fresh
statements observe a committed excluded-admin AA deactivation; Bob stays
unchanged and restoration restores Alice. These are data-change observations,
not revocation drain or enrolled-writer acceptance.

The producer fixture passes strict typing;25 candidate-condition tests and Python
boundaries pass. Evidence: `../../04-build/evidence/security-public-ontology-20261012/receipt.json`.
The ontology lives in adoc with zdoc's independent baseline retained. Duplicating
the whole ontology hit the existing4-MiB decision cap; the larger atomic seed
uses supported60-second operation/statement limits after default-deadline
cancellations. Those failed attempts and exact bounds remain explicit.

This is actual public-created graph membership feasibility, not protected Python
read adoption or a complete backend case. Fixture-authored candidate conditions
are not authenticated compiler output. Complete source enrollment, current
mapping and authority exclusion, callable closure, final release and original
public writer/revocation integration remain required before profile admission.


### Indeterminate private facts require operation refusal — 2026-10-12

The real ontology regression now separates the private text decision fold from
the Boolean native row-predicate adapter. Only permit/deny may become Boolean.
NULL, indeterminate or unknown states raise generic55000 rather than silently
become false. Removing the required active cell from inactive AB invalidates
complete Assignment source and produces indeterminate even for otherwise
authorized Bob. All three ordinary callers' list/count operations refuse with
primary message `security facts unavailable`; restoring the cell restores
source validity and original Bob visibility. Fifty-four native observations
and Python boundary checks pass; sources/results are retained in
`../../04-build/evidence/security-incomplete-ontology-facts-20261012/receipt.json`.

Adopt this refusal distinction when composing the real protected entrypoint.
Do not translate unavailable facts into a successful empty collection. This
fixture guard covers the selected required Boolean domain only; complete missing
endpoint/key/subject coverage still requires original source enrollment and
coherent authority/data admission. Whole native diagnostic/wire/trace privacy,
streaming release and public driver outcome mapping remain separately required.
Current runtime code is unchanged and no full backend case is promoted.
