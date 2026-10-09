# Local PostgreSQL deadline and installation integration

This handoff applies CONTRACT-007 and the owner-selected pgserver default to
the [installation plan](local-runtime-installation-migration-plan.md). It selects
execution ordering, not a qualified cancellation producer or native time bound.

## Version frontier

On 2026-10-09 the [published pgserver release](https://pypi.org/project/pgserver/)
remains0.1.4; its documented bundled server is16.2. The original local native
receipts independently observe16.2. There is no published newer pgserver release
in that listing to adopt as a solution to missing transaction_timeout. Do not
replace the selected local default with an assumed17.x binary or change the data
directory's major version during startup.

Native statement_timeout and lock_timeout constrain different scopes. Neither
provides an unavoidable deadline for the complete transaction, and an idle or
aborted transaction is still live. Existing callback-failure and rejection probes
observe a live backend after receiver quarantine; later explicit socket closure
and backend termination are separately observed. Client exceptions, coroutine
closure and missing visible writes cannot substitute for that native evidence.

## Selected execution ordering

Use the original admitted invocation/transaction account and its monotonic deadline
for status, verification, installation and migration. Reserve selected forward,
cancellation, containment, retained-evidence and recovery obligations before
dispatch. This handoff introduces no resettable timer or independent account;
exact duration/clock/native producer pins remain inputs of the complete profile.

| Boundary | Required behavior | What it establishes |
| --- | --- | --- |
| Before dispatch | Recheck original deadline, cancellation, exclusive connection/transaction and profile custody. Refuse exhausted admission once, with no control or business submission. | No new native work was submitted by that refusal. |
| Native statement | Use only the profile's registered timeout-setting/submission sequence on that same connection. A remaining-budget statement cap requires exact version/unit/setting correspondence and cannot extend the original deadline. | A qualified statement cap, never complete transaction termination or outcome. |
| Deadline during active work | Close new admission; use the pre-reserved original cancellation/containment procedure once. Retain the original attempt, operation ordinal and recovery reference before publishing uncertainty. | Cancellation was requested only when its original producer proves submission; request alone does not prove termination. |
| Failed transaction status | Keep the transaction and connection quarantined pending original termination/cleanup observations. | Aborted native state, not settled rollback or safe reuse. |
| Deadline near COMMIT | Preserve whether original COMMIT was submitted and its correlated outcome. Missing completion remains commit_unknown; later deadline/cleanup failure cannot overwrite a confirmed commit. | Separate application durability and cleanup/readiness facts. |
| Recovery | Reconcile the same original attempt through its registered read-only procedure. Never repeat DDL, a migration step, an application batch or COMMIT to discover the outcome. | Only the admitted original observation can resolve uncertainty. |

The host owns an externally supplied connection and its operations. LocalPostgres
owns its server lifecycle but does not grant each invocation permission to stop
the entire server or terminate unrelated connections. Its retained directory lease
and explicit close/recovery rules remain independent of per-query containment.
No hidden second connection, pool manager or global process-kill fallback is
selected here. If the required original native termination/whole-transaction bound
cannot be established on16.2, that capability/profile remains unavailable rather
than advertising a host timer as equivalent native enforcement.

## Implementation and qualification exits

The [original statement-timeout probe](evidence/design-audit/pg8000-local-statement-timeout-native.json)
now executes a fixed pg_sleep statement with session statement_timeout50ms on
pgserver0.1.4 / actual PostgreSQL16.2 and pinned pg8000 1.31.5. Original complete
frames are ErrorResponse SQLSTATE57014 followed by ReadyForQuery E, with no
successful CommandComplete. Independent pg_stat_activity still observes the same
backend idle in transaction (aborted). The receiver quarantines and refuses a
new submission without another send. Later explicit closure is followed by
independently observed backend termination and absence of the pending fixture
write; these are separate facts, not consequences inferred from the timeout.

This is a local-trust, fixed-statement component schedule using existing private
dependencies. It does not qualify an unavoidable complete transaction deadline,
original issuer/account/control permission, arbitrary cancellation latency,
ordinary-person/TLS execution or lost COMMIT recovery. The receipt retains
driverPortQualified=false and wholeTransactionDeadlineQualified=false.

Bind this procedure to the original driver producer/account and security services
before publishing a ready installation. Execute independent faults at head-lock
wait, active statement, statement completion, idle transaction, failed transaction,
before COMMIT, after COMMIT submission and after confirmed commit. Compare exact
submission counts, deadline/account custody, original registry effects and actual
backend lifetime. Include loss of cancellation acknowledgement, unavailable backend
observation, retained directory custody and fresh-process reconciliation. Every
uncertain schedule preserves its original recovery association with zero automatic
resubmissions. Supported native observations must retain their exact engine/driver
subset; ordinary statements are not an oracle for arbitrary uninterruptible work.

This closes ordering and classification for the local compatibility task. Native
producer implementation and the complete16.2 installation qualification remain
open, alongside the original issuer correction, canonical guards and populated
migration route. It does not reopen the user's runtime or connection-ownership
decisions.
