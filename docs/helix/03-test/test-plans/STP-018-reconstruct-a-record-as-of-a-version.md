---
ddx:
  id: STP-018
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-018
      kind: informed_by
    - id: TD-018
      kind: informed_by
    - id: SD-004
      kind: informed_by
---

# STP-018: Version-qualified reconstruction

## Selected decision handoff — 2026-10-07

Planned selected-history controls HSEL-01–03: reconstruct object ownership and edge endpoints/order after deletion without current-row access; independently observe very short/zero local retention with durable archive confirmation before deletion and reconstruct through the admitted archive; remove both local and archive evidence and require explicit unavailable history, never partial success. Consumer/receipt protections and complete mutation/transaction boundaries remain enforced. Cases are not_run.


Planned zero-retention schedules HSEL-04–08 supplement HSEL-01–03 under CONTRACT-006: (04) pause the archive worker across source commit and prove complete local history survives with no uncommitted publication; (05) lose the archive acknowledgment, retry identical original events, reject conflicting payloads and retain local history until qualified durability confirmation; (06) confirm the archive then fail local cleanup, proving reconstructability and safe cleanup retry with fresh protection checks; (07) register a protecting consumer or change the horizon between eligibility observation and deletion, requiring refusal rather than stale approval; (08) fill the selected finite archive backlog during an outage and require atomic write refusal before the bound is exceeded, without deleting protected history or partially committing graph/receipt effects. Thresholds and archive/native profiles must be pinned by the future harness. All cases are not_run.


## Story Reference

US-018, TD-018, SD-004, TP-001 and CONTRACT-002/003/007. Tests are planned, not native reconstruction evidence.

## Scope and Objective

Prove exact record reconstruction and historical interpretation, separating genuinely unwritten versions from unavailable history.

## Acceptance Criteria Test Mapping

Completeness-state probes distinguish a genuinely unwritten version from a trimmed create baseline, a missing middle event, missing historical definition and complete delete boundary. Empty native query output is insufficient for unwritten status. A qualified later checkpoint reconstructs only its declared horizon and cannot certify earlier discarded versions. Compare multi-row-version completion independently; partial rows cannot yield successful state. Hidden-history outcomes obey the same non-disclosure policy before any retained-gap detail is returned. Current canonical values cannot repair missing history.

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-018-AC1 | `version_two_matches_independent_state` | Four-version record reconstructs v2 exactly from create and applicable events, with absence/null retained | `@covers US-018-AC1` | Native integration | `tests/history/reconstruct.test.ts`; independently authored expected states |
| US-018-AC2 | `old_definition_not_current_definition` | Earlier version uses its recorded definition after in-place catalog meaning changes | `@covers US-018-AC2` | Native integration | Same file; qualified old/new definitions and schema_change |
| US-018-AC3 | `unwritten_version_returns_empty` | Proven never-written v9 yields empty history without error; missing retained prerequisites are tested separately | `@covers US-018-AC3` | Native integration | Same file; complete retained history through v4 |

## Executable Proof

Future command `bun test tests/history/reconstruct.test.ts` requires harness/files. Every criterion test cites its ID and pins event/layout/catalog/value/adapter/server versions. Missing definition or baseline evidence blocks support.

## Data and Setup

Add an independently authored definition-only revision fixture: create v1 under definition A, accept definition B with an exact presence-qualified no-op transform, then accept C. Assert no transform event or record-version increment for the no-op, retained `schema_change` evidence for each accepted definition change, and reconstruction of v1 with A's original interpretation pins after both acceptances. A current read identifies C through its separate read-catalog context. Removing A's retained definition must yield history-unavailable rather than falling back to B/C; no version-only reconstruction may imply a selected-catalog reinterpretation. Compare event counts, record versions and interpretation pins independently of the reducer.

Expected states are authored independently of event builder/reducer. Include rebind/transform ordering, unset/null, retained recursive values, edge metadata and deleted record. Compare actual journal/catalog loading to independent fixture inventory before asserting reconstructed output.

## Edge Cases and Failure Modes

