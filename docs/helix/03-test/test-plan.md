---
ddx:
  id: TP-001
  type: test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.prd
      kind: informed_by
    - id: SD-001
      kind: informed_by
    - id: SD-002
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: SD-004
      kind: informed_by
    - id: SD-005
      kind: informed_by
    - id: SD-006
      kind: informed_by
    - id: SD-007
      kind: informed_by
    - id: SD-008
      kind: informed_by
---

# Truss project test plan

## Testing Strategy

Prove the embeddable storage contract against independent PostgreSQL observations, exact value fixtures and real host transactions. Requirements come from the PRD, eight feature specifications and 45 stories; architecture and CONTRACT-001–011 determine the boundaries. This plan is draft strategy, not executable evidence. STP-001–045 allocate all 167 story criteria. Structural allocation is complete; semantic adequacy, shared protocol decisions and implemented tests remain release gates.

Qualification is per implementation, adapter, database version, layout, UMF model/adapter, Weft compiler/profile and selected optional modes. A passing narrower profile never implies full PRD support. PostgreSQL 16 and 17 are the proposed initial targets; the owner qualification decision remains pending. Capture actual patch versions in every native receipt.

| Level | Scope and coverage target | Priority |
| --- | --- | --- |
| Contract | Public request/result/error shape, exact codecs, deterministic bindings and bootstrap refusal; all supported cases in the language-neutral corpus | P0 |
| Unit | Pure algorithms with boundary and adversarial cases: recursive values, keys, group simulation, lock sorting and reports | P0/P1 |
| Native integration | Actual constraints, transactions, savepoints, role isolation, journal and catalog parity on every qualified target | P0 |
| E2E | Host embeds the published package, supplies connections, combines host and Truss writes, compiles through Weft and applies feed records | P0 |
| Performance | ADR-002 V1–V7 and proposed PRD latency/scale objectives; explicitly separate measured results from functional conformance | P1 |

Bun test runs TypeScript development tests under ADR-001. A real Chromium runner exercises the pure browser-compatible core. Bun and Node adapters must independently pass exact transport and host transaction tests; browser success cannot qualify a database adapter. Native tests use ordinary driver clients and independent SQL, not an in-memory database imitation. CI provider and browser harness versions are not yet selected; pin them before B-001 closeout.

## Test Data

Committed language-neutral fixtures cover absence, explicit null, large signed integers, decimal bounds/trailing zeroes, recursive arrays/records, retained unknown values, Unicode key normalization, composite keys, relationships and revisions. Include expected refusals for unsupported selected meaning. Fixture generation may vary object IDs and interleavings using a recorded seed; it must not derive expected values from the implementation under test.

Native bootstrap uses two independently installed databases: the existing SQL baseline and the generated candidate. Independent catalog queries compare complete physical inventories and behavior probes. Concurrency fixtures use separate connections and explicit barriers to force conflicting operations; elapsed sleeps are not proof that a race occurred. Fault injection wraps transport or terminates a designated connection at a named boundary. Mocks are limited to transport faults and pure interface shape checks; integrity, isolation and durability assertions require PostgreSQL.

## Coverage Requirements

| Metric | Target/minimum | Enforcement |
| --- | --- | --- |
| P0 criterion allocation | 100% / 100% | Every stable story criterion has exactly one primary layer and concrete STP tests before its slice starts |
| Required corpus cases | 100% / 100% | Unknown or skipped required cases fail full-profile conformance |
| Required native matrix | 100% / 100% | Missing server/adapter/mode entries are unverified and prevent their support claim |
| Pure-core branch coverage | 90% / 80% proposed | Enforce after instrumented baseline; exceptions require a named branch and rationale |
| Unsupported-semantic refusal | 100% / 100% selected unsupported cases | No successful result that discards selected meaning |

Critical P0 paths are exact persisted values and key uniqueness; atomic catalog acceptance; group validation and rollback; caller transaction durability and cancellation; unavoidable advertised database guards; complete history/feed state; stale read mappings; and role isolation. Code coverage does not substitute for these behavior gates. Secondary work includes performance optimizations, optional prepared statements and independent second-language implementations; each still needs its own qualified evidence when advertised.

## Acceptance Criteria Layer Allocation

The STPs own per-criterion test names and assertions. This aggregate allocates classes without duplicating their matrices. The entries below are the required allocation policy; all story plans now exist, while semantic qualification and runnable evidence remain pending.

