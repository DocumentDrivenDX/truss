---
ddx:
  id: STP-040
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-040
      kind: informed_by
    - id: TD-040
      kind: informed_by
    - id: SD-003
      kind: informed_by
---

# STP-040: Atomic groups

## Story Reference and Scope

US-040, TD-040, SD-003, TP-001 and CONTRACT-004/007/009. Tests are planned. Request-free atomicity is independent of gated receipt replay.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-040-AC1 | `valid_alias_group_has_ordered_results_and_one_origin` | All effects commit together; result order matches input and journal shares xid/origin with exact version progression | `@covers US-040-AC1` | Native integration | `tests/mutation/groups.test.ts`; parent/child/edge aliases |
| US-040-AC2 | `invalid_third_operation_rolls_back_entire_group` | Error names index 2/inner kind; no canonical/key/marker/journal/tombstone/receipt effects survive | `@covers US-040-AC2` | Native integration | Same file; preflight and persistence-failure variants |
| US-040-AC3 | `opposed_order_groups_acquire_same_sorted_lock_order` | Both request-free groups complete without PostgreSQL deadlock, retaining their own result order | `@covers US-040-AC3` | Native concurrency | Same file; independent initially empty transactions and explicit barriers |
| US-040-AC4 | `catalog_acceptance_and_group_have_serialized_legal_schedules` | Acceptance-first makes old-revision group refuse; group-first blocks acceptance until transaction end | `@covers US-040-AC4` | Native concurrency | Same file; observed lock acquisition/acceptance barriers |

## Data and Additional Probes

Use independently expected rows/versions/journal and observer connections. Include owned-deletion closure expansion between discovery and lock, re-key swaps/collisions, stronger delete locks, single/group overlap, mixed no-op operations and final minimum participation. Forward/duplicate aliases and empty group refuse without effects. Barrier/lock-state observations establish actual overlap; timing sleeps alone cannot prove concurrency.

Opposed-order proof excludes arbitrary prior host locks. Include host-induced deadlock as a separate retry/rollback probe without pretending it satisfies AC3. For caller adoption, successful group is pending; caller rollback removes it and failed group preserves earlier host work. Final invariant errors retain last-affecting index and all violation paths.

## Executable Proof and Handoff

Future command `bun test tests/mutation/groups.test.ts` requires implemented harness and finalized shared protocols. Pin layout/lock/adapter/isolation/roles, retain barrier traces and native deadlock SQLSTATE outcomes. All four criteria block closeout. AC4 now explicitly follows head-lock exclusion; no mid-lock acceptance is a valid test schedule.

## Public facade supplements

Select group handles inertly; request-none must work with no receipt namespace/storage installed when the selected request-free profile is otherwise qualified. Apply in an active outer engine/caller scope and require pending new results, not committed. Confirm one ordered result per input including no-ops and exact profiled inner errors/index attribution on failure. Incomplete planning/resource observation returns no successful partial result. Operation-local rollback preserves earlier host work and all group graph/key/journal/source/receipt effects disappear together.

Combined strict declaration checking includes `truss-mutation-group-capability-v0.1.typecheck.ts`: independent consumers reject standalone aliases, premature in-transaction commit, same-transaction replay labeled committed and failure with success payload. These are type distinctions only; native context and effects require the cases above.

Complete result wire checks use `check-group-result.ts` and independently authored operation/replay fixtures. Twenty structural expectations cover create/change/no-op/delete and same-transaction versus committed-receipt replay, including empty group/event and false replay durability rejection. Wrong input order, duplicate native event and forged committed disposition intentionally remain shape-valid semantic/native controls. Verify original complete input/result/alias/deletion/event correspondence and actual original commit/authority separately; schema pass never authorizes replay.

Unified planner lock-order controls follow the current CONTRACT-009 table rather than the retired seven-level shorthand. Mix single writes, request-free/request-bearing groups, re-key, owned deletion and concurrent catalog/policy/namespace administration. Independently verify full earlier guard sets before business/root/row locks and contained restart on newly discovered earlier owner/root/bucket; request-free omission never skips required policy admission. Native writer coverage and the selected advisory versus bucket observation profiles are separate prerequisites. Existing declared wire/type checks prove shape only, not complete closure/final invariant or lock ordering.

Resource profile probes use the exact CONTRACT-009 reference artifact. For each counter independently expect exact-bound admission and one-over resource refusal; force depth/node/closure/guard/simulation exhaustion without treating result paging or SQL LIMIT as complete discovery. Exhaust after graph/key/journal effects and independently verify confirmed savepoint rollback of every effect; cancellation with unresolved native cleanup is an outer execution failure. A long host transaction after a successful pending call retains its guards, with no deadline-triggered commit/unlock. Native actual scan/buffer/cancellation evidence is separate from logical counter evidence.

