---
ddx:
  id: STP-023
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-023
      kind: informed_by
    - id: TD-023
      kind: informed_by
    - id: SD-005
      kind: informed_by
---

# STP-023: Bounded traversal qualification

## Story Reference

US-023, TD-023, SD-005 and TP-001. Exact traversal contract/baseline definition is a prerequisite; tests are planned.

## Scope and Objective

Prove native semantic equivalence before qualifying one-to-three-hop performance and metadata-scale planning.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-023-AC1 | `one_hop_p95_matches_baseline_ratio` | Equivalent one-hop results and Truss p95 at most 2× independent hand-designed baseline | `@covers US-023-AC1` | Native performance integration | `tests/benchmarks/traversal.ts`; pinned corpus/selectivity/limits |
| US-023-AC2 | `two_three_hop_p95_matches_baseline_ratio` | Equivalent two/three-hop results, each p95 at most 2× respective baseline | `@covers US-023-AC2` | Native performance integration | Same file; filtered and high-degree corpus strata |
| US-023-AC3 | `type_count_traversal_planning_ratio` | Equivalent one-hop planning at 1,000 types within 2× 10-type metadata baseline | `@covers US-023-AC3` | Native performance integration | Same file; data/query/settings held constant |

## Executable Proof

Future commands `bun test tests/reads/traversal.test.ts` and `bun tests/benchmarks/traversal.ts` require harness/files and finalized semantics. Each benchmark cites its criterion and retains raw samples, p95/statistic policy and exact native/runtime/profile pins. No retry-to-green or incomparable baseline counts as passing.

## Data and Setup

Preregister AC1/AC2 as separate strata for hop count, direction, selectivity and degree; each required stratum must satisfy its own p95 ratio rather than averaging away a slow case. Baseline returns the same unique typed terminals under Truss's path-local cycle rule and complete work policy. A Weft bag query or baseline with fewer paths is incomparable. AC3 measures planning separately from execution/decoding and changes metadata count only; record native plan timing boundary, repetitions and statistic before running. TP-001 governs uncensored samples, paired order and unavailable denominators. Sample/repeat counts are selected by the [direct traversal experiment](../direct-traversal-experiment.proposal.md); resource limits and original corpus/native registration remain profile selections before qualification.

Independent graph fixtures cover chains, diamonds, cycles, isolated nodes, directions, hidden endpoints and high-degree expansion. Baseline schema/queries are authored separately from Truss templates. Verify returned identities/content/deduplication/completeness before measuring ratios. Include intermediate-work budget observations, not only result row counts.

## Edge Cases and Failure Modes

Stage continuation vectors race two resumes with one expected work version, raise an admitted budget without resetting counters, and replay an identical result cursor without advancing a global offset. Seal results before paging; a later discovery cannot append under the sealed identity. Wrong host/connection, ended snapshot, released generation and changed required grants refuse before payload disclosure. Last-returned typed boundary and n+1 lookahead govern more/end. Cleanup cannot commit/rollback host work or remove another stage. In-memory stage tests cannot qualify cross-process/crash resume.

Traversal-profile vectors include a diamond, the same typed node at different hop positions, paths with different visited sets, self-loop/start-return cycles and opposite directions. Compare unique terminal objects under the declared path-cycle rule; Weft bag results are not deduplicated by this fixture. Exhaust examined-edge/path-state/retained-byte budgets before output paging and require limited/not_established, never a false end or partial complete page. Resume only through qualified staged context/snapshot; expired/wrong-generation handles refuse. Hidden intermediate records cannot leak through counts or detailed work-limit diagnostics.

Resource exhaustion must explicitly refuse or return contract-qualified truncation; silent lost paths fail correctness. Snapshot/context changes, unsupported relationship variants and cursor visited-state gaps require explicit policy. Object deduplication is direct traversal semantics and cannot change Weft bag query results.

## Build Handoff

Weft e810335 adds a committed draft for two-hop occurrence bags and grouped
counts, as reviewed in TD-023. It supplies no executed compiler/native evidence
for this plan. Independent interoperability controls must distinguish six paths
from one terminal for parallel 2×3 edges, and distinguish legal draft self-loop
and forward/inverse return paths from the direct candidate's cycle exclusions.
Verify full document/type/revision continuity when equal local IDs occur across
scopes. Preserve complete path/count capacity before HAVING or outer LIMIT,
ordered-prefix/lookahead correctness, and absent-root versus present-empty
results under original authorization and cleanup. Run these against an actual
future admitted PostgreSQL path realization separately from direct traversal.
No compiled bag is deduplicated or filtered by host SQL to pass US-023; one-hop,
three-hop, stage continuation and performance exits remain independently required.
All new interoperability controls are `not_run`.

Finalize traversal contract, independently define corpus/baseline and sampling, implement red correctness tests, then native templates/benchmarks. All three criteria plus correctness/resource prerequisites block closeout. Performance-only success cannot qualify semantic support.

