# Original operation ordinal issuer integration

This execution handoff applies CONTRACT-001 OC01–OC07 and CONTRACT-007's shared
executor/transaction issuer. It precedes the missing canonical observer bodies;
it adds no public transaction ID, database counter, session setting or authority
issued by a JSON field.

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
only and establish no original artifact or mutation admission. The other three
families have the same inspected source expression; they were not executed by
this reproduction.

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
