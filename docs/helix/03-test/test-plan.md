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

## Baseline resource and driver acceptance — owner decision 2026-10-11

TP-001 qualifies stock psycopg 3 under ADR-003 and the PRD's practical resource profile. Required tests use public supported APIs and independent PostgreSQL observations: exact values/NULL/absence; maximum and one-over input/value/page/batch/concurrency limits; bounded retrieval and iteration; peak process memory under maximum admitted workloads; query/lock deadlines; earlier caller work surviving operation rollback; dry-run residue; stale handles and concurrent host use; cancellation/connection loss; confirmed and unknown COMMIT; safe discard/reuse; prepared/unprepared pool behavior; and actual Lakebase TLS/person-token/credential-refresh behavior for a Lakebase claim. Document tested versions, operating limits and measured peaks, not a hard process memory guarantee.

Private wire/frame/allocation instrumentation and strict backing/copy ledger tests are optional-profile qualification only. This applies to candidate predecode controls, DH-01/02/05 hook-specific portions, LR-03 physical-copy proofs and other strict transport schedules. Their not_run status cannot fail baseline release. Exactness, command/result correctness, transaction safety and authority portions remain mandatory, tested with supported driver APIs/native effects. A controlled wire peer is not required to qualify baseline functionality; optional hardening claims need their own evidence. The PRD's documented-deficiency/owner-ADR gate applies before building any custom protocol handler.

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

### Released binary runtime in CI and development

The normal setup command is `python scripts/install-local-runtime.py`. It selects
the runtime profile's public release, requires binary wheels, verifies published
checksums and rejects conflicting historical distributions. No source fallback
is allowed. `.github/workflows/python-runtime.yml` builds only Truss's pure Python
wheel and runs the focused installed smoke checks against released PostgreSQL18.6
on Linux x64/Python3.11, retaining logs and cleanup evidence even on failure.
[The first passing CI checkpoint](../04-build/evidence/design-audit/pg18-ci-released-runtime-20261011/summary.json)
records all six groups passing atb494b275 on the published Linux wheel, including
owned lifecycle, supported driver, cleanup/collision, interruption, CLI signals
and timeout. Installer controls also confirm corrupted cache refusal and a
consistent binary installation. The .0 checkpoint excluded Linux whitespace socket paths due to an observed
upstream quoting bug. Packaging version18.6.1 fixes that bug; current lifecycle
and CLI checks restore short paths with spaces and apostrophes on all platforms.
[Patch-release CI evidence](../04-build/evidence/design-audit/pg18-packaging-patch-ci-20261011/summary.json)
records all six installed groups passing against18.6.1 at347ac2be.
Broader corpus qualification is an explicit separate lane. The historical Truss
PostgreSQL recipe/build commands remain retired; native compilation belongs to
DocumentDrivenDX/pgserver.

### Local native test infrastructure — selected 2026-10-11

Routine native experiments share an owned pgserver18.6 Unix-socket cluster per
suite/worker. Allocate a fresh database and owner/probe roles per experiment;
verify native database/role/membership baseline before and after cleanup. Refuse
same-worker overlap. Failed setup/cleanup or producer death invalidates the worker;
stop the owned cluster before directory removal. Keep lifecycle, startup/shutdown
and destructive cluster-setting tests on isolated clusters. Separate workers
have distinct socket directories and disable TCP listening, so concurrent tests
can run with a pre-existing TCP5432 listener.

