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

No DDL. ID reads include type identity to avoid wrong-type matches. Baseline key lookup joins the fixed canonical key row to its object under one consistent snapshot/role; the selected full-byte bucket candidate uses exact namespace/key bytea plus a typed object join, with no baseline or digest-only fallback. Composite keys preserve declared component order; missing components refuse before database effects. Historical last-written revision identifies the encoding/meaning needed to interpret existing values; current catalog changes cannot silently coerce them. Upcoming document-qualified catalog identity remains D-04.

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
