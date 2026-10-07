---
ddx:
  id: TD-033
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-033
      kind: informed_by
    - id: SD-008
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
---

# TD-033: Isolated embedded PostgreSQL qualification

## Technical Approach

Run the exact bootstrap bundle on a fresh local PostgreSQL instance managed by a test harness, without a separately provisioned server. Reuse CONTRACT-008's generated artifact and independent native inventory comparator; do not maintain an embedded-only DDL variant. SPIKE-003 used pgserver 0.1.4/Python 3.11/PostgreSQL 16.2 and pgembed 0.2.0/Python 3.12/PostgreSQL 17.9. That evidence covers specific local server processes, not browser WASM or a future adapter.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/conformance/src/harness/embedded.ts` | Unique instance data/socket paths, process ownership and reliable teardown | US-033-AC1, US-033-AC3 |
| `packages/conformance/src/layout/native.ts` | Shared independent inventory and behavior probes | US-033-AC1, US-033-AC2 |
| `tests/host/embedded.test.ts` | Embedded install/check, server parity and parallel isolation | US-033-AC1, US-033-AC2, US-033-AC3 |

## API and Integration

Harness returns an executor endpoint and immutable runtime/server/platform identity; it belongs outside browser-compatible core. Each run owns a private data directory, socket directory and process handle. Cleanup terminates only that owned process, including on cancellation/failure. Use the same byte-pinned bundle on embedded and external test-server profiles. Compare stable semantic inventory: columns/types/defaults, keys, constraints, indexes, functions/triggers, partition configuration, policies/grants and marker. Normalize only volatile OIDs/physical paths; never mask missing semantics or search-path/privilege differences.

## Testing and Security

Install as a disposable administrative identity, then run behavior checks as ordinary writer and declared roles. AC2 object parity is necessary but cannot alone establish protocol or concurrency parity. Run the selected corpus additionally for the feature's broader protocol claim and qualify actual Bun/Node adapter combinations independently. Parallel fixtures use distinct sentinel objects, roles and mutations; each verifies absence of the other's state and survives teardown of the other instance. No shared default directory/port or global process kill.

## Sequence and Rollback

Finalize supported embedded distribution/platform and native target matrix; implement red install/parity/isolation tests; reuse bootstrap inventory; run corpus and publish scoped receipts. Disposable fixture cleanup removes only its own artifacts, never an existing host database. A failed run leaves diagnosable logs and cannot publish support.

## Risks and Gates

Embedded package/runtime selection and complete inventory remain gates. Historical versions are evidence pins, not mandatory current support or a license to claim all embedded implementations. Browser-embedded PostgreSQL would need a separate profile for functions, extensions, transaction/concurrency and adapter behavior. Real server parity and parallel lifecycle tests are required; parsing generated DDL is insufficient.
