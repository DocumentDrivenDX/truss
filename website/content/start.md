---
title: "Start with understanding."
description: "Inspect the repository, trace a claim and choose a bounded experiment."
composition: model-primary
number: "04"
---
## Read the direction

Begin with the [current documentation index](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/README.md), then read the [product vision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/00-discover/product-vision.md) and [requirements](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/01-frame/prd.md). These governed artifacts describe intent; the release notes and evidence describe what has actually been checked.

## Evaluate the Python release

Truss `0.0.41` is published for fresh PostgreSQL `18.6` installations using UMF `0.10.0` source documents. Focused installed-package qualification on macOS ARM64 passed 11 cohort controls and 9 current-query/disclosure runtime checks. The three real schemas and 11 stress cases are retained from `0.0.40` evidence and were not rerun. Linux x86_64 Weft `0.4.48` has packaging verification only; this release makes no Linux functional or full-suite claim. Python deployment embeds V8 and does not require Bun, Node or an external JavaScript process.

Use the [Python guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md#install-version-0041) for installation and workflow details. The [release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.41.md) and [qualification summary](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.41/qualification.json) define the exact evidence and limits. Truss requires an empty/new database namespace; it does not migrate an older installation.

```sh
git clone https://github.com/DocumentDrivenDX/truss.git
cd truss
```

The repository clone is for source inspection and development. Development checks may need Bun, a compiler and PostgreSQL; those tools are not runtime prerequisites for Python deployment. The release is available from [GitHub v0.0.41](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.41), with its [qualification summary](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.41/qualification.json).

## Follow a requirement to evidence

1. Find the intended behavior in the PRD or feature specifications.
2. Read its architecture decision and contract.
3. Check the implementation plan for open dependencies.
4. Read the source-pinned evidence and its exclusions.

## Contribute a concrete question

Useful contributions identify a schema-evolution case, an enforcement boundary or a reproducible integration result. Include the database version, source revision and observed behavior. Truss is licensed under MIT or Apache-2.0, at your option.

[Open the repository ↗](https://github.com/DocumentDrivenDX/truss)
