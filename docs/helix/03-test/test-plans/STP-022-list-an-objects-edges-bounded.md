---
ddx:
  id: STP-022
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-022
      kind: informed_by
    - id: TD-022
      kind: informed_by
    - id: SD-005
      kind: informed_by
---

# STP-022: Bounded edge listing

## Story Reference

US-022, TD-022, SD-005, TP-001 and CONTRACT-001/004/007. Tests are planned.

## Scope and Objective

Prove bounded direct endpoint listing and qualified relationship order without conflating related-key compilation.

Native predicate qualification targets CONTRACT-004's direct-page-observation-v0.1.proposal.sql, which is currently unexecuted source design. Independently expect tied non-null keys, a transition from the last non-null key into null keys, null-key continuation, terminal lookahead and a self-loop under both direction. Include a signed legacy relationship/type ID and a different object type with the same numeric object ID. Hidden rows cannot supply has_more. Reject nullable/malformed native slot combinations before submission rather than returning a valid empty page. Observe exact C ordering and original snapshot/current policy composition; an EXPLAIN or source inspection alone does not establish these behaviors or resource bounds.

## Acceptance Criteria Test Mapping

Resource controls use the unadopted direct-page-resource candidate: an oversized lookahead row, aggregate native bytes exceeding the bound despite a small public projection, UTF-8/escaping expansion, decoder copies and owner-inventory overflow withhold the whole result. Count the extra row and all original call work; LIMIT cannot qualify native scan/sort/memory bounds. A materializing driver lacking preallocation/framing guarantees is unavailable before claiming this resource profile. Independently fault containment and require original recovery rather than resource-unavailable. A smaller later caller request is a new explicit call, not an automatic shortened page or hidden retry.

Current-authority coordinator/guard schedules from CONTRACT-005 stage a complete held-snapshot page, revoke a relevant declaring/endpoint permission before fresh lease acquisition and require no page/cursor/lookahead disclosure. A revoke racing an already admitted shared lease follows its independently observed publication ordering; no mixed-policy partial page is returned. Test stale authority contexts, a different caller on the fresh connection, lease loss during decoding/publication, uncoordinated role/policy DDL and failure to close the authority context. Original caller data transaction/snapshot survives qualified lease cleanup; uncertain lease termination retains original recovery. Add a waiting catalog administrator before fresh coordinator admission and prove no coordinator head reacquisition behind it. Policy/helper DDL that conflicts with caller-held relation locks defers before the conflicting lock set unless original context drain is independently established; caller transaction termination remains host-owned. This candidate needs selected native bodies/guard/coordinator/profile evidence before support.

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-022-AC1 | `edge_page_has_exact_bound_and_more` | 250 eligible edges return exactly 100 and a valid continuation; final page has none | `@covers US-022-AC1` | Native integration | `tests/reads/edges.test.ts`; independent ID fixture |
| US-022-AC2 | `ordered_edges_put_unset_last` | Set keys follow qualified comparator; ties use stable ID; unset keys follow all set keys | `@covers US-022-AC2` | Native integration | Same file; tied/Unicode/boundary order fixture |
| US-022-AC3 | `direction_filters_authored_endpoints` | In/out returns only respective typed endpoints, including self-edge once per requested direction | `@covers US-022-AC3` | Native integration | Same file; mixed-direction and wrong-type fixtures |

## Executable Proof

Future command `bun test tests/reads/edges.test.ts` requires harness/files. Tests cite IDs and pin ordering/cursor/role/server/adapter profiles. Unsupported order variants remain unverified/refused.

## Data and Setup

Expected edge order is authored independently of production comparator. Observe complete relation/source/target metadata and exact values. Lookahead uses identical role/context filters. Empty and exact-limit boundaries expose off-by-one errors.

## Edge Cases and Failure Modes

Relationship-filter binding vectors normalize reordered equivalent qualified filter sets, reject duplicate/ambiguous pins and changing direction/object/filter on continuation, and verify empty all-incident selection still applies every relationship/endpoint policy. Swap a catalog relationship reference for a stored record identity and require invalid selection. Lookahead obeys the same policy/snapshot and does not leak a hidden edge. Mutable live ordering remains explicitly distinct from held-snapshot completeness.

