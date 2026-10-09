---
ddx:
  id: TD-035
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-035
      kind: informed_by
    - id: SD-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-005
      kind: informed_by
---

# TD-035: Immutable import source facts

## Technical Approach

Write one record_source row only when an import creates an object or edge. The source author/time/system are supplied source assertions, not authenticated journal origin. Preserve absent members and unknown source content; do not synthesize source author from the operator, role or load initiator. Later edits and skipped imports leave the original row untouched. Direct creates have no source row.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/import/source.ts` | Source object validation and explicit presence-preserving representation | US-035-AC1, US-035-AC2 |
| `packages/postgresql/src/import/apply.ts` | Atomic source insertion with created record and journal | US-035-AC1, US-035-AC3, US-035-AC4 |
| `packages/postgresql/src/reads/source.ts` | Authorized exact source lookup | US-035-AC1, US-035-AC2, US-035-AC3, US-035-AC4 |
| `tests/import/source.test.ts` | Independent source/origin/persistence assertions | All criteria |

## API and Storage

CONTRACT-001 owns (entity_kind,entity_id), load_id and source JSON object; CONTRACT-004 owns creation and CONTRACT-005 visibility. A lookup must distinguish a visible directly created record with no provenance from an inaccessible/unknown record under the host disclosure policy. Source retrieval does not turn untrusted authorship into verified identity. CONTRACT-004 now defines found/absent/not_found lookup, optional string/null source members and opaque exact source time text. The historical binding and retained-owner/current-authority semantic rule are drafted below; exact wire and native profile remain gates. Unknown values inherit D-05's exact carrier gate; JSONB cannot alone promise arbitrary numeric source spelling.

Insert source/canonical/journal effects under the same savepoint/transaction. A source insertion error removes the whole record attempt. Duplicate identity skip never replaces load_id or facts. Record updates do not touch source rows. Ordinary writer privilege permits append only under the qualified profile; verify update/delete refusal independently of application behavior. Polymorphic source identity lacks a simple shared FK: bind existence/type to the same checked creation pipeline and report engine-only guarantees honestly.

## Security and Lifecycle

The draft historical-source boundary in CONTRACT-004 now selects full original declaring/endpoint ownership under current authority, independently from live lookup. Load complete qualified creation inventory to distinguish imported found from proved direct-create absent; missing inventory is unavailable. Implement a separate opt-in retained-context reader, preserving original identity/endpoints after deletion and refusing current-key/replacement-row substitution. Exact loader/wire/resource/current-authority profile qualification remains open; semantic choice does not certify native support.

Module policies must protect source lookup for both objects and edges, including indirect reads and definer functions. The current visibility rule depends on the live record, while design says provenance survives deletion: deleted-record authorization uses the separate retained-context rule below, with native retention/loader qualification still required. Do not expose orphan source facts simply because a storage id is known. Re-created records use new ids and new provenance; earlier rows are not retargeted. Host-admin repair/retention authority, if offered, is separate from normal mutation and must be audited.

## Testing, Sequence and Rollback

STP-035 allocates four criteria. Consume the authored live/historical source classification and current-authority rules; select exact source carrier and original creation/source/native producers; write red atomicity, absence, immutable-edit and direct-create tests; implement insertion/read paths and qualify privileges/RLS. Caller rollback removes pending provenance; engine committed batches retain it. Implementation rollback does not erase historical source rows.

## Gates

Known-field types/null semantics and live lookup envelope are specified in CONTRACT-004. Exact unknown-value encoding, historical retained-context native qualification and native append-only enforcement remain explicit gates. No source-authentication guarantee or complete deleted-history access claim follows from storing caller assertions.


## Provenance retention dependency procedure

A deleted canonical row is not sufficient eligibility for source cleanup. Any separately selected administrative retention profile must first admit original installation/catalog/configuration custody and complete original source identity, creation classification, declaring owner and edge endpoint-owner closure. Observe all retained consumers of these facts: historical source lookup, original reservation/replay classification and required history/feed archive or recovery references. Use original immutable identities, not a recreated same-key record, as closure roots. A missing source/creation artifact or incomplete consumer inventory blocks cleanup rather than proving no dependency.

Reserve the complete bounded discovery, retained result/archive and containment resources before deletion. Under the original selected exclusion and lock order, revalidate both directions of the candidate cohort: every selected fact is eligible and every required dependent is retained or removed through the same explicitly admitted cohort procedure. Source cleanup cannot delete an active reservation, unresolved operation or retained recovery reference, nor remove the only ownership/creation evidence needed to distinguish imported from direct-created history. Selected retention policy must explicitly define expired-history behavior before removing such evidence; absent is never inferred from cleanup.

After confirmed deletion, preserve immutable original cohort/eligibility/dependency/result evidence outside the deleted source rows under the existing retention result custody. Unknown submission/termination keeps original cleanup recovery open; no automatic repeat under a newly discovered cohort. Routine source lookup remains read-only and cannot opportunistically clean rows. This specifies eligibility and preservation behavior without selecting a retention duration, enabling source deletion for ordinary writers or claiming an installed cleanup routine.


Live absence must be backed by original qualified creation classification, not merely an empty source-table query. An imported empty source object is found; missing required imported source evidence is unavailable/integrity failure through the selected existing outcome procedure. STP-035 separates direct absence, empty imported facts, missing evidence, hidden records and deleted/recreated identities. This refines the existing semantic distinction without adding a public status or substituting historical lookup for the live capability.
