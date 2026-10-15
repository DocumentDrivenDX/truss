# Browser cancellation — 2026-10-15

Astra Ultra approved the plan and implementation after current-batch admission
custody checks were added. Strict TypeScript and the final actual Chromium153 /
PGlite0.5.10 / PostgreSQL18.6 basic workflow passed: queued cancellation, exact
control replay, claim/execute PAP_CANCELLED refusal, reopen recovery and unchanged
business rows. Existing execution, rollback/conflict, no-op and journal pages also
passed. This is a local-owner profile, not native bulk/security qualification.

Two builds from different working directories matched the final Chromium source:
manifest `2b04a719c6ffa36c39f737a98d6d49ebcc3aee74c1cece0d8a9fc6b180ba87bb`,
provider `48e1f33b300aa26301fbf25562f553dd7f28c87abbab292402144480d612d100`.

Cancelled jobs retain their committed prefix and original results. Uncertain
admitted work remains reconciling; cancellation does not prove rollback.
Retention is lifetime-of-incarnation with no purge or token reuse; browser
storage eviction/clearing and arbitrary restore are not recovery guarantees.
