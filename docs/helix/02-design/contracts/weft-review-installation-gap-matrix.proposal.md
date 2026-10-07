# Review layout installation gap matrix

Companion to CONTRACT-008/012. Profile 0.7 is a 94-statement source composition, not an installation bundle. This matrix identifies concrete missing outputs without treating every unexecuted test as missing design. Historical profiles remain separately pinned.

| Family | Declared source home | Required design/implementation output before installer admission |
| --- | --- | --- |
| Catalog | Qualified module/type/relationship owners, lineage/source adjuncts, keys and lifecycle history | Original interpretation/extraction profile; acceptance/rebind/reactivation producer; report/head publication and complete conversion. Source-preserved high-water routines exist but need native binding. |
| Values and graph | Baseline object/edge plus tree/scalar homes, touch and capacity | Selected leaf/source-token/domain codecs; protected writer/finalizer, OLD/NEW attribution and complete operation generation/capacity guards. Five absent custom trigger bodies are identified separately. |
| Keys and reports | Full-byte bucket/reservation homes and immutable acceptance reports | Serialized digest-route/full-byte equality, original namespace encoder, reservation revalidation on reactivation and post-effect canonical report encoder. Do not reintroduce legacy object_key or schema_rev.report. |
| Complete feed | Four fact/prerequisite stores and complete consumer | Original five-fact/two-closure extraction, shared complete-union validator, registration/fencing, complete-boundary CAS and retained-floor admission. Baseline feed_consumer remains journal-only. |
| Recovery | Administrative receipt, seed attempt and seed artifacts | Protected immutable receipt arbitration before stale generation checks; seed state/artifact association and source confirmation; independent committed observation and protected cleanup. STP-041 RS-01–07 are planned. |
| Installation | Marker/archive | Complete original inventory/bundle/archive producer and IM01–IM07 atomic publication; actual role/namespace/dependency/body/type parity. Archive hashes alone cannot establish readiness. |
| Authority | Qualified module_access columns | Exact three-argument administrative helper and protected RLS/read/writer/retention roles for every selected store. The historical two-argument grant example and direct-DML privileges cannot qualify this expanded profile. |

## Authority composition boundary

### Exact trigger-to-routine composition worklist

The preserved trigger fragments describe thirteen source events referencing five trigger-returning routines. Source identities already exist for all thirteen: six row-home and three edge-limit triggers in their physical-ID catalogs, plus four feed triggers and four associated constraint effects in truss-feed-current-union-trigger-effects.proposal.json. The earlier physical-ids filename scan missed that effects catalog; reuse these existing IDs. None of these fragments is in layout 0.10, and matching table presence does not install their behavior.

| Trigger source family | Registered targets / events | Referenced private routine and required dependency |
| --- | --- | --- |
| Row-home observers (three) | row_home_state/node/scalar; AFTER ROW INSERT/every UPDATE/DELETE | row_touch_observe() RETURNS trigger; original OC registry selection, OLD/NEW tuple attribution, capacity reservation and generation producer |
| Completion guards (three) | row_home_touch/capacity/operation; deferred AFTER ROW INSERT/every UPDATE | row_touch_commit_check() RETURNS trigger; full touch/capacity/operation validation plus ordinary feed_union_validate_current_scope() RETURNS void when complete feed is selected |
| Edge/marker observers (two) | edge/edge_limit; AFTER ROW INSERT/every UPDATE/DELETE | edge_limit_observe() RETURNS trigger; original edge/marker contribution custody and EL complete-scope validation dependency |
| Catalog observer (one) | rel_def; AFTER ROW INSERT/every UPDATE/DELETE | edge_limit_catalog_observe() RETURNS trigger; protected catalog-operation custody, complete affected relationship scope and EL validation dependency |
| Complete-feed guards (four) | feed_tx/member/prerequisite/configuration_prerequisite; deferred AFTER ROW INSERT/every UPDATE/DELETE | feed_current_union_check() RETURNS trigger; exact feed-event attribution and the same ordinary feed_union_validate_current_scope() RETURNS void |

CONTRACT-006 proposes the exact zero-argument ordinary feed validator separately from the two trigger handlers. CONTRACT-001's edge_limit_verify_current_scope() RETURNS void is likewise a separate private validation dependency, not an additional observer or permission to call a trigger handler through SELECT. Include these call edges and complete collector/codec/account dependencies in CH-02. Routine source/type/security/profile selection remains open; this table allocates existing obligations without fabricating installed bodies.

CH-01 must cover source trigger identities and actual installed trigger/partition/enabled/internal dependency effects. CH-02 must cover caller/event/custody admission and native validator realization. CH-03 must reject a bundle containing only the thirteen declarations, or handlers without their ordinary validators. Whole-scope absence, direct privileged bypass, immediate constraint firing, later dirtying, rollback/savepoint and deferred COMMIT remain native qualification schedules. A trigger count or routine-name join cannot close these gates.

CONTRACT-005's qualified policy selects `grant_module_roles(document_id,module,writes)`. The current profile AST declares only two custom ordinary functions, catalog_global_high_water_v01 and catalog_key_high_water_v01. It does not declare the grant helper or the five trigger bodies. Source table presence therefore cannot establish policy installation.

