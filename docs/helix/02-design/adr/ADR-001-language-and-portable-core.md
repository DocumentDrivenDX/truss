---
ddx:
  id: ADR-001
  type: adr
  activity: design
  status: accepted
  authoring:
    home: repo
  links:
    - id: truss.vision-input
      kind: informed_by
    - id: truss.concerns
      kind: informed_by
    - id: SPIKE-001
      kind: informed_by
    - id: SPIKE-002
      kind: informed_by
    - id: ADR-002
      kind: informed_by
---

# ADR-001: TypeScript first, with a portable core and measurable triggers for a Rust core

| Field | Value |
|-------|-------|
| Status | **Accepted** with the drafted recommendations. Node support (D1) is provisional until check L1 (see §Owner decisions) |
| Date | Proposed 2026-10-03; accepted 2026-10-03 |
| Decider | Project owner |
| Drafted by | Claude Code agent |
| Evidence | [discovery input](../../00-discover/vision-input.md) §Language Analysis, [concerns](../../01-frame/concerns.md), [SPIKE-001](../spikes/SPIKE-001-apache-age.md) C9, [SPIKE-002](../spikes/SPIKE-002-storage-bake-off.md), [ADR-002](ADR-002-storage-strategy.md) |

AGENTS.md requires this ADR to confirm the language choice and the portable-core
split before any implementation code lands. With its acceptance, that condition
is met.

## Context

The owner directed on 2026-09-24 that truss is implemented in TypeScript first,
with Bun for development and testing, and moves to Rust only if a measured need
arises. The owner first considered Rust with Python and Node bindings, because
the query compiler must be fast and memory-safe and Rust embeds more easily than
Go. The [discovery input](../../00-discover/vision-input.md) records the options
weighed:

| Option | For | Against |
|--------|-----|---------|
| Rust core with Python and Node bindings | No runtime or garbage collector; C ABI; mature bindings (PyO3, napi-rs, wasm-bindgen); memory and data-race safety | Cannot reuse UMF's TypeScript library; truss would need its own UMF reader; per-platform binary builds |
| Go | Simple language; good concurrency | A Go runtime per embedded library; cgo overhead; awkward Python and Node bindings |
| TypeScript on Bun | Reuses UMF's TypeScript library directly; same toolchain as UMF; PostgreSQL does the heavy execution | No native Python embedding; single-threaded runtime; slower compile path |

A conflict is open in [concerns](../../01-frame/concerns.md). The `typescript-bun`
concern prefers Bun-native APIs (`Bun.sql`, `Bun.file`), but a library that Node
applications embed cannot depend on them. The concerns document records a
project override, a core free of I/O and host-specific APIs, marked "Needs ADR
(ADR-001)". It follows the split in UMF's own ADR-002.

What the spikes observed about the TypeScript path:

- **Throughput is adequate.** SPIKE-002's engine parsed, encoded, validated and
  rendered records in Bun 1.3.11 at 7.8–19.3 µs per record (51,827–128,873
  records per second, `out/23_engine_cost.txt`). Validation ran in client CPU
  before the insert; the database round trip dominated the write cost.
- **Generic code stays small.** SPIKE-002's option C catalog derivation, engine
  validator, write path and revision procedure were about 350 lines of
  TypeScript, and its six query shapes came from 16 template lines plus 5 helper
  lines.
- **Default driver decoding loses values.** `Bun.sql` and `pg` decode JSONB with
  `JSON.parse`, which rounds integers beyond 2^53 and drops decimal trailing
  zeros. `Bun.sql` also truncates timestamps to milliseconds and drops the scale
  of a zero `numeric`. Reading as text and parsing exactly gave zero silent
  changes (SPIKE-002 FINDING 5; SPIKE-001 C9 on Node 22 with `pg` 8.23.0 and on
  Bun).
- **UMF's library works from TypeScript but needs care on hot paths.** SPIKE-002
  imported UMF from source at commit `24d3bf3c`. Its YAML-backed
  `parseNativeJson` was used for exact reads, but bulk loading needed a faster
  exact parser. `encodeCoreKeyTuple` revalidates the whole document per call
  (124–176 keys per second), so bulk use needs a cached encoder.
- **Node with `pg` was not exercised in SPIKE-002.** It is listed as a
  limitation there.

[ADR-002](ADR-002-storage-strategy.md) adds requirements that apply in every
language: prepared statements in every adapter, an exact text read path, and
row-lock and transaction control (`FOR NO KEY UPDATE`, SERIALIZABLE where
needed).

## Decision

Implement truss in TypeScript, structured so the core can later be ported to
Rust and verified against the same conformance corpus. Each point carries a
confidence: **evidence** (a spike measured it), **inferred** or **choice**.

