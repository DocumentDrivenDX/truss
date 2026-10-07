---
ddx:
  id: TD-045
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-045
      kind: informed_by
    - id: SD-007
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
---

# TD-045: Bootstrap the internal layout from UMF

**User Story:** US-045. **Feature:** FEAT-007. **Parent:** SD-007.

## Technical Approach

Consume CONTRACT-008's installation state rules: dedicated administrative transaction, shared namespace lock before emptiness inspection/recheck, inventory validation before a provisional marker, and committed readiness only after confirmed commit. Resolve uncertain commit through fresh nonmutating marker plus full-inventory observation after the original transaction ends. Preserve foreign objects on every failure; default bootstrap refuses hidden nontransactional statements. Namespace-lock encoding, marker schema and outcome inspection remain explicit profile deliverables.

Inherit the UMF-native physical-model route of SD-007/CONTRACT-008. Keep the checked SQL as an independent comparison source until the authority transition passes. Native capture/deparse is a bounded model-authoring bootstrap, not a second general SQL generator. The design candidates under `02-design/models/` prove source retention and deterministic export only.

## Component Changes

| Component and planned files | Change | Criterion realization |
| --- | --- | --- |
| `packages/tooling/src/bootstrap/model.ts` | Verify pins; export current native model; deterministic inventory/statement accounting | US-045-AC1, US-045-AC3, US-045-AC4 |
| `packages/tooling/src/bootstrap/install.ts` | Inspect namespace, execute declared stages atomically, run installed checks | US-045-AC5 |
| `packages/conformance/src/bootstrap/catalog.ts` | Independently query every declared physical surface; normalize only environment OIDs | US-045-AC2 |
| `tests/bootstrap/model.test.ts` | Repeat, edited-node and omitted-object fixtures | US-045-AC1, US-045-AC3, US-045-AC4 |
| `tests/bootstrap/native.test.ts` | Two isolated generated/baseline databases and incompatible existing namespace | US-045-AC2, US-045-AC5 |

## Interfaces and Integration

CONTRACT-008 owns bundle, report, qualification and refusal semantics. UMF CONTRACT-015 owns native import/export fidelity. Use its supplied backend API; no string-replacement schema renaming or hand-patched fallback SQL. The installer is tooling outside the pure core and never runs during application catalog acceptance.

## Data Model

### Physical reconciliation before model authority

The existing 0.2 native capture is a baseline, not the completed toolkit layout. Reconcile these selected contract additions in a new versioned model/bundle before generating a claimed complete installation:

