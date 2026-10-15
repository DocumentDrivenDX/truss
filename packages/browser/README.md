# Truss browser lifecycle in progress

`openBrowserStore({name,layoutSql})` runs in a browser worker. Supply the exact
generated Truss layout SQL; its hash is checked before opening IndexedDB.
An available result contains `{store,owner}`. Keep the issued owner inside that
worker: `store.info(owner)` and `await store.close(owner)` require its original
identity. A second owner of the same canonical name returns `store_in_use`
immediately. This package exports no connection or raw SQL API.

One exclusive Web Lock protects the named IndexedDB store while its worker lives.
Original layout and the origin/name-bound store marker initialize atomically.
Opening an existing partial or foreign marker refuses without resetting it.
PGlite uses `relaxedDurability:false`; readiness and close await explicit flush.
Successful close is PGlite's lifecycle acknowledgement after that flush, not
proof of crash-safe physical IndexedDB shutdown. It also waits for Web Lock
handback before resolving. A reported lifecycle failure
fences the instance and retains its lock until the worker terminates.

The current API supplies lifecycle only. Catalog/model/action registration,
separate issued selection-read grants, original local-profile Weft lowering,
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
