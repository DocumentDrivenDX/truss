# Truss browser store

Private browser-worker implementation on PGlite0.5.10/PostgreSQL18.6. The current
functional path is register document → load objects → register action/read grant
→ Weft materialize → seal → submit → claim → execute frozen batches → recover.
Supported objects are rootless Records with required singular String Fields and
one single-member primary Key. Actions are the original UMF bounded constant
`graph-write/1` set recipe under `umf.actions.local-tx/1`. Relationships, wider
value domains, catalog evolution, cancellation, feed and retention are unfinished.
This is not complete local-bulk qualification or native66 installation/security.

## Worker lifecycle and catalog

`openBrowserStore({name,layoutSql})` requires the exact original generated Truss
layout SQL. It returns `{outcome:'available',store,owner}` or `store_in_use`.
Keep owner/action/grant/work capabilities inside the worker. No connection/raw
SQL API is exported. A Web Lock protects the named IndexedDB store; partial or
foreign markers refuse without reset. Origin/name/store/incarnation are retained.
PGlite uses `relaxedDurability:false`; acknowledged writes/readiness/close await
explicit flush. Close also waits for lock handback. Uncertain storage fences the
instance and retains its lock until worker termination. Successful close is a
PGlite lifecycle acknowledgement, not arbitrary crash/restore qualification.

`registerDocument(owner,{documentId,documentRevision,sourceUtf8})` registers the
supported core0.8 catalog through original UMF inspection and Truss SQL catalog/
lineage generation. Exact source, authored revision, validation observations,
definition identities, member/key order and changes are retained. Exact repeat
is unchanged; changed documents refuse. `catalog(owner)` returns the snapshot.
Catalog registration preserves the actions extension opaquely; only separate
`registerAction(owner,{module,action})` admits its original local preparation.
`grantSelectionRead(owner,action)` issues a separate capability over the complete
canonical target population and all original members. Metadata copies are inert.
Forged/foreign/previous-open handles refuse; reopen requires fresh issuance.

## Public object loading and readback

```ts
const input = {
  target: {documentId: 'product-local-action-demo', module: 'sales', record: 'products'},
  rows: [{fields: [
    {module: 'sales', field: 'product-id', value: 'bar'},
    {module: 'sales', field: 'product-name', value: 'Sample'}
  ]}],
  request: {requestKey: 'initial-products', attempt: 'load-1'}
};
const result = await store.loadObjects(owner, input);
const objects = await store.readObjects(owner, input.target);
const recovered = await store.recoverLoad(owner, input);
```

Retain exact input before dispatch. Loads accept 1–100 complete rows and 1MiB;
readback refuses above 100 rows/8MiB without truncation. Objects, original UMF Key
custody, guard generations, permanent reservations, creation journal and original
outcome commit together. IDs/versions remain exact text. Duplicate/reserved keys
refuse the whole load. After any dispatched request loses its response, use
recoverLoad only. Missing recovery is unresolved and never permits redispatch or
a new key. Recovery failure cannot establish original rollback.

## Materialization, seals and jobs

`materialize(owner,action,grant,{sql,parameters,batchSize,maxItems})` invokes pinned
original Weft WASM, validates the complete population, selects actual Key/ID/
version rows and constructs the original UMF manifest with original Key receipts.
Parameters currently contain exact `{string:value}` literals. Work handles stay
inside the issuing open worker. Manifest action revision retains the accepted
authored document revision; the source digest is a separate pin.

`seal(owner,action,grant,work,{requestKey,attempt})` persists original work and
receipt bytes. Retain pending key/attempt/reference before RPC. The inert reference
has profile `truss-browser-seal-reference/0.1`, storeId, incarnation, requestKey,
attempt, manifestSha256, planSha256 and modelSha256. `recoverSeal` takes fresh
capabilities and that reference after reopen. Exact replay returns original
bytes; changed input under the key conflicts. Missing is unresolved.

