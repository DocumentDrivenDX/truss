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

**Version 0.0.41:** native `0.72-candidate`, Weft `0.4.48`, and UMF core
`0.10.0`. Local macOS ARM64 qualification covers 11 cache/cohort controls and
nine PostgreSQL query/disclosure checks. The unchanged SQL runtime retains the
three real-schema and 11 stress-case results from v0.0.40; those workloads were
not repeated. Other platform checks cover packaging only. See the
[v0.0.41 release page](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.41).

Version 0.0.41 accepts only original UMF `0.10.0` source documents and
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
