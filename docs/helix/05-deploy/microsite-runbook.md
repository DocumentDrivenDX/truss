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

Publish four curated, signed source pages through Hugo 0.167.0 and GitHub Actions to https://documentdrivendx.github.io/truss/ . The owner explicitly requested source signing and publication. The site carries no runtime credentials or database data.

## Update

Edit `website/content/`, review against the brand voice and source evidence, then seal each changed page with pinned Innsigle using `.innsigle/colo.json` and its public URI. Never relabel model-written material human-authored. Keep private keys in 1Password. Verify all sources, build with `--panicOnWarning`, and run the link/seal checker before publishing.

## Delivery

The Pages workflow builds pull requests without deployment. Main pushes and manual main runs verify signatures, build, check links/current state/seal coverage, package public issuer files and deploy using Pages/OIDC permissions. GitHub Pages must use the Actions source. CI never reads signing keys or silently re-signs copy.

## Failure and recovery

Invalid or missing signatures block publication. Re-seal only after reviewing the changed source. Build errors and broken subpath links block publication. A failed deployment leaves the previous version available. Roll back by reverting the microsite change and allowing the same verification workflow to redeploy; do not revert unrelated product changes.

## Verification

Inspect desktop and narrow layouts, keyboard navigation and the four public routes. Confirm live issuer and attestation publication. Source signatures do not cover templates/CSS/rendered bytes. Static delivery has no RUM (real-user monitoring) or page-error telemetry; browser console and layout inspection provide bounded release checks. Web Vitals are not measured and no performance score is claimed.