| Criterion class / governing area | STP allocation status | Primary layer | Reason |
| --- | --- | --- | --- |
| Schema validity, diagnostics, value/key encoding and retained meaning — SD-001/002 | Allocated in STP-001–045; semantic qualification pending | Contract | Deterministic public semantic behavior |
| Exact persisted values, presence and sequence nonreuse — US-007 | STP-007 AC1/AC2/AC4 | Native integration | Database transport and durable identity |
| NUL refusal and rule/path — US-007 | STP-007 AC3 | Contract | Input semantic diagnostics before effects |
| Cross-row minimum safety — US-014 | STP-014 AC1 | Native integration | Parent-lock participation under forced concurrency |
| Cross-row guarantee classification — US-014 | STP-014 AC2/AC3 | Contract | Honest distinction between engine and database evidence |
| Transaction-local role/grant/capture — US-031 | STP-031 AC1–AC3 | Native integration | Actual database grants, trusted role and pooled reset |
| Named host-extension coexistence/policy/drift — US-030 | STP-030 AC1–AC3 | Native integration | Corpus, role-path visibility and independent physical inventory |
| Layout compatibility and native probe sensitivity — US-029 | STP-029 AC1–AC3 | Native integration | Nonmutating marker refusal and independently corrupted fixtures |
| Corpus aggregation/divergence — US-028 | STP-028 AC1/AC3 | Contract | Complete required outcomes and reviewed mismatch evidence |
| Independent native interchange — US-028 | STP-028 AC2 | Native integration | Bidirectional genuinely independent implementations |
| Contract-only implementability — US-027 | STP-027 AC1 | Contract review | Independent walkthrough without implementation code |
| Corpus shape/alias equivalence — US-027 | STP-027 AC2/AC3 | Contract | Complete normative expectations and identity-preserving normalization |
| Support receipt/version/staleness — US-026 | STP-026 AC1–AC3 | Contract | Exact contract/source pins and missing/failed run visibility |
| Complete evidence-qualified assertion report — US-025 | STP-025 AC1/AC3/AC4 | Contract | Assertion inventory and honest path/opaque classification |
| Authored-key database bypass guarantee — US-025 | STP-025 AC2 | Native integration | Ordinary writer cannot omit or forge derived-key maintenance |
| Complete single-revision catalog enumeration — US-024 | STP-024 AC1/AC2 | Native integration | Independent definitions and concurrent acceptance |
| Catalog enumeration latency — US-024 | STP-024 AC3 | Native performance integration | Public-call p95 over 100 sequential calls |
| One-to-three-hop traversal ratios — US-023 | STP-023 AC1–AC3 | Native performance integration | Independent semantic baseline before p95/planning comparison |
| Bounded edge direction/order — US-022 | STP-022 AC1–AC3 | Native integration | Typed endpoints, qualified comparator and lookahead |
| Direct type listing pages — US-021 | STP-021 AC1 | Native integration | Exact keyset/lookahead and context behavior |
| Direct list request limits — US-021 | STP-021 AC2/AC3 | Contract | Explicit required deployment bounds |
| Type-count page performance — US-021 | STP-021 AC4 | Native performance integration | Controlled 2× cost comparison |
| Direct ID/key lookup — US-020 | STP-020 AC1–AC3 | Native integration | Exact record/key/context observations |
| Incomplete lookup key refusal — US-020 | STP-020 AC4 | Contract | Complete ordered key request validation |
| Partition routing, audit immutability and retention — US-019 | STP-019 AC1–AC4 | Native integration | Actual partition, privilege, rollback and neighbor-state observations |
| Version reconstruction and historical definitions — US-018 | STP-018 AC1–AC3 | Native integration | Complete event/definition loading and independent prior state |
| Safe incremental journal eligibility/order — US-017 | STP-017 AC1–AC3 | Native integration | Observed late-commit snapshot boundary and complete positions |
| Journal writer modes and raw-SQL audit boundary — US-016 | STP-016 AC1–AC3 | Native integration | Native triggers, versions and mode exclusion |
| Atomic journal/origin/envelopes — US-015 | STP-015 AC1–AC4 | Native integration | Native event/state/role observations and real journal failure |
| Catalog race and acceptance serialization — US-013 | STP-013 AC1/AC2/AC4 | Native integration | Observed locking/snapshot interleavings |
| Catalog admission under load — US-013 | STP-013 AC3 | Native performance integration | Defined shared queue timing and sustained-writer load |
| Shared mutation state/diagnostics — US-012 | STP-012 AC1–AC3 | Native integration | Atomic persistent state and version checks |
| Mutation failure/retry inventory — US-012 | STP-012 AC4 | Contract | Exact error/scope/retry boundary with native supplements |
| Multiplicity and relationship-count planning — US-011 | STP-011 AC1/AC2/AC4 native integration; AC3 native performance integration | Native integration / native performance integration by criterion | Unavoidable guards, parent locks and measured planning ratio |
| Endpoint integrity and restrictive deletion — US-010 | STP-010 AC1–AC4 | Native integration | Plain-SQL bypass and competing transactions |
| Retained import content and atomic rebinding — US-008 | STP-008 AC1–AC3 | Native integration | Persisted homes, recovery and journal/revision atomicity |
| Persisted business-key equality/uniqueness and absent-component report — US-009 | STP-009 AC1–AC4 | Native integration | Native constraint arbitration and persisted canonical state |
| Catalog acceptance, persisted constraints, tightened rules and multi-client races — SD-001/003 | Allocated in STP-001–045; semantic qualification pending | Native integration | Real transactions and constraint enforcement |
| Individual/group writes, composition locks, replay and rollback — SD-003 | Allocated in STP-001–045; semantic qualification pending | Native integration | Durable state and competing connections |
| Journal reconstruction, feed positions, snapshot cuts and retention — SD-004 | Allocated in STP-001–045; semantic qualification pending | Native integration | Ordering and reconstruction depend on committed database state |
| Pure traversal/result shape and compiler mapping rejection — SD-005 | Allocated in STP-001–045; semantic qualification pending | Contract | Exact interface semantics |
| Weft SQL/result agreement and read snapshot obligations — SD-005 | Allocated in STP-001–045; semantic qualification pending | E2E | Cross-project consumer behavior |
| Enforcement report classification — SD-006 | Allocated in STP-001–045; semantic qualification pending | Contract | Honest advertised guarantees |
| Every database-enforced claim — SD-006 | Allocated in STP-001–045; semantic qualification pending | Native integration | Plain-SQL bypass must fail or preserve invariants |
| Public corpus/version negotiation — SD-007 | Allocated in STP-001–045; semantic qualification pending | Contract | Implementation-independent compatibility |
| UMF bootstrap repeatability/refusal — US-045 | STP-045 AC1/AC3/AC4 | Contract | Current-model export and coverage obligations |
| UMF bootstrap parity/existing-namespace refusal — US-045 | STP-045 AC2/AC5 | Native integration | Independent physical state evidence |
| Executor shape and parameter transport — SD-008 | Allocated in STP-001–045; semantic qualification pending | Contract | Exact host boundary |
| Host transaction ownership, runtime embedding and role context — SD-008 | Allocated in STP-001–045; semantic qualification pending | E2E | Observable application integration |

No P0 completeness declaration is permitted until all 45 STPs and their stable criterion citations are checked. A criterion spanning several layers has one primary allocation and may have supplementary evidence elsewhere.

## Implementation Order

1. Audit criterion identities and create the remaining story allocations before implementation handoff.
2. Build the fixture reader, criterion scanner and independent native harness; prove they detect a deliberately incorrect expectation or missing required case.
3. Qualify bootstrap and exact codecs before catalog/mutation implementation can depend on them.
4. Add transaction and concurrency cases before implementing locking, replay and journaling.
5. Add Weft consumer, host embedding, isolation and history/feed cases as their semantic gates close.
6. Run broader scale and portability evidence only for the profiles being proposed for support.

## Infrastructure

### Adapter and deployment matrix admission

The matrix manifest enumerates supported combinations explicitly; do not infer support from independent axis passes. Each entry pins runtime/driver versions, native server patch, transport/pooler version and mode, connection affinity procedure, engine/caller ownership, isolation/access mode, actual role/definer capture profile, cancellation/recovery procedure and selected capability families. PostgreSQL 16/17 remain proposed target majors until owner selection; embedded targets require their own engine identity/version and receipt, not a server alias.

| Required combination boundary | Required evidence before advertising it |
| --- | --- |
| Bun and Node direct connections | Independent exact raw-cell/parameter corpus and packaged-consumer execution; no inherited runtime qualification |
| Engine-owned writes at each advertised isolation | Begin/commit/rollback, serialization/deadlock retry, finalizer failure and uncertain commit classifications |
| Caller-owned writes at each advertised isolation | Actual host handle adoption, operation savepoints, preservation of earlier host effects, host-only commit/rollback and rejection after handle completion |
| Caller-owned explicit read-only held snapshot | Unchanged host access mode/snapshot; qualified current-authority coordinator/guard procedure; no forbidden data-connection lock or hidden transaction ending |
| Session pooling | Real borrower reuse with no leaked role/origin/cancellation/snapshot context; adapter ownership and reset behavior pinned |
| Transaction pooling | Same server connection throughout transaction, transaction-local state only, prepared/unprepared behavior under that exact pooler profile; no cross-transaction cursor snapshot claim |
| Non-superuser definer/role-switch profile | Independently observed session/current/acting role semantics, qualification of callable paths/search settings and no coordinator role substitution |
| Embedded PostgreSQL profile | Complete physical/correctness/transaction/role subset independently evidenced; missing native facilities explicitly unavailable |

For every entry, fault probes cover pre-send, server execution before reply, rollback cleanup, commit dispatch and acknowledged commit. Native witnesses distinguish cancellation acknowledgment from confirmed rollback and quarantine unresolved owned resources. If a combination is unsupported, mark it explicitly unavailable with the missing capability/profile rather than skip it inside a passing matrix. Selecting a narrower initial release does not close requirements for required later combinations; retain them as named planned entries. Pair optional journal/role/Weft modes only where their complete required corpus is enumerated. The manifest, not a generated Cartesian product of hypothetical settings, defines qualification scope.

Shared interface negotiation fixtures follow CONTRACT-007: exact tuple succeeds only with required qualification; same version/different digest refuses; unknown required operation/outcome/obligation refuses before native effects; permitted optional metadata remains archived where required. Include cache replay after one changed layout/value/backend pin and an explicit conversion with preserved original bytes/loss provenance. Closed-schema unknown fields cannot become implicit semantic extensions. These are contract tests supplemented by native no-effect/acknowledgment witnesses in the affected story plans.

### Performance experiment registration

The [pooler overhead experiment proposal](pooler-overhead-experiment.proposal.md)
now specifies the US-032-AC3 point-read dataset, paired call boundary, warm-up,
three repetitions and exact proposed mean-difference arithmetic. Statistic
selection and complete fixture/native environment pins remain pending; this
is an execution plan, not a registered or passing benchmark.

