# Scoped independent cleanup review

No remaining blocker found for the stated controlled lost-creation-response experiment. Source and retained evidence were audited without executing Docker or native tests.

All 795 unique source pins match current bytes and the exact ZIP entry set. They include the final native wrapper and its `cdb1c711` receipt. The shim performs real Docker creation, retains its actual ID/arguments/cidfile, then deliberately returns nonzero before the wrapper assigns that ID. The wrapper fails as required (exit 1), recovers only the fresh exact name plus owner label, and records removal of `0c438b7c07d7c8a2d5f1f789ead70d43a3014faab7c58c71f061c06c0a78196d` with exit 0. The retained independent real-CLI inspection returns exit 1, an empty result array, and a matching `no such object` diagnostic.

The audit checked the created-ID/cidfile/failure-receipt/cleanup correspondence, shim digest, control log, independent inspection, current source bytes and every ZIP entry. Receipt SHA-256: `299d88c2e28d82518959100b8ca32f038b7823977d96b5035e2928707982dd2f`. Detailed hashes are in `astra-audit.json`.

The earlier `4f566ee7` control failed a case-sensitive diagnostic check after actual successful removal; it remains historical. This final result establishes the controlled nonzero-response path after completed creation. It does not establish every asynchronous Docker/daemon/network timeout outcome or any native security, issuer, report, or acceptance qualification.
