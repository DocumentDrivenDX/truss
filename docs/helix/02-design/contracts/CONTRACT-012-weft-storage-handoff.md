---
ddx:
  id: CONTRACT-012
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: ADR-002
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
---

# Contract: PostgreSQL storage handoff to Weft

**Contract ID**: CONTRACT-012  
**Type**: schema / compiler boundary  
**Version**: source handoff 0.1.0, 2026-10-07  
**Status**: draft; source layout documented, complete installed layout and binding adoption pending

## Purpose

Give Weft one entry point for Truss's physical storage and logical-to-physical mapping. “On disk” here means PostgreSQL relations, columns, constraints and access paths; PostgreSQL owns heap/page representation. This document does not prescribe database filesystem files.

The full intended layout is **not complete**. Baseline 0.2 has concrete DDL; typed row homes, richer catalog custody and history/private-operation additions remain candidates. Weft can develop against the explicit baseline and row-home source surfaces below, but cannot claim an approved production storage adapter from them.

## Scope and Boundaries

- Truss owns the physical layout, binding export, value codecs, catalog/authority admission and execution obligations. Weft owns SQL parsing, logical planning, lowering and compiler embedding. UMF owns authored metadata semantics and portable key encoding.
- This handoff covers graph reads, property presence/values, key lookup and relationship joins. It does not require Weft to implement mutation, journal cleanup, catalog migration or Truss resource accounting.
- [CONTRACT-001](CONTRACT-001-storage-layout.md) owns physical storage; [CONTRACT-010](CONTRACT-010-exact-value-transport.md) owns exact value transport. This index does not replace either or approve proposals.

## Normative Surface

### Concrete binding review packet

A [source-backed binding packet](../../04-build/evidence/weft-source-binding/README.md) now supplies an actual envelope, original valid UMF Record/Field model, complete selected declared physical map, layout SQL and original home/value/codec/presence/read-context definitions. Six strict schema checks and independent artifact/profile/source/selector closure checks pass. Its 206,405-byte binding and 200,916-byte recursively decoded occurrence closure fit the inspected Weft four-MiB limits. This is a synthetic unregistered one-string-field fixture, not an accepted catalog, admitted native inventory or production exporter/adapter. The remaining review/registration evidence and planned fixture expansion are explicit in the packet.

### Current integrated review profile: 0.5 proposal

The [0.5 UMF model](../models/truss-layout-weft-review-0.5.proposal.umf.yaml), [SQL](../models/truss-layout-weft-review-0.5.proposal.sql), [column reference](weft-review-columns-v0.5.proposal.md) and [source inventory](weft-review-columns-v0.5.proposal.json) add installation marker/archive homes to the unchanged 0.4 selection: 78 statements, 32 tables, 282 declared columns and 16 explicit indexes. These metadata homes are separate from logical application records. CONTRACT-008 now defines IM01–IM07 fresh initialization/archive/marker/commit order and avoids self-embedding inventory digests.

Reproduce with `bun docs/helix/04-build/evidence/design-audit/check-installation-metadata-source.ts`, then `bun docs/helix/04-build/evidence/design-audit/compose-installation-metadata-profile.ts`; verify with `python3 docs/helix/04-build/evidence/design-audit/check-installation-metadata-profile.py`; regenerate columns with `python3 docs/helix/04-build/evidence/design-audit/collect-weft-review-columns.py --installation-metadata`. Source capture, saved-model export and independent ordered AST correspondence pass; no metadata rows were inserted and no native installation is qualified.

The source binding review packet remains explicitly pinned to 0.4; no compatibility/adoption is inferred for 0.5. Compiler-facing graph/value column declarations are unchanged, but selected complete layout/profile/SQL hashes differ and must be supplied together in any later admitted binding. Full native guard/grant/trigger/policy/dependency and initialization/migration qualification remain unfinished.

### Prior selected store profile: 0.4 proposal

The [0.4 UMF model](../models/truss-layout-weft-review-0.4.proposal.umf.yaml), [generated SQL](../models/truss-layout-weft-review-0.4.proposal.sql), [column reference](weft-review-columns-v0.4.proposal.md) and [source-effect inventory](weft-review-columns-v0.4.proposal.json) supersede 0.3 as the current integrated review selection. They contain 74 statements, 30 tables, 264 declared columns after selected ALTER effects and 15 explicit indexes. All earlier profiles remain historical/baseline references, not compatible aliases.

