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

Truss `0.0.47` restores explicit offline runtime migration from the exact populated UMF `0.10` v0.0.44 and shared v0.0.45/46 installations on PostgreSQL `18.6`. Only the latest application runtime is supported; admitted databases migrate forward without age-based expiry. The [Linux tag workflow](https://github.com/DocumentDrivenDX/truss/actions/runs/39702368076) passes selected installed-runtime checks, all 52 migration cases without skips and the original 1,000-object/1,000-edge public workload. [Public release verification](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/runtime-migrations-20261021/published-0.0.47/validation.json) checks all 12 checksummed assets, a fresh public-wheel 52-case run on macOS ARM64/Python 3.11.17, and the published `uvx` command with two independent instances retaining data across restart. [Release assets and pins](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.47) define the exact tuple. Pre-0.10 and protected-profile migration, managed-service support, broad discovery and performance certification remain outside this result. Python embeds V8 without an external JavaScript runtime.

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
