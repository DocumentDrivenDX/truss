# Private reference driver producer port

Design-only interface for CONTRACT-007's frozen node-postgres complete-frame/no-residual candidate. This is adapter-owned integration, outside the browser core and public toolkit exports. It selects a concrete producer boundary; stock pg does not thereby gain the port. Exact installed source/build/runtime/transport and native qualification remain required.

## Port operations and original custody

The port is created once by the admitted physical-lease issuer before reads/submission, from its pinned transport/parser/allocation producer bundle and original enclosing account. No application constructor accepts caller-supplied assertions. The issuer keeps a private identity registry; opaque tickets below represent registry entries, not serializable evidence or bearer authority. TypeScript branding alone cannot enforce this registry.

| Operation | Input | Output and required native meaning |
| --- | --- | --- |
| reserveIngress | Original lease/operation/cycle, selected producer maximum receive backing capacity, parser/capture overlap, control allowance and containment reserve | Private ingress ticket, before enabling actual reads. Missing conservative producer bounds refuses admission. No producer reads/allocates a first chunk to discover its bound. |
| retainChunk | Original ingress ticket and producer-observed backing identity/capacity/span/lifetime | Private retained span ticket after charging the original physical allocation and performed work. A subarray never changes original backing capacity. Multiple live spans share one backing occupancy with independently tracked lifetimes. |
| reserveFrame | Original ordered retained spans, complete scanner grammar/UTF-8 evidence, original frame/cycle and selected capture/parser overlap | Private one-use frame ticket. Admission includes every actual copy and conservative downstream allocation before it occurs. No peer length or parsed public Result can issue this ticket. |
| forwardFrame | Original one-use frame ticket | Synchronous complete-frame consumption receipt from the integrated parser: original frame identity, exact consumed bytes, pre/post residual observation and ordered callback correspondence. It captures original facts before public conversion. A receipt is private producer observation, subject to independent qualification. |
| releaseSpan | Original retained span and producer-observed end of its actual lifetime | Occupancy reconciliation for that original backing only after all retained views/copies/evidence lifetimes end. It never refunds cumulative work or ends transaction/recovery custody. |
| stopIngress | Original lease/cycle and failure/cancellation/disposal reason | Stops new forwarding and begins original containment. This result never means rollback, COMMIT outcome or pool-return permission. |

## Runtime admission rules

Every operation checks issuer identity, physical lease epoch, original account, cycle/order and current profile generation in the private registry. A copied, foreign, expired, already consumed or post-disposal ticket refuses. Tickets cannot be reconstructed from bytes, accepted across reopened leases or reissued to repair a failed forward. Asynchronous idle/session control messages retain explicit original lease-account attribution; absence of a command cycle is not permission to charge a new operation account.

reserveFrame reserves before capture/copy/parser overlap, then freezes the admitted original span inventory against mutation. Actual buffer ownership must prevent the upstream producer, callbacks or shared views from changing admitted bytes before consumption. A read-only TypeScript view does not supply runtime immutability. The source/build integration must select ownership transfer, inaccessible storage or a reserved isolated copy, and qualify that selection.

forwardFrame consumes its ticket on entry even when the parser throws or the postcondition fails. The integrated entry independently observes zero residual before forwarding and exact complete consumption with zero residual afterwards; it cannot accept a caller boolean. Callback dispatch stays within original cycle arbitration and cannot publish, reenter native submission or release custody. A precondition failure forwards nothing. A postcondition failure preserves original possible effects and enters containment; there is no second forward or replacement query.

Ingress/scanner/parser/capture allocation observations reconcile with the same original account. Runtime collector hooks may expose private allocation events for qualification, but missing events or unknown retained backing capacity refuse the bounded profile. Garbage-collection assumptions, a dropped reference or a small semantic byte count cannot mint release evidence. Account denial after native submission retains original possible-effects/recovery obligations and the separately reserved containment capacity.

## Implementation handoff

