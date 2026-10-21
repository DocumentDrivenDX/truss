---
title: "Start with understanding."
description: "Inspect the repository, trace a claim and choose a bounded experiment."
composition: model-primary
number: "04"
---
## Read the direction

Begin with the [current documentation index](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/README.md), then read the [product vision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/00-discover/product-vision.md) and [requirements](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/01-frame/prd.md). These governed artifacts describe intent; the release notes and evidence describe what has actually been checked.

## Evaluate the Python release

Truss `0.0.46` provides a private PostgreSQL `18.6` launcher alongside the Python embedding library. Eight focused lifecycle, isolation and CLI tests pass on macOS ARM64 and Linux x86_64 with Python `3.11.17`. The [published-package receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/isolated-local-install-20261021/published-0.0.46/receipt.json) verifies the quickstart outside the checkout: two simultaneous instances retain separate data and installation identities across restarts. The [Linux release gate](https://github.com/DocumentDrivenDX/truss/actions/runs/39670547224) also passes selected installed-engine workflows and the original small public workload. [Release assets and pins](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.46) define the package cohort. Broad discovery, managed-service support and performance certification remain unfinished. Python embeds V8 without requiring Bun, Node or an external JavaScript process.

Use the [Python guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md) for installation and workflow details. The [v0.0.46 release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.46.md), [published release and pins](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.46), [local validation record](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/isolated-local-install-20261021/validation.json) and [Python 3.11 receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/isolated-local-install-20261021/python311/receipt.json) define the exact scope. Truss requires a fresh database namespace; it does not migrate an older installation.

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
