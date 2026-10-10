# Original operation ordinal issuer integration

This execution handoff applies CONTRACT-001 OC01–OC07 and CONTRACT-007's shared
executor/transaction issuer. It precedes the missing canonical observer bodies;
it adds no public transaction ID, database counter, session setting or authority
issued by a JSON field.

## Accepted host boundary — ADR-008

The owner accepts the [trusted embedding host and adapter](../02-design/adr/ADR-008-trusted-embedding-host.md).
Original Python/TypeScript issuer custody is a qualified trusted-host obligation;
PostgreSQL does not authenticate Python object identity. Native transaction,
privilege/current-authority, conflict, epoch/configuration and full-effect checks
remain required. Correct all four families with the original host-issued ordinal;
do not replace MAX with a new rollback-sensitive counter. The original driver
port must bind exclusive physical-connection/transaction custody and retain
uncertain attempts without reuse. This decision permits the integration experiment,
not readiness or relaxation of ordinary-writer enforcement.

## Verified conflict

The private runtime_admit_operation, runtime_admit_operation_with_asserted_origin,
epoch-context and configuration-context admission sources derive next_ordinal from
max(operation_ordinal)+1 over surviving registry rows. The exact native function
names remain those in their original files; the families are identified here
rather than renamed. Those components cannot supply OC01's original issuer.

The [native reproduction](../../../scripts/check-pgserver-operation-ordinal-frontier.py)
uses original base0.16 SQL and operation-admission.sql in one PostgreSQL16.2
transaction. Admission returns ordinal0; rollback to the preceding savepoint
removes its registry row; the next admission in the same actual top-level xid
returns0 again. The [receipt](evidence/design-audit/pgserver-operation-ordinal-frontier.json)
records contractConformant=false. Successful reproduction is evidence of a gap,
not a supported operation. Synthetic nonempty input bytes exercise allocation
only and establish no original artifact or mutation admission. That base reproduction does not execute the other families. Separate asserted-origin
epoch-context and configuration-context reproductions below establish the same
native conflict across all four families.

## Corrected composition requirements

The original shared executor issues a distinct monotonic ordinal for every
attempt under its adopted native transaction. Issue before native operation
submission and retain it in original attempt/control/recovery custody. Operation
savepoint rollback does not rewind the issuer or reuse an issued ordinal. Gaps
are permitted. Finalized earlier operations retain their ordinals and remain in
complete commit collection. Actual top-level transaction identity is separate
from ordinal and does not establish original savepoint/adoption lifetime.

Native admission consumes that original issued ordinal and issuer evidence; it
must not calculate an ordinal from row count, MAX, current unfinished state or a
fresh host object. An exposed numeric argument alone is not issuer authority.
Resolve and verify the original private executor/driver custody through the
selected existing producer port before effects. Current registry/parity checks
still independently refuse conflicts, unknown lineage or overlapping unfinished
operations. No DELETE, fake finalization or counter reset makes room for reuse.

Use exact canonical integer text and checked native bigint bounds in transport;
Python uses int and TypeScript bigint internally. Bound issuance/control/recovery
work and reserve containment before submission. Exhaustion refuses before effects
without overflow or automatic retry. A lost/unknown native result retains its
original issued ordinal and recovery reference; reconciliation cannot issue a
replacement or rerun the attempt.

The query ordinal in packages/pg-runtime/src/index.ts identifies driver submissions
within a lease. It is not the governing operation issuer: one Truss operation can
submit multiple queries. Do not bind the two counters by equal spelling or use a
new connection/query lease to reset transaction operation history.

## Implementation order and independent controls

1. Bind one original executor/transaction issuer and qualified driver mode under
   CONTRACT-007, with exact transaction adoption, savepoint and attempt custody.
   Keep application caller transactions separate from migration-owned transactions.
2. Correct all four admission families together to consume original issuer
   output. Preserve their distinct actor/asserted/epoch/configuration captures;
   do not route advanced contexts through the earlier incomplete base routine.
   Record the new exact routine/build/profile inputs and retain old receipts as
   historical component evidence.
3. Verify actual savepoint rollback after native admission, failed admission before
   insertion, earlier finalized operations, changed issuer/transaction custody,
   unknown outcome, full transaction rollback and bounded exhaustion. Independent
   expected ordinals must show nonreuse; native registry state alone cannot author
   those expectations. Prior finalized entries remain intact for commit checks.