| Design surface | Required model/inventory closure | Independent parity/admission probes |
| --- | --- | --- |
| ADR-004 catalog lineage | Document-qualified ownership/definition archives and chosen lifecycle identity; preserve old pins | Same local identity in distinct documents; retired/reintroduced element; exact accepted archive lookup |
| CONTRACT-009 configuration | Source epoch/installation, monotonic generation and exact setting archive; head exclusion and qualified administrative procedures | Stale snapshot, generation exhaustion/reset refusal, mid-import settings change, journal-mode partial transition |
| CONTRACT-001 selected key profile | Portable byte transport and authored/local mapping; large-key bucket guard/key-row/nonunique digest index if selected | Exact native equality, incompressible index boundary, digest collision coexistence, stale-snapshot guard admission and protected reservations |
| ADR-005 receipt candidate, if selected | Complete input/result/original configuration, authorization and protection/expired-identity inventory | All-no-op replay/conflict, old policy replay, unknown commit and protected purge |
| CONTRACT-001 relationship retained home, if selected | Exact edge retained column/constraint or explicit replacement home, coherent model/statement/query descriptors, selected value/presence and existing-provenance handling | Full edge retained readback/history, wrong-marker query refusal, fresh bundle versus nonempty migration refusal; source capture is not native parity |
| CONTRACT-002 complete-carrier branch, if selected | Exact metadata op CHECK, four named coarse checks, full event/origin byte codec and protected producer/finalizer; legacy origin/request projection reconciliation | Native NULL-safe wrapper refusal, full semantic/column/role/group mismatch controls; 41-statement review source parity is not installed support |
| ADR-007 history and side facts | Complete object/edge envelopes, exact presence and old/new definitions; source/reservation original context | Deleted edge/endpoint history, no-op transform interpretation, exact source and typed reservation correspondence |
| CONTRACT-006 complete feed | Transaction/member/catalog-prerequisite/configuration-prerequisite stores, producer/finalizer, dependency guards and retained ownership | Forced immediate finalization followed by writes, savepoint rollback, revision-only transaction, missing configuration closure and ordinary-writer forgery |
| CONTRACT-005 authority | Selected current-authority guard/coordinator physical obligations and complete privilege/RLS/definer inventory | Held read-only snapshot with revocation; inherited/PUBLIC/child-partition bypass paths |
| CONTRACT-003 report home, if selected | Reconciled revision parent/seed and complete separate-report store, original artifact/readers, non-row report/head guards and privilege/dependency inventory; retain earlier revision identities | No placeholder parent report, exact one complete report per positive accepted revision, original artifact equality, head/report finalization and bypass refusal; fresh installation does not qualify retained conversion |
| CONTRACT-008/011 installation | Protected marker, exact full inventory and qualification observation surfaces | Forged marker, omitted helper/store, unknown installation commit, stale grants or changed function body |

No guessed column or opaque annotation closes these rows. UMF owns native physical-description/import/export fidelity; Truss owns which selected contracts the layout must realize. Preserve unresolved native semantics explicitly. Existing UMF capabilities are sufficient for the selected scope; Truss owns composition and complete generated/native correspondence. Escalate only a demonstrated governing requirement conflict, rather than treating partial declaration extraction as a new upstream feature prerequisite. Require exact model-node-to-statement/inventory accounting and baseline/native behavior comparison for each selected surface. Optional profiles remain explicitly qualified components; a full selected profile cannot omit a required store while retaining its capability claim. These are model-authoring deliverables, not a license to edit the old capture receipt or claim parser export proves installation parity.

Design candidates are separate native UMF documents for fixed layout and optional isolation. Their receipts pin source/model/generated hashes. Initialization and deployment names are separately explicit and inventory-accounted. A new layout candidate receives new versioned artifacts; old models/receipts remain recoverable.

## Security

Connections/administrative privileges belong to the host. Model text cannot load executable plugins. Reject unsafe identifiers and existing target objects before mutation. Roles outside the target namespace are preflight host obligations; do not alter shared roles blindly. Fixture installation uses isolated disposable targets, never a production endpoint.

## Testing

STP-045 maps every criterion. Compare source and regenerated native catalogs on each selected live-server version, then probe keys/endpoints, exact values, journal partition failure, role behavior and rollback in both databases. Use the existing checked SQL and independent assertions; generated SQL cannot define its own expected catalog. Parser success cannot count as AC2 or AC5 evidence.

## Migration and Rollback

Fresh installation only. Transactional failure rolls back schema objects/initial rows. Optional nontransactional stages record cleanup outcomes before readiness. Authority transition changes model plus generated artifact plus parity receipt in one reviewed change. No installed-data migration is included in this story; an incompatible namespace is refused.

## Implementation Sequence

1. Create red determinism, omission and changed-AST tests from design candidates; publish bundle/report schema under CONTRACT-008.
2. Implement pin/coverage validation and current-model export using the pinned UMF backend.
3. Build the isolated catalog oracle and baseline/generated probes; record all server/runtime/source versions.
4. Implement empty-target preflight and atomic installation; exercise failure and cleanup.
5. Review authority transition only after every criterion has evidence.

## Risks and Gates

Native backend release may differ from target server syntax; qualification is per server. PL/pgSQL bodies need actual server probes. Layout 0.2 comments/version inconsistencies need reconciliation. Receipt/identity proposals may change the physical layout; model generation must use the accepted candidate and preserve the older archive rather than baking a provisional layout into a release.

