# Original asserted-origin capture candidate

Status: implementation selection, not installed adoption. Governing sources:
CONTRACT-003 originalExecution, CONTRACT-007 separate asserted-origin argument,
CONTRACT-002 exact journal origin and the installed-context admission candidate.

Use the existing row_home_operation.original_context_bytes immutable home.
Do not add a second per-operation identity or origin store, reuse another
artifact column, or mutate context after runtime_admit_operation has inserted
it. The existing original-context guard protects the whole byte artifact,
including the selected new capture fields, and rejects deletion/truncation.

Introduce a distinct native context0.3 capture producer with the nine original
context0.2 native actor/executor facts plus assertedOriginUtf8Hex and
assertedOriginCaptureProfileHex. Both new fields retain exact original bytes;
neither is a derived journal projection or a role claim. A complete original
capture requires both. Context0.2 remains its original nine-field shape and
cannot be upgraded by defaulting an absent origin to null or supplying today's
profile. Report captureProfile still identifies the complete installed-context
composition, not this narrower native artifact alone.

The originating facade snapshots separate asserted-origin bytes on operation
admission before callbacks. Strict numeric-free JSON decoding refuses duplicate
members, invalid UTF8/surrogates, numeric nodes and malformed content before
business effects. Preserve original whitespace, escapes and order in retained
bytes while the mapped canonical tree separately preserves semantic content.
Caller labels remain asserted; native databaseRole comes from original native
actor capture. Nothing in asserted content selects a capture implementation or
changes authority.

A new private admission procedure accepts the six existing operation artifact
inputs plus original asserted bytes and the independently registered capture
profile bytes. It performs the same original actor, catalog exclusion,
transaction/ordinal and unfinished-operation admission as the existing
procedure. It creates complete context0.3 bytes before the one registry INSERT,
charging original and encoded context copies under the shared operation account.
No UPDATE exception or write-once nullable origin field is introduced. The old
procedure retains context0.2 behavior for its explicitly limited component
scope; complete public acceptance selects the new registered producer.

Retain the existing one-MiB native context artifact bound. Select initial
asserted-source bound 128KiB and capture-profile bound 64KiB; account their
hex expansion and actual native JSON envelope against that original context
bound before INSERT. Include them in operation aggregate accounting rather
than allocating extra uncharged capacity. These finite component limits do not
qualify heap/deadline/native resource behavior by themselves.

The versioned native collector returns exact original context bytes under
original writer/ordinal/generation and current actor/executor correspondence.
The host decoder requires exact context0.3 field inventory, scalar hexadecimal
carriers and complete decoded asserted-source/profile correspondence. Parse
original asserted bytes through the strict decoder; run the registered pure
origin mapping; independently compare report origin and journalOrigin before
acceptance persistence. Never accept a copied host origin basis as issuance.
All installed epoch/target/inventory authority is admitted separately and bound
to that same original attempt.

Decisive schedule: original whitespace/escapes and NUL source preservation;
number/duplicate/Unicode refusal; caller mutation after capture; original-role
mapping despite asserted databaseRole content; original profile substitution;
context update/delete/truncate refusal; context0.2 cannot qualify complete origin;
stale writer/ordinal/generation and changed actor/executor refusal; capacity
exhaustion before registry effects; savepoint/outer rollback; immutable historical
report on repeat while current invocation admits its own context. Use real
native context0.3 producer and original artifacts; fixture profile text cannot
establish installed capture authority.