4. Only then use the corrected admission/attribution dependency for unavoidable
   row/edge/catalog observers and full deferred transaction collection. Repeat
   original generation/capacity/journal/feed schedules on that same composition.

The selected native verification of private issuer evidence remains an engineering
integration output of the executor/driver and security composition. Existing
source-only or result-metadata hooks do not supply it. No additional product vote
is needed, and accepting a caller-provided ordinal as proof would weaken the
already agreed contract. The complete installer must refuse readiness for a
composition that retains the row-derived allocator.

## Implemented counter component

Private TypeScript operation-ordinal-issuer.ts and Python _operation_ordinal.py
now implement exact bounded issuance and original object-affinity checking, with
no reset/restore/rollback method. The six independently authored shared scenarios
cover burnt ordinals after rollback/failed admission, finite exhaustion, wrong
custody without consumption, and closed admission after cancellation/unknown
control/end. Python serializes issuance with a lock; TypeScript issuance is
synchronous. Native bigint bounds and exact host argument types are checked.

This counter is deliberately not exported as a public issuer or wired into the
old native admission functions. Creating an instance does not recognize a physical
transaction or grant authority. The qualified original adapter must retain exactly
one instance for its admitted original epoch, reserve enclosing control/account
permits before issuance, and bind its result to original savepoint/attempt custody.
Constructing another object cannot be a re-adoption or recovery procedure. Losing
that private state closes new admission until original reconciliation qualifies it.
The native MAX allocator conflict remains open until all four admission families
consume the original verified issuer output.

