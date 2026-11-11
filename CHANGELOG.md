# Changelog

Versions of the Python package `umf-truss`. Detailed per-release notes before 0.0.56 are in git history
(`docs/helix/05-deploy/releases/`, tag `v0.0.55` and earlier). Releases up to 0.0.50 were also published
as `truss-toolkit`, which is retired.

## 0.0.56 (unreleased)

- Query: Weft relationship and scalar queries work again. The 0.76 runtime release id was
  `truss-catalog-runtime/0.76-temporal-candidate`, which umf-weft 0.4.57 refuses ("Selected runtime
  context or limits refused"); it is now `truss-catalog-runtime/0.76-candidate`.
- Temporal values (date, instant and local timestamps) and bulk job control are included and are
  experimental.
- Supported database: PostgreSQL 18.6 (`pgserver-pg18` for local use). The `truss-migrate` baseline was
  regenerated for this runtime; databases from earlier Truss versions are not migrated.
- Release process: tag-driven `release.yml` publishes `umf-truss` to PyPI with trusted publishing; CI runs
  the Python test suite and the README quickstart on Linux. Committed run evidence, receipts and the
  security prototype were removed from the repository.

## 0.0.55

Optional `operation_timeout_ms` on `CatalogReferenceAssembly.install_in_transaction`, up to 180 s, for slow
fresh installations. Default behaviour is unchanged.

## 0.0.54

Adds the standalone `LocalTimestampValue` carrier. Temporal storage and queries were not yet available.

## 0.0.53

Fresh-install baseline dated 2026-11-02 on the source-custody runtime from 0.0.52. Predecessor migration
routes and historical receipt recovery were retired.

## 0.0.52

Feed source custody handle and a native 0.74 to 0.75 migration edge (superseded by 0.0.53).

## 0.0.51

First release under the `umf-truss` distribution name; same execution, owner and compiler cohort as 0.0.50.

## 0.0.50

Fewer synchronous database submissions during fresh installation; PostgreSQL 18.6, psycopg 3.3.6, UMF 0.10,
Weft 0.4.51.

## 0.0.44 to 0.0.49

Python embedder delivery for the Hohfeld feedback (0.0.44 to 0.0.45), explicit local PostgreSQL launcher
(0.0.46), forward runtime migration (0.0.47), query ABI 1.2 with native-indexed exact equality (0.0.48) and
managed platform grants (0.0.49).

## 0.0.1 to 0.0.43

Initial development: catalog registration, typed object and edge mutation, receipts, key lookup, pages,
history, imports and committed feeds.
