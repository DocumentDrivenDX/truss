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

Truss `0.0.49` adds managed platform-grant policy and install API/CLI support to the v0.0.48 HF baseline. Its published, source-bound evidence covers native manifest SHA-256 prefix `288801f7`, four admitted migration sources (106 cases), the HF62 independent corpus, the managed 21-module/130-test gate, the public Weft 0.4.51 cohort from compiler source revision `55715373…`, and selected installed Linux/macOS qualification. The [release notes](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/releases/v0.0.49.md) and [published verification receipt](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/04-build/evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json) identify the exact artifacts and limits. Actual Lakebase acceptance remains outside this evidence and requires separate qualification; broad native discovery and general p95 claims are not established by these selected gates.

Only the latest application runtime is supported. The latest tool provides offline, explicit transactional forward migration for the admitted UMF `0.10` sources: v0.0.44, the shared v0.0.45/46 lineage, v0.0.47 and v0.0.48 on PostgreSQL `18.6`. Admitted databases retain a forward route without a release-age cutoff. Startup never upgrades or resets a database.

## Three responsibilities

| Project | Responsibility |
| --- | --- |
| [UMF](https://github.com/DocumentDrivenDX/umf) | Schema metadata, interpretation and portable key encoding |
| Truss | Storage binding, mutation, constraints, direct reads and integration |
| [Weft](https://github.com/DocumentDrivenDX/weft) | Logical query compilation to SQL |

Truss consumes UMF; it does not redefine UMF semantics or implement a second SQL compiler. The reference direction uses a portable TypeScript core with separate database and host adapters.

## Integrity must be inspectable

The current report distinguishes database constraints from engine checks. The engine enforces business-key uniqueness under the transaction writer gate; the database key-table primary key serializes physical memberships. String `maxLength` counts Unicode scalar values and binary `maxLength` counts bytes; catalog evolution checks actual stored values before accepting a tightened limit. Retaining an assertion is not the same as enforcing it. The linked v0.0.49 macOS/Linux receipts qualify only their selected release gates; the retained v0.0.40 evidence remains historical, and broader native discovery is incomplete.

[Read the product vision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/00-discover/product-vision.md), [storage decision](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/adr/ADR-002-storage-strategy.md) and [architecture](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/architecture.md).

[See what the experiments establish →](../evidence/)
