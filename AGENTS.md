# Working in truss

Truss is an embeddable, property-oriented graph store on PostgreSQL whose types come from
UMF documents. The shipped product is the Python package `umf-truss` (`packages/python`).

## Build and test
- `bun install --frozen-lockfile && bun run typecheck && bun test`
- `python -m build packages/python`
- `pip install "dist/*.whl[local,native,query]" pytest pytest-xdist`, then
  `cd packages/python/tests && pytest -n 4 -m "not slow"`
- `python packages/python/examples/quickstart.py /tmp/truss-demo` must keep working.
- CI (`.github/workflows/ci.yml`) runs the same on Linux. Run native checks only on your own
  platform. Never start PostgreSQL on TCP; `LocalPostgres` uses a private Unix socket.

## Supported database
PostgreSQL 18.6 only: `pgserver-pg18` for local use (the wheels are public GitHub release assets at
`https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2`; pass them
with `--find-links` until they are on PyPI) or a host-supplied connection. The host owns any pool.

## Decisions in force
- ADR-001: TypeScript (strict ESM, Bun) for the portable core, which has no I/O and no host globals;
  database adapters are separate packages. Never hold stored integers, decimals or timestamps in a
  JS `number`/`Date`; adapters return text that the core parses exactly.
- ADR-003 (amends ADR-001's Python restriction): the tested Python 3.11+ implementation is the shipped
  engine. Consume Weft's Python bridge for query compilation; do not reimplement Weft or UMF semantics.
- ADR-002: generic catalog storage. Adding a type, property, key or relationship adds catalog rows,
  never columns, tables, partitions or per-type indexes. Objects are one table keyed on
  `(id, type_id)`; business identity (UMF keys) is in `object_key`; values are one JSONB map per object
  keyed by property id (missing = absent, JSON null = explicit null); unknown data goes in `retained`.
  Edges have typed endpoints. The object row is canonical; the journal records per-property history
  in the same transaction. No per-type DDL or CHECK constraints; cross-row rules lock the parent
  (`FOR NO KEY UPDATE`) or run SERIALIZABLE.
- ADR-004 to ADR-008: document-qualified catalog identity, complete group receipts, exact numeric
  carriers, complete historical envelopes, trusted embedding host.

## Boundaries
- Truss consumes UMF and never defines UMF semantics; carry missing concepts in a truss-owned UMF
  extension vocabulary and propose them upstream. UMF owns metadata semantics and SQL generation,
  Weft owns logical SQL lowering, Truss owns their composition.
- Truss is property-oriented: the property value and edge are the unit of storage and mutation;
  document-shaped views are derived. It is not part of Axon.
- Never silently lose meaning: keep UMF documents verbatim, retain data that binds to no known field,
  and report for each UMF assertion whether the database, the engine or nothing enforces it.

## Rules
- Do not commit run outputs, logs, wheels, zips or captures. `scripts/size-guard.sh` fails on tracked
  files over 1 MB.
- A support claim in README or docs needs a CI test that exercises it; otherwise call it experimental.
- Releases: bump `packages/python/pyproject.toml`, add a CHANGELOG section, tag `vX.Y.Z` on main;
  `release.yml` does the rest.
- Design docs are in `docs/helix/` (PRD, features, ADRs, architecture, contracts). Update the ADR or
  contract when behaviour changes.
