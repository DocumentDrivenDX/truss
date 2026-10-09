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

## Implementation order and ownership

The existing planner in `packages/tooling/src/layout-migration-plan.ts` selects
declared metadata only. The receipt guards in
`packages/postgresql/native/layout-migration-receipt-immutability.sql` are one
storage component. Neither is an executor. Implement the following sequence
against the existing administrative binding, without introducing another
framework-specific ledger or recovery service.

| Sequence | Concrete implementation output | Evidence required before the next dependent stage |
| --- | --- | --- |
| M1 select the first supported populated route | One exact registered source/target bundle pair, original recipes and ordered native/data/preservation inventories; declare receipt-home initialization or conversion in that route | Independently authored LM-T03 expectations cover objects, keys, edges, retained values, catalog, reports, journal, receipts, feed positions and unresolved recovery state. A metadata-only route or empty database is insufficient |
| M2 bind original administrative services | Private composition over the existing installation verifier, installed-target HostRecoveryRegistry, registered recipes and qualified driver; durable original request/attempt recovery custody before submission | Wrong service/build/profile, modified request, unavailable registry and caller-owned transaction refuse before effects; restart recovers the same original reference. No public JSON field grants administrative authority |
| M3 implement transactional apply | One owned transaction runs source verification under common exclusions, ordered steps, independent target/preservation checks and atomic receipt/archive/marker publication | LM-T05 demonstrates actual first-step effects followed by second-step failure, complete rollback and no target receipt. LM-T06 and LM-P01–03 exercise the security-owned writer/context fences and any required publication drain |
| M4 implement settlement and reconcile | Qualified original driver outcome correlation plus read-only original-attempt lookup, preserving every existing result variant | Actual lost-ack and post-commit verification failure produce commit_unknown/recovery_required/committed_unverified as applicable; reconcile never repeats recipes. LM-T04 verifies original repeat identity and fresh target parity, including changed bytes and native drift refusals |
| M5 expose the packaged deployment flow | Existing apply/reconcile contract exposed through selected release packaging, with a clean consumer example and advertised source/target matrix | LM-T01/02/07/08 prove bootstrap separation, ordinary catalog evolution without migration, unsupported-route refusal, no automatic upgrade and framework failure after confirmed Truss commit. Each advertised PostgreSQL or managed-service tuple has its own native evidence |

Truss owns route recipes, preservation obligations, executor composition and the
deployment example. UMF owns generic schema representation and DDL generation;
consume its admitted outputs rather than creating a second generator. Weft owns
logical SQL compilation; verify compatibility with both selected layout profiles
without moving migration execution into the compiler. The authorization/security
owner supplies administrative admission, common exclusion order, freshness and
publication drain. M3 cannot replace those with a Truss-specific ACL resolver or
assume native lock release settles a publisher.

M1 remains unselected: the authored physical layout proposals and component
receipts do not establish a released source/target upgrade pair. M2–M5 remain
unimplemented. Their first native schedule must use the same M1 pair throughout;
passing checks assembled from different layout proposals cannot qualify a route.
These are engineering delivery dependencies, not a reopening of the owner's
decision to ship migrations in the first release.
