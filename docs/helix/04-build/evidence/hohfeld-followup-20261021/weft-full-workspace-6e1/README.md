# Weft full local workspace verification — 2026-10-22

Both full Rust workspace variants pass on macOS ARM64 with Rust 1.90.0, locked dependencies, and offline Cargo resolution. The candidate run at source commit `6e1b64a750c6db15c52ad2aac9ba9afc0b38d02a` completed 62 result groups with 1,048 passed, 0 failed, 0 ignored and 0 filtered in 832.738s. The qualified run completed 62 groups with 1,049 passed, 0 failed, 0 ignored and 0 filtered in 730.790s. Both command exit codes are 0.

The exact invocations and wall times are retained in `original-results.json`. The complete original candidate and qualified logs and the independent parsed group counts are preserved byte-for-byte. Their SHA-256 values are in `receipt.json`; `original-counts.json` records the independently reconciled per-group totals. The subsequent Weft integration commit `cc694344da31af76ef6b97e572d20a8347989bdd` changed only workflow bootstrap files, not Cargo source or build inputs.

This closes the local full-workspace candidate and qualified Rust test gate for source `6e1b64a750c6db15c52ad2aac9ba9afc0b38d02a`. It is local macOS ARM64 evidence only. It does not establish hosted Linux conformance, browser/native packaging, publication, Truss installed-wheel qualification, or public release. Those gates remain separately required; do not infer their result from these Cargo runs.
