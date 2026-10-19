---
title: "Claims you can inspect."
description: "Design intent, scoped experiments and unfinished gates are different kinds of evidence."
composition: model-primary
number: "03"
---
## Current candidate evidence

Truss `0.0.40` is an unpublished candidate for PostgreSQL `18.6`, UMF `0.10.0` source documents and fresh installations. It targets Linux x86_64 and macOS ARM64 and embeds V8 for Python deployment. The complete installed-package native and stress qualification is pending; this page does not claim full release qualification.

| Scope | Evidence | Boundary |
| --- | --- | --- |
| Current catalog planner and stored-value evolution | Source analysis plus 57 in-memory PGlite differential cases | Covers selected planner, evolution and SQL bookkeeping/length-boundary behavior; it does not establish PostgreSQL authority, trigger, concurrency or full-runtime behavior |
| Candidate workflows | Focused native controls and a real-schema workflow have been exercised against PostgreSQL 18.6 | The final installed-package gate and unchanged stress matrix are pending |
| Earlier storage and query prototypes | Earlier records include PostgreSQL 16.2 and 17.9 checks | They do not qualify this candidate or establish PostgreSQL 18.6 support |

Read the [current candidate notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.40.md), the [Python guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md), and the [operation cost ledger](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/03-test/performance/operation-statement-audit-20261019.md) for exact scope, bounds and pending gates. The [current documentation index](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/README.md) connects these results to the governed artifacts. [Weft iteration feedback](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/contracts/weft-integration-iteration-feedback.proposal.md) remains a separate historical experiment.

## What remains open

The full cross-platform installed-package gate, unchanged large stress matrix and final source-bound package qualification remain open. A passing in-memory data comparison is narrower than a native PostgreSQL control; focused native checks are narrower than the full release suite. No production-readiness claim is made.

## What the seal proves

Each page source carries an Innsigle signature and a model-primary authorship declaration. The build verifies the committed source before showing its colophon. That signature covers the Markdown source and inline diagram, not generated HTML, shared styling, product correctness or performance.

[Evaluate from the repository →](../start/)