### D1. Language and runtimes

- truss is written in TypeScript (strict mode), as ECMAScript modules.
  *(choice; owner direction)*
- Bun is the development, test and tooling runtime. *(choice; owner direction)*
- The published library supports both Bun and Node. Node support starts with
  the maintained LTS lines, beginning with Node 22 (SPIKE-001 exercised Node
  22). *(choice; provisional until L1)*
- The core, the Bun adapter and the `pg` adapter are separate packages in one
  workspace, so the core package can be compiled with no host type definitions
  (D2). *(choice)*

### D2. Portable core

The code is split into three layers, with dependencies only pointing downward:

| Layer | Contents | May use |
|-------|----------|---------|
| Core | UMF catalog and binding derivation, value encoding and validation, enforcement reporting, query and mutation compilation, SQL generation per dialect, the exact value model | ECMAScript built-ins only. No I/O, no `node:*` or `bun` imports, no host globals, no clocks or randomness except through injected interfaces |
| Adapters | Database drivers behind one narrow interface: prepared statements, typed parameters, text-mode results, transactions with isolation level, row locks, advisory locks | Host and driver APIs: `Bun.sql`, `pg` |
| Tooling and tests | CLI, loaders, benchmarks, conformance runner | Anything, including Bun-native APIs |

This resolves the open conflict in concerns. The `typescript-bun` practice of
preferring Bun-native APIs applies to adapters, tooling and tests, and never to
the core. *(choice; follows UMF's ADR-002)*

The boundary is enforced mechanically, not by convention: the core package
compiles with no host type definitions, and a lint rule rejects host imports in
it. *(choice)*

### D3. Exact values in TypeScript

- The core never represents a stored integer, decimal or timestamp as a
  JavaScript `number` or `Date`. Values travel as source tokens, with the same
  tree shape as UMF's NativeJson. `bigint` is used for integer arithmetic.
  Decimal arithmetic (for example invariants such as `lineTotal = quantity *
  unitPrice`) uses a small truss implementation over `bigint` (scaled integers)
  with no floating point and no third-party dependency. Conformance tests check
  it against PostgreSQL `numeric` results. *(evidence: SPIKE-002 FINDING 5;
  choice for the implementation)*
- Every adapter returns JSONB, `numeric`, `bigint` and temporal columns as text,
  and the core parses them exactly. An adapter that cannot do this is not
  supported. *(evidence: SPIKE-001 C9, SPIKE-002 FINDING 5)*
- A conformance test runs the SPIKE-002 value corpus through every supported
  runtime and driver pair. *(choice)*

### D4. Consuming UMF

- The core uses UMF's TypeScript library for parsing and validating UMF
  documents, pinned to an exact version or commit, and never re-implements UMF
  semantics. *(choice; reuse is the main reason for TypeScript)*
- Hot paths (bulk encoding, key tuples) call UMF once per document revision and
  cache the result. They never revalidate per value. *(evidence: SPIKE-002
  key-tuple timing)*
- Exact JSON parsing on the read path may use a truss implementation, as long as
  conformance tests check it against UMF's `parseNativeJson`. *(evidence:
  SPIKE-002 used both)*

This settles how the TypeScript core reads UMF. Whether truss should instead
read pre-validated artifacts produced by UMF tooling stays an open decision; it
matters mainly for a future Rust core.

### D5. Conformance corpus as data

The conformance corpus is language-neutral data. It holds:

- UMF documents and bindings;
- graph data;
- operations: writes, revisions and queries;
- expected results;
- expected enforcement reports, with rule, layer and outcome.

Expected results and reports are normative. Expected SQL is recorded as
informative, so a Rust core can generate different but equivalent SQL.
Differential runs compare results, not SQL text. *(choice)*

The SPIKE-002 harness inputs (sales model, revisions R1–R5, value corpus,
enforcement matrix) are the seed corpus. *(choice)*

### D6. Triggers for a Rust core

Moving the core to Rust is considered only when at least one trigger fires and
is recorded with evidence in a new ADR:

| Trigger | Measure |
|---------|---------|
| T1. In-process use from a non-JavaScript host | A named consumer needs truss inside a Python (or other non-JavaScript) process, and an out-of-process service does not meet that consumer's needs |
| T2. Compile latency | Query or mutation compilation misses its PRD latency target on the benchmark shapes after profiling and caching. The proposed target is a cache-miss compile under 1 ms p95, the order of PostgreSQL's own planning for these shapes in SPIKE-002 |
| T3. Validation throughput or memory | Engine validation or encoding misses its PRD throughput or memory target after profiling. The observed baseline is 51,827–128,873 records per second per core in Bun |
| T4. Running inside the database | A decision to enforce rules inside PostgreSQL as an extension, which needs C or Rust (for example pgrx), not TypeScript |

