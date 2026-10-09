# Consumer deployment through shipped migration tooling

## Product expectation

Truss ships a migration system in its first release, with infrequent use as the
intended operating model. Its fixed storage layout must accommodate ordinary
consumer model evolution through catalog acceptance without physical migrations.
The shipped tooling covers necessary Truss storage format and installed runtime
upgrades; frequency is a design expectation, not a promise that upgrades will
never be required. Opening an application connection does not automatically
upgrade an installation. Deployment operators explicitly inspect, verify, apply
and reconcile registered upgrades using the flow below. This capability is a
release requirement; the planner and component evidence do not yet satisfy it.

## Planner wire correction — 2026-10-09

The private LM-01 planner now requires route direction to be an exact string;
coercing an array containing `downgrade` previously allowed a wrong-type direction
to enter a declared reverse plan. Complete manifest validation refuses malformed
directions in selected, unselected and at-target routes before returning any plan
or `no_steps`. Direct target text also receives a code-unit length precheck before
UTF-8 allocation, followed by the existing exact byte and version checks.
`bun test tests/layout-migration-plan.test.ts` passes eleven tests and forty
assertions. This corrects bounded metadata preparation only; original native
source/target admission and M1–M5 remain separate requirements below.

Implementation handoff for LM-06/B-014 under CONTRACT-008. This is a proposed
deployment flow, not a released command or executable example. Reuse the
[existing status/verify/apply/reconcile interface](../02-design/contracts/bindings/truss-layout-migration-v0.1.proposal.d.ts)
and LM-T01–08; public package and CLI names remain release outputs.

The consumer runs this deployment step outside its framework's outer database
transaction. It supplies the admitted administrative composition, original
registered manifest and exact source/target artifacts. Truss owns one dedicated
transaction for the entire transactional route. The framework must not supply
application credentials as administrative authority, wrap apply in its own
transaction, or treat its migration history row as Truss commit evidence.

### Decide which deployment operation is required

Release preparation compares the exact required installed inventory and retained
encoding/interpretation obligations, rather than treating every dependency
version change as a layout migration. This is engineering classification under
CONTRACT-008; it neither permits automatic DDL nor creates a new runtime API.

| Proposed change | Existing required route |
| --- | --- |
| Ordinary accepted UMF model revision | Catalog acceptance and its full validation/report/head protocol; fixed physical layout and migration ledger remain unchanged |
| Policy or execution configuration update within the admitted installed profile | Security/configuration owner's explicit protected transition, current-context invalidation and publication rules; no hidden routine replacement or layout marker advance |
| Python/TypeScript/Weft package update with the same required installed inventory and retained meaning | Admit the exact new host/compiler/backend tuple through its supported compatibility matrix; no database upgrade follows from package version alone |
| Required table, column, constraint, index, installed routine, grant or retained encoding change | Registered Truss administrative upgrade/conversion with original source/target, complete preservation, exclusion, settlement and verification; unchanged table count cannot exempt a changed routine or codec |
| Restore/fork or drifted installation | Existing restore/incarnation or explicit qualified repair/recovery procedure; neither ordinary acceptance nor repeating an already committed migration supplies the missing provenance |

An upstream schema/semantic version change is not enough to decide which row
applies. The selected owner interpretation must establish compatibility and any
required conversion first. Preserve original policy/model/profile bytes and
unknown content; do not relabel retained input to avoid a migration. Unsupported
new meaning keeps the affected capability unavailable until its exact tuple is
admitted. LM-T02 and the M5 clean deployment example must independently show
ordinary model/package evolution causes no physical migration, while a required
routine-only upgrade cannot bypass the registered route. These are planned
qualification controls, not support for an unselected upstream version.