Before executing a performance criterion, freeze an experiment artifact containing the exact AC IDs, threshold and units from the governing story/STP, dataset bytes and independent expected cardinalities, selected model/layout/codec/policy/backend/adapter/server pins, index/statistics inventory, hardware/runtime settings, concurrency, warm-up policy, measured call boundary, sample count, paired baseline procedure and raw-result format. An unspecified threshold or baseline leaves the experiment unregistered; do not choose one after seeing measurements. Proposed product targets remain proposed until owner selection, even when a run meets them.

Use monotonic elapsed time for public-call measurements, from API entry through complete validated decoding/assembly; retain exact nonnegative duration text and every sample in call order. For the US-024 100-call experiment, compute nearest-rank p95 from the sorted 100 durations (rank 95, one-based). Record warm-up separately; never discard slow measured samples as warm-up afterward. Errors, timeouts, overflow or incomplete results fail correctness and prevent a latency pass rather than being removed from the distribution. A server-only EXPLAIN measurement is a separate metric and cannot satisfy public-call latency.

For cost/ratio criteria, preregister numerator, denominator, comparable result semantics and aggregate statistic. Pair baseline/candidate on independently equivalent datasets and alternate their execution order to reduce order bias; preserve both raw sequences, cache state and plan artifacts. Zero/invalid denominator or incomparable cardinality yields unavailable, not a favorable ratio. Report each registered repeat independently; no best-run selection or retry-to-green. If the story lacks a repeat rule, the design review must select it before qualification. Optional indexes and refreshed statistics constitute distinct configurations, not unrecorded adjustments to a failed run.

The runner verifies a deliberately failing threshold and a malformed/missing sample fixture before its evidence can support qualification. Performance receipts name the exact registered procedure and measured boundary. Passing correctness is prerequisite; performance cannot repair missing history, reduced traversal scope, omitted required rows or relaxed authority checks.

Scratch databases and roles must be isolated from host application data. Test-owned resources use unique names, cleanup receipts and a dedicated disposable database principal. Qualification runs record server versions, driver versions, model/profile digests, journal mode and role configuration. No secrets appear in receipts. Browser tests import the same pure package intended for consumers and fail on Bun/Node-only imports.

Package consumer qualification targets the initial draft ESM ES2022/declaration distribution. Compare packed file/export/dependency inventory to the selected build profile, typecheck against shipped declarations and execute shipped JavaScript independently of workspace source resolution. Deliberately omit an export, shipped declaration or required dependency and require the qualification harness to fail. Chromium core consumption, Bun assembly and Node assembly are distinct runs with exact loader/build/adapter pins. An ESM pass does not establish CommonJS support, and a declaration pass cannot establish runtime module exports or browser compatibility. Public package/API review remains a design gate before release.

Native test commands are planned as `bun test tests/bootstrap/native.test.ts` and per-area `bun test tests/<area>/*.test.ts`; actual files and harness setup do not yet exist. The existing bounded native-model experiment remains separate evidence. Pin a reproducible runner command and matrix manifest during harness construction rather than claiming these commands run today.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Expected results generated by the same code | False confidence in layout/codec parity | Independent baseline SQL, catalog probes and exact fixture bytes |
| Race tests pass without overlapping | Hidden lock or integrity defects | Barrier receipts and asserted competing-lock state; bounded timeout fails the case |
| Test retries erase a failure | Misleading conformance | No automatic retry to green for correctness; retain first failure and seed |
| Missing target counted as success | Unsupported portability claim | Explicit unverified matrix entry and claim gate |
| Changing UMF/Weft semantics | Rework or invalid read mappings | Pin revisions and rerun contract deltas before handoff |
| Large native suite is slow | Delayed feedback | Isolate independent databases and shard by area; preserve required full matrix at qualification |

Known gaps: catalog document identity, exact lexical numeric preservation, durable no-op replay, historical envelopes/snapshot cuts and database guard coverage remain unresolved in design coordination. Their tests can be specified, but contradictory expectations cannot be declared passing or implemented by silently narrowing requirements.

## Build Handoff

Start pure allocation tooling with E-01 in the implementation plan; the first layout contract/native fixture work follows STP-045 once its original inventory/profile prerequisites exist. Each later build slice requires its TD, STP, initially failing behavior tests and declared dependencies. Closeout includes command, actual versions/digests, required-case counts, failures/refusals and native evidence. Full support requires all allocated P0 cases, the required target matrix and review of every qualified limitation. Document integrity checks qualify the documents only.

## E-01 expected allocation input and comparison

The [expected-inventory schema proposal](../02-design/contracts/story-allocation-inventory-v0.1.proposal.schema.json) names every required story, its complete criterion membership and its expected TD/STP identities. inventoryProfile pins the exact scanner/input grammar; sourceAuthority retains original governing scope evidence. Host tooling separately admits that authority and the original inventory bytes. The input cannot self-approve with a flag, matching digest or scanner-produced count, and refreshing it from discovered files is a separately reviewed scope change. No approved product inventory is issued by this proposal.

Before scanning, admit the complete inert input under finite limits, reject duplicate story/criterion/TD/STP identities and require every criterion's story prefix and each partner's numeric identity to match its declared story. Keep exact original source bytes and source locations for all diagnostics. Parse only the original leading frontmatter as metadata; identity-looking text in examples or later code fences is not metadata. The selected restricted Markdown grammar recognizes the exact named acceptance declaration and test-mapping sections outside fenced code. Unsupported or ambiguous grammar refuses explicitly rather than treating an unreadable section as empty. Planned scanner dependency/library selection must cover this grammar; the current Python audit is a narrower source verifier.

Compare full discovered story identities against full expected identities before counting: missing and unexpected stories both fail. Then compare each story's exact declared criterion set against its expected set, reject duplicate declarations, require the original TD/STP identities and source paths to resolve uniquely, and require each expected criterion to have exactly one primary allocation row in its original STP mapping section. Check all six required allocation columns and exact criterion citation; prose mentions elsewhere do not satisfy primary allocation. Additional narrative probes may repeat a citation but cannot become duplicate primary rows or silently allocate another story's criterion. Missing/extra/conflicting rows fail even when total row counts agree. Preserve explicit source-span diagnostics; never repair or rewrite governing documents during scanning.

Output retains original expected-inventory/profile/authority references, discovered source digests, full expected/discovered/matched membership and every refusal. Report only document allocation, separately from semantic adequacy, implemented case identity, runtime execution and support qualification. An unavailable source/grammar/resource outcome cannot become complete allocation; complete observed mismatch is failure, not unavailable. Order diagnostics deterministically by original artifact identity and source position, with criterion identity as a final tie-breaker. Counts are derived observations, not completeness authority.

Independent acceptance controls delete a whole story/TD/STP trio, replace one trio with another while preserving counts, add an unexpected story, remove/duplicate/rename a criterion, substitute partner identity, put a fake criterion in a fenced example and move a citation out of the primary table. Each must have the independently specified failure or ignored-example outcome under the pinned grammar. Revise the scope only by supplying separately admitted new authority/inventory. Existing fourteen source-verifier corruption controls cover a subset; the expected-inventory/Markdown/source-span parser and these complete-scope controls are future implementation obligations.

### E-01 bounded parsing profile proposal