Exercise every outcome in the [draft reconstruction binding](../../02-design/contracts/bindings/truss-history-reconstruction-v0.1.d.ts). Reject successful output with a different typed identity/version, a mismatched inventory digest or incomplete multi-row mutation. Proved-unwritten and deleted results carry no record; hidden/not-found carries no request context or completeness diagnosis. An unknown required operation refuses reconstruction before any result is exposed. Preserve unknown origin assertions in archived input rather than silently dropping them. Include an authorized caller and a hidden caller against the same missing baseline to prove that the latter cannot learn the retention gap.

Remove a create row or historical definition in a disposable fixture and require explicit incompleteness after policy is finalized. Unsupported required event kinds cannot be ignored. Role-restricted history must follow the qualified historical authorization policy. Concurrent revision/event reads use one consistent context. Resource overflow refuses rather than returns partial state.

## Build Handoff

Resolve envelope/horizon/deletion/policy gates, write red state fixtures, implement reducer then native loader. All three criteria and incompleteness supplements block closeout. A pure replay pass alone cannot qualify native historical reads.

## Bound history facade supplements

Retain a history facade handle across definition change, archive loss and disposal. Reconstruct with exact original pins: definition change cannot trigger current reinterpretation, archive loss returns history_unavailable and disposed invocation submits no SQL. Native observation/cancellation failure is an outer execution error, not unwritten or not_found. Current-authority checks run even under a caller-held old snapshot.

## Retained archive payload supplements

Admit exact baseline identity/epoch, complete sibling inventory and original definition/owner/retention evidence before reconstruction. Reject shape-valid future horizon without events, wrong baseline identity, event epoch mismatch and conflicting definition bytes. Canonical order must preserve semantic sequence/value spelling while ordering versions/seq exactly. Missing original native evidence stays unavailable; current canonical rows/definitions cannot repair archives. Type/schema probes do not substitute for independent expected reconstructed state.

### Mutation-group metadata correspondence controls

Independently author a baseline and two-property mutation with one full group-start/group-final metadata pair. Place the metadata sibling before, between and after property siblings with independently recomputed original manifests; each admitted producer order uses the same group-boundary interpretation, while property deltas retain their original order. Require full before match, sequential delta-before match and complete staged value versus after membership equality. A later snapshot cannot repair a missing property event, extra retained member, wrong definition/owner, duplicate conflicting transition or changed numeric source token. Matching counts and recomputed digests do not cure these semantic defects.

Refuse multiple ambiguous metadata witnesses, missing non-create/delete snapshot, foreign group-start state, after-version/context mismatch and unsupported metadata field changes. Independently preserve immutable identity/kind/creation meaning and exact original endpoint/order/ownership rules. Include valid metadata-only change, transform/rebind with all source homes checked, and definition-only revision with unchanged recorded interpretation. Oversized simultaneous snapshots, interrupted later group and unavailable original definitions with otherwise matching after images withhold the requested result. These planned tests require the specifically adopted producer interpretation; existing partial rows do not gain complete-history qualification.

### Native capture and rollback schedules

Use independently authored full states S0, S1 and S2. In one caller transaction, perform two successful changes to the same entity: first group's before/after must be S0/S1 and second S1/S2, with distinct admitted versions. Confirm commit and reconstruct both versions through a fresh qualified observer. Control: a producer using S0 for the second before must fail even if its count/digest is recomputed. Repeat with a request-free public group; no replay storage is a history prerequisite.

Inject failures at start capture, after canonical effects, final collection, envelope encoding and manifest publication. Observe each prescribed savepoint/outer rollback through an independent connection; no committed partial canonical/key/version/journal effect may survive. Roll back one operation savepoint, retain earlier host work, then retry against the actual surviving state: rejected capture/siblings cannot reappear in the retry. Outer rollback after sealing exposes neither group. Lost commit acknowledgment produces the original unknown/recovery outcome and no automatic replacement mutation.

Include intermediate-final-image substitution, a trigger sealing before later property effects, multiple permitted transitions on one home, and final value equal to start after meaningful intermediate effects. Assert the selected mutation/no-op rules independently; endpoint equality alone cannot erase required history. Native staging/sequence/digest implementation must be pinned before these tests execute. They are planned producer qualification, not evidence from pure reducer or schema checks.

