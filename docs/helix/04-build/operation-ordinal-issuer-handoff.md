# Original operation ordinal issuer integration

This execution handoff applies CONTRACT-001 OC01–OC07 and CONTRACT-007's shared
executor/transaction issuer. It precedes the missing canonical observer bodies;
it adds no public transaction ID, database counter, session setting or authority
issued by a JSON field.

## Current composition entry point — 2026-10-10

Use the [current frontier](remaining-design-handoff-audit.md#current-execution-frontier--2026-10-10)
for the verified component/dependency matrix. Current source passes114; the separately pinned installed wheel passes112
and predates resource registration preflight. All25 wheel modules match its original bytes. The older installed wheel71 is historical. Actual complete touch/cohort reads and shared
operation correspondence exist; protected original capture/authority, full
resource and semantic bodies remain missing. The ordered PA01–PA05 packet below
remains the release path. Later component sections supply scoped evidence, not
alternate readiness gates or another public API.

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


## Shared registry across four native families

The three new `issued-operation-ordinal-{base,asserted,epoch}-shared-registry-native.json`
receipts run the current unchanged producer and shared registry on corrected
PostgreSQL16.15. Each observes the same actual transaction with issued0/1/3,
ordinal2 burnt by native invalid-kind refusal, rollback removal and full-store
preservation for NULL/negative/unfinished controls. Together with
`issued-operation-ordinal-shared-registry-native.json` for configuration, these
cover all four administrative component schedules. Their false full-driver,
full-family-qualification and readiness flags remain deliberate: running each
family does not establish complete original authority/account/finalizer wiring,
ordinary-role execution or all-path admission. The Python design now includes
the registry state transitions, local lock order and remaining adoption obligations.

## Native registry projection through the Python decoder

The four `issued-operation-ordinal-{base,asserted,epoch,configuration}-registry-decoder-native.json`
receipts now retain five original observations per family on PostgreSQL16.15:
admission0, rollback to an empty registry, admission1, a second empty rollback,
and admission3 after invalid-kind ordinal2 was burned. Each actual xid and complete
16-cell row is passed through the private Python structural decoder. Original and
decoded rows are retained without reconstruction of context or byte carriers.
Existing exact context/configuration and native refusal controls still pass.

The checker wraps the original second SELECT from the documented
[registry projection](../02-design/contracts/row-operation-registry-observation-v0.1.proposal.sql)
in a JSON aggregation for the actual psql fixture transport. It retains the exact
wrapper SQL and original projection/decoder/source hashes. Column order comes
from the declared decoder columns; SELECT command and affected-row metadata are
fixture-supplied, not original PostgreSQL protocol descriptor/completion evidence.
This therefore establishes native cell/projection compatibility across the four
families, not original positional driver framing, complete observation termination,
ordinary-role access or OC02/OC06 authorization. Empty assigned registries remain
structural observations and cannot grant a write or classify transaction settlement.

Complete driver integration must independently validate the original descriptor,
command/completion, byte/work limits and same transaction/cut before using these
cells for operation selection. Native account/security/finalizer composition and
atomic installer readiness remain required; no result here supplies a commit proof.

## Same connection, distinct top-level transaction fixture

The `issued-operation-ordinal-{base,asserted,epoch,configuration}-transaction-reuse-native.json`
receipts extend the native schedules on the same psql process/connection. After
the first transaction's explicit ROLLBACK, an actual observation returns an
unassigned xid and absent fixture namespace. The trusted fixture then ends the
original registry binding. Its old issuer refuses with closed, and rebinding the
old token returns that same permanently closed issuer.

A distinct fixture token receives a different issuer, while native BEGIN/setup
and admission on the same connection produce a different actual xid with ordinal0.
The complete registry projection decodes that new row; the earlier issuer still
refuses. A final rollback and independent connection verify namespace absence.
The original0/1/3 and burned2 schedule, refusal controls and exact context captures
remain in each receipt. The registry's finite cumulative binding capacity is two;
ending the first binding does not refund it.

This is a trusted administrative lifetime fixture, not an implementation of the
original adapter adoption protocol. Its host constructs the new token, and its
psql JSON wrapper supplies command metadata; no complete descriptor/control-cycle,
account, ordinary-role authority or unknown-settlement observation is inferred.
In particular, the post-rollback unassigned xid alone does not authorize production
connection reuse. Qualified driver confirmation, original cleanup/recovery and
framing must establish the full reuse gate from the producer handoff. Lost COMMIT,
backend replacement and unresolved prior attempts remain separate unrun exits.

## Complete native cell expectation

The four `issued-operation-ordinal-{base,asserted,epoch,configuration}-complete-cell-oracle-native.json`
receipts strengthen these schedules by comparing every decoded cell. Expected
definition/input/prestate/candidate/obligation/group-custody hex comes from the
independent original literal fixture arguments01/02/03/04/05/06; admitted phase,
generation0 and nullable generations/result have independently stated expectations.
Context hex is compared with a separately correlated original native admission
observation, whose nested identity/configuration fields retain their existing
checks. This is correspondence between two native observations, not an independent
complete context producer or authenticity proof. The receipts retain the full
expected/original/decoded rows and this expectation basis.

All four families pass the complete-cell comparisons at0/1/3 and the distinct
new-transaction0, plus both empty savepoint rollback observations. Swapped payload
columns can no longer pass merely because ordinal, phase and hex shape match.
Original descriptor/completion, bounded ingress/account, ordinary authority and
full installer/finalizer qualification remain unchanged open obligations.


## Original connection/control producer candidate — 2026-10-10

The private [producer source](evidence/design-audit/pg8000_original_control_candidate.py)
now composes the existing installed Python issuer/account with original pg8000
1.31.5 instance handlers on actual PostgreSQL 16.15. It adopts an already assigned
transaction, verifies original exact xid text and CommandComplete/ReadyForQuery
frames, reserves outgoing savepoint payload capacity before permanent ordinal
issuance, and publishes only its own confirmed savepoint object. A nonblocking
invocation lock rejects overlapping calls. Exclusive physical-connection custody
is still a trusted host premise, not a sandbox against direct host SQL.

Attempt records retain ordinal, actual xid, fixed control SQL and phase before
submission. Confirmed rollback retains the original record and spent ordinal;
uncertain control completion closes issuer/account admission and retains
completion_unknown. A copied confirmation cannot dispatch. Closure deliberately
does not assert native termination or roll back the host's adopted transaction.

The [current native receipt](evidence/design-audit/pg8000-original-control-custody-native.json)
passes fifteen independent observations across four actual connections: caller
work preservation, ordinals0/1 across savepoint rollback, retained prior attempt,
copied-object refusal with no submission, exhaustion before another savepoint,
changed actual transaction refusal, uncertain handoff/no retry and independently
observed live backend after quarantine. The post-execution handoff injection is
not arbitrary network loss. The initial thirteen-observation receipt and both
original source versions are preserved separately; their archived bytes match
the original pins. No test or qualification count is summed across versions.

This moves original control/issuer composition beyond separately supplied numeric
arguments, but is not the released driver or native operation authority. Next
consume these exact confirmations through the existing one-use admission custody
and all four issued native context families, preserving their full artifact/actor/
epoch/configuration checks. Qualify failure/cancellation, original account/work/
containment, registry attribution, security-owned current authority and original
recovery/settlement before the seven bodies and complete installer can publish
readiness. Do not install this evidence-directory candidate as a public API or
replace the owner's security interface with its administrative fixture.


### Completed native rejection versus unavailable completion

The original candidate incorrectly closed its receive account for a complete
native statement rejection, preventing qualified operation-local rollback. The
[retained counterexample](evidence/design-audit/pg8000-aborted-control-counterexample.json)
records six independently expected observations: division-by-zero22012, actual
ReadyForQuery E, closed account, no available local rollback/control submission,
and an independently observed live aborted backend. Earlier producer/checker
bytes are archived and still match their original receipt pins.

The corrected private instance invokes the pinned original CoreConnection message
loop, retaining original ErrorResponse/context/error identity and matching
ReadyForQuery E from that same invocation. Only this completed native rejection
keeps the receive account open for original containment. Other failures still
quarantine the file/account. SQLSTATE alone does not prove completion, classify
a business refusal, permit retry or grant current authority. Original native
transaction-end/boundary observations invalidate the adopted control scope; an
ordinary changed-boundary refusal now emits no native inquiry.

For this confirmed aborted state, rollback-to is the first submission: no xid
query, restoration or release enters the aborted transaction. Original rollback
command and ReadyForQuery T must match; then reobserve actual xid before release,
confirm release and restored xid, and retain the failed original ordinal. The
[recovery receipt](evidence/design-audit/pg8000-aborted-control-recovery-native.json)
passes nine observations including caller sentinel7 rather than failed value9,
settled attempt0 and next ordinal1 in the same actual transaction. The separate
[current regression](evidence/design-audit/pg8000-original-control-after-abort-native.json)
passes fifteen original control/custody cases, including uncertain post-execution
handoff without retry. Those fixture counts are not full driver qualification.

This correction is a prerequisite for native admission-error containment, not
completion of it. Separate pre-reserved cleanup ingress/outgoing/work/containment
capacity, complete handle/ancestor invalidation, interrupted error-before-ready
controls, actual four-family admission, security authority and native recovery
remain required. The current bookkeeping account cannot manufacture an earmarked
cleanup lane after normal capacity is exhausted. Preserve that profile gap rather
than advertising the candidate as a released executor.


### Shared original issuer and savepoint lifetime

The preceding producer still created a fresh registry on facade construction.
The current candidate binds the registry, actual transaction token, invocation
lock, attempt inventory and handle inventory to the original connection. A second
compatible facade reuses that same issuer rather than restarting at0. Actual
connection-file/account/producer affinity must match before construction can
submit SQL. Exact ordinal-profile mismatch or changed native epoch cannot create
a replacement binding. The candidate retains one adopted epoch per connection;
full connection reuse remains a later qualification output.

The same connection owns a cumulative participant namespace registry. Names now
follow CONTRACT-007's `truss_sp_` +32 lowercase hex namespace + `_` + positive
canonical counter recipe. The positive counter is the issued operation ordinal
plus1; original operation ordinals remain0-based bigint text. Compatible facade
construction consumes distinct namespaces while sharing the nonrewinding issuer.
The trusted host must honor this reserved namespace; predictable names are neither
authorization nor a guarantee against arbitrary host SQL.

After independently confirmed rollback-to and restored original xid, later live
handles across all registered participants become invalidated before release.
Their original records remain retained. Unknown ancestor rollback keeps target
rollback_unknown and affected live descendants ancestor_rollback_unknown; shared
admission closes rather than treating either as a confirmed invalidation or
allowing another facade to resume. Actual original names/ordinals are retained
in producer custody, not selected again from mutable caller handle fields.

The [lifetime receipt](evidence/design-audit/pg8000-savepoint-lifetime-native.json)
passes fourteen native observations on16.15: shared ordinals0/1, distinct exact
participant names, shared inventory, caller sentinel7 after ancestor rollback,
cross-participant descendant invalidation, next ordinal2, expired-handle refusal
without SQL, foreign-account refusal without spending either account, and unknown
ancestor/descendant custody with no peer resumption and an independently live
backend. [Control regression](evidence/design-audit/pg8000-original-control-shared-lifetime-native.json)
passes fifteen cases and [native error recovery](evidence/design-audit/pg8000-aborted-control-shared-lifetime-native.json)
passes nine separately scoped cases. Earlier original producer/checker bytes are
archived with matching historical pins.

This corrects shared-issuer and descendant-lifetime defects before four-family
admission. Generic explicit rollback-only/release-only public handles, complete
host stack/depth observation, pre-reserved cleanup and bounded full native work/
containment remain required. The candidate's combined rollback-and-release helper
does not implement the complete public SavepointHandle protocol or publish driver
readiness. Current security and complete installed routine/inventory gates remain.


## Original four-family admission composition — 2026-10-10

The private original-driver admission candidate now connects confirmed native
savepoints to the installed one-use admission custody on the same physical
connection. All facades share the issuer, confirmation inventory and admission
custody; admission requires the latest live boundary. Payload reservation precedes
SQL encoding, and original native context cells remain authoritative.

[The native receipt](evidence/design-audit/pg8000-four-family-original-admission-native.json)
records 92 observations on PostgreSQL16.15 across base, asserted-origin,
source-epoch and configuration admission. Each family verifies complete original
context and registry cells, refuses confirmation reuse before further SQL,
rolls back admitted registry/configuration rows, and contains an actual SQLSTATE
22023 rejection by rolling back first from ReadyForQuery E. The next operation
uses ordinal2 after rolled-back ordinals0 and1; earlier caller data and the
original transaction ID survive. There is no automatic retry. The original
DatabaseError is retained; successful local containment does not classify a
business refusal or establish complete healthy-scope authority.

The shared locked rollback helper also passes the
[14-observation lifetime regression](evidence/design-audit/pg8000-savepoint-lifetime-after-admission-native.json)
and [nine-observation abort-recovery regression](evidence/design-audit/pg8000-aborted-control-after-admission-native.json).
The before-admission original control source is archived alongside the candidate
so prior receipts retain their exact producer bytes.

This is administrative local evidence using six synthetic artifact byte strings.
It does not qualify their meaning, ordinary-person isolation/origin, current
security, the complete allocator/native-work and pre-reserved cleanup profile,
seven native bodies, finalization, commit cohorts, journal/feed/receipts or ready
publication. Driver qualification and installer readiness remain false; no
acceptance criteria are promoted. The next implementation composition must add
original artifact/authority admission and the protected native guard inventory
before exposing an installed mutation API.

## Protected admission execution packet — 2026-10-10

The [actual admission/elevation receipt](evidence/design-audit/admission-elevation-native.json)
qualifies the current invoker guard and original context preservation, with ten
PostgreSQL16.15 observations. It does not qualify ordinary protected admission.
Use this packet as the next integration item rather than further treating capacity
helper coverage as progress toward a usable mutation API.

### Destination and ownership

Keep host attempt/ordinal/confirmation custody in the existing private Python
`_operation_admission` boundary and original driver adapter. Keep installed native
admission realization under `packages/postgresql/native/issued-operation-admission/`.
Preserve all four original source families and their separate artifact carriers.
The protected realization must be a distinct explicitly versioned profile when its
actor-capture or callable contract differs; do not replace the 0.2 invoker source
or weaken its nested-DEFINER refusal. No new public operation API is implied.

Truss owns physical-connection affinity, original attempts and byte carriers,
installed identities/ACL reconciliation, native operation effects and containment.
The security owner owns authenticated subject mapping, old/new write authority,
current-fact admission and protected publication lifetime. UMF owns the admitted
metadata/key/value semantics; Weft owns compiler obligations and lowering. Consume
exact original owner artifacts at these seams, without a second resolver/parser.

### Ordered implementation outputs

| Order | Concrete output | Exit evidence |
| --- | --- | --- |
| PA01 | An original entry/capture/writer call map for each of the four families, showing the actor before capture, every elevation and the actual installed owner at every native write | Actual function bodies/signatures, original context-version meanings, native role OIDs and effective grants; reconcile intended and installed routes in both directions under the protected-access closure algorithm. A source-only graph leaves this item incomplete. |
| PA02 | A protected capture-to-writer protocol that retains original invoker context and binds it to the original attempt, actual xid/session/database/backend, installed generation and admitted subject | Demonstrate that caller JSON/GUC labels, copied context, another attempt or a different installed wrapper cannot authorize registry insertion. Native registration and trusted-host custody have distinct evidence; neither substitutes for the other. No direct consumer INSERT/UPDATE grants. |
| PA03 | Original owner authority/artifact admission before business effects, with all applicable epoch/configuration/profile checks | Exact owner interface/build/policy/mapping/target pins, complete original obligation inventory and immutable backend declaration/parameter correspondence. Unsupported or unfinished owner paths refuse; equal names/version labels are insufficient. |
| PA04 | One original submission through Python confirmation and one-use custody into each protected family | Preserve issued gaps and original result/context bytes, complete registry/configuration parity and actual physical connection; source-family artifact semantics remain distinct. No advanced-family fallback to the base routine. |
| PA05 | Protected native observation/finalization and full transaction completion | Implement all seven registered semantic bodies, full original contributors, reservation/release/cache composition, journal and current feed union. Native ordinary-role complete effects, denial/rollback and acknowledged/unknown settlement evidence precede API publication. |

PA01–PA04 are not yet execution-ready for a public release: the original protected
capture/writer protocol and actual owner subject/current-authority contract are
missing. Implementing the installed inventory and tests can proceed without
selecting policy semantics. PA05 retains the complete story/criterion scope and
cannot be replaced with a successful synthetic artifact insertion.

### Independent native acceptance matrix

Run against the actual installed candidate using separate ordinary login and
integrity-owner roles, the original Python physical-connection adapter and all four
families. Administrative setup is allowed only outside the measured operation.
Retain complete source/profile pins and actual effects before/after each case.
These are planned scenarios, not passed receipts.

| Case | Original scenario | Required observable outcome |
| --- | --- | --- |
| PA-N01 | Ordinary login performs an authorized protected operation | Caller identity remains original; registry/business writes execute only through the registered private chain; complete result remains pending until host commit acknowledgement. |
| PA-N02 | Host uses an explicitly granted native SET ROLE before admission | Preserve distinct session and acting-role names/OIDs; owner mapping must admit the subject interpretation. RESET ROLE or a role change cannot reuse earlier original admission. |
| PA-N03 | Execute from a distinct unregistered DEFINER wrapper, including one with the same apparent name | Refuse before registry/business effects; no caller or owner substitution. Retain the already issued ordinal and original error. |
| PA-N04 | Call every private writer/helper directly as the ordinary role; attempt direct registry/configuration/touch writes | Native effective privileges deny all unadmitted routes. Matching source function names or synthetic bytes do not bypass the boundary. |
| PA-N05 | Copy an admitted context into another attempt, transaction or physical connection | Refuse before effects; neither context bytes nor a digest alone authenticate original attempt custody. |
| PA-N06 | Change body, owner, private ACL, search path, dependency or installation generation | Reject the affected original profile before publication; missing and extra reachable dependencies are independently detected. |
| PA-N07 | Change epoch/configuration after capture; submit each advanced family | One refusal, zero business effects, no silent base-family delegation and no internal retry; original issued ordinal stays burned. |
| PA-N08 | Deny old-state, new-state or individual field-write authority | Entire operation refuses under the original owner interpretation. No partial canonical/key/edge/journal/feed/receipt effect or protected diagnostic disclosure. |
| PA-N09 | Admit, roll back the original savepoint, then submit another operation through another facade | Native rows roll back; all facades share the issuer and next ordinal advances. Earlier successful outer work and original xid survive confirmed local containment. |
| PA-N10 | Lose ready/commit acknowledgement or cancel while native completion is unavailable | Close new admission, preserve original recovery/settlement custody and avoid retry; do not classify unknown completion as success or confirmed rollback. |
| PA-N11 | Repeat early constraint checking, then mutate again and commit | Every final contributor is checked under the current full scope; no first-check cache bypass, unfinished reservation or partial journal/feed union. |
| PA-N12 | Spoof asserted origin; exercise legitimate original origin independently of native caller | Preserve exact original asserted-origin bytes/profile, qualify attribution authority separately, and never substitute origin for authenticated person or installed owner. |

Use the existing ten-check receipt only as PA-N03 boundary evidence for the actual
invoker prototype and read-only context preservation. It does not pass these full
matrix cases. Shared B001–B015, all 45 stories/167 criteria, native corpus,
interchange and deployment profile gates remain mandatory.

### Configuration, diagnostics and analysis

Select the complete immutable installation/owner/codec/resource tuple once per
original admitted operation; no mid-operation configuration reload or permissive
fallback. Public configuration must not expose arbitrary native callable names or
SQL. Original profile drift is an explicit refusal, not an automatic repair.

Report bounded stage/refusal identifiers and correlation under the existing
observability contract. Keep actor/context/policy/original input bytes out of
ordinary telemetry and errors; retain protected evidence only under its governing
authority and retention profile. Measure each repeated native check and cleanup
against the original account; coalescing does not erase actual work.

Formal analysis should distinguish original caller, installed execution owner and
asserted origin as separate identities, and show attempted transitions cannot
create authority or reuse an ordinal after rollback. Connect each model transition
to the actual installed source/native matrix case. An abstract invariant or an
owner's compiler lineage proof cannot establish the missing protected native
handoff, write authority or publication lifetime.

## Python contributing-operation syntax profile

The private `_acceptance_json.decode_row_operation_json` now provides an explicit
proposed 8-MiB numeric-free syntax profile for the original touch contributing-
operation carrier. It shares the strict duplicate-key/Unicode scanner with the
unchanged 1-MiB acceptance profile, with a fixed 40-million logical-work ceiling;
node/depth/array limits remain 100,000/128/4,096. The
[source regression receipt](evidence/design-audit/python-row-operation-json-source.json)
records 76 passing Python source tests, including five focused full-byte-bound,
profile-separation, ordered-identity, hostile-grammar and array/input controls.

Syntax decoding does not admit the closed body, profile/artifact hashes, unique
operation identities, contiguous touch-local positions or full original native
registry/effect/authority correspondence. The ordered-identity witness deliberately
uses an incomplete body to prove only that syntax preserves positions 0/1 and
identities representing native 7/11; it is not a valid admitted custody manifest.
The host retains original immutable bytes rather than reserializing the decoded
projection. Caller-supplied identity strings remain unauthenticated.

Next compose the closed original body validator and actual original registry
resolution at the canonical observer boundary. Retain independent full-row native
framing limits: an 8-MiB JSON body does not imply the entire row fits the 8-MiB codec
ceiling after its other cells and framing overhead. Logical scanner work does not
qualify actual allocator/decoder workspace, deadline or original account admission.
No public API, installed-wheel result or seven-body readiness follows from this
private source component.

## Closed Python custody-body projection

Private `_row_operation_custody.decode_row_operation_custody` now composes the
8-MiB syntax decoder with the existing closed body/artifact/profile grammar.
It verifies protocol constants, required members, artifact base64 byte/hash
correspondence, unique operation identities, contiguous touch-local positions and
one through 1,024 operations. It retains the original immutable byte object and
frozen nested views; no JSON reserialization or native identity renumbering occurs.
The [source receipt](evidence/design-audit/python-row-operation-custody-body-source.json)
records 79 passing Python source tests, including exact immutable projection,
ten independently mutated body refusals and the operation-count boundary.

This supersedes the prior missing closed-body parser component, not original
semantic/native admission. A parsed profile/hash/identity is data, not authority.
The fixture's local 0/1 versus native 7/11 identities remain illustrative strings;
actual registry resolution and complete original contributor/effect-readiness
checks must still be wired to the canonical observer. The parser does not interpret
artifact value/prestate/owner meaning or classify empty bytes as absent state.
Original parameter/profile/body bytes remain necessary for that later admission.

No native row fit, original resource-account/allocator/hash/work containment,
installed-wheel interchange or semantic body readiness follows from this source
suite. Next compose original registry lookup and owner-authority correspondence
under the protected installed chain, without treating this decoded view as a seal
or allowing caller-supplied identities to authorize effects.

## Original address-to-registry integration sequence

CONTRACT-001 already selects the proposed four-string address
`["truss-row-operation-address/0.1.0", installationIdentity, originalWriterXid, operationOrdinal]`.
Under that exact profile, each manifest entry's operationIdentity and
nativeGroupCustodyIdentity must carry the same complete original address string.
Do not invent UUID aliases, derive identity from touch-local position, or parse an
arbitrary label into an executor ordinal. The closed Python body validator does
not yet enforce this profile; its native-7/group-0 fixtures are body controls only.

Implement the remaining integration in this order:

| Step | Original input and concrete output | Independent check |
| --- | --- | --- |
| RC01 address codec | Original registered installation identity and native xid/issued ordinal strings; exact compact four-string JSON address under an explicitly pinned scalar spelling procedure | Domain/arity/type/native integer-domain/canonical-byte checks, Unicode/control escaping and no whitespace/BOM/newline. Preserve exact strings and full bytes; no JS number or digest-only identity. The encoder does not authenticate its inputs. |
| RC02 original scope | Original installed generation, current physical connection/transaction and registered operation/authority admission | Confirm actual assigned xid, session/database/backend, original installation/profile and current authority before address lookup. A caller address cannot choose a foreign scope; no name-only or copied profile admission. |
| RC03 complete native capture | Full original operation registry for that admitted actual xid, through the original descriptor/cycle/completion/account boundary | Reuse `_operation_registry.COLUMNS` and its sixteen-cell decoder; retain every phase and operation, including finalized and no-touch operations. Do not select MAX, newest, manifest-only ordinals or an RLS-visible subset as the complete cohort. Direct table access remains unavailable to ordinary consumers. |
| RC04 entry correspondence | Each original manifest address and complete registry row, in original execution order | Both identity fields equal the same address. Resolve native ordinal independently of local position; compare original definition/input/prestate/candidate/obligation and complete context/group-admission bytes. Missing/extra contributor, reordered operation or wrong native group refuses. Noncontributing operations still remain in the complete transaction cohort. |
| RC05 readiness and seal | Actual registered effect readiness, original complete candidate/prestate attribution and canonical effect observation | Resolve generation/phase and actual effects independently before sealing. A decoded row or matching address does not prove readiness; no future digest embedded into its own producer input. |
| RC06 completion | Complete surviving operation/touch/reservation scope plus journal/current feed union and host outcome | All required semantic bodies and finalizers check the actual full scope. Retain original acknowledged/unknown settlement and bounded recovery; no receipt/publication from parsing or registry shape alone. |

The existing issued admission context0.2 and advanced fixture contexts are scoped
native producer observations, not the complete governed
truss-row-operation-context/0.1.0 semantic carrier. Original installation/layout/
resource/definition/execution/acting-role/catalog-cut/owner-union/group artifacts
must enter a deliberately versioned complete producer profile. Never relabel the
existing minimal context or fill its missing fields with synthetic artifacts.
Likewise, six fixture bytes and shape-valid original_group_custody_bytes cannot
establish the original address/family-group admission correspondence.

RC01 and RC03 have concrete source destinations: the private Python custody
boundary and original registered PostgreSQL adapter. RC02/RC04–RC06 depend on the
protected admission and security-owner handoff, original complete artifact
producer and seven semantic bodies. The sixteen-cell decoder is a structural
component, not a scope/current-authority factory. Actual callable identities,
private ACL, complete indirect dependencies and native receipts must qualify the
installed path. None of these six integration steps is passed by the current
parser tests; keep all consumer/corpus/interchange/release exits in scope.

## Python candidate address codec and manifest correspondence

Private `_row_operation_address` supplies the RC01 candidate four-string encoder/
decoder and selected manifest address correspondence. Integer strings stay exact
through native unsigned64 xid and nonnegative signed64 ordinal domains. The
candidate scalar recipe uses literal UTF-8, compact comma/colon JSON and standard
string escapes, matching the existing Python receipt codec's recipe; decoding
compares complete original bytes and refuses alternate spelling, whitespace,
BOM/newline, wrong domain/arity or noncanonical/overflowing integer carriers.
Native encoder/profile correspondence still needs independent qualification.

The pure `check_custody_addresses` component checks both identity fields against
the same original address, the supplied original installation/xid projection and
strictly increasing native ordinals in manifest execution order. Local positions
remain 0/1 while native ordinals may be 7/11. These arguments are already admitted
scope projections at the intended integration boundary; supplying strings to this
helper does not authenticate them, acquire authority or permit a database lookup.

The [source receipt](evidence/design-audit/python-row-operation-address-source.json)
records 82 passing Python source tests and three new focused controls, including an
independent exact Unicode/control/maximum-domain byte expectation. RC01 gains this
host codec component; native production registration, complete codec/resource
qualification and RC02–RC06 remain incomplete. No caller-address registry selection,
installed wheel/public API or semantic body readiness is advertised.

### Address output preflight correction

The candidate Python address encoder now computes complete escaped scalar UTF-8
and fixed JSON framing size before serialization. It refuses an oversized result
or unpaired surrogate before invoking the serializer, then checks produced length
against the original preflight. The
[source receipt](evidence/design-audit/python-row-operation-address-preflight-source.json)
records 83 passing source tests, including exact 8-MiB output and negative controls
whose serializer is replaced with a failure if called. This removes the earlier
serialize-then-refuse allocation path. Prior codec/test bytes are archived with
exact correspondence to the unchanged historical 82-test receipt.

Output preflight is not complete peak-heap/work/deadline or original resource-
account admission. Existing input strings, serializer overhead and native encoder/
text domain remain independently qualified responsibilities; no installed authority,
public API or RC02–RC06 completion is inferred.

### Native scalar-spelling correspondence checkpoint

The [native address oracle receipt](evidence/design-audit/operation-address-native.json)
compares the Python candidate against PostgreSQL16.15's original builtin to_json
string spelling, composed with fixed compact array framing and convert_to UTF8.
Eight independent samples cover ordinary identifiers, quote/backslash/control
escapes, Latin text, Unicode line separators, scalar encoding boundaries and
supplementary characters. Complete native bytes match the Python encoder and
strict decoder while preserving the actual assigned native xid and manually
selected ordinal gaps. Two additional observations verify SQLSTATE22021 for NUL
in native text and unchanged xid after confirmed savepoint containment.

This is actual primitive correspondence, not an installed registered encoder.
The full statement and original Python/checker pins are retained; no source routine
identity/owner/private ACL/dependency or complete native domain qualification is
supplied. Manually chosen ordinals are not original host issuer evidence. All
RC02–RC06 and full semantic/current-authority/resource installation exits remain.

Native installation-identity admission must preserve the supported text domain.
A host JSON string can represent NUL, while PostgreSQL text refuses it; no escaping,
replacement, truncation or generic shape-success may silently widen the native
profile. Refuse unsupported identity under the original selected native profile
before lookup/submission. The generic host syntax/codec remains data interpretation,
not permission to manufacture or submit an installation identity.

## Actual native address encoder component

`packages/postgresql/native/operation-address/encoder.sql` now provides the private
candidate operation_address_original(text,xid8,bigint) -> bytea. It is INVOKER,
VOLATILE, PARALLEL UNSAFE, called on null input with explicit refusal, and has
fixed pg_catalog/pg_temp search path and PUBLIC EXECUTE revoked. Native UTF8
identity text and typed unsigned64 xid/nonnegative bigint ordinal produce the
existing compact four-string address; input data never creates registry authority.

The encoder preflights framing/native integer strings and original UTF8 bytes,
then counts escape expansion before constructing JSON output. It checks final
native bytes against that preflight. Native text rejects NUL; no replacement or
widened host-string support is inferred. Complete native allocator/work/account/
deadline qualification remains required beyond the bounded loop/output procedure.

The [UMF source receipt](evidence/design-audit/operation-address-source.json) proves
exact archive/reload/guarded export with existing owner APIs. Declaration coverage
remains partial (zero declarations/two unhandled statements); UMF does not interpret
PL/pgSQL authority semantics. The
[native encoder receipt](evidence/design-audit/operation-address-encoder-native.json)
executes that actual owner export on PostgreSQL16.15 and passes 19 observations:
eight Python scalar-byte correspondences, actual fixture identity/attributes/ACL,
NUL refusal/confirmed same-xid containment, null/negative refusals, exact 8-MiB
output, one-byte/escape-expansion overflow, native maximum domains and actual
ordinary-role direct-call denial.

RC01 gains an actual native encoder component, separate from the seventeen
capacity helpers. Do not replace the seven semantic bodies or their 49 unresolved
bindings with this codec, adopt the administrative postgres owner/OID as production
registration, or use callable success as authority to resolve a caller address.
Original registered owner/dependency/profile/resource adoption and RC02–RC06 remain
incomplete. No installer, public operation or managed-service gate is promoted.

## Actual native address decoder pair

Private operation_address_decode_original(bytea) now returns typed installation
text, native xid8 and bigint ordinal. It bounds original bytes before UTF8/JSON
parsing, rejects any root/entry that is not the required four-string array,
checks domain and canonical integer spelling/range, and compares complete original
bytes with operation_address_original. JSONB parsing cannot admit object/number
content as strings: these kinds refuse before fields are projected. No generic
object round-trip or unknown-content preservation claim follows from this codec.

The [decoder source receipt](evidence/design-audit/operation-address-decode-source.json)
proves exact UMF archive/reload/export; declaration interpretation remains partial
(zero declarations/two unhandled statements). The
[paired native receipt](evidence/design-audit/operation-address-pair-native.json)
passes 43 PostgreSQL16.15 observations. It includes the earlier 19 encoder controls,
eight exact native field round trips, maximum domains, thirteen malformed/
noncanonical/type/domain refusals, exact 8-MiB decoding and ordinary-role SQLSTATE42501.
Earlier receipts and producers retain their original scopes and hashes.

RC01 now has native encoder/decoder components. Neither returns an admitted
transaction or an operation permission. Preserve original installation/current
scope and context/group/artifact/readiness checks in RC02–RC06; native casts and
address lookup cannot reconstruct that authority. Complete production callable/
owner/private ACL/dependency/resource and JSON parser workspace/error containment
qualification remain absent. Native text/NUL and UTF8 limitations remain explicit,
and no full address profile, semantic body, public operation or installer is ready.

### Closed original group-custody carrier proposal (2026-10-10)

The [group-custody proposal](../02-design/contracts/row-group-custody.proposal.md)
and its `truss-row-group-custody-v0.1.proposal.schema.json` close the previously
prose-only `original_group_custody_bytes` carrier. They bind the complete original
address, operation kind, selected profile and exact original family-admission
artifact. The context and group wrapper reference the same family artifact; the
wrapper does not embed future completion evidence or create a context/self-seal
cycle. This is proposed composition, not adoption into an installed profile.

`evidence/design-audit/schema-inventory-row-group-custody.json` records strict
registration/reference compilation of all 162 schemas with zero errors.
`evidence/design-audit/row-group-custody-shape.json` records 12 passing shape
controls, including explicit examples where shape acceptance cannot establish
canonical address spelling or semantic admission of empty family bytes. Original
artifact hash correspondence, native scope, registered family meaning, complete
contributors and independent completion remain separate obligations.

RC04 now has a closed proposed carrier to target. Its native producer, original
context/manifest/group comparison and semantic refusal scenarios remain
unexecuted. Historical synthetic native context and group bytes are not relabeled
as this carrier; the seven mandatory semantic bodies and their native evidence
remain outstanding.

The private Python `_row_group_custody.py` now decodes this proposed carrier into
frozen projections while retaining the original immutable bytes. It checks the
closed protocol fields, all six kinds, canonical address spelling and exact
family-artifact digest correspondence. Four focused test methods exercise six
kinds, thirteen carrier mutations, three syntax refusals and an empty artifact
whose shape/digest acceptance explicitly does not establish family admission.
`evidence/design-audit/python-row-group-custody-source.json` pins source and test
bytes; its retained log records all 87 Python source tests passing on Python3.11,
including the existing local runtime tests. This is source evidence, not a rebuilt
installed wheel or native group-producer qualification. Original context/manifest/
registry correspondence, full family semantics, accounting and completion remain
unexecuted integration gates. Public exports are unchanged.

### Python complete context and correspondence component (2026-10-10)

`_row_operation_context.py` decodes the complete existing context0.1 carrier,
retaining original bytes and all nine exact artifacts. It checks closed protocol
fields, exact artifact digests and native xid8/nonnegative-bigint address ranges.
`check_context_group_manifest` compares selected profile, complete canonical
address, operation/group identity, kind, original layout/operation definition and
family-admission artifact across the three decoded projections. Manifest local
position0 remains distinct from native ordinal7. The comparison grants no native
registry or authority admission and does not choose a current/newest operation.

The source-pinned `evidence/design-audit/python-context-group-manifest-source.json`
and retained log record 90 passing Python source tests. Three focused methods
cover nine required-artifact omissions, seven context mutations, seven independent
correspondence substitutions and four invalid local positions. Existing local
PostgreSQL tests run in the same source suite; this does not constitute a native
context/group producer or installed-wheel test. Original registry byte matching,
complete contributor/cohort coverage, native family semantics, current authority,
readiness, protected effects and original settlement remain independent integration
exits. No public exports or seven-body readiness claims change.

### Python complete supplied registry correspondence (2026-10-10)

`_row_registry_correspondence.py` consumes the complete supplied sixteen-cell
registry through its existing structural decoder. It decodes original context and
group bodies for every retained operation, checks installation/xid/ordinal, kind,
profile, original layout, definition and family artifact correspondence, and then
matches manifest contributors' original definition/input/prestate/candidate/
obligation bytes. Native ordinals resolve explicitly; no MAX/newest selection or
manifest-only filtering is introduced. The immutable result retains both the
original supplied cohort and the ordered contributor projections, sharing the
matched operation objects. Finalized/no-touch operations remain available for
separate complete-transaction settlement. This candidate composition requires the
selected manifest profile/layout to match every retained operation context; mixed
profile/layout cohorts are refused pending an explicitly qualified composition.

`evidence/design-audit/python-registry-correspondence-source.json` and its retained
log pin 94 passing Python source tests. Four focused methods retain unordered
native ordinals20/7/11 with ordered contributors7/11 and finalized noncontributor20;
reject seven contributor carrier substitutions, missing/duplicate contributors,
foreign xid and three noncontributor context scope substitutions; and check row/
byte capture bounds and immutability. These registry rows are synthetic unit-test
inputs, not an original native capture. Existing local-runtime tests in the full
suite do not upgrade that evidence scope.

The original adapter must independently establish descriptor/cycle/completion,
complete row visibility and actual transaction/current-cut custody before calling
this component. Neither the supplied cohort nor labels prove those facts. Full
native row framing/work accounting, current subject authority, family semantics,
complete touch contributor coverage, readiness, native effects and original
settlement remain outstanding. Public operations and all seven semantic body
readiness fields remain unchanged.

### Original native registry read and Python correspondence (2026-10-10)

`evidence/design-audit/check_registry_correspondence_native.py` now composes the
original complete current-xid registry query with the existing pinned pg8000 raw
text/accounted-control seam and private Python correspondence. The retained
`registry-correspondence-native.json` records PostgreSQL16.15, nine passing
observations and seven original captures, each with the sixteen-field descriptor,
raw text/null cells and original CommandComplete/ReadyForQuery frames. All fields
have native text OID25/format0. The original SELECT3 completion and transaction
statusT are checked before correspondence. The native table is created from the
retained original operation declaration in an isolated administrative fixture.

The fixture manually populates fresh complete proposed context/group carriers for
native ordinals7/11/20 under the actual assigned xid. The full query returns all
three with exact original cell correspondence; finalized noncontributor20 remains
in the cohort, while manifest contributors resolve7/11 in order. A separate foreign
xid row is excluded by the original native current-xid predicate. Five original
native definition/input/prestate/candidate/obligation substitutions produce one
Python refusal each. Confirmed savepoint rollback restores the exact cells under
the same xid. Confirmed final ROLLBACK returns statusI, and observation preserves
no-assigned-xid as NULL without assigning another transaction.

This is original native read/decoding correspondence evidence, not protected
producer qualification: fixture-owner inserts and phase labels establish neither
family admission nor readiness. Installed marker/current subject/private role ACL/
callable dependency closure, complete touch contributor coverage, resource/native
work/deadline, seven semantic bodies and original application settlement remain
unqualified. No synthetic historical carrier is relabeled, public API released or
consumer acceptance case promoted.

### OC02 unique unfinished selection after complete correspondence (2026-10-10)

The private Python `resolve_unfinished_operation` now applies the existing OC02
rule to the complete retained correspondence cohort: zero unfinished operations
refuses missing custody; more than one refuses ambiguity; exactly one returns
that original operation object. Finalized later ordinals do not replace the
unfinished operation. OC06 commit continues to use the complete cohort, not this
observer selector. Projection constructors, supplied labels and phase strings
cannot establish native admission/current authority/liveness.

`evidence/design-audit/python-registry-unfinished-source.json` pins 95 passing
Python source tests. It also maps the two changed source/test files to retained
exact initial archives matching the historical94-test receipt.
`registry-unfinished-native.json` records twelve passing native observations and
nine complete registry captures on PostgreSQL16.15. It adds actual native phase
schedules: two unfinished7/11 refuse without latest fallback; unique unfinished7
is selected with finalized11/20 retained; three finalized operations refuse
observer selection while remaining in the complete cohort. Fixture-owner phase
updates are synthetic scheduling, not semantic readiness/finalization proof. The
original nine read/cell/substitution/rollback checks remain in this separately
pinned producer; its initial checker/receipt are preserved unchanged.

This realizes OC02's host-side selection component without filling the seven
semantic wrappers' native body/owner/ACL/dependency registrations. Complete
protected producer/context/authority, OC03–OC07 actual effect/settlement/account
composition and ordinary-role installation remain outstanding.

### Native cascade attribution prerequisite for row_touch_observe (2026-10-10)

The original `source-epoch-layout-0.16.owner-export.sql` now has a separate native
cascade observation packet: `evidence/design-audit/check_row_cascade_attribution_native.py`,
`row-cascade-attribution-probe.sql` and `row-cascade-attribution-native.json`.
Eight observations pass on PostgreSQL16.15: three actual DELETE events each for
object and edge property homes, complete state/node/scalar removal, and confirmed
savepoint restoration under the same native xid. Fixture setup includes the current
qualified property-module and complete catalog source columns; no CHECK or FK is
disabled to populate the generated tables.

At each node/scalar AFTER DELETE observation, both the live state and node are
absent. The original state OLD image still directly carries its owner association;
node/scalar OLD retains state/node identity, and separately retained prestate
supplies the owner/property tuple. The packet preserves distinct object100 and
edge100 associations; edge relationship discriminator10 is separate from property
owner type3. All six original event tuples and actual relation OIDs are retained.
Savepoint rollback restores both homes, their two nodes/scalars and the empty
observation log. No particular relative trigger event order is claimed.

This executes a native attribution prerequisite, not row_touch_observe. The probe
captures selected typed attribution fields only and manually snapshots prestate;
it cannot qualify complete image/payload fidelity, original prestate producer,
family/subject authority, admission/cascade scope, actual touch/generation/capacity
updates or installed routine/role/ACL/dependency closure. Fixture catalog/source
labels are administrative data, not accepted catalog semantics. No criterion or
seven-body registration is promoted.

The row_touch_observe implementation must consume independently admitted retained
OLD association before deletion, validate complete typed images against that
custody and the original operation's effect scope, and retain every actual cascade
contribution before event-local tuple deduplication. A live parent lookup is only
corroboration: absence cannot produce skipped events, guessed owner identity or
zero-property attribution. Next native realization is the protected prestate/image
producer plus complete scope checks; copying this observation probe into the
semantic wrapper would omit those obligations.

### Complete native row-image codec component (2026-10-10)

`packages/postgresql/native/row-image/codec.sql` supplies four private INVOKER
routines: original complete column-profile validation and state/node/scalar image
encoding. The validator checks every ordered user field, native type OID,
nullability, typmod, collation, dropped status, array dimension and inheritance
against the existing native0.16 table shapes. The images retain domain-tagged
PostgreSQL composite binary output, including every field type OID, explicit NULL
and complete payload. Native numeric datum/token, temporal instant/text and source
bytes remain separate. Neither generic JSON nor session display text supplies the
original value image.

Existing UMF owner APIs archive/reload/export the exact source in
`row-image-codec-v0.1.proposal.umf.json`; `row-image-codec-source.json` records zero
declarations/eight unhandled CREATE/REVOKE statements and complete=false. The
actual owner-exported codec is executed against the original UMF-exported tables
by `check_row_image_codec_native.py`. Its `row-image-codec-native.json` passes21
PostgreSQL16.15 observations: three complete stored row images; seven constructed
scalar payload samples with independently authored OID/null/full binary byte
expectations; three null-image and one unknown-kind refusal; three native structural
profile corruptions with rollback restoration; and four actual ordinary-role
42501 private-call denials. All complete image bytes are retained. The exact decimal
sample exceeds JavaScript safe integer precision and keeps its original leading-zero
token; temporal instant and original timezone text remain independent. Constructed
scalar samples establish datum fidelity only, not accepted logical value semantics.

This component supplies native image fidelity for subsequent prestate/OLD/NEW
composition. It does not authenticate a trigger/candidate/prestate, admit family
or association meaning, current authority, deployed callable/builtin/dependency
closure or private native roles. Its eight-MiB output ceiling is postserialization;
original admission must independently qualify pre-materialization/detoast/record-send/
copy/work/allocator/deadline bounds. Binary codec support is version-qualified,
not portable canonical UMF value encoding. The README preserves these limits.
No touch observer registration or seven semantic body field is filled by these
codecs. Next composition must bind original event/prestate/native allocation
custody, full effect scope and actual resource admission before semantic updates.

### Native row-image exact output preflight (2026-10-10)

The current codec source adds private `row_image_size_original` and checks exact
whole-frame length before state/node/scalar record serialization. Typed text/bytea
lengths, fixed-width datum lengths, explicit NULL handling and original numeric
binary length determine domain/header/payload size. Actual serialized output must
match that independent length. The numeric length measurement still serializes its
numeric cell; native datum materialization/detoasting/copies/work/deadline and
whole-account admission remain separate obligations. This does not qualify a
full pre-materialization memory or time bound.

The new `row-image-codec-v0.2.proposal.umf.json` is a Truss source artifact revision;
the row-image wire domains remain0.1 and existing complete image bytes are unchanged.
`row-image-codec-preflight-source.json` records exact existing-UMF archive/reload/
export with zero declarations/ten unhandled CREATE/REVOKE statements, complete=false.
The actual exported five-routine component passes31 native observations in
`row-image-preflight-native.json`: all original21 fidelity/profile/private-call
checks, three exact row-kind length parities, four invalid length-array refusals,
exact eight-MiB independent byte equality, one-byte overflow refusal and actual
ordinary-role denial of the new private size helper. The receipt does not claim
an allocator/record-send instrumentation proof or protected touch observation.

`row-image-preflight-history.json` verifies the retained initial codec source
matches both historical source/native receipt digests. Initial models, exports,
checkers and receipts remain intact. The README now describes the current exact
output preflight and its remaining native resource limits. Original protected
prestate/event/association/family/current-authority, complete native dependency/
private role closure, full resource admission and seven semantic bodies remain
required before installation/public effects; no readiness field is promoted.

### Python original native row-image framing and span retention (2026-10-10)

The [native row-image profile](../02-design/contracts/native-row-image.proposal.md)
and private `_row_image.py` now give the subsequent prestate/event correspondence
path a complete bounded Python projection. The decoder checks domain/version,
original ordered OIDs/required/null fields, complete lengths, primitive widths,
UTF8/Boolean representation and absence of trailing bytes. Immutable original
bytes and frozen cell offsets/lengths provide read-only memoryview payload spans;
NULL remains None and present empty bytes remains a zero-length view. Numeric/
temporal payloads, original tokens/text and codec/source bytes stay independent.
The decoder does not infer logical native numeric/temporal validity or event
provenance from framing or OIDs.

`evidence/design-audit/python-row-image-source.json` pins99 passing Python source
tests including existing local-runtime tests. Four focused methods replay ten
retained native image vectors and test eleven framing/type/null/length corruptions,
four primitive/UTF8 corruptions, exact eight-MiB input/overflow and invalid cell
indices. Cell views refer to original bytes without per-cell retained payload
copies. UTF8 validation still creates temporary copy/text work; this is not whole
resource qualification. Native execution remains the separately pinned31-case
codec receipt, not a new native producer or installed-wheel run. Full original
OLD/NEW/prestate/candidate/allocation, current authority and semantic wrapper/
resource composition remain required. Public exports and seven-body readiness
fields are unchanged.

### Full OLD/NEW image correspondence and owner attribution (2026-10-10)

Private `_row_event_attribution.py` now requires complete event-image byte equality
against the separately supplied original prestate/candidate map. State attribution
uses the full direct owner/property branch; node/scalar requires retained state,
and scalar requires retained node, without live parent lookup. Duplicate map keys,
conflicting state associations for globally unique native node IDs, missing/foreign
association, mixed owner branches or altered complete originals refuse. OLD/NEW
side availability is explicit for INSERT/UPDATE/DELETE. Both original images and
attributed tuples are retained; only event-local touch owners are deduplicated.
Signed native owner/catalog IDs are preserved exactly. Edge property owner is not
substituted with its relationship discriminator.

`evidence/design-audit/python-row-event-attribution-source.json` pins103 passing
Python source tests, including existing local-runtime tests and four focused
methods covering all three image kinds/event sides, separate changed UPDATE
associations, original/mapping/side/bound corruptions and immutability. Changed
ownership/reparenting projection does not qualify an operation profile permitting
those effects; original scope/guards/authority admission remains required first.

`row-event-attribution-conflict-native.json` adds16 observations on PostgreSQL16.15
through the original UMF-exported layout/codecs and retained observation probe.
Six actual cascade OLD images match all original prestate bytes and project the
expected distinct object/edge association after live parents disappear. Complete
removal/confirmed rollback checks remain; actual native-input missing-state and
corrupted conflicting-node projection controls refuse. The latter is explicitly a
projection corruption, not an impossible conflicting native row or native constraint
proof. The initial14-observation receipt/checker remain untouched; the archived
initial Python module matches that historical native source digest.

The probe's prestate/candidate and catalog labels remain administrative fixtures,
not original protected admission/family/subject authority. The current component
performs no database lookup/DML, touch or operation generation update, authorization
resolution or finalization. Complete native event/routine/role/DDL/cut/codec/scope,
held guards/capacity and full resource/settlement composition remain outstanding.
No public API, installed-wheel claim or seven-body readiness field changes.

### Native touch transition composition (2026-10-10)

The retained `touch-transition-descriptor-native.json` passes18 observations and
retains16 original wire captures on PostgreSQL16.15. Its producer executes the
existing UMF-exported first-touch, seal, operation-reset and generation-advance
statements with their original positional parameters. All returned12 touch or16
operation cells, exact column names/text OIDs/formats, native INSERT/UPDATE
completion frames and transaction status match the selected expectations.

Checks cover unassigned-xid refusal without assigning a transaction ID; reset
clearing prior proofs; first touch and sealing; generation advance invalidating
seal and retaining the complete next contributor manifest; stale generation,
foreign layout/owner/context/prior manifest, empty next manifest, finalized
operation and exhausted generation refusals. Confirmed savepoint rollback restores
both registries to empty under the same original transaction ID. The initial
15-observation/13-capture producer and receipt remain separate and unchanged.
Both receipts pin their exact producer and original SQL source digests.

The owner tuple comes from retained historical native images; current event
provenance and complete protected scope are not supplied by this experiment.
Operation phase/seal labels and contributor manifests remain administrative
fixtures. Head/capacity/held guards, native contributor/family/current-authority
proof, complete callable/role/DDL closure and full resource accounting remain
required before integrating an installed observer. Zero affected rows require a
refusal, without retry or success classification. This checkpoint adds no public
API, installed-wheel evidence or seven-body readiness claim.

### Actual cascade operation-generation composition (2026-10-10)

`row-event-generation-native.json` retains21 observations from the existing
private `runtime_observe_operation_generation` trigger composed with the original
UMF-exported native0.16 tables, current row-image codecs and original cascade
image probe on PostgreSQL16.15. Six real state/node/scalar DELETE events advance
the surviving operation generation from0 to6 and clear readiness/seal/application
generations and application result. All six original OLD images still correspond
to retained prestate and the correct distinct object/edge owner-property tuples.
Confirmed savepoint rollback restores both canonical rows and prior operation
phase/generation/proofs, without changing the original transaction ID.

With no unfinished operation, actual cascade writing fails55000. At exhausted
generation it fails54000 without arithmetic overflow; rollback restores canonical
rows and the original exhausted generation. The attempted ambiguous operation
fixture fails23505 at `row_home_operation_unfinished_xid`, before any observer
event. The checker preserves this actual native invariant rather than dropping
the index to manufacture an unreachable installed state. The trigger's defensive
multiple-operation branch is not thereby exercised. An initial failed harness
attempt revealed that constraint; no completed receipt was overwritten.

Administrative caller/phase/catalog/prestate fixtures do not establish protected
admission or current authorization. This is the existing partial INVOKER producer,
not the missing complete `row_touch_observe` body. Key/reservation trigger paths,
held guards, full touch/contributor/family/scope/capacity composition, callable
role/DDL closure and whole resource qualification remain independent. Native
pg8000 calls in this probe do not qualify the accounted original-control seam.
No public API, installed-wheel claim or seven-body readiness field changes.

### Native key/reservation generation paths (2026-10-10)

`key-event-generation-native.json` pins10 PostgreSQL16.15 observations against
the original UMF-exported native0.16 layout and existing private generation
trigger. Both actual key and reservation INSERT/UPDATE/DELETE paths clear
operation proofs. Same-route UPDATE advances one distinct guard once; moving
the namespace advances both old and new route guards. Eight actual events leave
operation generation8 and route generations6/4. An exhausted destination guard
raises54000 on reservation INSERT; confirmed rollback leaves no inserted row
and restores prior route/operation generations. Whole savepoint rollback restores
the original two guards and operation phase/generation/proofs under the same xid.

An initial fixture attempt failed the original key-definition source-completeness
constraint; the completed producer includes its required accepted-document
columns. No constraint was bypassed and no completed receipt overwritten.
Native driver result cells are retained; this experiment does not qualify the
accounted original-control seam, native protected subject/authority, full key
derivation/collision/concurrency/event custody, guard ownership/lock admission,
touch/capacity or installed privilege closure. Exhausted insertion does not
qualify partial two-route failure ordering. This closes the previously untested
finite key/reservation generation paths, not complete observer readiness.

### Ordered two-route failure containment (2026-10-10)

The separate `key-event-atomic-generation-native.json` adds12 native observations
and preserves the earlier10-check producer/receipt unchanged. The checker reads
actual native bytea route order, inserts an original reservation on the first
route and exhausts the second. An actual namespace move reaches the ordered
guard loop, whose first UPDATE is eligible and whose second guard raises54000
(`original key guard exhausted`). Confirmed rollback restores the complete
returned route/key/generation, operation phase/generation/proof/result and
reservation identity/value/generated-route projections byte for byte. Setup
rollback then restores prior6/4 guard generations and operation generation8;
whole rollback restores the original guards and operation proofs. Original xid
is unchanged throughout.

This closes the previously explicit finite partial two-route failure experiment.
It supports atomic refusal containment under the existing single-attempt policy;
it does not replace independent held-guard/head/capacity admission or prove
concurrent deadlock behavior. The intermediate first UPDATE is established by
original loop order and eligible fixture state, not an independently exposed
mid-statement observation. The experiment tests reservation movement; key-row
movement success is covered separately, but its partial-failure path is not
claimed. All administrative-custody, native profile/role, protected authority,
full resource and seven-body gaps remain unchanged.

### Complete Python touch registry decoding (2026-10-10)

Private `_row_touch_registry.py` retains the entire supplied12-cell touch cohort
and immutable decoded custody. It checks exact selected columns/count/completion,
original actual xid, canonical signed native owner/catalog integer domains,
positive bounded dirty/seal generations, seal<=dirty, unique full touch identities,
strict original hex carriers and complete layout/home/owner-property byte
correspondence to the retained operation manifest. Manifest native addresses must
match the selected installation/xid. Older seals remain retained rather than
being normalized into current readiness. No undocumented positive catalog-ID
constraint is invented. Duplicate rows refuse rather than collapse.

`python-touch-registry-source.json` pins107 passing source tests and four focused
methods replaying all four nonempty touch vectors from the retained18-observation
native transition receipt. Controls cover signed boundaries, older seal, duplicate
identities/distinct owner kinds, malformed cells/custody, installation mismatch,
exact logical byte/row bounds and incomplete descriptor/completion. This replays
retained native bytes; it is not a new native capture or installed-wheel run.

The next composition consumes original native SELECT control/descriptors under
the complete same-cut capture schedule, then checks each retained manifest against
the complete operation registry via existing correspondence. Semantic owner/home
codec admission must independently bind the typed tuple to original artifact
meaning; opaque byte equality cannot do so. Full subject/current-authority,
held guards/capacity, event provenance, finalization and whole resource/settlement
qualification remain outstanding. The decoder performs no DML and changes no
public exports, layout/UMF schema or seven-body readiness field.

### Original touch point read through Python decoding (2026-10-10)

`touch-point-decode-native.json` pins24 PostgreSQL16.15 observations and22
original control captures. It executes the existing exact UMF-exported five-
parameter current-writer tuple lookup without rewriting positional SQL. All12
original text/null cells and column names/OIDs/formats, SELECT completion frame
and transaction status are checked before private Python decoding. Original
first-touch, sealed and advanced complete contributor-manifest rows round trip
without cell replacement. Unassigned lookup leaves xid unassigned; foreign kind
and confirmed rollback produce empty selected-tuple projections. Previous18-
observation transition producer/receipt remain untouched.

The lookup is a selected owner/property tuple read, not the complete touch cohort
scan. Empty projection alone cannot prove authorized absence: original visibility,
same-cut control, protected scope/owner codec/current authority must be admitted
separately. No LIMIT/phase/readiness filter or caller-xid fallback is introduced.
Receiver byte permits/native control capture qualify only their selected seam,
not whole allocation/work/deadline or privileged original actor evidence.
Full operation-registry correspondence and complete observer/finalization remain
required before publication; no public or seven-body gate changes.

### Complete current-writer touch cohort query (2026-10-10)

`row-touch-current-writer-cohort-v0.1.proposal.sql` selects every touch for the
actual assigned xid with all12 original text/null fields and deterministic native
identity order. It has no caller-xid parameter, tuple/phase/seal filter, LIMIT or
partial row cap. Native receive/decode resource exhaustion must refuse capture,
not silently publish a prefix as complete. This is a commit-cohort projection,
separate from the five-parameter point lookup and from observer OC02 selection.

The existing UMF owner APIs preserve the original source, serialized reload and
export exactly. The new source artifact carries a retained SELECT native AST;
DDL declaration extraction reports zero declarations/one unhandled statement
and complete=false. No reusable SQL generator or metadata semantics are copied
into Truss. There is no physical table/ER layout change.

`touch-cohort-decode-final-native.json` passes29 observations with27 original
control captures on PostgreSQL16.15 through the pinned accounted driver seam.
Complete empty/unassigned, single-row, two-owner-kind and rollback cohorts match
full native descriptors/completion/status and Python-decoded originals. A stored
seal older than dirty generation remains present. The initial receipt retains
inherited text incorrectly denying the newly tested cohort scan; its exact
producer is archived as `check_touch_cohort_decode_initial_native.py`. A separate
actual rerun corrects that scope text without rewriting the initial receipt.

The two-kind fixture is administrative, including supplied owner-property
artifacts and a manually staged old seal. It proves finite native query/decoder
composition, not semantic owner-codec admission, original protected visibility/
coherent cut/current authority, full contributor operation correspondence or
complete accounting. Those inputs remain mandatory for commit finalization and
publication. Seven-body readiness and public exports remain unchanged.

### Shared complete operation cohort and every touch manifest (2026-10-10)

Private `check_touch_operation_correspondence` now decodes the complete supplied
operation cohort once under independently supplied profile/layout projections,
then matches every touch's original contributor manifest against that cohort.
All phases/noncontributors remain retained. Each touch's raw original carriers
must match its retained custody projection, actual xid/profile/layout must agree
and complete touch identities cannot duplicate. Contributor objects share the
original decoded cohort rather than recreating separate native context/group
projections per touch. Existing single-manifest correspondence uses the same
decoder/matcher. Empty touch input still validates all original operation
contexts/groups, retaining catalog or other non-row operations.

`python-touch-operation-source.json` pins111 passing Python source tests. Four
focused methods check shared object identity, finalized noncontributors and
manifest ordering, missing/substituted contributors, foreign/raw custody,
duplicate touch identities, empty-touch malformed registry refusal and touch
count boundaries. Multiple unfinished entries and older seals remain structural
data in this commit-cohort check; observer OC02 remains separate. This does not
qualify a native state permitting overlapping operations or prove readiness.

The concrete next integration sequence is: original complete native operation
and touch captures under one independently protected coherent cut; this shared
correspondence; admitted semantic owner/home codec and current subject/authority
for every retained original obligation; held guards/head/capacity and full
resource accounting; complete registered native validation/finalization/journal/
feed/settlement. Profile/layout arguments alone do not authenticate an installed
profile. Syntax/row/byte ceilings do not account for repeated per-manifest matching
work or temporary copies. The new composition is private, performs no DML and
changes no installed-wheel/public API or seven-body readiness claim. Earlier
source/native checkpoints remain historical to their exact pinned module bytes.

### Aggregate contributor expansion preflight (2026-10-10)

The shared touch/operation matcher now requires explicit `maximum_contributors`
in addition to touch/operation-row/byte allowances. It charges every original
manifest entry across all touches before operation context/group decoding,
refusing an exhausted or invalid Boolean/float/negative allowance. This prevents
separate per-touch limits from admitting an unbounded combined expansion.
No contributor prefix is published and no allowance is reset per touch. Empty
touches with allowance0 still decode the complete operation cohort.

`python-touch-contributor-bound-source.json` pins112 passing source tests. The
new independent boundary test accepts exactly2 entries for one touch/exactly4
for two owner kinds, refuses combined3 and malformed limits before operation
decoding, and retains the empty-touch cohort behavior. This is a logical count
preflight; nested JSON, byte comparisons/hex copies, native/host allocations,
time/deadline and original shared account still require full qualification.
It changes a private component signature only, not public APIs or body gates.

### Installed helper definition and membership drift (2026-10-10)

The separate79-check [native drift receipt](evidence/design-audit/private-callable-drift-native.json)
extends the17-helper attribute/effective-EXECUTE experiment with same-signature/
same-OID original definition-byte drift and an unexpected routine membership
control, both followed by exact restoration. PA01's inventory must preserve
these complete identities/definitions and compare both membership directions;
matching selector/version labels alone is insufficient. The finite administrative
helper subset remains separate from complete installed public/private/admin
closure, dynamic dependency admission and security-owner coherent-cut authority.

### Generation trigger inventory and drift consequence (2026-10-10)

The [25-check native trigger experiment](evidence/design-audit/generation-trigger-drift-native.json)
retains exact five-trigger native registration and actual disable drift. With
the scalar generation trigger disabled administratively, a canonical UPDATE
leaves old operation proofs unchanged. This validates PA01/PA05's requirement
for independent complete trigger coverage and protected cut/final freshness: a
phase/generation label cannot certify effects when the installed producer drifted.
Rollback restores both native trigger inventory and canonical value. Complete
ordinary/admin privilege and installation publication enforcement remain open;
this probe is not that enforcement. Existing21-check cascade receipt is retained.

### All four original invoker families reject elevated capture (2026-10-10)

The [four-family elevation receipt](evidence/design-audit/four-family-elevation-native.json)
passes22 PostgreSQL16.15 observations. Alongside the earlier base-family original
actor/context preservation controls, asserted-origin, epoch-context and
configuration-context candidates are actually installed and invoked through
separate SQL DEFINER wrappers owned by integrity_probe. All three retain native
INVOKER/search-path attributes, raise55000 at the original invoker guard, restore
the original actor after confirmed savepoint containment and leave no surviving
registry row. The earlier10-case producer/receipt remains unchanged.

This confirms the original actor boundary applies across every family, rather
than silently treating an advanced context as a protected owner-aware route.
It does not realize PA01/PA02's protected capture: a separately versioned original
caller/capture/writer protocol must retain actual subject/attempt/connection/
installed authority across elevation. Broad administrative base fixture grants
and synthetic wrapper inputs remain explicitly unadopted. Advanced family
artifact admission is not exercised because the guard refuses first; complete
native OID/owner/ACL/dependency closure and original accounted controls remain
separate outputs. No guard removal, direct consumer registry grants, public API
or semantic-body readiness change is authorized by this experiment.

### Four-family original native registration correspondence (2026-10-10)

The [39-check registration receipt](evidence/design-audit/four-family-registration-native.json)
extends all-family elevation controls with exact original stored body comparison
against each frozen SQL source. It retains complete native function definitions,
definition digests, actual routine/namespace/owner OIDs, exact source selectors
and original ACL cells. All four selected routines share the fixture namespace
and owner while retaining four distinct native identities. Native language,
security mode, volatility/parallel/null/leakproof/search-path attributes, result
type and effective actor/integrity/PUBLIC EXECUTE rights match independently
selected expectations. The earlier22-check producer/receipt remains unchanged.

Fixture rights intentionally differ: the base ordinary actor is broadly granted
for its original invoker experiment; advanced routines are executable by the
fixture integrity owner for the nested-DEFINER refusal controls. None is an
adopted production privilege plan. These exact ephemeral registrations advance
PA01's identity/body correspondence component, not complete public/private/admin
callable/data/DDL/transitive closure, protected actor capture, owner authority or
installed publication. Complete dependency inventory cannot be inferred from
matching function bodies or regprocedure resolution. Native definitions retain
original source meaning; current context versions are not reinterpreted as
protected owner-aware contexts. No public API or seven-body gate changes.

### Minimal ordinary admission rights and missing dependency control (2026-10-10)

The [49-observation receipt](evidence/design-audit/four-family-ordinary-denial-native.json)
extends native registration/elevation evidence with a separate ordinary login
receiving only schema USAGE and admission EXECUTE. Base and asserted-origin
entry refuse42501; direct registry SELECT/UPDATE/DELETE refuse42501. Confirmed
containment leaves no registry rows. Epoch/configuration entries instead
refuse42883 for original runtime_lock_source_epoch missing from this intentionally
registration-only fixture. Their original native messages are retained separately:
this is a missing fixture dependency, not ordinary permission-closure proof or
a claim that no helper implementation exists in the repository.

The initial harness incorrectly expected42501 for every family; the actual result
changed the experiment's classification. No completed receipt was overwritten.
Next jointly install the original epoch/configuration dependencies and qualify
full original native invocation/data/ACL closure before asserting advanced
ordinary-role denial. Current same-source registration and nested-DEFINER guard
checks cannot certify those unexecuted paths. Public protected APIs and all
semantic body gates remain closed. Broad earlier fixture grants are not adopted.
