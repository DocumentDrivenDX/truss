---
title: "Start with understanding."
description: "Inspect the repository, trace a claim and choose a bounded experiment."
composition: model-primary
number: "04"
---
## Read the direction

Begin with the [current documentation index](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/README.md), then read the [product vision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/00-discover/product-vision.md) and [requirements](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/01-frame/prd.md). These governed artifacts describe intent; the release notes and evidence describe what has actually been checked.

## Evaluate the Python release

Truss `0.0.49` adds managed platform-grant policy and install API/CLI support to the v0.0.48 HF baseline. The published evidence covers native manifest SHA-256 prefix `288801f7`, four admitted migration sources (106 cases), the HF62 independent corpus, the managed 21-module/130-test gate, the public Weft 0.4.51 cohort from compiler source revision `55715373…`, and selected installed Linux/macOS qualification. The [v0.0.49 release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.49.md) and [published verification receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json) identify the exact artifacts and limits. Actual Lakebase acceptance remains a separate qualification.

Only the latest application runtime is supported. The latest tool provides offline, explicit transactional forward migration for the admitted UMF `0.10` sources: v0.0.44, the shared v0.0.45/46 lineage, v0.0.47 and v0.0.48 on PostgreSQL `18.6`. Admitted databases retain a forward route without a release-age cutoff. Startup never upgrades or resets a database.

Use the [Python operator guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md#runtime-migrations--v0049) for managed-grants configuration, backup, migration, original-attempt recovery and limits. The [v0.0.49 public release](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.49) provides checksum-verified assets. Fresh installation requires a new namespace; existing admitted databases use explicit migration. Startup never upgrades or resets a database. The historical [v0.0.48 release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.48.md) and [verification receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/validation.json) retain their original scope.

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
