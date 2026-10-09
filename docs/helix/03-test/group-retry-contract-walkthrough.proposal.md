# Mixed group and durable retry contract walkthrough

Author review for US-043/044, consumer R6/R7 and CONTRACT-004/007/009. This
walkthrough uses the existing GroupCapability.applyInTransaction method and
request-present overload. It is not an independently reviewed implementer case
or executed native evidence. Materialize it using the shared case grammar,
operation registry, exact input/result profiles and independent observers.

## Original setup and ordered calls

Admit one complete installed catalog with an authored scalar property, two
objects A/B and a current authorized writer. A starts with value `before` and B
with value `stable`; retain exact original versions and independent state,
journal, receipt, protection and catalog/report inventories. Bind identities
only from qualified original setup results. Register a fresh request identity
in its authorized namespace and retain the complete original semantic input.

The input has two ordered update_object operations: set A to `after`, then set B
to its already-present exact logical value `stable`. Both carry their original
expected versions. Do not turn the second operation into an absent value, null
or a different lexical representation. Invoke applyInTransaction in an original
caller transaction containing unrelated prior caller work. Keep execution
Outcome separate from GroupApplicationResult and its pending response.

## Independent normative observations

| Boundary | Required expected observations |
| --- | --- |
| Successful call before outer commit | Ordered results distinguish A's changed update from B's unchanged update. A's version advances under the selected mutation contract; B's does not. Actual selected A event inventory is complete; B creates no value-change event. Complete input/result receipt is pending in that same transaction. No durable response/token is published. Catalog/report bytes and unrelated caller state are unchanged |
| Confirmed outer commit | Graph changes, actual journal/effects and full receipt share the original commit. Independent fresh reads find A=`after`, B=`stable`, original ordered receipt results and admitted protection. Any consumer token requires its separately selected original position producer and confirmed commit |
| Later independent edit | Change A to `later` using a different admitted action. Retain its complete new effects independently; do not modify the first receipt or redefine its original input |
| Exact original retry | Supply the same request identity and complete original input, including original expected versions. After current replay authorization and committed-receipt correspondence, return the original ordered results. Preserve A=`later`; create no new graph version, journal effect or receipt. Replay must not rerun the old preconditions against current rows or reconstruct results from them |
| Changed original request input | Change one semantic input member under the same request identity. Return request_conflict after current authorized full-input comparison; original graph, journal, receipt and reports stay unchanged. Matching claimed digest never replaces full comparison |

Observe complete inventories at each boundary, not just A/B or selected journal
counts. Storage locks or allowed observation work are not graph changes. Do not
require a particular number of journal rows without the selected codec/effect
inventory. A no-op operation still occupies its original ordered result slot.

## Failure, transport and retention variants

Make the second operation violate an actual admitted precondition after the
first would write. Independent operation rollback must remove the first effect
and full group receipt while preserving unrelated prior caller work; the host
still owns outer termination. Dry-run uses the actual effect/final-validation
path followed by confirmed outer rollback, with no durable receipt/token.

Lose acknowledgment after native COMMIT submission. Retain original attempt,
request identity and full input. Unknown stays unknown until qualified original
recovery: confirmed commit replays original results; confirmed rollback permits
new application under fresh admission. Never replace the request identity to
hide ambiguity or automatically rerun a caller callback.

Repeat with both operations unchanged: the complete result receipt persists
without invented journal events. Apply the RV-12 minimum-window/clock controls
and current authorization refusal before replay. After valid expiry, return
receipt_expired rather than reapply. This case consumes the security owner's
namespace/session/disclosure boundary, not a fixture boolean granting access.

## Executable packet allocation

Materialize the primary mixed/retry sequence as one case with the ordered steps
above. Split failure and retention variants into separate immutable cases with
their own original setup and scope generations; do not execute them against the
primary sequence's mutated state and then rewrite expected starting versions.
The independent fixture producer must establish actual identities, authorized
namespace and native starting inventories before any operation under test.

| Packet case | Required operation sequence and observer boundaries |
| --- | --- |
| Mixed commit, later edit, retry and conflict | Observe initial state; mixed call in adopted scope; pending boundary; confirmed outer commit; later edit and its commit; exact original retry; changed-input conflict. Capture complete graph, journal, receipt/protection and unchanged catalog/report inventories at each applicable boundary |
| Second-operation failure | Seed unrelated caller work before the group, admit A's first update, fail B's actual precondition, then observe group-local rollback inside the still-live caller transaction. Independently commit only the surviving prior work and verify no group receipt or A effect survived |
| Actual dry-run | Run the same mixed input through real final validation in an adopted scope, observe provisional effects without durable publication, then confirm outer rollback. Fresh observation finds original graph and no new journal/receipt/token |
| All-no-op durable result | Apply both exact unchanged updates, confirm outer commit, then retry. Observe the full two-slot receipt with original results and no invented value-change events before or after replay |
| Lost acknowledgment, committed branch | Submit original COMMIT and lose its acknowledgment; observe unknown outcome without publishing a committed token. Original recovery proves commit, then exact retry returns its original results once with no repeated effects |
| Lost acknowledgment, rolled-back branch | Lose response under an independently controlled schedule whose original termination observer proves rollback. Preserve that evidence, perform fresh admission for the same semantic request, and verify one eventual committed application; missing receipt alone cannot select this branch |
| Minimum protection and valid expiry | Use the registered trusted clock/retention procedure around the specified minimum interval. While protected, exact retry returns original results. Only independently proved valid expiry selects receipt_expired, which does not reapply or extend the old receipt |
| Current replay authority refusal | Commit under the original admitted authority, then perform the actual registered authority transition. Exact retry under the now-disallowed caller reveals no retained private result and creates no effects; a fixture denial flag is insufficient |

Original registered observer procedures determine required `(surface, step,
boundary)` keys. Populate the expectation artifact from independently retained
inventories, including explicit empty new journal/receipt inventories where
required; never derive required coverage from the implementation's returned
events. Starting, pending, terminated and committed observations must name their
actual scope/cut. An old snapshot can establish its own observed state but cannot
prove the fresh committed inventory or current replay authority.

Treat durable response loss separately from native termination. An assessor may
record interrupted/unavailable evidence, but it cannot choose the committed or
rolled-back packet branch from a convenient fixture label. Each controlled fault
must retain original native submission, termination and recovery observations.
For both language interchange directions, the reader inspects the writer's
actual committed database and original receipt; it does not reseed equivalent
objects or re-encode the writer result as its expected oracle.

The executable packet still needs original registered setup/operation/observer
artifacts, exact resource/native profiles and independent expected inventories.
Run it through TypeScript and Python on the same admitted layout, then perform
both write/read interchange directions. Shared native routines and agreement
between hosts do not replace independently authored expectations.
