# Interactive consumer read integration

Consumer R8 and catalog-enumeration needs map to SD-005, TD-020/021/022/039, CONTRACT-004/007/010/012 and CH-04/05. This proposal composes existing direct-read and Weft contracts; no second parser/optimizer is introduced. [Committed Weft source evidence](../../04-build/evidence/design-audit/weft-consumer-read-source.json) retains the application-read and Python boundary observed during review. Owner qualification is scoped to its own fixtures; Truss installation, mapping, identity, native plans and public publication remain unqualified.

## Read routes and access plans

All routes use the actual person's read-only transaction, original accepted catalog/layout/codec context and the shared authorization workstream. A compiled artifact's obligations are admitted before its SQL is submitted; query-use/disclosure, current authority and exact buffered-result validation precede publication. Unavailable profiles cannot fall back to arbitrary SQL or unqualified scans.

| Consumer shape | Owning route | Required access path and exact meaning | Bound and qualification gate |
| --- | --- | --- | --- |
| Typed object/edge ID lookup | Truss DirectReadCapability.lookup | Object native type/ID identity or global edge ID; native exact record/retained values and read versus last-written revisions | Existing lookup resource candidate; one authorized logical match, duplicate/incomplete observation refuses. Qualify fixed index and complete logical decoder |
| Business-key lookup | Truss direct object_key lookup | Original ordered complete key/profile; digest routes to full-byte namespace/key equality and authorized object identity. Collisions never establish equality | Existing lookup/key-codec bounds, bucket candidate capacity and complete private match; ordinary-role non-disclosure. No whole-database search fallback |
| Equality over authored keys | Direct lookup for a complete unique key; Weft for logical predicates/partial key or multi-source shapes | Known exact equality/operator/collation and complete key component order; index prerequisites derived from admitted physical mapping | Unique lookup bounds do not apply to partial keys. Compiled page requires bounded result and separately qualified native candidate work |
| Indexed property equality | Weft application-read equality filters | Original Field-to-property storage/home/codec and usable declared index; exact numeric/text/absence/null predicate semantics | Require native index readiness and plan evidence at the admitted catalog/role. Result LIMIT does not bound scanned/filtered candidates; unsupported index/domain is explicit |
| Relationship predicate | Weft HAS_RELATED; direct edge pages for explicit storage-level enumeration | Authored relationship/endpoint/key/multiplicity/lifecycle and direction; existential predicate cannot multiply source rows; native endpoint/relationship indexes | Complete source/related authorization and key-domain binding; refusal for unsupported polymorphism/association or index profile. One-to-many skew included in native work tests |
| Complete entity alias.* | Weft explicit 0.2 entity-page projection | Every ordered Record member, exact tagged presence and recursive descriptor/carrier; bare * excluded. Relationships are requested explicitly, not inferred as fields | No omitted unsupported member. Existing owner descriptor limits apply. Cap RELATED_KEYS columns and each list in the selected Truss application profile; validate all lookahead before returning any prefix |
| Logical keyset page | Weft explicit application-read page | Complete authored unique key in declared ASC order; composite tuple lexicographic seek; exact numeric or qualified text collation | Owner initial LIMIT maximum 1,000. Cursor retains model/binding/read context. Native ordering/index/uniqueness required; same snapshot for stable pages. Equality/different order/partial composite continuation refuses |
| Storage ID page | Truss DirectReadCapability.page | Type/positive object ID ASC, or qualified edge order_key/ID tuple; existing fixed native statements | Existing direct page profile: at most 1,000 requested/1,001 observed rows plus independent byte/work limits. This route does not implement logical business-key order |
| COUNT(*) GROUP BY one property | Weft count-summary | Exact bag count, including join multiplicity; exact mathematical integer text; grouped empty input zero rows; global empty input one zero count | Complete grouping order/LIMIT for grouped output. Index readiness, equality domain and actual aggregate scan/group/sort work separately qualified. No sample, count cap or partial aggregate reported as exact |
| Module revisions/layout enumeration | Truss catalogView and installed layout observation | Complete selected definition/report/revision dependency view under one accepted revision; live installed marker/version independently admitted | Existing catalog-view/resource bounds and current disclosure. Enumeration never combines definitions from concurrent accepted heads or treats core browser validation as readiness |

