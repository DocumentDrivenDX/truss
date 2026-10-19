# Browser prototype

This prototype is not distributable. `buildBrowserAssets` explicitly refuses to
build because genuine current UMF 0.10 action and local compiler owners are not
available. Earlier owner bundles are not a replacement, and action execution is
not qualified for the current source format.

The catalog preparation source accepts only UMF `0.10.0`. It preserves original
source bytes and diagnostics, and derives Record/member/key declarations from the
actual validated source. Its prototype subset is one rootless Record with
required singular String fields and a single primary key. Relationship declarations
are outside that subset. The default browser fixture is a derived current-format
source; its provenance sidecar records the original and derived hashes.

Focused checks execute catalog preparation against that fixture, verify refusal
of older source markers, and strictly typecheck the browser source. They do not
qualify PGlite registration, object mutation, action execution, recovery or a
published browser distribution. Current installed Python/native qualification is
a separate delivery path.

The earlier cross-provider seal-upgrade check is retired. Historical code,
owner artifacts and evidence remain in Git; there is no supported old-installation
upgrade route or selectable old-format builder. A future browser distribution
must use actual current action/compiler/provider implementations and receive its
own lifecycle, correctness and browser qualification.
