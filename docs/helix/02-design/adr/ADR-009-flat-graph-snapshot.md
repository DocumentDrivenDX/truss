---
ddx:
  id: ADR-009
  type: adr
  activity: design
  status: withdrawn
  authoring:
    home: repo
  links:
    - id: ADR-001
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: ADR-006
      kind: informed_by
    - id: ADR-008
      kind: informed_by
    - id: FEAT-005
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
---

# ADR-009: Publish a graph as a read-only flat snapshot for in-browser reads

| Date | Status | Deciders | Related | Confidence |
| --- | --- | --- | --- | --- |
| 2026-11-06 | Withdrawn 2026-11-08 | Product owner | ADR-001, ADR-002, ADR-006, FEAT-005 | Medium; format unmeasured |

## Withdrawal (2026-11-08)

Withdrawn before acceptance. The driving consumer, the Atlas document graph, is
served by the Arras `arras.graph` v1 JSON file and Arras's static, read-only
client-side backend (Arras 0.8.0, ADR-031 and CONTRACT-012 in the Arras repository).
At Atlas's scale (under 1,000 nodes of under 8 KB, hubs up to 1,000 edges) the JSON
bundle needs no binary snapshot. No measurement showed JSON load cost to matter, and
SPIKE-004 was never run. The binary layout and its contract proposal are not kept in
this repository; the design below is retained only as a record of the alternative.

Reopen only if a dataset outgrows a JSON graph file and measured load cost matters.
Any such encoding must carry `arras.graph` semantics and be proposed through Arras,
not as a parallel Truss-only format.

## Problem

Truss has one storage home: PostgreSQL. The only browser path is the
non-distributable PGlite prototype (`packages/browser`), which ships a database
engine to serve what is often a read-only view of published data. A consumer who
wants to publish a graph (a catalog revision plus its objects and edges) and let a
browser read it must today run a server or load a database engine. Neither starts
fast or scales to a static host.

## Driving use case — Atlas document graph (2026-11-06)

Atlas will publish a document graph (documents as nodes, typed links as edges),
and users must walk it through a UI. This is the first consumer and shapes the
requirements below: interactive expansion of a node's neighbourhood in both
directions (links and backlinks), bounded fan-out with paging so a hub node cannot
stall the UI, document bodies that load lazily rather than with the graph,
type/facet filtering, and title/key search. Stable ids and deep-linkable
node/edge references are required so a UI route can name a node.

**Findings from the Atlas repository (2026-11-06) and owner figures.** Atlas is a
HELIX `technology-atlas` flow, not a UMF/Truss-stored graph: nodes are Markdown
files with `ddx` frontmatter (six types), edges are `ddx.links` of four kinds
(`addresses`, `evaluates`, `supported_by`, `contradicts`) with pinned `rev`s and
cross-graph targets. Today 11 documents of about 13 KB; owner expects under 1,000
nodes of under 8 KB, hubs of low hundreds of edges (never over 1,000), weekly
republication, public audience. Its `build-site.py` already emits `graph.json`
and static pages; search and graph browse are planned. The whole graph is
therefore at most about 8 MB uncompressed and about 2 MB gzipped, and **Atlas does
not need a binary snapshot**: a JSON bundle parses in milliseconds at that size,
and exactness concerns do not arise (no stored numbers). Atlas is a poor driver
for this ADR; keep ADR-009 for datasets that outgrow a JSON bundle, and do not
accept it on Atlas's account. No .NET example was found in the Atlas repository.

## Update — 2026-11-06: an existing flat file and UI layer was found

Arras (`/Users/erik/Projects/arras`) already defines `arras.graph` v1, a deterministic
JSON graph file that round-trips through `export_records`/`import_records`, loads into
its in-memory adapter or Truss, and is read by its React Graph Browser. That answers the
original question (an in-memory and flat-file graph exists in the family) and covers the
Atlas use case. **Do not accept this ADR on the strength of Atlas or any dataset that
fits a JSON graph file.** Keep it only as a candidate for a future zero-copy binary
encoding of the graph file if the JSON file's load cost is shown to matter; any such
format must carry `arras.graph` semantics and be proposed through Arras, not as a
parallel Truss-only format. Status remains proposed and should likely be withdrawn.

## Decision

Define a **Truss Graph Snapshot** (TGS): one immutable binary file holding one
catalog revision and the objects and edges committed at one journal position.
A browser reads it in place, without a database engine and without a parse
pass.

1. **Read-only.** A snapshot is published, never mutated. Writes, locks, the
   journal and enforcement stay in PostgreSQL. Updates are a new snapshot;
   a later delta segment keyed to the change feed (FR-52) is a possible
   follow-up, not part of this decision.
