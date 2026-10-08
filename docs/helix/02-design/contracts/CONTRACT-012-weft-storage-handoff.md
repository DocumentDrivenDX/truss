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

Latest source composition is [layout 0.11](../models/truss-layout-weft-review-0.11.proposal.sql) and its [UMF model](../models/truss-layout-weft-review-0.11.proposal.umf.json), adding the owner-selected request-receipt storage direction. The [0.11 column index](weft-review-columns-v0.11.proposal.md), [feed/lifecycle/receipt chapter](weft-review-columns-v0.11.feed.proposal.md) and [source-effect inventory](weft-review-columns-v0.11.proposal.json) now document all 46 tables and 442 columns. The current 0.11 source packet is separately documented below; historical 0.10 remains preserved. Neither qualifies native replay.

## Current 0.11 source binding packet

The [matching source packet](../../04-build/evidence/weft-source-binding011/README.md) carries actual 0.11 SQL and all 442 declared columns. Six strict schemas, original UMF model validation, independent artifact/profile/source and exact SQL/table-pointer/unique-selector checks pass. Seven damaged-packet controls refuse. Source-only review011 selectors do not replace authored physical IDs or admit native correspondence. The 346965-byte envelope and 341497-byte decoded occurrence closure fit the inspected limits. This remains an unregistered one-string fixture; compiler/native execution and owner adoption are open. Earlier packets remain unchanged.

## Receipt storage composition 0.11

Reproduce the current declaration references with `python3 docs/helix/04-build/evidence/design-audit/collect-weft-review-columns.py --request-receipts`. The collector verifies the original AST digest, preserves CREATE/ALTER effects and retains other statements by original pointer. An independent comparison confirms all prior 0.10 table/index entries remain unchanged and the three receipt tables add exactly 3/13/6 columns. Explicit declaration nullability is distinct from CHECK/protected-procedure acceptance. Native routines, roles and implicit effects remain outside this column inventory.

The full ordered 0.10 statement array is preserved and the existing receipt candidate adds five statements: request_receipt_route_guard, request_receipt, request_receipt_protection, a positive bigint allocator and a nonunique digest route index. The resulting source has 106 statements, 46 tables, 442 columns (CREATE plus ALTER ADD), 24 explicit indexes and eleven sequences. Existing UMF capture APIs compose/save/reload/export under unchanged limits; independent full ordered AST comparison and all output/source hash checks pass. This is source evidence, not an installed or accepted compiler profile.

Route digest pairs serialize collisions; only full namespace/request bytes establish request identity. Complete receipt bytes retain original ordered results and producer context; expired identity bytes preserve conflict/expiry meaning after eligible payload clearing. Separate protection bytes retain original update evidence and transaction provenance. Their declared native checks do not decode these artifacts or implement full-identity uniqueness, replay authority, clocks, current protection or unknown-commit recovery.

Reuse the 49 already-authored receipt candidate identities through original source/creator/parent reconciliation. The receipt direction is now selected by ADR-005; the private routine/security/resource/clock/namespace profile remains to be composed. All-no-op groups still persist a complete receipt in the same transaction; request-free groups invoke no receipt home. Native expiry must never turn retained identity into reusable absence. Include source generation, initialization, protected producers/readers, privileges and independent retry/rollback/lost-acknowledgment/expiry schedules before enabling replay readiness.

Historical 0.10 review entry: [layout 0.10](../models/truss-layout-weft-review-0.10.proposal.sql), [420-column index](weft-review-columns-v0.10.proposal.md), and [matching source packet](../../04-build/evidence/weft-source-binding010/README.md). Earlier sections preserve historical checkpoints; their packet/version statements do not select the current input. This contract remains draft and the packet remains unregistered.

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

### Current integrated review profile: 0.6 proposal

The [0.6 UMF model](../models/truss-layout-weft-review-0.6.proposal.umf.json), [SQL](../models/truss-layout-weft-review-0.6.proposal.sql), [column index](weft-review-columns-v0.6.proposal.md), [feed column chapter](weft-review-columns-v0.6.feed.proposal.md) and [source-effect inventory](weft-review-columns-v0.6.proposal.json) now integrate the four complete-feed stores plus a distinct complete consumer registration/checkpoint home. The selected source has 85 statements, 37 tables, 350 declared columns and 17 explicit indexes.