First call the draft migration `status` and `verify` procedures under their
original registered inspection/resource profiles to observe and independently
verify the complete actual installed source. These methods remain unimplemented;
the source cannot be inferred from a marker or planner input. Use the pure planner only to select an explicit
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
| M2 bind original administrative services | Private composition over original status/verify inspection, installation verifier, installed-target HostRecoveryRegistry, registered recipes and qualified driver; durable original request/attempt recovery custody before submission | Wrong service/build/profile, modified request, unavailable registry and caller-owned transaction refuse before effects; restart recovers the same original reference. No public JSON field grants administrative authority |
| M3 implement transactional apply | One owned transaction runs source verification under common exclusions, ordered steps, independent target/preservation checks and atomic receipt/archive/marker publication | LM-T05 demonstrates actual first-step effects followed by second-step failure, complete rollback and no target receipt. LM-T06 and LM-P01–03 exercise the security-owned writer/context fences and any required publication drain |
| M4 implement settlement and reconcile | Qualified original driver outcome correlation plus read-only original-attempt lookup, preserving every existing result variant | Actual lost-ack and post-commit verification failure produce commit_unknown/recovery_required/committed_unverified as applicable; reconcile never repeats recipes. LM-T04 verifies original repeat identity and fresh target parity, including changed bytes and native drift refusals |
| M5 expose the packaged deployment flow | Existing status/verify/apply/reconcile contracts exposed through selected release packaging, with a clean consumer example and advertised source/target matrix | LM-T01/02/07/08 prove bootstrap separation, ordinary catalog evolution without migration, unsupported-route refusal, no automatic upgrade and framework failure after confirmed Truss commit. Each advertised PostgreSQL or managed-service tuple has its own native evidence |

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

### M1 populated preservation comparison

Before selecting a route, author its expected preservation mapping independently
of the executor. LM-T03 uses that same mapping for committed target checks;
LM-T05 compares confirmed rollback with the original source. Counts and aggregate
hashes are supporting observations, not substitutes for the following comparisons.

| Retained surface | Required source/target comparison |
| --- | --- |
| Objects, keys and edges | Preserve full typed identities, key ownership, endpoint direction and membership. Compare every independently seeded property, including absent, explicit null, empty sequence, exact decimal, large integer and unknown retained content. An explicitly declared conversion needs both original bytes and independently expected target meaning |
| Catalog and acceptance reports | Preserve original document bytes, revision lineage, immutable full reports and source artifact membership. Verify current head and lifecycle state separately; recreating an equivalent-looking report cannot replace its retained original |
| Journal and reconstruction | Preserve group order, complete sibling membership, property deltas, metadata witnesses and declared history horizon. Reconstruct independently selected before/after states through the admitted target reader; equal row counts do not prove replay compatibility |
| Mutation receipts | Resolve each retained original request to the same committed outcome and complete results after upgrade. Changed requests still conflict. Preserve the remaining retry protection interval; migration time does not shorten or restart it without an explicit qualified rule |
| Feed and acknowledgments | Preserve original epoch/incarnation, positions, consumer acknowledgments and protected unread horizon under the declared compatibility mapping. Exercise a pre-upgrade token against the target resolver and verify actual continuation/reached meaning, rather than comparing token spelling |
| Unresolved recovery and publications | Preserve original attempt references, durable recovery membership and outstanding resource/protection obligations. An unresolved attempt stays unresolved until its original settlement procedure proves an outcome. Consume the security owner's required buffer/drain observations separately from native transaction state |
| Allocation and installation state | Verify each declared allocator's committed nonreuse obligation, complete target inventory and exact archive/marker provenance. Sequence gaps after rolled-back work may be permitted by the selected allocator profile; rollback must not reset an allocator merely to reproduce its previous numeric value |

Seed at least one meaningful instance of each applicable surface, including an
outstanding protected receipt/feed/recovery case. Explicitly identify inapplicable
surfaces from the selected source profile; an empty fixture is not evidence that
the route preserves an implemented surface. Retain independently encoded source
expectations before collecting the executor's output. If a conversion cannot
preserve an original token or decoder contract, declare its compatibility and
recovery treatment before route admission; do not discover a silent break after
publishing target readiness.

Fault immediately before conversion, after a populated conversion, before
receipt/marker publication and at commit acknowledgment. Confirmed rollback
restores transactional source data and publication state while retaining allowed
allocator gaps and original recovery evidence. Unknown settlement keeps both
the original attempt and readiness gate intact. These are planned LM-T03/05
comparison requirements; no populated route is qualified by this handoff.

