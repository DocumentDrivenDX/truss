---
ddx:
  id: ADR-007
  type: adr
  activity: design
  status: accepted
  authoring:
    home: repo
  links:
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: CONTRACT-006
      kind: informed_by
    - id: US-018
      kind: informed_by
    - id: US-041
      kind: informed_by
---

# ADR-007: Complete historical record envelopes

## Owner decisions — 2026-10-07

Accepted by the owner: history supports reconstruction without current rows. Creates retain complete new records; deletes retain complete prior records; updates retain ordered property deltas plus the selected complete metadata boundary witness. The selected two-property mutation emits two property deltas and one witness. Local retention is deployment-configurable, including very short or zero retention. Continued reconstruction after local deletion requires a qualified durable archive handoff; otherwise return explicit unavailable history. Required consumer/receipt protections and atomic history production are not bypassed by a zero-retention setting. Native producers, archive continuity and selected encoding/profile qualification remain build gates.


**Status:** accepted reconstruction/retention direction; qualified versioned journal profile required. **Date:** 2026-10-05.

## Problem and proposed decision

The current create/delete props/retained envelope omits edge endpoints/order and object ownership metadata. Property updates do not by themselves describe changes to native record metadata. An independent historical reconstruction or delete consumer cannot recover complete graph state from that representation.

Propose a versioned complete record envelope on whole-record create/delete events and explicit before/after presence for changes. Preserve existing physical journal partition/position semantics; do not reinterpret old rows as complete. A new journal encoding/profile and exporter/decoder pins are required even if envelope content fits existing JSONB columns.

## Envelope meaning

[Historical-event schema](../contracts/history-event-v0.1.schema.json) now supplies the six operation variants matching the draft declaration. Required create/delete records, transform pins and four rebind homes are structural obligations; actual group identity/digest, legal transitions and historical context remain semantic/native obligations. Twelve structural cases pass and deliberately include a forged count that cannot establish completeness. Side/manifest/activation wire schemas remain separate outputs.

[Historical-record JSON Schema](../contracts/history-record-v0.1.schema.json) now supplies a closed proposed object/edge wire shape referencing the existing exact-value schema. Objects require explicit rootless/owned state; edges require source/target identities and null/text order key; every record retains last-written revision/version/timestamps and property/retained inventory. Twelve [structural checks](../../04-build/evidence/design-audit/check-history-record.ts) pass using installed Ajv; [receipt](../../04-build/evidence/design-audit/history-record.json). Duplicate properties, unresolved ownership and malformed timestamps deliberately remain structurally valid and require semantic rejection. Definition/identity domains, uniqueness, total bounds and historical continuity are not established by this schema. Complete event/side/manifest/activation wire schemas and native production remain separate outputs.

[Draft historical-record binding](../contracts/bindings/truss-history-v0.1.d.ts) expresses the complete object/edge union, recursive exact values, explicit root/order-key states and prior-record deletion evidence. Its catalogRevision names the record's last-written catalog context, distinct from the enclosing event revision. Endpoint source/target members are typed identities; imported source provenance remains a separately associated side fact. The declaration passes strict no-emit typechecking only. Runtime uniqueness, definition/owner resolution, scalar grammar, resource bounds and event continuity remain required; this binding does not qualify current storage or silently reduce the PRD to its initial carrier subset.

| Common member | Meaning |
| --- | --- |
| envelopeVersion | Exact recognized semantic version |
| kind, id, typeId | Typed storage identity with exact id text |
| recordRevision, recordVersion | Last-written definition context and pre/post event record version, separate from journal event revision/version |
| props, retained | Complete exact value maps under pinned encoding, preserving absence versus present null |
| createdAt, updatedAt | Exact qualified stored time representation, not host Date |
| ownership | For objects: root identity or explicit no-root state |
| endpoints | For edges: authored typed source and target identities |
| orderKey | For edges: explicit native null state or exact text |

Every applicable member is required; inapplicable object/edge members are forbidden rather than silently defaulted. Generated storage ids are distinct from authored business-key values. Retained content/extension carriers follow the exact value profile, not generic host JSON parsing. Delete envelope is the full prior record; its recordVersion remains the prior version while journal event ver is the deletion version. Source provenance and reservations remain separately identified side records, not invented as canonical record fields.