Deleted edges between pages do not repeat stable-order survivors. Order-key mutation, mixed relationships and null/unset states require finalized context policy. Hidden endpoints/edges cannot leak through continuation. Wrong cursor direction/type/profile refuses. No authored target-key ordering or undirected support is inferred.

## Build Handoff

Resolve ordering/cursor gates, write red fixtures, implement direct reads and qualify visibility/continuation. All three criteria block story closeout. No frozen multi-page state follows from a cursor alone.

## Filter normalization supplements

Independently order qualified references by per-field unsigned UTF-8, including equal prefixes, non-ASCII scalars and numeric-looking IDs. Reversed unique input yields the same normalized filter/cursor admission. Exact duplicates and repeated relationship IDs with different pins/owners refuse, without selecting the first/last occurrence. A changed owning document or definition cannot resume under a same-name relationship. Verify complete selection comparison despite a forced equal digest; filter normalization never changes native edge result order.

## Mixed relationship ordering witnesses

Mix ordered/unordered relationship references in one filter, with non-null a/b keys and null positions. Expect the same global key/null/id sequence regardless of relationship metadata or filter input order. All-null fixtures reduce to immutable ID ordering. A retained non-null key on an unordered relationship is not discarded or sorted under another algorithm. Repeat across page boundaries and both directions; incompatible future comparator profiles refuse old cursors.

## Independent continuation vectors

Use immutable edge ids as exact decimal strings and this independently authored order under the selected C comparator: `(a,10)`, `(a,20)`, `(b,5)`, `(NULL,7)`, `(NULL,30)`. NULL here is the native order_key state, not the text string "NULL". With limit 2 and one held repeatable-read snapshot:

| Request | Expected returned ids | has_more | next_after |
| --- | --- | --- | --- |
| First page | 10,20 | true | (a,20) |
| After (a,20) | 5,7 | true | (NULL,7) |
| After (NULL,7) | 30 | false | absent |
| After (b,5), limit 2 | 7,30 | false | absent |
| After (NULL,30) | empty | false | absent |

Remove a hidden edge between 20 and 5 from the authorized fixture: its presence must not change any visible boundary/lookahead verdict. A mismatched direction/relationship/endpoint/profile context refuses, even if its raw boundary values happen to exist. Repeat the fixture with ids beyond host-number precision to detect numeric coercion.

For live READ COMMITTED mode, moving edge 30 from NULL to a before a prior (NULL,7) boundary may omit it; this is the explicitly declared live-order behavior, not a frozen membership pass. Held-snapshot repetition must retain the original order despite concurrent mutation. These vectors support US-022-AC1/AC2 and are planned semantic expectations, not executed native evidence.

Direct page result wire witnesses: run `bun docs/helix/04-build/evidence/design-audit/check-direct-page-result.ts <Ajv Draft 2020-12 module path>`. Eighteen independent cases cover closed success/failure variants, exact current-record wrappers, missing/stray cursors and prohibited partial failure disclosure. Wrong current revision, duplicate membership, empty-more, cursor advanced past lookahead and forged scope deliberately pass shape validation and require semantic/native refusal. Native schedules must assert unchanged snapshot/authority and no callback/log disclosure before whole-page admission; these shape cases do not execute those schedules.


Ordering-domain controls independently seed signed catalog IDs whose decimal text order differs from native numeric order, positive graph IDs and business-key values with a different authored sort. Direct object and edge pages retain their declared storage/order_key order; compiled business queries retain typed authored component order. Reject out-of-range/aliased catalog input before query and do not substitute a key discriminator for component comparison. Retained cursor/stage continuation across a namespace migration requires original valid context/binding; no reset or lexical reinterpretation repairs a stale cursor. Native schedules remain planned.


D0–D7 planned page controls inject a malformed, unauthorized-owner, out-of-order or oversized lookahead after independently valid requested records. No prefix, end page or cursor may publish. Truncated native completion after zero/limit rows also refuses. Validate all observed identities and exact selected order before current-authority closure, then race cancellation/disposal/authority expiration against D7 with independently observed zero publication. Charge lookahead, parser state, native candidates and full serialized output concurrently; no public-size limit may erase native work or allocation. Run through the actual selected transport/coordinator producers before qualification.
