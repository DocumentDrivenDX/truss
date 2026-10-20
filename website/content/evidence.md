---
title: "Claims you can inspect."
description: "Design intent, scoped experiments and unfinished gates are different kinds of evidence."
composition: model-primary
number: "03"
---
## Published release evidence

Truss `0.0.41` is published for fresh installations using UMF `0.10.0` source documents. Its current focused installed-package checks are qualified locally on macOS ARM64 with PostgreSQL `18.6`; Python embeds V8 and needs no Bun, Node or external JavaScript process. The three real schemas and 11 stress cases are retained from `0.0.40` evidence without rerunning them; their SQL and bundled runtime payloads are unchanged. Linux x86_64 Weft `0.4.48` has packaging checks only. No Linux functional or full-suite claim is made.

| Scope | Evidence | Boundary |
| --- | --- | --- |
| Current v0.0.41 focused package checks | 11 cohort/originals controls and 9 current-query/disclosure runtime checks pass on macOS ARM64 with PostgreSQL 18.6 | Focused selectors only; this is not a complete native suite or broad discovery pass |
| Retained v0.0.40 installed-package workflows | Three real schemas and all 11 unchanged stress cases passed locally on macOS ARM64 with PostgreSQL 18.6 | Reused unchanged from v0.0.40; not rerun for v0.0.41 and do not qualify Linux or larger workloads outside documented limits |
| Linux x86_64 Weft package | The Weft 0.4.48 wheel archive, RECORD, metadata, ABI tag and notices were checked | Packaging evidence only; no Linux native semantics or Truss runtime behavior was tested |
| Current catalog planner and stored-value evolution | Source analysis plus 57 in-memory PGlite differential cases retained from earlier evidence | Covers selected planner, evolution and SQL bookkeeping/length-boundary behavior; it does not establish PostgreSQL authority, trigger, concurrency or full-runtime behavior |
| Historical v0.0.40 native unittest selection | 95 existing selectors across 88 modules, covering 287 distinct latest method results | Retained v0.0.40 results only; not a full rerun on the v0.0.41 wheel |
| Historical broad native discovery | Raw receipt reports 1,927 tests across 295 of 313 modules; workers shut down | The discovery run is failed and incomplete; it is not a whole-suite pass |
| Earlier storage and query prototypes | Earlier records include PostgreSQL 16.2 and 17.9 checks | They do not qualify this release or establish PostgreSQL 18.6 support |

Read the [release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.41.md), the [Python guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md#install-version-0041), and the [operation cost ledger](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/03-test/performance/operation-statement-audit-20261019.md) for exact scope and bounds. The published [qualification summary](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.41/qualification.json) accompanies the release. The [current documentation index](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/README.md) connects these results to the governed artifacts. [Weft iteration feedback](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/contracts/weft-integration-iteration-feedback.proposal.md) remains a separate historical experiment.

## What remains open

The broad native discovery receipt remains incomplete, and performance budgets remain provisional. Linux native functionality remains unqualified. ABI 1.1 scans at most 10,000 rows per selected record or relationship type; complete-entity relationships are limited to 100 keys. The retained `large` stress workload's SQL list exceeds the ABI scan bound, so its v0.0.40 result does not qualify larger complete SQL lists. See the release notes for the complete boundary controls and qualification limits.

## What the seal proves

Each page source carries an Innsigle signature and a model-primary authorship declaration. The build verifies the committed source before showing its colophon. That signature covers the Markdown source and inline diagram, not generated HTML, shared styling, product correctness or performance.

[Evaluate from the repository →](../start/)
