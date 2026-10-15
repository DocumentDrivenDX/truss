---
ddx:
  id: PLAN-key-encoding-performance
  type: implementation-plan
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: ADR-003
      kind: informed_by
---

# Database-owned key derivation

## Decision and scope

Owner-directed 2026-10-15; reviewed with Astra. The earlier shared Rust client
encoder proposal is superseded. PostgreSQL already verifies scalar key tuples
and owns the admitted catalog, source bytes, current values and uniqueness.
Factor that verifier into one native encoder and derive keys at the storage
boundary. No client encoder, context cache, per-key receipt or mandatory Weft
dependency is needed for ordinary object keys.

Preserve `umf-key-tuple-v1`, existing namespace bytes, hex transport, locking,
source epoch/definition pins, authorization and collision checks. Support stays
within the admitted native subset: string, integer, boolean, binary, and decimal
precision 18 with scale 2 or 4. Apply selected Field allowedValues using canonical
scalar bytes; defaults never fill missing key components. Independent bundled
UMF producers remain differential test oracles. Optional query compilation uses the minimal Weft 0.4.31 compatibility release
(backend unchanged), accepting actual native 0.65/0.66 bindings. Registration's broader UMF
preparation and the separate protected security observation retain their Bun
requirements.

## Implementation

SDK 0.0.31 / native 0.66 derives create/update, precondition, lookup, import and
catalog-backfill keys in PostgreSQL. Compatibility parameters accept empty or
NULL client key payloads; supplied encoded tuples/receipts are rejected.
New key contexts identify native derivation, while historical contexts and key
rows remain untouched. Native 0.65 upgrades verify the existing owned transition
layout without attempting its older migration a second time.

## Verification and limits

The [database evidence summary](evidence/database-key-derivation-20261015/summary.json) records actual tests and byte-preserving upgrade
results. Differential tests compare all five families against UMF 0.7/0.8 and
exercise refinements, exact numeric normalization, bounds and private helper
permissions. Runtime tests forbid client encoders after registration. The upgrade
test seeds a real native 0.65 predecessor and compares complete stored key and
reservation bytes before and after upgrade, then reads and rekeys the old object.

Historical [client encoder evidence](evidence/key-encoding-20261015/summary.json)
belongs to the superseded Rust client proposal. Its encoder timings do not measure
this database implementation. Consumer-reported 0.25–0.29 seconds per Bun call
motivated the change; no new end-to-end throughput claim follows from removing
those calls. Packages remain unpublished; remote release CI is not run locally.
