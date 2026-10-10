---
ddx:
  id: TD-036
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-036
      kind: informed_by
    - id: SD-001
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# TD-036: Revision acceptance origin

## Technical Approach

Store acceptance origin on the accepted schema_rev in the same transaction as documents, catalog changes, transforms and head advance. Caller supplies actor/reason and extension facts; database supplies trusted acting role. Ignore forged db_role exactly as journal origin does. Rejection or caller rollback leaves no revision-origin row. Reuse the trusted-origin mechanism rather than a second catalog-specific identity convention.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/catalog/accept.ts` | Atomic origin insertion at accepted revision | US-036-AC1, US-036-AC2, US-036-AC3 |
| `packages/postgresql/src/journal/origin.ts` | Shared trusted role capture and origin construction | US-036-AC1, US-036-AC2 |
| `packages/postgresql/src/catalog/revisions.ts` | Authorized revision origin lookup | US-036-AC1, US-036-AC3 |
| `tests/catalog/origin.test.ts` | Native role, rejection and shape guard matrix | US-036-AC1, US-036-AC2, US-036-AC3, US-036-AC4 |

## Interfaces and Model

CONTRACT-003 defines origin input and atomic acceptance; CONTRACT-002 defines actor versus trusted role; CONTRACT-007 preserves caller transaction ownership. Origin must be a JSON object with x-* content retained under the qualified exact carrier. The generated bundle's schema_rev CHECK must refuse arrays/scalars/SQL NULL at the native boundary, not only through TypeScript validation. Include this constraint in bootstrap inventory and corrupt-surface probes. Definer functions must capture acting role before privilege elevation or use a qualified trusted propagation path; function owner is not the actor.

## Security and Read Semantics

Catalog acceptance requires administrative authority separate from ordinary mutation role grants. Read authorization must cover origin actor/reason/extension disclosure; a revision spanning multiple modules must not leak hidden module details through a global report. Define the shared projection/disclosure policy before release. Caller actor remains a supplied assertion unless host authenticates it; db_role is database-derived. No-actor origin still contains the trusted role.

## Testing and Failure Handling

STP-036 owns four criteria. Observe schema_rev/head/catalog/data/journal independently after semantic rejection, late persistence failure, cancellation and caller rollback. A returned rejected diagnostic is not persisted as an accepted revision. Only verified complete acceptance-input equality at the current head returns the existing revision/report and preserves its original origin. Equal derived rows alone cannot establish repeat: changed document bytes, binding, policy, validator/support or transform pins require current acceptance validation under CONTRACT-003. A historical match after intervening acceptance is not a current-head repeat. The new attempt’s supplied actor/reason cannot overwrite the original accepted origin or silently create accepted-history evidence for a no-op. If attempted-acceptance auditing is needed, the host owns a separate mechanism; it must not masquerade as accepted history.

## Sequence, Rollback and Gates

Finalize shared trusted-role/definer capture and catalog-read policy; write red native origin and JSON-shape tests; implement shared builder/insertion/read path; qualify each target. Origin failure rolls back acceptance. Historical provenance is not erased when disabling an implementation. Exact extension preservation, origin constraints/privileges and read projection remain gates. No support claim follows from schema parsing alone.
