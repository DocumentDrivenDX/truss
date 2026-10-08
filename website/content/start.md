---
title: "Start with understanding."
description: "Inspect the repository, trace a claim and choose a bounded experiment."
composition: model-primary
number: "04"
---
## Read the direction

Begin with the [documentation index](https://github.com/DocumentDrivenDX/truss/blob/5cff55183c0c7aad647c49611c2110ce1cdecca8/docs/helix/README.md), then the [product vision](https://github.com/DocumentDrivenDX/truss/blob/5cff55183c0c7aad647c49611c2110ce1cdecca8/docs/helix/00-discover/product-vision.md) and [requirements](https://github.com/DocumentDrivenDX/truss/blob/5cff55183c0c7aad647c49611c2110ce1cdecca8/docs/helix/01-frame/prd.md). Draft status matters: these describe the target, not a released product.

## Inspect the experiments

The experimental query integration lives in `packages/weft`, with its pinned compiler adapter in `packages/weft-bun`. Read the package documentation and [iteration feedback](https://github.com/DocumentDrivenDX/truss/blob/5cff55183c0c7aad647c49611c2110ce1cdecca8/docs/helix/02-design/contracts/weft-integration-iteration-feedback.proposal.md) before reproducing it. Check prerequisites and exact source pins in the repository. There is no production installation quickstart here.

```sh
git clone https://github.com/DocumentDrivenDX/truss.git
cd truss
```

The clone is the starting point for inspection. Running fixtures requires the documented Bun, compiler and database prerequisites; cloning alone does not install or qualify the runtime.

## Follow a requirement to evidence

1. Find the intended behavior in the PRD or feature specifications.
2. Read its architecture decision and contract.
3. Check the implementation plan for open dependencies.
4. Read the source-pinned evidence and its exclusions.

## Contribute a concrete question

Useful contributions identify a schema-evolution case, an enforcement boundary or a reproducible integration result. Include the database version, source revision and observed behavior. Truss is licensed under Apache 2.0.

[Open the repository ↗](https://github.com/DocumentDrivenDX/truss)
