# Published numeric release — 2026-10-13

Truss v0.0.2 source52e0476e9b50f93b93268b94aa7653e110a3c7b6 is published with
wheel, sdist, SHA256SUMS and release-pins.json. Release workflow38426428948 passes
package build, installed adopter + both UMF0.7/0.8 numeric workflows on
Linuxx86_64/macOSarm64, then publication.

Matching Weftv0.4.4 source25c9938ce178ec0dfa8c57aabdb26721088bed08 is published.
Workflow38425316938 passes all five ABI3 wheel builds/smokes and publication:
Linuxx86_64/arm64, macOSx86_64/arm64, Windowsx86_64. Backend0.4.9 targets Truss.39.

Actual public wheel/sdist checksums and source/runtime/backend pins were
downloaded and verified. Installed public Truss and macOSarm64 Weft wheels pass
both basic numeric workflows locally (2tests18.362s). No prototype wheel was
substituted. The release preparation and completed numeric source were reviewed
with Astra Ultra. Upstream Ashlar also reports its original typed source→Delta→
Weft consumer workflow preserving9007199254740993/1.2300; this is consumer-reported
integration evidence, not a Truss-owned managed-service qualification.

Release links:
- https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.2
- https://github.com/DocumentDrivenDX/weft/releases/tag/v0.4.4

Next feature tranche is typed business keys, retaining original source/owner
semantics, string reservations and historical replay. It is not in v0.0.2.