### Administrative migration receipt lifecycle

The mutation request's at-least-24-hour retry guarantee does not define an
administrative migration receipt's purge time. Current migration receipt guards
refuse UPDATE/DELETE/TRUNCATE, and complete retention cleanup remains unavailable.
M2/M4 must retain original route/request/attempt/recipe/profile and commit evidence
for every still-protected reconciliation and installed-lineage obligation. Do not
reuse mutation expiry or zero journal retention as administrative cleanup authority.

The selected route must inventory those protection dependencies with original
custody, including unresolved registration/application/cleanup attempts, later
routes that depend on its installation provenance, and still-advertised original
retry/reconciliation. Any future offload or retirement needs a separately admitted
complete lifecycle and retrieval/authority/resource correspondence. Neither upload
acknowledgment nor a retained version/digest is the original complete receipt.
Until that lifecycle is qualified, preserve the current unavailable-cleanup rule;
this handoff selects no administrative TTL or archive provider.

LM-T03/04/08 must independently expire eligible mutation receipts and apply the
selected short/zero journal policy while keeping a protected migration attempt.
Its complete original administrative receipt and recovery reference remain
available under current disclosure admission; reconciliation submits zero recipes.
Add direct migration-row delete/truncate attempts and missing/offloaded-but-
unretrievable original evidence. Unqualified deletion refuses, and unavailable
historical evidence keeps reconciliation unavailable rather than triggering apply.
Repeat across the subsequent-upgrade reconciliation schedule. These planned controls keep
separate lifecycle protections observable; the private trigger component alone
cannot qualify complete installed privileges or archival durability.

### M2/M3 full migration receipt capacity

The current migration storage adjunct has one aggregate native check:
`octet_length(original_request_bytes) + octet_length(original_receipt_bytes)`
must be at most 16,777,216 bytes. Both artifacts must be nonempty. This is a
combined stored-byte ceiling, not two independent sixteen-MiB limits. The
planner's one-MiB metadata and 1,024-step ceilings do not qualify complete
request/receipt production, storage or delivery.

For M1's selected route, serialize and retain the exact original request before
submission. The original receipt producer must supply a finite bound for its
complete ordered step evidence, original recipes/procedures, preconditions,
actual effects, target/preservation observations and installation/inventory
artifacts. Admit request size plus that complete receipt bound against the native
ceiling and original shared account before the first recipe effect. A small
trial receipt, identity/digest-only substitution or dropping unselected original
manifest content cannot establish capacity. If no complete bound is available,
the route remains unavailable. This does not require predicting arbitrary
allocation failure; unexpected late failure still uses original containment and
settlement.

Separately account base64 expansion inside exact artifacts, outer delivery,
native backing/detoast and simultaneous retained/decoded views. The four-MiB
acceptance-response candidate is not a migration response profile. The selected
migration apply/reconcile transport must preserve its complete original receipt
and commit/recovery evidence under its own admitted limits.

Independent M2/M3/M4 controls must include:

| Capacity case | Required observation |
| --- | --- |
| Valid route metadata fits the planner, but full request plus receipt bound exceeds storage | Refuse before recipe effects, receipt/archive insertion or marker advance; preserve actual administrative containment |
| Combined stored bytes equal the native ceiling, then exceed it by one byte | Independently authored complete artifacts establish the exact boundary; both source and target/protection inventories remain complete. Native constraint success alone does not qualify semantic admission |
| Each artifact separately fits sixteen MiB but their sum does not | Refuse aggregate capacity; no independent-per-field shortcut |
| Original receipt grows through an additional step, recipe body or preservation inventory | Recompute the complete selected route bound; do not reuse the previous route's favorable receipt size |
| Late encoding, consolidation or persistence failure after actual recipe effects | Confirm full rollback before reporting it; unknown termination/commit retains original recovery custody, never a shortened success receipt |
| Apply committed but delivery/reconcile response capacity is unavailable | Preserve original confirmed commit and immutable receipt; no rerun or pruning to make delivery fit |

These controls use M1's real populated route and the existing M2–M5 services.
They introduce no alternate ledger, new native cap, public permit or automatic
migration behavior. Source arithmetic and declarations alone remain unqualified.

