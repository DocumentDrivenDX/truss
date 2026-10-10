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

## Reconciliation with the existing frozen-source review

CONTRACT-007 already contains a stronger source-level node-postgres review than the mutable API documentation above. Its [frozen source receipt](../../04-build/evidence/design-audit/node-postgres-frozen-source-review.json) identifies revision `9808955838dd84835c4ca904228c9c2eaeda047e` and source metadata pg 8.23.0 / pg-protocol 1.16.0. Its [frame-source receipt](../../04-build/evidence/design-audit/node-postgres-frame-source-review.json) covers original BufferReader/Parser/Connection/Query bytes. Those records remain the authority for this candidate; the documentation survey does not restart driver selection or override the existing source findings.

The source review identifies two concrete missing boundaries: original CommandComplete/RowDescription/ReadyForQuery capture before public Result conversion, and frame/resource/UTF-8 admission before parser buffer growth and text decoding. Accordingly, a stock per-query identity parser plus array rows cannot implement the selected exact bounded executor. The implementation handoff is a versioned adapter-owned transport/capture integration at those boundaries, with original physical-client/cycle custody. It is not a second SQL compiler or a new public result shape.

| Candidate integration point | Required source-level review cut | Failure that blocks profile admission |
| --- | --- | --- |
| Transport ingress before Parser.mergeBuffer | Exact installed transport hook and dependency closure; complete allocation/overlap reservation before chunk retention or parser growth; fragmented frame and strict UTF-8 handling. | The hook runs after original decoding/allocation, cannot account for socket/parser copies, or observes only completed rows. |
| Native protocol capture before Result | Exact original descriptors, command tag/count text and ready status associated with one original epoch/cycle; independently verified order and full native response enumeration. | Public command/rowCount used as original evidence, unknown cycle, unexpected completion, stale descriptor or event observer installed too late. |
| Queue/cancel/termination coordination | One original issuer queue covering controls, statements, savepoints and settlement; explicit native end/ready evidence after cancellation; retained unknown-outcome custody. | Promise rejection or cancel acknowledgement releases custody, starts replacement acquisition or returns the connection to the pool. |
| Package/runtime boundary | Exact installed package hashes and transitive dependency/runtime tuple plus supported hook compatibility. | Source-tree package version treated as installed build proof, mutable private fields used as authority, or unreviewed driver upgrade retaining prior readiness. |

These cuts are prerequisites for a prototype adapter qualification task. If the selected installed build cannot provide the two preconversion boundaries, record that candidate as unavailable and compare another transport against the same contract. Do not relax exact-value, resource or transaction semantics to obtain a passing adapter. Bun 1.4.2 declaration observations remain a separate candidate survey; they supply no evidence that these native boundaries exist.

Local Bun checkpoint: the [declaration review](../../04-build/evidence/design-audit/bun-sql-declaration-source-review.json) pins the installed bun-types 1.4.2 package metadata and SQL declarations; the observed Bun executable reports 1.4.2. Query is a generic Promise with cancel/raw/values methods, and reserved release returns void. The inspected declaration surface supplies no original RowDescription/CommandComplete/ReadyForQuery capture or predecode allocation hook. This is a declaration limitation, not proof those capabilities are absent internally or a qualification of the executable/dependency closure. Bun public SQL convenience is therefore not selected as a complete Truss adapter on this evidence. A candidate would need separately pinned native integration at the same required boundaries as the node-postgres proposal.

## Selected predecode gate algorithm

The reference adapter gate uses one original physical-client/cycle custody record and an incremental bounded frame scanner before forwarding admitted bytes to the selected driver parser. This selects processing order, not an available driver hook. Installation of a passive observer beside the parser is insufficient: the gate must control forwarding and allocation admission at the selected transport boundary.