## Complete-feed fact timing inventory

The proposed feed_member physical inventory now includes trusted original fact-write timestamp and fact-clock profile for every required kind. Native producer capture is atomic/savepoint-scoped and immutable across finalizer rebuilds and delivery; authored source.at remains domain provenance. B-011 must qualify timestamp precision/clock procedure and journal write-time agreement before describing this extension in the generated UMF model. Legacy metadata absence permits no fabricated timing backfill or complete freshness claim. Bootstrap inventory/digests include the chosen timing columns, native guards and clock procedure as an explicit new profile.

## Proposed installation metadata property homes

For the new layout candidate, place protected installation identity and original bundle/inventory bytes in fixed native metadata, separate from application object/edge/catalog records. Proposed logical inventory identities are `truss.installation_marker` and `truss.installation_archive`; deployment SQL names remain resolved through the collision-checked bundle identifier map. These are proposed additions to the next layout, never patches to the captured 0.2 model. Author exact native nodes only after the selected profile’s checks and privilege/retention procedure are admitted.

| Native inventory identity | Required property home and invariant | Write/retention boundary |
| --- | --- | --- |
| installation_marker | One deployment marker per intended namespace: exact installation/layout/database/schema identities, bundle digest, inventory profile/digest and database-observed installedAt. Identity text stays opaque; no UUID parsing or display-name substitution. Full row matches CONTRACT-008 marker wire. | Installer-only insert after same-transaction inventory check; ordinary writers cannot insert/update/delete. No runtime catalog mutation can replace it. |
| installation_archive | Immutable original exact bundle and expected/installed inventory bytes with content digests and original profile pins, keyed by the marker’s installation identity and artifact identity. Complete artifact bytes are retained, not only hashes or regenerated current inventory. | Installer writes in the same transaction before the marker; no partial committed archive. Selected retention cannot remove bytes needed for installed readiness or unresolved original attempt recovery. |
| native inventory observation | Fresh independently queried catalog/body/grant/partition facts and profile-scoped normalized comparison evidence. Original installed inventory remains immutable even when observed state has changed. | Explicit authorized read procedure; observation never edits marker/archive or repairs drift. |
| qualification evidence | Target/backend/runtime-specific receipts and support qualification belong to external conformance/recovery custody, linked to exact installation and inventory pins. | Evidence records are not an editable database ready flag and cannot replace native observation or current data authority. |

Marker/archive physical scalar types, identifier byte bounds, digest derivation, unique/FK actions and byte custody are part of the selected versioned native profile. Preserve exact bytes in a binary carrier; an incidental JSON parse/render must not replace original bundle content. Marker native fields and encoded marker artifact must compare exactly. Store no connection strings or host credentials in these identities. Domain artifacts retain their complete unknown extension content under governing contracts; they are not redacted by guessing field names.

Bootstrap checks full archive/marker correspondence in its own transaction; success remains provisional until original commit confirmation. Direct native insertion of a forged marker or replacement of archived bytes by an ordinary writer must fail independent bypass tests. Administrative function/privilege alteration invalidates qualification until the actual installed inventory is re-observed; a hash stored before the alteration cannot certify current state. Restore/clone identity handling requires an explicit deployment profile and cannot silently reuse original recovery identity. Exact native DDL/guard/administrative trust and recovery custody profiles remain design gates.

Marker/archive native definitions and original creation recipe enter the immutable inventory basis; actual generated marker/basis archive row contents are separately observed/validated, avoiding self-embedding hashes. The complete full observation envelope retains those rows and original correspondence evidence. Initial pre-marker absence is stage-specific only; final provisional and all committed checks require exact marker plus complete archives before readiness. Never repair committed missing metadata by recreating rows from present native tables.

## Baseline physical ID allocation fragment

