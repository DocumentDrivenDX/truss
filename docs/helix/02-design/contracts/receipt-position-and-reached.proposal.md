# Receipt position and visible-data comparison

Candidate design for consumer R7 under ADR-005 and CONTRACT-004/006/007. The existing [complete transaction and coverage domains](bindings/truss-feed-transaction-v0.1.d.ts) govern feed inclusion; [request receipts](bindings/truss-request-receipt-v0.1.d.ts) govern exact replay. This proposal adds a consumer-facing opaque position, not an alternative feed order or journal-only acknowledgment. Public registration, native producer and wire adoption remain open.

## Meaning

`reached` answers whether the original committed group's Truss effects are included in the data visible through the supplied read transaction and admitted scope. It does not promise that current records still equal the original result: later authorized changes may supersede them. It does not prove that arbitrary host writes in the same transaction were replicated. The complete Truss transaction boundary is required even when the group is a subset of a larger caller transaction.

The operation returns available/included, available/not-yet-included, or unavailable with a disclosure-safe reason. Unavailable cannot become false or true. Reads and comparison use the same original read transaction; an observation in a newer transaction cannot certify an older snapshot. On the authority, a fresh authorized snapshot after confirmed commit includes the group immediately. A preexisting repeatable-read snapshot may not. A pending/unknown commit has no durable consumer token.

## Token producer and replay

Recommend a versioned opaque serialized locator whose internal interpretation identifies the original installation/source epoch, producing full transaction xid, selected scope/position profile and original immutable receipt identity. The exact serialization and registered resolver are adoption outputs. A digest may route lookup but cannot replace complete original receipt/token correspondence. The token carries no grant or authenticated actor assertion. Its contents remain opaque to consumers and are validated under current authority on every use.

The producer retains the position basis in the same effects transaction as the immutable request receipt. Native full xid comes from the original operation context, including an all-no-op group with no journal rows. Capture it before finalization, but expose the durable token only after original confirmed outer commit. Multiple groups in one caller transaction may have different receipts while sharing the same complete transaction boundary. Never allocate a synthetic journal seq for a no-op or infer a source epoch from today's pointer.

Equal request-ID/full-input retries return the same original ordered results and token after independent committed-receipt observation. Changed input conflicts. Receipt lookup follows current replay authorization; possessing a token does not reveal a forbidden receipt or transaction. Request-free groups retain their current receipt-free behavior; publishing an independently recoverable request-free token needs an explicit separate producer/profile and is outside this request-enabled candidate.

A token is stable across ordinary process/feed restarts in the same source epoch. Restore/fork epochs are distinct. Matching xid text from another epoch or installation is incomparable. Cross-epoch inclusion requires an explicit independently qualified lineage/seed proof; there is no numeric shortcut. Expired receipt/required evidence produces unavailable(retention), even if the caller remembers its token.

## Authority comparison

Resolve and admit the original committed receipt/position under the current person's authorized scope. Bind its original producing transaction to the supplied native snapshot and installed source epoch. Inclusion requires original commit/visibility evidence for that snapshot; an application's committed flag or current row value is insufficient. A same-producing-transaction observation cannot upgrade its uncommitted receipt into durable proof.

If the token resolves to a committed receipt that is excluded by the supplied snapshot, return not-yet-included only when the qualified resolver can establish its valid identity without crossing disclosure boundaries. If that evidence is unavailable in the snapshot, return unavailable(observation); do not open another connection silently. Exact native snapshot/status routines and bounded original evidence resolution must be selected before this capability is available.

## Replica comparison

The replica compares against its durably applied state in the same read snapshot. Source delivery, assembled fragments, worker claim, source ACK, or a checkpoint label alone cannot certify downstream visibility. Use the original committed application/seed evidence and the existing complete-feed boundary domains.

| Durable visible evidence | Permitted inclusion reasoning |
| --- | --- |
| Exact applied transaction | Token's original source/scope/xid matches the completely applied manifest; all required members/prerequisites and original application commit are admitted |
| Complete coverage interval | Token xid is strictly below throughExclusiveXid and inside the proven gap-free applied interval from an admitted seed/prior boundary. This uses existing safe-watermark/coverage evidence; a larger observed xid alone proves nothing |
| Seed | Original seed cut and complete authorized state/prerequisites independently prove inclusion of the token's committed transaction. A seed ID or activation hash without admitted content/cut proof is insufficient |
| Fragment/partial application, delivery or queued work | Cannot prove inclusion; return not-yet-included only with otherwise complete identity/observation evidence |

All-no-op receipts use genuine committed transaction identity and proven complete coverage or seed. They require no invented manifest member or copying of private request receipt payload into the graph feed. Exact-transaction evidence normally has no manifest for an entirely feed-empty transaction; coverage can account for its absence. Token validity and receipt commitment still need qualified original custody, including a selected way for the replica to admit that source evidence without leaking receipt content. This evidence route is an explicit unresolved producer, not a caller trust flag.

The existing safe-watermark rule matters: transaction 124 may commit while 123 remains open. Applying 124 cannot prove 123 included. Coverage advances only after all required original transactions below its exclusive frontier are accounted for and durably applied. A journal-only `(xid,seq)` checkpoint remains incomparable to this complete visibility domain.

## Proposed facade and limits

Recommend `reachedInTransaction(token, transaction, limits)` on a selected read-visibility capability. This is a proposed semantic name, not a callable export today. The supplied handle is the original caller read-only transaction, never a transaction ID. Explicit selection binds authority versus replica implementation, exact position/resolver/application/seed profiles and current authorization; construction is inert.

The result identifies its versioned comparison domain and includes only the available boolean or an unavailable reason (authorization, epoch/profile, retention, observation/integrity, or controlled-work limit). Exact public error/detail disclosure follows the security workstream. Require bounded token bytes, evidence bytes, retained resolution work and native statements. No waiting or polling occurs inside reached; the host may retry in a new snapshot. It cannot start a feed worker, extend retention or acknowledge data as a side effect.

## Retention and dependencies

The consumer requests a retry promise of at least 24 hours. That is still a deployment selection, not an accepted universal default. Measure any selected promise from qualified first confirmed commit observation and keep the receipt/input/result/position and required comparison evidence protected together. Journal retention alone does not implement it; zero local journal retention remains possible after the required durable archive/feed/receipt protections. Retention cannot silently change a valid token into false. No-op receipts have the same request-conflict/replay obligations.

Truss owns token/receipt/native/feed/application composition. Weft supplies compiled reads where applicable and owns no visibility comparison. UMF gains no new primitive from this design. The security agent supplies current-principal/disclosure admission; the host supplies its authenticated connection and durable downstream implementation. Remaining design choices: token wire/profile and producer custody; authority snapshot evidence; replica source-token commitment evidence; seed inclusion proof; public facade registration; selected bounds; and minimum retry lifetime. Implement only after those original producers are specified and admitted.

## Independent execution schedule

The [RV-01–14 schedule](../../03-test/receipt-position-and-reached-scenarios.proposal.md) belongs to B-007/008/009/014 and CH-02/05/06. It closes the consumer-facing comparison meaning while leaving explicitly named native/profile realization to those work items. A passing parser/type test is insufficient; actual original commits, snapshots, complete downstream application and unchanged denied state are required.