### Reserved sequence publication controls

For the selected reference complete-group algorithm, still requiring native qualification, independently author three sibling payloads and their original positions 41, 43 and 48. Compute expected ordered manifest from those exact payloads without the producer encoder; assert gaps do not imply missing siblings. Refuse duplicate or decreasing positions, a changed insertion-returned seq, an extra sibling, and payload/position substitution even when count matches. Two interleaved producers may have individually increasing nonconsecutive positions; compare complete groups rather than assuming one global consecutive range.

Inject allocation failure, uncertain allocation response, failure on a later append and failure on final identity/payload comparison. Require prescribed rollback and no partial committed group. An uncertain allocation or append response permits only qualified original-operation observation, never a repeated phase call, fresh positions or reapplication. After confirmed rollback, an explicitly authorized new operation uses fresh original operation/start evidence and may obtain new actual positions; it never fills guessed gaps. Lost-response barriers must independently prove zero second allocator/append calls while original custody is unresolved. Allocate then roll back: the gap alone proves neither a missing committed version nor history-unavailable. Original allocator durability/recovery and xid watermark tests remain separate native requirements. Baseline insertion-assigned writer and this reserved-position profile cannot be silently mixed by namespace or decoder selection.

### Full snapshot current-authority controls

Independently author a mutation whose before image belongs to document A/module shared and after image to document B/module shared. Grant the caller B only: current record readability must not disclose A's values, original owner identity or protected missing-history diagnostics. Repeat with an edge changing endpoints, a rebound retained field, and an intermediate property delta whose owner does not appear in the requested final record. The required union includes all original prerequisites; matching module labels or final-result owners cannot reduce it. Missing original owner provenance is unavailable, not repaired through current catalog endpoints.

Use separate connections and explicit barriers around original union discovery, fresh admission and publication. Revoke an old-image owner's permission under the selected guard protocol; assert publication ordering against actual exclusion/revocation completion, not elapsed time. Discover an additional owner after tentative admission: require the existing release/restart procedure and no partial record. Coordinator loss or caller-role change withholds all payload and protected evidence; cleanup never commits or rolls back the caller data transaction. Full history cannot pass by dropping a sibling or redacting a required snapshot field. These schedules require native authority qualification, independent from pure reducer correctness.

### Scoped metadata correspondence experiment

[Sixteen synthetic vectors](../../04-build/evidence/design-audit/history-metadata-correspondence-v0.1.vectors.json) and a [finite experiment helper](../../04-build/evidence/design-audit/check-history-metadata-correspondence.py) exercise three metadata positions, seven original boundary corruption refusals and six standalone retained-addition controls. Each corrupted inventory has a recomputed internally consistent experiment count/digest, so these controls demonstrate why manifest consistency alone cannot replace boundary correspondence. The [receipt](../../04-build/evidence/design-audit/history-metadata-correspondence-audit.json) records sixteen passes under normal and optimized Python execution.

This exact-tree experiment uses simplified property homes, fixed versions and experiment JSON hashing. It does not implement the public event wire, adopted journal canonical encoding, native producer/cut/custody, historical definitions, authority or production resources. It supplements the proposed procedure's consistency evidence only; all native schedules above remain planned.

### Standalone retained-addition candidate controls

Independently author a baseline with retained name keep and a standalone physical addition of two new names, one present null and one exact opaque/token value. Under the proposed new event profile, expect one retain event with two unique presence deltas and one group metadata witness, not two fabricated same-seq events. Reduce both additions and compare full retained inventory to the final image; preserve keep unchanged. Literal slash/dot/empty/Unicode-distinct names use exact selected carrier rules, not path interpretation.

Refuse existing-name replacement, removal disguised as metadata, duplicate names, missing member, null-to-absence conversion, source-byte substitution and unresolved historical context. A physical new_value map with old_value NULL does not independently prove all before states absent. The unchanged event/0.1.0 decoder must refuse this new required variant rather than skip it. These are planned new-profile controls; no schema or native support was added by this proposal.