[Draft baseline IDs](../models/truss-layout-0.2.physical-ids.draft.json) explicitly allocate thirty Truss-owned IDs for one schema, nineteen tables, two sequences and eight explicitly declared indexes in the checked 0.2 SQL. Original text line locators and source SHA-256 are recorded only as provenance, not a SQL parser or native coverage certificate. Labels are authored allocations rather than a rule to regenerate identity from current spelling. Preserve them under later native rename only through reviewed versioned binding/lineage design.

The fragment is explicitly complete:false. Column IDs are now allocated; their native type/default/null/collation/generated definitions, constraints/implicit indexes/roles/functions/initialization and optional/new toolkit additions remain enumerated outputs. It cannot replace the selected expectedCatalog manifest or qualify the earlier captured model. Existing source/model/generation receipts stay unchanged. The structural allocation receipt checks uniqueness and exact original declaration locators; the omitted surfaces prevent complete-authority or native support claims.

The baseline fragment now adds 132 explicitly authored column IDs across all nineteen captured tables, for 162 allocated entries total. Parent IDs, original declaration locators and authored column order are checked against the unchanged source hash. These are semantic inventory allocations, not evidence of native attnum/type/default/collation or complete model binding; native observation and full definitions remain required. No current data IDs, UMF element IDs or Weft entity identities are inferred from these column labels.

The 162 allocations now also carry exact JSON pointers into the unchanged captured UMF tagged tree, bound to its original SHA-256. Each pointer resolves uniquely and its captured native name matches the authored inventory identity; all 132 column orders were compared with captured declarations. These locators strengthen provenance without making source statement indexes generated-output ordinals. They do not close native definition qualification, complete exporter correspondence, selected new layout inventory, or rename lineage. [Binding receipt](../../04-build/evidence/design-audit/physical-id-model-binding.json) records this limited check.


## Relationship lineage candidate capture inventory

The [candidate UMF model](../models/truss-relationship-lineage-candidate.umf.json) captures CONTRACT-001's unapplied fixed relationship_lineage adjunct through the existing owner parser/model/export path. Its [capture receipt](../models/truss-relationship-lineage-candidate.capture.json) passes exact archived source, JSON reload, stable export and the five-column order. One table declaration is observed; selected native type/index semantics retain unresolved diagnostics and complete=false. No core scalar interpretation or native validity is invented.

[Seventeen authored physical allocation entries](../models/truss-relationship-lineage-candidate.physical-ids.draft.json) cover the table, five columns, five constraints, explicit/primary-key indexes, three explicit NOT NULL attributes and one generated expression. All seventeen entries bind exact captured source nodes/bases with source/model hashes; the primary index shares its owning primary-constraint source basis, not independent index emission. These are stable Truss allocation labels, not IDs regenerated from spelling. Unnamed/implicit native objects have no guessed native name or generated statement ordinal. Independent native object/ownership identity and complete exporter accounting remain open, as do referenced rel_def home/provenance, replacement legacy uniqueness, complete owner/policy mapping and native canonical/full-equality/finalizer/privilege procedures. The adjunct's source receipt cannot qualify the new full layout or silently modify baseline 0.2.

## Selected metadata realization (2026-10-07)

Marker/archive native declarations are now authored in installation-metadata-v0.1.proposal.sql and integrated into CONTRACT-012's 0.5 review model. Two tables, a separate archive allocator, deferred archive-to-marker FK and nonunique complete-identity route replace the earlier “exact native DDL still missing” status for these homes. Original artifact bytes remain binary, public marker identities stay opaque, and native clock/text parity is an explicit protected producer obligation. Metadata definitions/recipe enter the immutable inventory preimage; actual marker/archive row values and eventual commit observations stay separately retained/validated. CONTRACT-008 IM01–IM07 and STP-045 IM-T01–IM-T08 now give concrete publication and failure ordering. Exact native roles/producers/guards/dependencies and complete installed parity remain unfinished; the source composition is not an installable bundle.
