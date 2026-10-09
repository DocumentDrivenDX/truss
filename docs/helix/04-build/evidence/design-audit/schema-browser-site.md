# Truss microsite schema browser evidence

The Model page embeds the actual UMF schema browser, pinned to owner revision
`1f7b5f5d2a355c4b476e3a96b289b9048f03f567`. Its JavaScript, CSS, and logo are
copied without changes from the owner's committed build. The Truss shell supplies
one catalog entry containing the exact current structural projection 0.6 of native
layout 0.16, including the separately uncomposed configuration and migration
adjuncts. The generated asset manifest records source and asset hashes.

Reproduce from the Truss checkout:

```sh
python3 scripts/build-umf-schema-browser.py --check
hugo --source website --destination public --panicOnWarning
python3 website/scripts/check_site.py website/public --require-seals
bun scripts/check-schema-browser.ts
```

The generator reads the pinned commit from `/Users/erik/Projects/umf`; regeneration
requires that commit locally. The browser verifier uses that checkout's Playwright
installation. `schema-browser-site.json` records real Chromium evidence on the
Hugo output under the production `/truss/` URL prefix: embedded inspection,
current declaration_module field navigation, deep links, exact source download,
byte-exact retained native/configuration/migration downloads, and mobile page
width. It does not establish native enforcement, complete native
DDL equivalence, or production publication. Signed Markdown page sources were
not changed; the insertion is in the page layout.

A fresh owner fetch on 2026-10-09 still resolves `origin/master` to the pinned
revision. `build-umf-schema-browser.py --check` confirms all selected static assets
and exact catalog source bytes. This refresh corrects stale evidence prose; it
does not claim a new Chromium run or publication. The existing JSON receipt
records Chromium 153.0.8010.12 and 532 inspected definitions.

A subsequent actual Chromium run adds migration FK navigation to the receipt.
From `layout_migration_receipt`, its core `physical-fk` parent reference opens
`source_epoch_registry`. The `installation_id` and `original_source_epoch`
source fields independently open `source_epoch_registry.installation_id` and
`source_epoch_registry.source_epoch`, with exact qualified deep-link assertions.
This verifies the existing structural references, not native FK enforcement,
portable key interpretation or an installed upgrade. The owner-asset check and
Hugo build also pass. No production site was published by this run.