T2 and T3 figures are proposals for the PRD's non-functional requirements, not
measured limits. *(choice)*

### D7. How a move to Rust would happen

- Port the core only. Adapters and tooling may stay in TypeScript and call the
  Rust core through Node-API (napi-rs, which Bun also loads) or WebAssembly.
- The Rust core passes the full conformance corpus before it replaces the
  TypeScript core. Both cores are maintained in parallel only during that
  transition.

*(choice)*

## Consequences

**Positive**

- Direct reuse of UMF's TypeScript library and toolchain; no second UMF reader.
- One language for the core, adapters, tests and tooling during the period of
  fastest design change.
- The portable-core boundary keeps a Rust port mechanical: the core already has
  no I/O and the corpus already defines correct behaviour.

**Negative**

- No in-process Python use until a Rust core exists (T1).
- Every adapter carries an exact text read path and cannot use default driver
  decoding.
- Exact decimal arithmetic must be implemented or depended on; JavaScript has no
  built-in decimal type.
- The core cannot use Bun's faster native APIs. Any benefit from them is
  limited to adapters and tooling.
- Supporting both Node and Bun doubles the adapter and conformance matrix.

**Effect on concerns.** Recorded in [concerns](../../01-frame/concerns.md) on
acceptance: the `typescript-bun` override's authority changes from "Needs ADR
(ADR-001)" to ADR-001. The `rust-cargo` concern stays inactive until a D6 trigger fires.

## Alternatives considered

| Alternative | Why not chosen |
|-------------|----------------|
| Rust core from the start | Loses direct UMF library reuse and slows early design iteration. No measured need yet: PostgreSQL does the heavy execution, and SPIKE-002's TypeScript engine throughput was adequate |
| Go | A runtime per embedded library, cgo overhead, weak Python and Node embedding |
| TypeScript using Bun-native APIs everywhere | Node applications could not embed truss |
| TypeScript on Node only | Gives up Bun's built-in test runner and PostgreSQL client for development, with no gain for the core, which stays host-neutral either way |

## Conditions that would reverse or modify this decision

1. Any D6 trigger fires and is recorded with evidence.
2. UMF's TypeScript library stops being the reference implementation truss can
   pin to, removing the reuse benefit.
3. Keeping the core host-neutral costs more than the embedding benefit, for
   example if Node support finds no consumer.

## Validation after acceptance

| ID | Check | Decides |
|----|-------|---------|
| L1 | Run the SPIKE-002 fidelity suite on Node 22 with `pg`, as well as Bun with `Bun.sql` | D1 Node support; D3 adapter rule |
| L2 | Build a skeleton core package with the D2 restrictions (no host types, lint rule) and import it from both Node and Bun | D2 is enforceable |
| L3 | Measure cache-miss compile time for the six SPIKE-002 query shapes in a minimal TypeScript compiler | T2 baseline |

## Scope of the evidence

- Bun 1.3.11 with `Bun.sql` (SPIKE-001, SPIKE-002);
- Node 22.22.2 with `pg` 8.23.0 (SPIKE-001 only);
- PostgreSQL 17.11 and 18.6;
- UMF `master` `24d3bf3c`, UMF core 0.7.0;
- one shared 4-vCPU VM.

The throughput figures are single-process measurements of spike code, not of
truss.

## Owner decisions (2026-10-03)

The owner accepted this ADR with the drafted recommendation for each open
question.

| # | Question | Decision |
|---|----------|----------|
| 1 | Which Node versions to support first? | Node 22 and later LTS lines (D1). Provisional until L1 runs the fidelity suite on Node 22 with `pg` |
| 2 | Separate packages, or one package with subpath exports? | Separate packages in one workspace: core, Bun adapter, `pg` adapter (D1), so D2's no-host-types rule is enforceable |
| 3 | Exact decimal arithmetic: truss implementation or pinned dependency? | A small truss implementation over `bigint`, checked against PostgreSQL `numeric` in conformance tests (D3); the core keeps no dependency other than UMF |
| 4 | Are the proposed T2 and T3 figures acceptable as PRD targets? | Yes, as proposed PRD targets; the PRD may revise them (D6) |
| 5 | Is expected SQL informative rather than normative in the corpus? | Yes, informative (D5) |
| 6 | Require L1–L3 before acceptance, or accept now? | Accept now. L1 confirms or amends Node support; L2 is the first build task; L3 sets the T2 baseline |
