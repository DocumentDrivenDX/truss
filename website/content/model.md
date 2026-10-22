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

Truss `0.0.48` publishes latest-tool-only offline migration for the admitted UMF `0.10` sources: v0.0.44, the shared v0.0.45/46 lineage, and v0.0.47 on PostgreSQL `18.6`. Admitted databases migrate forward without a release-age cutoff; previous application runtimes are not supported. The public 80-case migration, 62-case independent archive, selected driver checks and two-instance `uvx` restart receipts are [Linux 80-case migration receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/public-assets/migration-qualification.json), [macOS 80-case migration receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/mac-migration80/qualification.json), [Linux 62-case conformance receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/public-assets/hf-conformance-qualification.json), [macOS 62-case conformance receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/mac-independent62/qualification.json), [30-driver receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/mac-driver30/receipt.json) and [two-instance uvx receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/mac-uvx-two-instances/receipt.json). [public release validation](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/hohfeld-followup-20261021/published-0.0.48/validation.json) binds the published assets and exact count (15). Pre-0.10/protected-profile migration, managed services, other drivers, broad discovery and general p95 certification remain outside this result. Python embeds V8 without an external JavaScript runtime.

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