`feed_tx`, `feed_member`, `feed_prerequisite` and `feed_configuration_prerequisite` retain original transaction manifests, ordered member facts and catalog/configuration prerequisites. `complete_feed_consumer` retains full original identity/registration/current state, fencing generation, seed protection floor/evidence, exact seed/transaction/coverage boundary and original procedure/downstream profiles. Its identity route is nonunique; the protected producer must enforce full-byte projection/identity and at-most-one nonremoved registration, retain removed registrations for recovery, and never recreate a VerifiedApplication from stored bytes or hashes. Worker generation is fencing, not progress. An equal acknowledgment or heartbeat cannot refresh actual applied progress.

The legacy `feed_consumer` table is journal-only. It cannot store complete manifest boundaries or stand in for seed registration/protection. Full-feed checkpoint lookup uses the admitted complete identity and original registration/generation, locks its selected row, compares exact full prior boundary under the original profile and advances only after current host proof/authority/interval verification. Retention protection uses the independently derived inclusive floor and complete seed/classifier/coverage meaning, not xid subtraction or a fabricated seq maximum. Seed activation, administrative receipt homes and full producer/guard/retention bodies still need complete installation integration.

The combined pretty YAML exceeds UMF's existing serialization length limit. This model uses compact standard JSON, then passes UMF `readDocument` under unchanged text/structure/depth limits and produces an identical native export after saved-model reload. No UMF capability, validation limit or SQL meaning was changed. Reproduce with `bun docs/helix/04-build/evidence/design-audit/check-complete-feed-consumer-source.ts` and `bun docs/helix/04-build/evidence/design-audit/compose-complete-feed-layout.ts`; verify with `python3 docs/helix/04-build/evidence/design-audit/check-complete-feed-layout.py`; generate both reference chapters with `python3 docs/helix/04-build/evidence/design-audit/collect-weft-review-columns.py --complete-feed`.

The [custom trigger body inventory](../../04-build/evidence/design-audit/native-trigger-body-gaps.json) identifies thirteen authored observer/guard references to five bodies not declared in this selected model: row_touch_observe, row_touch_commit_check, edge_limit_observe, edge_limit_catalog_observe and feed_current_union_check. These trigger fragments are not included in executable-ready SQL. Their signatures, required algorithms and native bodies/privileges must be completed together; adding a trigger name without its body cannot qualify enforcement. This inventory excludes builtin dependency resolution and other runtime/admin producers. None of the source counts proves the whole physical installation complete or supplies an admitted Weft adapter.

### Prior integrated review profile: 0.5 proposal

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

## Current recovery profile 0.7 (2026-10-07)

The [UMF model](../models/truss-layout-weft-review-0.7.proposal.umf.json) and [exported SQL](../models/truss-layout-weft-review-0.7.proposal.sql) extend the unchanged 0.6 statements with the three [recovery homes](feed-recovery-layout-v0.1.proposal.sql). This selected source profile has 94 statements, 40 tables, 386 columns and 20 explicit indexes. The [column index](weft-review-columns-v0.7.proposal.md), [feed chapter](weft-review-columns-v0.7.feed.proposal.md) and [full source-effect inventory](weft-review-columns-v0.7.proposal.json) retain original declaration pointers.

Administrative receipt storage is independent of consumer removal; source attempt/artifacts preserve original seed state and classifier custody. Original production evidence is separate from later committed observation, avoiding a self-referential commit proof. Native full-byte arbitration, decoded-column parity, worker/state CAS, protected artifact immutability, resource/retention rules and transition producers remain required. The [allocation](feed-recovery-storage-allocation.proposal.md) and STP-041 RS-01–07 define those obligations. No native tests are claimed.

Existing UMF capture/reload/export and independent ordered AST comparison pass for the nine added declarations. Compact JSON uses unchanged UMF reader limits. These checks prove source preservation/composition only. The concrete Weft binding packet remains pinned to 0.4; it is not implicitly compatible with this layout. Native routines, roles, deployment qualification and complete installer conversion remain unfinished.

The [installation gap matrix](weft-review-installation-gap-matrix.proposal.md) allocates each remaining family, identifies the missing qualified grant helper and separates source homes, design selections, native body implementation and qualification. Use it with the current profile rather than treating historical direct-DML grant examples as installer-ready.

## Current operation uniqueness profile 0.8 (2026-10-07)

