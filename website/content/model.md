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

## Three responsibilities

| Project | Responsibility |
| --- | --- |
| [UMF](https://github.com/DocumentDrivenDX/umf) | Schema metadata, interpretation and portable key encoding |
| Truss | Storage binding, mutation, constraints, direct reads and integration |
| [Weft](https://github.com/DocumentDrivenDX/weft) | Logical query compilation to SQL |

Truss consumes UMF; it does not redefine UMF semantics or implement a second SQL compiler. The shipped engine is the Python package; the portable TypeScript core remains the reference for the shared conformance corpus.

## Integrity must be inspectable

The enforcement report distinguishes database constraints from engine checks. The engine enforces business-key uniqueness under the transaction writer gate; the database key-table primary key serializes physical memberships. String `maxLength` counts Unicode scalar values and binary `maxLength` counts bytes; catalog evolution checks actual stored values before accepting a tightened limit. Retaining an assertion is not the same as enforcing it. Support claims are limited to what the test suite exercises.

[Read the product vision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/00-discover/product-vision.md), [storage decision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/adr/ADR-002-storage-strategy.md) and [architecture](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/architecture.md).