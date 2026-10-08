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
