---
ddx:
  id: truss.query-export-source
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-005
      kind: informed_by
    - id: SD-005
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
---

# Native query export sources

**Type:** library/storage boundary. **Version:** 0.1, unreleased.

## Purpose

Provide validated PostgreSQL sources for a separately selected export compiler
profile, without the ordinary query sources' cumulative row and byte limits.
This contract alone does not qualify a public SDK stream or a compiler release.

## Scope and Boundaries

Truss owns these native sources and their installation. Weft owns their explicit
selection and lowering; the host owns the connection, deadlines and PostgreSQL
resource configuration. Ordinary queries and bounded export backend 042 retain
their existing source functions and limits. Protected queries and temporal SDK
support remain outside this profile.

## Normative Surface

| Function | Arguments | Result |
| --- | --- | --- |
| `truss.query_export_objects` | `binding jsonb, selected_type int` | `TABLE(id bigint, props jsonb)` |
| `truss.query_export_edges` | `binding jsonb, selected_relationship int` | `TABLE(id bigint, source_id bigint, target_id bigint)` |
| `truss.query_export_page_objects` | `binding jsonb, selected_type int, selected_key text` | `TABLE(id bigint, props jsonb)` |

The exact installed release manifest MUST bind these routines and their bodies.
A distinct compiler/export profile MUST select them explicitly; ordinary or
bounded-export SQL MUST NOT be rewritten to select them after compilation.

Every function MUST validate the complete original binding through `query_scope`
before and after its source processing. Record/relationship selection, exact
values, physical roots, endpoints and ownership readers retain the ordinary
sources' checks. Every root's original document/module MUST be present in the
selected binding; complete selected-document module admission covers all those
root owners. A stream MUST additionally perform fresh complete admission before
and after each fetch, under its separately qualified exclusive connection lease.

The ordinary 0.5 binding's `maximumScanRows` and `maximumResultRows` remain valid
metadata for ordinary queries; this profile does not apply them to export source
cardinality. `maximumBytes` bounds each source row's property-map UTF-8 JSONB text,
not cumulative source bytes. Metadata bounds and per-value validity remain active.
The page source MUST validate the complete declared Key and refuse duplicate
logical Key tuples across its complete source before returning buffered rows.

These sources MAY buffer their complete validated results under PostgreSQL's
normal tuplestore, `work_mem` and spill behavior. Fetching the first page MAY
scan, validate, materialize and sort the complete source and exceed its deadline.
This profile does not promise server memory proportional to client page size or
successful completion at arbitrary scale. Client row/page bounds and deadlines
remain required by the stream contract.

## Precedence and Compatibility

Existing ordinary source signatures, limits and logical ABI remain unchanged.
This profile is opt-in through a distinct compiler target and exact native release
binding. It confers no additional document/module authority. Bound versus natural
exhaustion, terminal failure and owned cleanup follow the SDK stream contract.

## Error Semantics

| Condition | Result | Recovery |
| --- | --- | --- |
| Invalid selection/binding or unsupported value/Key profile | Existing `22023`/`0A000` refusal | Correct the request; no internal retry |
| Missing current reader | `42501` refusal | Discard the page and close the owned stream |
| Malformed stored value, root, endpoint or duplicate Key | Existing native invariant refusal | Discard the page; repair through the owning system |
| Row carrier exceeds `maximumBytes` | `54000` refusal | Discard the page and close the owned stream |
| Native deadline expires | `57014` cancellation | No partial page; settle owned cleanup explicitly |

## Examples

With an admitted exact original binding, `SELECT count(*) FROM
truss.query_export_objects($1::jsonb, $2::int)` may validate 10,001 rows where
`query_objects` refuses its 10,000-row source bound. This is native source evidence,
not a generated public stream. An export compiler supplies its own authored-Key
ordering and the host fetches bounded pages from the resulting owned cursor.

## Verification

On PostgreSQL 18.6 / pgserver-pg18 18.6.1 / psycopg 3.3.6, the two native
source cases in `test_query_export_sources_native` and three populated published
native68 upgrade cases pass (five tests, 19.515 seconds). Administrative read
fixtures establish source validation, not public mutation or SDK qualification.
A focused populated upgrade verifies ownership and consumer EXECUTE for all three
new routines (6.345 seconds). The existing protected-activation case passes
(6.515 seconds), including direct export refusal, explicit regrant detection and
blocked protected upgrade/configuration. Ordinary `query.sql` remains byte-identical.
Astra Ultra reviewed the plan, source and added protection controls. Public
compiler/stream admission and hosted release validation remain separate work.
