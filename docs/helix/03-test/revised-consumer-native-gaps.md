---
ddx:
  id: truss.revised-consumer-native-gaps
  type: test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: ADR-003
      kind: informed_by
---

# Revised consumer corpus: required native additions

Input authority is the frozen 2026-10-09 requirements/corpus, retained under
`04-build/evidence/consumer-revision-2026-10-09`. This review is assertion coverage,
not executed Truss evidence. Preserve the 41 original consumer cases; these additions
supplement the full language-neutral release corpus and existing story plans.
Fresh frontend resolution does not execute a consumer case or validate an effect.

| Original case | Observed expectation | Native addition / existing authority |
| --- | --- | --- |
| `action.dry-run-writes-nothing-and-keeps-the-key` | Successful Create/Link preview, precondition failure, unchanged visible count, later apply with same key | R6/PY-04: actual caller transaction and complete selected final-state/deferred validation; independent graph/key/reservation/journal/request/receipt/report observations after caller rollback. Compare same-plan native violations with real apply. No outer completion by Truss; no durable token/pending IDs publication. |
| `action.failed-precondition-changes-nothing` | Missing UseCase failure and unchanged visible count | CONTRACT-004/009: real first-step/late-precondition failure schedule where applicable, full operation/group containment and unchanged private/derived state. Preserve prior caller work and original recovery on unknown rollback. |
| `action.atomic-batch-is-all-or-nothing` | Two successes/replay, then duplicate-key failure and absent new object | STP-040/043: verify complete ordered results, original input/ID correspondence, no repeated effects/journal/facts and atomic rollback across all touched stores. An action batch is not proof of atomic import semantics. |
| `import.identity-skip-and-provenance` | Mixed created/skipped/rejected records, original-author/load provenance and unchanged existing record | STP-034/035: actual native source attribution, actor from authenticated session, original timestamp/null spelling and unknown retained content; repeat/deleted identity and derived/key/edge/journal/report invariants. Counts and one projection are insufficient. |
| `import.entities-before-relationships` | Edge-before-entity input creates both and reads relationship | Import ordering/alias protocols: actual accepted identities and endpoint/key ownership, full original semantic indices, ordinary caller authority and late relationship failure containment. Preserve authoring order in results even when execution staging differs. |
| `import.administrative-principals-only` | Reader/non-admin/anonymous refusals and mismatched initiated_by invalid | R4/R5: independently authenticated native session, security-owned admin capability and current disclosure; prove zero effects and exact journal/action origin on allowed import. Host actor fields cannot grant authority. |
| `import.deleted-stays-deleted` | Deleted identity remains absent; later import skips | STP-034: native retained/tombstoned identity and reservation/key policy, exact absence evidence and no accidental resurrection, with full journal/receipt/feed facts and no caller-supplied identity shortcut. |

## Additional full-release schedules

Add a separate **atomic import** case under CONTRACT-004's selected import mode,
not an `atomic:true` flag invented in the consumer adapter. Start with valid entity,
then valid relationship, then a late invalid item; require no committed import
items/derived/key/report/journal/request/feed artifacts for that attempt. Preserve
unrelated preexisting data. Compare the corresponding **per-item import** using
the same original records, proving independently which items survive, skip or
reject and preserving original ordered outcomes/provenance. The mixed consumer
case alone does not establish this atomic-versus-per-item conjunction.

For dry-run, include a violation seen only by the selected full native final-state
validator, not merely an application precondition simulation. Observe the caller's
actual outer rollback and independently verify its committed absence; do not use
blanket constraint-mode changes that validate unrelated caller work. Respect the
existing group protocol's complete scope and native ownership. A pending response
or failed rollback remains uncertain; row absence is not original containment proof.

"Writes nothing" excludes surviving application/journal/request/receipt state;
it does not promise reclaimed IDs, ordinal permission or refunded cumulative work.
Use the existing original counter/account/allocator protocol and observe burnt
reservations under its selected scope. A second facade or rollback must not reset
original issuer/resource custody. No new product allocator semantics are selected.

