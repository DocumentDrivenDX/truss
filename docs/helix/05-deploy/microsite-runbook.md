---
ddx:
  id: truss.microsite-runbook
  type: runbook
  activity: deploy
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.design-system
      kind: informed_by
---
# Truss microsite runbook

Publish four model-primary, build-signed source pages through Hugo 0.167.0 and GitHub Actions to https://documentdrivendx.github.io/truss/ . The owner explicitly requested source signing and publication. The site carries no runtime credentials or database data.

## Update

Edit `website/content/` and review against the brand voice and source evidence. Main publication seals all four pages with pinned Innsigle using `seal --all --role build`, `.innsigle/colo.json` and their public URIs. For a local preview, run the same sealing command before verification. Never relabel model-written material human-authored. The build private key is held locally in `.innsigle/private/build.priv.pem` (mode0600, directory0700), excluded by `.gitignore`. The same build key is stored as the encrypted repository Actions secret `INNSIGLE_BUILD_KEY` in `DocumentDrivenDX/truss`, explicitly authorized by the owner on 2026-10-20. Its public key is registered with role `build`; no human-authorship or human-key-recognition claim is made. Verify all sources, build with `--panicOnWarning`, and run the link/seal checker before publishing.

## Delivery

The Pages workflow checks the exact four-page inventory and `composition: model-primary` declarations on every run. Pull requests build and check links without signing, secret access or deployment. Main pushes and manual main runs seal sources with `INNSIGLE_BUILD_KEY`, verify signatures, build, check links/current state/seal coverage, package public issuer files and deploy using Pages/OIDC permissions. The secret is exposed only to the main signing step. GitHub Pages must use the Actions source. The four current model-primary pages use the build key; no human key is used. Generated attestations are published with the site; CI does not commit them back to source.

## Failure and recovery

Invalid or missing signatures block publication. A missing or mismatched build key blocks the signing step; check the repository secret and registered public key before retrying. Review changed source before publishing; main CI then re-seals it automatically. Build errors and broken subpath links block publication. A failed deployment leaves the previous version available. Roll back by reverting the microsite change and allowing the same verification workflow to redeploy; do not revert unrelated product changes.

## Verification

Inspect desktop and narrow layouts, keyboard navigation and the four public routes. Confirm live issuer and attestation publication. Source signatures do not cover templates/CSS/rendered bytes. Static delivery has no RUM (real-user monitoring) or page-error telemetry; browser console and layout inspection provide bounded release checks. Web Vitals are not measured and no performance score is claimed.
