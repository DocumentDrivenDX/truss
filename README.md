# truss

Truss is an embeddable property-oriented graph toolkit for PostgreSQL, with
property values typed by [UMF](https://github.com/DocumentDrivenDX/umf) schemas.

**Status:** experimental Python reference implementation. The
[Python interface](packages/python/README.md) provides installation and upgrades,
catalog registration, exact scalar/nested-container object and independent edge mutations/reads,
preconditions, idempotent receipts, host-owned imports, history, committed feeds
and Weft-compiled scalar and relationship queries. The local baseline is DocumentDrivenDX
`pgserver-pg18==18.6.1` (PostgreSQL18.6) with psycopg3.3.6. Start with the [runnable adopter workflow](packages/python/examples/adopter_workflow.py).

Cyclic schema definitions, record-valued properties, composition/owned objects,
history offload and managed-service qualification remain unfinished. Design and evidence live in
[`docs/helix/`](docs/helix/README.md).

## Relationship to other DocumentDrivenDX projects

- **UMF** describes schemas; truss executes against them. truss depends on UMF
  and never defines UMF semantics.
- **Axon** is document-oriented. truss is property-oriented: its unit of
  storage and mutation is the individual property value and edge.
- **HELIX** governs this repository's planning artifacts.

## License

[Apache License 2.0](LICENSE).

## Experimental runtime build

An initial private [inert PostgreSQL assembly package](packages/postgresql/README.md)
can be built and consumed as ESM with public declarations. It deliberately has
no native capability or installed Truss runtime. See the scoped
[build evidence](docs/helix/04-build/evidence/inert-assembly/README.md).
