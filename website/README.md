# Truss microsite

Build: `hugo --source website --destination public --panicOnWarning`.
Check: `python3 website/scripts/check_site.py website/public --require-seals`.
Verify sources: `node /path/to/innsigle/src/cli.mjs verify --all`.

Four authored pages use shared layouts and an original inline structural graphic.
Source declarations are model-primary; the signature covers Markdown, not the generated site.
Pinned Innsigle revision: 4185eb56beb7b52beaa4a00c2fc897f93d44b939.
Page changes require individual re-sealing with `.innsigle/colo.json` and the public page URI.
Private keys remain in 1Password and never enter CI. CI verifies and deploys main through GitHub Actions.
