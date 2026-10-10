---
ddx:
  id: STP-021
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-021
      kind: informed_by
    - id: TD-021
      kind: informed_by
    - id: SD-005
      kind: informed_by
---

# STP-021: Bounded direct listing

## Story Reference

US-021, TD-021, SD-005, TP-001 and CONTRACT-001/004/007. Tests are planned.

## Scope and Objective

Prove direct type/ID paging, explicit request bounds and qualified type-count performance without conflating Weft key order.

## Acceptance Criteria Test Mapping

Native projection controls use the direct-page observation and decoder handoff in CONTRACT-004. Independently compare complete props/retained/ownership and row-written versus read catalog revisions after definition-only acceptance. Include native timestamp precision beyond milliseconds, signed catalog/property IDs, literal tag-looking strings, null versus absent values and a malformed partial root pair. Missing columns, rounded host values or unknown-property omission fail full-record admission; source provenance is tested through its separate capability rather than injected into a DirectRecord. These controls remain planned native/decoder evidence.

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-021-AC1 | `three_pages_have_exact_continuations` | 120 Customers produce 50/50/20 exact nonrepeated IDs; only first two continuations indicate more | `@covers US-021-AC1` | Native integration | `tests/reads/list.test.ts`; independently ordered IDs and one read-context profile |
| US-021-AC2 | `missing_limit_refuses` | Omitted limit yields defined refusal before execution | `@covers US-021-AC2` | Contract | Same file; pure request fixture |
| US-021-AC3 | `deployment_max_is_enforced` | Above-max limit refuses without clamping or unbounded query | `@covers US-021-AC3` | Contract | Same file; pinned explicit max and boundary requests |
| US-021-AC4 | `type_count_page_cost_ratio` | Controlled small-type page cost at 1,000 types remains within 2× the 10-type baseline | `@covers US-021-AC4` | Native performance integration | `tests/benchmarks/type-listing.ts`; preregistered sampling/statistic |

## Executable Proof

Future commands `bun test tests/reads/list.test.ts` and `bun tests/benchmarks/type-listing.ts` require harness/files. Actual tests cite IDs and pin server/adapter/index/role/cursor/limit profiles. Benchmarks retain raw distributions; no retry-to-green.

## Data and Setup

For AC4 register the exact cost statistic before execution; the 2× ratio alone does not define public-call elapsed time versus native execution time. The [reference experiment candidate](../type-page-cost-experiment.proposal.md) authors public-call p95 including lookahead/decoding, three complete paired blocks and an exact integer ratio decision. Adopt its exact registered environment/profile before execution; the candidate itself is not performance support. Keep selected-type row count, payload bytes, visible role scope, page limit/cursor position, data snapshot, index/statistics and query text constant while metadata grows from 10 to 1,000 types. Compare complete expected pages before accepting a ratio. TP-001 governs raw paired samples and zero/invalid baseline refusal; an unselected cost statistic cannot produce a qualification pass.

Use independent expected ID lists, including exact large IDs. Empty type, exact-limit page and limit-plus-one distinguish lookahead errors. Compare payload decoding to committed fixture values. Hold small-type size/data distribution/query/settings constant in the benchmark; vary metadata type count only.

## Edge Cases and Failure Modes

Direct-page binding vectors change limit within the allowed bound while preserving selection/context, validate n+1 lookahead cursor at the last returned row, and reject mismatched catalog/profile/scope or invalid snapshot handle. A copied expired/wrong-connection snapshot identity cannot reopen a transaction. More requires actual authorized lookahead; end has no cursor. Current carrier shape does not qualify historical reconstruction. Ordinary authority is re-established independently of cursor integrity.

Zero/negative/malformed limits and mismatched type/profile/role cursor refuse under finalized policy. Concurrent inserts/deletes are tested separately from a consistent host snapshot; continuously-existing eligible objects must not repeat/skip. Hidden rows do not affect visible has-more leakage. Late committed ID reservations are new visibility, not proof of a frozen cursor.

## Structured cursor shape evidence

Run `bun docs/helix/04-build/evidence/design-audit/check-direct-cursor.ts <installed-Ajv-2020-module-path>` from the repository root. Twelve cursor and nine request shape witnesses cover closed members, edge null/empty-text distinction and held-snapshot handle requirements. Forged scope and unsupported identity are shape-valid controls requiring separate semantic refusal; the schema never grants authority or certifies liveness.

## Build Handoff

Admission-result witnesses distinguish an authorized empty/end page from invalid request, unavailable snapshot/profile/observation and selected resource exhaustion. Exceed decoding bytes on a returned row or scan budget before n+1 establishment: emit unavailable/resource with no page, records or cursor. Do not advance past the undisclosed row or reduce the admitted limit. Native failure/cancellation remains an execution failure, never empty/end. Permitted malformed-cursor diagnostics cannot expose hidden existence or authority details. Independently check that successful more uses the last returned boundary and retains the real lookahead row for the next page.

Finalize shared cursor/limit policy, write red cases, implement fixed read/lookahead and qualify concurrency/benchmark matrix. All four criteria block complete profile closeout. No authored-key or arbitrary SQL paging support is inferred.

Direct page result wire witnesses: run `bun docs/helix/04-build/evidence/design-audit/check-direct-page-result.ts <Ajv Draft 2020-12 module path>`. Eighteen independent cases cover closed success/failure variants, exact current-record wrappers, missing/stray cursors and prohibited partial failure disclosure. Wrong current revision, duplicate membership, empty-more, cursor advanced past lookahead and forged scope deliberately pass shape validation and require semantic/native refusal. Native schedules must assert unchanged snapshot/authority and no callback/log disclosure before whole-page admission; these shape cases do not execute those schedules.


D0–D7 planned page controls inject a malformed, unauthorized-owner, out-of-order or oversized lookahead after independently valid requested records. No prefix, end page or cursor may publish. Truncated native completion after zero/limit rows also refuses. Validate all observed identities and exact selected order before current-authority closure, then race cancellation/disposal/authority expiration against D7 with independently observed zero publication. Charge lookahead, parser state, native candidates and full serialized output concurrently; no public-size limit may erase native work or allocation. Run through the actual selected transport/coordinator producers before qualification.