The [driver producer control binding](../02-design/contracts/reference-driver-producer-port.proposal.md#operation-issuer-and-savepoint-control-binding)
now specifies the missing reserveOperationControl → bindIssuedOperation →
submitOperationSavepoint boundary, original registry/account affinity and actual
confirmation requirements. It is a design handoff, not an implemented stock-driver
API. Its independently required fault schedules precede native allocator correction;
ingress/frame receipts cannot substitute for operation control confirmation.

## Original Python control-frame seam

The [local driver probe](evidence/design-audit/check_pg8000_local_control_native.py)
reuses the pinned pg8000 1.31.5 instance receiver and original complete-frame
correspondence rather than reading public cursor results. On pgserver0.1.4 / actual
PostgreSQL16.2 it captures BEGIN, SAVEPOINT, ROLLBACK TO, RELEASE and outer ROLLBACK
as five distinct fixed submissions. All ten independently expected CommandComplete
and ReadyForQuery frames match in order, including active/idle state. Startup ready
observation remains separate. No authentication or backend-key bodies are retained.

The [receipt](evidence/design-audit/pg8000-local-control-native.json) keeps
 driverPortQualified=false. Probe cycle labels are local instrumentation, not the
original issuer/epoch/account binding. Dependencies are reused from the existing
private pg8000 and pgserver environments. This evidence establishes a concrete
source/transport seam for original control capture, not lost-response handling,
finite pre-ingress heap accounting, savepoint authority, original outcome settlement
or TLS/current-person admission. Implement the original reservation/issuer binding
at this seam and qualify its complete independent controls before adopting it.

### Failure after original savepoint command capture

The [failure probe](evidence/design-audit/check_pg8000_local_control_failure_native.py)
injects a handler exception after capturing the original SAVEPOINT CommandComplete
frame and before its ReadyForQuery observation. The instance receiver quarantines;
a subsequent submission refuses without another send. Independent pg_stat_activity
observation still shows that same backend idle in transaction. A client exception
therefore did not settle the transaction or restore usable driver custody.

The probe explicitly closes its original socket, then separately observes backend
termination and absence of its earlier pending fixture write. This explicit probe
cleanup is not automatic replay or a production recovery procedure. The
[receipt](evidence/design-audit/pg8000-local-control-failure-native.json) preserves
 driverPortQualified=false. It qualifies this injected callback failure seam only,
not arbitrary network loss, original issuer/account/control permits, unknown COMMIT,
durable recovery registration or ordinary-person/TLS admission. Native pending and
later terminated observations remain separate from adapter quarantine.

## Per-family correction and preservation matrix

| Original routine | Existing capture that correction must preserve | Independent native continuation |
| --- | --- | --- |
| runtime_admit_operation | Context0.2: actual xid/ordinal, invoker/session identities and role OIDs, database/backend; six original artifact columns and group custody | Original base rollback reproduction currently returns0 twice. Corrected original issuance must return0 then1 in the same actual xid with no first registry row left. |
| runtime_admit_operation_with_asserted_origin | Context0.3 adds exact assertedOriginUtf8Hex and assertedOriginCaptureProfileHex; invoker identity remains separate from asserted origin | Fresh asserted-family reproduction also returns0 twice while preserving both independently expected fixture byte strings. Retain those bytes across corrected admission and forbid asserted actor substitution. |
| runtime_admit_operation_with_epoch_context | Context0.4 additionally retains installationId/sourceEpoch/targetIncarnation and original source-epoch profile/evidence bytes from runtime_lock_source_epoch | Qualify on original installed epoch custody: stale epoch/incarnation refuses before registry effects, but an already issued host ordinal stays consumed. Do not replace original epoch inputs with synthetic nonempty bytes. |
| runtime_admit_operation_with_configuration_context | Context0.4 plus separate operation_configuration row: original generation, key-reuse/journal modes, context digest, admission profile and configuration/binding/inventory bytes | Independently compare both rows and exact context digest. Rollback removes both; issuance does not rewind. Changed configuration refuses before business effects; no partial configuration capture or advanced-to-base delegation. |

The [new asserted-family receipt](evidence/design-audit/pgserver-asserted-operation-ordinal-frontier.json)
comes from a fresh disposable PostgreSQL16.2 run. Synthetic original byte fixtures
exercise capture only; originalOriginAdmissionQualified and contractConformant
remain false. It retains the complete captured contexts, source hashes and actual
same-xid observations. Rollback removes the entire namespace. The epoch and
configuration families still have source inspection only for this conflict; the
matrix does not claim their native rollback schedules ran.

For each corrected family, run native schedules for: rollback after successful
admission; admission failure before insertion; foreign original issuer/epoch;
unconsumed versus replayed original attempt; unknown control completion; exhausted
int64 issuer; and a previously finalized operation followed by a failed attempt.
Compare independent issued ordinals, actual registry/configuration effects and
retained exact context/artifacts. No automatic replay is allowed. Full outer
rollback may remove durable rows but cannot be interpreted as permission to reset
a still-live original epoch. A genuinely new admitted native transaction gets its
own issuer only through the original adoption protocol.

## Native control outcome correspondence

The [private typed control binding](../02-design/contracts/bindings/truss-operation-control-v0.1.proposal.d.ts)
now separates original reservation, issued ordinal, bound control, confirmed
savepoint and recovery identities. Only the confirmed branch can enter the native
admission dispatcher. Confirmed failure and unavailable completion retain recovery
custody but expose no confirmation; a pre-submission refusal remains distinct.
The original counter privately produces the issued token after reservation; its
text value cannot construct that token. All post-issuance failures burn the ordinal.
The producer registry must enforce affinity and one-use semantics at runtime:
TypeScript branding is not a security boundary or native verification mechanism.

The accompanying typecheck includes independently specified rejected uses for a
bound-but-unconfirmed control, any nonconfirmed result, caller-constructed issuer
or confirmation objects, and JavaScript numeric transport. This is a concrete
adapter implementation interface, not an implemented producer or evidence that
native admission is qualified. Full native verification, accounting, registered
control correlation and the four SQL corrections remain required. Escaped adapter
exceptions retain the pre-registered recovery association and unavailable status;
they never make a consumed submission permission reusable.

The [server-rejection probe](evidence/design-audit/pg8000-local-control-rejection-native.json)
now provides the independent negative outcome alongside the happy-control and
interrupted-callback probes. A deliberately malformed `SAVEPOINT` submission
produces an original ErrorResponse containing SQLSTATE42601 followed by exact
ReadyForQuery E, with no CommandComplete. Independent pg_stat_activity observes
the same backend idle in transaction (aborted). The receiver quarantines and a
new submission refuses without another send. Explicit socket close is separately
followed by observed backend termination and absence of the pending fixture write.

| Observed candidate boundary | Truthful interpretation for original integration |
| --- | --- |
| Original expected command and ready frames for a registered valid control | Candidate successful frame correspondence. Original transaction/attempt/savepoint confirmation and account custody are still required before admission. |
| Correlated ErrorResponse then ReadyForQuery E, no successful command completion | Confirmed failure of that submitted negative control, with the outer transaction aborted but not yet rolled back/settled. Preserve issued ordinal; permit no registry/business admission. |
| CommandComplete captured, callback fails before ReadyForQuery | Completion is unavailable to the original host protocol. Backend can remain live and pending. Close admission, preserve original recovery custody and do not resubmit. |
| Later explicit transport closure plus independent backend termination | A separate containment observation. It is not implied by client quarantine, exception, failed-transaction status or uncommitted-row invisibility. |

The rejected malformed command is a negative protocol fixture, not an admitted
registered savepoint definition. This probe uses local trust and reused private
driver dependencies; driverPortQualified remains false. It supplies neither
original account/control permits nor lost-COMMIT/durable recovery qualification.
Complete producer integration must preserve these distinct outcomes rather than
classifying every exception as an unknown result or an already settled rollback.


## Epoch-context rollback reproduction

The [epoch-context probe](../../../scripts/check-pgserver-epoch-operation-ordinal-frontier.py)
executes the original source-epoch0.16 layout, source-epoch lock and epoch admission
routine against pgserver0.1.4 PostgreSQL16.2. It seeds an explicitly administrative
marker/epoch fixture before the operation savepoint. Both admissions observe the
same actual top-level xid and return ordinal0 after rollback removes the first
operation. The [receipt](evidence/design-audit/pgserver-epoch-operation-ordinal-frontier.json)
records contractConformant=false and verifies complete rollback removes the namespace.

Both returned contexts preserve the expected installation, epoch and incarnation,
original profile/evidence bytes, and asserted-origin/capture-profile bytes. These
checks constrain the all-family allocator correction: replacing allocation must
retain the advanced context capture. They do not admit those fixture bytes as
trusted installation authority or qualify a protected producer. The configuration reproduction below extends these controls to its separate row.


## Configuration-context rollback reproduction

The [configuration probe](../../../scripts/check-pgserver-configuration-operation-ordinal-frontier.py)
adds the original operation-configuration storage and configuration admission
routine to the same rollback-only PostgreSQL16.2 administrative epoch fixture.
An explicit installation-admission fixture contains generation7, forbid/engine
modes, binary configuration bytes including NUL and FF, and distinct binding and
inventory bytes. These are synthetic capture inputs, not accepted installation
artifacts or registered configuration meaning.

The [receipt](evidence/design-audit/pgserver-configuration-operation-ordinal-frontier.json)
shows ordinal0 reissued after rollback in the same native xid. Both separate
configuration rows retain every fixture value and the exact admission-profile
bytes. Their context digests independently match SHA-256 of returned original
context bytes, without JSON reserialization. Full rollback removes the namespace.
All four allocator families now have native conflict evidence; none is corrected
or qualified by these reproductions. The implementation handoff remains to bind
original issuer custody and correct all four families together, preserving their
individual capture requirements and the separate configuration row.


## Python one-use admission custody component

Private `_operation_admission.AdmissionCustody` now captures the original
producer and synchronous verify/admit callbacks. Registration retains original
confirmation object identity under a caller-selected finite enclosing capacity;
it supplies no native confirmation factory. A ticket is recognized only by this
registry. Original confirmations cannot register twice; capacity is cumulative
and never refunded. Dispatch consumes permission before verification/native
callback and rejects copied, foreign, consumed, closed or reentrant entries.

Verification must complete synchronously with no value or raise; asynchronous
functions/callable objects and returned awaitables cannot grant permission.
Generator functions/callable objects and returned generator objects also refuse:
the port cannot defer native work until iteration after the admitted call. Returned
generators close without executing their suspended bodies.
Unexecuted coroutine results close before refusal. Escaped verification/admission
failure closes this custody and retains all original entries for the enclosing
host recovery protocol; no reset/retry method is exposed. Cancellation/expiry can
close custody through the original producer. Actual native authority/lifetime,
account and outcome classification still belong to the original qualified port.

Six synthetic Python test methods verify original input correspondence, repeated/
copied/foreign ticket refusal, no repeat after either callback failure, closure of
pre-registered later tickets, reentrancy, finite capacity and async/nonvoid check
refusal, plus deferred admission refusal with no deferred native effect. They
establish host registry behavior only, not native authority or an
implemented protected writer. Binding this component to original control/ordinal
and native verification remains required; the four SQL allocator corrections are
still outstanding. The source change adds a twelfth package module; earlier
installed eleven-module/36-test receipts remain historical until rebuilding and
running the expanded41-test suite.


## Issued-ordinal native candidates

The separate `packages/postgresql/native/issued-operation-admission/` sources now
add the host-issued bigint to all four original families together, preserving
their capture paths and unfinished-operation checks. Native state rejects invalid
negative/null or conflicting surviving ordinals; original host custody supplies
nonreuse after rollback. Legacy sources remain historical; a complete selected
installer must exclude executable legacy allocator overloads. Native execution
and actual Python/driver binding are not yet qualified. Run the original rollback/
prior-finalized/epoch/configuration/uncertain controls on corrected16.15 next.


## Current issued-ordinal execution checkpoint

The four separate issued candidates now run on corrected16.15 with actual source
Python counter issuance before savepoint submission. Each retains successful
ordinals0/1 in the same native transaction across rollback, burns ordinal2 on
actual22023 admission refusal, and next admits3 after rollback. Separate
configuration capture independently observes exact original fixture bytes and
context digest, with removed configuration rows after rollback. Original row-MAX
reproductions above remain historical; candidate implementation is no longer
wholly absent. These administrative/synthetic-artifact component receipts do not
qualify original driver/security/resource/finalizer composition or readiness.

## Minimum security owner handoff for initial operations

The [read-only interface review](evidence/design-audit/minimum-security-owner-interface-review.json)
pins current owner worktree exports and procedural source, including dirty-status
flags. Policy evaluation/read registration/authority guard/write evaluation/
disclosure exports are owner APIs, not proof of an adopted native PostgreSQL port.
Use existing owner case IDs to specify the exact required subset:

| Initial capability | Required owner handoff and evidence |
| --- | --- |
| Administrative installation | Exact installer/excluded-assessor identity, protected routine/role/grant inventory and ordinary-role separation; B05/B06/B09/B11/B12/B14 plus activation rollback L12. No application authority from an administrative fixture. |
| Key/edge and compiled reads | Authenticated subject mapping, complete native owner/fact mapping, original registration and authority lifetime, protected output; applicable B01–B04/B10/B13/B15 and L03–L06/L11/L13/L14. Actual same-local-name/document qualification and empty/hidden cases remain required. |
| Apply/import/dry-run | Registered old/new-state and field-write authority with effect/publication lifetime; L01/L02/L03/L11/L12 and relevant bypass/inventory cases. Retain denied-operation zero effects and native actor versus asserted-origin separation. |
| Unsupported masks/history/streaming | Explicit pre-effect refusal under B07–B09/L04/L07–L10 until exact supported interpretation/native subset is adopted. An unsupported profile cannot weaken reports or expose protected facts. |

This table stages the first installed capabilities; it does not delete any owner
acceptance case or Truss full-release obligation. Applicable resource/performance
B16 and complete custody B12 remain required for every advertised profile.
The concrete packet must name interface/build/model/policy/mapping/native profile
pins, actual roles/routines/installation procedure and original case receipts.
Truss owns adapter composition and native issuer wiring, while the owner retains
policy meaning, authority/current-fact resolution and protected publication.
No cross-chat message was sent and no unfinished API was adopted by this review.


## Shared Python issuer registry

Private `OperationOrdinalRegistry` now binds one retained issuer per original
transaction token within one trusted physical-connection/producer registry. A
second facade receives the identical issuer. Ended transactions retain the closed
issuer; rebinding cannot restart at zero, and retained bindings never refund the
explicit enclosing capacity. Connection closure closes every issuer. The trusted
adapter must create/share the original registry and supply genuine adoption
tokens; the component does not discover or authenticate native transaction state.

Two new component methods cover shared facades, ended/rebound custody, distinct
transaction lifetime, cumulative capacity, foreign connection/producer and close.
All44 current source Python tests pass in the corrected local runtime environment;
the boundary checker still passes51 imports. The native configuration schedule
now shares this registry over the actual psql process and preserves0/1/3 issuance
and exact captures. This is source-component/local native fixture evidence, not
a rebuilt-wheel claim, qualified driver port or complete original admission.

## Installed shared-registry wheel checkpoint

The rebuilt Python wheel contains all12 current modules, including the shared
registry. Installed/wheel/source module bytes match, and all44 tests pass with
execution outside the checkout using the reused corrected pgserver environment.
The separate `python-shared-registry-installed-suite.json` receipt preserves
module/test hashes, dependency versions and original suite output. Earlier
42-test wheel receipts remain historical. This establishes packaged component
behavior on macOS arm64/Python3.11/PostgreSQL16.15; it does not qualify clean
dependency resolution, public installation/migration APIs or a complete engine.