Implement this port inside the versioned adapter integration at the frozen parser boundary, not as an application event listener. Bind reserveIngress to the actual socket/TLS producer before enabling reads, and forwardFrame to an explicit integrated parser entry with original consumption assertions. Keep native authentication and earlier protocol phases separately admitted. No fork or installed runtime is supplied by this document.

Qualify independent ledger and wire/native observations in STP-044 DH-01–05. Required faults include forged/foreign tickets, repeated forward, frame mutation after admission, shared-backing early release, wrong cycle/epoch/generation, synchronous callback reentrancy and parser exception after capture. Compare actual allocation order, forwarding count, captured native facts and original containment outcome; adapter-issued receipts cannot be their own expected oracle.

## Operation issuer and savepoint control binding

The ingress operations above reserve control allowance but do not themselves
issue an operation ordinal or confirm an operation savepoint. Complete this
binding inside the same admitted physical-lease issuer; do not treat the current
counter component or a resolved control Promise as that binding. This extends
original private producer custody, not the public Executor protocol.

The selected integration needs three private operations on the existing issuer:

| Private operation | Original inputs | Required output and custody |
| --- | --- | --- |
| reserveOperationControl | Admitted original transaction epoch, exclusive arbitration, current profile/cancellation state, cumulative account, selected savepoint and containment/cleanup procedure bounds | One opaque reservation registered with that issuer. Reserve all forward and cleanup obligations before consuming an ordinal. Failure publishes no operation and submits no native control. |
| bindIssuedOperation | That unconsumed original reservation and the separately consumed exact operation ordinal | Original attempt/control association retained before native submission. No caller bytes or copied ticket can bind an ordinal. Failure after issuance burns the ordinal; it never rewinds the counter. |
| submitOperationSavepoint | That original bound reservation and selected registered savepoint control definition | One submission, then original correlated native completion/containment observation for that epoch, operation and control cycle. Confirmed savepoint permits later native admission; unavailable completion keeps it closed and retains original recovery custody. |

These names describe the required private binding, not implemented or callable
stock-driver APIs. The same account and physical issuer registry govern them and
the ingress operations. Keep operation ordinals, protocol-cycle ordinals and
savepoint-control identities separate, with explicit original correspondence.
No additional database table or independently resettable issuer is introduced.

reserveOperationControl must complete before bindIssuedOperation and before any
savepoint is submitted. If cancellation or epoch/profile change occurs during
reservation, recheck under the original arbitration before publishing its ticket.
Never use a later epoch's reservation to finish an earlier operation. After
issuance, failed binding, cancellation or failed savepoint creation preserves the
burnt ordinal. Unused occupancy may be reconciled only from actual original
producer lifetime evidence; cumulative work is not refunded.

submitOperationSavepoint consumes its submission permission on entry. Parser,
transport or callback failure cannot permit a second submission. The original
control completion must establish that exact savepoint exists in the admitted
original transaction through the selected control/native producer protocol;
ReadyForQuery T alone, a command tag alone or a resolved Promise is insufficient.
The same original outcome correlation determines confirmed failure versus
unknown control completion. Unknown completion closes new operation admission,
retains original attempt/control/account/cleanup custody and follows the existing
recovery procedure without creating a replacement counter or savepoint.

Native head/capacity admission, registry insertion and canonical effects follow
only confirmed containment. They must consume original issuer evidence through
the selected private native admission composition, rather than trusting a numeric
argument. The four row-derived native allocation candidates remain incompatible
until that verification is implemented. No successful reservation proves current
person authorization, installed inventory or publication-drain completion.

Qualify this binding under CONTRACT-007's original adoption/control schedules and
DH-01–05, with actual native observation in addition to independent host accounting:
reservation denial before any submission; concurrent wrapper adoption; cancellation
between reservation and issuance; failure after issuance; lost savepoint response;
wrong epoch/control cycle; duplicate submission; confirmed savepoint followed by
actual rollback; and loss of private issuer state. Every schedule observes exact
forward/control counts, burnt/nonreused ordinals, complete original custody and
whether native registry effects were permitted. A fake successful control callback
cannot author the expected native confirmation. Python and TypeScript must satisfy
these same controls on their own selected driver tuples before sharing support.
