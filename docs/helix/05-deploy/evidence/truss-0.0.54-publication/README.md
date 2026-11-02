# Truss 0.0.54 public delivery

[GitHub v0.0.54](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.54)
and [PyPI umf-truss 0.0.54](https://pypi.org/project/umf-truss/0.0.54/)
deliver the standalone canonical `LocalTimestampValue` carrier from source
`da07d0b6e45f3b4bd0a918ebedcebd086a5b9b55`.
Existing value, container, import and native profiles retain their refusals.
Temporal native storage, admission and query execution remain unqualified.

## Exact qualification and publication

- [Exact-tag Linux run 41520042911](https://github.com/DocumentDrivenDX/truss/actions/runs/41520042911)
  passed the complete installed-runtime workflow, including the carrier's 31
  checks, six fresh-baseline/refusal controls, 62 independent HF cases, 174
  managed-grant tests and the required original public workload. Optional
  stress and scale campaigns were not selected.
- [Trusted PyPI run 41524935908](https://github.com/DocumentDrivenDX/truss/actions/runs/41524935908)
  passed source verification, actual OIDC upload, served-byte verification and
  a fresh Linux query/carrier consumer.
- The [independent receipt](receipt.json) verifies all 18 immutable GitHub
  assets, their SHA256SUMS and GitHub digests, actual PyPI archive downloads,
  exact tag/source correspondence and unchanged 0.0.53/0.0.52 asset inventories.
  The public wheel/sdist equal the successful tag's original package artifact.

| Public archive | SHA-256 |
| --- | --- |
| `umf_truss-0.0.54-py3-none-any.whl` | `4aebc56e92fdbde6714d9b811860707d2ffc9b0edbc63cc91e9dc3488c042b52` |
| `umf_truss-0.0.54.tar.gz` | `28930d23b7783876c36f6d92594b03d2b043a4ad45f6f291f51a8c5b6d0682f0` |

## Original evidence

[Carrier qualification](standalone-carrier-qualification.json) binds the 31
installed checks to this source and wheel. [Baseline qualification](baseline-qualification.json)
and its [original cleanup](baseline-cleanup.json) record the six current-only
controls and confirmed PostgreSQL shutdown: pg_ctl status3, no postmaster PID.
The immutable release retains the original HF and managed-grant receipts and
evidence archives; their counts, source/wheel bindings and cleanup were checked.
[Public workload status](original-public-workload-status.json) retains the
actual successful source-bound result.

The original [source verification](pypi-source-receipt.json),
[OIDC publication](pypi-publication-receipt.json) and
[Linux public consumer](pypi-consumer-receipt.json) receipts are preserved
byte-for-byte. [Wheel correspondence](wheel-correspondence.json) compares the
actual immutable 0.0.53 wheel with the qualified 0.0.54 wheel: only
`truss/__init__.py` and `truss/contracts.py` change. The other 448 payloads,
including native SQL, ABI1.2, migration baseline and embedded owners, are exact.

## Additional fresh public consumer

The [local consumer receipt](fresh-public-consumer.json) records an uncached
public-index UV installation on macOS ARM64, all 31 checks passing, and all 450
Truss payloads matching the verified public wheel. The installed compiler's
payloads match the actual public archive of its existing frozen Mac cohort.
This is standalone-carrier/refusal evidence; no Mac native smoke is claimed.

The initial standard pip installation also completed successfully. Its
[raw report](fresh-public-pip-report.json.gz) records only official PyPI file
URLs, and its actual 450 installed payloads and compiler hash also match.
The [original UV test receipt](fresh-public-uv-tests-original.json) is retained;
the local consumer receipt explicitly corrects its provisional statement that
the first install had been stopped. Test counts and outcomes are unchanged.
The [UV installation log](fresh-public-uv-install.log.gz) is retained separately.

## Remaining temporal feature

The genuine snapshot at `8bc82edd270a0043cd48ef8073fb2ef755eb017b` remains
retained locally and remotely until owner qualification lands. Its
[preservation record](temporal-snapshot-preservation.json) separates the
historical push workflows triggered by restoring its absent ref from this
release's qualification. Neither establishes temporal acceptance.
The [current integration plan](../../../04-build/temporal-current-baseline-plan.md)
continues to govern the missing UMF/Weft interfaces and Truss native composition.