The retained-addition experiment includes one successful two-name addition and five duplicate/existing-name/missing-delta/before-state/token refusals. Independent case membership is checked by exact IDs, so a same-sized substituted corpus cannot pass membership admission. Synthetic literal names and simplified values do not establish original native context/byte/Unicode/codec admission or integrate retain into the unchanged event wire.

### Retained dispatch and later rebind controls

Admit a later-profile retain event adding two homes, followed in the same mutation by a legal rebind consuming one added home under its own exact source/destination evidence. Independently expect the unconsumed retained home plus the bound property and compare the full final witness. Reject wrong event version, payload-only admission without common-context profile, wrong rebind-before, or failure on the second retain member. No prefix, current-definition fallback or snapshot overwrite may repair the group. The old event/0.1.0 decoder refuses the new required event even if its standalone payload is shape-valid. These are planned full profile/definition/source tests, beyond the simplified experiment.

### Definition-derived entity kind controls

Independently author an object and edge with coinciding numeric id/typeId but distinct original definition pins. Property-only events resolve kind from the exact retained historical definitions; compare physical entity_kind and full metadata image kind independently. Swap pins or physical kind while keeping schema-valid IDs and recomputed manifest: refuse. Missing original kind interpretation, a pin mapped to both meanings and current-table presence as fallback cannot qualify the event. A later current catalog changing interpretation does not replace original evidence. New explicit-kind wire proposals require their own version/profile and cannot be accepted by adding fields to the closed existing identity schema.

Retained payload shape evidence now pins both proposal/exact-value schemas and checker bytes, the installed Ajv version and actual Bun runtime in its receipt. Reproduction still requires the named local validator dependency; this is tooling execution, not a portable/browser library or native producer claim. The separate TypeScript receipt and synthetic reducer receipt retain their distinct scopes.

### Later event outer-carrier compatibility controls

Embed the proposed retain payload as if it were an event in the unchanged archive and journal page shapes: reject rather than ignore it or cast it through generic JSON. For selected later carriers, independently test exact complete event versions/profiles, mixed-version continuity only where explicitly admitted, original positions/order and old-decoder refusal. An outer archive version alone cannot authenticate missing historical content or select a new event meaning. Full selected archive/page/seed/feed integration remains planned; current payload checks do not prove it.

### Complete-history supplementary case inventory

These stable case IDs allocate the supplements above to runner-visible planned tests. They are not new acceptance criteria or evidence that the native cases ran. Preserve their required membership in the independently approved corpus for the selected complete profile; an unresolved prerequisite is blocked/not_run, never an omitted passing case.

| Case | Planned test | Criterion allocation | Primary layer | Independent expected observation |
| --- | --- | --- | --- | --- |
| HR-01 | metadata_boundary_position_and_missing_delta | US-018-AC1 | Pure reducer plus native producer | Before/between/after witness placement preserves complete boundary state; recomputed manifest cannot hide missing/conflicting property delta |
| HR-02 | original_capture_two_operations_and_rollback | US-018-AC1 | Native integration | S0/S1 then S1/S2 under distinct versions; rolled-back capture/siblings never enter retry or committed reconstruction |
| HR-03 | reserved_positions_exact_publication | US-018-AC1 | Native integration | Increasing nonconsecutive original positions match complete envelopes; duplicate/substituted/uncertain positions cannot fabricate history |
| HR-04 | complete_historical_owner_union_current_authority | US-018-AC1, US-018-AC2 | Native authorization/concurrency | Old/after/intermediate owners remain independently required; revocation ordering and coordinator failure withhold protected state |
| HR-05 | retained_addition_then_rebind | US-018-AC1, US-018-AC2 | Pure reducer plus native integration | Exact additions and later legal move preserve remaining retained content; old event decoder refuses new required meaning |
| HR-06 | original_definition_kind_and_versioned_carriers | US-018-AC1, US-018-AC2 | Semantic admission plus native loader | Historical pins distinguish object/edge and original interpretation; archive/page/decoder tuple cannot widen through generic JSON |
| HR-07 | partition_checkpoint_horizon_not_unwritten | US-018-AC3 | Native retention/reconstruction | Qualified checkpoint restricts supported horizon; missing discarded evidence is unavailable and never proved unwritten |
| HR-08 | cumulative_snapshot_resource_and_interruption | US-018-AC1 | Native resource/fault | Full simultaneous snapshots/deltas/definitions/work are charged; interruption or overbound later group publishes no requested prefix |

