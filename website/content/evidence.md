---
title: "Claims you can inspect."
description: "Design intent, scoped experiments and unfinished gates are different kinds of evidence."
composition: model-primary
number: "03"
---
## Published release evidence

Truss `0.0.47` restores explicit offline runtime migration from the exact populated UMF `0.10` v0.0.44 and shared v0.0.45/46 installations on PostgreSQL `18.6`. Only the latest application runtime is supported; admitted databases migrate forward without age-based expiry. The [Linux tag workflow](https://github.com/DocumentDrivenDX/truss/actions/runs/39702368076) passes selected installed-runtime checks, all 52 migration cases without skips and the original 1,000-object/1,000-edge public workload. [Public release verification](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/runtime-migrations-20261021/published-0.0.47/validation.json) checks all 12 checksummed assets, a fresh public-wheel 52-case run on macOS ARM64/Python 3.11.17, and the published `uvx` command with two independent instances retaining data across restart. [Release assets and pins](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.47) define the exact tuple. Pre-0.10 and protected-profile migration, managed-service support, broad discovery and performance certification remain outside this result. Python embeds V8 without an external JavaScript runtime.

| Scope | Evidence | Boundary |
| --- | --- | --- |
| Current v0.0.47 runtime migration | 52 installed cases without skips on Linux x86_64 and clean public-wheel macOS ARM64; full Linux tag gate and original small public workload pass | Exact unprotected PostgreSQL18.6/UMF0.10 source tuples and qualified initializer profiles; not pre-0.10 or protected-profile migration |
| Historical v0.0.46 local-runtime checks | Eight focused tests passed on macOS ARM64 and Linux x86_64; the published `uvx` command preserves two independent instances across restarts | Python 3.11.17/PostgreSQL 18.6; not broad discovery or performance certification |
| Historical v0.0.46 Linux installed workflows | [Release gate](https://github.com/DocumentDrivenDX/truss/actions/runs/39670547224) and [original small workload status](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/isolated-local-install-20261021/published-0.0.46/linux-public-workload-status.json) passed against the installed wheel | Selected workflows only; optional large-capacity and stress jobs were skipped |
| Historical v0.0.41 focused package checks | 11 cohort/originals controls and 9 current-query/disclosure runtime checks passed on macOS ARM64 with PostgreSQL 18.6 | Historical focused selectors; not a complete native suite or broad discovery pass |
| Historical v0.0.40 installed-package workflows | Three real schemas and all 11 unchanged stress cases passed locally on macOS ARM64 with PostgreSQL 18.6 | Reused unchanged from v0.0.40; not rerun for v0.0.41 and do not qualify Linux or larger workloads outside documented limits |
| Historical Linux x86_64 Weft package | The Weft 0.4.48 wheel archive, RECORD, metadata, ABI tag and notices were checked | Packaging evidence only; no Linux native semantics or Truss runtime behavior was tested |
| Retained catalog planner and stored-value evolution | Source analysis plus 57 in-memory PGlite differential cases retained from earlier evidence | Covers selected planner, evolution and SQL bookkeeping/length-boundary behavior; it does not establish PostgreSQL authority, trigger, concurrency or full-runtime behavior |
| Historical v0.0.40 native unittest selection | 95 existing selectors across 88 modules, covering 287 distinct latest method results | Retained v0.0.40 results only; not a full rerun on a later wheel |
| Historical broad native discovery | Raw receipt reports 1,927 tests across 295 of 313 modules; workers shut down | The discovery run is failed and incomplete; it is not a whole-suite pass |
| Earlier storage and query prototypes | Earlier records include PostgreSQL 16.2 and 17.9 checks | They do not qualify this release or establish PostgreSQL 18.6 support |

Read the [v0.0.47 release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.47.md), [Python operator guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md#runtime-migrations--v0047) and [release page](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.47). The [documentation index](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/README.md) connects the original receipts to governed requirements, contracts and test plans. Earlier release evidence retains its original scope.

## What remains open

The broad native discovery receipt remains incomplete, and performance budgets remain provisional. The v0.0.47 migration checks cover the exact source tuples on Linux x86_64 and macOS ARM64; the linked tag workflow defines the selected installed-engine scope. A future real native edge must add skip-release-chain proof. Large-database migration capacity and additional restore profiles require their own qualification. ABI 1.1 scans at most 10,000 rows per selected record or relationship type; complete-entity relationships are limited to 100 keys. The retained `large` stress workload's SQL list exceeds the ABI scan bound, so its v0.0.40 result does not qualify larger complete SQL lists. See the release notes for boundary controls and qualification limits.

## What the seal proves

Each page source carries an Innsigle signature and a model-primary authorship declaration. The build verifies the committed source before showing its colophon. That signature covers the Markdown source and inline diagram, not generated HTML, shared styling, product correctness or performance.

[Evaluate from the repository →](../start/)
