# Deploy

Document release readiness, deployment checks, monitoring, and operations.

GitHub release archives and the public PyPI channel are defined. Executed
registry gates and their immutable source identities are recorded below.

## Public PyPI distribution

Owner direction on 2026-10-26 requires the qualified Python distribution on
public PyPI, with future released versions published automatically. The
`publish-pypi.yml` driver runs on the default branch and consumes exact existing
GitHub release assets after the release producer succeeds. Explicit backfills
require the release tag, its source/metadata commit and SHA256SUMS digest.
No existing version is rebuilt, renamed or retagged for the index.

The validator checks tag identity, release pins, GitHub asset digests, checksum
entries, archive names/versions and dependency metadata. A separate main-only
`pypi` environment grants OIDC upload authority to that workflow without stored
tokens or a reviewer per release. A version must be absent or already contain
exactly the same files and bytes. Conflicts and registry errors fail closed;
only initial absence is retried within a bounded visibility wait.

A job without OIDC verifies a fresh public-index installation and retains its
receipt separately from the upload/byte receipt. Configuration and local tests
do not prove publication. The approved publisher is configured, and actual
public-byte and installed-consumer receipts are retained in the executed
publication record below. This changes distribution, not runtime
semantics, platform qualification or the latest-only support policy.

## Executed PyPI publication

On 2026-10-26, [run 40361086218](https://github.com/DocumentDrivenDX/truss/actions/runs/40361086218)
published the unchanged `truss-toolkit==0.0.50` wheel and sdist through GitHub
Actions OIDC. Exact PyPI-served bytes and a fresh public-index `[query]` install
passed. Source, publication, consumer and verified artifact-digest records are
retained under `evidence/pypi-0.0.50/`. The configured main-only publisher
automatically consumes successful qualified tag/release producers.

Every public registry upload, including historical backfills, executes in
GitHub Actions bound to the verified immutable tag and GitHub release. Local
preparation and verification do not authorize a local registry upload.
