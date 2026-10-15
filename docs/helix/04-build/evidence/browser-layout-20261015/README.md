# Browser provider dependency: original layout in PGlite

The private browser workspace pins PGlite0.5.10. Its basic Bun1.4.2 check observes
PostgreSQL18.6/server_version_num180006 and executes the exact current generated
Truss layout SQL without rewriting it. The receipt retains the SQL hash and all
48 returned table names. Native int8 transport returns bigint beyond JavaScript's
safe integer range; numeric(18,4) returns original exact text in the sample.
These are transport observations, not UMF validation or a complete numeric API.

Run `bun install --frozen-lockfile`, then
`bun packages/browser/check-layout.ts /new/receipt.json` from the repository root.
The lock retains the exact dependency integrity. This is an in-memory Bun/WASM
layout check. It is not a browser run, native runtime installation, IndexedDB
persistence, local-owner/read-grant authority, sealed action execution or a public
provider. Those remain implementation work under UMF CONTRACT905 at40f01140;
its separate local model/action/preparation/Weft source pins must be preserved.