1. Before enabling reads, reserve the selected transport's complete conservative receive-buffer, scanner-state and downstream parser capacity/overlap bounds in the original shared account. The actual transport must expose or independently establish these bounds. If it can allocate an unbounded chunk before interception, this integration is unavailable; checking its size afterwards cannot repair admission.
2. Admit each received chunk against the original account before controlled retention/copy. Keep original physical capacity and backing-buffer ownership, including a retained slice's full live backing allocation. Advance scanner offsets without concatenating repeatedly or allocating a buffer from a peer-declared length. Charge scanning and repeated observation to the cumulative work/deadline account.
3. Collect only the fixed native header under the selected protocol phase, then validate the exact message kind and declared length before accepting its body. Startup/authentication and ordinary response framing are distinct; a normal response header rule cannot be reused for earlier protocol phases. Reject unsupported kinds/phase combinations and length overflow. The declared length remains an obligation to validate, never a permit for allocation.
4. Incrementally validate complete field boundaries and the selected message grammar. DataRow field counts must match the original admitted descriptor; the exact SQL NULL sentinel consumes no field body and differs from zero-length text. Reject other negative lengths, overrun, missing/trailing fields or inconsistent framing. Descriptor, command and error/control text follow their selected complete grammar too.
5. Maintain strict UTF-8 validation state across chunks within each original text field. An incomplete code point may continue only within that field's declared bytes; field/frame termination requires a complete valid sequence. Reject overlong encodings, surrogate code points, invalid continuation and out-of-range values. Valid UTF-8 for the replacement character remains content. Never validate the string after lossy decoding or normalize original spelling.
6. Freeze the full validated frame and original metadata under admitted capacity before forwarding it once. Reserve downstream parser growth, conversion and overlap first; a parser that copies into larger capacity needs its actual bound, not the received-byte length alone. Forward only the exact original frame bytes in original order. Do not pass a validated prefix while its remaining frame grammar or encoding is unresolved.
7. Capture the original RowDescription, CommandComplete and ReadyForQuery facts from admitted frames into the original cycle record before driver-public conversion. Full descriptor/command/ready ordering and cardinality are independently checked against the selected command protocol. Data/control observations with no active original cycle refuse success; unexpected sequence cannot be repaired by relabeling it as another query.
8. Release occupied frame/scanner/downstream buffers only after the selected producer confirms their actual lifetime ends. Spent work remains spent. A consumer releasing its reference does not prove the driver's copies were released. The account must include retained completion/error evidence and original recovery custody until their governed retention obligations end.
9. On incomplete frame, malformed input, resource refusal, unsupported response or deadline/cancellation, stop new admission and forwarding under the original cycle. Preserve the actual submitted/possibly applied state; run selected containment/termination without publishing success, manufacturing rollback or returning the connection to the pool. A confirmed physical close may retire lease occupancy while unknown COMMIT custody survives.
10. Qualify the same gate with DH-01–05 and actual PostgreSQL successful/failure/settlement schedules. Receipts pin scanner, forwarding hook, driver parser, allocation producers and runtime source/build tuple. Any change to one of those dependencies invalidates readiness until the exact combination is requalified.

This gate does not parse application values into new semantic carriers, lower SQL, redefine Weft's decoder ABI or replace PostgreSQL authentication. The selected driver still owns its admitted protocol implementation; Truss owns controlled predecode admission and original execution custody. TLS/network buffers outside the chosen controlled boundary must be classified explicitly under the accepted resource scope. Do not claim bounds for them without a qualified producer, or enlarge the selected guarantee by silently treating kernel/native allocations as toolkit-controlled.

## PostgreSQL 17 frame grammar checkpoint

