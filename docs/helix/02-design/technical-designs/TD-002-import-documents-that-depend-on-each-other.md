---
ddx:
  id: TD-002
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-002
      kind: informed_by
    - id: SD-001
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
---

# TD-002: Deterministic dependency ordering

## Technical Approach

Build the validated document dependency graph, collapse strongly connected components, then topologically order the component graph dependency-first. Order members of a cyclic component by exact document identifier UTF-8 byte order. Among ready components use their sorted identifier vectors lexicographically as deterministic tie-breaker. Derive all types across the resulting whole set before properties/keys/relationships; cyclic ordering never requires premature endpoint derivation.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/catalog/dependencies.ts` | Qualified dependency extraction and missing-target diagnostics | US-002-AC1, US-002-AC2 |
| `packages/core/src/catalog/order.ts` | SCC/topological ordering and byte-order comparison | US-002-AC1, US-002-AC2, US-002-AC3 |
| `packages/postgresql/src/catalog/derive.ts` | Whole-set phased derivation and persisted ord | US-002-AC1, US-002-AC2, US-002-AC3 |

## Upstream Dependency Gate

The story's cross-document references and mutual-dependency examples are not yet implemented by UMF's current local-reference resolver. Proposed CONTRACT-045 does not authorize Truss to invent dependency syntax, flatten documents or resolve bare identifiers globally. Keep AC1/AC2 native acceptance gated until a concrete available owner representation supplies valid dependency/external-reference and cycle semantics, or the owner resolves the demonstrated requirement conflict. The direction that current UMF is sufficient does not authorize generic new upstream feature work or waiting for CONTRACT-045 implementation. Pure graph fixtures can prove ordering algorithm independently, but cannot prove those input documents are valid or accepted. If upstream rejects a cycle, reconcile the governing requirement rather than silently accepting invalid UMF.

Missing external target is assessed under upstream package validity first; Truss unknown-endpoint policy cannot bypass a required missing dependency rejection. Prior accepted documents require exact revision/digest pins, not newest fallback. Duplicate document identifiers and equal module names across owners must follow the shared qualified-identity contract. Current independent valid documents remain orderable by byte identity.

## Interfaces, Determinism and Limits

CONTRACT-003 owns recorded schema_doc ord and phases. CONTRACT-003 now pins the exact component tie-breaker; valid upstream package/cycle input remains gated. Source bytes/digests remain unchanged by graph ordering. Byte comparison is independent of locale, host sort, Unicode normalization and database collation. Use a bounded nonrecursive graph algorithm or explicit checked work stack; define document/edge limits without silently dropping dependencies. Input permutation cannot affect ids/reports through hidden iteration order.

## Tests and Handoff

STP-002 allocates three criteria. Resolve upstream graph syntax/cycles/qualified pins, define ordering profile, write red pure graph permutation tests and gated native acceptance cases, then implement SCC/phases. Unsupported package semantics refuse without effects. Failed order/derivation rolls back the whole set, not one component at a time. Algorithm evidence and valid package acceptance evidence remain separate.
