# truss

Truss is an embeddable property-oriented graph toolkit for PostgreSQL, with
property values typed by [UMF](https://github.com/DocumentDrivenDX/umf) schemas.

**Status:** experimental Python reference implementation. The
[Python interface](packages/python/README.md) provides fresh installation,
catalog registration, exact scalar/nested-container object and independent edge mutations/reads,
preconditions, idempotent receipts, host-owned imports, history, committed feeds
and Weft-compiled scalar and relationship queries. The local baseline is DocumentDrivenDX
`pgserver-pg18==18.6.1` (PostgreSQL18.6) with psycopg3.3.6. Python deployments
use embedded V8 through `mini-racer==0.14.1`; Bun and Node are not required. Start with the [runnable adopter workflow](packages/python/examples/adopter_workflow.py).

## Run a private local instance

The source candidate is **v0.0.49**, adding explicit managed platform grants to
the separate [v0.0.48 HF baseline](docs/helix/04-build/releases/v0.0.48.md).
Final v0.0.49 lineage, installed-artifact and Linux publication qualification
are pending; see the [v0.0.49 draft](docs/helix/04-build/releases/v0.0.49.md).
The command below targets v0.0.49 and requires its qualified release assets and
tag, which are not public yet. Do not substitute v0.0.48 when you need
managed-grants support.

With `uv` installed, run the v0.0.49 launcher in an isolated Python3.11 tool
environment after its assets are qualified and public:

```sh
uvx --no-config --isolated --python 3.11 \
  --constraints https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.49/isolated-runtime-constraints.txt \
  --find-links https://github.com/DocumentDrivenDX/truss/releases/expanded_assets/v0.0.49 \
  --find-links https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2 \
  --from 'truss-toolkit[local,native]==0.0.49' \
  truss-local-postgres \
  --data-dir "$HOME/.local/share/truss/beads" \
  --install
```

The first run may download Python and package wheels. This provisions local
PostgreSQL18.6 and the Truss schema/routines in private per-instance data and
Unix-socket directories. It needs no system PostgreSQL, administrator access,
TCP listener or port configuration. The launcher runs in the foreground;
Ctrl-C stops it while retaining data. Rerun with the same directory to restart.
Add `--probe` to install or confirm Truss and stop while retaining data. This is
a local database runtime, not an HTTP, MCP or TrussRPC application service.
Tools still embed the Python library, connect with an ordinary identity and
register UMF documents; public business-role and module-access configuration is
separate. For development against the current checkout, use `./scripts/truss-local`.

**Source candidate v0.0.49:** native `0.74-candidate`, Weft `0.4.51`, UMF core
`0.10.0`. It adds managed platform grants to the v0.0.48 HF baseline. Final
v0.0.49 lineage, installed-artifact and hosted Linux qualification remain
pending. The latest application runtime is the sole support target. Existing
databases from the exact v0.0.44, shared v0.0.45/46, v0.0.47 and v0.0.48
tuples move forward through explicit transactional migration with
original-attempt recovery and no release-age cutoff. Startup never upgrades or
resets a database. See the [migration guide](packages/python/README.md#runtime-migrations--v0049),
[v0.0.49 draft](docs/helix/04-build/releases/v0.0.49.md), the historical
[v0.0.48 release notes](docs/helix/04-build/releases/v0.0.48.md), and the
[migration qualification plan](docs/helix/04-build/runtime-migration-restoration-plan.md).
Actual Lakebase acceptance and broader managed-service support require separate
qualification.

For source development, the checkout wrapper selects the matching constraints
and PostgreSQL wheel:

```sh
./scripts/truss-local --data-dir "$HOME/.local/share/truss/beads" --install
```

Historical release summaries and their evidence follow.

Version 0.0.41 accepted only original UMF `0.10.0` source documents and
requires a fresh installation. Earlier UMF source formats and upgrades from older Truss
installations are unsupported. Existing databases are never migrated or reset
automatically. Earlier catalog revisions, receipts and retained history within
a current installation remain available under their existing authority rules.

Catalog preparation retains original source documents,
reuses immutable schema indexes in application memory, and checks the current
database basis and authority before prepared writes. Truss v0.0.48 query ABI1.2
uses native-indexed exact string/boolean equality and eligible single required
string-key pages above10,000 source rows. Complete candidate and byte limits apply
before residual filters and `LIMIT`; numeric, temporal, composite and larger-key
queries retain the bounded complete fallback. Complete-entity relationships
remain capped at100 related keys. The v0.0.47/Weft0.4.49 ABI1.1 source-bound
behavior remains historical. Behavior and evidence are tracked in
[`docs/helix/`](docs/helix/README.md). Cyclic schema definitions, record-valued
properties, history offload and managed-service qualification remain unfinished.

## Relationship to other DocumentDrivenDX projects

- **UMF** describes schemas; truss executes against them. truss depends on UMF
  and never defines UMF semantics.
- **Axon** is document-oriented. truss is property-oriented: its unit of
  storage and mutation is the individual property value and edge.
- **HELIX** governs this repository's planning artifacts.

## License

[MIT OR Apache-2.0](LICENSE.md), at your option.

## Experimental runtime build

An initial private [inert PostgreSQL assembly package](packages/postgresql/README.md)
can be built and consumed as ESM with public declarations. It deliberately has
no native capability or installed Truss runtime. See the scoped
[build evidence](docs/helix/04-build/evidence/inert-assembly/README.md).