The [PostgreSQL 17 message formats](https://www.postgresql.org/docs/17/protocol-message-formats.html) define ordinary backend frames with a kind byte and length including the length field. DataRow contains a field count, then signed lengths and payloads; -1 means SQL NULL. RowDescription carries each field's name, table/attribute identity, type, size, modifier and format. CommandComplete carries a terminated tag. ReadyForQuery carries idle, active-transaction or failed-transaction status. These facts guide the selected scanner; this checkpoint is documentary rather than native evidence.

The Truss gate requires exact frame consumption after validation. Use checked integer arithmetic for declared offsets and reject lengths below the message's minimum or beyond the admitted frame maximum before growth. Preserve original descriptor ordinals and format/provenance, including legitimate absent table provenance; do not infer a base table from aliases. Admit text format only for the selected RawCell profile. Empty text and SQL NULL stay distinct. A syntactically valid field count still must match the original descriptor for that cycle.

Bounded notices, errors and parameter-status messages require explicit grammar, resource accounting and cycle/session attribution; they cannot masquerade as completion or disappear from the selected transport inventory. An unsupported COPY/replication response closes ordinary executor admission and enters original containment rather than being parsed as rows. Authentication, cancellation connection and startup phases require their own admitted transport procedures; this ordinary-frame cut does not qualify them. A ReadyForQuery observation reconciles actual native state with the original command and ownership, and never grants engine settlement authority over an adopted transaction.

## Gate account composition

Do not reuse the journal JSON parser's limits for wire transport. For compiled reads, the existing [compiled-result policy](bindings/compiled-result-resource-v0.1.candidate.json) is the enclosing candidate; direct reads use their original lookup/page policies, and mutation/private-phase responses use their admitted original operation/phase account. Gate admission always takes the minimum of applicable ceilings and remaining capacity, preserving each counter's original unit and meaning.

For each selected command, produce a bounded transport plan before submission: required descriptor/control grammar and worst-case custody, complete allowed frame lengths, row/field/result totals, ingress/parser/conversion peak capacity and overlap, cumulative scan/copy work, operation deadline and original containment reserve. The plan must charge frame headers, length fields, terminators, notice/error/control occurrences and all physical copies even where a semantic result-byte counter excludes them. A semantic byte ceiling cannot substitute for a wire/allocation bound. Missing native frame or control bounds make that transport profile unavailable before submission.

The reference gate has no reusable independent account. Each admitted frame retains original operation/cycle attribution; asynchronous session messages charge the original physical-client custody account and any applicable operation account, with an explicit finite selected message/cumulative policy. A message arriving outside a query cannot obtain an unbounded free allowance. Actual cleanup/unknown-outcome observations retain their separate original recovery reserve and cannot reset an exhausted operation's work or deadline.

Before BEGIN or command submission, reserve the complete selected transport plan and original containment capacity. Before each growth, reconcile actual remaining original obligations; reject unsupported combinations rather than truncating fields, dropping diagnostics, splitting an atomic request or changing the query. Exhaustion after submission follows original possible-effects/containment outcome. Successful complete native effects cannot be relabeled rolled back because public decoding ran out of capacity. The exact plan producer, counter instrumentation and conservative driver/native bounds are implementation qualification outputs; the existing candidate maxima are not themselves proof that a plan fits.

## Accepted Weft candidate host-obligation integration

The owner acceptance at Weft 3ad557b, reviewed from 2399e30, covers the synthetic candidate host in `tests/truss-postgresql/host_obligation_fixture.py`. The [source review](../../04-build/evidence/design-audit/weft-candidate-acceptance-source-review.json) pins that dependency. Its injected callbacks establish orchestration evidence; Truss must bind them to actual CONTRACT-005 authority and CONTRACT-007 execution observations. This is an integration procedure for that exact candidate subset, not a general obligation interpreter or adoption of layout 0.12.

1. Before any SQL, capture the complete original compiled artifact and admitted compiler/backend/definition/binding tuple. Validate every obligation's full shape, owner, failure code, exact original parameters and known meaning. The candidate recognizes `truss.candidate.context`, `truss.original.complete-read-context` and indexed `truss.original.owner-payload-*` / `truss.original.owner-structural-*` obligations. A matching name prefix alone grants no authority to arbitrary SQL. Resolve each indexed obligation against the original admitted compiler artifact, codec/presence/scan definitions and parameter vector; unknown, omitted, duplicate or altered requirements refuse under the complete selected inventory. Preserve original order and identity. This subset cannot serve unsupported future obligation families.
2. Reserve one enclosing operation account and acquire the qualified live affine transaction through the selected executor. Its complete command mediation covers preparation, every guard, data execution, publication rechecks and containment. Retain actual installation/catalog/layout/model/role and binding observations, complete owner visibility and original authority before interpreting absence or child membership. A caller boolean or fixture authority string cannot establish those facts. Independently admit the full owner union, including owners whose rows will not match predicates or joins.
3. Execute every admitted structural/payload prerequisite in original order before submitting the data query. Preserve its original parameters through exact native translation. Admit each guard's original descriptor and complete result under its registered guard result grammar; for this candidate the complete violation result must be exactly one canonical zero count. Missing, extra, malformed, partial or nonzero results refuse before data SQL. LIMIT, pagination, unmatched join rows and data predicates cannot narrow the guard's owner-wide scope. Guard transport, decoding and authority collection charge the same original operation account as data; no per-guard reset.
4. Execute the unchanged admitted data SQL and parameters only after all prerequisites pass in that same transaction. Apply the selected predecode/frame gate and original native descriptor/completion admission before result interpretation. Buffer the complete bounded semantic result privately. Do not stream provisional rows, rewrite SQL, narrow the selected homes, coerce decimals through host numbers or publish a prefix when capacity expires.
5. Before publication, recollect actual current authority, complete visibility and all original binding/model/target observations through the protected selected paths. Compare against the original admitted execution and enforce CONTRACT-007's actual transaction/query-cycle state. A changed authority or binding refuses publication even when every buffered row is correct. Preserve original data/query and guard evidence for containment; refusing disclosure does not retroactively classify native settlement. Separate pages do not imply shared snapshot continuity.
6. Release buffered results only through the selected original decoder and public execution outcome after full recheck. Preserve any original unknown completion, cancellation or failed cleanup custody; no replacement transaction, pool release or retry follows from a fixture-style exception alone. Read success does not claim host transaction commit. Production callback identity, effective policy scope and full driver/account/dependency binding must be qualified before this procedure becomes available.

Build handoff: the Truss adapter consumes the compiler artifact and exact registered obligations; it does not compile SQL or implement a parallel UMF encoder. The protected context/visibility producers, original prerequisite runner, shared account, complete private result buffer and prepublication observer are one integration unit. STP-039 OJ-01–04 retain the independent original-sales/domain and refusal scenarios; STP-044's driver/account/unknown-outcome schedules qualify the actual executor. Owner compiler acceptance removes an upstream candidate-completion dependency, while these Truss implementation/profile outputs remain open.

## Concrete frozen parser integration cut

The pinned `Parser.parse` invokes `mergeBuffer` before it reads a frame length or dispatches `handlePacket`. When residual bytes exist, `mergeBuffer` may allocate a geometrically grown buffer and copy both residual and ingress bytes. Its growth loop continues while the required new length is greater than or equal to candidate capacity, so an exact capacity boundary can double again. A frame-length check after entry cannot retroactively admit that allocation. Query.handleDataRow then parses cells and may accumulate rows; Query.handleCommandComplete converts the original command message into Result metadata. These are exact reviewed source placements, not installed-hook evidence.

The reference integration procedure is to place the owned incremental gate before the driver parser entry, and forward only complete, fully admitted frames in original byte/order/cycle custody. Before each forward, prove the integrated parser has no retained residual frame and reserve the complete parser/message/string/Result overlap under the original account. After synchronous forwarding, confirm it consumed the exact frame and retained no residual bytes. Those assertions require an explicit versioned adapter integration interface/build, not reading mutable private fields as authority. The selected reference design requires these no-residual assertions. Missing assertions or any residual bytes refuse this profile; residual/growth instrumentation is an independently versioned alternative and cannot silently replace the selected integration. No stock mergeBuffer allocation is treated as bounded merely because the semantic frame size was admitted.

Capture original admitted descriptor, command and ready-status bytes/meaning at the frame gate before forwarding/conversion, then correlate the driver callbacks with that same original cycle. An event listener attached after Query/Result processing cannot supply original evidence. A driver-generated parsed row or numeric rowCount is not a substitute for retained exact native cells/count text. Control/notice/error frames follow their existing complete grammar and account rules; unsupported modes enter containment before ordinary row decoding.

The gate does not own allocation that already occurred in the socket/TLS ingress producer. Before acquisition/command use, the selected transport profile must reserve and instrument the actual ingress producer and simultaneous gate/parser buffers, with its own finite chunk/control bounds. Fragmented-frame admission and no-parser-residual proof do not qualify TLS/native-buffer allocation, asynchronous messages, cancellation transport or unknown settlement. Exact adapter hook/build/runtime/transport tuple and native schedules remain required. This specifies the authoring cut; no driver fork, dependency change or live connection is created here.

### Buffer views and retained backing custody

A frame view’s byteLength is a semantic span, not proof of the physical capacity it retains. The selected runtime/allocator profile must identify original backing allocations and all simultaneous ingress/gate/parser/capture views and copies. Charge retained backing capacity once per original allocation under the shared physical account, while separately charging scan/copy work and each required semantic span to its own counters. Two views cannot obtain two independent allowances, and releasing one view cannot refund capacity still retained by another view, parser, captured evidence or pending publication. Unknown backing identity/capacity or allocator retention makes the claimed physical bound unavailable; do not guess a runtime pool size.

If the integration deliberately copies an admitted complete frame into isolated owned storage, reserve original ingress backing plus destination capacity and the complete copy work before copying. Preserve the source/cycle evidence before discarding an original reference. A smaller copied frame cannot retroactively erase ingress allocation, and dropping a JavaScript reference is not evidence of physical allocator reclamation. Exact runtime instrumentation/conservative producer bounds and the qualified release procedure must establish when capacity may be reused. The gate may not overwrite retained capture bytes to avoid that accounting.


### Selected complete-frame integration state transitions

The reference adapter selects the complete-frame/no-parser-residual branch above. At cycle admission, bind the original physical lease, command ordinal, transport plan and containment reserve. Ingress may accumulate one incomplete frame only within the admitted gate/backing accounts; it never forwards a partial header, length, body or UTF-8 field to the driver. A chunk containing several frames is processed in original order, each with its own complete grammar admission and the shared enclosing budgets. An asynchronous continuation cannot forward a later frame while an earlier frame's capture/parser correspondence is unresolved.

For each complete frame, reserve capture and driver-overlap capacity; retain original exact descriptor/cell/command/status evidence; require no parser residual; forward once synchronously through the selected integrated entry; then verify exact frame consumption, no residual and callback/cycle correspondence before accepting another frame. No callback can independently publish rows, settle the operation or release the lease. Reentrant query submission through a callback remains behind issuer-wide arbitration and cannot replace the active cycle. A failed precondition forwards no frame; a failed postcondition preserves possible native effects and enters original containment, without repeating that frame to repair parsing.

Ready/status observation closes only its corresponding admitted command cycle after all original required messages and result sets are complete. It cannot settle a different command, release a still-owned adopted host transaction or prove outer commit from an unrelated idle message. Gate closure on disposal/cancellation stops new forwarding and retains unresolved original custody. The implementation must supply the exact build-level assertions and ingress producer evidence; this selection is a design choice, not a qualified installed adapter or a claim that stock node-postgres exposes the required interface.

The [private producer port](reference-driver-producer-port.proposal.md) selects original reservation/backing/span/frame consumption interfaces for this complete-frame candidate. It requires runtime issuer registries and actual allocation/consumption observations; tickets and producer receipts do not independently prove native qualification.


## Python first integration target — 2026-10-10

Select synchronous pg8000 1.31.5 as the first Python P0/P1 adapter implementation
target. This supersedes an open-ended Python driver comparison, not the separate
TypeScript frozen-parser target or any release qualification gate. Reuse the
original instance-control experiments and producer port; their historical16.2
observations are not corrected16.15 support. The target composition is Python3.11,
the private corrected pgserver16.15 local tuple and explicit host-supplied physical
connection. No pool, asynchronous callback port, reconnect fallback or managed
TLS target is selected by this local integration decision.

Build one versioned Truss adapter integration with original instance-scoped
command/frame handlers and the selected socket/read producer boundary. Do not
install process-global monkeypatches or use a user event listener as the producer.
Reserve actual ingress backing, capture/parse/decode/copy and containment capacity
before their allocations; the existing post-receive frame hook alone cannot pass.
Capture original ordered descriptor/cells/completion/control state before pg8000
public conversion. The application supplies the actual connection and trusted
registered adapter, not an issuer token reconstructed from a status property.

Implement the original producer-port operations and transaction lifetime registry
on that connection under exclusive dispatch. Bind confirmed control to one native
admission, preserve burned ordinals and original unknown-outcome recovery, and
reject unsupported driver/source/transport modes before native effects. Use exact
registered parameterized statement descriptors; no text interpolation or stock
conversion through floats/dates/JSON supplies the exact result grammar. Driver
selection does not authorize Truss to commit a caller-owned transaction.

Qualification order is original ingress/account and framing first, original
control/adoption/one-use dispatch second, complete current security/native
installation third, then public operations and lost-result/cleanup/reconciliation
schedules. Freeze original source/build/dependency hashes and the actual mode at
each boundary. Independent STP-044 controls and complete PKG-02/08 installed
observations remain required for the controlled-operation profile. Qualify its
actual statement/lock/control observation and containment mechanisms separately
from an entire host-owned transaction lifetime guarantee, following the
[accepted claim domains](reference-local-deployment.proposal.md#controlled-work-versus-native-guarantees--accepted-scope-reconciliation).
PostgreSQL16.15's missing transaction_timeout excludes that hard lifetime claim;
it does not by itself exclude a qualified controlled-operation adapter. Until the
controlled-operation gates pass, that adapter remains unavailable. No stock-driver
API or successful local fixture can weaken those gates. A capability explicitly
requiring the unavailable native guarantee still refuses. Other Python platforms and Aurora/Lakebase must retain
separate target admission. Do not change published package dependencies or claim
usable installation merely from this engineering target selection.


### Frozen Python receive allocation placements

The [source allocation review](../../04-build/evidence/design-audit/pg8000-receive-allocation-source-review.json)
verifies pg8000 core SHA256cac1e505 against the original1.31.5 experiment pin.
The existing FrameFile/Receiver seam is a candidate, not a bounded adapter:
its wire counters neither issue original allocation permits nor charge all copies.

| Source placement | Required original account action before allocation |
| --- | --- |
| Receiver header bytearray(5), memoryviews and read attempts | Reserve header backing and selected view/metadata/read work; each repeated recv_into remains cumulatively charged. |
| Admitted whole frame bytearray(F) and bytes(source) | After original header/length admission, reserve both live frame backing and immutable copy before constructing either; retain original lifetime association. |
| FrameFile header/body slicing | Reserve the new immutable slice backing before slicing. Clearing pending does not prove the original frame is dead or refund cumulative allocation. |
| pg8000 _read bytearray(read-result), extend and bytes(buff) | Reserve bytearray capacity/growth and final immutable copy before the core allocations. A complete-frame shim avoids partial read extension only under its qualified original consumption invariant. |
| Message handler, descriptor/cell parser and public conversion | Admit selected complete message/cell grammar and conservative object/string/list/decoder overlap before dispatch; raw frame length does not bound their object count or retained capacity. |

For body length B=F-5, the existing seam can create whole-frame mutable and
immutable storage plus body slice, core bytearray and final body bytes. Charge
each actual allocation and performed copy even when an earlier reference may
already have died; reconcile live occupancy from original lifetime observations.
This enumeration is not an exact heap formula: allocator overhead/capacity,
header slices, views, metadata, parser products and outbound/control/recovery
buffers require their selected profiles too. Never promote 5+2F+3B to a complete
heap guarantee or assume garbage collection releases occupancy.

Integrate reservation/drawdown at these actual producer placements and retain
original account tokens across callbacks and failure. Refuse before allocation
when forward capacity is unavailable; after submission preserve containment
reserves and original possible effects. Qualify exact-at/one-over, fragmented
reads, parser exception, retained-view lifetime and cancellation using independent
allocation/dispatch observations. Source inspection and the private scalar byte
ledger do not execute or qualify these integration schedules.


### Corrected local control-frame compatibility

The [corrected control receipt](../../04-build/evidence/design-audit/pg8000-corrected-local-control-native.json)
executes the original five control statements through pg8000 1.31.5's frozen
instance seam on actual PostgreSQL16.15. All ten independently expected original
CommandComplete/ReadyForQuery frames match. This supersedes reliance on16.2
only for this control-frame compatibility observation, not role/reset/RLS,
original issuer/account or unknown-outcome support.

The checker now takes --corrected-pgserver plus a fresh receipt basename, verifies
the actual corrected native version and refuses to replace any existing receipt.
Historical16.2 evidence remains intact. This run uses the corrected test Python
environment and appends the existing pg8000-runtime environment's site-packages
for pinned driver/dependency access; it is not clean dependency resolution or a
built Truss driver package. Execute through the retained checker with its evidence
directory on the import path. The runtime tuple, source hashes and original frame
bytes are retained; driverPortQualified remains false. Pre-ingress/account and
original adoption/permission/cancellation/settlement integration still precede
public driver support.


### Corrected native failure and rejection observations

The [post-capture failure](../../04-build/evidence/design-audit/pg8000-corrected-local-control-failure-native.json)
and [server rejection](../../04-build/evidence/design-audit/pg8000-corrected-local-control-rejection-native.json)
now run on the same selected pg8000 1.31.5/actual16.15 local tuple. Injected failure
at original SAVEPOINT CommandComplete capture leaves the backend idle in transaction;
the malformed negative control returns SQLSTATE42601 and ReadyForQuery E, leaving
it idle in transaction (aborted). Both independently observe the pending write
as uncommitted, enforce quarantine without another send, explicitly close the
fixture socket, then separately observe backend termination and absent pending
write. Client failure/quarantine therefore does not imply native termination.

Historical16.2 receipts remain unchanged. Both checkers accept a corrected tuple
and fresh receipt basename and refuse existing output before runtime startup.
The same reused environment/driver-path composition as the successful control
probe applies; no clean installed adapter claim follows. The callback injection
is not arbitrary network loss and the malformed control is not a registered
original savepoint. Original issuer/account/control authority, unknown COMMIT,
durable recovery and complete deadline/containment profiles remain unqualified.
Use these distinct actual states when implementing producer settlement rather
than mapping every exception to rollback or treating a captured command as complete
savepoint confirmation. Independent full driver/native integration remains required.
