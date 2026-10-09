# Truss microsite schema browser evidence

The Model page embeds the actual UMF schema browser, pinned to owner revision
`e3555b9aac9e4c3caa952203958c4b0c33cdf519`. Its JavaScript, CSS, and logo are
copied without changes from the owner's committed build. The Truss shell supplies
one catalog entry containing the exact current structural projection 0.3 of native
layout 0.15. The generated asset manifest records source and asset hashes.

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
and mobile page width. It does not establish native enforcement, complete native
DDL equivalence, or production publication. Signed Markdown page sources were
not changed; the insertion is in the page layout.
