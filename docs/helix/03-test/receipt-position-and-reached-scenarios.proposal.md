# Receipt visibility execution schedule

Planned independent native scenarios for [receipt position and reached](../02-design/contracts/receipt-position-and-reached.proposal.md), consumer R7 and existing group/receipt/feed/read obligations. This is a test design, not executed evidence. Use real authenticated source and downstream connections, a complete installed layout/catalog and independent original state/journal/receipt/manifest/application observations. Save generated tokens by aliases; never assert their encoded text or numeric order.

| Case | Original setup and actions | Required independent result |
| --- | --- | --- |
| RV-01 fresh authority | Commit a request-enabled group; begin a new authorized read-only transaction and compare its saved token | Included true; original group effects/journal/receipt commit together; later record edits do not change historical inclusion |
| RV-02 older snapshot | Establish a repeatable-read snapshot before the group commits on another connection; compare in the old transaction and then a fresh one | Old snapshot cannot report true. Return false only with qualified valid-token/exclusion proof, otherwise unavailable(observation). Fresh snapshot reports true |
| RV-03 adopted pending/rollback | Apply in caller transaction with prior caller work; attempt durable-token publication before commit; roll back outer transaction | No durable token or committed result before confirmed commit; no receipt/journal/effects afterward; rollback-only simulation does not reserve request ID |
| RV-04 unknown commit | Lose connection after submitting COMMIT; retain original request input/ID and retry after original recovery | Unknown remains unresolved until qualified original observation; committed branch returns original result/token, rolled-back branch may execute once; no blind callback rerun |
| RV-05 exact replay/conflict | Commit mixed changed/no-op group; edit affected records later; repeat same request/input, then changed input | Same original ordered results/token, no new effects; changed input conflicts; neither result reconstructed from current rows |
| RV-06 all-no-op | Commit an entirely unchanged request-enabled group; replay it; apply source coverage to replica | Original receipt/token exists with genuine full xid and no invented journal event. Replay preserves token. Qualified coverage proves inclusion without a fabricated manifest |
| RV-07 delayed lower xid | Hold transaction A open, commit B with a later xid, deliver/apply eligible evidence, then settle A | B's position cannot prove A included. No coverage crosses unresolved gap; after original complete coverage/application settles A, its committed token can report true |
| RV-08 incomplete transaction | Deliver all but one property/lifecycle/revision member or prerequisite; attempt reached and ACK | No true result or durable complete ACK; required missing member is independently observed. Complete atomic application/commit changes visibility only afterward |
| RV-09 receipt/application divergence | Deliver full manifest but omit downstream effects, or advance a checkpoint without original application proof | Integrity/observation unavailable; delivered fragments/checkpoint/source ACK do not substitute for durable visible effects |
| RV-10 restart | Restart source/worker/replica after original durable application; recover original receipts and applied proof | Same token meaning and result in the same epoch; lost process-local issuer custody requires qualified reassessment, not caller JSON recognition |
| RV-11 epoch/seed | Restore/fork with a different native-issued epoch and coincident xid values; compare old token; separately use a qualified seed lineage proof | Coincident numbers never report true. Incomparable epoch is unavailable until original complete seed/lineage/profile proof explicitly admits it |
| RV-12 retention | Compare before selected retry window ends; attempt premature cleanup; then permit expiry after all protections | Premature cleanup refuses. Valid protected receipts replay. Missing expired evidence reports unavailable(retention), not false; no-op and event-bearing receipts both covered |
| RV-13 current authorization | Revoke module/subject access between token issuance and comparison; use outsider and another request namespace | No forbidden receipt existence, actor, payload, transaction or position detail is disclosed. Security workstream specifies exact safe result; possession of token grants nothing |
| RV-14 bounds/read-only | Malformed/oversized token, unsupported position profile, substituted original transaction/connection, exhausted evidence bound | Refusal before native effects; no worker start, ACK, retention update or new transaction. Comparison uses the supplied read-only snapshot and finite selected work |

The runner records exact layout/corpus/position/security/driver/database/application tuples, original read cuts and observed commit outcomes. Expected state is authored independently. Fresh true results require original inclusion proof; agreement between two implementations alone cannot certify it. Execute the same relevant cases through TypeScript and Python, then interchange saved tokens through the admitted shared resolver. Unsupported/incomplete required profiles remain unavailable and block full consumer qualification.

## RV-12 minimum-window and journal-retention controls

Use CONTRACT-009's original first trusted confirmed committed observation as
the window basis, not receipt creation, client submission or a fixture's claimed
commit time. Independently observe full payload protection at 86,399,999,999
microseconds after that basis. At 86,400,000,000 microseconds, expiry is permitted
only if every longer declared window, retained-event and dependency protection
also permits it; the boundary alone is not a purge permit. Repeat for an
event-bearing group and an all-no-op group.

Delay the first confirmed observation and verify the conservative later deadline.
Restart, move the wall clock forward/backward, and withhold qualified continuity
evidence: cleanup must preserve payload rather than interpreting the jump as
elapsed time. Extend protection concurrently with expiry assessment; purge must
reobserve the latest original protection under its native arbitration.

Select a qualified zero-local-journal-retention profile and complete its required
durable archive/feed handoff. Removing eligible local journal rows must not
remove the protected full receipt, change the original replay result/token or
authorize request reapplication. Conversely, keeping journal rows without a
complete protected receipt cannot manufacture full replay. After legitimate
expiry, replay follows receipt_expired and reached follows disclosure-safe
unavailable(retention); neither repeats mutation or reports false inclusion.
Record original native clock, commit, protection and retention observations;
synthetic timestamps or a fake clock exercise pure arithmetic only.

## Locator wire and receipt transition controls

Planned subcases under RV token/replay/compatibility schedules: exact original
locator equality after confirmed commit and all-no-op repeat; maximum signed64
receipt row and unsigned64 xid without host-number conversion; unknown members,
duplicate keys, wrong alphabet/padding, malformed Unicode, over-bound strings,
noncanonical integers and unknown profile refusal before native submission.
Author the selected encoder's byte-exact golden vectors independently.

Tamper original row/xid/installation/epoch/profile separately and retain denied,
missing and expired outcomes without protected existence disclosure. A current
same-numbered receipt or replica row cannot replace original source evidence.
Old receipt profile without retained position basis must refuse token production,
not acquire today's epoch. A changed new receipt body must fail original full
correspondence; no circular whole-receipt token hash is accepted. Run fresh and
held snapshots and real complete downstream application after native producer
admission; a locator parser pass cannot prove reached or durable retry.

## Authority receipt-proof controls

Under the selected protected resolver, independently verify that the visible
receipt and every required effect/finalization belonged to one real commit.
Attempt raw/incomplete receipt insertion, changed original writer/context,
same-writer pending lookup and legacy receipt-body substitution: none can
publish included. Exercise an exact storage-row locator whose private namespace
would be wrong if supplied by the host; native traces must show derived full
original correspondence and common guard order, with no direct receipt grant.

Compare an old snapshot with no visible row, an expired retained identity and
an unauthorized receipt scope. Absence alone never yields false; a deliberately
missing exclusion producer returns unavailable(observation). Race protection
expiry/current-authority change and backend loss before final release, preserving
private evidence without boolean or existence disclosure. These are planned
native/protected-publication tests, not proof from a shape-valid token.