`submit(owner,action,grant,{key,reference,control:{requestKey,attempt}})` persists
one job and its original sampled control result. Submission key identifies full
frozen manifest/source intent; control key identifies one observation. Same
control replays exactly. New control for the same intent observes the same job's
current state. Distinct genuine seals of identical work identify the same job;
first original full seal remains evidence. `recoverSubmit` observes exact original
input without mutation. Recorded semantic refusals recover before fresh seal
admission. `reviewJob(owner,action,grant,job)` returns retained manifest/state.

`claim(owner,action,grant,{job,control})` persists a claim for the next batch and
its original result together. It returns batch ordinal, exact decimal fence and
actual PostgreSQL 60-second lease. `recoverClaim` never renews the original fence/
deadline. A fresh claim while active refuses, even after expiry. Persistent
lastFence survives batch advancement; exhaustion refuses without wrap. A recovered
claim is an observation, never proof of current execution eligibility.

## Atomic execution and recovery

```ts
const input = {job: claimed.job, batch: claimed.batch, fence: claimed.fence};
const outcome = await store.executeBatch(owner, action, grant, input);
// After a lost/indeterminate reply, observe only; retain the original input.
const recovered = await store.recoverBatch(owner, freshAction, freshGrant, input);
```

Current issued owner/action/read grant and exact retained source/seal are required.
The engine checks the live claim, commits an effect-admission record and flushes
it before invoking the business transaction. Existing admission can return only
the original terminal outcome or indeterminate; it never redispatches effects.
Lease expiry cannot interrupt the already-admitted serialized transaction.

Original UMF preparation, manifest/input/frame/Key interpreters validate the
entire batch before effects. Current identity/version/key membership/reservation
must match the frozen work; Key Fields cannot change. Successful property changes,
version increments, full before/after journal events, complete item verification,
receipt, original batch outcome and contiguous job progress commit atomically.
No-op items retain version and emit no business journal entry while keeping a
durable outcome. Replayed outcomes retain original bytes. A confirmed original
same-instance callback rollback records a stopped conflict/rejected/failed outcome
in a separate acknowledged transaction. Commit/rollback/flush/custody uncertainty
fences; admission without outcome remains indeterminate and prohibits redispatch
or a replacement fence. No pg_xact_status inference or new sidecar is used.

## Journal and checks

An explicit browser-only two-CHECK/finite-partition adjunct selects
`truss-browser-journal-exact-bytes/0.1` with browser history event/record0.1.
Original foundation layout SQL/hash stays unchanged. Marker-retained CHECKs and
partition bounds are verified in UTC/ISO. Actual PostgreSQL JSONB text bytes,
base64 and SHA256 are retained; native history decoders are excluded. Creation
and property events carry actual store/incarnation, xid/seq, original control or
job/batch/item, and full rootless images/source digest. The finite horizon spans
the previous month through 13 months ahead; expiry blocks new events without
silently extending it. Existing readback/replay/recovery remains available.

```sh
bun install --frozen-lockfile
bun node_modules/typescript/bin/tsc -p packages/browser/tsconfig.json
bun packages/browser/check-lifecycle.ts /path/to/playwright/package.json /new/receipt.json
bun packages/browser/build-assets.ts /absolute/new/browser-bundle
```

The real Chromium worker check covers public load/read, original Weft/UMF work,
three updates in two batches, exact replay/reopen recovery, no-op, stale second
item and a real SQL second-item fault proving whole-batch rollback. Test-only
fault injection is separate from the production provider. No administrative
business seeding or arbitrary crash/eviction/restore qualification is claimed.

Owned bundles contain original layout, pinned PGlite, original UMF core7c0f0c98
and local-action40f01140/producer633f8ad6, original Weft4f5b73df JS/WASM, existing
notices and complete emitted-asset manifest. Runtime URLs are relative for Pages
prefixes; mutable checkouts/compilation services are not runtime dependencies.
Two-CWD builds verify reproducible assets. Notice inventories do not invent
missing project licenses or claim complete licensing closure. This private
source delivery does not publish new Python/Weft wheels.