### M2/M3 inspection-to-application change schedule

Implement CONTRACT-008's “Metadata plan to registered execution correspondence”
with independently controlled changes between initial inspection and the fresh
source verification under writer/security/configuration exclusion. The retained
inspection and inert plan do not reserve an installation or grant permission to
execute. Preserve both observation cuts; never replace the original request with
a silently refreshed plan.

LM-T04/06 must exercise the following schedules before qualifying M3:

| Change after planning | Required observation before the first recipe effect |
| --- | --- |
| Same-version routine, grant, constraint or retained encoding drifts | Fresh complete source comparison refuses; matching version text cannot permit execution |
| Another original administrative attempt commits the selected route | Settle and inspect through the original receipt/commit procedures; do not infer `already_applied` from target-looking inventory or execute the recipes again |
| An unselected manifest route changes, or selected recipe order changes | Complete registered manifest/plan correspondence refuses, even when the selected route ID and individual digest fields appear unchanged |
| Caller mutates manifest or source-observation buffers | Original retained bytes remain fixed; changed supplied correspondence refuses before effects |
| Source collection or exclusion becomes unavailable | Preserve the actual admission/containment outcome and original recovery custody; zero recipe effects and no automatic bootstrap or repair |

Record original bytes, independently expected differences, effect observations
and the actual result/termination evidence. Distinguish permitted transaction
setup, exclusion and recovery registration from recipe effects; “zero effects”
must not conceal an unconfirmed administrative transaction. After a refusal, a
new request requires fresh explicit admission and any original-attempt settlement;
it is not an automatic callback retry. These are planned M2/M3 qualification
controls, not evidence of an implemented executor or a supported populated route.

### M5 deployment ordering and runtime compatibility

The first packaged route must include a deployment sequence and an explicit
runtime compatibility matrix alongside its source/target layout matrix. Same
layout major does not admit an arbitrary runtime build. For each advertised
runtime tuple, record whether it can open the source, open the target, retain a
live lease across the transition, or must be stopped before application. These
entries must reference the selected admission and exclusion procedures; a
consumer framework's migration version is not a compatibility decision.

For the default transactional route, the clean deployment example performs
read-only source inspection, creates the inert plan, establishes the required
writer/publication exclusions, explicitly applies, settles the original attempt,
and independently admits the committed target before enabling its runtime.
Consumers preserve the original recovery reference across deployment-process
restart. An acknowledgment timeout pauses this sequence at settlement; it does
not advance to starting the target or create a second apply attempt.

LM-T06/08 must cover these independent deployment observations:

| Deployment event | Required observation |
| --- | --- |
| Old runtime connects while upgrade is pending | Original source admission and selected fence semantics decide wait/refusal; no target-only routine is invoked under source admission |
| Old runtime reconnects after confirmed target commit | Its declared target compatibility is checked against the actual target; an unsupported build refuses before application work, even when the major version is unchanged |
| Target runtime starts before settlement | Target readiness remains closed until original confirmed commit and target admission; a target-looking marker cannot bypass unknown settlement |
| Consumer application deployment fails after upgrade commit | Truss remains at the independently verified committed target. Returning to an older application build is allowed only if that build is admitted by the target compatibility matrix |
| Operator requests physical downgrade | Only a registered, independently qualified reverse route can apply. Application rollback must not synthesize a down script or run bootstrap against the populated installation |

Rolling deployment is advertised only when the selected route qualifies the
necessary simultaneous runtime tuples and transition leases. Otherwise publish
the route's required interruption and exclusions explicitly, without claiming
online upgrade support. These cases extend the existing LM-T06/08 obligations;
they are not executed evidence or a selection of a populated release pair.

### Security enrollment/exclusion ordering dependency

The security owner’s active 2026-10-09 review identified a possible circular
wait when a reader holds a shared guard while awaiting publication enrollment:
a queued exclusive changer may prevent the issuer’s subsequent shared admission.
Its proposed repair enrolls before reader guard acquisition and refuses busy
enrollment immediately. This is an in-progress owner finding, not a released
protocol or Truss-native qualification. The owner thread is
`01a11b8b-06bb-7091-a11a-b7eba0a432eb` (Assess security control support).

