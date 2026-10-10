---
ddx:
  id: TD-008
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-008
      kind: informed_by
    - id: SD-002
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
---

# TD-008: Keep what the schema does not define

**Story:** [[US-008]]. **Parent:** [[SD-002]]. **Feature:** FEAT-002.

## Technical Approach

Inherit separate defined-property and retained maps. Unknown fields are retained under their authored names, with exact recursive values supplied by US-007's codec. Classification is catalog-driven and never infers a type from JSON appearance. Catalog acceptance computes explicit name-to-property rebind candidates, validates them before persistence, and applies accepted moves atomically with the revision and journal.

The complete source of each accepted import record must remain recoverable across retained/defined homes. CONTRACT-003 now requires absent destinations, unambiguous qualified matching and valid candidate values; collisions/incompatibility refuse without loss. CONTRACT-004 preserves existing retained entries against differing set/unset and permits exact representation-identical no-ops. Mapping profile and complete event encoding remain gates; no silent coercion or merge is permitted.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/core/src/values/classify.ts` | Partition values by pinned definitions, retaining authored names and exact content | US-008-AC1, US-008-AC3 |
| `packages/core/src/catalog/rebind.ts` | Produce validated moves with source/destination and rule diagnostics | US-008-AC2 |
| `packages/postgresql/src/catalog/rebind.ts` | Persist moves, journal each and update revision atomically | US-008-AC2 |
| `packages/core/src/reports/retained.ts` | Enumerate retained values and accepted rebind outcomes without hiding unresolved content | US-008-AC1, US-008-AC2 |
| `tests/retained/native.test.ts` | Import/revision/recovery observations through independent SQL | All criteria |

All runtime components are new. Pure classification and reports remain browser-compatible and I/O-free.

## API/Interface Design

CONTRACT-001 owns retained storage; CONTRACT-003 owns revision/rebind reports; CONTRACT-002 owns journal rows; CONTRACT-004 owns import/writes; CONTRACT-007 owns transactions. Consume CONTRACT-003/004’s authored collision, incompatibility and exact-no-op precedence. Selected name/owner mapping, recursive value/event codecs and native producer/profile admission remain implementation handoffs; do not invent a different overwrite rule in an inline story API.

## Data Model and Integration

Use the existing `retained` map and property map. A successful move removes the exact retained entry and inserts the validated property-id entry in the same transaction. The complete rebind event must identify both homes and preserve presence/value evidence under the authored complete-event contract. Admit the exact original event/codec/extractor profile before persistence; a property-only delta cannot qualify full history. Match only within the owning type/document identity and explicit declared property naming policy, never across a guessed global namespace.

The importer keeps rejected-record source/report evidence separate from accepted persisted values. Rejected input is not an accepted lossy record. Later writes follow CONTRACT-004’s explicit retained collision rule: an exact representation-identical set is a no-op, while a different set or unset refuses the whole mutation/group. Setting a newly defined same-name property cannot bypass an unresolved retained entry. Unrelated writes report the surviving entry; no cleanup removes it.

## Security and Performance

Host role/context controls stored rows and reports. Parameterize names and values; authored names never become SQL identifiers. Reports must respect row visibility and avoid leaking hidden retained content. Catalog rebind scans can be large: plan candidate validation before effects, record affected counts and measure acceptance duration; do not move work outside the atomic revision to meet a latency target. Pure code caches definitions by full catalog identity.

## Testing

STP-008 allocates all three criteria. Use independently authored source fixtures with unknown nested numeric, binary, null and empty values. Count source leaves/homes and compare recovered content, not merely row totals. Three matching values yield three rebind events; unmatched values remain byte/meaning-exact within the qualified profile. Execute STP-008’s authored failure/collision cases under the selected complete profile, asserting old head/maps/journal survive refusal. Present-null, equal-value and unequal-value destinations all refuse; an absent destination alone permits a validated candidate move.

## Migration and Rollback

No layout DDL. Failed revision rolls back moves and journals, leaving the old accepted head and retained content. Never delete retained values as cleanup. Changing name matching or encoding requires an explicit profile/migration decision. Unknown source/native content remains recoverable across any such change.

## Implementation Sequence

1. Create import retention and three-value rebind fixtures/red native tests.
2. Consume shared refusal/no-op/rebind rules; admit exact original owner/name mapping, recursive codec and complete event/native producer profiles before effects.
3. Implement pure classification/rebind planning and transactional persistence/report assembly.
4. Verify independent recovered content, revision failure atomicity and browser-compatible core.

## Risks and Gates

Numeric lexical retention consumes the selected exact-value direction and requires its actual codec qualification. Destination collision, incompatible-candidate refusal and later retained-write precedence are authored in CONTRACT-003/004; they are not pending product choices. Exact unambiguous owner/name correspondence and complete value/event/native profile composition still gate general support. Mapping may not case-fold, normalize names, infer global owner identity or overwrite present null to obtain a successful rebind. Qualification remains required for all three story criteria; source/codecs or fixture counts alone do not establish lossless import/history.
