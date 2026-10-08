# Reference driver hook review

Companion to CONTRACT-007 and STP-044. Documentation reviewed on 2026-10-08; no package version, native adapter or deployment is selected by this review. Bind a concrete build and verify its actual behavior before using any listed hook as evidence. Core remains driver-independent and browser-compatible.

## Documented candidate hooks

[Bun SQL documentation](https://bun.sh/docs/runtime/sql) documents reserved connections, query cancellation, raw results and transaction helpers. Pool reservation can wait with an AbortSignal; cancellation after reservation resolves does not release the returned connection. Reserved connections have an explicit release operation. The reference documentation separately warns that [reserve inside TransactionSQL](https://bun.com/reference/bun/TransactionSQL/reserve) acquires a new connection. Therefore transaction-affine Truss work cannot obtain custody by calling reserve on an already active transaction. These are documented API observations, not evidence of protocol completion or safe pool return.

[node-postgres query documentation](https://node-postgres.com/features/queries) documents array rows and per-query type parser overrides. Its [client API](https://node-postgres.com/apis/client) documents parameterized queries and named prepared statements. These provide candidates for positional exact-text transport and controlled statement dispatch. They do not by themselves prove whole-result resource bounds, cancellation settlement, actual transaction identity or exclusive mediation of all client aliases.

## Required release-profile evidence

| Required boundary | Exact qualification output |
| --- | --- |
| Acquisition and exclusivity | Selected build/API mapping to a physical lease; issuer-wide custody and serialized queue; pool acquisition cancellation/late-client race observations. Calling a high-level transaction helper does not prove all earlier/later host commands are mediated. |
| Parameter transport | Selected extended-protocol path, positional null/text/byte carriers and actual native type correspondence. No simple multi-statement helper for parameterized operation execution; no driver number/JSON/date conversion changes exact values. |
| Result transport | Original ordered field descriptors, exact SQL NULL/text cells and command completion/status. Prove complete native result-set enumeration and pre-materialization limits; an array or raw-result convenience alone does not supply either. |
| Transaction settlement | Original command/protocol observation mapped to committed, rolled back or unknown; drain and termination evidence. A rejected promise or successful cancel call does not resolve outer COMMIT. |
| Session return | Original bounded baseline and all allowed mutations, qualified restoration/cache agreement and confirmed idle protocol state. A release helper must remain unreachable until the CONTRACT-007 cleanup gate passes. |
| Adopted transactions | Actual original native identity/generation and access mode, all compatible aliases sharing one queue, no automatic outer settlement and original host completion handoff. A newly reserved connection cannot substitute for the adopted transaction. |
| Resource custody | Concrete parser/decoder/copy/cancellation bounds charged to the original shared operation and lease accounts. Missing build-level bounds leave the adapter profile unavailable; documented convenience APIs are insufficient. |

Start with owned execution using explicit private reservation and explicit transaction commands if the selected driver can expose the required evidence. Qualify adopted execution independently; do not advertise it because owned execution passes. The implementation task must produce a method-to-CONTRACT-007 mapping, pinned driver/runtime dependency tuple, native protocol observations and STP-044 outcomes before claiming support. This review leaves the driver choice open because the documented hooks do not yet establish all required completion and bounded-result semantics. It does not authorize new pool configuration, network connections or live installation.