The [UMF model](../models/truss-layout-weft-review-0.8.proposal.umf.json) and [SQL](../models/truss-layout-weft-review-0.8.proposal.sql) preserve all 94 prior statements and add the existing [unfinished-operation unique index](row-operation-unfinished-unique-v0.1.proposal.sql). Profile 0.8 has 95 statements, 40 tables, 386 columns and 21 explicit indexes. The [column index](weft-review-columns-v0.8.proposal.md), [feed chapter](weft-review-columns-v0.8.feed.proposal.md) and [source-effect inventory](weft-review-columns-v0.8.proposal.json) are pinned to this composition.

The index constrains at most one nonfinalized registry row per stored writer xid. It cannot prove existence, authentic actual xid, original issuer/savepoint custody, valid phase transitions or complete commit collection. OC01–OC07, original phase/generation producers and independent native tests remain required. Finalized records stay available for full transaction validation; no deletion/fake finalization may make room for a new operation. Independent ordered AST comparison and existing UMF reload/export pass; native installation and Weft adoption remain unqualified. The concrete binding packet remains 0.4.

## Separate current source binding packet

A [0.8 review packet](../../04-build/evidence/weft-source-binding08/README.md) now accompanies the current layout. Its exact 301749-byte envelope maps all 386 declared columns with source-only review08 identities, actual SQL and original UMF string fixture definitions. Six schema checks, source/profile/artifact closure and four damaged-packet refusals pass. No compiler/native execution or registration is claimed. The historical 0.4 packet remains unchanged; neither packet establishes accepted Truss backend adoption.

## Current key lifecycle profile 0.9 (2026-10-07)

The [UMF model](../models/truss-layout-weft-review-0.9.proposal.umf.json) and [SQL](../models/truss-layout-weft-review-0.9.proposal.sql) preserve all 95 prior statements and compose the existing owner-local key_lifecycle_history table/index. This profile has 97 statements, 41 tables, 395 columns and 22 explicit indexes. [Column index](weft-review-columns-v0.9.proposal.md), [feed/lifecycle chapter](weft-review-columns-v0.9.feed.proposal.md) and [source-effect inventory](weft-review-columns-v0.9.proposal.json) pin the actual declarations.

This closes the source-home omission identified in the reactivation audit. Protected original chain production, complete creation/transition custody, owner-local interpretation, immutable report effects and native CP-01–06 evidence remain required. Existing UMF save/reload/export and independent ordered AST comparison pass; source composition does not qualify native enforcement. The separate 0.8 and historical 0.4 Weft review packets retain their original pins and are not implicitly compatible with 0.9.


Source referential audit: check-layout-foreign-key-closure.py verifies all 59 explicit inline/table foreign-key column tuples against declared target tables and nondeferrable PK/unique source keys in profile 0.9. A deliberately missing target is rejected. This covers source target/arity/key closure only; actual native type/collation/operator/dependency parity and implicit effects remain installer qualification. The receipt pins the source-effect inventory and verifies its saved AST hash.


Index/allocator source audit: check-layout-index-sequence-closure.py verifies all 22 explicit indexes, including expression/predicate column references, and all 12 literal nextval defaults against the nine declared sequences. No dangling declared column/sequence reference was found. The inventory/AST is pinned; dynamic references refuse this audit. Native search-path/regclass/type/opclass/collation/OID and routine-body dependencies are outside its scope and remain installer admission work.

## Current migration homes profile 0.10 (2026-10-07)

Identity reconciliation now starts from review010-prior-identity-catalogs.json, a hash-pinned manifest of authored entry catalogs discovered by content in the models directory. Preserve their authored IDs and original versioned captured-model locators; the new effect worklist's null identities are not permission to reallocate by name. Repeated IDs across catalogs require original source/definition review, not automatic last-file selection. The manifest is a reconciliation input, not a completed 0.10 binding or native identity inventory.

The [UMF model](../models/truss-layout-weft-review-0.10.proposal.umf.json) and [SQL](../models/truss-layout-weft-review-0.10.proposal.sql) preserve the 97 prior statements and add installation_admission plus key_migration_receipt, its allocator and route. The source profile has 101 statements, 43 tables, 420 columns and 23 explicit indexes. [Column index](weft-review-columns-v0.10.proposal.md), [feed/lifecycle/migration chapter](weft-review-columns-v0.10.feed.proposal.md) and [source inventory](weft-review-columns-v0.10.proposal.json) pin original declarations.

Existing UMF reload/export and independent ordered AST composition pass. This closes the declared migration-home omission; initialization and exact marker/admission continuity, original generation/receipt production, full feed transition/archive correspondence and native conversion/privilege/profile qualification remain open. No migration capability is admitted by source composition alone. Policy guard remains a separate optional candidate. Weft packets stay pinned to 0.8/0.4; neither implicitly adopts this layout.