Traversal wire check: `bun docs/helix/04-build/evidence/design-audit/check-direct-traversal.ts <Ajv Draft 2020-12 module path>` passes 24 shape witnesses. Native schedules must independently reject forged/stale stage custody, smaller-than-consumed bounds, conflicting expected work versions, expired snapshots, wrong full query despite matching digest and empty-more; these intentionally cannot be established by schema. Verify path-local cycles and terminal dedup using independent graphs, no partial frontier disclosure on limits, stable replayed sealed pages and host transaction ownership during cleanup. Stage-release ABI is authored; host/native resource profile remains pending; no shape pass qualifies resumability.

Release/error wire corpus now passes 35 cases; strict consumer controls reject rollback options, empty unresolved recovery and invalid-with-records. Required host schedules: release racing resume/seal/page; release after snapshot end/disposal/revocation; wrong original registry/generation; lost cleanup reply; partial deletion then crash; idempotent completion tombstone; missing registry versus unknown cleanup; attempted generation reuse. Independently verify no post-invalidation disclosure or state resurrection, original recovery registration before cleanup, confirmed quiescence/deletion before released, and unchanged host transaction/services/graph/feed. Shape-valid forged recovery is a semantic refusal. These schedules remain planned, not executed evidence.

Reference-resource schedules use the exact original candidate artifact and independently counted path graphs. Test each boundary at limit and limit+1; repeated edge encounters, cycle rejection and terminal dedup still consume work. Race stage reservations so aggregate 32-stage/256-MiB limits cannot oversubscribe; unresolved deletion retains charge. Compare actual allocator/copy/index overhead against conservative byte accounting. Resume after near-limit work without counter/time reset; in-flight native wait counts as active time, stopped staged time does not. Exhaust decoding before disclosure: unavailable/resource with unchanged sealed-page boundary. Active-work exhaustion: limited/active_work after confirmed containment; lost containment retains original quarantine. Hidden physical scan/driver-buffer limits require their own evidence. Wire corpus now has 37 cases; these resource schedules remain planned.

Host-service strict consumer checks reject public-handle leases, forged registrations, group selection, resume without adopted transaction/request and empty unresolved custody. Planned independent service probes count zero callbacks/SQL/allocations during registration; reject duplicate/replacement issuer and affinity/profile mismatches. Race publication/reservation and seal/release; force exception after allocation before admission reply, conflict after native work, publication acknowledgment loss and closure uncertainty. Verify pre-effect original recovery registration, actual pending allocation charges, old lease invalidation, exact version+1, immutable query/sealed membership and no success/disclosure after uncertainty. No structural check qualifies private-state/evidence codecs or store atomicity.

Run `bun docs/helix/04-build/evidence/design-audit/check-traversal-private-state.ts <Ajv Draft 2020-12 module path>`: fifteen private codec shape cases pass. Wrong hop/path repetition, forged sealed terminals and reset counters deliberately require semantic/native refusal. Independent frontier schedules crash between scan advance and enqueue, discard prefetched edges, resume after a chunk exactly at its limit, exercise both-direction self/parallel edges and converge diamond paths. Assert no lost edge/terminal, path-local cycle semantics, complete exhaustion before seal, unchanged full query and independently ordered terminal membership. Repeated real work after failed publication remains charged; it cannot reset cumulative budget merely because the checkpoint rolled back. Saved state is host-private; no test exposes it through public results.

Resource-ledger races: reserve competing last-capacity permits; fail publication after confirmed work; lose reservation/settlement reply; repeat original settlement; supply stale accounting versus current frontier version; exceed reserved work; attempt seal/release with unsettled permit. Independently assert failed work remains charged across resume, uncertainty never refunds capacity, original successful settlement counts once, actual excess is preserved rather than clamped, and original permits cannot be fabricated from public handles/leases. Strict consumer checks reject lease-as-work-permit and unavailable-with-permit. These are declaration checks and planned schedules, not physical enforcement evidence.

Private ledger shape command: `bun docs/helix/04-build/evidence/design-audit/check-traversal-resource-ledger.ts <Ajv Draft 2020-12 module path>`. Twelve cases pass. Native/host admission must reject shape-valid duplicate permits, incorrect outstanding totals, actual work above reserved maxima, unbacked byte refunds and forged completion. Independently compute initial+settled and reserved-only sums; omit an issuer-known outstanding permit despite internally consistent totals and require refusal. Fill tombstone storage to capacity and assert new work refuses without loss of idempotency custody. No schema proves physical bytes, registry completeness or atomic settlement.

Run `bun docs/helix/04-build/evidence/design-audit/check-traversal-canonical.ts <Ajv Draft 2020-12 module path>` for three published canonical tree/preimage/hash witnesses and wrong-domain controls. Add independent production/browser cases for duplicate JSON members, invalid UTF-8/unpaired surrogates, noncanonical escapes/whitespace, ordered frontier/terminal/permit arrays, Unicode preservation, query-digest versus raw-artifact digest substitution and unknown semantic fields. The current verifier checks correspondence and hashing, not independent complete canonical spelling or raw parser behavior.

