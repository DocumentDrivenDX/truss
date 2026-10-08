# Experimental direct PostgreSQL host adapter

`src/index.ts` supplies native connection ports to `createEngineExecutor` in the
portable package. It uses pinned pg 8.16.3 with text parsers for every text-format
native type, ordered rows and native field descriptions. Command-tag counts now come from original admitted protocol text, including
values beyond host numeric precision; stored
numeric/temporal/JSON cells are never decoded into host numbers or dates.

The native probe is `bun scripts/check-pg-executor.ts`. It uses the existing
explicitly labeled private development sandbox; credentials remain memory-only.
Evidence is in `docs/helix/04-build/evidence/inert-assembly/pg-executor.json`.
No connection creation, role, grants or maintenance changes are implied by import.
The caller owns connection settings/authentication. This is a built experimental host package, with public ESM/declaration exports.
It is not published or production-qualified; clean packed-host consumption is checked with `bun scripts/check-packed-host.ts`
using both actual local archives and an explicit unreleased-dependency override. Build the portable package first with `bun run build`, then
`bun run build:host`.

Caller adoption and cancellation remain unavailable. Uncertain connections are
retained in a quarantine set, never returned to the pool. `close()` refuses while
quarantined resources remain; original settlement/recovery integration is still
required. Full resource limits, driver loss/termination behavior, native error
mapping, prepared/pooler/Node support and full Truss bootstrap are unfinished.
Internal SQL templates are trusted implementation code; this is not an arbitrary
SQL authorization boundary. The pg package stays outside the portable library.


Confirmed pg server COMMIT errors in SQLSTATE classes 23/40 are classified only
after same-connection ROLLBACK command confirmation. Other COMMIT failures remain
unknown and retain quarantine. Deferred-FK rejection is natively verified; lost
transport and commit-time serialization schedules remain unfinished.


The experimental bridge now validates complete original frames before invoking
the existing pg parser on every native query. It derives public columns/raw cells/
command counts from those frames and waits for original ReadyForQuery after errors.
Unnamed parse/bind/no-data responses are supported in the observed subset.
Per-query limits: 1 MiB frame, 4 MiB delivered response, 2048 fields, 10000 frames,
five-second response observation. Socket allocation, total heap/shared-operation
accounting and original issuer/epoch/recovery custody remain unqualified.
