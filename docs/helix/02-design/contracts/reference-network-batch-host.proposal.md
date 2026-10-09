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

## Client retry decision and original request custody

The reference client retains one immutable complete semantic request and its
admitted qualified request identity before first dispatch. Transport attempt
metadata is separate from that semantic request. A retry reuses both original
values; it may refresh authentication without changing the request namespace,
operation order, aliases, original expected versions or exact numeric spelling.
Persisting client intent is host/application policy; a process restart cannot
reconstruct missing intent from current graph state and claim it is a retry.

| Observed disposition | Permitted client action | Required host evidence |
| --- | --- | --- |
| Complete admitted committed result/replay | Settle that original intent once; repeated delivery is the same result | Confirmed original commit or admitted committed receipt under current disclosure |
| Connection loss, timeout, partial or undecodable response | Keep outcome unknown; retry the identical request or reconcile original attempt through its selected recovery route | No inference of rollback from transport absence; original receipt/native settlement observation controls execution |
| Explicit unresolved native settlement | Keep intent unresolved; use original recovery custody | No replacement writer until original termination is independently admitted |
| Input/identity conflict | Stop automatic retry and surface conflict | Full semantic input mismatch under original receipt identity; no new identity generated as a repair |
| Expired identity or unavailable retained receipt interpretation | Stop retry-as-replay; require explicit application reconciliation | Absence/expiry cannot authorize repeating the effect |
| Current authorization refusal | Surface refusal without original payload disclosure | Refreshing credentials does not waive owner-union admission or disclose retained results |
| Confirmed rollback/contained failure | Preserve the original failure semantics; retry only when the governing failure/profile permits | Actual original containment/termination, not transport status or an empty result |

Backoff and finite attempt/deadline budgets belong to the selected client/host
profile and never alter these correctness outcomes. A retry budget expiring
leaves an unknown original outcome unknown. No callback can convert a partial
body or locally cached pending result into committed success. A changed
request ID is a newly authorized application intent with independent effects;
it is never the automatic fallback for conflict, expiry or lost receipt.

Extend NB-01/03/05/06 with a client restart from retained original intent,
partial-body delivery, budget expiry during unresolved commit and independently
changed retry identity/input controls. Compare complete source graph/version/
journal/receipt state before and after; require at most one original committed
effect and the complete original result. These client schedules remain planned
and share STP-043/044 authority, rather than defining a second retry protocol.