The [consumer checkpoint](../04-build/local-runtime-installation-migration-plan.md#current-embedded-runtime-delivery--owner-decision-2026-10-11)
selects reusable PostgreSQL18.6 wheels and focused installed consumer, supported
driver, restart, socket/collision, cleanup, interruption and timeout smoke checks.
The optional comprehensive corpus remains separate; historical17.11 results do
not establish18.6 or Lakebase acceptance. Reproduce with
`scripts/check-local-runtime-smoke.py RUNTIME_WHEEL TRUSS_WHEEL --run-id FRESH_ID`.

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


### Optional strict-profile driver predecode controls

For CONTRACT-007's frozen-driver proposal, independently supply original protocol bytes: valid UTF-8 split at every multibyte boundary; valid literal U+FFFD; malformed and truncated UTF-8 in values, names and control text; invalid field lengths/counts, missing cstring terminators and unexpected trailing packet bytes; unsupported binary descriptors; oversized declared frames and fragmented frames that never complete. Assert refusal before lossy conversion or unreserved retention/allocation, using original byte and allocation observations rather than decoded-result equality. Observe parser growth/copy overlap and socket buffers under one ledger, and prove unknown termination retains custody/reserves. These are optional strict-profile controls, not baseline release gates or passing native evidence.


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


## Formal-methods adoption: Python original ordinal/admission slice

The owning [Python technical design](../02-design/python-integration.proposal.md#formal-specification--original-ordinal-and-admission-custody)
defines PY-ORD-001/002, PY-ADM-001–005 and the unqualified PY-NATIVE-001 obligation.
Current assurance adds the [bounded abstract component analysis](../04-build/evidence/design-audit/python-custody-bounded-model-controls.json)
to author-reviewed specification and component tests. It is not an implementation
refinement or unbounded proof. Run existing component evidence with:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/python/src python3.11 -W error -m unittest discover -s packages/python/tests -p 'test_operation_*.py' -v
```

The historical two-ordinal/six-custody checkpoint below predates the shared
connection registry and registry decoder. The command now selects all current
operation component modules; decoder tests are not temporal-model correspondence.
Required ordinal/admission behaviors remain shared six ordinal scenarios,
original successful dispatch, consumed/copied/foreign/refund refusal, failure
closure, reentrant/verification-time-close refusal and deferred-port refusal.
The [source-bound checkpoint](../04-build/evidence/design-audit/python-formal-correspondence.json)
records actual command/version/source hashes and results. Tests are implementation evidence, not machine-checked formal analysis.
No local method tests the full authenticated/native issuer/account protocol.

The selected component explorer checks906 states/6224 transitions with six
detected broken variants and the deliberately false local-close/native-fence
implication. Preserve its exact bounds, exclusion of full PY-NATIVE-001, initial
harness-expectation failure and author-only review. Reproduce using a fresh
receipt basename:

```sh
python3.11 docs/helix/04-build/evidence/design-audit/python_custody_model.py NEW_ANALYSIS_RECEIPT.json
```

Before integrated readiness, the full protocol's later analysis must select its
model/configuration and broader bounds described by the design. Require reachable success,
external recovery/unknown controls and targeted broken-mechanism counterexamples;
replay supported traces. Check model/code correspondence at actual lock, callback,
transaction and native authority boundaries. Specifically inject close/cancel
between the Python close gate and native effects: local ticket consumption alone
must not be reported as fencing those effects. Preserve original outcome/recovery
when native dispatch has happened but return/cleanup fails. PY-NATIVE-001 remains
open until actual producer/arbitration/security/native integration evidence exists.
Unrelated rendering/numeric convenience slices record non-applicability rather
than run empty models. Unchecked bounds, timeout/error and stale mapped source
invalidate the corresponding assurance claim without rewriting historical receipts.

### Configured catalog original-call qualification

The implementation-plan configured producer checkpoint retains final positive e267de87 and omitted-lock negative f4854ca4 packets. Require the sixteen configured/release controls plus twelve original dispatch cases, including the actual retained configured encoder→native admission→NativeCatalogCapture route. A downgrade control must strip configured-only fields into otherwise-valid legacy grammar; crossed-context controls must recompute both metadata digests and duplicated epoch coordinates; origin/capture substitutions and changed-only configuration profile must refuse independently. Enforce the closed sixteen-string context and exact thirty-home configured emptiness list. Missing release must refuse before the nontransactional first-effect sequence changes; rollback must remove original catalog/configuration effects. Retain exact source/dependency/native pins, module boundaries and owned cleanup before claiming this administrative component. Four complete-report authority producers and all backend acceptance bindings remain separate gates; these tests do not pass B11/B12 or qualify ordinary-role security.

The final d42 reconciliation uses the tagged configured empty-scope envelope and validates its full-row native metadata as well as the compact source. Require exact shared-coordinate correspondence: a coherent two-cut compact generation plus release generation change, or each compact artifact digest substitution, must refuse against unchanged full rows. Require selected strict initial/NULL epoch correspondence even though the generic metadata validator supports a separate restore candidate. The final positive0ee77fdd packet executes45 cases (16+14+15), including incoming hostile-rendering/context-boundary controls. The pre-d42 e267/f485 evidence does not qualify these later bytes. Public installer/authenticated authority, complete report and backend acceptance remain open.

### Declared report dependency archive qualification

Require all21 original declared paths and hashes, independently query native archive row IDs and byte lengths, and compare the ordered manifest before/after actual staged effects. Test missing/duplicate/corrupt/oversized inputs before the first effect, equal-length same-writer byte mutation, equal-byte replacement under a new archive row ID, rollback and isolated host manifest substitutions (including release/resource row-ID collision). Protocol0.4 must refuse otherwise-valid configured0.3 or legacy0.2 downgrades. Retain exact digest-check and archive-lock mutants with only their intended failures. Positive1197e66c passes48 tests; the implementation plan records exact receipts and independent Astra audit. Exact capacity boundaries and full resource-cost accounting remain planned, not proven. CONTRACT-063/STP-056 B11/B12 and AC9/10 retain their complete authority/acceptance requirements.


### Selected archive self-write fence controls

CONTRACT-008's candidate expands CONTRACT-063/STP-056 B11/B12/L03 prerequisites without promoting them. Require actual original archive table definitions, valid immediate FK seed and all four native write events under an actual granted ShareLock. Independently test real/empty INSERT, real/empty UPDATE, DELETE, TRUNCATE, attempted change/restore, unselected write success, read preservation, ALWAYS trigger mode and effective-default PUBLIC execution privileges. Verify original ShareLock after AccessExclusive upgrade, and its absence after rollback crossing acquisition under unchanged xid. Test RELEASE reparenting, later rollback and replica mode independently. Disable only the guard predicate and require exactly the intended not-raised failures without incidental errors; preserve per-control savepoint rollback even when assertions fail. Original source pins, exact mutation preimage, owned cleanup and separate formal scope are required. The standalone fixture cannot establish protected configured installation, native trigger custody or complete backend acceptance.


### Configured fence admission integration controls

Require admission before the independent first catalog effect for missing/renamed/disabled/ordinary/replica-only/wrong-event/conditional/extra archive triggers; changed body, owner, definer/search-path/volatility/parallel/strict/leakproof attributes; same-name overload; nonset-to-SETOF trigger signature; and PUBLIC/nonowner/default-NULL EXECUTE grants. For default ACL, recreate the original body/recipe without REVOKE and independently assert proacl IS NULL before invoking admission. Reset the nontransactional first-effect sentinel for each isolated drift after rollback. Drain only the valid archive FK before trigger DDL so pending unrelated commit-barrier events do not obscure the oracle.

Exercise the original configured encoder/native admission/capture and two checks around real effects. Same-writer changed bytes, equal-byte replacement and change/restore attempts must hit the native fence; staged catalog state must roll back. Late source-body substitution must fail after the effect sentinel is reached, then restore original source on rollback. Preserve signature/settings/owner/ACL and694-byte length in both body-only substitutions. Remove only the body-hash predicate and require exactly those two non-refusals. Remove both configured comparison call sites and require21 isolated pre-effect drift non-refusals plus one late non-refusal, not incidental setup errors. These administrative controls qualify prerequisites for CONTRACT-063/STP-056 B11/B12/L03 and US-056-AC9/AC10; authenticated source/caller, complete inventory, held source/authority use and final disclosure remain mandatory acceptance gates.

### Epoch-state fence controls — 2026-10-11

For CONTRACT-008's epoch-state fence candidate, qualify both table locks and matching writer-before-row ordering on the current pinned PostgreSQL17.11 tuple; retain prior16.15 receipts as historical component evidence. Exercise issuer refusal before a nontransactional registry first-effect sentinel; all four native write events on both tables, including empty statements; active writer refusal without reader row wait; reader-first external issuer refusal; commit/rollback release; acquisition rollback with unchanged xid; RELEASE reparenting and later rollback preservation; replica mode; missing ordinary execution grants; and isolation refusal. Retain omitted-predicate controls that fail only intended own-write assertions. This supports original epoch-state custody prerequisites for CONTRACT-063/STP-056 B11/B12/L03 and US-056-AC9/AC10; it cannot promote complete source/authority or backend acceptance.

The ordering oracle must observe the issuer waiting on an independently held marker row before checking both ROW EXCLUSIVE modes. A separate reader attempt then refuses55P03. Erasing only the early table LOCK must reproduce zero early modes and successful reader acquisition; modes observed only after issuer completion are insufficient. Keep the entry-guard and trigger-predicate mutants distinct. With only SELECT and helper EXECUTE, an ordinary role must read the current pointer but fail SHARE acquisition42501 and fail direct epoch DML. Valid registry INSERT controls exclude generated evidence_sha256; valid registry TRUNCATE controls include the native dependency scope. An omitted selected fence may still encounter the independently retained immutable-registry TRUNCATE guard; report its diagnostic mismatch honestly.


### Closed original epoch capture family controls — 2026-10-11

Run the same original acquisition schedules for both concrete families: successful and lost local response, exact maximum profile/evidence bytes, later ordinary error, same-backend issuance, uncertain control reply and transport closure. Reconstruct exact original Q and T/D/C/Z bytes and the retained row. Read original backend/database pg_locks from a separate administrative connection: the old family has zero selected table ShareLocks, the fenced family has both. Retain RELEASE reparenting, rollback-across invalidation before host settlement, unchanged original scope objects, no retry after uncertain control and actual external successor issuance after release. The old family must retain its self-issuance counterexample; the fenced family must refuse55000 while lifecycle invalidation already occurred.

For each family, exercise capture() on altered SQL, altered comparison, copied gate, copied request, crossed session and foreign non-session reference. Require exact NativeBoundaryRefusal before any new native call/session call, original request-root preservation, no observation/acquisition and original admission closure. Pure controls separately test frozen fields, exact primitive recipe types, subclass refusal and bidirectional scope crossover. Capture all implementing Python bytes, both new SQL assets and tests before execution; reject source drift and retain owned fixture cleanup. The request identity/closed-family SMT abstraction must retain SAT omitted-check witnesses and fresh-context replay; it does not establish Python runtime or SQL refinement. These controls support CONTRACT-063/STP-056 B11/B12/L03 and US-056-AC9/AC10 prerequisites only.


### Native selected routine-DDL participation controls — 2026-10-11

Invoke the actual private `runtime_admit_operation` producer with original bounded
artifacts; compare native xid/ordinal/context and its retained registry row. With
no epoch SHARE locks, selected routine DDL must refuse55000 before writer modes,
later event-trigger effects or body changes. A later savepoint rollback must not
remove refusal. Rollback across admission must remove the row and allow DDL while
the original parent xid remains equal. A separately omitted operation predicate
must allow changed body/effects behind that actual admitted row. These controls
qualify the admitted phase only, not complete finalization, registry immutability,
all operation producers or authenticated ordinary-person admission. Retain the
conditional UNSAT exclusion law and SAT omitted-guard witness independently of
native producer/refinement claims.

For CONTRACT-008's automatic six-tag adjunct, retain exact tag order, ALWAYS mode, original invoker/no-PUBLIC execution/settings readback; before-effect refusal for all six tags under an actual own ShareLock; independent first-effect sequence unchanged on ordinary/invoker-definer/external reader refusal; pending original DDL writer modes surviving to COMMIT/ABORT; fresh successful reader/body after completion; marker-specific two-writer refusal before a later event-trigger effect; and original savepoint RELEASE/later-rollback lock preservation. Older Repeatable Read/Serializable readers refuse before acquisition. Replica mode must still execute the ALWAYS fence.

Independently erase only actual own-ShareLock selection, early table modes and marker row exclusion in separate isolated schedules. Require same-backend body change while actual ShareLocks remain, pending foreign commit changing actual execution/census while reader ShareLocks remain, and simultaneous distinct selected DDL effects under both compatible writer modes, respectively. Use exact replacement preimages/counts, original native errors and bounded calls. Include privileged hook disable and relevant shared-role BYPASSRLS change as successful excluded-authority controls. Both must preserve epoch identity while falsifying any complete source/authority-cut claim. Retain complete compressed census bytes plus digest/octet readback where collected; these are administrative materialized observations, not original NativeCall/host disclosure custody.

Require successful selected DDL with changed source body/census and unchanged epoch. Source snapshot equality cannot be inferred from the epoch. Saved formal one-step laws require continuously alive cuts, complete selected-tag participation, actual mode/marker compatibility and own entry guard; retain omitted-premise SAT controls and separate native scope. These prerequisites support CONTRACT-063/STP-056 B09/B11/B12/L03 and US-056-AC7/AC9/AC10/US-057-AC2 without promoting acceptance. Full source-epoch semantics, writer coverage, installed authority, ordinary executor and final disclosure remain required.


### Supported psycopg epoch-cut composition — 2026-10-11

For CONTRACT-008 and CONTRACT-063/STP-056 B11/B12/L03 prerequisites, acquire the
actual fresh fenced helper through the original psycopg operation scope. Require
exact twelve-field correspondence before callback, two actual native SHARE modes
during callback, and independent selected routine writer refusal. Require own DDL
refusal and callback error to roll back the cut while retaining earlier host work
and timeout settings. Wrong expected profile and READ ONLY must not invoke the
callback. Rollback across the outer host savepoint must release the earlier cut
under the same parent xid; a later invocation must reacquire rather than reuse it.
Exercise custom host string dumper/loader isolation and mutation of the comparison
carrier after primitive snapshot. Run all26 supported adoption controls alongside
these eight native composition controls. Freeze sources/preimages before execution,
refuse drift, retain outcomes and independent owned stop/status/socket checks.
These are administrative components, not a new132-case acceptance binding or a
whole-source/authority/final-disclosure refinement proof.


### Flat/graph fact-cut native schedules — 2026-10-11

For CONTRACT-063/STP-056 B10/B11/B12/L03 and US-056 AC2/AC8/AC9/AC10 plus US-057
AC2 prerequisites, run actual flat Assignment rows and actual typed Truss edge,
object, relationship and endpoint rows under unchanged native constraints. Require
identical selected project identities inside their held cuts; exercise independent
bounded DML conflicts and all four own DML events on both stores. Pending original
fact writer refuses before callback; retry only as a new explicit operation after
writer completion. Changed relation identity, inheritance, duplicate binding and
missing/disabled ALWAYS guard refuse before callback. Native replica mode still
fences writes. Temp catalog shadows must not substitute readback or epoch identity.
After original reader rollback, commit flat deactivation and native edge deletion;
a fresh same-epoch lookup must return no memberships. Restore fixture originals.

Keep an explicit omitted installed-guard control: disable its trigger outside the
cut, require normal component refusal, then deliberately omit qualification while
retaining native SHARE to demonstrate same-writer changed facts. Do not treat that
countervariant as admitted behavior. Run10 fact controls, eight epoch controls and
26 supported adoption regressions, frozen sources and boundary check; retain
independent named cleanup for epoch/fact fixtures. Component evidence does not
prove hidden-fact nondisclosure, ordinary Staff authentication, complete provider
coverage, accepted graph catalog, source/role closure or protected final handback.


### Graph projection native/formal controls — 2026-10-11

Under actual epoch/edge cuts and retained original native scope, require INSERT,
UPDATE and DELETE of unrelated typed business edges to succeed while a required
membership edge stays equal. Selected association INSERT/UPDATE/DELETE and any
TRUNCATE refuse. Reclassification both into and out of a selected type refuses
using actual NEW and OLD values. Missing scope refuses even unrelated writes.
Observe original native context/evidence; reject immutable scope UPDATE/DELETE/
TRUNCATE, changed evidence, malformed/duplicate/unknown type lists, union overflow
and foreign native xid insertion without partial rows. Monotonic extension retains
and protects earlier types. Rollback across registration under the same parent xid
removes scope/cut; fresh registration is explicit. Replica mode preserves guards.
An omitted required association must remain an unsafe success countercontrol.

The conditional SMT model uses unbounded symbolic edge IDs, opaque typed rows and
required/native scope sets. Require complete-superset row preservation, missing
scope/TRUNCATE refusal and monotonic coverage laws, with SAT business-write,
omitted OLD/NEW guard, missing required membership, omitted TRUNCATE and scope
shrink controls. Finite-history induction assumes native faithful row effects,
continuous cuts and complete required scope at each step; newly added scopes need
fresh baselines. These are CONTRACT-063/STP-056 B09/B11/B12/L03 and US-056 AC2/AC7/
AC9/AC10 plus US-057 AC2 prerequisites, not authorization/finalization acceptance.


### Original graph registration wrapper controls — 2026-10-11

Require actual registered union/context/evidence readback before unrelated business
callback; selected writes still refuse. Custom host integer, array and byte dumpers
must not substitute the original recipe. A missing association definition must
refuse with no callback or scope rows. Replace only the native registration INSERT
association with a different valid association while retaining its plausible count:
require original-ID readback refusal, no callback and native rollback of new rows.
Mutate the comparison carrier after primitive snapshot; native IDs/evidence must
remain the original selected recipe. Keep native readback separate from required
semantic dependency completeness and installed source authority. These support
CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10 prerequisites, without promotion.


### Original semantic dependency coverage diagnostics — 2026-10-11

The fixture producer invokes UMF's original `securityPolicyDependencies` over its
Staff → Project → Resource conformance policy. Retain exact original policy and
resolution bytes and their direct hashes; do not recreate semantic traversal in
Truss. Its dependency inventory contains eight fields and two associations.
Association-only declarations leave all eight fields missing. Preserve owner
enumeration and exact document/module/element references, including opaque Unicode
spelling. Reject absent dependency lists, duplicate keys/references, foreign or
repeated bindings and changed artifact bytes. Expected hashes compare bytes; they
do not authenticate an issuer. Even complete declarations remain diagnostics with
`admitted=False`: producer names are unqualified and no physical mapping is inferred.

Retained packet `evidence/security-fact-coverage/6ad3e5ea-7efa-4b4a-a039-717339bbebde`
passes six consumer controls, three original UMF dependency tests and module
boundaries, with 369 current/archived source pins and exact original input hashes.
The earlier 6f525c23 packet qualifies its earlier source tuple only. This supports
CONTRACT-063/STP-056 B11/B12/L03, US-056 AC9/AC10 and US-057 AC1/AC2 prerequisites;
no backend acceptance binding or native support claim is promoted. Semantic closure
stays in UMF; physical provider qualification and source cuts stay with backend
integration. Authenticated owner handoff, actual field/provider bindings and cuts,
installed role/body closure, protected mutation dispatch and final disclosure remain
required. No new formal refinement or Astra review is claimed. The goal remains
active at 26/132 bindings with 106 missing.


### Semantic field/provider cut obligations — 2026-10-11

Formal packet `evidence/security-field-cuts-formal/456a26c5-c5a3-4f80-b944-39ac77d34fb7`
retains eight SMT2 queries and fresh-context replay (two UNSAT, six SAT), six source
preimages and the original ten UMF dependency identities. The model admits
unbounded facts/providers and opaque complete provider states. Complete required
membership, actual/declared provider correspondence, continuous effective cuts and
stable deterministic decoding imply one-step required-fact preservation. Induction
requires these premises at every step. Opaque state equality abstracts complete
rows/presence/nulls/values; this does not prove PostgreSQL or semantic decoding
refinement, native source authenticity or policy authorization.

Countermodels separately demonstrate omitted `active` membership, wrong provider
mapping, missing provider cut, released/bypassed cuts and changed decoding despite
all data cuts; unrelated uncut provider state may change under full premises.
Physical admission must therefore qualify original mappings AND their decoding
source/config/role dependencies, not just compare column names or lock declared
tables. Expected artifact hashes do not qualify issuer or physical mapping.

For backend tests tied to CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10,
require each required field/association to resolve through an original qualified
provider recipe; substitute a wrong but valid provider and demand refusal before
callback; omit a required field or cut and demand refusal; change the installed
decoder/source while preserving data and demand refusal. These are required native
controls, not passed by symbolic countermodels. Flat columns and graph payloads
must each prove decoding correspondence, including absence/null/type semantics.
No public API, native admission or acceptance binding is promoted; checkpoint
remains 26/132 with 106 missing and the objective stays active.


### Original native field descriptor correspondence — 2026-10-11

Private fact-table recipes now carry bounded exact column comparisons. Snapshot
name, native attribute number, type OID/modifier, nullability, collation OID and
stored-generation/identity markers before the original epoch scope. Reject duplicate
names/numbers and malformed comparisons before native work. Under actual table
SHARE and installed ALWAYS guard correspondence, read explicit pg_catalog attributes
as nine text descriptors; require exact original descriptor and non-dropped column
before callback. Retain the relation-only read subset separately: an empty column
recipe does not establish field dependency coverage.

Final native packet `evidence/python-psycopg-epoch-cut/613a92b8-17f9-4db8-8475-478496590c55`
passes 68 tests (17 fact,16 graph/gateway,nine epoch,26 adoption), with current and
archived source correspondence, native payload pins, module boundaries and three
independent named fixture stop0/status3/socket-absent cleanups. Seven added controls
cover original descriptor success, wrong valid type, actual native type/nullability
changes, drop/recreate under the same name, duplicate recipe before xid assignment
and hostile temporary pg_attribute shadow. Refusal preserves pre-existing lock
baselines and prevents callback. Initial7889a5b7 passes its earlier66-test tuple;
845be9f0 retains a failed assertion that incorrectly expected the preceding table
rewrite's lock to disappear. The corrected baseline assertion passes in the final
packet; historical evidence is unchanged.

Field-cut model replay `evidence/security-field-cuts-formal/0a706a61-4f48-46c6-905e-32b82f9e03ac`
retains the new module source and the same eight conditional queries, not a native
refinement proof. Descriptor equality does not authenticate mappings or establish
decoder/type/collation/generated-expression/role/config closure. The original
semantic dependency-to-provider handoff and complete cuts remain required for flat
and graph fields. This advances CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10
prerequisites only; no public API, grants or backend acceptance binding changes.
The full goal remains active at 26/132 with106 missing.


### Complete dependency/provider cut controls — 2026-10-11

For CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10 prerequisites, compose
actual original UMF fixture dependencies with explicit five-table providers.
Require ten-dependency coverage, five actual table SHARE locks and fixture resource
membership `r1`; omission of `active` or all field bindings must refuse with no
callback and no assigned native xid. Substitute the field descriptor and require
native refusal before callback. Under complete cuts, attempt same-writer active
revocation and require SQLSTATE55000 with unchanged facts after rollback. These
five controls pass in packet79a2bb83 (73 total methods); this is not complete
semantic mapping provenance, authorization or backend acceptance promotion.


### Original logical/semantic/native fixture correspondence controls — 2026-10-11

Under the ten-reference/five-table cut, read explicit native text facts and execute
the original UMF owner evaluator. Verify permit with salary withheld for active
same-project membership and deny for inactive, other-staff, sibling-project,
missing-ownership and missing-assignment variants. Tie these fixture prerequisites
to UMF US-079 AC1/AC4/AC5/AC7 and backend US-056 AC9/AC10; they do not qualify the
ordinary caller, decoder/source closure, complete mutation executor or release.

Retain a separate negative control: bind active to a valid alternate boolean column
and decode it while the original column is false. The current private prototype
permits these substituted facts. Required future admission must instead reject the
substituted original mapping/decoder before policy evaluation or any publication.
The counterexample is evidence of incomplete enforcement, not a passed acceptance
case or a requirement to keep this behavior in an admitted implementation.


### Epoch-bound original provider recipe controls — 2026-10-11

Four new native controls require the original stored profile to derive complete
provider cuts, reject a well-typed decoy-active replacement profile before callback,
refuse an original stored profile missing active, and refuse a wrong requirement
digest. Fixture issuance occurs in the owned transaction and rolls back with its
scope; no installation/caller authority is inferred. These advance
CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10 prerequisites only. Required
future admission controls must also reject unqualified original issuer/semantic
mapping and independently changed callback/decoder source; these are not proved by
exact native profile-byte correspondence.


### Fixed raw-cell capture controls — 2026-10-11

Require fixed epoch-bound reads to select original active=false despite a real
true decoy column, omit unneeded salary, record a present Ownership binding with
zero rows explicitly, and refuse complete results above row/payload limits.
Verify exact native int8 text9007199254740993, SQL NULL without empty-string
coercion, and host custom text-loader isolation. Changed physical Staff mappings
in integer/NULL controls test native raw encoding only; they are not qualified
against the original ontology's required string identity. These seven controls
advance CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10 prerequisites, not
original trusted fact construction, protected evaluation or final publication.


### Original identity reconstruction controls — 2026-10-11

For CONTRACT-063/STP-056 B11/B12/L03, US-056 AC9/AC10 and UMF US-079 AC3/AC6
prerequisites, consume original ten-field/two-association identity transport.
Reject omitted instance Keys before native xid assignment; reconstruct original
a1/o1 Keys and permit with salary withheld; deny inactive assignment and missing
owner; reverse provider order without changing identity; refuse duplicate instance
Keys as indeterminate and incompatible native/semantic literal domains before
policy output. Seven native controls pass in packetb6affb88,98 total component
methods. These do not qualify issuer/mapping provenance, protected reconstruction
lifetime, ordinary caller authentication, complete graph decoding or final release.


### Original native result cardinality controls — 2026-10-11

Insert10000 additional fixture rows and independently confirm10001 source rows.
Observe original stock psycopg PGresult.ntuples after the actual capture submission:
require101 before `fetchmany`, and whole capture refusal. Deliberately remove only
the submitted SQL limit; retain ordinary post-fetch refusal and observe10001 native
rows. This counter proves the missing server bound without manufacturing a response.
The two controls advance CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10
resource-bound prerequisites only; source/role/RLS completeness, strict byte
accounting and final publication still require independent qualification.


### Original native fact-source visibility controls — 2026-10-11

Three PostgreSQL16.15 controls require whole-cut refusal without callback: enabled
RLS even when the administrative session sees all rows; FORCE RLS while ENABLE
RLS is false; and an actual nonowner role whose native policy hides the fixture row.
The nonowner control independently observes count zero, successful epoch acquisition
and the original native metadata result (`true`, `false` RLS flags); it requires a
Python metadata refusal with no SQL error. Transactional role/grant/policy fixtures
are rolled back. Packet027f2354 passes103 component methods. These advance
CONTRACT-063/STP-056 B11/B12/L03, US-056 AC9/AC10 and US-079 AC6 completeness
prerequisites; they do not qualify an RLS-aware fact provider, complete role/config
cuts, ordinary authenticated authority or protected disclosure.


### Native visibility lifetime and table-DDL participation — 2026-10-11

Four additional controls in packet30ba8a7b require: competing ENABLE/FORCE RLS
DDL times out under the retained fact SHARE lock; after reader release a committed
ENABLE is observed and the fresh cut refuses; actual same-session ALTER succeeds
when the optional writer barrier is omitted (counterexample); installing the
selected barrier refuses same-session ALTER before its effect with55000; and a
pending participating ALTER excludes a fresh epoch reader with55P03 until abort,
after which a fresh cut succeeds. Two behaviors share the first control.
All107 component methods and three independent native cleanups pass. Trace:
CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10 lifecycle prerequisites.
These do not establish whole source/role/config closure or public authority.


### Joint installed DDL/fact readback controls — 2026-10-11

Seven native controls qualify selected installed metadata correspondence: exact
routine/table barrier pair passes and composes with retained fact SHARE; missing
table barrier refuses; disabled table barrier refuses; incomplete native table tag
set refuses; wrong original owner/function/body comparisons refuse; disabled
routine barrier refuses even when table barrier is ALWAYS; joint fact acquisition
with a missing barrier refuses before fact locks or callback. Native mismatches
produce metadata refusal rather than an unrelated SQL permission failure.
Packetf764ff62 passes114 component methods and three independent cleanup checks.
Trace CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10 correspondence
prerequisites. Administrative fixtures do not establish ordinary caller authority,
installed administration exclusions, whole source lifetime or final disclosure.


### Original role exclusion and native event-trigger privilege — 2026-10-11

Four native methods require: a real nonowner session passes selected original
role exclusion and PostgreSQL refuses its ALTER EVENT TRIGGER with42501; the
original superuser session refuses before callback; native membership in the
barrier owner refuses; original CREATEROLE and BYPASSRLS fixtures refuse. Privilege
failure is contained by a savepoint and the barrier remains ALWAYS. Each owned
role/grant fixture is removed after closing the actor connection.
Final5db462c6 passes118 methods; original source pins and three cleanup receipts
are retained. Trace CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10
prerequisites only. Formal50354147 separately retains three UNSAT properties and
two SAT counterexamples for abstract role snapshots; no native membership
algorithm, SQL/Python refinement, role lifetime or full authority proof.


### Native reachable-definer bypass and selected refusal — 2026-10-11

Three controls require: the original invoker-only actor fixture passes; an actual
nonowner with EXECUTE on an owned SECURITY DEFINER routine can disable the native
table barrier through the weaker role-only snapshot, while the selected stronger
profile refuses without callback; removing direct and PUBLIC EXECUTE from another
definer independently reports native false reachability and permits the stronger
snapshot. Actor grants explicitly exclude the two exact layout administrative
high-water definers. The bypass control observes its attack EXECUTE=true and both
high-water EXECUTE=false, so refusal is attributed to the intended native path.
Packetc5ef24cc passes121 methods; three native cleanups retained. Trace
CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC5/AC9/AC10 prerequisites.
Formale1dfc639 supplies three conditional UNSAT/two SAT results; no native
EXECUTE implementation, SET ROLE closure, shared ACL lifetime or final-release
refinement proof.


### Native SET ROLE membership semantics — 2026-10-11

Five controls require: original invoker actor passes; NOINHERIT but SET-enabled
CREATEROLE membership passes the weaker snapshot and refuses stronger admission,
while actual SET ROLE observes its privileged attribute; a definer unavailable to
the original role becomes callable after native SET ROLE and stronger admission
refuses; a transitive SET-enabled/noninherited chain refuses and actually creates
an owned temporary role that transaction rollback removes; MEMBER=true with
INHERIT=false/SET=false passes the selected stronger snapshot and PostgreSQL
independently denies SET ROLE with42501 under a contained savepoint.
Final7f63dbb2 passes126 methods and three independent native cleanups. Trace
CONTRACT-063/STP-056 B11/B12/L03, US-056 AC5/AC9/AC10 prerequisites. Formal
d4af259a separately models unbounded abstract SET/inheritance reachability: two
UNSAT properties/three SAT counterexamples. It does not prove PostgreSQL's
membership traversal, complete privileged capability inventory or role lifetime.


### Shared-role lifetime counterexample and participating writers — 2026-10-11

Four native controls require: an excluded administrator's uncoordinated ALTER
ROLE commits CREATEROLE during the strongest retained snapshot and original actor
observes true (counterexample); explicit participant refuses55P03 under a reader,
then changes the role only after reader rollback and its writer rollback restores
false; a pending participant changes its own role view but excludes fresh actor
admission55P03 before callback, then abort permits a fresh read; same-backend
retained reader attempting participant acquisition refuses55000 and operation
rollback removes the acquired fact cut. Original native statements and outcomes
are retained in final0d2d8de8,130 total methods, three fixture cleanups.
Trace CONTRACT-063/STP-056 L03/B11/B12, US-056 AC9/AC10 lifecycle prerequisites.
Formal4ab1bad4 models external exclusion and explicit participant effect intervals
with three UNSAT/two SAT results; it does not prove all administrators participate,
cluster-wide role safety, helper installation custody or final disclosure.


### Native atomic authority-change generation controls — 2026-10-11

Four controls require: committed role configuration and authority-change successor
produce exact predecessor/reason/incarnation, old generation refuses55000 without
callback and new exact comparison passes; abort restores role inheritance/current
pointer and removes successor registry row; mismatched target incarnation refuses
and rollback preserves original state; missing and stale predecessor cases refuse
without committed role/pointer/registry effects. Restore cleanup issues a distinct
original restore epoch after the committed fixture, preserving reason meaning.
Final2472b218 passes134 methods and three independent native cleanups. The UMF
owner adjunct round-trips saved-document export exactly. Trace
CONTRACT-063/STP-056 L03/B11/B12 and US-056 AC9/AC10 lifecycle prerequisites.
Formal42fb89e5 retains three UNSAT/two SAT results under atomic visibility and
distinct successor premises; no native issuer, complete role/ACL installation,
cluster-wide coordination, commit-uncertainty or final-release refinement proof.


### Installed authority writer/issuer correspondence — 2026-10-11

Private source verification now composes original epoch/DDL barrier readback with
exact installed shared-authority writer and authority issuer OIDs, owners, names,
plpgsql language, ordinary function kind, argument/return shapes, scalar return,
non-STRICT/invoker/volatile flags, exact search_path/body and absent PUBLIC EXECUTE
before callback. Comparisons are bounded original fixture metadata, not credentials.
Four native controls pass: exact installed source pair; actual PUBLIC EXECUTE drift
refuses; SECURITY DEFINER drift refuses; STRICT drift demonstrably returns NULL
without null-predecessor validation, while the stronger source check refuses.

Final `evidence/python-psycopg-epoch-cut/4a75f4b6-57c0-472a-adf8-f7ddf050f746`
passes138 methods (87 fact/dependency/identity/visibility/DDL/role/issuer,16 graph,
nine epoch,26 adoption), module boundaries,138 current/archived Truss pins,363
original UMF sources,1614 native payload pins and three stop0/status3/socket-absent
cleanups. Earlier16944e98 passes137 methods under its earlier source tuple.
Trace CONTRACT-063/STP-056 L03/B11/B12 and US-056 AC9/AC10 source-correspondence
prerequisites only. No new formal refinement or backend acceptance binding.
Complete language-handler/dependency and all-role ACL/lifetime closure, original
issuer credentials, qualified profile/evidence production, ordinary caller/mapping
and protected final release remain open. Last full checkpoint26/132,106 missing;
goal active. Next compose qualified lifecycle producer and original profile sources
with this source verification; installed comparison alone is not authority.


### Original policy/resolution source-bound profile — 2026-10-11

Private `truss-flat-fact-provider-fixture/0.2` retains policyUtf8/resolutionUtf8
strings alongside the original requirement digest and provider declarations.
Fixed capture requires a bounded original source bundle, snapshots its immutable
bytes before validation, checks owner-artifact source-digest correspondence and
exact native-profile inline UTF8 byte correspondence before host invocation.
Original native epoch comparison still requires the same complete installed profile
bytes; replacing all caller-side source/requirement/profile copies cannot match it.
Semantic interpretation remains UMF-owned. Legacy0.1 remains its separately scoped
subset and is not silently upgraded to exact inline-source correspondence.

Five native methods prove original identity-cell capture, missing source-bundle
refusal before xid assignment, policy/resolution byte-change refusals before xid,
whole caller-copy replacement refused by actual retained native generation, and
private snapshot stability despite later caller-carrier mutation. Source-artifact
validation lives in the original artifact module, not native provider code.
Final `evidence/python-psycopg-epoch-cut/d0767fa6-5104-4968-b8a2-21a352b3ba99`
passes143 methods (92 fact/dependency/identity/visibility/DDL/role/source,16 graph,
nine epoch,26 adoption), module boundaries,138 current/archived Truss pins,363
original UMF sources,1614 native payload pins and three independent
stop0/status3/socket-absent cleanups. Initial5d33494a passed142 native methods but
correctly failed its module boundary for a misplaced hashing import; it remains
nonqualifying evidence.

Formal `evidence/security-source-profile-formal/b94c4652-0014-4ee8-913a-41d0fb5f2a5f`
passes five fresh-context queries (three UNSAT/two SAT) with four exact source
preimages. Under faithful original/selected/native byte correspondence, source
substitution is excluded. Abstract finite-width digest equality alone and
self-consistent replaced manifests without retained native comparison have
countermodels; no hash injectivity assumed. Earlier123e8acb retains its simpler
self-agreement counter and original source tuple. No UTF8/JSON/Python/PostgreSQL,
epoch projection or SHA256 implementation refinement theorem.

Trace CONTRACT-063/STP-056 B11/B12/L03 and US-056 AC9/AC10 provenance prerequisites.
Source bytes/digests remain comparison premises, not authenticated issuer identity
or physical mapping meaning. Qualified producer/caller authority, original mapping
and decoder construction, complete source/role/ACL lifetime and protected final
release remain open. No backend acceptance binding or public support flag promoted;
last full checkpoint26/132 with106 missing. Goal active. Next bind original semantic
and physical profile construction to qualified issuer custody and protected release.


### Owned within-host capture, semantic evaluation and decision projection — 2026-10-11

An owned flat-table read spike now composes source-bound0.2 profile validation,
native dependency/fact cuts, shared fixed raw-cell capture and the original UMF
identity decoder/evaluator inside one host operation/savepoint. Semantic ownership
stays in UMF; Python does not interpret policy or Keys. The tool emits only the
original determinate decision/dispositions, excluding raw cells/private identities
and subprocess diagnostics. An indeterminate or malformed evaluation refuses.
The original evaluator's trusted=true, issuer/mapping and subject assumptions are
explicit administrative fixture premises, not ordinary-user authority.

Four native methods prove active assignment permits with salary withheld, inactive
assignment denies without raw output, duplicate identity/indeterminate evaluation
rolls back the operation while preserving earlier caller work, and original UMF
evaluation runs with all seven required native fact/epoch SHARE locks. Independent
competing fact UPDATE and explicit shared-authority writer acquisition refuse
during that actual evaluator invocation. Private fixed capture is shared between
the existing raw-cell profile and this owned tool; no public user SQL/decoder
callback was added to fixed capture.

Final `evidence/python-psycopg-epoch-cut/01992ea3-7088-472c-9ca1-fb66a52f73af`
passes147 methods (96 fact/dependency/identity/visibility/DDL/role/semantic,16 graph,
nine epoch,26 adoption), module boundaries,139 current/archived Truss pins,363
original UMF sources,1614 native payload pins and three independent
stop0/status3/socket-absent cleanups. Initial49f139f4 retains17 failed capture
regressions from a missing SQL import during helper extraction; it is not a pass.

Trace CONTRACT-063/STP-056 B01/B07/B10/L03/B11/B12 and US-056 AC1/AC6/AC8/AC9/AC10
composition prerequisites only. Native lock observation and owned source checks
do not prove executed bundle/dependency provenance or full semantic/SQL refinement.
No new formal theorem or backend acceptance binding. Qualified ordinary caller,
issuer/mapping/decoder and packaged evaluator custody, complete source/role/ACL
lifetime, graph decoding and protected final release remain required. Last full
checkpoint26/132 with106 missing; goal active. Next qualify original operation
context and mapping/producer custody before turning this pipeline into ordinary
protected disclosure.


### Requalified against concurrently advanced main — 2026-10-11

Preserved concurrent public assembly/resource simplification and PostgreSQL18.6
main history through a merge. The runner retains the added147-case security scope
and current runtime metadata; exact runtime profile JSON and shared-fixture source
are now retained inputs. Final
`evidence/python-psycopg-epoch-cut/ab9d3789-a230-46c2-be8e-c4c2a9f475cd` passes147
methods on pgserver-pg18 18.6.0/PostgreSQL18.6 with stock psycopg3.3.6 binary/libpq
18.6, module boundaries and three independent stop0/status3/socket-absent cleanups.
Earlier01992ea3 remains its separate PostgreSQL16.15/source tuple, not current-main
qualification. Initial5a38c4e4 stopped during input discovery due to a wrong fixture
source path; no native fixture launched and no qualification claimed.
The owned within-host evaluator remains an administrative flat-table spike;
ordinary caller, full original issuer/mapping/package custody, complete role/ACL
lifetime, graph decoder and protected final release remain open. No new backend
acceptance binding; last full checkpoint26/132,106 missing. Goal active.


### Native caller-bound subject selection — 2026-10-11

Private source-bound provider profile0.3 adds exact session/effective role OIDs
and original typed Core subject-key values. Native role correspondence is observed
inside the original host/fact cut before raw capture in both fixed capture and
the owned semantic tool. UMF's original key encoder validates/normalizes the
selected key; the evaluator receives exactly one matching subject, not all Staff
rows. Missing/ambiguous subject or role mismatch refuses without semantic output.
Legacy0.1/0.2 remain explicitly scoped subsets, not authenticated caller profiles.

Five native methods exercise real nonowner session with multiple Staff records:
assigneds1 permits with original withholding, unassigneds2 denies, mismatched
native role refuses, missing subject refuses, and fixed raw capture cannot skip
caller correspondence. Fixture-issued generations are restored after actor
connection/role cleanup. Initial499b30da retains generation-contamination failures;
c4df45ef retains two positive failures from plain strings instead of original
Core typed key literals. Neither is qualification evidence.
Final `evidence/python-psycopg-epoch-cut/d5a5b6ef-39f7-4ef8-9181-cc3f2f9e8982`
passes152 methods on PostgreSQL18.6 (101 fact/dependency/role/caller,16 graph,nine
epoch,26 adoption), module boundaries,142 current/archived Truss pins,363 original
UMF sources,1705 native payload pins and three independent
stop0/status3/socket-absent cleanups.

Formal `evidence/security-caller-binding-formal/41315cae-22d0-4128-a0dc-45542dd20b46`
passes five fresh-context queries (three UNSAT/two SAT), retaining four source
preimages and SMT/model receipts. Under faithful native identity capture and
retained canonical subject selection, session/effective mismatches and subject
substitution refuse. Caller claims without capture and unauthorized issuer
semantic mappings have countermodels. No database authentication/Core key
encoding/JSON/Python/PostgreSQL refinement or full authority theorem.

Trace CONTRACT-063/STP-056 B01/B05/B10/B11/B12 and US-056 AC1/AC5/AC8/AC9/AC10
prerequisites only. Actor fixtures retain broad native grants and administrator-
issued subject mapping/trusted=true premises. Direct private-fact protection,
issuer/mapping authority, full reachable-role/routine/ACL/lifetime closure, graph
decoding and ordinary protected final release remain open. No backend acceptance
binding; last full checkpoint26/132,106 missing. Goal active. Next qualify original
subject-mapping issuer custody and remove ordinary direct private-fact bypasses
before exposing protected reads.


### Privilege-separated owned read service boundary — 2026-10-11

Private profile0.4 retains separate original caller and executor session/effective
role OIDs. Caller subject selection remains original typed Core keys. A trusted
owned application holds both host references: the ordinary caller host operation
captures actual native caller identity; its scope encloses a separate executor
host operation holding epoch/fact cuts and original UMF evaluation. Executor
identity and observed database OID must correspond, alongside configured endpoint
parameters. These comparisons are not independent server authentication. Neither
existing invoker elevation guards nor fixed raw-capture caller checks are removed;
raw capture cannot consume0.4 without the original delegated caller scope.

Four native methods use a catalog-only caller with schema USAGE and no private
table/internal function grants. Actual direct SELECT, COUNT and writer helper
EXECUTE refuse42501 under caller savepoint containment, while original delegated
evaluation permits assigneds1 with withholding and denies unassigneds2. Wrong
executor identity refuses; raw-capture shortcut refuses before execution. Only
original determinate decisions/dispositions leave the trusted service spike.
Final `evidence/python-psycopg-epoch-cut/da76c214-655b-4a04-aeca-24916d4307ce`
passes156 methods on PostgreSQL18.6 (105 fact/dependency/role/delegation,16 graph,
nine epoch,26 adoption), module boundaries,142 current/archived Truss pins,363
original UMF sources,1705 native payload pins and three independent
stop0/status3/socket-absent cleanups. Earlierb069e2cd passes155 methods under its
original source tuple, without the final database/raw-shortcut controls.

Formal `evidence/security-delegated-read-formal/95a73d81-b266-4cc0-8aa0-a5ff35234eee`
passes five fresh-context queries (three UNSAT/two SAT), retaining four exact
source preimages and SMT/model receipts. Abstract original caller/executor
verification plus live release guard exclude missing custody and retirement;
trusted delegation can evaluate without caller private-table privilege. Omitting
release guard admits publication after retirement. No native privilege/host lease/
SQL/JSON/UMF/connection authentication refinement theorem.

Trace CONTRACT-063/STP-056 B01/B04/B10/B11/B12/L03 and US-056 AC1/AC5/AC8/AC9/AC10
prerequisites. This is an owned service architecture spike, not a database grant
of executor authority or a public request API. Trusted application credential/
target custody, original issuer/mapping/package provenance, all-role/ACL/source
lifetime, graph decoding and protected final release remain open. No backend
acceptance binding; last full checkpoint26/132,106 missing. Goal active. Next
qualify trusted service caller/target/credential custody and complete reachable
privilege inventory before admitting ordinary protected disclosure.


### Original caller/executor pair reservation through publication — 2026-10-11

Private delegated orchestration now reserves both original toolkit connection
leases before caller capture and retains them through caller operation completion.
Acquire in deterministic custody order, nonblocking; partial acquisition releases
only newly acquired locks. An original thread-bound reservation permits each
host's normal scoped operation without releasing its outer reserved lease.
Same-host nested operations remain refused while pending; other threads cannot
reuse either host. Reservation retirement releases both leases and quarantines
unresolved pending custody. No driver-private API, reusable capability or new
public authority flag. Raw aliases remain forbidden during toolkit operations.

Two native controls prove executor reuse from another thread refuses after actual
evaluator return but before original caller publication, reservations disappear
after successful return, and failed acquisition preserves the independently held
executor lease while releasing the caller lease. Final
`evidence/python-psycopg-epoch-cut/836ef23f-c205-4309-af76-768faf8de05b` passes158
methods on PostgreSQL18.6 (107 fact/dependency/role/delegation,16 graph,nine epoch,
26 adoption), module boundaries,142 current/archived Truss sources,363 original
UMF sources,1705 native payload pins and three independent
stop0/status3/socket-absent cleanups.

Trace CONTRACT-063/STP-056 L03/L11/B11/B12 and US-056 AC9/AC10 custody prerequisites.
This verifies toolkit lease exclusion, not native raw-alias interception, trusted
service credential/target authentication or complete final-release authority.
Original issuer/mapping/package/source/role/ACL lifetime, graph decoder and public
protected disclosure remain open. No new formal native refinement theorem or
backend acceptance binding; last full checkpoint26/132,106 missing. Goal active.
Next qualify native release guard ownership and original service target/caller
custody alongside this toolkit reservation.

### Native delegated release guard observation — 2026-10-11

The private delegated read now observes existing executor ShareLocks on every
original fact relation and both epoch tables before caller completion. It does
not reacquire lost guards. Two native controls refuse release after executor
transaction retirement and after rollback to an earlier savepoint loses guards
while retaining the same native transaction ID. These controlled raw-alias
violations remain outside the supported host contract; observation does not
prove uninterrupted guard lifetime or exclude loss/reacquisition ABA.

Evidence `evidence/python-psycopg-epoch-cut/d0f2095f-5fd8-4227-bc91-3aee055d07fd`
passes all160 component methods on PostgreSQL18.6/psycopg3.3.6 binary, module
boundaries,142 source hashes,363 original UMF sources and1705 native payload
pins, with three stop0/status3/socket-absent cleanups. Trace shared CONTRACT-063 /
STP-056 L03/L11/B11/B12 and US-056 AC9/AC10 custody prerequisites. No new formal
native refinement theorem or backend acceptance binding is claimed. Original
issuer/mapping/credential/target authentication, source/role/ACL lifetime, graph
capture and complete protected disclosure remain open. Last full backend gate
checkpoint remains26/132 with106 missing bindings; goal active.

### Formal release-observation limit — 2026-10-11

`evidence/security-release-observation-formal/d568bc78-6f68-433b-9899-8e277afc42fd`
retains five Z3 4.15.4 queries and fresh-context SMT-LIB replays: three UNSAT,
two SAT. In the explicit capture/loss/reacquisition/check model, release requires
an observed guard; loss without reacquisition refuses; no loss preserves the
original cut. Countermodels show both that the same native xid can survive guard
loss and that lost/reacquired guards can pass final observation without continuity.
This explains the boundary of the160-method native packet, rather than proving a
PostgreSQL or host refinement. No-loss remains a premise of exclusive toolkit
custody and the prohibition on raw aliases. Trace CONTRACT-063/STP-056 L03/L11;
no backend binding or complete final-release theorem is promoted.

Post-main integration requalification: concurrent host receive/resource changes
are preserved in main b3647328. Fresh
`evidence/python-psycopg-epoch-cut/9880771d-a781-4414-b64e-a043dec60dce` passes160
native methods and module boundaries on PostgreSQL18.6, with current source pins
and three stop0/status3/socket-absent cleanups. The prior native packet retains
its original pre-integration source scope; qualified exclusions remain unchanged.

### Conservative predefined-role privilege snapshot — 2026-10-11

Private `_run_predefined_role_excluded_ddl_fenced_epoch_operation` composes the
original epoch/DDL/role/definer checks with a native predefined-role exclusion.
For every identity SET-reachable from actual session/effective users, inspect
USAGE or SET reachability to reserved pg_ roles. This conservatively refuses
predefined capabilities without treating MEMBER, SET and inherited privilege as
equivalent or assigning portable meanings to version-dependent built-in roles.
It is an optional private composition, not automatically applied to the delegated
service spike or a new public admitted backend profile.

Three native controls observe a real private Assignment count after SELECT is
revoked but pg_read_all_data is inherited with SET FALSE, refusal before callback
for that case and SET-only pg_write_all_data, and acceptance of inactive membership
with both INHERIT and SET FALSE. Final
`evidence/python-psycopg-epoch-cut/7ddffb08-f18c-4d54-b497-901a6de7e0e4`
passes163 methods on PostgreSQL18.6/psycopg3.3.6 binary, module boundaries,
141 current/preimage Truss pins,363 UMF sources and1705 native payload pins,
with three stop0/status3/socket-absent cleanups.

Final `evidence/security-predefined-role-formal/ec82bd53-2246-4b50-a071-77d0df523de7`
retains five source inputs and five Z3 4.15.4 queries with independent-context
SMT-LIB replay: three UNSAT active-path refusal results and two SAT inherited-
privilege/inactive-membership controls. Initial651651f8 retains the same model
with only four source pins; final packet adds exact native check source custody.
No PostgreSQL role graph/SQL or host refinement theorem is claimed. Role/ACL
lifetime, ordinary grants, complete routine closure, original authentication,
protected graph and final disclosure remain open. Trace shared CONTRACT-063 /
STP-056 B04/B05/B10/B11 and US-056 AC5/AC8/AC9 prerequisites. No new backend
binding: fresh full gate remains26/132 with106 unbound cases; goal active.

### Delegated caller predefined-role admission — 2026-10-11

The owned delegated profile0.4 service now executes the extracted original native
predefined-role reachability check inside caller custody before caller/profile
verification or executor fact capture. The optional epoch/DDL role composition
uses that same check. It excludes active predefined privileges of every identity
SET-reachable from original session/effective users; it does not authorize an
executor, authenticate an issuer or replace original native identity verification.

Two native controls refuse before the executor runs: directly inherited
pg_read_all_data with SET FALSE, and a caller that can SET a bridge role which
inherits pg_read_all_data. In the latter, original caller USAGE and SET paths to
the predefined role are both false; actual SET LOCAL ROLE bridge nevertheless
exposes the private Assignment count. Rollback restores caller identity before
admission, and the service refuses without invoking the evaluator. Existing
catalog-only delegated permit/deny and transaction/guard-retirement controls pass.

Final `evidence/python-psycopg-epoch-cut/be21743a-f9f9-4ba6-a468-3a56030a37df`
passes165 methods on PostgreSQL18.6/psycopg3.3.6 binary, module boundaries,
141 current/preimage Truss source pins,363 original UMF sources,1705 native
payload pins and three stop0/status3/socket-absent cleanups. Formal replay
`evidence/security-predefined-role-formal/beadcd6f-3b03-42dd-a98f-a03643a8a717`
retains five exact inputs and five original queries, three UNSAT/two SAT with
fresh-context replay. It remains an abstract role-path model, not native SQL/role
or host refinement. Trace CONTRACT-063/STP-056 B04/B05/B10/B11 and US-056 AC5/
AC8/AC9 prerequisites. Role/grant lifetime, ordinary grants, complete routine
closure, trusted caller/executor/issuer/mapping/target authentication and protected
publication remain open. No new backend binding; full goal stays active at26/132,
106 unbound required cases.

### Delegated caller private-fact privilege exclusion — 2026-10-11

Owned profile0.4 caller admission now inspects all SET-reachable original caller
identities for superuser/CREATEROLE/BYPASSRLS, EXECUTE on any SECURITY DEFINER
routine, and table or column privileges on the original provider relation OIDs.
The table probe includes SELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER/
MAINTAIN; the column probe includes SELECT/INSERT/UPDATE/REFERENCES. The native
OID-based definer probe intentionally does not depend on current schema USAGE.
This is conservative private-service snapshot exclusion, not complete callable
closure, grant/role lifetime or authorization of the executor.

Three controls establish actual column-only and full-table private reads, and
EXECUTE reachability to a definer without schema USAGE, then refuse before executor
evaluation. Final `evidence/python-psycopg-epoch-cut/37e19ef3-7536-45c8-bfc4-2c86f63b7e8d`
passes168 native methods on PostgreSQL18.6/psycopg3.3.6 binary, module boundaries,
141 current/preimage source pins,363 original UMF and1705 native payload pins,
with three stop0/status3/socket-absent cleanups. Earlier5e0d4404 ran zero tests due
to shared-memory-ID exhaustion; bdba4985 ran168 with one incorrect name-resolution
probe denied by schema USAGE. The corrected probe captures the routine OID as the
installer. Then71a6ff76 ran168 with one existing delegated-permit refusal; the final
unchanged-source rerun passes. That intermittent refusal remains unexplained and
retained, not evidence of general availability or deterministic load performance.
No refusal or resource bound was weakened to obtain the passing run.

Formal `evidence/security-private-fact-privilege-formal/9611d128-bf44-495a-95ed-62ca5a7d64df`
retains five source inputs and five Z3 4.15.4 SMT-LIB queries/fresh-context replays:
three UNSAT exclusion results and two SAT controls, including a table-only filter
admitting column-only access. Initial38563687 retains the pre-correction test input.
This is an abstract conditional model, not native privilege/role/SQL refinement.
Trace CONTRACT-063/STP-056 B04/B05/B10/B11 and US-056 AC5/AC8/AC9 prerequisites.
Complete routine/alternate-source/diagnostic closure, grant/role lifetime, original
caller/issuer/mapping/target credentials and protected publication remain open.
No backend binding is promoted; full goal stays active at26/132 with106 unbound
required cases. Diagnose the retained intermittent refusal before any availability
or complete protected-service qualification.

Integrated-main requalification: concurrent installation privilege work changed
native host test and boundary checker inputs. The pre-merge37e19ef3 packet retains
its original source scope. Fresh
`evidence/python-psycopg-epoch-cut/9c3297e7-8705-4d75-81b4-f893d8d21140`
passes168 native methods and boundaries against integrated main a69788bf, with142
current/preimage Truss source pins and three stop0/status3/socket-absent cleanups.
This requalifies the finite composition; the retained intermittent refusal and
complete backend admission/lifetime obligations remain open.

### Sanitized delegated layer diagnostics and evaluator timeout — 2026-10-11

Owned evaluator subprocess TimeoutExpired now becomes a sanitized TimeoutError,
so the original executor host classifies it as locally contained cancellation.
The owned native harness records only test name, executor/caller status and safe
result code plus elapsed milliseconds in `delegated-layer-outcomes.jsonl`. No
fact cells, subjects, credentials, identities, stdout/stderr or exception text are
retained in that journal. Production caller results remain sanitized and raw
executor diagnostics remain private.

A deterministic TimeoutExpired carrying private partial stdout/stderr produces
executor cancelled, outer caller invalid_transaction, no private text in the
returned result and both original reservations retired. This distinguishes the
refusal layer without weakening the4-second evaluator or5-second host bounds.
Final `evidence/python-psycopg-epoch-cut/10a9cf97-62a9-4d56-8b0d-c9ab4579a068`
passes169 methods, module boundaries and142 current/preimage source pins on
PostgreSQL18.6/psycopg3.3.6 binary, with363 UMF and1705 native payload pins and
three stop0/status3/socket-absent cleanups. Journal observations distinguish
pre-executor privilege refusal, executor cancellation, executor identity refusal
and caller guard-retirement refusal after successful evaluation; ordinary permit
and deny succeed. These finite schedules do not identify the earlier71a6ff76
intermittent permit refusal or prove deterministic availability under load.

Trace shared CONTRACT-063/STP-056 B10/B12/B16/L11 and US-056 AC8/AC10 custody/
diagnostic prerequisites. The journal is owned test evidence, not a public audit
API or receipt that grants authority. No new formal native refinement or backend
binding is claimed. Original authentication, full routine/source/privilege/lifetime
closure and complete protected disclosure remain open; full goal active at26/132,
106 unbound required cases. Use these layer outcomes to diagnose any future
reproduction before making availability claims.

### Delegated preparation deadline, repeated decisions and cancellation recovery — 2026-10-11

Initial evaluator source pinning now occurs before delegated caller operation
custody/deadline acquisition. A private frozen administrative preparation retains
the selected tool and exact source digest tuples. Guarded evaluation still checks
those original bytes before returning a decision. Public delegated inputs cannot
supply a preparation; the constructible private dataclass is not authentication,
a reusable authority capability or a complete package-delivery proof. Native
caller/executor/epoch/fact checks and4-second evaluator/5-second host bounds remain.

Repeated actual calls across fresh executor transactions yield permit/deny/permit
for authored assigned/unassigned Staff fixtures. A contained evaluator cancellation
allows an explicit same-host retry with a freshly issued generation and the exact
previously issued predecessor; no cancelled decision is reused. A real owned
source-file edit after preparation refuses guarded publication, and exact edit
restoration preserves unrelated concurrent content. Preparation is independently
observed before either host has pending operation custody or pair reservation.

Final `evidence/python-psycopg-epoch-cut/9ed3269a-0edd-4aba-8aa3-1ab66b4e815f`
passes172 methods, module boundaries and142 current/preimage Truss pins on
PostgreSQL18.6/psycopg3.3.6 binary,363 UMF sources,1705 native payload pins and
three stop0/status3/socket-absent cleanups. Earlier64ce211a passes171 before the
source-drift control. Initial5a8176ee fails two new fixture controls: absent s2 row
and stale predecessor. Those fixtures were corrected without weakening admission.
Thenf46b8c09 passes both new schedules but the existing permit case records executor
ok/caller cancelled at6965ms. This reproduces a caller deadline refusal; initial
source pinning inside that window was an avoidable workload. The earlier71a6ff76
refusal remains without layer diagnostics and cannot be retroactively assigned
this cause. Passing finite schedules after preparation refactoring do not prove
unrestricted availability or exclude every deadline/refusal cause under load.

Trace CONTRACT-063/STP-056 B10/B11/B12/B16/L03/L11 and US-056 AC8/AC9/AC10
prerequisites. No new formal native refinement theorem or backend binding. Complete
original caller/issuer/mapping/package/target authentication, source/role/ACL and
callable lifetime, graph capture and protected final publication remain open.
Full goal remains active at26/132 with106 unbound required cases.

### Delegated final caller privilege snapshot — 2026-10-11

The owned delegated service rechecks original native caller identity, predefined
privilege reachability and private-fact table/column/definer/administration
exclusions after executor evaluation and existing native guard observation, before
returning the decision. This detects final-state drift; it does not hold shared
role/ACL lifetime guards or make the checks/publication atomic.

Two native controls use separate original postgres administrative connections to
GRANT inherited pg_read_all_data or EXECUTE on an existing SECURITY DEFINER
private-count routine after successful original evaluation. These uncoordinated
administrative grants actually complete under retained executor guards. The
caller then refuses; sanitized layer journal retains executor ok/caller
invalid_transaction, with no decision returned. Final
`evidence/python-psycopg-epoch-cut/c17be521-afd0-41c0-b3fd-13e6a3668395`
passes174 native methods and module boundaries on PostgreSQL18.6/psycopg3.3.6
binary,142 current/preimage Truss sources,363 UMF and1705 native payload pins,
with three stop0/status3/socket-absent cleanups.

`evidence/security-caller-release-snapshot-formal/29d04440-5819-4401-98fd-378bdc6f31a9`
retains five exact source inputs and five Z3 4.15.4 SMT-LIB/fresh-context replays:
three UNSAT refusal results and two SAT controls. Admission-only checking admits
late privilege; grant-and-revoke between admission/final snapshots remains
compatible with release. Changes after the final check also remain unqualified.
These are conditional endpoint-model results, not native role/catalog/SQL/host
refinement or uninterrupted authority/revocation-drain theorems.

Trace shared CONTRACT-063/STP-056 B04/B05/B10/B11/L03/L11/L13 and US-056 AC5/AC8/
AC9 prerequisites. Complete authorized writer participation, original issuer/
caller/mapping/package/target authentication, shared role/ACL and callable lifetime,
graph capture and atomic protected publication remain required. No new backend
binding; full goal stays active at26/132 with106 unbound cases.

### Cross-database committed-pending authority transition spike — 2026-10-11

Governing shared CONTRACT-063 requires complete writer participation, fresh cuts
and reader drain through protected release. Database-local advisory or relation
fences do not intercept shared-role mutations made in another database. A private
backend transition may first commit an unadmitted pending generation in the
original source realm, then perform the remote mutation, and only after explicit
original requalification issue a fresh successor. Existing epoch registry opaque
profile/evidence fields carry this spike without a core-envelope or layout change.
This lifecycle mechanism belongs to the backend enforcement/issuer implementation;
the portable ordering and refusal obligations remain shared security semantics.

| Phase | Required behavior |
|---|---|
| Original admitted generation | Original readers retain their source-realm guard through release. |
| Publish pending | Original native issuer must exclude retained readers before committing pending; no remote change precedes that commit. |
| Pending / remote mutation | Old generation comparisons and all existing semantic provider-profile parsers refuse. Pending remains closed after publisher disconnect. |
| Requalify successor | Original issuer independently proves complete current state and known remote outcome, then issues a fresh successor with exact pending predecessor. |
| Interrupted or unknown outcome | Remain pending; inspect original native state. No blind replay, guessed commit or automatic reopening. |

`scripts/security_authority_transition.py` implements only the private successful
commit/explicit-successor fixture mechanics using the original installed native
issuer. It requires an idle administrative connection, returns after successful
transaction completion, preserves installation/incarnation and exact predecessor,
and uses an unsupported pending profile kind. Successor qualification is a trusted
fixture premise, not authenticated or independently enforced by this helper.
Comparison dataclasses and hashes grant no authority. Complete writer routing,
issuer credentials, malicious/incorrect administrative bypass, remote commit-unknown,
crash/WAL/refinement and recovery require separate qualification. This is not a
shipped public coordinator or distributed atomic-commit implementation.

Native controls commit pending in the source database, disconnect its publisher,
change a shared role through a second database and independently observe pending
still current. Old fenced read refuses before callback; the original dependency
recipe rejects pending. Explicit successor issuance restores the administrative
fixture and receives a fresh native epoch. Another control proves pending cannot
publish while an original retained reader holds SHARE; after reader retirement
pending succeeds. This proves finite native commit/connection-disconnect schedules,
not power-loss durability or all writer coverage. Final
`evidence/python-psycopg-epoch-cut/42d80ee6-9171-47ab-860c-1c234160581c`
passes176 methods, module boundaries,143 current/preimage Truss source pins on
PostgreSQL18.6/psycopg3.3.6 binary,363 UMF and1705 native payload pins and three
stop0/status3/socket-absent cleanups.

`evidence/security-pending-authority-formal/b021be50-a63f-4b93-8b06-eb2d1ba4095f`
retains five exact inputs and five Z3 4.15.4 SMT-LIB/fresh-context replays, three
UNSAT/two SAT. Conditional ordering excludes pending admission, undrained pending
publication and reopening under unknown remote outcome. Omitting committed
pending or qualification yields countermodels. The qualification guard is an
obligation, not implemented authenticated receipt ingestion or a native distributed
refinement theorem. Trace CONTRACT-063/STP-056 B11/B12/L03/L11/L13 and US-056
AC9/AC10 prerequisites. No backend binding is promoted; complete authentication,
writer/current-state closure, graph capture and protected final release remain
required. Full goal active at26/132 with106 unbound cases.

Integrated-main runtime requalification: concurrent packaging work changes the
selected distribution to pgserver-pg18 18.6.1, engine18.6. Historical42d80ee6
retains its original18.6.0 declaration/payload scope. Fresh
`evidence/python-psycopg-epoch-cut/d1962dc8-ef99-4968-9540-d9da358c7adb`
passes176 methods, boundaries and143 current/preimage Truss inputs on the selected
18.6.1 release, with363 UMF and1705 native payload pins and three cleanups.
Supplementary `runtime-release-provenance.json` retains exact macOS arm64 wheel
SHA256 fd42f07982693e16478ed42a297890d142d22250116e08887146e690f0dd2649,
published r2 checksum URL/file digest and installed distribution metadata match.
The task-owned environment is separate from historical runtime environments.
This is native/release correspondence, not hermetic build or publisher identity
qualification. Formal five-input model source remains unchanged; no backend
binding or complete cross-database issuer/qualification/recovery claim is promoted.

### Pending transition current-image correspondence and fresh producer cut — 2026-10-11

Private transition issuance now opens its own fresh administrative READ COMMITTED
transaction after requiring an idle connection. It invokes the installed native
participating-writer fence before reading current pointer/registry correspondence.
Six exact OID25 text fields compare installation, epoch, incarnation, original
profile/evidence hex and actual read-committed isolation. The marker/write modes
remain held through native successor issuance and commit/abort. This excludes
participating writers; uncoordinated administrators and complete cross-database
routing remain unqualified. No borrowed caller transaction is weakened.

Native controls reject a fabricated pending kind for an otherwise current epoch
and changed pending evidence, with unchanged pointer and registry count. An
inherited repeatable-read session default still permits the fresh producer path;
the native isolation readback verifies READ COMMITTED and the session default
remains unchanged afterwards. Final
`evidence/python-psycopg-epoch-cut/ff7b9635-e298-456f-9dc8-7a5c1b36f0e0`
passes179 methods, boundaries,143 current/preimage sources on engine18.6 /
pgserver-pg18 18.6.1 / psycopg3.3.6 binary,363 UMF and1705 native payload pins
with three stop0/status3/socket-absent cleanups. Earlierb96528b2 runs178 and fails
ancillary database creation under the3-second fixture default; that isolated
administrative allocation/deallocation now uses its own bounded15-second connection.
Security-operation deadlines are unchanged. Then32e6bc7f runs179 and fails existing
fixture DDL timeout and delegated containment under pressure; unchanged-source
final rerun passes. Both failed packets remain retained. Observed system load
41.77/59.78/65.17 may explain timing pressure but does not prove every failure cause
or deterministic availability. Required complete recovery/availability remains open.

Formal `evidence/security-pending-authority-formal/891218fc-7449-414c-a934-c534c5705315`
retains five exact source inputs and eight Z3 4.15.4 SMT-LIB/fresh-context replays,
five UNSAT/three SAT. It adds current-image and fresh post-fence snapshot guards;
self-asserted pending kind without native correspondence admits a countermodel.
Initiale20cbfba retains seven queries/four UNSAT/three SAT before explicit freshness.
This remains a conditional ordering model, not native SQL/commit/driver refinement,
authenticated issuer or successor-qualification enforcement. Trace shared
CONTRACT-063/STP-056 B11/B12/L03/L11/L13 and US-056 AC9/AC10 prerequisites.
Complete issuer/mapping/target authentication, known remote outcome recovery,
writer/callable/current-state closure, graph capture and atomic protected release
remain required. No backend binding; full goal stays active at26/132 with106
unbound required cases.

### Single pending transition and stale completion replay — 2026-10-11

The private canonical pending fixture refuses a begin from an already-pending
comparison. A forged nonpending comparison still must match the actual pointer/
registry bytes under the native writer fence before issuance. This prevents the
helper's own overlapping transitions from superseding an unresolved pending
phase. Unknown/foreign administrative profiles and all external writer coverage
remain unqualified; this is not a generic issuer authorization rule.

Two native controls prove an overlapping begin and completion replay after a
successful successor leave both current pointer and registry count unchanged.
Final `evidence/python-psycopg-epoch-cut/750ff122-d396-44a2-8e1e-2990172ed62a`
passes181 methods, boundaries and143 current/preimage Truss sources on engine18.6 /
pgserver-pg18 18.6.1 / psycopg3.3.6 binary,363 UMF and1705 native payload pins,
with three stop0/status3/socket-absent cleanups.

Formal `evidence/security-pending-authority-formal/2904ff32-8353-4cc2-975b-dfe6a22c992f`
retains five original inputs and ten Z3 4.15.4 SMT-LIB/fresh-context replays,
six UNSAT/four SAT. The added single-pending obligation excludes second begin;
omitting it admits overlap. Existing native-image guard excludes stale successor
correspondence. This is a conditional ordering model, not native SQL/commit/driver
refinement, authenticated issuer or recovery proof. Trace CONTRACT-063/STP-056
B11/B12/L03/L11/L13 and US-056 AC9/AC10 prerequisites. Exact remote-plan/outcome
binding, issuer/mapping/target authentication, complete writer/current-state
closure, graph capture and protected final release remain required. No new backend
binding; full goal active at26/132 with106 unbound required cases.

### Live role identity and cached role-setting replacement — 2026-10-11

The newly selected CONTRACT-005 session-person fresh-catalog policy authorizes
native session person A with exact role=none and registrar authority. It is a
separate catalog-operation profile. It does not replace the owned delegated
`truss-flat-fact-provider-fixture/0.4` data-read profile, which compares explicitly
selected original session/effective role OIDs and retains its privilege exclusions.
The similarly numbered native catalog context0.4 is not this provider profile.
Neither profile derives identity from a cached role-setting name.

Two native controls apply a controlled role rename/recreation before fresh fixture
profile issuance. The active native role retains its OID under the renamed role,
while current_setting(role) still names the replacement role with another OID.
Live-OID-based delegated evaluation permits the original mapped fixture subject;
a fixture issuer selecting the replacement hint OID refuses before executor
execution. The replacement role has CREATEROLE but cannot donate its identity.
This is fresh controlled identity correspondence, not an uncoordinated role-change
lifetime guarantee, session-person catalog facade qualification or original
subject-mapping authentication.

Final `evidence/python-psycopg-epoch-cut/8a721750-03d0-4498-8322-efdc497192fb`
passes183 methods, boundaries,143 current/preimage Truss sources on engine18.6 /
pgserver-pg18 18.6.1 / psycopg3.3.6 binary,363 UMF and1705 native payload pins,
with three stop0/status3/socket-absent cleanups. Formal
`evidence/security-caller-binding-formal/6a204e59-b195-4825-9569-4369f75ee22d`
retains five exact source inputs and eight Z3 4.15.4 SMT-LIB/fresh-context replays,
four UNSAT/four SAT. It adds live-versus-hint role correspondence; hint-only
mapping admits a replacement-identity countermodel. Faithful native capture and
semantic subject mapping remain separate premises; no native decoder/driver,
authentication, source/role lifetime or protected-release refinement is claimed.
Trace CONTRACT-063/STP-056 B05/B11/B12 and US-056 AC5/AC9/AC10 prerequisites.
Complete issuer/mapping/target credentials, callable/writer/current-state closure,
graph capture and protected publication remain open. No backend binding; full goal
active at26/132 with106 unbound cases.

Integrated-host requalification: main semantic-ordinal work changed psycopg_host
and module boundary checker inputs. Pre-merge8a721750 keeps its original scope.
Fresh `evidence/python-psycopg-epoch-cut/6e633de9-94eb-4514-a47e-9f35fd98cdee`
passes183 methods and boundaries with143 current/preimage source pins and three
cleanups on the integrated host. Earlierf94848cd runs183 and fails an existing
permit control: journal records executor cancelled/caller invalid_transaction
at11389ms. Unchanged-source rerun passes. Both packets are retained; no deadline,
containment or authority check was weakened and deterministic availability is not
claimed. Exact earlier cause remains unqualified beyond the observed cancellation.
The eight-query abstract caller model remains unchanged and does not establish
native host/ordinal refinement. Full backend acceptance stays26/132; goal active.

Final source-inventory integration: a further main catalog-candidate change alters
one retained input after6e633de9. Fresh
`evidence/python-psycopg-epoch-cut/1ba2a07c-9f61-4b5c-aaa8-c6a53b9418f0`
passes183 methods, boundaries and143 current/preimage inputs with three cleanups
against both integrated changes. Earlier packets retain their own source scopes.
This security composition run does not independently qualify the new catalog
facade/dispatch workflow or promote any backend acceptance binding.

### Private authorization-fact statistics counterexample — 2026-10-11

An actual catalog-only native caller with no table/column SELECT can distinguish
private Assignment populations through pg_catalog.pg_class.reltuples. After
excluded admin ANALYZE, controlled populations1 and2 yield text statistics1 and2;
private SELECT/count still refuse42501. The extra inactive fixture row is removed
and statistics restored. This is finite analyzed-table statistics evidence, not
an exact general-purpose row-count oracle or graph logical-association count proof.
Final `evidence/python-psycopg-epoch-cut/9e6718b6-281d-4c0c-8e4d-ab3c5f0318d9`
passes184 methods, module boundaries,143 current/preimage sources on engine18.6 /
pgserver-pg18 18.6.1 / psycopg3.3.6 binary,363 UMF and1705 native payload pins,
with three stop0/status3/socket-absent cleanups.

This confirms that `_exclude_native_private_fact_privileges` establishes only its
named table/column/definer privilege snapshot, not B10 observation isolation. RLS,
column masking and ACL denial alone do not remove system-catalog/statistics access.
The owned delegated tool's trusted application host references are not evidence
that an end user lacks another SQL credential/endpoint. A positive hidden-fact
profile must qualify every untrusted observation channel, including system
catalogs, statistics, plans/errors and alternate endpoints. Select an enforced
mediated channel with private executor credentials and complete receiver routing,
or independently qualify native diagnostic/callable/catalog restrictions. Merely
adding a request/configuration boolean such as sqlExposure=false is forbidden.
Unknown coverage refuses positive admission. This obligation applies equally to
raw tables and graph stores; the concrete counterexample covers this flat fixture.

Trace CONTRACT-063/STP-056 B04/B05/B10/B11/B12 and US-056 AC5/AC8/AC9/AC10. The
next protected service integration must prove credential/receiver channel custody
and native source privacy, alongside original issuer/subject/mapping/target,
writer/current-state and final-release closure. No backend binding or complete
privacy/noninterference claim is promoted. Full goal remains active at26/132 with
106 unbound cases; the original acceptance scope is unchanged.