The selected proposal makes these dispositions explicit:

| Concern | Selected physical home | Rule |
| --- | --- | --- |
| Live logical keys | `object_key_bucket` replaces `object_key` | Exact namespace/key bytes and original context; nonunique digest routing, full-byte identity |
| Object-key reservations | `object_key_reservation_bucket` | Complete immutable reservation artifact; no object reservations in a second canonical home |
| Bucket exclusion/generation | `key_bucket_guard` | Digest collisions share exclusion; generation counts actual membership mutations; never digest-only semantic equality |
| Edge endpoint reservations | `key_tombstone`, restricted to `entity_kind = 'e'` | Existing endpoint-ID encoding and typed relationship context; object legacy tombstones require explicit migration into the reservation artifact home |
| Acceptance reports | `catalog_acceptance_report` replaces `schema_rev.report` | One nonempty canonical report artifact per accepted positive revision, persisted only after complete actual event/report finalization |
| Allocation observation | Two protected high-water function declarations | Retained active/provisional/retired catalog IDs included; negative legacy IDs remain valid, new positive allocation is bounded and separately guarded |
| Private capacity initialization | Existing parameterized fresh-only INSERT | Installer supplies full admitted layout/resource definition bytes, proves empty scope, inserts exactly once, independently reobserves; no reset/upsert or marker-only bytes |

For a bucket key lookup, filter the admitted native type/key-number and qualified namespace/key digest route, compare **both full namespace_bytes and key_bytes**, then join `(object_id,type_id)` to `object.(id,type_id)`. Digest collision alone is neither a match nor a uniqueness failure. The binding must retain original namespace/portable encoding/definition context and qualify the exact byte parameter protocol and bounded collision processing. The old object_key text join remains baseline-only. Ordered logical-key paging still requires its independently admitted comparator; storage_row_id orders internal locators, not logical key values.

For acceptance, insert the complete parent revision/origin/documents and candidate catalog/data effects in one protected transaction, finalize actual journal/feed facts, encode and persist the final immutable report bytes, prove positive-revision report completeness and only then advance `schema_head`. Revision zero is bootstrap empty-catalog state, not a positive accepted report. The existing three-value schema_rev seed now assigns its third JSON object to origin after report removal; the selected source inventory explicitly records this change. A failure rolls back parent/report/catalog/data/journal/head effects together. Full guard bodies and producer privilege closure remain mandatory and are not supplied by the table PK/FK alone.

Migration must preserve exact retained numeric IDs and original meanings. Legacy key text/report JSONB is not automatically original canonical bytes; an independently admitted complete source/codec/owner mapping must prove conversion or refuse. Distinct original reservation identities are retained even when routing hashes collide. No downgrade may collapse qualified owner identities, discard reservations or manufacture missing original report/value artifacts. M-01–M-07 still own bounded staging, atomic activation, unknown-outcome recovery and rollback.

Reproduce with `bun docs/helix/04-build/evidence/design-audit/capture-key-and-allocation-sources.ts`, then `bun docs/helix/04-build/evidence/design-audit/compose-weft-key-profile.ts`. Verify the selected replacements/additions with `python3 docs/helix/04-build/evidence/design-audit/check-weft-key-profile.py`; generate the reference with `python3 docs/helix/04-build/evidence/design-audit/collect-weft-review-columns.py --key-profile`. The [composition receipt](../../04-build/evidence/design-audit/weft-key-profile-composition.json) pins all four inputs and model/SQL/saved AST outputs.

This is a design selection for review, not owner adoption or installed support. Remaining installation outputs are exact initialization/admission producers, all required protected guard/routine/trigger/policy/grant definitions, complete implicit/dependency/native correspondence and the populated conversion profile. An actual exporter binding and registered Weft adapter remain separate outputs. High-water declarations observe maxima; they do not allocate, lock, prove visibility, enforce resources or finalize acceptance by themselves.

### Selected integrated review profile: 0.3 proposal

The [single UMF model](../models/truss-layout-weft-review-0.3.proposal.umf.yaml) and [generated SQL](../models/truss-layout-weft-review-0.3.proposal.sql) now compose one review selection: 64 statements, 27 tables, 249 explicitly declared columns after selected ALTER effects, and 13 explicit indexes. The [current column reference](weft-review-columns-v0.3.proposal.md) and [source-effect inventory](weft-review-columns-v0.3.proposal.json) describe that selection. Baseline references below remain for compatibility review; they are not the current integrated proposal.

