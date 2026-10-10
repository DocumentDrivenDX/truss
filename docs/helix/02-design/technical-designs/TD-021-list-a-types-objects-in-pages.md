---
ddx:
  id: TD-021
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-021
      kind: informed_by
    - id: SD-005
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
---

# TD-021: Bounded direct object listing

**Story:** [[US-021]]. **Parent:** [[SD-005]]. **Feature:** FEAT-005.

## Technical Approach

Use fixed type/ID keyset access with validated positive limit and one-row lookahead in the same read context. Return at most the requested limit and a continuation only when lookahead proves more eligible rows. Storage ID order is distinct from Weft authored-key ordering; no compiler logic is introduced here. Require the limit and enforce the explicit deployment maximum before execution.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/reads/page-request.ts` | Required limit/max validation and typed cursor context checks | US-021-AC2, US-021-AC3 |
| `packages/postgresql/src/reads/list.ts` | Type-filtered ID keyset template, lookahead and exact decoding | US-021-AC1 |
| `tests/reads/list.test.ts` | Native pages and contract refusal cases | US-021-AC1, US-021-AC2, US-021-AC3 |
| `tests/benchmarks/type-listing.ts` | Controlled 10/1,000-type page-cost comparison | US-021-AC4 |

All runtime components are new. Reuse exact record decoding rather than separate JSON conversion.

## API/Interface Design

CONTRACT-004 owns list_objects; CONTRACT-001 owns fixed index; CONTRACT-007 owns read context. CONTRACT-004 now specifies continuation context, live versus fixed snapshot behavior and lookahead. Closed request/cursor/result wires are authored, and the direct-page finite resource candidate supplies proposed named limits. Native profile/resource adoption remains a publication gate. Reject mismatched type/profile/role context rather than reinterpreting an old marker. Do not infer this API's maximum from Weft dialect bounds.

## Data Model and Integration

No DDL. Use `(type_id,id)` index and immutable storage IDs; parameterize type and lower-bound ID. Lookahead and payload read must share a consistent snapshot. Across separate READ COMMITTED pages, creations/deletions can change observed membership; a cursor alone is not a frozen snapshot. A host-maintained consistent snapshot supports stronger paging guarantees and must be reported explicitly.

## Security and Performance

Apply identical qualified role policy to page and lookahead, avoiding hidden-row existence leaks. Context changes require refusal/restart according to the shared policy. Deployment max bounds returned rows, not arbitrary value-byte cost; value resource limits remain separately qualified. AC4 holds query shape, small-type size and server/settings constant while changing type-count metadata; record full cost distributions and plans.

## Testing

STP-021 allocates four criteria. Independently expect 50/50/20 for 120 ordered IDs, plus empty/exact-limit/lookahead boundaries. Record IDs beyond host-number precision. Supplement concurrency with objects present throughout traversal and separately qualified snapshot behavior. Benchmark statistic/sampling and resource bounds must be explicit before claiming the 2× threshold.

## Migration and Rollback

No schema migration. Changed cursor semantics get a new profile/version; incompatible cursors refuse. Failed reads advance no durable consumer state. Keep prior qualified package/profile, without translating storage-ID cursors into authored-key cursors.

## Implementation Sequence

1. Admit the authored shared cursor/resource/context proposals, settle remaining native profiles and create red page/refusal cases.
2. Implement pure validation and fixed keyset/lookahead read.
3. Qualify concurrency/role/context boundaries and native plans.
4. Run preregistered scale benchmark before performance claim.

## Risks and Gates

Cursor role/context lifetime and catalog changes require explicit policy. Late committed reserved IDs need careful continuously-existing-object versus new-object classification. No multi-page snapshot claim follows from ORDER BY. Performance target is required evidence, not assumed from index existence. Broader source querying remains Weft-owned.

Direct page result uses the [closed result wire](../contracts/direct-page-result-v0.1.schema.json) under CONTRACT-004. Decode complete current-record wrappers, validate current revision/selection/order and full n+1 observation, then disclose atomically. End has no cursor; more uses the last returned row and requires a nonempty page plus observed lookahead. Invalid/unavailable expose no partial page; executor failure retains CONTRACT-007 handling. Resource and native observation profiles remain required implementation prerequisites.

### Concrete observation and decoder handoff

CONTRACT-004 now authors direct-page-observation-v0.1.proposal.sql, fixed column-to-record correspondence and direct-page-resource-v0.1.candidate.json. list.ts handles object selection; shared pages.ts owns fixed statement/slot binding, and decode-record.ts owns category-specific exact native projection. Avoid parallel query/decoder implementations in these planned files. SQL source survives pinned UMF archive/reload/export, while complete query extraction and native execution remain unqualified. Current-authority coordinator admission consumes CONTRACT-005's existing guard/adoption protocol and cross-connection wait matrix; no second authority profile or hidden caller commit.