Each case pins event/record/archive/page/layout/codec/kind/authority/resource/adapter/native profiles applicable to its layer, original fixture bytes and independently authored expected full states. Pure portions must be recorded separately from native producer/loader outcomes. The sixteen synthetic experiment cases are component evidence for limited HR-01/HR-05 behavior, not substitutes for these full cases. HR-07 supplements AC3 without weakening its genuinely-unwritten expectation. Native publication/retention actions execute only in the qualified disposable harness under their existing administrative scope.


Plan OA-01–04 for the offload handoff: upload bytes successfully but omit durable complete retrievability confirmation and prove local deletion remains protected; confirm a cohort then substitute installation/epoch/definitions/owner inventory or expire its selected retrieval lifetime before cleanup and require refusal; lose local cleanup commit acknowledgment and independently resolve committed/rolled-back/active/unknown outcomes without blind resubmission or archive rewrite; retain duplicate exact local/archive copies after cleanup failure and reconstruct from the original archived cohort after qualified cleanup succeeds. Missing later archive content returns explicit unavailable without current-row substitution. All are planned selected-provider/native history tests; archive shape probes cannot qualify these phases.


### Selected reference child-store qualification (planned JS-01–04)

These cases qualify CONTRACT-001’s selected row_home_journal_stage composition, independently from historical archive cleanup. Pin the actual installation, parent/stage definitions, phase codec, native roles, descriptor, account and original settlement/dependency producers before execution. All cases remain not_run.

| Case | Independent setup and barrier | Required observation |
| --- | --- | --- |
| JS-01 incompatible cleanup | Present an otherwise matching baseline operation/touch-only cleanup profile to the selected child-store composition | Refuse composition admission before any stage insertion or cleanup SQL. No baseline wire reinterpretation or FK-error-driven cleanup fallback |
| JS-02 complete returned cohort | Retain an original parent with start, ordered transitions, final, reserved and publication stages. Independently retain all six native fields and body bytes. Substitute missing, duplicate, foreign-parent or changed-body observations; permute an otherwise exact DELETE/RETURNING result | Defects refuse the complete attempt; a pure row-order permutation remains admissible after exact membership/body comparison. No LIMIT, phase filter or caller child list can certify completeness |
| JS-03 atomic child/parent disposal | Admit original settlement and current dependency closure, delete the complete child cohort, then inject failure or changed parent correspondence before parent deletion completes | Contained rollback restores all child and parent rows. Recovery/request/feed/history/touch protection added before dispatch prevents deletion. Expected-empty stages require independent complete empty proof |
| JS-04 lost outer acknowledgment | Lose the acknowledgment after the original cleanup transaction’s outer commit attempt; observe committed, rolled-back, active and unavailable outcomes through the qualified original observer | Retain original attempt/cohort custody; no blind second deletion or synthetic success from absent rows. Confirmed rollback may permit a new cleanup attempt only after fresh complete eligibility; active/unknown/unavailable preserve recovery evidence |

Observe native commands and original transaction outcomes independently of the cleanup implementation. Source AST parity, FK presence and shape-valid cohort fixtures cannot prove native visibility, settlement, protected authority, complete returned membership or bounded materialization. These cases supplement existing phase generation/frozen-prefix and reservation recovery controls; they do not permit journal phases to set parent readiness or infer outer commit.


Plan JA-01–03 for the selected journal_seq realization: substitute a same-named foreign sequence or wrong increment/cycle/cache/domain definition and require admission refusal before nextval; independently observe exactly one allocation per frozen sibling and zero for proven empty scope, then require explicit inserts and zero additional allocator calls during append; exhaust int8 capacity or lose allocation response and require original contained recovery with no restart/setval/replacement sequence. Independently corrupt an insertion trigger to replace seq and require full parity failure/rollback. Source-selected settings and ordinary role denial must be checked against actual installed inventory; all native cases remain not_run.