The selection replaces exactly the baseline `module_access`, `type_def` and `rel_def` declarations with [qualified owner homes](catalog-owner-homes-v0.1.proposal.sql). It retains the complete history/edge-retained/private-operation composition and adds the fixed row tree/scalar/touch/capacity stores, relationship lineage and independent catalog definition-source homes. Replacement is deliberate: old module-only uniqueness is removed, not left installed alongside the new owner meanings. `type_def.document_id` and `rel_def.document_id` identify declaring owners independently of `definition_document_id`; property/key owners follow the owning type. The module grant primary key is `(document_id,module)`.

Type identity is full registered `lineage_bytes`, projected to exact document/module/element values, with nonunique `(lineage_sha256,type_id)` routing. Relationship identity remains the full tagged adjunct, not a new UNIQUE(document,module,rel_id) that would collapse authored/composition identity. Both require protected full-byte uniqueness/total-coverage validation. Fresh CREATE declarations do not supply a populated migration, implicit grants or native guard bodies.

Reproduce the selected model/SQL with `bun docs/helix/04-build/evidence/design-audit/compose-weft-review-layout.ts`; verify complete ordered source AST correspondence with `python3 docs/helix/04-build/evidence/design-audit/check-weft-review-layout.py`; regenerate its column reference with `python3 docs/helix/04-build/evidence/design-audit/collect-weft-review-columns.py`. The [composition receipt](../../04-build/evidence/design-audit/weft-review-layout-composition.json) pins eight original model inputs, the UMF owner source, replacements and output hashes. YAML is the UMF-supported serialization selected because the combined pretty-JSON output exceeds UMF's serialization limit; no limit was raised or bypassed.

**Still incomplete:** this review selection is not the complete installation profile. Key-bucket/allocator/acceptance-report alternatives, initialization with admitted private-profile bytes, all guard/function/trigger/policy/grant definitions, implicit/dependency/native parity and populated conversion still require integration or explicit disposition. It has no actual exporter binding instance or registered Weft adapter. The schema marker explicitly says REVIEW ONLY. The new profile resolves the missing declaring-owner declarations; it does not claim those remaining obligations are finished.

### Exact source selection

[Source manifest](weft-layout-handoff-v0.1.proposal.json) pins the six selected files by SHA-256. A consumer MUST distinguish these source sets:

| Surface | Exact source | Status / scope |
| --- | --- | --- |
| Baseline layout 0.2 | [storage-layout.sql](storage-layout.sql) | 19 fixed tables, two sequences, eight explicitly authored indexes; exact column order, types, defaults, nullability, CHECK/PK/UNIQUE/FK and journal partition expression are in this DDL |
| Baseline UMF model | [truss-layout-0.2.umf.json](../models/truss-layout-0.2.umf.json) | Captured baseline; [column semantics](../models/truss-layout-0.2.column-semantics.draft.json) retain original column nodes; native completeness remains false |
| Row-home candidate | [tree SQL](row-home-tree-v0.1.proposal.sql), then [scalar SQL](row-home-scalar-v0.1.proposal.sql) | Three additive fixed tables; separate allocator; two baseline ALTER UNIQUE effects; three explicit indexes. Not baseline row support or an installer |
| Binding envelope | [PostgreSQL binding schema](truss-postgresql-binding-v0.1.proposal.schema.json) | Proposed exporter-to-Weft envelope, not an accepted binding instance |
| Row join definition | [row join schema](truss-row-join-definition-v0.1.proposal.schema.json) | Complete physical selectors and original profile/source custody for candidate row reads |

The baseline SQL's first comment says 0.1 while its schema marker says 0.2; the marker and CONTRACT-001 identify this baseline as 0.2. The comment remains a documented editorial mismatch; changing the pinned original SQL requires refreshing its existing source receipts. The 23-, 37-, 41- and 43-statement review compositions elsewhere are different proposal selections. Consumers MUST NOT assemble a layout by unioning those fragments or infer adoption from statement counts.

### Column dictionary

The [column reference](weft-layout-columns-v0.1.proposal.md) lists all 168 columns across the 19 baseline and three candidate tables in declaration order, with native type names, declared/default presence and primary-key-aware nullability. The [machine dictionary](weft-layout-dictionary-v0.1.proposal.json) retains complete original column/table nodes, type modifiers, defaults, collations, constraints and all other selected statements. Reproduce it with `python3 docs/helix/04-build/evidence/design-audit/collect-weft-layout-dictionary.py`. It is source coverage, not resolved native inventory or adoption.

