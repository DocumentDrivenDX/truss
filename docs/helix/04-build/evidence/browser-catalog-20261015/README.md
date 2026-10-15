# Browser core catalog and owned asset bundle

UMF source40f011402bf8f0c9512225975b62a034f1da325c,
`docs/helix/03-test/fixtures/bulk-update/local-products-input.json`, supplies the
original local Products model. Its UTF8 is retained unchanged at
`packages/browser/fixtures/local-products-model.json`, digest
b8ce3cfe76eeda7c1531b2bbf8aba121c9d9614800ff1f3301f853c048516f27.

The basic Chromium153 worker case exercises the exact owned asset build:
original layout, registered Record/two Fields/primary Key, identical retry,
three original catalog change rows, metadata/source readback across IndexedDB
reopen, issued-owner refusal and exclusive worker handoff. The existing native
lineage/catalog planner and containers dependency execute unchanged. Generated
columns are excluded during persistence and schema_change uses its original
JSON-null-preserving function. Strict browser-worker TypeScript also passes.

The original core0.8 owner bundle7c0/88899e interprets selected core meaning;
its unknown umf.actions extension remains opaque and preserved. The catalog's
profile is truss-browser-catalog/0.1, never native66 admission. No action
registration, independent selection-read grant, object effect, sealing, replay,
crash recovery or full local-bulk executor is qualified. Lifecycle limitations
from the earlier browser checkpoint still apply.

See packages/browser/README.md for the portable build/check commands. The
receipt records the actual provider/manifest digests; the asset manifest retains
original input hashes separately from generated output and inventories pinned
PGlite assets and licenses. No site deployment occurred.

Two fresh builds from the repository root and `/private/tmp` produced identical
manifest and provider hashes, matching the retained Chromium receipt. Supported
Bun whitespace minification removes CWD-dependent generated path comments. The
builder rechecks captured source hashes after packaging and verifies the emitted
layout against its captured input before writing the manifest.
