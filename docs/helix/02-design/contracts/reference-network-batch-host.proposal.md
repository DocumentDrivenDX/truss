# Reference network batch host contract

Design handoff under CONTRACT-007/009 and ADR-005. Network consumers submit one complete bounded group per request; the host owns its database transaction and acknowledges success only after confirmed outer commit. Transport routing, authentication and client libraries remain host-owned. No remote transaction handle, create-transaction endpoint or commit-by-ID method is introduced. This contract supplies orchestration rather than an HTTP framework, deployed service or new compiler.

## Request and execution procedure

1. Admit the complete transport envelope and its byte/work/peak limits before full decoding or opening a database transaction. No streamed prefix is an executable partial group. Preserve the original complete semantic input, operation order, aliases and explicit omission/presence of optional fields. Exact numeric wrappers remain strings; JSON numbers cannot replace unsafe integer/decimal carriers.
2. Authenticate through the host's selected resolver and admit the existing qualified request namespace and actual Truss actor/authority. A submitted namespace, request ID or digest is not an authority credential. Derive no namespace from a client display label. Requests claiming retry-safe writes require the existing request-present profile; an explicit request-free operation retains its independent semantics and supplies no idempotent-retry guarantee.
3. Reserve the original complete operation and response/custody resources, acquire one qualified owned database scope, and call the existing group interface once with the complete input and optional admitted request identity. Execute its original receipt-lock/equality/replay protocol. Do not split one transaction across requests or turn a batch-size limit into multiple committed groups.
4. Keep all pending operation results, generated IDs and journal positions private. A successful callback, savepoint release, receipt insert or driver statement completion is not outer commit. A same-transaction replay is still pending and cannot be narrowed to CommittedGroupResponse for network success.
5. Request outer commit through the original owned executor and admit its actual termination evidence. Confirmed commit permits the committed response; confirmed rollback permits only the governing contained failure. Unknown settlement returns the existing unresolved execution outcome and retains original recovery custody. Never publish pending semantic success, guess rollback from a broken socket or automatically execute a replacement group.
6. Construct/send the response only from the admitted committed result or original committed receipt observation. Preserve the complete ordered results, including no-ops and original aliases/versions/events. Later graph edits cannot replace receipt content. Response disposition/observation evidence may differ between initial application and replay while their original semantic result agrees.

## Disconnect and retry rules

Before commit dispatch, a confirmed cancellation may enter the original containment procedure; no disconnected request is automatically retried. A disconnect/cancellation racing with commit cannot promise rollback. Once commit is confirmed, failed encoding, failed response delivery or client timeout cannot reverse the transaction. Retain receipt/recovery protection and reconcile the original attempt under current authority. Never remove its receipt to make a subsequent request look new.

The client retries the same complete semantic request and same qualified request identity after a lost acknowledgment. The host reacquires fresh current authorization and invokes the existing receipt decision procedure; it does not repeat native writes merely because the connection or HTTP request is new. Equal input returns the original committed semantic results, different input conflicts, expired identity does not authorize re-execution, and an unresolved original attempt remains unresolved until original native observation admits settlement. A changed request ID represents a distinct authorized operation, not recovery of the previous one.

Serialize the complete response within its admitted budget. A response too large or interrupted after durable commit becomes a delivery/recovery problem, never a clean rolled-back mutation or partial semantic success. Error/status/transport mapping must preserve this distinction under the existing result and executor error contracts; no new success-like transport code supplies native durability evidence. Do not expose provisional IDs through progress callbacks, logs, response headers or partial bodies before confirmed commit.

## Independent host qualification schedules

NB-01: original mixed changed/no-op/changed group, confirmed commit, lost response, unrelated later edits, equal retry. Return exactly the retained original semantic results and no new graph/version/journal effects.

NB-02: all-no-op request commits its complete receipt; lost response and later edits still replay its original no-op versions/results. Journal absence is not receipt absence.

NB-03: client disconnect before commit dispatch, during native commit, after confirmed commit and during response serialization. Independently observe containment/settlement; no pending response escapes and no unknown commit is relabeled rollback.

NB-04: incomplete/truncated/oversized envelope, unsafe numeric JSON carrier, wrong namespace authority, changed semantic input or expired request identity. Refuse at its actual admission phase without a fabricated new attempt or partial group.

NB-05: two requests with the same admitted identity overlap, including cancellation and original unknown settlement. Native receipt serialization/current-authority evidence determines outcomes; timing alone cannot prove single execution. Confirm no cleanup erases unsettled receipt protection or returns an uncertain connection to a pool.

NB-06: receipt authorization revoked before replay, response exceeds its admitted size, malformed original receipt or lost recovery custody. No current-record reconstruction, incomplete result or stale authority substitutes for the original complete receipt. Keep the broader STP-043 retention/concurrency/resource corpus and STP-044 executor/pool schedules.

These are planned host observations, not deployed network/native receipts. Exact transport/resolver/driver/resource and response/error encoding profiles remain implementation integration outputs. Truss supplies the reusable group/receipt/executor contracts; the reference host composes them without taking UMF or Weft ownership.