Deadline/containment boundary: hold native work beyond the 30,000 ms candidate invocation budget, then permit rollback during the independent 5,000 ms containment observation. Confirm no effect survives and only then expect resource unavailable. In the alternate barrier schedule, withhold termination confirmation past containment allowance: expect outer unresolved execution, original recovery reference and quarantined unreleased connection, with no automatic reexecution or whole host transaction termination. Verify both schedules independently rather than treating cancellation acknowledgment as rollback.

Composed value/group resource tests use independently counted roots and canonical bytes. A value within its own limits exceeds whole-group depth only after envelope nesting; many individually valid values exceed aggregate input/result limits; one value exceeds its scalar/collection bound while aggregate group bytes fit. Require the named failing profile/counter and whole-operation refusal, without tag conversion, profile substitution or truncation. Envelope expansion is admitted before allocation/native submission and failure after effects is fully contained. Validity of an individual carrier never qualifies the containing operation's decoder/work profile.

### Request-free dispatch controls

Under an independently selected ordinary-group deployment without receipt storage, instrument the full admitted command/procedure path. A request-none invocation performs no request namespace lookup/lock, receipt read/write, replay digest or retention-clock work, while retaining all original policy/catalog/operation/touch/journal/finalization controls. A unavailable or hostile receipt-only service must not be invoked or cause ordinary readiness failure. This is not permission to bypass unknown installed-policy objects or an ordinary group producer failure.

Invoke identical request-none operations twice in separately confirmed transactions: independently expect each operation's normal second-invocation meaning, including unique-key conflict, stale-version refusal or valid new effect/no-op as appropriate. Never expect replayed solely from equal input. Inject lost completion after submission and lost commit acknowledgment; require original recovery custody and no automatic replacement invocation, receipt lookup, manufactured request identity or receipt_expired result. Also mutate the caller request envelope after admission and verify branch choice remains original. Cases compare original command traces and complete graph/key/journal/result state, not just the response discriminator. Request-present replay qualification remains STP-043 work.


## Concrete final-state relationship replacement

Start from the independently authored reference M03 graph: Account A has AB and AC, Item D is unlinked, the Account's target maximum is two, each Item's source maximum is one, and both lower bounds are zero. On a fresh isolated copy submit one request-free atomic group: first create A→D, then delete original AB. Independently expected final membership is exactly AC plus the newly assigned AD; A/B/C/D all remain live, B becomes unlinked and no independent-lifecycle target is deleted. The intermediate simulation has three targets for A, but the complete final graph satisfies the selected cross-row group invariant. Do not classify the first operation as the standalone M04 third-target refusal; CONTRACT-009 qualifies final cross-row checks for the group while each operation still has its complete field/type/key/endpoint/authority admission.

On a separate fresh original graph submit the reverse ordered group, deleting AB then creating AD. Both groups produce the same logical final membership, but retain their own original operation order, actual newly assigned edge identity, ordered semantic results, version/source/origin and complete journal/metadata references. Do not require equal generated IDs, sequence order or complete receipt bytes across independent executions. Original AC's edge identity and unchanged endpoint record state must remain exact. No provisional intermediate graph is published outside the original transaction.

Negative controls omit deletion of AB (invalid final third target), delete an unrelated edge (same final violation), use a missing or wrong-typed D, or create a second incoming source for an already linked Item. Require indexed failure according to the selected immediate-versus-final violation rule and confirmed complete group rollback, preserving original graph/key/reservation/source/journal state. An unknown containment/commit outcome retains original recovery rather than a rollback assertion. Inspect complete finalizer/touch participation: deleting AB cannot hide a required dirty A/D/B scope or omit one of the two operation results.

Hold the group pending under an adopted transaction: its original admitted scope sees the complete pending final graph, while an independent committed observer retains AB/AC until host settlement. Host rollback restores the original graph; host commit publishes only the final AC/AD membership. Native trigger firing/deferred constraint timing and protected producer orchestration must independently realize this result without changing caller transaction constraint mode. These planned cases supplement US-040 atomicity/rollback criteria and the existing lock/concurrency corpus; standalone max violations still refuse.


For the replacement case, distinguish original semantic order from admitted native dependency order. The fixed marker profile may remove AB before inserting AD; do not require a physically stored third marker as evidence of final-state support. Capture the complete preplanned native effect ordering and original semantic attribution independently. A forced implementation that cannot retain both ordered results and full original history correspondence refuses qualification; silently swapping public operation indices or dropping a deletion event fails. Plain-SQL caller flags or future-delete promises never grant a finalizer exemption.
