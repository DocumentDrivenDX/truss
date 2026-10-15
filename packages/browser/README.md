# Truss browser store in progress

`openBrowserStore({name,layoutSql})` runs in a browser worker. Supply the exact
generated Truss layout SQL; its hash is checked before opening IndexedDB.
An available result contains `{store,owner}`. Keep the issued owner inside that
worker: `store.info(owner)` and `await store.close(owner)` require its original
identity. A second owner of the same canonical name returns `store_in_use`
immediately. This package exports no connection or raw SQL API.

`await store.registerDocument(owner,{documentId,documentRevision,sourceUtf8})`
registers one complete core0.8 Record with required singular String Fields and
one single-member primary Key. It uses original UMF inspection and the existing
Truss SQL catalog/lineage planner. Original UTF8, authored revision, validation
observations, definition coordinates, key order and catalog changes are retained.
An exact ID/revision/full-source repeat returns `unchanged`; changed documents
or another registration return `refused` until catalog evolution is implemented.
`await store.catalog(owner)` returns that metadata, or null before registration.
Registration, metadata reads and close are serialized and registration flushes
before returning success. Other relevant unknown meanings refuse. The opaque
`umf.actions/0.1.0` extension is retained, without admitting its action semantics.

One exclusive Web Lock protects the named IndexedDB store while its worker lives.
Original layout and the origin/name-bound store marker initialize atomically.
Opening an existing partial or foreign marker refuses without resetting it.
PGlite uses `relaxedDurability:false`; readiness and close await explicit flush.
Successful close is PGlite's lifecycle acknowledgement after that flush, not
proof of crash-safe physical IndexedDB shutdown. It also waits for Web Lock
handback before resolving. A reported lifecycle failure
fences the instance and retains its lock until the worker terminates.

`await store.registerAction(owner,{module,action})` derives original UMF local
preparation from the registered source and returns an opaque action handle plus
separate model/pin/preparation metadata copies. `await store.grantSelectionRead(owner,action)`
issues a separate opaque grant and an informational declaration over the full
canonical target population and all original members. Keep both handles inside
the worker. Forged, foreign and previous-open action handles refuse; persisted
store identity does not preserve issued handle identity across opens.

The current API supplies lifecycle, this core catalog subset and local action/read
grant issuance. Original local-profile Weft selection integration,
keys, sealed manifests, effects, replay and recovery remain unfinished under
UMF CONTRACT905 at40f01140. Owner possession does not grant selection/action
authority. There is no native person/SCRAM/C-D-E claim or production provider.

Basic checks from the repository root:

```sh
bun install --frozen-lockfile
bun node_modules/typescript/bin/tsc -p packages/browser/tsconfig.json
bun packages/browser/check-lifecycle.ts /path/to/package.json /new/receipt.json
```

The supplied package.json must resolve an installed Playwright and Chromium.
The harness serves original PGlite distribution assets without rewriting them
and exercises real workers, two-tab exclusion, immediate handoff, owner identity and IndexedDB
reopen. The retained Chromium153 result is in
`../../docs/helix/04-build/evidence/browser-lifecycle-20261015/receipt.json`.
It is not an interruption/quota/crash/restore or action-execution qualification.

Build a fixed website-consumable bundle with:

```sh
bun packages/browser/build-assets.ts /absolute/new/browser-bundle
```

The fresh directory contains `store.js`, original `layout.sql`, pinned PGlite
distribution assets and licenses, unchanged UMF local-action ESM under `owners/`,
its original notice inventory/files, plus `manifest.json`. Import `store.js` inside
the website worker; keep capabilities there. All asset URLs are relative, so the
bundle can live under a GitHub Pages prefix. The manifest distinguishes original
UMF input hashes, actual Truss/build input hashes and the generated provider hash.
It records every emitted asset except itself; the command returns its own digest.
The Chromium check builds and exercises this exact output. No temporary checkout
or compilation service is a runtime dependency. The package remains private and
unpublished; this build is the current source-vendor interface.

Weft main `4f5b73d` compiles the original local Products UPDATE through its
Rust mutation registry and production WASM `MutationCompiler`. Building with
`--features truss-browser-local` adds `register_browser_selection` and
`lower_selection_json` over the separate `truss-browser-binding/0.1` profile.
It preserves native transaction admission and validates original ordered member
and primary-key mappings. All Record members enter complete-population
preflights, including fields unused by the predicate. Basic Rust checks retain
native65/66 behavior and the64-member browser mapping; actual Chromium executes
the resulting selection SQL against a real registered Truss catalog in PGlite.
That component test explicitly installs original scalars.sql and seeds rows
administratively. Provider selection/read-grant consumption and helper installation are now
implemented below; worker action execution remains unfinished. This source checkpoint is not a
new published wheel or an enabled executor.

The worker now also provides `materialize(owner, action, grant, input)`,
`seal(owner, action, grant, work, {requestKey, attempt})` and
`recoverSeal(owner, freshAction, freshGrant, reference)`. Materialization invokes
original Weft WASM, validates the complete target population, selects actual
IDs/versions and constructs the original UMF manifest with exact Key receipts.
The manifest retains the accepted authored document revision as its action
revision; the source content digest remains a separate pin. Work handles stay
inside the issuing worker and open store.

Persist the pending request key, attempt and reference before calling `seal`.
The reference contains profile `truss-browser-seal-reference/0.1`, storeId,
incarnation, requestKey, attempt, manifestSha256, planSha256 and modelSha256.
It is recovery metadata, not authority. Identical retries return the original
receipt bytes; different input under the same key conflicts. Recovery after
reopen requires freshly issued action/read-grant capabilities. Missing records
are unresolved and do not authorize a new attempt. Confirmed callback rollback
is reported separately from ambiguous commit/flush outcomes; uncertainty fences
the store. No automatic retry loop is provided.

The basic Chromium workflow materializes three rows into batches of two and
one, seals, replays and recovers after reopen. Its rows are administrative test
fixtures. Production bootstrap/import, batch mutation, effects, journal/feed and
execution receipts remain unfinished. Seal recovery alone is not crash safety
qualification or action execution. The owned bundle includes unchanged pinned
Weft JS/WASM and available original notices; its producer metadata records the
limited notice inventory without claiming complete licensing closure.