Before composing M3 with that protocol, independently schedule an original live
publisher, a queued migration/change, and a new or nested enrollment. Record the
actual guard/native enrollment order and bounded refusal/settlement observations.
The pending changer must not strand the existing publisher’s final release, and
failed enrollment must not create an active publication or release another
publisher’s custody. After the confirmed change, a successful new admission must
use the fresh selected installation/authority generation. Cancellation and lost
backend cases still require original outcome/drain evidence; elapsed time alone
does not establish cleanup. Test both a compatible upgrade and a transition
requiring publication retirement according to their selected profiles.

Consume the owner’s final registered ordering and evidence in LM-T06/LM-P01–03.
Do not hard-code the tentative repair into a second Truss lease service or infer
that a native lock timeout proves publication retirement. Earlier drain receipts
retain their original scope and cannot prove this newly identified interleaving.

The subsequent read-only owner checkpoint inspected
`docs/helix/04-build/evidence/security/pg-raw-persistent-drain-component.json`
in the security worktree: SHA-256
`9de0d6d9a819dbe03a324ad70920561b99bf7dd76b50cdbb01f4c9898eaec0df`,
status passed, 1,196 recorded observations, all 87 recorded source hashes matching
current files. Truss did not rerun these native tests. The receipt expressly
excludes a truthful public retirement service, general read-path enrollment,
complete writer closure and registered L03 qualification. Its controlled consumer
discard acknowledgment and fixture assessor do not supply those missing services.

The owner's current implementation work tracks retained host buffers and refuses
retirement while any remain, including buffers surviving rollback or backend
loss. M3 must consume the final original host-custody API, not translate callback
return, cleared local arrays, native rollback or backend disappearance into a
discard acknowledgment. Independently retain a buffer through each such failure,
then require transition refusal until its original authorized final release is
proved. Releasing one publisher must preserve all siblings. These are shared
security integration dependencies, not a new Truss ownership or lease protocol;
the inspected component count does not close migration readiness.

### Managed host-custody checkpoint — 2026-10-09

A later read-only inspection supersedes the pending implementation description
above for the owner's routed-buffer component only. The owner now provides
`src/extensions/security/publication-custody.ts`: opaque instance-local handles,
owned JSON copies, sealing before retirement, retained buffers across backend
loss, and quarantine when consumer release fails. Native retirement is invoked
only after the sealed instance has no retained buffers. Callback success means
the host's declared final release; this component cannot observe arbitrary copies
outside that host contract. Truss must consume this owner implementation rather
than implement a parallel custody map.

The updated `pg-raw-persistent-drain-component.json` has SHA-256
`da04030b947af909903550742e3a72103559af3a547a005c129869fecf9eb162`,
status passed, 1,421 observations and all 90 recorded source hashes matching at
inspection. Primary, replay, sibling and fresh publications now traverse managed
host custody before native issuer retirement acknowledgment. Its consumer-failure
case receives an actual payload, rejects release, emits no retirement request and
leaves durable pending custody blocking revocation after child shutdown. Excluded
fixture teardown is not successful recovery. Truss did not rerun the native test.

The separate `publication-custody-browser.json` has SHA-256
`5fe9012cbbea8127d53821ef708fd0b4fe06a59b6982e3ac4f0b0b0dea986fce`,
status passed, 31 observations and all six source hashes matching. Its scope is
browser/Bun owned-copy and local-handle behavior; it does not prove native issuer
authentication, process recovery or complete backend acceptance.

M3/LM-P03 must now exercise the actual owner custody instance on the selected
migration path: quarantine after failed release cannot become a discard merely
because the enclosing migration rolled back or its process disconnected. Preserve
original recovery obligations and keep readiness closed until the owner procedure
proves settlement. The local component has no restart restoration or public
quarantine recovery API; those remain original-owner integration dependencies,
not permission for Truss to clear retained handles or invoke retirement directly.
Public broker authentication, general read enrollment, full writer closure and
L03 qualification remain outside both inspected receipts.


### M4 original attempt reconstruction and commit-loss schedule

