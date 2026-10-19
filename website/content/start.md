---
title: "Start with understanding."
description: "Inspect the repository, trace a claim and choose a bounded experiment."
composition: model-primary
number: "04"
---
## Read the direction

Begin with the [current documentation index](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/README.md), then read the [product vision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/00-discover/product-vision.md) and [requirements](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/01-frame/prd.md). These governed artifacts describe intent; the candidate notes and evidence describe what has actually been checked.

## Evaluate the Python candidate

The current Truss `0.0.40` candidate targets PostgreSQL `18.6` on Linux x86_64 and macOS ARM64, with UMF `0.10.0` source documents and fresh installations only. Python deployment embeds V8; it does not require Bun, Node or an external JavaScript process. Full installed-package and stress qualification is still pending.

Use the [Python guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md#install-the-current-candidate) for the candidate install and workflow, and read the [candidate notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.40.md) and [operation cost ledger](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/03-test/performance/operation-statement-audit-20261019.md) before interpreting scope. The candidate requires an empty/new database namespace. It does not migrate an older installation.

```sh
git clone https://github.com/DocumentDrivenDX/truss.git
cd truss
```

The repository clone is for source inspection and development. Development checks may need Bun, a compiler and PostgreSQL; those tools are not runtime prerequisites for Python deployment.

## Follow a requirement to evidence

1. Find the intended behavior in the PRD or feature specifications.
2. Read its architecture decision and contract.
3. Check the implementation plan for open dependencies.
4. Read the source-pinned evidence and its exclusions.

## Contribute a concrete question

Useful contributions identify a schema-evolution case, an enforcement boundary or a reproducible integration result. Include the database version, source revision and observed behavior. Truss is licensed under MIT or Apache-2.0, at your option.

[Open the repository ↗](https://github.com/DocumentDrivenDX/truss)