## Updates and reconstruction

The binding now proposes a closed historical-event union: complete create/delete records, property presence deltas, transforms with both definition pins, rebinds with all four source/destination presence states, and complete before/after records for metadata changes. Event revision/version are separate from record context, and source epoch/top-level xid/seq plus trusted database-role origin are explicit. This is a candidate event representation for review, not a reinterpretation of existing journal rows or accepted operation names.

Runtime validation must require matching typed entity identity, applicable object/edge metadata, exact version progression and legal rebind move states (present retained source to absent destination, then absent source/present destination). No-op events refuse under the selected mutation profile. Metadata envelopes preserve endpoint/root/order changes and historical authorization contexts. Multiple property rows at one mutation version need a complete event-group boundary before final reconstructed state can be exposed. Full event JSON schema, group completeness and native writer equivalence remain gates.

Property event values use explicit `{present:false}` or `{present:true,value:...}` before/after states. This distinguishes unset from setting JSON null. Rebind records must identify the exact removed retained path and destination property with both definition contexts; property id alone is insufficient. Transform events carry old/new definition pins and exact values. Native metadata changes (ownership/endpoints/order and any exposed mutable metadata) must be journaled with a versioned explicit member path or complete before/after envelope. Select that event representation in CONTRACT-002 before implementation; no mutation may become invisible to reconstruction.

Reconstruction starts from a complete create or qualified seed at/before requested version, applies ordered contiguous versioned events with retained historical definitions, and validates resulting typed graph state. A missing event/definition/retained horizon blocks with an explicit unavailable-history outcome. Empty legitimate state is distinct from missing history. Multiple property events at one version are one logical mutation; pages must not publish an incomplete version as final state.

## Authorization and feed

Historical edge visibility requires the relationship's declaring module and both historical endpoint owners. Deleted object/source visibility requires retained ownership facts; current live-row lookup cannot establish it. Proposed document-qualified ownership from ADR-004 must be carried or derivable from immutable pinned definitions, not looked up by mutable names. Global feed completeness and role-filtered projection remain separate advertised scopes.

Feed change identity should retain immutable source position plus source epoch/profile to avoid cross-restore ambiguity. This proposal does not resolve revision-only/side-record checkpoint ordering or initial snapshot cut; those remain D-07 gates. Complete delete content is necessary but not sufficient for full feed qualification.

## Compatibility, migration and tests

### Mutation-event completeness proposal

For each typed entity/eventVersion mutation, retain a group manifest with exact positive eventCount and orderedEventDigest under truss-history-group/0.1.0. Every event carries the same manifest; group identity additionally includes source epoch, producing xid and typed entity identity. Event sequence order is exact source-position order, not property-name order. No-op operations produce no empty group. Engine and trigger paths construct the same complete semantic group before the transaction can commit.

The digest covers the ordered canonical event payloads with mutationGroup members excluded to avoid a circular hash. It includes operation, exact before/after meaning, definition context, source position and origin under the selected event profile. Exact serialization/domain rules must be published with the JSON schema; a count alone cannot detect substitution. Loader verifies count, unique event identities, ordered digest and consistent context before exposing a final reconstructed version or acknowledging that mutation. Missing, repeated, substituted or mismatched events produce unavailable/corrupt evidence rather than a partial state.

Pages may transport fragments but cannot advertise a completed mutation until the manifest is satisfied. Large groups require bounded staged accumulation or explicit resource refusal; silently truncating history is forbidden. This is a candidate completeness representation, not installed column compatibility. Physical manifest persistence, trigger generation, canonical event wire schema and native equivalence remain approval/build gates. Whole-transaction feed completeness additionally covers other entities, revision and side facts; this per-mutation manifest cannot replace it.

Independent vectors: two property events with count two; missing second event; duplicated first event; same count but substituted payload; differing manifests on sibling rows; interrupted page followed by complete resume; large group limit refusal; transaction containing several complete entity groups plus required side facts. Only the complete matching vector may expose its final version.