Two-version publication races: prepare a candidate, advance the ledger through a separately admitted settlement, then publish under the old accounting version. Require conflict with unchanged checkpoint and preserved real charges. Substitute latest version text without full candidate correspondence, rewind saved accounting cut, or allocate replacement buffers outside reservation: integrity refusal/containment. After confirmed old-buffer deletion, admit a sealed page using unchanged terminal membership and reconciled newer ledger. Private-state corpus now has 17 cases; three canonical vectors and strict declarations pass after the new field. No shape/type pass establishes atomic host store behavior.

Publication shape command: `bun docs/helix/04-build/evidence/design-audit/check-traversal-publication.ts <Ajv Draft 2020-12 module path>` passes nine cases. Native/host probes must reject unchanged version, substituted state/ledger and forged store observation; lose reply after replacement and reconcile exact original attempt once, then distinguish a new same-bytes attempt. Forbid stored before actual replacement confirmation and prohibit publication proof from becoming graph commit, membership completeness or cleanup permission. Shape-valid observation remains unqualified without original issuer/native producer.

Reference-store fault schedules instrument every allocation/validation before root replacement and reply preparation after it. Before replacement, original root remains intact; after replacement, lost reply resolves original confirmed attempt once. Inject callback reentrancy outside the critical section, stale root/state/ledger generation, concurrent reserve/publish/invalidate, counter exhaustion and attempted issuer/generation reuse. Assert zero await/native/caller callback inside critical sections; separate active workers stay tracked before effects. Abrupt process loss cannot claim released or resume the old snapshot. Actual physical memory/copy bounds remain independent qualification.

Run `bun docs/helix/04-build/evidence/design-audit/check-traversal-store-observation.ts <Ajv Draft 2020-12 module path>`: nine metadata shape cases pass. Required host probes independently compare actual predecessor/replacement root and exact version+1; wrong original service/generation/attempt and copied records must fail custody. Observe a confirmed old publication after a newer publication and after stage release: historical replacement may reconcile, but no lease/current disclosure results. Lose original process registry and require unavailable; no restart from copied bytes. Recovery observation performs no new publication or data transaction control.

Work-completion shape command: `bun docs/helix/04-build/evidence/design-audit/check-traversal-work-completion.ts <Ajv Draft 2020-12 module path>` passes nine cases. Independent schedules substitute original permit/worker, forge termination, omit clock span, lose native termination reply, publish failure after actual work and claim zero usage. Require retained charge/recovery until original actual termination/usage/time is established; no future settlement/cleanup claim or public private-state disclosure. Selected producer/clock/physical profiles remain unqualified.

Cleanup metadata command: `bun docs/helix/04-build/evidence/design-audit/check-traversal-cleanup.ts <Ajv Draft 2020-12 module path>` passes nine cases. Independent host/native probes keep old root, callback buffer or unresolved permit reachable during release and require unresolved charged custody; retain minimal tombstone without retaining state payload. Omit a generation-owned resource and require complete-inventory refusal. Verify retained metadata charge and stage-slot accounting; distinguish logical reference deletion from measured allocator/RSS reclamation. No explicit or implicit host transaction/service close is permitted. Selected producer/accounting/retention profiles remain open.

Independent mathematical ledger witnesses: `bun docs/helix/04-build/evidence/design-audit/check-traversal-ledger-arithmetic.ts` passes seven cases using exact integer arithmetic and independently specified totals. Cases preserve the initial path charge, retain outstanding maxima after lost reply, reject duplicate settlement and actual above reservation, and charge fresh work after failed checkpoint. The audit helper is not production accounting and has no store/issuer/physical evidence. Pair these witnesses with original issuer inventory probes: an internally consistent ledger missing an outstanding registered permit still refuses.


## Independent path-local cycle and terminal-dedup oracle

The [six-edge logical fixture](../reference-traversal-path-cycle.proposal.json) concretizes the proposed unique-terminal semantics while owner choice remains pending. All edges use the same admitted relationship/direction and all objects are independently authorized in one qualified snapshot. One hop from a returns b/c; two hops returns d once despite two valid paths; three hops returns b through a→c→d→b while rejecting a→b→d→b. The a→a self-loop is excluded at every expansion because a already occurs in that candidate path. A global visited-node set that remembers b from the first hop would incorrectly discard the valid three-hop result. Distinct path states reaching d must therefore remain distinct until expansion, although d appears only once in the two-hop terminal result.

The native harness assigns actual typed IDs and compares complete observed identity/record membership independently; fixture aliases are not allocator predictions or a compiler mapping. Count both diamond paths and rejected-cycle work under the original resource profile even when terminal output deduplicates. Withhold output until complete bounded membership is established. A hand-designed benchmark must implement these same meanings; a Weft query returning two d rows is a different bag result and is not silently rewritten. Selection of path-valued traversal would require revising this proposed oracle and governing profile before qualification. The fixture is authored expected data only; all native cases remain not_run.