The [finite parser profile proposal](../04-build/evidence/design-audit/story-allocation-parser-profile.proposal.json) selects a TypeScript host-tooling line-state machine for this restricted grammar, without requiring a general YAML/Markdown renderer. Preserve original bytes and strict UTF-8 scalar decoding, allow LF or CRLF while retaining byte offsets, and refuse BOM, invalid UTF-8, NUL, oversized line/frontmatter or unsupported identity syntax. A leading line containing exactly --- opens frontmatter and the next exact delimiter closes it; admit exactly one column-zero ddx block and one unquoted two-space-indented id scalar in that block. Other frontmatter remains retained source content, not executed or interpreted as scanner authority. Reject ambiguous ddx/id aliases, multiline values, indentation or duplicate keys on that identity path. Artifact type/path and expected identity must independently agree.

Outside frontmatter, track backtick/tilde fences opened with at least three identical markers and at most three leading spaces. Ignore all declarations/headings/tables inside the fence; only a same-marker closing run at least as long with trailing whitespace closes it. Refuse an unclosed fence. Recognize the exact second-level named section outside fences and end it at the next second-level heading. Stories require checkbox declarations with bold exact criterion IDs in the acceptance section. Plans require one six-column primary table: AC ID, Planned failing test, Asserted behavior, Citation or Required citation, Primary layer, and Setup/File/setup/File and setup. These three existing header alternatives preserve current documents. Require the separator row and exactly one row per expected criterion; reject malformed row widths, unsupported embedded/escaped pipes and ambiguous table selection instead of splitting away content. Exact @covers citation tokens are checked in the citation cell, allowing their existing single-backtick wrapper. This profile does not render or reinterpret general Markdown.

Limits are inclusive: 1 MiB expected input and each document, 64 KiB frontmatter, 16 KiB line, 4 KiB path, 768 documents, 256 stories, 8192 criteria, 32 MiB total source, 128 MiB accounted peak, 512 MiB cumulative allocation, 64 million inspection work units and 30 seconds total operation. Reserve original/decoded buffers, identity indexes, sort work, diagnostics and output before allocation; inspected scalar/byte visits and sort comparisons charge work, including repeated visits. Disposal releases confirmed buffers but never refunds cumulative work/allocation. Complete diagnostics must fit the same ledger; exhaustion returns explicit incomplete/unavailable resource outcome without a pass, truncated failure list or partial completeness claim. Enumeration is bounded before opening additional documents; approved input roots and normalized relative paths prevent arbitrary external-file traversal, while paths/digests alone provide no source authority.

The [source inventory](../04-build/evidence/design-audit/story-allocation-parser-source.json) measures the present 135 documents: 841407 bytes total, largest 55924 bytes and longest line 1630 bytes. This establishes only that the source sizes are below proposed lexical bounds, not actual peak/work/time behavior or parser correctness. Independently test exactly-at/one-over limits, CRLF offsets, fenced fake metadata/criteria, unclosed fences, every supported header alternative, malformed pipes and diagnostic exhaustion. Profile adoption and actual bounded implementation/accounting remain open; these concrete limits/grammar are authored design rather than unspecified parser selection.


## Internal observer harness integration

STP-009 now specifies O1–O6 for the internal bucket observer harness: exact deployment/compile and independent role-policy parity, original expected fixtures, internally granted native caller/guard schedules, complete typed/byte comparison, quantitative resource evidence and confirmed owned cleanup. STP-037 supplies module-policy and hidden-disclosure controls. The future observer-native command is not an implemented test. Fold these cases into the exact required conformance manifest only after their selected native/profile/setup definitions exist; parser/source round-trip receipts do not satisfy their expected evidence. Preserve separate case status for compilation, authority/completeness, bytes and resource/containment instead of promoting a partial pass to observer qualification.

## Packed reference-host parity qualification

B-014/B-015's packed reference-host handoff specifies twelve required consumer scenarios, including clean public exports, real-browser pure core, inert construction, public mutation parity, optional Weft, host transactions, disclosure, disposal/recovery, explicit tooling, owned teardown and separate runtime claims. Expected state comes from existing story criteria and independently authored fixtures, never a reference-only SQL bypass or generated implementation snapshots. Workspace declaration/source tests do not establish packed consumption; browser/Bun/Node/driver claims remain separately scoped. Suites are planned under tests/package, tests/reference-host and tests/browser; no harness execution is claimed here.

Bun SQL candidate qualification must test original host transaction identity versus unrelated reserve, engine/caller ownership, explicit savepoint collisions/lifetime, exact parameter domains/nulls, raw buffer null/encoding/duplicate columns, native command/affected-row metadata and decoder failure after a successful write. Cancel-request/flags/rejection never establish termination/reuse; prove original protocol/native/registry/resource outcomes independently. Pinned declaration review is design evidence only; Node/pg and browser portable-core claims remain separate selected targets.

Explicit savepoint schedules create A/B/C, rollback to B and expect B live/C invalid, then release A and expect A/B invalid with retained effects still pending host commit. Test same-name external shadowing, foreign/forged/stale handles, namespace issuer conflict, counter exhaustion and concurrent host control. Aborted-state release cannot claim recovery; confirmed rollback-to revalidates native transaction but does not rewind cursor position or sequence allocations. Lose each control completion independently and require unknown/unusable custody with no blind replay or caller transaction termination. Tests remain planned for the selected adapter/native profile.

Exact parameter transport schedules test contiguous/duplicate/missing/out-of-range slots and original SQL identity, with no cast rewrite or slot renumbering. Observe actual native received values/domains for high-range integers/OIDs, exact decimal exponent/negative zero, null/boolean, Unicode/SQL-like text, JSON large numeric tokens and complete typed arrays. Undefined/JS numeric/object fallback and JSON reserialization must refuse this candidate. Inspect native parameter format/preparation and transaction outcomes independently; parameterless trusted statements cannot use semicolon heuristics or simple multi-statement fallback. Planned driver tests do not follow from source/type checks.


Positional result qualification requires independently authored duplicate-name/column-order and exact-width fixtures, empty text versus SQL NULL versus JSON-null text, multibyte/invalid/truncated encoding, large numeric and temporal text, wrong native type/format and missing/extra descriptors. Exercise original metadata with zero-row RETURNING, absent/rounded/noncanonical counts, explicit command-specific zero mapping and multiple completions. Inject decode/resource failure after a confirmed write and independently observe retained pending effects, native termination, transaction usability and recovery custody; require no success, false pre-native refusal or automatic replay. Buffered-row completion and public command/count cannot satisfy commit/protocol evidence. Cases remain planned for the selected original adapter profile.


Host issuer qualification uses two distinct wrappers of one actual transaction, two transactions sequentially reusing one actual connection, two original issuer objects with equal metadata and two compatible assemblies. Independently observe single-custody admission, epoch permanence through savepoints, epoch change only at actual begin and permanent old-handle refusal. Barrier an end/rebegin between initial adoption observation and publication; require no stale handle. Lose end completion and retain original quarantine; race duplicate adoption with the first claimant's failure without overwriting its recovery. Exercise host statements between completed Truss calls, forbidden concurrent bypass, coordination-revision drift, forged handles, epoch exhaustion and restart with equal tokens. Native hooks/exclusion and actual outcomes need original selected driver evidence; mocks/type brands alone cannot qualify caller adoption.


Savepoint resource scenarios independently exercise 64 total native depth versus 64 Truss-only handles, 8192 creation attempts including failed/unknown submissions, retained-record/peak/cumulative/work ceilings and 32768 normal controls. Release and rollback do not reset cumulative counters or name uniqueness. Exhaust normal controls with live boundaries and verify previously reserved cleanup remains possible under actual native usability; no new creation borrows cleanup allowances. Ancestor invalidation releases only confirmed descendant reservations. Unknown creation retains depth/record custody. Test two assemblies sharing one epoch and host-created stack entries; unknown host depth refuses the finite candidate before creation. Actual producer costs and metering remain unqualified.


