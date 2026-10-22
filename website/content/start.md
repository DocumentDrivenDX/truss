---
title: "Start with understanding."
description: "Inspect the repository, trace a claim and choose a bounded experiment."
composition: model-primary
number: "04"
---
## Read the direction

Begin with the [current documentation index](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/README.md), then read the [product vision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/00-discover/product-vision.md) and [requirements](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/01-frame/prd.md). These governed artifacts describe intent; the release notes and evidence describe what has actually been checked.

## Evaluate the Python release

Truss `0.0.47` restores explicit offline runtime migration from the exact populated UMF `0.10` v0.0.44 and shared v0.0.45/46 installations on PostgreSQL `18.6`. Only the latest application runtime is supported; admitted databases migrate forward without age-based expiry. The [Linux tag workflow](https://github.com/DocumentDrivenDX/truss/actions/runs/39702368076) passes selected installed-runtime checks, all 52 migration cases without skips and the original 1,000-object/1,000-edge public workload. [Public release verification](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/runtime-migrations-20261021/published-0.0.47/validation.json) checks all 12 checksummed assets, a fresh public-wheel 52-case run on macOS ARM64/Python 3.11.17, and the published `uvx` command with two independent instances retaining data across restart. [Release assets and pins](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.47) define the exact tuple. Pre-0.10 and protected-profile migration, managed-service support, broad discovery and performance certification remain outside this result. Python embeds V8 without an external JavaScript runtime.

Use the [Python operator guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md#runtime-migrations--v0047) for backup, migration, original-attempt recovery and limits. The [v0.0.47 release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.47.md), [public release](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.47) and [verification record](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/runtime-migrations-20261021/published-0.0.47/validation.json) define the exact scope. Fresh installation requires a new namespace; existing admitted databases use explicit migration. Startup never upgrades or resets a database.

```sh
git clone https://github.com/DocumentDrivenDX/truss.git
cd truss
```

The repository clone below is for source inspection and development; the published package quickstart above does not require a clone. Development checks may need Bun, a compiler and PostgreSQL; those tools are not runtime prerequisites for Python deployment.

## Follow a requirement to evidence

1. Find the intended behavior in the PRD or feature specifications.
2. Read its architecture decision and contract.
3. Check the implementation plan for open dependencies.
4. Read the source-pinned evidence and its exclusions.

## Contribute a concrete question

Useful contributions identify a schema-evolution case, an enforcement boundary or a reproducible integration result. Include the database version, source revision and observed behavior. Truss is licensed under MIT or Apache-2.0, at your option.

[Open the repository ↗](https://github.com/DocumentDrivenDX/truss)