### Producing transaction association proposal

CONTRACT-006 now proposes fixed transaction/member/catalog-prerequisite/configuration-prerequisite stores plus a repeatable explicit protected finalizer and write-free native completeness constraint. They preserve original exact payloads and complete manifest bytes with guarded committed immutability; retention protects the dependency union. This is a candidate physical-profile extension, requiring independent DDL/UMF inventory and policy review. It does not make existing storage or legacy rows complete, nor accept this ADR.

CONTRACT-006 now supplies a candidate whole-transaction manifest and side-fact payload/order declaration. Native change sequence is distinct from manifest ordinal; revision-only transactions retain membership, and source/reservation payloads preserve historical owner/key context. This refines wire meaning without selecting storage. Enclosing host-transaction finalization, immutable payload/manifest persistence, unavoidable production and legacy seed/migration remain required before accepting the profile. Call-local counts cannot prove no later host operation adds a required fact.

Retain the producing top-level full xid8 on every feed-bearing acceptance, source and reservation fact, alongside existing journal xid. Proposed fixed columns on schema_rev, record_source and key_tombstone capture pg_current_xact_id() inside the same transaction that inserts the fact; caller input cannot supply or overwrite them. This is a versioned physical-profile change, not existing layout compatibility. In adopted transactions all facts share the enclosing host transaction identity, including savepoint calls; rolled-back facts leave no committed event.

Immutable original facts keep their producing xid. A skipped import or replay must not relabel provenance with the retry transaction. Missing legacy association cannot be backfilled from timestamps, record ids or guessed neighboring journal rows. Migration must establish it from qualified retained evidence or report that historical subset unavailable for snapshot-seed qualification.

After the safe watermark establishes transaction completion, enumerate all required associated facts under one consistent observation and a complete required-kind manifest. Producing xid alone does not establish event identity, ordering or transaction completeness. Revision prerequisites may need delivery before an older-xid writer's later change; acknowledgment must account for that dependency without advancing past unrelated unapplied positions. Event ordinals, side-record identity and full checkpoint schema remain separate outputs.

Review vectors include revision-only acceptance, source/reservation creation, two calls in one host transaction, savepoint rollback, retry preserving original association, missing legacy association and revision dependency delivery for an older-xid writer. Exact columns, privileges, migration and native evidence require review before acceptance.

Old props/retained-only rows are a legacy partial profile. Native metadata missing from historical records cannot be backfilled by assuming current endpoints/order are historical. A reviewed seed/migration boundary may start complete history; support claims must name that horizon. Rollback cannot strip new envelopes and retain a reconstruction promise.

Independent fixtures must include object ownership changes, edge create/update/delete with changed endpoints/order, null-versus-unset property edits, retained-path rebind, catalog transform across definitions, multiple property rows per version, missing history and hidden historical owners. Reconstruct a graph and apply delete from the event alone with no current-row access. Require both engine and trigger writer profiles to emit identical semantic envelopes. Exact wire schemas and native bypass/retention evidence follow this proposed decision; none is claimed passed here.

### Metadata witness interpretation reconciliation

CONTRACT-002 now proposes one complete group-start/group-final metadata snapshot pair for each non-create/delete entity/version mutation, including property-only changes that advance exposed record metadata. Property/transform/rebind deltas remain independently required and reduce in original source order. The metadata pair witnesses complete boundary correspondence; it cannot overwrite staged values or compensate for omitted deltas. Its original sequence position remains in the group digest. TD-018 and STP-018 carry this conditional producer/reducer handoff and independent controls.

This refines the proposed complete profile and remains subject to ADR adoption and exact native producer review. Existing metadata rows with intermediate or sequential-replacement semantics require a distinct qualified profile or migration horizon; they cannot acquire this meaning by decoder selection alone. No legacy completeness claim or new accepted journal operation follows.


Owner decision, 2026-10-07: a two-property mutation includes its two property deltas plus one metadata boundary witness. This resolves the governing event-count interpretation; it does not adopt all remaining history/feed/native profile obligations.