2. **Zero-copy layout.** Fixed little-endian header and section table; every
   section 8-byte aligned so the reader takes `Uint32Array`/`BigInt64Array`
   views over the fetched `ArrayBuffer`. Cost to open is header and section
   table validation, not data size.
3. **Columnar objects, CSR edges.** Objects are densely ordinal-numbered in
   `(type_id, id)` order. Each declared property is a presence bitmap plus a
   typed column. Each relationship is stored as compressed-sparse-row in both
   directions, with edge properties in parallel columns. Sorted key and declared
   property indexes give binary search. Indexes exist only where the binding
   declares them (ADR-002).
4. **Exactness preserved.** ADR-006 and CONTRACT-010 apply unchanged. Integers
   and decimals are never stored as binary64 unless the declared domain is float.
   Original exact tokens are retained wherever the spelling differs from the
   canonical form. The reader returns exact tokens by default.
5. **Self-describing and honest.** The snapshot embeds the original UMF source
   bytes verbatim, the catalog revision identity, source hashes, the acceptance
   receipt hash, the journal position, and the enforcement report. Retained
   (unbound) data travels with each object. The snapshot states that it enforces
   nothing; it reports what the source database enforced at export.
6. **Verifiable.** Per-section SHA-256 and a whole-file digest sit in the footer.
   Integrity is checked once at load (or lazily per section with range reads).
7. **Portable core.** The reader is a pure TypeScript package over `Uint8Array`
   with no I/O and no `node:*`/`bun` imports (ADR-001). Fetching, range requests
   and caching belong to the host. The writer is a tooling package that exports
   from one repeatable-read PostgreSQL snapshot.
8. **Query scope is the direct read surface.** Point read by id or key, keyset
   list, bounded edge list, one-to-three-hop traversal, and catalog
   enumeration (FEAT-005 RD-01 to RD-05). The Weft SQL surface (RD-06) is
   **not** provided by a snapshot; a consumer needing SQL loads a database
   engine instead.

The byte layout, error behavior and compatibility rules were drafted as a contract
proposal, which was dropped with this withdrawal.

## Why We Chose This

### Over shipping PGlite (or SQLite WASM) with a dump
Full SQL and enforcement, but a multi-megabyte WASM engine, load/import time
proportional to data size and memory well above file size. Right when a browser
needs writes or arbitrary SQL; wasteful for published read-only data.

### Over JSON or JSONL
Simple and universally readable, but parse cost is proportional to size,
numbers lose exactness through `JSON.parse`, and traversal needs a second index
built at load.

### Over Apache Arrow IPC or Parquet as the whole format
Arrow IPC is columnar, zero-copy and has decimal128 and dictionaries, so it is a
serious candidate for the column encoding. It has no graph adjacency, no key
index and no catalog binding, so those would be Truss conventions layered on top
anyway. Parquet needs a WASM reader and decompression. This ADR is accepted only
after a spike compares a thin custom container against Arrow IPC (see Validation);
the property and edge semantics above hold in either case.

### Over a purpose-built graph engine in WASM
Highest read power, a second engine to qualify, and it would compete with the
Weft and PostgreSQL path (ADR-003) rather than consume it.

## Consequences

**Good**: Static hosting (CDN, object store); open cost independent of data
size; memory near file size; graph reads in microseconds; every snapshot is
traceable to a catalog revision and journal position; no new semantic authority
(UMF meaning stays upstream).

**Trade-offs**: Read-only; no SQL; the whole snapshot is exposed to anyone who
can fetch it (no per-row authorization inside the file); a second reader
implementation to qualify against the conformance corpus; format versioning
becomes a Truss compatibility surface.

**Drift signals to watch**: A mutation API on the reader; stored `number` for
exact types; reader code importing host I/O; a snapshot field that restates UMF
semantics rather than referencing the embedded source; support claims without
engine, UMF version and evidence.

## Assumptions

- Target datasets fit in browser memory (working figure: up to a few hundred MB;
  to be measured). Larger ones need the range-addressed mode, which is provisional.
- `DecompressionStream` (gzip/deflate) is available in supported browsers; brotli
  and zstd are transport-level only. Wrong if a target browser lacks it.
- One export position is sufficient; consumers do not need history. Wrong if
  as-of reads are required (would need journal-derived segments).

## Validation

**Result**: not tested
**Evidence**: planned SPIKE-004. Build the writer for a real catalog from the
existing conformance corpus; compare custom container vs Arrow IPC on: open time,
point and key lookup, one- and three-hop traversal, memory vs file size, gzip size,
and exactness round-trip on signed-64 and decimal edge cases. Proposed targets,
unmeasured: open under 50 ms at 1M objects; id lookup under 10 µs; key lookup
under 50 µs; one-hop under 20 µs; resident memory within 1.5× file size.

## Concern Impact

- No override of a selected concern. Extends ADR-001's portable-core rule to a
  second storage-neutral package.
