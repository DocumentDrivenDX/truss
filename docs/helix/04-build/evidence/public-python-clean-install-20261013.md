# Public Python clean install — 2026-10-13

The corrected quickstart succeeds in a fresh CPython3.12.14 virtual environment
on macOS arm64. The owner pg18.6-pgv0.8.6-r2 GitHub release supplies
pgserver-pg18==18.6.1 through its expanded-assets listing; a package-index-only
install fails because that distribution is not on the configured index.
`pip --find-links` selects the actual matching CPython/platform wheel.

The new runtime build helper archives committed Weft
cb10d8e6fbf60c43c0daa0c2e7422375fd1e13e5 and uses maturin1.9.6 from the caller's
Python environment, targeting the same interpreter with the normal
truss-postgresql-pg18 feature. Rust1.90.0 builds its release wheel successfully
with cached dependencies (--offline). The initial helper prototype incorrectly
used python -m maturin; maturin supplies an executable instead. The corrected
helper uses the caller environment's scripts directory. No repository files
are substituted into the committed archive.

After force-reinstalling that wheel and installing Truss[local,native] with the
owner release listing, the actual adopter_workflow.py finishes: accepted catalog,
committed mutation, committed replay, included receipt, relationship query,
rolled-back dry-run, created import, three feed transactions and committed ACK.
This is one practical clean install and public workflow, not a new conformance,
performance or interchange inventory. Historical build/preview artifacts keep
their original profiles. Astra reviewed the plan; source review precedes commit.
