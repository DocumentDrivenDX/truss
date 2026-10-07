---
ddx:
  id: STP-005
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-005
      kind: informed_by
    - id: TD-005
      kind: informed_by
    - id: SD-001
      kind: informed_by
---

# STP-005: Tightening and transforms

## Story Reference and Scope

US-005, TD-005, SD-001, TP-001 and CONTRACT-003/007. Tests are planned. Independent expected violations and transformed values qualify the declared exact profile.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-005-AC1 | `tightening_lists_all_three_and_large_violator_sets` | Complete typed/path violation set returned; candidate has no persisted effects and hidden rows cannot evade scan | `@covers US-005-AC1` | Native integration | `tests/catalog/tightening.test.ts`; 3 plus multi-page fixtures |
| US-005-AC2 | `tightening_accepts_only_after_complete_clean_scan` | All checks complete with zero violators before new definitions/head commit | `@covers US-005-AC2` | Native integration | Same file; corrected data and scan-failure control |
| US-005-AC3 | `total_transform_commits_values_history_and_each_change_journal` | Independently expected exact transformed values/derived keys commit with definition history and one journal entry per actual changed value | `@covers US-005-AC3` | Native integration | `tests/catalog/transforms.test.ts`; qualified deterministic profile |
| US-005-AC4 | `type_change_without_transform_rejects_atomically` | Missing transform refuses even if current sample values appear convertible, leaving all state unchanged | `@covers US-005-AC4` | Native integration | Same file; type/cardinality changes |

## Failure and Boundary Probes

Execution-profile controls distinguish a trusted synchronous callback from a qualified isolated callback: a blocking cooperative function cannot pass a claimed hard deadline merely because a timer was scheduled. Isolated timeout/worker loss returns incomplete/refusal with no candidate persistence, no truncated all-violators report and owned-resource cleanup only. Exact large numeric/dependency inputs survive boundary transport. Missing memory/preemption evidence cannot become an advertised bound. Repeated deterministic output is a control, not universal purity proof.

Transform dependency fixtures declare same-record prior-state properties explicitly. Reverse target iteration and require identical candidate outputs; mutual prior-value reads are deterministic and do not consume earlier candidate outputs. Absent dependency is explicit Presence false; duplicate/wrong definition or undeclared access refuses the selected profile. Changed dependency registration pin changes acceptance input. Resource accounting includes frozen dependency bytes. Persistence failure/retry never reevaluates callbacks; final candidate invariant failure leaves all values/head/history unchanged.

Registered-transform vectors reject unknown registration/definition pair, mutable input access, clock/random/global-state dependency under the qualified host profile, thrown/invalid outputs and candidate resource overflow. Absence/null/empty values remain distinct. A spy confirms persistence uses retained outputs without a second invocation. Exact unchanged presence yields the proposed no-op outcome while definition change remains audited; lexical decimal change emits a mutation despite equal key identity. Cross-property reads require a declared dependency profile, not hidden global access. Runtime trust/isolation and native history/no-op reconciliation are qualification gates, not supplied by a function type.

Use independent expected Unicode length semantics, null/absence and exact large numerics. Inject non-total transform on a late record, timeout, duplicate transformed key and journal failure: complete atomic rollback is required. Transform-generated candidate values must undergo final assertion checks. A clean partial page does not establish complete scan.

Test deterministic pure transform outputs in browser separately; native acceptance proves persistence/history. Trace registered transform identity/version; untrusted UMF code strings cannot execute. Concurrent conforming mutation is excluded by head lock with explicit barriers.

## Executable Proof and Handoff

Future command `bun test tests/catalog/tightening.test.ts tests/catalog/transforms.test.ts` requires actual harness and finalized transform/check-order/completeness semantics. Retain full expected/actual violation sets, before/after state and journal receipts. All four criteria block closeout.

Transform callback input/result wires are authored under CONTRACT-003, preserving exact absence/null and prior-state dependency boundaries. Original registration/dependency/profile admission and complete candidate-state validation remain mandatory; callback shape cannot establish purity or totality.

Run `bun docs/helix/04-build/evidence/design-audit/check-catalog-transform.ts <Ajv Draft 2020-12 module path>`: thirteen shape cases pass. Independently reject duplicate/incomplete dependencies, wrong prior snapshot/candidate revision, forged callback/profile and unqualified source-code input. Rejected callbacks cannot retain partial candidate output; available diagnostics remain bounded/current-authorized. No shape test qualifies host isolation or native final-state invariants.

Registration probes count zero callbacks/native/clock/scheduler activity; reject duplicate function/profile replacement, empty/duplicate definition pairs, wrong dependency ownership and mutable getter/proxy inputs. Dispose before invocation and require new-admission refusal while original admitted attempts retain custody. Throw/malformed result yields permitted failure without raw stack/partial persistence; persistence never reexecutes callback. Qualify returning deadline excess separately from interruptible hard-bound isolation; the current synchronous type rejects Promise callbacks. Three strict consumer controls pass, with original runtime/host execution still unqualified.

Transform registration now requires canonical immutable manifest provenance binding implementation/environment, resource/execution/value/dependency profiles and definition pairs. Registration pin hashes exact manifest bytes; duplicate runtime fields must match, and original host recognition binds the actual function. Names/function.toString cannot qualify closure identity. Changed semantics cannot reuse the old accepted transform pin. Retained exact repeat never reruns the callback.

Callback/manifest corpus now passes 19 cases. Independently substitute runtime resource/dependency fields behind unchanged manifest, mutate captured implementation state, offer unknown implementation issuer, and replace manifest while retaining old pin: refuse before invocation. Interpret original retained report without callback reexecution; missing archive/profile cannot become current-default interpretation.

Acceptance report retains complete original transform registration manifests and implementation recognition in a required inventory. Verify exact set equality against distinct accepted-input pins and persist atomically before head advance. Retained exact repeats do not invoke callbacks or substitute current manifests.

Accepted-report corpus now has 13 shape cases. Independently omit/add/duplicate registration entries, mismatch manifest SHA or recognition issuer, fail archive persistence, and change current callback before exact repeat. Require semantic refusal/whole rollback as appropriate and unchanged original report on admitted repeat; no current-default reconstruction.
