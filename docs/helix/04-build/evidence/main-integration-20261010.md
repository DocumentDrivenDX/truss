# Truss main integration — 2026-10-10

Integrated committed design/runtime branch 01a4c3ed and Ashlar runtime branch 8af84f71 with remote main 8e2ddf41. Existing uncommitted changes in the primary checkout remain untouched. Historical spec branches contain superseded product drafts and are not blindly merged over the current governed contracts.

Conflict resolution preserves all ignore rules, the schema browser embed, both implementation evidence sections, the current package-delivery qualification and both runtime/Weft build commands. The lockfile includes the combined workspace packages.

Validation: 15 Weft query tests passed; strict Weft type checking passed; inert PostgreSQL and host package builds passed; Hugo, source-seal coverage/site checks and Chromium schema browser checks passed. Full Bun discovery produced 202 passes and 13 failures/errors requiring externally supplied original UMF producer directories. This is not a complete native acceptance qualification. No producer fixtures were invented to suppress those gates.

Merge commits use [skip ci] to avoid triggering the newly added main deployment workflow; no live site publication was requested. Numeric monitor: committed UMF javascript-numeric exports and implementation/tests have no changes since browser baseline 322b193; no new numeric adoption is required.
