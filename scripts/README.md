# scripts

Developer tools, not part of CI. The `build-*`, `compose-*`, `project-*`, `export-*` and `extract-*`
generators write SQL and assets into `packages/` from UMF models; the TypeScript ones import UMF from a
checkout next to this repository (`../umf`). `regenerate-migration-baseline.py` rewrites
`packages/python/src/truss/_migrations` after any change to `_catalog_runtime/manifest.json`.
`size-guard.sh`, `check-module-boundaries*.py` and `run-hf-conformance.py` run in CI.
