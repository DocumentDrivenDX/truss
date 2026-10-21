---
title: "A graph with a structural foundation."
description: "Understand the design before evaluating the implementation."
composition: model-primary
number: "02"
---
## The property is the unit

Truss is property-oriented. An individual property value or edge is the logical unit of identity, mutation and history. Document-shaped views can be derived from that structure.

The selected PostgreSQL storage design packs values into one flat JSONB map per object, keyed by catalog property ID. A missing key means absent; JSON `null` means explicit null. Unknown values belong in a retained map. Logical granularity and physical packing are separate decisions.

## Evolve a catalog

A fixed shared layout stores objects, business keys, relationships and schema definitions. Adding a type, property, key or relationship adds catalog rows rather than per-type tables, columns or indexes. The object row is canonical; the journal is designed to capture property history in the same transaction.

Truss `0.0.46` provides a private PostgreSQL `18.6` launcher alongside the Python embedding library. Eight focused lifecycle, isolation and CLI tests pass on macOS ARM64 and Linux x86_64 with Python `3.11.17`. The [published-package receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/isolated-local-install-20261021/published-0.0.46/receipt.json) verifies the quickstart outside the checkout: two simultaneous instances retain separate data and installation identities across restarts. The [Linux release gate](https://github.com/DocumentDrivenDX/truss/actions/runs/39670547224) also passes selected installed-engine workflows and the original small public workload. [Release assets and pins](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.46) define the package cohort. Broad discovery, managed-service support and performance certification remain unfinished. Python embeds V8 without requiring Bun, Node or an external JavaScript process.

## Three responsibilities

| Project | Responsibility |
| --- | --- |
| [UMF](https://github.com/DocumentDrivenDX/umf) | Schema metadata, interpretation and portable key encoding |
| Truss | Storage binding, mutation, constraints, direct reads and integration |
| [Weft](https://github.com/DocumentDrivenDX/weft) | Logical query compilation to SQL |

Truss consumes UMF; it does not redefine UMF semantics or implement a second SQL compiler. The reference direction uses a portable TypeScript core with separate database and host adapters.

## Integrity must be inspectable

The current report distinguishes database constraints from engine checks. The engine enforces business-key uniqueness under the transaction writer gate; the database key-table primary key serializes physical memberships. String `maxLength` counts Unicode scalar values and binary `maxLength` counts bytes; catalog evolution checks actual stored values before accepting a tightened limit. Retaining an assertion is not the same as enforcing it. Release qualification is scoped to the linked macOS and Linux checks and retained `0.0.40` evidence; broader native discovery remains incomplete.

[Read the product vision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/00-discover/product-vision.md), [storage decision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/adr/ADR-002-storage-strategy.md) and [architecture](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/architecture.md).

[See what the experiments establish →](../evidence/)
