---
ddx:
  id: STP-036
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-036
      kind: informed_by
    - id: TD-036
      kind: informed_by
    - id: SD-001
      kind: informed_by
---

# STP-036: Catalog acceptance origin

## Story Reference and Scope

US-036, TD-036, SD-001, TP-001 and CONTRACT-002/003/007. Tests are planned. Prove stored accepted-origin atomicity and database-derived role.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-036-AC1 | `accepted_revision_returns_actor_role_reason` | Authorized lookup returns actor a, actual role w, reason and qualified extension facts on accepted revision | `@covers US-036-AC1` | Native integration | `tests/catalog/origin.test.ts`; accepted revision under explicit role |
| US-036-AC2 | `caller_role_spoof_cannot_replace_database_role` | Forged db_role is ignored; trusted acting role survives qualified definer execution | `@covers US-036-AC2` | Native integration | Same file; distinct caller/owner/forged roles |
| US-036-AC3 | `rejected_acceptance_has_no_origin_row` | Rejected set produces no schema_rev/origin/head/catalog/data/journal changes | `@covers US-036-AC3` | Native integration | Same file; violation and late-failure fixtures |
| US-036-AC4 | `native_revision_origin_shape_guard_refuses_nonobjects` | Direct native insertion of array/scalar/SQL NULL origin fails constraint with no persisted row | `@covers US-036-AC4` | Native integration | Same file; disposable qualified insert principal |

## Data and Additional Probes

Independent native observer reads origin and catalog head. Include absent actor, x-* content, equal-byte no-change acceptance retaining original origin, concurrent acceptance and caller rollback. Verify ordinary caller cannot rewrite accepted origin under the declared privilege profile. Choose a principal able to reach the shape CHECK so privilege refusal alone cannot satisfy AC4; assert constraint identity/SQLSTATE and confirm an object-valued control insertion reaches the same path.

## Executable Proof and Handoff

Future command `bun test tests/catalog/origin.test.ts` requires shared origin mechanism, shape constraint and authorization policy. Record role/definer/search-path/server/adapter configuration plus independent before/after effects. All criteria block closeout. Host-supplied actor is not authenticated by storage fidelity.


## Original asserted origin and journal-mapping correspondence

Independently author acceptance origin containing exact tagged numeric text, nested empty arrays/objects, absent actor and a literal string resembling a value tag. Run through the selected AcceptanceAttemptContext canonical-tree input and qualified journal-origin mapping; compare both original representations and native caller capture independently. Do not feed the assertion directly into an ExactValue codec or replace tag-looking strings with interpreted values. Missing/incompatible mapping refuses before new acceptance effects, while actor/extension text never authorizes a caller.

After confirmed acceptance under original actor A, submit the same complete acceptance input at that head through an independently authorized actor B. Exact repeat preserves A’s complete original report/origin/capture/mapping bytes and performs no new attribution or journal effects; current B authority remains required for disclosure. Revoke B before publication and require the security-owned protocol to withhold the result, without rewriting A’s report. Separately hold new acceptance pending in an adopted host transaction: its original scope may observe pending attribution, but no committed revision/origin claim is published before host settlement. Lose settlement acknowledgment and retain original recovery instead of using a later actor’s attempt to reconstruct or overwrite provenance. These are planned native/host controls, not qualified mapping or security evidence.
