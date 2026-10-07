# Conditional durable allocation service

Companion to CONTRACT-009 AP03. This design applies only if the owner selects permanent reservation of precommit disclosed IDs. That choice is pending. It does not alter FR-15 or adopt a service in the default toolkit. UMF interpretation and Weft compilation are unaffected.

## Host interface and custody

An explicitly registered installation-bound host service exposes `reserve(originalAttempt)` and `observe(originalAttempt)`. The private original attempt contains exact installation/continuity identity, allocation profile, issuer-issued attempt identity, ordered create ordinals and full admitted scope/authorization evidence. The service retains these exact bytes; callers cannot fabricate an admitted attempt by copying its serialized representation. Counts and aliases do not substitute for create ordinals.

Reserve returns either a committed original receipt with ordered `(createOrdinal, exactBigintId)` pairs and original commit observation, a conflict for reused attempt identity with unequal full input, unavailable with no usable IDs, or unresolved original recovery custody. Observe never allocates. Matching an existing original receipt precedes fresh allocation; equal retries return its original IDs. All numeric transport remains canonical exact bigint text/bytes, never a host floating-point number.

## Ordered allocation protocol

1. Verify the live registered host/installation and original attempt custody; reserve complete request, response, native work and persistent receipt capacity before opening the service scope. Unsupported durability/continuity or missing finite limits refuses before sequence use.
2. Acquire service-local original-attempt arbitration on its own admitted connection. It must not acquire catalog/head/policy/owner/capacity locks already held by the graph transaction. Admission requiring that inversion refuses rather than opening another hidden connection or committing the caller.
3. Resolve an existing complete receipt by full attempt/input bytes. Otherwise allocate once per original create, in original ordinal order, from the same installation object/edge sequence. Validate positive native bigint range, exact sequence identity/configuration and absence of occupied ownership; no resetting, recycling or skip-until-success.
4. Persist full original attempt and ordered allocation receipt in the allocation transaction. Commit under the explicitly selected synchronous durability/replication profile before returning any ID to graph producers or public pending results. Receipt failure rolls back its custody; consumed sequence gaps are permitted and never reused deliberately.
5. After independent original commit observation, return the immutable receipt. Lost acknowledgment retains original attempt/connection recovery custody and uses observe; never allocate a replacement block merely because a response was lost. No partial usable ID list is returned on an unresolved outcome.
6. Graph execution consumes only a matching committed receipt, verifies exact create-ordinal correspondence and installation continuity, and records its original receipt reference in operation custody. Caller graph rollback does not undo the committed reservation or authorize reuse. Graph execution and allocation commit remain separate transaction owners.

## Retention and deployment continuity

Receipt retention covers original unknown-outcome recovery and every graph/history/request reference. Cleanup never recycles IDs and requires complete dependency accounting. If the service cannot preserve required durable evidence within admitted resources, new allocation refuses. Restoring an older allocator state or switching to an unqualified replica cannot resume the same continuity identity; deployment recovery must fence it before allocation. A synchronous local commit alone does not qualify arbitrary backup restoration or asynchronous failover.

The installation bundle must supply the receipt home, exact protected producers/readers, same-sequence binding, effective role/connection paths and complete original deployment continuity profile. These outputs are conditional and are not included in layout 0.8. No generic service can claim the requirement without actual original durability/failover evidence.

## Independent planned schedules

DA-01 concurrent same/different attempts: equal original input yields the same committed pairs; unequal reused identity conflicts; distinct attempts never overlap IDs.

DA-02 allocation/receipt failure and service rollback: no usable receipt is returned; gaps remain permitted; later allocations never deliberately recycle consumed values.

DA-03 crash before commit, after commit and around acknowledgment: no precommit ID disclosure; observation recovers the original attempt without replacement allocation.

DA-04 caller graph savepoint/transaction rollback after reservation: reservation remains committed and later creates receive different IDs; caller transaction control stays with its owner.

DA-05 graph holds policy/head/owner guards while service runs: independent connections do not introduce lock inversion; missing safe admission refuses before sequence use.

DA-06 qualified failover and older-state restoration: independently compare durable receipts and sequence continuity; stale installation cannot allocate under the old identity.

DA-07 exact/one-over count, retained bytes, arbitration work and response limits: complete refusal before usable partial output, with unresolved reservations retained until authoritative settlement.

These tests are not run. If the owner instead selects provisional pending IDs, this service remains an optional proposal and must not become a default host dependency.