Give every addition independent original setup/call/expected artifacts and native
observation procedures in the shared corpus. Record exact installed source/catalog/
layout/compiler/security/driver/corpus tuple, ordinary-role authority and complete
state observations. Run Python and TypeScript against the same committed database
for the full interchange gate. Until the complete producers/installation exist,
these are unexecuted required scenarios; no fake, spy or schema-valid fixture can
be counted as native conformance.


## Concrete R6 deferred-final-state witness

Register an independently authored model with three same-type objects A, B and C
and one directed relationship whose selected source-side maximum is one. Start
with zero edges and complete independent identity/key/value observations. The
positive plan creates A-to-B. The negative plan creates A-to-B and A-to-C in one
atomic group. Both exceed neither input size nor object/key validity bounds;
the negative final state violates the maximum. Two distinct neighbors avoid
conflating the separate occurrence-cap and UMF distinct-neighbor meanings.
Register the actual selected native count/guard profile before the test.

Use fresh equivalent installations/state for preview and real apply arms. For
the deferred-only arm, require actual effect submission and a native barrier
before the selected full final-state validator reports the violation. A profile
that refuses earlier may qualify its own early validation but cannot pass this
deferred-only witness. Do not disable guards, force ALL constraints or guess
prior timing to create the intended ordering. If the selected native mechanism
cannot produce the required schedule, retain this arm unavailable and select a
separately authored realizable deferred-only violation; input-precheck failure
cannot substitute it.

Before preview, the caller updates a separate sentinel object's label from
`committed-before-preview` to `caller-pending-before-preview` in its original
transaction. After the invalid group's confirmed operation-local rollback,
observe through that same admitted caller scope that the sentinel pending change
survives and no preview edge, journal/request/receipt or reservation survives.
Do not use an independent connection to infer uncommitted sentinel state. Then
the caller explicitly rolls back the outer transaction; independent observation
must show the original committed sentinel and complete original graph/history.
Lost savepoint or outer rollback observation retains original unknown recovery,
not an unchanged-state pass.

The valid preview executes complete finalization but publishes only provisional
results; caller outer rollback leaves no durable edge/request/receipt. A fresh
real apply of the same admitted logical plan commits one independently observed
edge with its complete actual history and original actor. The negative real apply
returns the same selected violation as the preview under equivalent original
state and preserves complete rollback/no-durable-effects. Independently compare
original violation identity/path, not just a generic exception or count. Include
original exact input, pending identities, full surviving operation inventory,
constraint timing, cumulative resource use and actual native containment in the
receipt. All composed native/Python cases remain not_run; no public dry-run API
or installed guard support follows from this fixture.


### Native transaction-state component witness

The [original native receipt](../04-build/evidence/design-audit/python-dry-run-native-savepoint.json)
on corrected PostgreSQL16.15 verifies a separate deferred UNIQUE fixture. Actual
validation produces23505, and a read before savepoint rollback produces25P02.
Confirmed ROLLBACK TO SAVEPOINT restores access to the caller's earlier pending
sentinel with zero preview rows; explicit outer rollback restores the committed
sentinel. Four independently authored observations match. The retained harness
uses an administrative disposable fixture, not Truss guards or security APIs.

The composed R6 runner must therefore inspect earlier caller work only after
qualified operation-local containment restores native usability. Before that,
retain transaction_unusable/original native diagnostics and submit no ordinary
read. Lost containment cannot be replaced by an independent unchanged row count.
This native component supports the ordering requirement only; the concrete
Truss relationship violation, complete journals/receipts/accounts and actual
Python dry-run API remain not_run.


The [fresh-state replay](../04-build/evidence/design-audit/python-dry-run-native-savepoint-fresh.json)
uses the revised witness with explicit fresh data-directory/receipt arguments.
Both must be absent before native startup; receipt creation is exclusive.
All four native observations pass again. The [reuse refusal](../04-build/evidence/design-audit/python-dry-run-savepoint-reuse-refusal.json)
returns before startup and preserves the original receipt hash. The first exact
harness source is archived separately as python_dry_run_savepoint_native_original.py;
its original receipt is unchanged. Preflight is a trusted local harness check,
not a hostile filesystem-race guarantee or Truss transaction/security qualification.