Implement recovery through the existing request/attempt/receipt types and shared
registry, not through a framework ledger or a second migration identity. Capture
exact expected source/target preservation before execution and keep the same M1
route/profile tuple in every branch below.

1. Before any recipe submission, register and confirm durable custody of the
   exact original request, installed target context, original source observation,
   procedure/resource/transition pins and recovery reference. If that registration's
   acknowledgment is itself unknown, resolve its original registration attempt
   before submitting migration effects. A host-generated attempt ID alone does
   not establish registration or authorize native work.
2. Under the original dedicated transaction, apply every ordered registered step,
   retain actual step/preservation/target observations, prepare the immutable route
   receipt and marker/archive publication, and perform the governing final checks.
   No intermediate step receipt or target-looking marker independently opens
   runtime readiness. Security publication enrollment/exclusion/drain remains the
   existing owner's dependency.
3. Cut the actual original driver's COMMIT acknowledgment after submission. Retain
   original possible effects and resource quarantine. Stop consumer startup, keep
   the original recovery reference and do not invoke apply again merely because
   the framework retries its deployment callback. Losing the process cannot turn
   that uncertain route into an unsubmitted request.
4. On restart, restore the original request/recovery custody, including exact bytes
   and registered profile membership. Use reconcile for that original attempt under
   independently admitted current administrative/disclosure authority. Changed
   manifest/recipe/procedure bytes or another installation's receipt refuse
   correspondence; do not regenerate the request from current version numbers.
5. Obtain qualified original termination and settlement evidence. A complete original
   committed receipt/attempt observation establishes original commit under its
   admitted observation profile; an absent receipt alone does not establish rollback.
   A still-active backend, unavailable observation, incomplete receipt/archive or
   incomparable incarnation keeps recovery/readiness closed. Do not refund or reuse
   unresolved native/publication custody merely because the client restarted.
6. After original commit is confirmed, independently verify the complete current
   target inventory, data/codec/history compatibility and security/resource state.
   Return original commit plus current verification only when both admit. Current
   drift yields committed_unverified, not rolled_back or permission to rerun the
   route. Confirmed original rollback retains verified source state; any new attempt
   requires fresh original source/authority admission and original cleanup settlement.

| Independent fault branch | Required original observations and outcome |
| --- | --- |
| Recovery registration acknowledgment lost before recipe submission | No recipe effect; resolve the same original registration before eligibility. Framework callback retry cannot create a second effect-bearing attempt |
| Route committed, commit acknowledgment lost, process restarted | Same original request/attempt and immutable receipt; complete actual target preservation; reconcile submits zero recipes and supplies original committed evidence plus fresh verification |
| Route rolled back, commit acknowledgment lost | Original qualified termination/rollback and complete source preservation; no target receipt/publication. Mere marker/receipt absence is insufficient |
| Original outcome still unavailable after termination | Keep original recovery and readiness closed; no synthetic rollback, alternate-source route or duplicate apply |
| Route committed, then a required native routine/grant drifts | Original committed custody remains intact; fresh verification fails and target runtime stays closed. Restore/repair follows explicit qualified administration, not replaying the original upgrade |
| Framework fails after confirmed Truss commit | Framework status may fail independently; original route stays committed. On retry, fresh source/target verification and original receipt determine already_applied versus committed_unverified |

Retain exact original and later observations separately. Compare complete native
source/target data and effect inventories, recipe-submission counts and original
attempt references; framework status, table counts and version strings are supporting
facts only. These are executable test requirements for LM-T04/05/08 and M4/M5;
no registered original recovery service or populated route is qualified here.


## Inspection service prerequisite and adoption boundary

Before M3 dispatch, register `inspectionRequest`/`status` and
`verificationRequest`/`verification` from the portable inspection schema and
qualify LM-V01–06 through the exact original administrative procedures. Observe
complete matching source, same-version routine/grant drift, unavailable collection
and unchanged managed state independently. M2 must preserve their current-state
scope separately from HostRecoveryRegistry's original-attempt outcomes. A failed
inspection cannot trigger apply, bootstrap or a hidden repair.