Existing numeric limits above are design/owner-profile inputs, not latency or native-work guarantees. Keep direct lookup/page profiles separate; the lookup candidate permits larger private matched/context transport than public record output. The general Weft 0.1 language is not silently promoted to the bounded 0.2 application profile.

## Parameterized compiler result and parsed-input boundary

Weft owns model resolution, typed named source parameters, SQL emission, ordered native slots, result descriptors, diagnostics and host obligations. Python receives that artifact intact and passes its ordered parameters through the original admitted executor. It need not parse emitted PostgreSQL text. Truss validates provenance/profile/obligations and exact result metadata rather than reparsing SQL to invent meaning.

The consumer already parses its own statement and requests a parsed-statement integration. Current committed Python compile_json accepts SQL-text requests. Passing a host AST as logical IR is not a supported public entry point; merely serializing a lookalike plan cannot establish resolution/provenance. Record this as a Weft-owned dependency: an explicit versioned parsed/normalized input adapter must preserve the same model/parameter/type/relationship/security/result semantics and produce the same complete compile artifact. No Truss adapter may relabel caller AST data as trusted compiler output.

Until that owner interface is selected, SQL-text compilation is an explicit interim route requiring consumer agreement. Do not claim the no-reparse parsed-input requirement closed. Retain original consumer query/model/parameters so qualification can compare the two routes when available. This interface gap does not block direct key/ID/page reads or current SQL-text backend integration.

## Parsed-input owner handoff

Fresh committed-source review at Weft `5856c73db0342363e64802905a94abb96209d757`
confirms the [same unresolved interface boundary](../../04-build/evidence/design-audit/weft-current-consumer-interface-review.json):
the Python public entry accepts serialized SQL-text compile requests; request
0.2 requires sql and rejects unknown members. The committed presence parser
admits authored JSON-null members but explicitly retains native-null as requiring
a separate profile. That does not close the Truss row-home Item.note mapping.

For R8, Weft must own a separately versioned parsed-input admission boundary.
The consumer supplies data from its parser, not trusted compiler output. The
owner chooses its public syntax-tree/normalized-input grammar and any supported
host-parser adapters. A Rust internal struct or the emitted typed-plan schema
is not a public input ABI merely because it can be serialized. Do not define a
Truss-owned AST grammar or serialize the consumer's tree back to SQL and call
that no-reparse support.

The owner admission procedure must retain these obligations:

| Boundary | Required meaning |
| --- | --- |
| Input provenance | Exact original input bytes, parser/profile/version and supported grammar/subset. If original SQL is also supplied, define/check its correspondence; do not trust a host assertion that it matches the tree |
| Syntax data | Reject unknown/executable node forms, target SQL fragments, ambiguous names, unsupported constructs and invalid scalar/Unicode data. Integers/decimals retain exact token text, never host float values |
| Semantic resolution | Resolve names/aliases/ordered projections, parameters, types/keys/relationships and presence against the same exact supplied UMF/model/binding/profile. A claimed resolved identity or inferred type from the host cannot skip owner checks |
| Lowering | Produce the complete ordinary compiler artifact: ordered parameter slots, descriptors, required integrity/security/host obligations and diagnostics. The input cannot inject target SQL or suppress obligations |
| Resources | Select finite input-byte/node/depth/resolution/descriptor/work limits before decoding/expansion. Exceeding limits refuses the whole input; no partial plan or result |
| Host execution | Truss consumes the original artifact through the same admitted transaction/authority/result path. Parsed input grants neither database authority nor publication permission |
| Compatibility | An unknown parser/input profile refuses before native submission. Existing SQL-text callers keep their selected behavior; adopting a new input route does not widen old backend registrations |