### Complete baseline table index

The selected DDL is the exact column/constraint reference for every table below. All names are deployment-schema qualified; `truss` is the default, not an unquoted string to interpolate into SQL.

| Group | Tables | Compiler relevance |
| --- | --- | --- |
| Settings and optional isolation | `setting`, `module_access` | Admission/authority context; module_access alone does not install policies |
| Revision/source custody | `schema_rev`, `schema_head`, `schema_doc`, `schema_change` | Current revision and immutable authored documents; never resolve solely by a display name |
| Binding catalog | `type_def`, `prop_def`, `key_def`, `rel_def`, `rel_endpoint` | Typed identities, property homes, key components and permitted endpoint types |
| Current graph | `object`, `object_key`, `edge`, `edge_limit` | Objects, logical keys, relationships and cardinality support |
| Import custody | `key_tombstone`, `record_source` | Reservation/provenance; not additional current objects |
| History/feed | `journal`, `feed_consumer` | History/consumer state; not current graph values |

`id_seq` supplies graph IDs; `journal_seq` supplies journal positions. `journal` is RANGE partitioned by `at`; deployment creates time partitions. Adding a logical UMF type/property/relationship MUST NOT create per-type tables, columns, partitions or indexes. History time partitions are distinct from type partitions.

### Identity and joins

| Operation | Required physical correspondence |
| --- | --- |
| Object scan | `object.type_id = admitted typeId`; object identity is `(id, type_id)` |
| Key lookup | Match `object_key.(type_id,key_num,k)`; join `(object_id,type_id)` to `object.(id,type_id)`. Resolve ordered key components through the admitted key definition and UMF encoding |
| Outgoing edge | Match admitted `edge.rel_type_id`; join `(source_id,source_type)` to source object `(id,type_id)` and `(target_id,target_type)` to target object `(id,type_id)` |
| Incoming edge | Same typed endpoint pairs, opposite traversal direction; do not swap the authored relationship meaning |
| Edge property | Resolve `rel_def.assoc_type_id` as property-owner type; relationship ID and property-owner type ID are separate domains |
| JSON property | Resolve admitted property ID; address `props` by that ID rendered as text, not logical property name |
| Row property | Select admitted row-home binding; join state by full owner kind/typed identity/property identity, then root/node/payload within that same state |

Catalog IDs are PostgreSQL `int`, key numbers `smallint`, graph IDs/versions `bigint`. Bind exact canonical text with native-domain checks; do not pass them through JavaScript `number`. Legacy signed catalog domains MUST NOT be rejected merely because future allocation prefers positive IDs. A logical key cursor is not a graph-ID cursor.

### Presence and exact values

For baseline JSON properties, missing map key is absent, JSON `null` is explicit null, and a present non-null value is present. SQL NULL from an extraction MUST NOT conflate missing and explicit null: check map membership and JSON value state before decoding. Empty string, zero, false and empty containers are present values.

For the row candidate, `row_home_state` identifies a property root; `row_home_node` retains root/parent/slot and value-kind information; `row_home_scalar` holds a scalar payload. Missing payload is not proof of property absence. A null node has no scalar payload; an empty container retains a root with no children. Sequence slots are zero-based; map keys use exact text; record slots use complete authored field-identity bytes. Reads MUST retain source/profile custody and refuse incomplete or inconsistent trees.

Scalar native projections are `text_value`, `boolean_value`, `numeric_value`, `binary_value` and optional `temporal_instant`. Numeric original spelling remains in `numeric_token`; timestamps retain `temporal_text`; original source and codec bytes remain mandatory. Native numeric projection alone does not prove exact source grammar/domain/facets. An optional instant projection does not qualify arbitrary timestamp comparison. Unknown opaque bytes do not acquire a comparator automatically. Consult CONTRACT-010 for decoder and reconstruction obligations; cast/extraction syntax is compiler output, not a codec specification.

Baseline object `retained` stores unmatched content. The baseline edge lacks the newer retained/source homes; candidate compositions propose those additions. Weft MUST NOT treat a candidate column as installed or silently reinterpret retained content as a known property.

### Access paths

