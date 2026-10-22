---
title: "Start with understanding."
description: "Inspect the repository, trace a claim and choose a bounded experiment."
composition: model-primary
number: "04"
---
## Read the direction

Begin with the [current documentation index](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/README.md), then read the [product vision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/00-discover/product-vision.md) and [requirements](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/01-frame/prd.md). These governed artifacts describe intent; the release notes and evidence describe what has actually been checked.

## Evaluate the Python release

Truss `0.0.48` publishes latest-tool-only offline migration for the admitted UMF `0.10` sources: v0.0.44, the shared v0.0.45/46 lineage, and v0.0.47 on PostgreSQL `18.6`. Admitted databases migrate forward without a release-age cutoff; previous application runtimes are not supported. The public 80-case migration, 62-case independent archive, selected driver checks and two-instance `uvx` restart receipts are [Linux 80-case migration receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/public-assets/migration-qualification.json), [macOS 80-case migration receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/mac-migration80/qualification.json), [Linux 62-case conformance receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/public-assets/hf-conformance-qualification.json), [macOS 62-case conformance receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/mac-independent62/qualification.json), [30-driver receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/mac-driver30/receipt.json) and [two-instance uvx receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/mac-uvx-two-instances/receipt.json). [public release validation](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/validation.json) binds the published assets and exact count (15). Pre-0.10/protected-profile migration, managed services, other drivers, broad discovery and general p95 certification remain outside this result. Python embeds V8 without an external JavaScript runtime.

Use the [Python operator guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md#runtime-migrations--v0048) for backup, migration, original-attempt recovery and limits. The [v0.0.48 release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.48.md), [public release](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.48) and [public release validation](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/validation.json) define the exact tuple and scope. Fresh installation requires a new namespace; existing admitted databases use explicit migration. Startup never upgrades or resets a database.

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
