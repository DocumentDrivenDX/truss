---
ddx:
  id: TD-038
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-038
      kind: informed_by
    - id: SD-008
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-005
      kind: informed_by
---

# TD-038: Cross-module relationship authorization

## Technical Approach

A relationship retains its declaring module independently of source/target type modules. Derive typed endpoints from valid UMF references, then enforce edge visibility as the intersection of relationship, source and target module read authority. Creation additionally requires relationship-module write authority. Neither application filtering nor source-only policy is sufficient.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/catalog/relationships.ts` | Preserve declaring identity and resolved endpoint identities | US-038-AC1 |
| `packages/postgresql/src/catalog/derive.ts` | Typed endpoint triples and relationship ownership | US-038-AC1 |
| `packages/tooling/src/policy/bundle.ts` | Reuse CONTRACT-005 intersection predicate and WITH CHECK | US-038-AC2, US-038-AC3, US-038-AC4 |
| `tests/host/cross-module-edges.test.ts` | Native visibility and write-refusal matrix | US-038-AC1, US-038-AC2, US-038-AC3, US-038-AC4 |

## UMF and Weft Boundary

Current UMF can resolve module references within an owning document. Use one valid document containing sales and billing for initial AC1 proof; it does not prove cross-document resolution. Proposed UMF CONTRACT-045 dependencies are not implemented and do not reinterpret bare local references. Truss must not bypass reference-validator rejection by inventing external resolution or provisional semantics for invalid UMF. Unknown-endpoint policy applies only after upstream-valid supported input; broader package/external acceptance requires its own original upstream-valid representation and complete source/profile adoption. ADR-004 already requires document-qualified identity in mapping without collapsing equal module names; it does not create external reference-resolution support.

Weft owns relationship SQL compilation; Truss owns storage mapping and database authorization. HAS_RELATED/RELATED_KEYS and direct edge lists must execute under the actual role so hidden links do not enter aggregates or decoded keys. Native integration qualifies this obligation; compiled artifact acceptance alone does not.

## Data, Security and Read Paths

No additional per-relationship DDL. Relationship type and endpoint triples use the shared catalog. Include a three-module fixture with relationship declaring module distinct from both endpoints, proving all three checks independently. Test outgoing/incoming lists, direct SELECT, lookup by edge id and declared compiler reads. Endpoint visibility alone is insufficient without declaring-module access. Unauthorized creation must leave edge, markers, journal and source facts absent. Changing endpoints/type must reapply the write predicate.

CONTRACT-005 now requires historical relationship and both endpoint ownership contexts under current grants for journal/source/tombstone disclosure after deletion. Full before/after payloads require both contexts, and missing retained provenance refuses rather than falling back to relationship-only access. Physical provenance and policy implementation remain gated; a direct edge visibility pass cannot establish complete historical isolation. FK/unique existence leaks remain documented and host-mediated. Definer execution must preserve acting role and fixed search path.

## Testing, Sequence and Rollback

STP-038 allocates four criteria. Pin valid in-document references and catalog ownership; write red three-module native tests; derive endpoint triples; qualify policy and direct/compiler reads. Policy rollback must not broaden access; withdraw incompatible profile until host-admin repair. Unknown external dependencies remain blocked without network/latest fallback. All runtime components and tests are planned.
