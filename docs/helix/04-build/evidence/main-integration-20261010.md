# Truss main integration — 2026-10-10

Integrated committed design/runtime branch 01a4c3ed and Ashlar runtime branch 8af84f71 with remote main 8e2ddf41. Existing uncommitted changes in the primary checkout remain untouched. Historical spec branches contain superseded product drafts and are not blindly merged over the current governed contracts.

Conflict resolution preserves all ignore rules, the schema browser embed, both implementation evidence sections, the current package-delivery qualification and both runtime/Weft build commands. The lockfile includes the combined workspace packages.

Validation: 15 Weft query tests passed; strict Weft type checking passed; inert PostgreSQL and host package builds passed; Hugo, source-seal coverage/site checks and Chromium schema browser checks passed. Full Bun discovery produced 202 passes and 13 failures/errors requiring externally supplied original UMF producer directories. This is not a complete native acceptance qualification. No producer fixtures were invented to suppress those gates.

Merge commits use [skip ci] to avoid triggering the newly added main deployment workflow; no live site publication was requested. Numeric monitor: committed UMF javascript-numeric exports and implementation/tests have no changes since browser baseline 322b193; no new numeric adoption is required.

## Historical spec branches

The [original-commit inventory](historical-branch-inventory-20261010.json) retains 13 unique commits across `spec/storage-layout-and-contracts`, `spec/import-idempotency` and `spec/change-feed-and-groups`. Every changed path still exists on main. This establishes retained locations only, not patch-equivalent incorporation; the branches remain unmerged.

Current governing requirements retain these historical concerns: caller-controlled transaction rollback in CONTRACT-004 and CONTRACT-007/US-044; import identity and provenance in CONTRACT-004/US-034/US-035; module isolation in CONTRACT-005; atomic groups and feed delivery in CONTRACT-004/CONTRACT-006/US-040–042. Current complete-result request receipts under ADR-005 supersede the historical journal-only request-index mechanism. Current document-qualified identity and protected original authority/custody contracts supersede baseline module-name-only authority. Historical native spike files retain their original engine/layout scope; their presence does not qualify the current layout.

Do not merge these old trees wholesale or mark them integrated merely because their file names survive. Any future cherry-pick must identify an actual missing requirement/evidence addition, compare its original source with the current governing contract, and preserve current receipts/security/layout boundaries. No historical branch is deleted by this review. Active uncommitted acceptance/security work remains outside main until its owner supplies a reviewable commit.