Savepoint cleanup arithmetic controls verify the simultaneous 128 outstanding permits, cumulative 16384 cleanup and total 49152 normal-plus-cleanup ceilings. A failed/unknown submission consumes its category and total charge. Repeated rollback-to cannot replenish a single-use permit: further dependent work requires independently charged replacement cleanup reserves. Exercise normal capacity remaining with exhausted total/cleanup capacity and cleanup capacity remaining with exhausted total; all independent limits must hold, without retry or detached extra resource ledgers.


Host stack tests start from independently confirmed fresh begin, interleave host and Truss boundaries, shadow a host name twice and independently expect rollback/release to target the latest ordinal while preserving older occurrences. Verify host ancestor control invalidates the correct Truss descendants. Adopt a preexisting transaction without complete original stack history and require unsupported finite-profile admission; driver callback nesting must not invent zero depth. Lose control completion, bypass mediation or inject an unreported driver-helper boundary and close further admission with original quarantine. Native transaction status alone cannot reconstruct the stack. Cases require actual original host/driver mediation and native completion evidence.


Command-completion controls consume the fourteen independently authored [tag vectors](../02-design/contracts/bindings/command-complete-v0.1.vectors.proposal.json), then observe actual selected native completion independently. Test INSERT's fixed middle zero, SELECT versus mutation count meaning, high/max uint64 counts, overflow, canonical ASCII grammar, no-count descriptor/category mismatch, missing/multiple completion, EmptyQueryResponse, PortalSuspended and write failure. COPY tag recognition cannot qualify COPY transport. CREATE TABLE AS cannot be treated as a guessed no-count DDL. Independent driver observations must preserve exact original tag/count or prove an equivalent producer; fixture syntax alone does not qualify native metadata.


Query-cycle controls independently pair ordinary/savepoint completion with active transaction state, native error with failed state, qualified rollback-to with restored active state and actual end with idle state. Inject stale ready events from another borrower/epoch/ordinal, missing cycle completion, malformed state, intervening notices and delayed completion after disposal. Idle after a data operation invalidates the epoch but cannot choose commit versus rollback. Sent COMMIT with missing confirmation remains commit_unknown; confirmed native commit followed by bookkeeping failure preserves its original outcome. Command result, native cycle, transaction outcome and resource release each need separate expected evidence. Caller-owned end observation never authorizes Truss to terminate the host transaction. Tests remain planned for the selected nonpipelined adapter profile.


Failure-order tests combine serialization/deadlock errors with uncontained caller/engine scopes, confirmed rollback, unknown connection outcome and sent-COMMIT loss. Require no retry from error identity alone. A qualified terminated serialization/deadlock with known caller transaction state reports whole_transaction retry without Truss ending the host transaction; its failed generation remains closed to ordinary calls. Operation-local rollback never narrows the restart to the Truss call. Exercise a late cancellation after confirmed commit, native timeout without original mapped cause, malformed/unknown native codes, privilege/read-only errors and hostile driver exception hooks. Observe original submission/cycle/containment evidence independently and verify fixed public classification plus protected custody; omission of public SQLSTATE cannot change retry/outcome. Cases remain planned for the selected native mapping.


The twelve [failure-order semantic fixtures](../02-design/contracts/bindings/failure-order-v0.1.vectors.proposal.json) supply independently stated classification, retry scope, original-generation admission and unresolved-recovery expectations. Each observation must be produced by actual original native/host barriers under the selected mapping; fixture strings cannot become self-issued evidence or error-message matching. Compare outcomes separately from handle/resource state. A known failed caller scope can report whole-transaction retry while its old generation remains closed, and ordinary pending host durability alone is not unresolved library work. No fixture permits automatic replay or Truss whole-caller termination. These are planned expectations, not executed adapter cases.


Cancellation-lifetime regression: after confirmed operation rollback/restoration in a caller-owned transaction, independently observe native usable pending state and preserved earlier host writes, while the cancelled Truss context refuses new data calls. Another wrapper/duplicate adoption cannot erase the latch. Original containment/recovery remains allowed under its existing authority, without Truss whole-host termination. Explicit separately qualified re-adoption needs reconciled original custody and fresh original native/host verification; it is not automatic reuse.


### Original driver prepared execution parity handoff

For the selected Truss driver profile, consume original Weft artifacts without SQL/cast/slot rewrites. Independently author the stored fixture and expected exact values; never derive these solely from compiler SQL or decoded results. Execute each artifact first through the actual selected host driver parameter API and separately through the independently maintained native oracle. Retain original parameter position/logical/native domains, raw transport, actual result descriptor/tag/count and original obligations/outcome evidence. SQL PREPARE through escaped SQL literals is a separate native emission witness and cannot substitute for the driver bind.

Test multiple sequential executions of the same prepared SQL with distinct values, exact integer/decimal boundaries beyond host-safe ranges, Unicode/quotes/backslashes, NULL versus empty text and declared typed arrays. Guard/check statements share original parameter allocation and transaction/context; a zero reported violation does not replace complete guard execution evidence. A failed admission must submit no SQL; a postsubmission decoder/obligation failure requires original containment and cannot replay automatically. Compare direct Truss and compiled reads under the same selected mapping/authority while keeping their expected fixture independent. Driver-only success cannot adopt an unreviewed Weft layout or qualify caller ownership/cancellation. Exact driver/build versions and native receipts are still required.


### Transform final-state scan acceptance

Construct two independent records whose proposed business keys swap: under an explicitly admitted allow/final-state profile, validation must avoid a spurious sequential collision while preserving actual unique final keys. Under forbid, the same fixture must reject any governing reserved-key transfer rather than receive an implicit transform exemption. Then transform both to the same final key and require both original contributors in complete diagnostics. Exercise a prior-state dependency changed by another candidate and verify the callback sees original prior state exactly once, while final rules see the complete candidate graph. Include absent and opaque values, affected edges, a hidden disclosed violation, over-budget diagnostic inventory, lost candidate checkpoint and post-validation persistence failure. Original callback counters and independent before/after graph/journal observations must show no replay or partial accepted effects. Native scan/store/rule/resource and report profile execution remain planned.


Transform native key replacement schedules must compare allow and forbid policies, unaffected live keys, preexisting and newly required tombstones, immediate native one-per-object/full-key constraints and guard generations. Inject failure after complete old-membership deletion and halfway through replacement insertion; qualified rollback must restore all original memberships, values, versions and provenance without callback replay. Independently attempt concurrent canonical lookup/write and ordinary direct SQL during the transient gap; admitted exclusion/privilege behavior must preserve the governing snapshot/authority semantics. Native statement triggers must not emit extra semantic record deletions or duplicate version changes. These native/profile cases remain planned.


### Isolated transform custody schedules

For an explicitly selected versioned isolated bridge, inject duplicate, foreign and late original result messages; race cancellation against a valid callback result and require the original latch to prevent late candidate publication. Timeout after work submission cannot resubmit the callback. Separately observe valid result retention and worker/process termination/resource cleanup; the former cannot certify the latter. Test wrong module/export/registration/environment, lossless exact input/result transport, forbidden capability transfer and unknown termination retaining original custody. Cooperative callback fixtures must not claim hard preemption from timers. Current synchronous public callback remains unchanged; isolated bridge implementation/adoption and native host evidence remain planned.


### Historical transform repeat schedules

Accept an independently chosen transform request, then replace current registration with a different pin/function and advance the catalog. An authorized exact original request must return its retained report/IDs with zero callback and graph/key/journal/head mutations; it cannot use the new registration as provenance. Change one incoming semantic profile/parameter and verify no exact-repeat classification. Remove/duplicate/substitute one original manifest/recognition artifact, corrupt its bytes or deny current owner authority: each prevents report disclosure/reuse despite an active matching callback. A supported historical reader with no active old callable may interpret original report evidence without executing code; unsupported interpretation remains unavailable. Native/archive/reader qualification remains planned.


