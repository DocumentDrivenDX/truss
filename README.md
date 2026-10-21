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

With `uv` installed, run the published Truss `0.0.46` launcher in an isolated
Python3.11 tool environment:

```sh
uvx --no-config --isolated --python 3.11 \
  --constraints https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.46/isolated-runtime-constraints.txt \
  --find-links https://github.com/DocumentDrivenDX/truss/releases/expanded_assets/v0.0.46 \
  --find-links https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2 \
  --from 'truss-toolkit[local,native]==0.0.46' \
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

**Version 0.0.46:** native `0.72-candidate`, Weft `0.4.49`, UMF core `0.10.0`.
Eight focused lifecycle, isolation and CLI tests pass on macOS ARM64 and Linux
x86_64 with Python3.11.17 and PostgreSQL18.6. The [published-package receipt](docs/helix/04-build/evidence/isolated-local-install-20261021/published-0.0.46/receipt.json)
verifies this exact quickstart outside the checkout: two simultaneous private
instances retain separate data and installation identities across restarts.
The [Linux release gate](https://github.com/DocumentDrivenDX/truss/actions/runs/39670547224) also passes the selected installed-engine workflows and original small public workload.
Broad test discovery, managed-service support and performance certification
remain unfinished. See the [release notes](docs/helix/04-build/releases/v0.0.46.md).

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
database basis and authority before prepared writes. Query ABI 1.1 buffers each
selected record or relationship type's complete source set before caller
predicates, up to 10,000 rows per type; complete-entity relationship data remains
separately bounded to 100 related keys. Behavior and qualification
evidence are tracked in [`docs/helix/`](docs/helix/README.md). Cyclic schema
definitions, record-valued properties, history offload and managed-service
qualification remain unfinished.

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
