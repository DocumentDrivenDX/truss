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
