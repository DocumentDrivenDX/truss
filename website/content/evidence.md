---
title: "Claims you can inspect."
description: "Design intent, scoped experiments and unfinished gates are different kinds of evidence."
composition: model-primary
number: "03"
---
## Published release evidence

Truss `0.0.46` adds a one-shot local PostgreSQL `18.6` runtime for fresh fixtures, alongside the Python embedding library. The available local evidence uses macOS ARM64, Python `3.11.17` and PostgreSQL `18.6`; eight focused lifecycle, isolation and CLI tests passed, followed by a clean `uvx` install and same-identity status confirmation. This evidence qualifies the local runtime path, not the full engine. The [v0.0.46 release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.46.md) and [published release assets and pins](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.46) define the package cohort. The hosted release workflow defines any additional platform qualification. Broad discovery, managed-service support and performance certification remain unfinished. Python embeds V8 and does not require Bun, Node or an external JavaScript process.

| Scope | Evidence | Boundary |
| --- | --- | --- |
| Current v0.0.46 local-runtime checks | Eight focused lifecycle, isolation and CLI tests passed on macOS ARM64 with Python 3.11.17 and PostgreSQL 18.6; a clean `uvx` install and same-identity status confirmation also passed | Qualifies this local runtime path only; not full engine qualification or broad discovery |
| Historical v0.0.41 focused package checks | 11 cohort/originals controls and 9 current-query/disclosure runtime checks passed on macOS ARM64 with PostgreSQL 18.6 | Historical focused selectors; not a complete native suite or broad discovery pass |
| Historical v0.0.40 installed-package workflows | Three real schemas and all 11 unchanged stress cases passed locally on macOS ARM64 with PostgreSQL 18.6 | Reused unchanged from v0.0.40; not rerun for v0.0.41 and do not qualify Linux or larger workloads outside documented limits |
| Historical Linux x86_64 Weft package | The Weft 0.4.48 wheel archive, RECORD, metadata, ABI tag and notices were checked | Packaging evidence only; no Linux native semantics or Truss runtime behavior was tested |
| Current catalog planner and stored-value evolution | Source analysis plus 57 in-memory PGlite differential cases retained from earlier evidence | Covers selected planner, evolution and SQL bookkeeping/length-boundary behavior; it does not establish PostgreSQL authority, trigger, concurrency or full-runtime behavior |
| Historical v0.0.40 native unittest selection | 95 existing selectors across 88 modules, covering 287 distinct latest method results | Retained v0.0.40 results only; not a full rerun on a later wheel |
| Historical broad native discovery | Raw receipt reports 1,927 tests across 295 of 313 modules; workers shut down | The discovery run is failed and incomplete; it is not a whole-suite pass |
| Earlier storage and query prototypes | Earlier records include PostgreSQL 16.2 and 17.9 checks | They do not qualify this release or establish PostgreSQL 18.6 support |

Read the [v0.0.46 release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.46.md), the [Python guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md) and the [v0.0.46 release page](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.46), which lists the release assets and pins. The [operation cost ledger](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/03-test/performance/operation-statement-audit-20261019.md) documents bounds outside this local-runtime change. The [current documentation index](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/README.md) connects these results to the governed artifacts. [Weft iteration feedback](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/contracts/weft-integration-iteration-feedback.proposal.md) remains a separate historical experiment.

## What remains open

The broad native discovery receipt remains incomplete, and performance budgets remain provisional. The v0.0.46 local-runtime evidence is limited to macOS ARM64; any additional platform qualification is defined by the hosted release workflow and release assets. ABI 1.1 scans at most 10,000 rows per selected record or relationship type; complete-entity relationships are limited to 100 keys. The retained `large` stress workload's SQL list exceeds the ABI scan bound, so its v0.0.40 result does not qualify larger complete SQL lists. See the release notes for boundary controls and qualification limits.

## What the seal proves

Each page source carries an Innsigle signature and a model-primary authorship declaration. The build verifies the committed source before showing its colophon. That signature covers the Markdown source and inline diagram, not generated HTML, shared styling, product correctness or performance.

[Evaluate from the repository →](../start/)