Node-postgres candidate qualification must independently verify original full command/count capture before Result number conversion, duplicate-name positional rows, text-format identity parsing, SQL NULL/empty distinctions and exact null/string parameter transport. Exercise timeout rejection before ReadyForQuery, queued versus submitted cancellation, foreign/stale ready events, host transaction/control aliases and unsupported pipeline use. Bind all evidence to an immutable selected package/protocol/runtime/server build; mutable upstream source review is not executable support.


Frozen driver protocol capture schedules must show original tag/descriptor/ready observations bound before public count conversion, including counts beyond host-safe integer range via independent protocol fixtures. Reject stale epoch, foreign cycle, unexpected multiple completion and unmediated concurrent controls. Test timeout callback before actual native ready, COMMIT versus unrelated idle-ready, transaction rebegin on the same client and queued versus submitted cancellation. Source pg 8.23.0/pg-protocol 1.16.0 metadata at the pinned revision does not qualify installed package/runtime behavior; native production tests remain planned.


### Candidate driver predecode controls

For CONTRACT-007's frozen-driver proposal, independently supply original protocol bytes: valid UTF-8 split at every multibyte boundary; valid literal U+FFFD; malformed and truncated UTF-8 in values, names and control text; invalid field lengths/counts, missing cstring terminators and unexpected trailing packet bytes; unsupported binary descriptors; oversized declared frames and fragmented frames that never complete. Assert refusal before lossy conversion or unreserved retention/allocation, using original byte and allocation observations rather than decoded-result equality. Observe parser growth/copy overlap and socket buffers under one ledger, and prove unknown termination retains custody/reserves. These are required future controls, not passing native evidence.


Package closure qualification additionally consumes B-014's independently reviewed public API inventory and exact shipped build manifest. Inspect every reachable static/dynamic/reexport/conditional-export dependency per selected entry, then exercise each claimed loader/runtime; bundler removal is not an exemption. Reject a leaked private source path, undeclared/global/workspace-resolved dependency, forbidden host-only core import and shipped runtime/declaration export mismatch. Spy on connection, SQL, registry/compiler registration and worker startup during separate import and construction phases, including optional entry imports. Fixtures supply only explicit declared dependencies and host services. These planned controls prove their selected distribution boundaries only; they cannot qualify database behavior, Node from Bun, or unselected loader profiles.


Reference-host lifetime qualification includes two compatible packed assemblies sharing one qualified supplied executor and actual adopted transaction. Admit/rollback an operation through the first facade, dispose it and construct another inert facade; confirm the host transaction remains live, the other facade's ownership stays intact and new native admission consumes a fresh ordinal from the same original issuer. Reuse of the old capture refuses. Spies independently confirm zero SQL/registry/counter allocation at import/construction, no executor/host-registry disposal and no host whole-transaction completion by facade disposal. Lose original counter/epoch state or native owned-connection end evidence and require unavailable/quarantined admission rather than a new wrapper resetting identity or budgets. These planned packed/native cases supplement STP-044; they do not create a public counter API or infer host qualification from a declaration pass.

### Integration profile selection consistency

Use the first PostgreSQL milestone's complete selection rows as independently reviewed required membership. Before integration-run admission, verify original source/review correspondence and consistency among installation inventory, values/keys, executor ownership, Weft binding, fixture scope and finite resource profiles. Exercise missing/proposed/unreviewed rows, stale hashes, cross-row layout/codec mismatch, unmediated host command paths and omitted required fixture capabilities. Refuse before deployment or runner invocation. A source experiment may preserve unresolved selections only under its explicit narrower evidence claim; it cannot qualify the complete milestone. Preserve historical manifests and invalidate affected current selections after source, authority or scope changes. No manifest-schema pass substitutes for native behavior or owner adoption.

### Private operation registry retention qualification

RT01–RT06 cleanup qualification includes finalized zero-touch operations, mixed operation/touch cohorts and retained references to original operations. Reject finalized-but-live, commit_unknown, backend-disappeared and zero-unfinished-only settlement controls. Retain original bytes and full dependency membership; dangling touch/archive/group/recovery references, deletion of current cleanup custody, count-only deletion proof and guessed capacity reclamation fail. Race original dependency/authority changes across selection and exclusion; actual drift preserves the whole candidate under original containment. Unknown completion retains original recovery and unsettled capacity; later absence alone cannot acknowledge cleanup. These planned cases require exact extended selection/evidence and native producer profiles, not phase-label/source validation.

The private cleanup selection's eighteen schema controls are scoped source evidence only. Native retention qualification must independently reject its shape-valid duplicate membership, out-of-domain identity and wrong snapshot/settlement artifacts, and prove complete absence for an empty dependency array. The 512-row schema boundary does not prove pre-materialization bytes/work/clock accounting or complete collection. Original source/hash and actual selected registry/native correspondence remain required.

Mixed-custody cleanup resource tests combine operation and touch rows at 512/513, then independently reach per-row, aggregate evidence, repeated decode/copy, native transport expansion and peak-memory limits. Identical artifact identities backed by distinct actual copies remain charged. Recollection and transfer evidence consume the same enclosing attempt ledger. Missing pre-materialization admission refuses before unsafe buffering; unknown termination retains original cleanup recovery and capacity. Keep the touch-only profile as a distinct historical candidate, not silently migrated support.

Cleanup dependency closure cases include an unselected incoming recovery reference, selected outgoing reference, multi-home cycle, duplicate reference occurrences, equal IDs in distinct home kinds, same typed identity with conflicting bytes, unknown dependency kind and newly introduced reference during RT04. Expected outcomes are independently authored complete graphs. A retained consumer blocks deletion without qualified acknowledged transfer and post-removal resolution proof; a remove-with-cohort target outside exact selected membership refuses. Empty outgoing references with a hidden incoming consumer cannot pass absence. Resource limits charge repeated occurrences and exact-byte comparisons even when expansion is deduplicated. These remain planned native producer tests.

Private cleanup result cases independently compare exact admitted/removed membership, full preserved dependency/disposition coverage and actual capacity before/after values. Reject count-only success, omitted/extra row, foreign recheck/context/attempt, substituted capacity evidence and result archival dependent on deleted source. Pending shape cannot advertise committed durability or reusable cleanup permission. Lost response/commit completion retains original recovery; confirmed rollback invalidates pending effects. These are planned semantic/native controls for the original private result, separate from public feed retention.

Bounded cleanup collection includes a settled producing transaction whose aggregate carriers exceed one attempt's decode budget but whose independently selected cohort fits. Exact-PK snapshots must retain all fields, require one row each and preserve unselected dependency evidence. Missing/multiple selected rows, wrong native identity casts, phase filtering, LIMIT1 and a hidden incoming reference refuse. Repeated snapshot queries charge one cumulative attempt ledger. The full-transaction observation is separately admitted only when its complete resource profile fits; it cannot become an unconditional cleanup prerequisite or a silently truncated proof.

Cleanup discovery tests independently author mixed typed identities with negative signed legacy IDs, numeric-order traps such as 2/10, equal integers in different row kinds and multiple touch discriminators. Exercise first-page/continuation and 512-plus-lookahead boundaries, duplicate/malformed/nonmonotone identities, stale cuts, authority revocation and actual native scan exhaustion behind a small page. Discovery can report more candidates without establishing their eligibility. A cohort that exceeds snapshot/dependency/result budgets refuses intact; only a separately explicit smaller attempt may proceed after fresh admission. Old continuation after committed/rolled-back/unknown cleanup cannot become deletion authority or a retained history horizon. Exact source/native query and transport evidence remain required.

