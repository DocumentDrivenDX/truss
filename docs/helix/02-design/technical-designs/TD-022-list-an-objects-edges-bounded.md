---
ddx:
  id: TD-022
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-022
      kind: informed_by
    - id: SD-005
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
---

# TD-022: Bounded edge listing

**Story:** [[US-022]]. **Parent:** [[SD-005]]. **Feature:** FEAT-005.

## Technical Approach

Use direct typed-endpoint access and bounded lookahead. Outgoing selection matches the authored source tuple; incoming matches target tuple. All selected edges use CONTRACT-004's single qualified order-key comparator, unset last and immutable edge-ID tie breaker. A selection whose edges all have unset keys therefore orders by edge ID. Relationship ordered/unordered metadata does not switch the cursor comparator or silently erase a retained non-null order key; mixed selections preserve the same total order. Complete cursor order must match the selected query rather than reusing object-list cursors.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/reads/edge-page.ts` | Validate direction, limits and complete order cursor | US-022-AC1, US-022-AC2, US-022-AC3 |
| `packages/postgresql/src/reads/edges.ts` | Endpoint filters, qualified ordering, lookahead and exact edge decoding | US-022-AC1, US-022-AC2, US-022-AC3 |
| `tests/reads/edges.test.ts` | Native bounds/order/direction and continuation cases | All criteria |

New components reuse codecs/read context. This direct operation is not Weft's related-key compiler.

## API/Interface Design

CONTRACT-004 owns list_edges; CONTRACT-001 owns edge/order representation; CONTRACT-007 owns context. Shared contract authors mixed relationship ordering, tie-breakers, C/null-state comparison and live versus held continuation; exact native context/comparator adoption remains required before publication. This TD does not author a new cursor payload.

## Data Model and Integration

No DDL. Typed endpoint filters prevent wrong-type ID matches. Edge payload preserves relation and both endpoint identities. Lookahead has the same role filters/order/snapshot as returned rows. Inverse display names cannot reverse the stored authored relationship identity silently. Self-edges belong to each explicitly requested direction once, not double-counted within one direction.

## Security and Performance

Require endpoint/relationship visibility under the qualified policy. Hidden edges must not leak through has-more. Parameterize endpoint and cursor values. Use qualified source/target indexes and record sorting cost for ordered/mixed queries. Deployment limits bound rows; value-byte limits remain separate. No target-key ordering claim follows from order-key or edge-ID order.

## Testing

STP-022 owns criteria. Include 250 edges, tied/set/unset order keys, opposite directions, self-edge and hidden endpoints. Independent fixture order exposes collation and null-order errors. Deleting edges between pages must not repeat surviving stable-order edges; mutable order-key updates need explicit snapshot/continuation policy, not a blanket no-repeat claim.

## Migration and Rollback

No schema migration. Changed comparator/cursor semantics require explicit profile/version and refusal of incompatible continuation. Read failure changes no state. Preserve prior qualified comparator instead of silently normalizing stored order keys.

## Implementation Sequence

1. Admit the authored ordering/cursor/resource proposals and create independent red native fixtures under the selected remaining profiles.
2. Implement pure request validation and endpoint/order templates.
3. Qualify role, self-edge, deletion and snapshot continuation behavior.

## Risks and Gates

CONTRACT-004 now pins C comparison, NULL-last key/id ordering, mixed filtered-list ordering and live/snapshot continuation. The draft structured cursor schema and declaration now represent null/empty-text positions explicitly; semantic/native profile review remains. External opaque transport belongs to a selected host integration, not the in-process paging API. A mutable order key can move an edge across a cursor under separate snapshots; stable guarantee needs a qualified context. Broader UMF undirected/association variants must be mapped explicitly or refused, not collapsed into this directed subset.

Direct page result uses the [closed result wire](../contracts/direct-page-result-v0.1.schema.json) under CONTRACT-004. Decode complete current-record wrappers, validate current revision/selection/order and full n+1 observation, then disclose atomically. End has no cursor; more uses the last returned row and requires a nonempty page plus observed lookahead. Invalid/unavailable expose no partial page; executor failure retains CONTRACT-007 handling. Resource and native observation profiles remain required implementation prerequisites.

### Concrete observation and decoder handoff

CONTRACT-004's direct-page-observation-v0.1.proposal.sql uses one incident predicate, preserving one row for a both-direction self-loop, complete signed native relationship filters and exclusive non-null/null continuations. edges.ts handles selection; shared pages.ts binds its exact admitted slots and decode-record.ts preserves relationship/endpoints, metadata and value/definition correspondence. The named direct-page resource candidate charges native and public bytes separately, including lookahead, all owner/decoder work and containment. CON-TRACT-005's existing coordinator wait matrix governs fresh authority publication under held snapshots. Source round-trip evidence is not native predicate/parameter/policy/resource qualification.