The declared dependency audits now accept an explicit inventory version and preserve historical receipts. On 0.10, all 60 explicit foreign keys resolve to declared tables/unique targets; all 23 indexes and 13 literal sequence defaults resolve against the ten declared sequences. The missing-target corruption control rejects. This includes migration admission head linkage and receipt allocation/route. Native type/operator/OID/search-path, implicit effects, routine bodies and installation parity remain outside these source checks.


The [current 0.10 source packet](../../04-build/evidence/weft-source-binding010/README.md) now accompanies this layout: 328413 bytes, all 420 declared columns, exact SQL and original logical fixture definitions. Six schema checks, independent artifact/source closure and four corruption refusals pass. Historical packets remain unchanged. No compiler/native execution, registration or owner adoption follows; the string-only fixture does not imply full mapping capability.


CH-01 now has review010-declared-effects.json: exact source pointers for 43 relations, 420 columns, 563 constraint-source nodes, 60 expression/allocator nodes, 23 explicit indexes, ten sequences and two routines. These are source categories, not native physical counts. It separately lists 116 implicit-dependency work items and eight other statements requiring effect review. Authored/native IDs remain unresolved rather than being fabricated from names/pointers; prior authored IDs must be reused through original correspondence. Complete implicit effects, types/roles/policies/grants and actual native inventory remain required.

### Physical identity reconciliation handoff (proposed)

Current correction: content-based discovery finds 22 authored-entry catalogs and 567 distinct IDs, including constraint, supporting-index, initialization and derived-effect catalogs omitted by the earlier physical-ids filename filter. The original 435-ID input is preserved as review010-prior-physical-filename-catalogs.historical.json. No repeated IDs were found in this current discovered scope; this is not a claim that every repository identity has been discovered.

The catalog manifest now retains all 547 recorded parent/creator edges. Every target resolves within the discovered scope and the graph is acyclic; independently injected dangling and cyclic references refuse. This checks reference membership/order prerequisites only. An existing but wrong parent ID, original source relocation, native ownership or selected effect disposition still needs semantic correspondence review and the owning allocation checker. No edge is silently dropped to obtain closure.

The current original-node scan yields 431 unique exact-node candidates and 136 without an exact match. The additional 36 unmatched entries are eight feed trigger/associated-constraint effects, nineteen baseline constraint IDs, seven baseline supporting-index IDs and two initialization entries (schema comment and row-capacity initialization). Preserve each original creator/parent and initialization meaning during reconciliation. Supporting effects can point to the same creator node as their constraint; that is not two installed declarations and does not collapse their distinct authored identities.

The feed trigger effects catalog already allocated its four trigger IDs and four associated constraint IDs. Its existing checker passes eight independent corruption refusals for missing effects, wrong parents/creators, duplicate IDs, forged native binding, invented supporting indexes, altered original node digest and false completeness. The four source-custody controls for the broadened node scan also pass. These are source checks; trigger bodies, selected composition, implicit native expansion and installation parity remain incomplete. Do not allocate replacement feed IDs or report the historical 435-ID scope as a complete authored inventory.

The historical physical-ids filename scan checked 435 prior IDs against the pinned selected tagged model, retaining original model/hash/pointer custody. That narrower scan found 335 unique exact-node candidates and 100 without an exact match: 42 baseline entries, 49 separate receipt-candidate entries, six row-home triggers and three edge-limit triggers. The [candidate inventory](../../04-build/evidence/design-audit/review010-original-node-correspondence.json) makes no identity assignments. Changed nodes, unselected candidates and genuine omissions are not distinguished by absence alone. Parent/composition/evolution review remains required even for an exact match. Independent selected-model, original-model and catalog hash substitutions plus a re-pinned wrong original-node locator all refuse with the expected custody reason; these controls qualify this scan only.

Baseline diagnostic comparison now preserves both complete before/after definitions and separates 21 parser-location-only differences, 15 definition changes and six absent named candidates. It drops only `location`, `stmt_location` and `stmt_len` for this diagnostic comparison; it does not assert native equivalence or allocate IDs. Named lookup is a review aid only. The original tagged-node scan remains unchanged.

