# truss

truss is a planned property-oriented graph engine that runs on SQL databases.
It will store graph data in a fixed set of tables, starting on PostgreSQL,
with each property value typed by a [UMF](https://github.com/DocumentDrivenDX/umf)
schema, and later add query, mutation and constraint engines on top.

**Status:** discovery. No code exists yet. Direction, prior art and open
decisions are in [`docs/helix/`](docs/helix/README.md), starting with the
[product vision](docs/helix/00-discover/product-vision.md).

## Relationship to other DocumentDrivenDX projects

- **UMF** describes schemas; truss executes against them. truss depends on UMF
  and never defines UMF semantics.
- **Axon** is document-oriented. truss is property-oriented: its unit of
  storage and mutation is the individual property value and edge.
- **HELIX** governs this repository's planning artifacts.

## License

[Apache License 2.0](LICENSE).
