# Experimental direct PostgreSQL host adapter

`src/index.ts` supplies native connection ports to `createEngineExecutor` in the
portable package. It uses pinned pg 8.16.3 with text parsers for every text-format
native type, ordered rows and native field descriptions. Command-tag counts are
accepted only as nonnegative safe integers and exposed as decimal text; stored
numeric/temporal/JSON cells are never decoded into host numbers or dates.

The native probe is `bun scripts/check-pg-executor.ts`. It uses the existing
explicitly labeled private development sandbox; credentials remain memory-only.
Evidence is in `docs/helix/04-build/evidence/inert-assembly/pg-executor.json`.
No connection creation, role, grants or maintenance changes are implied by import.
The caller owns connection settings/authentication. This is source-only host code,
not a published/packed or production-qualified host package.

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