| Unmatched group | Composition evidence / required disposition |
| --- | --- |
| 21 baseline columns with location-only changes | Re-capture within replaced owner tables changes source offsets. Review original parent identity and explicit composition correspondence before retaining IDs; no definition migration is justified solely by these offsets. |
| 15 baseline table/column definition changes | `compose-weft-review-layout.ts` replaces module_access/type_def/rel_def with owner-qualified definitions; `compose-weft-key-profile.ts` changes schema_rev/key_tombstone; the journal-stage input changes journal. Review full retained before/after definitions and explicit dependency/conversion obligations for each ID, including parent tables. Equal names cannot authorize identity retention. |
| Six absent baseline entries | The key-profile composition deliberately removes object_key and its four columns, replacing live-key storage with object_key_bucket; it removes schema_rev.report in favor of catalog_acceptance_report. Record supersession plus required original data/report conversion. New homes are not aliases for the old physical IDs. |
| 49 separate receipt-candidate entries | These belong to the unselected request-receipt candidate, not the declared 0.10 store scope. Preserve them as excluded candidate evidence pending ADR-005; their absence cannot narrow full replay requirements or qualify request-free groups as replay support. |
| Six row-home and three edge-limit triggers | Their candidate source is absent from 0.10. Record an enforcement composition gap, not retirement or an optional omission: required protected body/security/resource profiles and complete trigger composition must precede installer readiness. |

This accounts for the source-review reasons for the 100 unmatched entries in that historical filename-scoped scan. It does not close CH-01: reviewed per-ID parent/evolution decisions, identities for selected effects without prior allocation, complete implicit/security dependencies and native correspondence remain separate deliverables. These groups must stay explicit in the installer comparison; neither ignored entries nor generated replacement IDs may make coverage appear complete.

CH-01 MUST produce an explicit correspondence before the current review declarations become an installation inventory. Inputs are the pinned prior catalogs, their original captured models/source bytes, the selected composed model/AST and the declared-effect worklist. A source pointer identifies a node within one pinned document; it is not a durable physical identity. Native names and OIDs are observations under one installation, not authored IDs.

For each prior entry, retain its catalog path/hash, authored ID, original model path/hash/pointer and complete original node. For each selected effect, retain its selected model/AST path/hash/pointer, effect kind and owning relation correspondence. The reconciliation output MUST classify every prior entry and every selected effect; unclassified entries make the result incomplete. Supporting indexes and other implicit effects retain their creator correspondence separately from any observed generated native name.

| Classification | Required evidence and disposition |
| --- | --- |
| Retained | Original node correspondence, kind and parent identity agree; preserve the authored ID. Parser location changes alone do not authorize replacement. |
| Changed under retained identity | Explicit reviewed before/after definition and allowed evolution identify the same authored object; retain the ID and record changed dependencies. Structural similarity alone cannot choose this class. |
| Superseded or removed | Explicit composition/evolution decision identifies the original entry and its disposition; preserve its history and any successor relation. An absent source node alone is an unresolved omission. |
| Newly authored | No prior identity applies, with complete checked prior scope and deliberate new identity allocation. Record the allocation decision; a generated name/pointer ID is insufficient. |
| Unresolved or conflicting | Missing originals, ambiguous parent/correspondence, incompatible repeated-ID definitions or competing IDs for one effect. Refuse installation readiness; preserve all competing evidence. |

Repeated IDs across catalogs MUST be evaluated against both originals and their version relationship. Identical retained declarations may share one correspondence while preserving both source witnesses. Different definitions require an explicit evolution edge or remain conflicting; directory order and newest filename confer no authority. Conversely, two distinct authored IDs MUST NOT collapse because their declarations or native names match. Parent reconciliation precedes child reconciliation, including owner-local columns/constraints and creator-owned implicit effects.

The output has separate `sourceCorrespondenceComplete` and `nativeInventoryQualified` conclusions. The first requires exhaustive dispositions, original custody, unique selected ownership and resolved conflicts for the selected source scope. The second additionally requires the independently collected installed object/dependency/security inventory and its full comparison. A source-complete result cannot publish the ready marker, register the Weft binding or certify native support by itself.

Planned independent CH-01 controls: remove a prior original; substitute a model hash; move an otherwise identical column to another parent; reuse one ID for incompatible definitions; assign two IDs to one selected effect; omit a superseded baseline entry; replace a supporting-index creator with its generated name; and change only parser locations. The first seven MUST refuse completeness; the last MUST retain identity when independently established composition correspondence agrees. These are required future reconciliation tests, not executed evidence.