Identity-page branch cases independently expect operation-before-touch membership for one originally qualified producing xid, a page crossing the branch boundary, and withheld lookahead returned first on the next page. Two 513-row branch responses cannot produce 1024 selected identities or reset aggregate work. Exact signed tuple ordering must match native domains; first pages use no fabricated minimum cursor. Operation exhaustion must be established before touch advancement. These four source statements do not qualify cross-transaction discovery or native work bounds.

Cleanup parameter ownership controls swap a discovery cursor into snapshot membership, substitute another producing xid with equal-looking keys, reorder native parameters, change an output alias/order and turn a nullable proof/result into empty bytes. Require original admission/decoder refusal; no wrong-source query can return authorized absence. Verify every query against the independent original parameter/output proposal and actual native descriptors. The proposal is not a caller-supplied authorization object or public compiler ABI.

RT05 deletion schedules remove several independently admitted rows then inject a zero-row, changed-snapshot, generation/NULL/carrier mismatch or native error at a later identity. Confirm complete original rollback of earlier deletions, dependency evidence and capacity changes; lost containment remains unresolved. Exact RETURNING membership/bytes must equal original RT04 snapshots, with no count-only success or compensation by other rows. Ordinary-role DELETE/TRUNCATE and direct helper calls remain denied; full administrative current-union verification must preserve its own live custody. The two unexecuted deletion sources prove no guard or role behavior.

Snapshot native/semantic qualification uses the independent operation/touch records behind the twelve shape controls. Preserve NULL separately from empty bytes and exact signed integer text beyond host-number precision. Reject missing descriptor/alias/field, altered byte carriers, native range overflow, impossible phase/generation combinations, empty required original carriers and unknown original kind/phase under integrity admission. Payload schema success is intentionally weaker than cleanup eligibility. Retain original raw cell evidence and complete transport/profile/cut correspondence before any deletion.

Semantic cleanup snapshot controls cover exact native endpoints/one-over, signed legacy IDs, host-number precision traps, finalized zero-effect generation 0, missing/unequal operation proofs, null/empty application result, unknown operation/owner kind, stale touch seal and empty original carriers. A touch referencing one missing/foreign/unsettled operation fails despite equal current value. Independently retain full original carrier/result correspondence and actual settlement evidence; successful generation comparison cannot replace them. Recheck before/after deletion and require whole-attempt containment on mismatch.

Packed property-definition consumer checks trace the complete runtime dependency closure and instrument public construction/metadata admission for zero SQL/connection/compiler initialization. A public reference host explicitly obtains native mapping readiness, registers through the selected owner bridge, compiles and executes while preserving original binding bytes/profile. Changing the basis between stages refuses. Browser core consumption needs no compiler/adapter/global backend registration. Candidate metadata must never be promoted to native support by successful packaging or pure schema checks.

Snapshot encoding qualification reuses independently authored canonical byte vectors with private snapshot trees, including reordered input keys, controls/Unicode, duplicate members and exact NULL/empty/hex distinctions. Preserve embedded original bytes unchanged and refuse profile substitution or lost original artifact reconstruction. Resource realizability tests take a row below the nominal 8-MiB cap whose expanded complete one-row cleanup exceeds canonical/aggregate/transport limits; writer admission must refuse before retained effects. A smaller cohort cannot repair a single-row over-limit proof. Retained legacy custody remains preserved pending explicit qualified handling.

Cleanup recovery schedules lose the RT05 response before/after result persistence and lose commit acknowledgment after the same original administrative attempt. Retain exact xid/ordinal/context/selection/result custody and preserve cleanup's own registry row outside its cohort. Lookup of a later equal selection, digest-only match, removed-source absence or reconstructed result cannot resolve the original attempt. Confirmed rollback invalidates pending effects; unavailable original evidence preserves uncertainty. A restart-durable claim requires its own selected persistent producer and crash schedule, not the in-memory host registry's shape.

Complete-feed freshness now has fifteen scoped v0.2 shape controls. Native qualification independently seeds publishable versus held complete transaction membership, side/revision/transition-only facts, unavailable original clock evidence and stale/foreign worker/source context. Compare exact source acknowledgment against separately observed ahead downstream durability; do not infer zero lag or age from missing source facts. Unavailable scope/backlog must expose no forbidden boundary/time/age. A schema-valid fabricated timestamp/profile/artifact refuses semantic/native admission. Original clock/coherent inventory/retention/authorization and finite resources remain explicit prerequisites.

Freshness native boundary cases require exact producer xid at watermark W to be held, W-1 publishable only with complete committed membership, and W+1 held only when originally proved committed/visible. Use valid independent full-xid fixtures rather than arithmetic at unsupported native endpoints. A writable supplied transaction's own pending fact cannot enter either committed population; a pending acknowledgment/generation cannot become confirmed sourceApplied. An ahead confirmed boundary under a behind observation must not yield empty backlog/coverage. Missing original member time yields clock-unavailable without age/time; scope authorization/coherence failure leaks no boundary. These are semantic/native controls, not additional shape successes.

Feed member identity tests register facts in a different order from final delivery order, repeat identical facts without refreshing write time, add a later member after early finalization, and force routing collisions between distinct complete fact keys. Verify full immutable originals, generation invalidation and deterministic final ordinals. Conflicting same-kind/key originals refuse. Rollback/private-address reuse cannot revive a stale host capture or turn a missing fact into a different member. Independently exercise keys beyond native index-entry assumptions under the selected bounded comparison/address profile; no truncation or digest equality can preserve identity. Native store selection/execution remains open.

The implementation plan now decomposes B-011a/b into F01–F08 native delivery units, from exact native authority/account/profile declarations through independent extractors, registration, canonical production, dispatcher, write-free guard, retention and installation reconciliation. STP-041 owns their planned native/state/resource/bypass corpus; STP-045 owns complete source/effect installation correspondence. A green source receipt or one family fixture cannot satisfy F08 whole-profile coverage. B-011c–g remain distinct required boundaries interleaved after producing-side F01–F06 and before the final F08 whole-profile audit; retention F07 consumes their selected protection design. No cyclic prerequisite or reduced release scope is implied.

Packed-consumer qualification must include the explicit tooling-owned native helper artifacts from the selected installation profile. Test missing/substituted/foreign-target artifacts and forbidden helper loader/build/download dependencies reachable from core or assembly. Original source/build/binary/security/resource and installed correspondence belong to the exact native profile; portable/browser import success cannot establish native helper availability, and a native package presence cannot excuse import/construction side effects.


### Reference-host checkpoint completeness admission

The implementation plan's S01–S09 sequence is an execution order, not the release coverage inventory. Before a reference run, independently admit the selected supported-profile requirements and their primary STP cases, then map each required case to its checkpoint. Preserve exact package/compiler/database/profile pins and expected fixture identities. A checkpoint may complete only when every required case assigned to it has complete matching evidence; the number of successful cases cannot establish membership. Optional profile selection must precede execution and cannot be changed afterward to exclude a failed case. Required product behavior remains required even when its implementation is unavailable.

Use CONTRACT-011's existing receipt outcomes exactly: passed, failed, skipped, blocked and not_run. Passed requires complete matching observations; failed requires complete contrary observations. A known unmet prerequisite is blocked with its original diagnostic; a never-started case is not_run. Neither skipped nor blocked can satisfy a required case. Unavailable preparation/assessment and interrupted original runs remain their existing tooling lifecycle results, not additional per-case outcome tokens. In particular, unknown active/native/cleanup work retains the original interrupted run and recovery evidence; do not manufacture a complete receipt by labeling its active cases failed or not_run. A recorded stopped receipt requires confirmed containment, original completed verdicts and accurate never-started not_run entries under CONTRACT-011. These rules do not change the existing operation failure/result vocabulary. A release assessment requires all required cases passed, complete S01–S09 membership for the selected release claim, and the independent full story/criterion inventory. Missing evidence is unverified; it cannot become a pass, an empty checkpoint or a successful zero-case run. Cleanup and containment evidence remain separately required after failed/interrupted cases, and their failure cannot overwrite the original outcome.