The administrative helper must resolve exact document/module and native role identities, reject missing/ambiguous mappings and apply only privileges admitted by the selected protected-writer profile. `writes` must not grant raw DML that bypasses canonical writer/finalizer/receipt/seed enforcement. Fixed schema usage and qualified callable privileges are distinct from document-specific row authority; policies require current complete owner union. Select exact routine identity, owner, search path, argument/result types, effective role paths and authorized invocation before including its body/grants in the bundle. Do not grant blanket access to archive/recovery evidence as a workaround for a missing reader.

## Next composition outputs

### Migration home omission (current 0.9 audit)

The [bootstrap initialization source](migration-admission-initialize-v0.1.proposal.sql) now defines the exact eight original parameters and five result fields. The protected initializer admits complete installation/epoch/configuration/binding/inventory originals and selected starting generation first; it verifies scalar key_reuse/journal_mode against decoded configuration and marker installation identity against exact UTF-8 bytes. Original bootstrap generation comes from the selected initialization profile, not a guessed migration receipt. The binding must resolve to exact installed key/layout/interpretation meaning and its original initialization anchor.

Acquire original schema_head/namespace exclusion and prove complete admission-row absence before INSERT. Repeating initialization is not upsert: an existing row enters the full existing-installation observation/reconciliation path. Require exact INSERT completion/cardinality and result descriptors/hex/generation correspondence, then independently reread all stored bytes and scalar projections. Digest equality alone cannot close this check. Initialize before the final ready-marker publication in the same installation transaction; any failure rolls back both. Unknown commit retains the original installation attempt rather than creating a new epoch or generation. Existing IM01–IM07 native parity/constraints/archive obligations remain mandatory.

Both original declarations now have existing-UMF source captures: [admission model](migration-admission-layout-v0.1.draft.umf.json) and [receipt model](migration-receipt-layout-v0.1.draft.umf.json). Capture/save/reload/export preserves exact source and exported SQL; one admission table and one receipt table are recognized. Receipt allocator/index remain unhandled by the scoped declaration projection but are retained in the native tree and full export. Source capture does not supply native inventory completeness, installation initialization or profile adoption. Use the complete preserved statement arrays when composing; do not discard unhandled statements or treat table counts as all physical effects.

The selected table inventory omits `installation_admission` from [migration admission SQL](migration-admission-layout-v0.1.draft.sql) and `key_migration_receipt`/its sequence and route from [migration receipt SQL](migration-receipt-layout-v0.1.draft.sql). These existing declarations remain unadopted fragments. Layout 0.9 cannot claim the receipt-backed migration capability merely because its key bucket and installation marker tables exist.

Before composition, reconcile installation_admission's original installation/epoch/configuration/binding/inventory carriers with installation_marker/archive. The marker records installed identity/readiness; admission records current selected configuration/binding under schema_head exclusion. They must agree on exact installation continuity without conflating the original installed inventory with later migration state. Never initialize admission from today's marker hashes alone or replace head locking with this observation row.

The receipt producer preserves exact original request/attempt/result and checked prior/resulting generation in the same migration transaction. Nonunique digest routing requires full installation/epoch/attempt-byte equality before effects; sequence defaults do not establish idempotency. Retain original receipts and dependency closure across later configurations, failure and acknowledgment loss. Native generation overflow must refuse before subtraction/increment effects. Compose exact source identities, initialization, privileges, archive/receipt conversion and complete feed transition correspondence as one versioned migration-capable profile; do not enable the capability on 0.9 by adding only a marker flag.

1. Select one original operation/codec/security/resource tuple against the governing contracts, including allocation durability and permitted deployment constraints. Record unresolved product choices separately.
2. Allocate exact routine/trigger/policy/grant and dependency identities across the families above; attach source bodies and complete implicit-effect inventory. Keep native catalog observations separate from authored IDs.
3. Compose a versioned full installer with initialization and conversion, then independently compare the actual native inventory. Publish the ready marker only after complete parity.
4. Submit the exact versioned storage/binding scope for Weft review when authorized. Accepted compiler mapping, installed layout and support qualification are independent evidence.

Native routine implementation and execution are future build work. Remaining unspecified codec, operation registry, driver observation and security/deployment selections are design gaps. This matrix neither adopts ADR-005/006/007 nor turns optional compiler capabilities into required upstream changes.


Reactivation audit: key_lifecycle_history is an existing separately captured source home absent from profile 0.8. [Selected persistence](catalog-reactivation-persistence.proposal.md) requires its composition plus owner-local transition producers and explicit reactivation report inventory before claiming key lifecycle support.


Current source correction: profile 0.9 now composes the key_lifecycle_history table/index. The earlier 0.8 omission remains historical evidence; protected transition/report production and CP-01–06 native qualification remain open.


Current composition correction: profile 0.10 now includes both migration homes, allocator and route. The 0.9 omission is historical; original marker/admission initialization and continuity, protected receipt/feed producers and complete native qualification remain required.