M1 still requires a real populated source/target pair. Author source/target
preservation expectations before recipe implementation; inspection tests against
one admitted installation are useful prerequisites but do not qualify an upgrade
edge. The current component labels 0.15/0.16 are not stable released migration
versions. No generated source/target manifest is published as supported until
its full bundle/producer/security/resource correspondence and independent native
preservation/recovery evidence pass. M5's clean consumer demonstrates inspection,
explicit application and original reconciliation separately; a convenience deploy
wrapper cannot collapse unavailable, drift and commit_unknown into success.

### M4 reconciliation after a subsequent committed upgrade

LM-T04/08 must retain an original S-to-T attempt with a lost acknowledgment,
independently settle that attempt, then apply an admitted T-to-U route before
reconciling the retained S-to-T reference. Use two real populated registered
routes with independently frozen preservation expectations; a marker mutation
cannot stand in for the second upgrade. This schedule becomes executable only
when both routes and their original recovery procedures are qualified.

Original commit evidence still identifies S-to-T, its ordered recipes and its
immutable target observation. Reconciliation submits zero recipes, never rewrites
that receipt as S-to-U, and never restores T merely to reproduce the old result.
Observe U through a separate current status/verification request under freshly
admitted administrative authority. A valid original T receipt does not assert
that T is still installed or admit a T-only runtime against U.

Under the existing draft binding, `already_applied.currentVerification` must
actually verify the original target T. If the current installation is U and no
registered verification profile establishes the required T correspondence, retain
the confirmed original commit through `committed_unverified` with the actual
mismatch evidence. Do not manufacture a successful T verification from U's larger
version number, same major, or independently successful U verification. The
consumer may separately admit its runtime against U using U's actual compatibility
matrix; that admission does not change the old attempt's outcome or target.

Independent observations compare both complete immutable receipts, exact original
attempt references, recipe-submission counts, current U inventory and all retained
receipt/feed/history protections across both transitions. Include a changed old
request, an unavailable historical receipt and a U-compatible versus T-only
runtime. A missing historical proof remains unavailable; current U contents alone
cannot reconstruct whether the old route committed. These are additional planned
recovery controls, not support for a second migration edge or a new result API.


### M4 restore/fork identity separation

CONTRACT-008 retains the original source installation, epoch, incarnation and
trusted database/cluster target independently of native OIDs and copied marker
bytes. Extend LM-T04/08 with two explicitly admitted deployment targets whose
backup-derived tables, schema names, OIDs where reproducible, original request
and immutable migration receipt bytes are otherwise equal. One is the original
source of the attempt; the other is a restored or forked incarnation. Register
that distinction through the existing trusted deployment/restore identity
procedure, never by editing a receipt or inventing a second identity authority.

| Schedule | Required observation |
| --- | --- |
| Reconcile the original reference against the original target | The selected original-attempt procedure determines its outcome; actual receipt, target and current authority correspondence remain required |
| Present the same reference and copied receipt on the fork | Refuse original-target correspondence or leave it unavailable under the selected protocol. Matching version, bytes, OIDs or schema name cannot produce original commit evidence or `already_applied` |
| Lose the original target while the fork remains available | Preserve original recovery custody; fork availability cannot establish original termination, rollback or release of its native/publication obligations |
| Restore a snapshot predating the upgrade while retaining the original host recovery reference | Observe the new incarnation separately. Do not rerun the old request, infer rollback from missing receipt, or retarget the original attempt to the restored connection |
| Restore a post-upgrade snapshot with complete copied target inventory | Current restored-installation verification and original-attempt settlement remain separate. Readiness requires the admitted restore/incarnation procedure and current compatibility; a copied successful receipt cannot skip it |

Independently record trusted target/incarnation observations, original reference
membership, recipe-submission counts and native/publication custody. All lookup
branches submit zero migration recipes. Any subsequently authorized upgrade on
the restored installation requires its own freshly admitted original source and
request; it does not rewrite the historical attempt. No generic reset, receipt
rebind, restore provider or new migration result variant is selected here.
These cases become executable with M1/M2/M4's actual registered services and
independent restore identity evidence; copied fixture labels alone do not qualify
the separation.
