# Truss

Truss is an embeddable, property-oriented graph store on PostgreSQL. Types, properties, keys and
relationships come from [UMF](https://github.com/DocumentDrivenDX/umf) documents and are stored as
catalog rows in one generic schema, so adding a type never adds a table, column or index. Values and
edges have per-property history in a journal, and committed changes are readable through an
acknowledged change feed. Queries are SQL-like text compiled by [Weft](https://github.com/DocumentDrivenDX/weft).

**Status: experimental.** PostgreSQL 18.6 only, Python 3.11 or newer, Linux and macOS (CI tests Linux).
The Python package `umf-truss` (import name `truss`) is the product. Version: see
[CHANGELOG](CHANGELOG.md).

## Install

```sh
python -m venv .venv && . .venv/bin/activate
pip install "umf-truss[local,native,query]" \
  --find-links https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2
```

- `local`: `pgserver-pg18` (PostgreSQL 18.6) so `truss.LocalPostgres` can start a private server on a
  Unix socket. The wheels are GitHub release assets for now, hence `--find-links`; the line goes away when
  they are on PyPI. Without `local`, connect to your own PostgreSQL 18.6.
- `native`: `psycopg`, the supported driver. `query`: `umf-weft`, for relationship queries.
- Python embeds V8 (`mini-racer`); Bun and Node are not needed to run Truss.

## Quickstart (about five minutes)

`packages/python/examples/quickstart.py` starts a private PostgreSQL in a directory you name, installs
Truss, registers a UMF document, creates two notes and an edge in one atomic group, looks a note up by
key, runs a relationship query, and reads and acknowledges the committed change feed. CI runs it on every
change against the built wheel in a fresh virtual environment.

```sh
curl -LO https://raw.githubusercontent.com/DocumentDrivenDX/truss/main/packages/python/examples/quickstart.py
curl -LO https://raw.githubusercontent.com/DocumentDrivenDX/truss/main/packages/python/examples/notes.umf.json
python quickstart.py ./truss-demo
# {"catalog": "accepted", "mutation": "committed", "lookup": "found", "query": "relationship", "feed_transactions": 1, "ack": "committed"}
```

The first run starts PostgreSQL (`initdb`), which takes a minute on a slow disk. Set
`TRUSS_LOCAL_TIMEOUT_S` to allow longer. If a run is killed, stop the leftover server with
`pg_ctl -D ./truss-demo/postgres/data stop` (the `pg_ctl` inside the `pgserver` package). See
[`packages/python/README.md`](packages/python/README.md) for the API, and
[`adopter_workflow.py`](packages/python/examples/adopter_workflow.py) for receipts, replay, imports and dry runs.

## Experimental

Temporal values, bulk job control, the `typed-sdk` extra (`truss.access`, needs umf-access 0.10.11, not yet
published) and `experimental-pg8000` are experimental and are not part of the quickstart.

## Documentation

[Architecture](docs/helix/02-design/architecture.md), [decisions](docs/helix/02-design/adr/),
[contracts](docs/helix/02-design/contracts/), the [design index](docs/helix/README.md),
[CHANGELOG](CHANGELOG.md), [ROADMAP](ROADMAP.md) and the
[microsite](https://documentdrivendx.github.io/truss/).

## Relationship to other projects

- **UMF** describes schemas; Truss executes against them and never defines UMF semantics.
- **Weft** compiles queries; Truss composes them with its storage.
- **Axon** is document-oriented. Truss is property-oriented: the property value and edge are its unit
  of storage and mutation.

## Development

`bun install && bun test && python -m build packages/python`; see [AGENTS.md](AGENTS.md) for the rest.

## License

[MIT OR Apache-2.0](LICENSE.md), at your option.
