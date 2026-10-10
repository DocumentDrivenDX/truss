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
