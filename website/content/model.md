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

Truss `0.0.41` is published for fresh PostgreSQL `18.6` installations using UMF `0.10.0` source documents. Focused installed-package qualification on macOS ARM64 passed 11 cohort controls and 9 current-query/disclosure runtime checks. The three real schemas and 11 stress cases are retained from `0.0.40` evidence and were not rerun. Python embeds V8 and does not require Bun, Node or an external JavaScript process. Linux x86_64 Weft `0.4.48` has packaging verification only; no Linux functional or full-suite claim is made. See the [release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.41.md), the [Python guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md#install-version-0041) and the [qualification summary](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.41/qualification.json).

## Three responsibilities

| Project | Responsibility |
| --- | --- |
| [UMF](https://github.com/DocumentDrivenDX/umf) | Schema metadata, interpretation and portable key encoding |
| Truss | Storage binding, mutation, constraints, direct reads and integration |
| [Weft](https://github.com/DocumentDrivenDX/weft) | Logical query compilation to SQL |

Truss consumes UMF; it does not redefine UMF semantics or implement a second SQL compiler. The reference direction uses a portable TypeScript core with separate database and host adapters.

## Integrity must be inspectable

The current report distinguishes database constraints from engine checks. The engine enforces business-key uniqueness under the transaction writer gate; the database key-table primary key serializes physical memberships. String `maxLength` counts Unicode scalar values and binary `maxLength` counts bytes; catalog evolution checks actual stored values before accepting a tightened limit. Retaining an assertion is not the same as enforcing it. Release qualification is scoped to the published local macOS ARM64 checks and retained `0.0.40` evidence; broader native discovery remains incomplete.

[Read the product vision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/00-discover/product-vision.md), [storage decision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/adr/ADR-002-storage-strategy.md) and [architecture](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/architecture.md).

[See what the experiments establish →](../evidence/)
