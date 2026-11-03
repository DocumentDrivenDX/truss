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

## Assemble a final release asset set after the managed gate

After the managed Ashlar result and final owner review, the release owner should
make a fresh release-asset directory from the verified candidate assets. Add
final `release-pins.json`, `SHA256SUMS`, current receipts, the macOS
qualification manifest, the component-reuse binding, and the exact published
.54 receipts required to support the approved reuse statement. Keep each
receipt's original source commit, wheel hash, and platform. Do not substitute
old receipts for current evidence on changed host/installation behavior.

Before tagging, verify the final pin's version, source commit, distribution,
wheel/sdist/HF hashes, runtime and migration manifests, current macOS scope,
and historical-receipt references against the contents of that directory.
Keep the candidate wheel and sdist hashes listed in the release notes unchanged.

## Create the GitHub release locally

Only after that final asset set passes review, the release owner can use the
GitHub CLI to create the tag and release from the approved source commit and
attach the staged files:

```sh
gh release create v0.0.55 \
  --target <approved-source-commit> \
  --title "Truss v0.0.55" \
  --notes-file docs/helix/05-deploy/releases/v0.0.55.md \
  /path/to/final-release-assets/*
```

The repository's release workflow is `workflow_dispatch` only; this local
command does not dispatch it. Verify the published asset digests and immutable
release state before any separate PyPI upload. This document does not authorize
or perform those external actions.