The exact owner request member, version, grammar, public function and registration
remain unresolved outputs. Truss can design their integration obligations and
independent acceptance cases now without claiming that an owner ABI exists.
The [IR-12 parsed-input schedule](../../03-test/interactive-consumer-read-scenarios.proposal.md#ir-12-parsed-input-admission-schedule)
defines semantic parity and hostile-input controls. Equivalent results require
independent expected values; byte-identical SQL text is not necessary if the
owner permits different valid emission. Parameter order, descriptors and
obligation correspondence must follow the declared artifact compatibility rule.

## Index and bounded-work admission

Truss's fixed-layout rule remains: publishing a type adds catalog rows, never per-type tables/columns/partitions/indexes. Consume declared bounded physical optimization/index profiles under their own lifecycle; do not add a per-type index to satisfy this matrix. Logical definitions and compiler fixture paths cannot certify a live physical index. Verify original native relation/index keys, operators/collation/expression predicates, readiness/validity and full stored-domain correspondence under the selected installed context.

Read-only EXPLAIN/EXPLAIN ANALYZE on the disposable qualified corpus observes actual scans/joins/sorts/aggregates, rows removed, buffer usage and elapsed time at representative cardinality/skew, with current identity policies applied. A plan can change with statistics/cardinality: retained plan evidence qualifies its measured tuple, not all data sizes. Enforce selected controlled-work/result/statement deadline and cancellation limits through the admitted executor; arbitrary native database-wide resource guarantees remain separately reported under owner scope. If an index requirement is unmet, the interactive profile is unavailable rather than silently selecting a scan.

Do not force a native planner to claim an index is used merely because it exists. Small-fixture sequential scans can be legitimate; interactive qualification requires the declared scale/threshold and independent baseline. Preserve exact aggregate semantics even when they cost more than lookup. A result limit never grants permission to stop counting early. Oversized grouped output, recursive entities, relationship lookahead or unknown codec/obligation fails the whole public result; no partial prefix is returned.

## Bounded related-list result admission

Committed Weft CONTRACT-004 defines `RELATED_KEYS` as
`{items:[keyTuples],truncated:boolean}` with declared multiplicity, complete-key
ordering and lookahead or equivalent exact cardinality evidence. This intentional
bounded projection is a valid logical result. Whole-result refusal on malformed
or over-budget input must not erase the truncation marker or require fetching an
unbounded relationship. Truss consumes the original owner artifact; it adds no
SQL rewrite or relationship evaluator.

For each selected projection, retain the original bound k, qualified relationship,
direction, target key/codec, multiplicity and read/security context. Admit the
owner's exact proof procedure and its descriptor/obligations before submission.
Under a lookahead procedure, validate the original ordered candidate tuples,
including the extra tuple, before exposing the envelope. At most k complete
items are returned, and truncation is true exactly when the admitted procedure
proves another qualifying item in that same read context. Exactly k items without
end-of-stream or equivalent proof cannot establish false. A short stream caused
by cancellation, decoder refusal or unavailable observation is not completion.

A lookahead tuple is subject to original type/key/codec and disclosure admission
and finite shared work/storage accounting even though it is not a returned item.
Do not expose its key or identity through errors. Predicate, returned items and
truncation must follow the same selected security meaning; raw hidden endpoint
presence cannot manufacture a truncation flag. If that owner policy/proof is
unavailable, refuse the projection rather than guessing false or filtering a
previously computed raw truncation flag in the host.

Related columns and lists also share the selected whole-result account. Exhausting
that account refuses the entire operation; it cannot turn a resource failure into
`truncated:true`, silently lower k, drop another projection or publish earlier
rows. An admitted envelope with true truncation remains complete under its declared
contract. Native candidate scanning/fan-out limits remain separate from k and
from result-byte limits.

IR-07/08 must independently seed k-1, k and k+1 qualifying related items, equal
key tuples with declared bag multiplicity, and an empty relation. Compare exact
ordered items and flags. Include a malformed or over-budget extra tuple after
otherwise valid k items, transport loss at the completion boundary, a second
related column exhausting the aggregate account, and a denied endpoint affecting
the raw candidate set. Compare actual results to the selected owner's independent
security expectation; source row filtering alone cannot qualify relationship
publication. These are implementation-ready controls once the exact owner
proof/security/account tuple is registered; no native execution is claimed.

## Session loss and final publication dependency

The [security owner evidence review](../../04-build/evidence/design-audit/security-publication-lease-loss-review.json)
retains a current-worktree native counterexample: killing the reader backend
releases its transaction lock, allowing revocation to commit while the live
client still holds the original unpublished result. No unauthorized publication
was executed. This contradicts using native session/transaction termination
alone as proof of application-buffer drain; it does not replace or amend the
security workstream's policy semantics.

Every selected read-publication profile must consume the security owner's
admitted publisher/lease protocol through final release/cleanup, including
backend loss, cancellation and buffered-result disposal. A held native read-only
transaction is necessary where selected but cannot supply this entire proof.
Later connection-error detection, cooperative buffer discard or a current-epoch
retry cannot retroactively justify an earlier revocation acknowledgment.
Unknown publisher drain keeps acknowledgment unavailable under that protocol;
it is not successful cleanup or permission to return buffered protected results.

The same boundary applies where reports, receipt replay, enumeration, feed or
reached disclose protected facts. Each capability declares its real publisher
and final-release point rather than borrowing a query-only receipt. Truss wires
that shared boundary into its host adapters and public facades; it does not
implement another policy resolver or invent a lease from caller flags. Exact
issuer/participation/resource/native composition remains security-owned and
must be qualified before claiming the drain guarantee.

## Delivery and evidence

B-008/CH-05 wires existing direct lookup/page/catalog facades and complete decoder. B-012/CH-04 imports Weft's explicit application-read artifact with original Truss definitions/homes/parameters/obligations. The security workstream supplies predicate/use/disclosure and original principal admission; this read work does not duplicate ACL resolution. B-014/PY-02/05 publishes parameterized Python/TypeScript facades only after actual native/public support evidence.

[IR-01–12](../../03-test/interactive-consumer-read-scenarios.proposal.md) supplies independently authored native correctness/access-plan schedules. Keep compiler capability, index readiness, native runtime bounds and latency measurements separate in each receipt. Missing Lakebase/version/extension qualification remains an explicit target gap.

Remaining adoption inputs: original accepted consumer schema and complete native homes/codecs; actual index/statement/deadline profile; cap on related projection columns/lists; current authorization and publication integration; native plan-scale corpus; parsed-input Weft ABI/consumer interim agreement; complete packed Python/TypeScript surfaces. All are within the near-term existing slices. No new UMF primitive or duplicate compiler is required.


### Original publication cleanup and retirement correspondence

The [current security-owner review](../../04-build/evidence/design-audit/security-publication-retirement-review.json) retains two additional scoped counterexamples. Closing one original publication cannot retire every publisher for the same actor: cleanup consumes exact original identity/generation and completion custody, preserving independent sibling buffers and obligations. A terminal identity visible as pending in a retained snapshot is not a reusable publication lease. Read/replay admission must consume the owner’s current freshness/fencing protocol after original shared participation, not infer liveness from snapshot-visible registration or a matching UUID.

Truss consumes this shared protocol for every applicable direct/compiled result, report, receipt replay, feed and reached observation. Unknown cleanup or freshness keeps publication unavailable and retains original recovery; it does not acknowledge drain, refund unrelated capacity or reopen the terminal handle. The owner’s conditional retirement algebra is evidence of stated premises only, not an installed native/multi-publisher proof. Exact protocol/profile and ordinary native execution remain security-owned qualification dependencies. No Truss-local authorization resolver, epoch allocator or competing cleanup registry is introduced.

## Committed presence contract and Item.note adoption control

Read-only comparison of Weft `5856c73db0342363e64802905a94abb96209d757`
with current committed local HEAD `94b2de5` finds no changes in the compiler/CLI
source directories or CONTRACT-004 application-read contract. Dirty security
sources remain separate owner work. The existing contract requires tagged
absent/null/value cells where meaningful and separately admitted native-null
semantics; source JSON-null acceptance does not by itself select the Truss
physical null interpretation. No rebuild or expanded support claim follows from
the newer microsite commits.

Before CH-04 adopts the consumer's optional note projection, freeze three actual
original object states under one accepted Field/codec profile: absent property,
present explicit null and present empty string. Independently expect distinct
logical cells, preserving original typed identity and last-written context.
Include present nonempty Unicode text as a fourth control. Resolve every
selected field's original native-null permission and authored availability before
compiler execution; optionality alone cannot supply it.

Run both direct logical read and explicit Weft whole-entity/scalar projection
against the same protected database cut. Compare each route with the independent
expectation rather than using direct output as the compiler oracle. A selected
projection/binding that cannot distinguish required states must refuse before
any result prefix; SQL NULL cannot become a guessed absent or explicit-null cell.
Observe the complete original descriptor, native cell, decoder and final tagged
public value separately, including zero visible rows and denied current authority.
A nullable scalar SQL result without the required presence discriminator does
not qualify the whole-entity contract. No Truss-local SQL rewrite is commissioned;
Weft retains lowering and the selected joint mapping remains an adoption gate.

## Consumer traversal necessity review

Review of the original Python consumer R8 and its full needs list establishes
relationship predicates and bounded relationship columns, alongside key/equality
lookup, keyset paging and grouped count. It requests no recursive search, path
result, traversal cursor or independently named direct traversal capability.
`reached` in R7 compares an opaque committed/feed position; it is not graph
reachability and must not be implemented by walking relationships.

The existing read-route table remains the consumer implementation boundary:
Truss owns direct identity/key/catalog reads and complete logical enrichment;
Weft owns relationship predicate SQL and registered logical lowering. There is
no consumer requirement for an additional public direct traversal API. Keep
bounded same-cut authorization, exact typed endpoint/relationship identity,
explicit truncation and complete absent/null meaning in their existing routes.
This conclusion does not adopt unfinished Weft APIs or waive parsed-input and
profile compatibility gaps.

FR-31/RD-04/US-023 still require practical one-to-three-hop graph reads, cycle
behavior and the hand-designed-schema/scale benchmarks. SD-005 already assigns
logical planning/lowering to Weft and native execution to Truss. Preserve all
three US-023 criteria and its independent identity/multiplicity/cycle/performance
oracles. General direct-traversal proposals remain unadopted design inputs; their
unique-terminal/path-output question is not reopened as a consumer product vote.
Before advertising any such extra capability, establish a separate requirement
and reconcile its meaning with US-023 and Weft's explicit SQL multiplicity.

This removes an unsupported additional-API prerequisite from the near-term
consumer path, not the underlying graph-read requirement or its qualification.
The source-pinned [review receipt](../../04-build/evidence/design-audit/consumer-traversal-necessity-review.json)
records inspection scope only; no native traversal or consumer integration test
ran as part of this review.

## Committed Weft0.3 refresh

Fetched Weft `1a1c0ad2c26d0cdd7aa6fb7f415abbaa44ab2842` adds explicit
0.3 compile/language/IR requests, exact arithmetic, additional comparisons,
unqualified Field resolution and positional repeated scalar output labels.
The [source review](../../04-build/evidence/design-audit/weft-v03-committed-source-review.json)
pins original contract/schema/backend/emission/runtime bytes. Truss PostgreSQL
still declares only0.1/0.2 language profiles; its native/qualified profile sources
are unchanged and still require17.9 fixture qualification. These additions do
not fix the local16.2 registration gap or supply the consumer parsed-query ABI.
No new compiler build/native test was adopted during this read-only refresh.

Keep the currently admitted Truss version pair closed. Unknown0.3 requests,
carrierName metadata or weft.output.positioned obligations must refuse before
user SQL, not be discarded as optional metadata. Any later positioned-output
adoption must retain every original logical output and scan identity by ordinal,
verify complete native column count/order/unique carrier names and retain ordered
exact row arrays. A Python dictionary or JavaScript object keyed only by repeated
logical output names would silently lose cells. Execute compiler SQL unchanged.

If arithmetic is later added to the Truss backend, consume the owner registration
and all original source/intermediate/candidate-bag capacity checks before
publication. Final-result exactness or postfilter bounds cannot replace those
checks. No Truss parser, arithmetic lowerer or host SQL patch is introduced.
Existing0.1/0.2 artifacts and their qualified subset remain separately pinned;
new source HEAD cannot relabel an older wheel/WASM build or native receipt.

The existing browser-compatible Truss wrapper now explicitly rejects carrierName
metadata and weft.output.positioned obligations in its0.2 compile admission.
Unknown0.3 version pins already refuse. Four mutated responses derived from the
actual pinned f05f2df compiler prove these refusals before any native context
acquisition, including null carrierName and a permissive registered host handler.
All15 wrapper tests pass and strict TypeScript compilation passes. This is a
closed-version integration correction, not0.3 adoption or native publication
qualification; the original committed compiler build pin is retained.

The [Chromium component receipt](../../04-build/evidence/design-audit/weft-v02-admission-browser.json)
now confirms the same four refusal codes in actual Chromium153.0.8010.12, with
zero native context acquisitions. The browser-target wrapper admits and freezes
the unchanged original0.2 baseline response. Its original response, bundle and
source hashes are retained. The probe replays a response from the pinned native
f05f2df compiler; it does not rebuild Rust/WASM, run user SQL or qualify0.3/native
publication. Browser dependencies come from the existing private UMF environment.


## Current-owner frontend replay: original consumer SQL

The [new isolated source replay](../../04-build/evidence/design-audit/consumer-revised-frontend-ee90571.json)
uses exact committed Weft `ee90571a5aa67b6d2e6069220f6e1cc0eec3822c`, its
original lockfile and Rust1.90.0, with the unchanged revised consumer snapshot.
All90 original queries run through the owner test frontend:80 resolve and10
refuse with WFT-NAME-MISSING. The same five relationship-predicate steps per
model remain blocked. No name, SQL, model or expected consumer shape was rewritten.
Original retained module/pin correspondence is checked for each resolved response.
The receipt retains every response digest and diagnostic, plus original archive,
harness/input/output/run identities. The older f05f2df receipt remains historical.

This does not lower SQL, qualify a parsed public ABI, native Truss mapping/plan,
complete logical value decoder or R8 acceptance. Truss's adopted f05f2df compiler
pin stays unchanged. Do not treat current-owner frontend resolution as a released
compiler realization, and do not replace relationship predicates with test-only
alternate SQL to declare consumer-ready support. The next Weft handoff must
resolve original relationship access semantics or an explicitly agreed consumer
contract amendment, then qualify exact produced language distributions and native
Truss observations under the existing full R8 gates.

The checker now accepts explicit exact commit/archive digest and a fresh receipt
basename after its existing ACTION/WORKSPACE/OWNER/TOOLCHAIN arguments. It verifies
all original committed regular-file bytes before harness execution and refuses
existing receipt destinations; no previous review is overwritten or adopted.


## Security Record-home owner handoff — 2026-10-10

The [read-only owner checkpoint](../../04-build/evidence/design-audit/security-record-home-source-review-2026-10-10.json)
records a moving, unadopted `weft.security.record-homes/0.1.0` physical-binding
proposal. Its ten conditional correspondence laws and389 schema observations
had matching recorded source digests at this read. Truss did not reexecute them.
The owner is still implementing/reviewing physical interpretation; shape/formal
results grant no installed mapping, policy or native authority. The security
backend's26/132 acceptance frontier is unchanged.

| Required integration | Truss continuation and owning boundary |
| --- | --- |
| Exact engine/profile | The first proposal selects PostgreSQL17.9, UTF8 and C text collation. The local16.15 candidate needs explicit owner-supported interpretation and independently qualified native correspondence. Keep the actual engine/version plus binding/backend/compiler/storage/security tuple; no target-name alias or relabeled17.9 receipt. |
| Generic storage | Truss supplies original qualified generic property/Record/relationship/Key identities and exact physical source observations to the owner. The first required-column Record-home interpreter cannot be assumed to describe props maps or row-home graphs. Do not create per-type columns/tables/indexes to fit it: ADR-002's fixed layout and DDL-free catalog revisions remain required. Any selected view or derived source requires its original registered definition, complete dependencies and native/host correspondence. A matching owner interpretation is an integration dependency, not a second Truss compiler/resolver. |
| Logical/native values | The proposal's required singular text/boolean/signed64 codecs do not admit optional/null, exact decimal, binary, structured or unsupported transformed outputs. Complete logical-value reads, including absent/null Item.note, remain required. Supply the applicable original domain/presence/carrier meanings; do not erase fields or coerce them into this restricted set. Text NUL has no PostgreSQL text image and must produce the owner's explicit refusal, not a silent domain rewrite. |
| Population and identity | Preserve document/revision-qualified refs, ordered Keys and endpoint role/target/selected-Key/domain equality. Identical source selection may be reused for the same qualified type without merging scan occurrences; distinct types require the owner's exact native discriminator/disjointness interpretation. Bidirectional carrier membership, multiplicity and field-value coherence require actual complete original source observations. Counts, hashes or forward-only matching cannot establish them. |
| Authenticated person | The first subject mechanism is pg-session-user and context is empty. Actual unique subject resolution and current privilege/source/disclosure closure still come from the owner. Caller labels/GUCs and elevated integrity owners cannot supply the authenticated person. Existing R4/R5 and current-authority/drain obligations remain intact. |
| Resource and literal admission | The proposed interpreter requires four-MiB input, depth64, one million work visits and16000000 aggregate retained/copy/normalized UTF8 bytes. These owner requirements need an original bounded invocation under Truss's stricter enclosing account, not fresh per-field budgets or schema maxima as runtime guarantees. Check all known policy/disclosure/application/parameter/domain literals even in dead branches and empty results. |

Continue the original Truss issuer/account/native reservation and guard work
without adopting this moving API. The physical handoff must receive an owner
interpreter and exact public Rust/Python bridge realization, full original
Truss mapping plus ordinary-role/native16.15 evidence, and current security
lease/publication custody before readiness. Source-column codecs do not replace
the separately admitted complete result-cell decoder. Truss's adopted f05f2df
compiler remains unchanged; no policies, semantic interpreter or lowerer are
forked here.

## Registration and obligation custody handoff — 2026-10-10

[The read-only owner refresh](../../04-build/evidence/design-audit/owner-custody-cli-refresh-2026-10-10.json) records unfinished security work on
immutable backend registration. Truss's future query/read admission must consume
one owner-registered declaration and exact target selection, preserving the
original registration bytes and complete opaque obligation parameters together
with every selected-capability provenance occurrence. Matching backend ID/version,
target labels or obligation IDs alone cannot authenticate this correspondence.
Do not call a mutable declaration callback again, reconstruct authority from a
response's obligation names, drop repeated selected origins or accept conflicting
parameters/owner/failure codes through deduplication.

The proposed closed security0.4 response has no generic obligation-parameter
member. Truss must await the owner's admitted registration/selection interface or
explicitly qualified original-host reconstruction before native submission. Exact
host reconstruction requires the same immutable original registration bytes and
selected target, not an independently fetched same-label manifest. This is an
owner interface dependency, not a Truss-owned security registry/resolver fork or
a request to add arbitrary response fields locally. Unknown parameter semantics
remain unsupported until interpreted and natively discharged; retention is not
execution authority. Preserve the earlier original-current-authority/subject/
publication/complete native proof requirements.

The owner found ordinary nested object keys `$serde_json::private::Number` and
`$serde_json::private::RawValue` could be reinterpreted by typed serde conversion.
Its unfinished reader/extraction fixes are not adopted here. Before consuming
that boundary, require raw-string controls covering nested/sibling/order and
non-string values in all four opaque channels: session settings, logical domain,
result domain and obligation parameters. Retaining raw bytes alongside a changed
parsed tree is insufficient. Truss Python/TypeScript adapters must preserve the
same source/tree correspondence and exact numeric carriers without regenerating
unknown content from lossy numeric values.

Future integration tests must cover callback drift after registration, exact
whitespace/number-token custody, repeated-ID parameter/owner/failure conflicts,
complete multi-capability provenance, duplicate/missing/inapplicable selections,
same-label substituted host registration, reserved-looking ordinary JSON keys and
resource exhaustion before copies/comparisons. These are integration exit cases,
not completed native evidence. Owner work is still in progress; no API/profile,
backend acceptance case or Truss installer readiness is promoted.
