# Truss 0.0.55 local publishing workflow

This procedure stages the exact locally qualified artifacts without invoking
GitHub Actions. The current bundle is for review only: the managed Ashlar gate
has not completed, so it is not a publishable release set and no tag/release
command should run yet.

## Verify the staged candidate

From the current reviewed Truss checkout (package source baseline
`43b863053925d376030792c922b7098134890853`; release metadata baseline
`71c3e14bbb97fc9f1c938587d535ab69d2032ba0`):

```sh
python3 scripts/release-qualification/verify_local_bundle.py \
  --source-root . \
  --bundle-root /private/tmp/truss055-local-publish-run/local-release-bundle
(cd /private/tmp/truss055-local-publish-run/local-release-bundle/assets && \
  shasum -a 256 -c SHA256SUMS)
```

The verifier checks the exact wheel and sdist against production source, current
and prior runtime package members, the native and migration manifests, the
published 0.0.54 receipt checksums, the 754-file grants input-basis comparison,
and the HF archive's exact metadata-only delta. It also checks the current
installed-wheel carrier/timeout receipts and Ashlar R61 wheel binding. It does
not run tests, use a database, create a tag, or publish assets.

The component-reuse binding and macOS manifest are the review record for this
subset. The .54 HF, migration and grants test results remain historical; they
must be bundled under their original identities rather than rewritten as .55
passes. The current macOS result is separate from Ashlar's managed Linux trial
and does not claim Truss Linux native qualification.

## Review the prepared local asset set

The private review bundle contains the four qualified files and the candidate
`release-pins.json`; its `assets/SHA256SUMS` covers all five files.
The repository-side `dist/SHA256SUMS` and local qualification checksum record
the same names and hashes. These are review inputs only. They do not create a
tag, draft, release, or publishable status.

## Refresh the release asset set after the managed gate

After the managed Ashlar result and final owner review, the release owner should
make a fresh release-asset directory from the verified candidate assets. Refresh
`release-pins.json` and `SHA256SUMS`, then include current receipts, the macOS
qualification manifest, the component-reuse binding, and the exact published
.54 receipts required to support the approved reuse statement. Keep each
receipt's original source commit, wheel hash, and platform. Do not substitute
old receipts for current evidence on changed host/installation behavior.

Before tagging, verify the final pin's version, source commit, distribution,
wheel/sdist/HF hashes, runtime and migration manifests, current macOS scope,
and historical-receipt references against the contents of that directory.
Keep the candidate wheel and sdist hashes listed in the release notes unchanged.

## Stage and verify a GitHub draft locally

Only after the final asset set passes review and its tag points to the approved
source commit, the release owner can stage a GitHub draft. Use an explicit
repository because this isolated checkout may not have a GitHub remote:

```sh
gh release create v0.0.55 \
  --repo DocumentDrivenDX/truss \
  --target <approved-source-commit> \
  --verify-tag \
  --draft \
  --title "Truss v0.0.55" \
  --notes-file docs/helix/05-deploy/releases/v0.0.55.md \
  /path/to/final-release-assets/*
```

Download the draft assets into a new empty directory. Confirm the draft state,
then verify every downloaded asset against the final bundle checksum manifest
and compare `release-pins.json` byte-for-byte with the staged pin file:

```sh
gh release view v0.0.55 --repo DocumentDrivenDX/truss --json isDraft,assets
gh release download v0.0.55 --repo DocumentDrivenDX/truss --dir /path/to/empty/draft-readback
(cd /path/to/empty/draft-readback && shasum -a 256 -c SHA256SUMS)
cmp /path/to/final-release-assets/SHA256SUMS /path/to/empty/draft-readback/SHA256SUMS
cmp /path/to/final-release-assets/release-pins.json /path/to/empty/draft-readback/release-pins.json
```

Only after the downloaded draft matches the reviewed asset set should the
release owner publish it:

```sh
gh release edit v0.0.55 --repo DocumentDrivenDX/truss --draft=false
```

Verify the final asset digests and immutable release state before any separate
PyPI upload. The repository's release workflow is `workflow_dispatch` only;
this local process does not dispatch it.
