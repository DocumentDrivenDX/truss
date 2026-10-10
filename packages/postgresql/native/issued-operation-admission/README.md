# Trusted-host issued ordinal candidates

These four separate candidates implement ADR-008's host-issued ordinal input.
They preserve each original family's actor/artifact/epoch/configuration capture,
add a leading nonnegative native bigint, and reject an ordinal no greater than a
surviving operation in the same native transaction. Existing unfinished-operation
checks remain. PUBLIC execution is revoked on the new exact signatures.

Nonreuse after rollback is the trusted host issuer's obligation: native rows
cannot prove a removed attempt never used a number. The host must issue before
savepoint submission, retain cumulative custody across failures and close admission
on uncertain outcomes. These sources alone do not provide that driver binding,
resource account, authority or finalizer.

The older files outside this directory remain historical reproduction inputs.
A selected complete installer must install only the admitted issued signatures;
it must not leave legacy row-allocator overloads as executable alternatives.
No public API or deployment profile adopts these candidates. Qualification must
run all four families with actual Python-issued values on corrected PostgreSQL,
including savepoint rollback, prior finalized operations, invalid/conflicting
ordinals, actual epoch/configuration captures and original outcome correlation.
No synthetic artifact fixture can establish full acceptance or security readiness.
