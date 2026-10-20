# Published Truss 0.0.43 verification

PR #18 merged the exact reviewed candidate tree. Both candidate and tagged release matrices passed their selected Linux x86_64 and macOS ARM64 workflows. These receipts bind the published commit, all 413 runtime payloads in wheel and sdist, complete 421-member wheel RECORD, metadata, exact release pins and nine checksummed assets. The checksum manifest itself and all nine assets also passed fresh unauthenticated public downloads.

The immutable source tag retains the pre-publication notes; the public GitHub release notes and the current release record contain the verified delivery. Earlier failed and local development receipts remain unchanged. This is selected-workflow evidence, not full discovery, Windows, managed-service or upgrade qualification. Full historical three-schema and eleven-case stress benchmarks were not repeated; selected registration, replay and public workflows were.

To repeat the offline artifact checks after downloading the public release assets into a fresh directory, copy `delivery-result.json` into that directory and run Python 3.11 or later:

```sh
git fetch origin refs/pull/18/head
git rev-parse FETCH_HEAD # Must equal a2b9c8a1fc98a34528a32492b7ca5ad4a1bad955
python docs/helix/04-build/evidence/design-audit/embedder-e0-e1-20261020/v0.0.43-published/verify-release.py --repo "$PWD" --delivery-dir /path/to/fresh-downloads --qualified-ref a2b9c8a1fc98a34528a32492b7ca5ad4a1bad955
```

The verifier uses pinned Git source, does not install or extract archives, and makes no network or GitHub changes. `source-binding.json` records candidate/merge tree equality; `public-download-verification.json` records the separate unauthenticated HTTP checks.
