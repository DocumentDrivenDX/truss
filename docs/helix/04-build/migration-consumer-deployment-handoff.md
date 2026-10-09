# Consumer deployment through shipped migration tooling

Implementation handoff for LM-06/B-014 under CONTRACT-008. This is a proposed
deployment flow, not a released command or executable example. Reuse the
[existing apply/reconcile interface](../02-design/contracts/bindings/truss-layout-migration-v0.1.proposal.d.ts)
and LM-T01–08; public package and CLI names remain release outputs.

The consumer runs this deployment step outside its framework's outer database
transaction. It supplies the admitted administrative composition, original
registered manifest and exact source/target artifacts. Truss owns one dedicated
transaction for the entire transactional route. The framework must not supply
application credentials as administrative authority, wrap apply in its own
transaction, or treat its migration history row as Truss commit evidence.

First inspect and independently verify the actual installed source through the
selected installation tooling. Use the pure planner only to select an explicit
registered route. Persist original request/attempt recovery custody before native
submission through the governing registry procedure. Invoke apply with that
original request; do not derive SQL from version strings or mutate the request
after submission. Interpret its exact result as follows:

| Result | Consumer deployment action |
| --- | --- |
| migrated | Retain original confirmed commit and target evidence; complete current readiness verification before opening compatible application connections |
| already_applied | Retain original commit and fresh currentVerification; do not submit steps again; admit runtime only under complete current target verification |
| refused | Record the refusal and its actual containment phase; stop the deployment step, without marking the target installed |
| rolled_back | Retain original termination evidence; keep the verified source state; a later attempt requires fresh source/authority admission, not automatic callback retry |
| commit_unknown | Retain originalAttempt, originalEvidence and recoveryReference; keep target readiness closed and call reconcile for that same reference |
| recovery_required | Preserve original custody for unknown application/cleanup; reconcile without resubmitting effects or releasing an unconfirmed native lease |
| committed_unverified | Preserve confirmed commit; keep target readiness closed until original recovery and current verification succeed; never label this rolled back |

Reconcile is read-only original-attempt lookup. observation_unavailable does not
prove rollback or permit a new apply attempt. Other reconciliation variants
retain the same result meanings above. A process restart restores the original
recovery reference from admitted durable custody; it cannot infer an outcome
from a framework success flag, current version or a missing response.

If no route is needed, the planner's no_steps is only a metadata result. Perform
the selected current installation/native/security/data verification anyway.
Ordinary consumer UMF revisions use catalog acceptance and never invoke this
physical upgrade flow. Fresh bootstrap uses its separate nonempty-namespace
refusal and installer protocol, rather than pretending an absent database is a
registered upgrade source.

The clean packaged-consumer example must demonstrate these branches without
private imports, retain actual emitted artifacts and fail application startup
when verification is unavailable. Include framework failure after confirmed
Truss commit: the upgrade stays committed. Include actual lost-ack recovery,
changed recipe/drift refusal and the
[receipt/feed compatibility controls](../03-test/receipt-position-and-reached-scenarios.proposal.md#receipt-visibility-across-shipped-layout-upgrades).
Qualify PostgreSQL and each advertised managed-service tuple separately. The
example becomes executable only when the original installer, migration executor,
recovery registry, verifier and public packaging are implemented.