Plan runner acceptance controls with independently authored manifest/outcomes: remove S06 while preserving the total number of entries by duplicating S05; omit one required case while retaining a passed checkpoint summary; replace a required case identity with an unexpected passing case; mark an unavailable required adapter as skipped; change the selected profile after a failed execution; interrupt collection after submission while leaving earlier checkpoints green; and lose owned-cleanup confirmation after an otherwise matching case. Every control prevents a complete release receipt and retains the original case/status and missing or conflicting evidence. The positive control supplies complete independently matched membership and observations, including confirmed containment/cleanup where required. These are planned runner tests, not runtime qualification or a new public conformance wire.

### First integration checkpoint evidence allocation

The implementation plan's M00–M07 scenario is an integration checkpoint, separate from the S01–S09 release sequence. Admit its full selected fixture, original deployment tuple and complete expected state before M00. The table identifies primary story-test owners; it does not replace their criteria, native controls or CONTRACT-011's required manifest. Each checkpoint retains original inputs, actual procedure/observer identities and independently expected observations. Later success cannot retroactively close missing earlier evidence.

| Checkpoint | Primary test-plan owners | Required original observation |
| --- | --- | --- |
| M00 assembly | STP-027, STP-044 | Instrumented construction performs zero toolkit native calls; host-owned pool/services retain ownership; uninstalled readiness prevents graph/catalog operations. |
| M01 installation | STP-029, STP-045 | Independently complete installed object/effect/dependency inventory and committed initialization, original layout marker/archive parity; zero application instances/catalog acceptance. SQL-text equality alone cannot close this row. |
| M02 catalog acceptance | STP-001, STP-006, STP-036 | Exact fixture catalog/identity/source/report correspondence and actual commit; complete native DDL/effect comparison excludes per-type objects; zero application instances. |
| M03 initial graph | STP-007, STP-009, STP-010, STP-011, STP-015 | Complete four-object/two-edge graph, distinct typed identities/key bindings, exact numeric tokens and absent/null/empty distinctions; committed journal/source/state independently match expected effects. |
| M04 isolated refusals | STP-009, STP-011, STP-012 | Separate duplicate-key, third-edge and stale-version attempts retain the full M03 committed graph/key/value/source/journal state after confirmed containment. Allocator evidence follows the selected FR-15 grammar separately. |
| M05 caller rollback | STP-044 | Same original caller transaction sees pending B null; separate qualified observer sees committed B absence; original rollback is confirmed and complete committed state returns to M03. No toolkit commit or host transaction termination. |
| M06 committed update | STP-007, STP-015, STP-044 | Original host-confirmed commit changes only B note/presence and its single version transition; full independently expected journal sibling inventory, including any selected metadata boundary witness and manifest, matches the selected profile; property count is separate from total event count. |
| M07 direct/compiled reads | STP-020, STP-023, STP-039; executor controls STP-044 | Common qualified committed cut, original occurrence/value provenance, exact authorized values and B/C target multiplicity; full result matches independent expectations. Compiled execution retains every original owner-wide prerequisite, actual guard/result descriptor and complete private result before protected prepublication authority/pin checks. Stale/unknown binding or obligation refuses before SQL; post-query authority change refuses disclosure. |

Native producer/observer requirements follow each story test plan and the selected deployment profile. The reference writer, decoder or compiler output cannot generate its own expected state. Direct-versus-compiled agreement is supplementary: two paths sharing a faulty codec may agree while both fail the independent oracle. Preserve unordered bags and compare order only when the query explicitly selects an admitted order. Query failure, incomplete observation or unknown cleanup withholds complete-checkpoint evidence; never publish an earlier partial result as M07 success.

M07 additionally consumes STP-039's compiler integration controls. An orchestration receipt lacking the original prerequisite inventory/guard traces, relying on injected authority as production proof, or publishing rows before the final protected recheck cannot complete M07 even when direct and compiled results agree. The same original transaction and enclosing account cover guards, data and publication observations; independently retain a nonmatching owner with invalid selected numeric content to prove filtering cannot hide a required domain refusal. This supplements the existing scenario without substituting Weft's sales fixture for the selected Truss schema.

Plan orchestration controls that remove M02 evidence while leaving M03/M07 green, replace M04's three isolated attempts with one rolled-back combined group, substitute another transaction's rollback acknowledgment for M05, or accept direct/compiled agreement with an independently wrong decimal token. Each must prevent milestone completion. A positive orchestration case includes all eight checkpoints with exact original membership and independently matched observations. These controls test the integration harness; they do not themselves qualify storage, compiler execution or the full release corpus. Existing checkpoint and qualification receipt surfaces remain authoritative; no new public outcome vocabulary is introduced.

### Integration journal inventory controls

Before M03/M06, independently admit the selected profile and complete expected event membership. The current complete-profile proposal gives M06 one property delta plus one metadata witness; its two-event manifest must cover the full original inventory. Until US-015 row-count semantics and profile adoption are resolved, this candidate is unselected preparation, not a passing filtered property test. Deliberately remove the witness, exclude it from manifest count/digest, or substitute legacy partial envelopes while labeling the run complete-profile: each blocks the checkpoint claim independently of direct/compiled read agreement. M05 rollback removes all selected-profile pending events, not just property rows.


The [independently authored Account/Item state oracle](reference-account-items-expected-states.proposal.json) fixes complete logical object/edge/business-key membership and exact field presence/token expectations for M03–M06, including pending versus independently committed M05 observations. It preserves B absence, C null and D empty text. Expected values are authored from the original milestone, not generated from Truss readers/compiler outputs. Native IDs and initial versions require independent original symbol binding; full source/journal/report/authority and settlement evidence remain separate required oracles. This artifact cannot pass the whole milestone by logical graph equality alone.


## Pure numeric convenience operation qualification

For the proposed public core viewNumericAsNumber helper, compare exact rational meaning independently for integer 42/decimal 0.5 success, integer 9007199254740993 and decimal 0.1 refusal, signed-zero original preservation and subnormal/underflow/overflow boundaries. Resource cases use the existing numeric-admission-resources profile: combined token/work/peak boundaries, preflight before scaling, complete grammar before zero shortcut and repeated failed conversions within one enclosing account. A full token ceiling that exceeds remaining work must refuse before traversal rather than refresh the budget. Source validity, numeric lossiness, unsupported profile and resource refusal remain distinct.

Run the actual packed public helper in Chromium and selected server runtimes with no I/O/host-global dependency. Retain exact helper/resource/parser/build definitions and original token bytes, independently authored rational outcomes and actual work/peak observations. Type shape or Number formatting cannot establish equality. Field/native admission, shared executor accounting and complete browser-core qualification retain their separate required evidence; these planned helper cases do not replace them.


The [numeric view oracle](numeric-number-view-expected.proposal.json) now authors sixteen original wrapper/outcome cases, including representable-but-unsafe integer refusal, decimal binary loss, overflow/underflow and signed-zero/source preservation. Expected numberMeaning strings label exact intended results; they are not formatted-number equality witnesses. Native/Field admission is outside this pure helper. Resource/profile prerequisite failures remain explicit rather than passing a semantic case; remaining subnormal/finite-boundary/resource/browser scenarios are listed and still required. The oracle is not_run and must not be regenerated from the converter's output.
