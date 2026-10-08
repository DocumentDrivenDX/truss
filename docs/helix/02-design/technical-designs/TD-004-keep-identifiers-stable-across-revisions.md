---
ddx:
  id: TD-004
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-004
      kind: informed_by
    - id: SD-001
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
---

# TD-004: Catalog identity across revisions

## Technical Approach

Separate logical lineage identity from revision-qualified definition and generated storage identifier. Match unchanged lineage before allocating any new id; names never substitute for element identity. Retire removed definitions without deleting historical meaning. Allocate monotonically within the appropriate catalog namespace under the head exclusive lock, including retired rows in the high-water mark. Object/edge sequences are separate from catalog allocation.

## Component Changes

ID05 in the implementation plan owns populated owner/source/grant conversion as a separate boundary from ordinary catalog acceptance. Its phases preserve original IDs/creation revisions, resolve complete source categories and qualified owners before alteration, admit native DDL/held-context compatibility, validate actual pending target parity and activate the layout/policy/binding atomically. Consume CONTRACT-001's fixed home proposals and CONTRACT-005's explicit grant mapping; do not infer permission ownership from source pointers. Add the migration orchestration to `packages/postgresql/src/catalog/migrate-ownership.ts` after exact native/resource/privilege procedures are selected. It owns no compiler or UMF encoder and cannot silently terminate host contexts to obtain DDL locks. Native tests and owner adoption remain gates.

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/catalog/identity.ts` | Qualified identity matching and change/no-change classification | US-004-AC1, US-004-AC3 |
| `packages/postgresql/src/catalog/identity.ts` | Locked catalog/key-number allocation and retained history | US-004-AC1, US-004-AC2 |
| `tests/catalog/identity.test.ts` | Rename/retirement/no-change independent assertions | All criteria |

## Material Identity Gates

CONTRACT-003 names document/module/element identity. Baseline 0.2 uniquifies module/element; current layout 0.11 composes qualified owner homes. Complete source/native identity binding, protected acceptance and populated conversion must qualify coexistence before support. UMF CONTRACT-045 proposes document revision/dependencies but is not implemented; do not activate it from unknown keys. Keys have authored key identity plus stable per-type key_num; preserve both, never derive stability from display name/order.

The owner selected same-qualified-identity reactivation on 2026-10-07. Reintroducing the exact original lineage preserves its storage ID after complete retained value/key/reservation/endpoint/ownership/cardinality and current-authority validation. A distinct identity receives a fresh ID; display-name or document-revision equality cannot establish lineage. Reactivation never implicitly restores grants. Moving owning document/module is a distinct lineage unless an explicitly admitted versioned migration defines otherwise. The remaining gate is exact native lifecycle/history/report conversion, not a repeated retirement-policy choice.

## No-change Acceptance

CONTRACT-003 now requires complete verified acceptance input equality at the current head. Document bytes, owning identity/revision, binding, policy, validator/support pins and transform identities participate; derived-row equality alone does not. Preserve the original report/origin and do not repeat transforms or index dispatch. A historical match after intervening acceptance undergoes current candidate validation. CONTRACT-003 already authors the complete acceptance-input wire, and CONTRACT-009 authors canonical bytes and domain framing. Remaining gates are their exact profile adoption, bounded original producer/decoder and persisted-input/archive lookup with complete correspondence; changed archived content cannot disappear behind equal derived definitions. Do not reopen the wire as an unspecified design task or treat its shape checks as persistence evidence.

## History, Testing and Handoff

Definitions before/after in schema_change retain exact historical meaning for old property/journal rows. Rejected allocation must not advance a committed catalog head or erase retained definitions. STP-004 allocates three criteria. Compose qualified ownership, selected reactivation and complete-input repeat profiles; write red identity/reactivation/retirement/no-change cases, implement shared identity index and locked persistence. Disabling code preserves all historical ids; migration cannot remap stored/journal ids casually. All runtime components remain planned.


## Synthesized relationship identity handoff

Consume ADR-004's proposed tagged relationship lineage. Pure classification distinguishes authored opaque identities from composition_field tuples even when textual renderings match. Derivation requires qualified source field continuity, complete owner Record/field source provenance and exact profile; a missing upstream identity contract refuses the stable-derived-lineage capability without rejecting otherwise valid UMF. The candidate matcher excludes target/cardinality/lifecycle from lineage but includes them in revisioned definition/candidate validation. Numeric allocation persists category/full identity/provenance under head exclusion; no prefix/digest-only mapping.

STP-004 covers category collisions, qualified rename/reorder continuity, owner moves, target changes and unavailable field identity. Complete physical mapping, extraction/Weft review and exact native retirement/reactivation profiles remain separate adoption gates. No same-identity retired row is reactivated merely by this matching algorithm.


## Locked allocation profile

CONTRACT-003 now proposes truss-catalog-id-allocation/0.1.0: independent global native-int type/property/relationship domains and per-owning-type native-smallint key numbers, positive new allocation, complete active/provisional/retired high-water observation and whole-acceptance preflight exhaustion. Match lineage first; same-identity retired reintroduction follows selected reactivation validation. Use exact qualified authored/full derived identity order, not input/name/ordinal order. Preserve admitted legacy IDs without renumbering, private tentative IDs without public authority, original rollback/durability and retained high-water evidence. Exact native visibility/max/capacity/assignment/role/finalizer/resource implementation is a B-006 design/adoption prerequisite.


## Bidirectional relationship finalization

CONTRACT-003's truss-relationship-mapping-finalization/0.1.0 now specifies complete retained pre-state coverage, full-byte uniqueness, immutable original mappings, candidate-first allocation, private paired persistence and complete actual post-state correspondence before head publication. The PostgreSQL catalog identity component owns this protected transaction procedure; the core component supplies pure admitted lineage matching. Legacy activation separately proves original source/category/owner provenance and removes the incompatible legacy uniqueness rule only through reviewed layout migration. Complete bounded collectors, canonical/native admission and original evidence producers remain explicit implementation profile selections.


STP-004 now defines the ordered A → repeat A → B → A → repeat A native schedule using the equal-membership STP-024 source pair. It distinguishes current-head repeat from historical input reuse, preserves every lineage/local ID through supported display-name changes and requires exact original archive/preimage/report custody plus independently observed no-effect repeat behavior. Attempt origin/context remains separately attributed outside compared input. Exact original fingerprint/archive/decoder/current-head producers and report/profile adoption still precede execution; source validity and byte witnesses cannot close these native procedures.


Owner selected reactivation on 2026-10-07. Match the exact original authored lineage, preserve its storage ID and historical definitions, fully validate retained values/keys/reservations/endpoints/ownership/cardinality and current authority, then atomically reactivate with catalog acceptance. Failed validation preserves retirement and prior head/effects. Distinct incarnations never inherit old permissions or storage identity.
