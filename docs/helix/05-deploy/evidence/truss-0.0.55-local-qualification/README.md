# Truss 0.0.55 local qualification

This packet records the local candidate evidence for package source commit
`43b863053925d376030792c922b7098134890853`, with version-aligned release
metadata at `71c3e14bbb97fc9f1c938587d535ab69d2032ba0`. It is not a publication receipt.
No v0.0.55 tag, GitHub release, hosted release workflow or PyPI upload has
occurred.

## Candidate artifacts

The local wheel and source archive are listed in
[`local-artifact-SHA256SUMS`](local-artifact-SHA256SUMS):

| Artifact | SHA-256 |
| --- | --- |
| `umf_truss-0.0.55-py3-none-any.whl` | `156df20641d8c4fee6d836c6b29266a0a7eb3b1299c407e430ce0d2c07a79805` |
| `umf_truss-0.0.55.tar.gz` | `be2964a6f17064fd2061e46882f745c6dc730915f488293eb70dc203b9dd5c26` |

The later documentation and fixture metadata commits do not change the wheel
payload. These are local build hashes, not public registry hashes. A passive
bundle verifier compares the current wheel and sdist production sources against
the candidate assets.

## Focused timeout tests

[`focused-timeout-tests.json`](focused-timeout-tests.json) records four passing
tests from the packaged timeout module and one supplementary pure parent
deadline check, all against the installed exact .55 wheel under macOS arm64 and
Python 3.12.14. The supplementary check freezes the clock and observes a
5-second remaining parent deadline clamp a requested 180-second install
override before SQL. Its source is outside `packages/python`, so the qualified
wheel and sdist remain unchanged. These focused tests are not the full Truss
test suite.

[`qualification-manifest-macos.json`](qualification-manifest-macos.json) names
the current local target. [`component-reuse-binding.json`](component-reuse-binding.json)
binds the current wheel/source, the published .54 receipts, and the exact
changed component set. The .54 migration, HF and managed-grants results remain
historical execution evidence; none is labeled as a current .55 suite pass.
All 754 managed-grants input-basis files were compared and are byte-identical,
but that does not carry its old pass across the changed host/installation code.
The changed .55 native code is covered only by the focused timeout checks and
the R61 path described below. No Truss Linux native qualification is claimed.

## Fresh Truss source and ACK evidence

The Ashlar R61 local qualification installed the exact Truss 0.0.55 wheel into
its selected runtime and exercised the public fresh installation, acceptance,
source/consumer registration, native feed and protected ACK path. It produced a
four-role Delta 0.4 publication, native Weft read results, a continuation ACK,
and an original Truss graph release/custody pair. A separately bounded
GraphFrames-only run then validated the retained release bytes, full-row parity
and directed path counts. The exact Ashlar closeout is copied byte-for-byte as
[`ashlar-r61-closeout.json`](ashlar-r61-closeout.json), SHA-256
`8e45c1ccbeed123749ec4353af2d12ee6cc2dd0f48f2658109c55b10094fac1f`. The
[GraphFrames report](graphframes-report.json) is SHA-256
`94f82de749ed2d9169be87c4a159bc2dcb044f7fbeabac0a6acb2ff9cb6183cf`.

The closeout is intentionally explicit about run composition: the source
worker completed publication, protected ACK, owner export and cleanup, then
exited at the GraphFrames custody adapter. After that adapter was corrected,
the bounded GraphFrames-only action passed against the retained immutable
release/custody bytes. No source, ACK or original Delta operation was replayed.
The worker's native Weft results were returned in memory but not serialized into
a completion receipt after the later adapter exception; the closeout records
the result values and this evidence limit.

## Qualification boundary

This evidence covers the selected local macOS ARM64/Python 3.12.14,
PostgreSQL 18.6.1 and fresh-install profile only. It does not claim the full
Truss suite, exact-tag CI, general platform support, managed-service or
production acceptance, backend termination on timeout, safe reuse after
cancellation, historical upgrade/recovery, or public PyPI/GitHub delivery.
The fresh-install-only baseline and its existing refusals remain unchanged.

## Local bundle verification

The local bundle at
`/private/tmp/truss055-local-publish-run/local-release-bundle` contains the
candidate assets, exact .54 release receipts/assets, current qualification
receipts, and a checksum manifest. Verify it without network or database access:

```sh
python3 scripts/release-qualification/verify_local_bundle.py \
  --source-root . \
  --bundle-root /private/tmp/truss055-local-publish-run/local-release-bundle
```

This validates hashes and source relationships only. Final release pins and
publication remain pending the separate managed Ashlar gate and owner review.