Baseline explicit indexes: `object_type_id`, `edge_out` (unique), `edge_in`, `edge_limit_edge`, `record_source_load`, `journal_entity`, `journal_feed`, `journal_request` (partial expression). Primary/unique constraints also create supporting indexes. A foreign key does not imply a new local index. The exact index definitions, include columns and predicates are in selected SQL.

Row candidate indexes: `row_home_one_root` (unique, parentless nodes), `row_home_sequence_slot` (unique, sequence slots), `row_home_map_parent` (map-parent lookup). Full arbitrary map keys/record identity bytes do not have an unrestricted full-value B-tree promise. Compiler support for a predicate and storage index support are separate capability claims.

### Exporter / compiler binding

The proposed envelope requires `interfaceVersion`, pinned `bindingProfile`, `basis`, `entities`, `properties`, `keys`, `relationships`, `executionObligations`, `qualification` and `bindingProfileId` as specified by the schema. `basis` pins model bundle, accepted catalog/revision, namespace, exact layout inventory/SQL/exporter and identity/value/key/read-context profiles. Each definition retains its exact source/accepted definition rather than resolving a replacement by name.

Property mappings select `home: props | row`, original home/value/presence definitions and owner/property IDs. Row selectors reference admitted physical identities for owner/state/node/scalar columns; a matching relation name is insufficient. Relationship mappings carry both endpoint type IDs, selected key IDs and ordered endpoint property IDs. SQL values MUST be parameters; identifier components MUST be separately validated and quoted.

The Truss executor owns current authority/revision/installation checks and the registered decoder. Weft compilation does not discharge those checks. No accepted binding instance or registered production adapter is supplied by this document.

## Precedence and Compatibility

Accepted ADR-002 governs fixed generic storage. Baseline 0.2 and additive candidates remain distinct. A future selected full profile MUST pin one complete UMF model, emitted DDL, physical inventory, value/key/presence/read definitions and exporter version together. Changing column homes, encodings or relationship interpretation requires a new profile and explicit migration/admission; consumers MUST NOT infer compatibility from same-named tables.

## Error Semantics

| Condition | Outcome | Recovery |
| --- | --- | --- |
| Missing/unadopted binding or unsupported original profile | Refuse preparation for that surface | Supply an admitted binding; no guessed columns or JSON fallback |
| Stale catalog/authority/installation context | Refuse execution/publication | Re-admit under current context; do not silently reuse compiled assumptions |
| Missing root/payload, mismatched owner or unknown codec | Refuse complete value/result publication | Diagnose original state; do not return partial/null substitutes |
| Native execution/transaction outcome unresolved | Preserve unresolved execution outcome | Executor recovery protocol; never claim committed/rolled back from compiler success |

These are boundary outcomes, not newly assigned public error-code strings.

## Examples

Informative baseline typed traversal (parameter slots denote exact text/native-domain-admitted values):

```sql
SELECT dst.id::text
FROM truss.object AS src
JOIN truss.edge AS e ON (e.source_id, e.source_type) = (src.id, src.type_id)
JOIN truss.object AS dst ON (dst.id, dst.type_id) = (e.target_id, e.target_type)
WHERE src.id = $1::bigint AND src.type_id = $2::int
  AND e.rel_type_id = $3::int AND dst.type_id = $4::int;
```

This illustrates join correspondence only; it omits admission/authorization and does not qualify a logical-query compiler or host parameter protocol.

## Completion and next work

Prioritize these deliverables before declaring the layout Weft-ready:

1. Select and reconcile the complete intended physical profile, including document-qualified catalog identity, row homes, edge retained/source custody and complete history. Produce one full model/DDL/inventory rather than fragment counts.
2. Produce an actual deterministic binding instance from that selected profile, with fixtures for object/key/typed-edge joins and absent/null/exact scalar/recursive values. Jointly reconcile it with Weft's current definition grammars; shape-only validation is insufficient.
3. Register the selected exporter/adapter and independently execute generated reads and original decoders against the installed profile. Test wrong profile/revision/owner, null/absence, exact integer/decimal and unsupported-family refusals.
4. Separately finish native guard/grant/function/trigger/dependency inventory and mutation qualification. These do not justify withholding a clearly scoped compiler source handoff, but are required for full storage support.

Current Weft B-005 evidence explicitly says no approved Truss binding or registered adapter exists. Its synthetic native compiler tests do not close the above gates. The source manifest can be checked immediately for stale files; native parity and binding adoption remain unclaimed.
