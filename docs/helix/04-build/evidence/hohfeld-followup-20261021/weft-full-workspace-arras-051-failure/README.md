# Selected Weft 0.4.51 full-suite attempt — 2026-10-22

This packet preserves the selected-source full-workspace attempt made before
the B-006 test-only correction. The selected Weft checkout was at
`84bde6e6f1ebe406cf01f4b344c977739dbe0180`, including the B-001 historical
fixture harness restored in `e43b7a8c`. The attempted qualification used
macOS ARM64, Rust 1.90.0, locked dependencies, offline Cargo resolution and
`/private/tmp/weft-arras-051-full-target`.

The candidate invocation was:

```sh
cargo test --workspace --features weft-runtime/truss-postgresql-candidate,weft-runtime/ashlar-databricks-candidate,weft-runtime/test-original,weft-runtime/test-third,weft-postgresql/conformance-original --locked --offline
```

The original captured output is `original-candidate.log` (SHA-256
`826d66f5c9baa2f7fe88ba685d34d8b5f30326ae99da8084a3820f33e593dbe3`). It
contains 42 completed result groups: 1,012 passed and 1 failed, with no
ignored or filtered tests. The sole failure is
`ashlar_tests::ashlar_feature_controls_registration_and_retains_public_artifact`
in `crates/weft-runtime/src/lib.rs`. The retained B-006 compile request is
UMF 0.7.0, and the current source envelope returns `WFT-INPUT`; the old
test expected the historical compiled response. This exposed a stale
`cfg(test)` expectation, not a compiler behavior regression. The captured
failure shows the actual blocked response and no SQL.

The test-only correction is preserved in
`test-only-ashlar-expectation-correction.patch` (SHA-256
`cf718d06a6d7e91efdb8efd04598eec0b64bcecb40342e8b051f276ae3576f71`) and is
committed in selected Weft as `56d5507c` (`Correct historical B-006 runtime
test expectation`). It keeps the original UMF 0.7 fixture and historical
golden intact, asserts the current `WFT-INPUT` refusal and absence of SQL, and
changes only a `cfg(test)` module. The current selected full suites must still
both pass before a new source freeze or release build is accepted.

The qualified invocation was:

```sh
cargo test --workspace --features weft-runtime/truss-postgresql-qualified,weft-runtime/ashlar-databricks-qualified,weft-runtime/test-original,weft-runtime/test-third,weft-postgresql/conformance-original --locked --offline
```

`original-qualified-cancelled.log` (SHA-256
`431cc820cb5d72b1373f92a6689acbfdf392bcb1e89494f2371aeb893583e293`)
ends while tests were still running. It contains 29 completed result groups
and 682 passing tests before cancellation. The parent confirmed process group
27993 was stopped deliberately. This is an incomplete run, not a pass; no
terminal Cargo result was captured.

## Release-candidate disposition and next build

The earlier Weft Mac wheel `weft_sql-0.4.51-cp39-abi3-macosx_11_0_arm64.whl`
(`a21faed75304e730c7cc9782394001be2ba1772b429e587f0d1910c2269dabbe`, source
freeze `86c092178bb8ca1a0d84edfebc175009d8862493`) and the Linux artifacts
from packaging run `39811059843` remain historical evidence. They are not
active final-release candidates after this follow-up. Their source, wheel and
receipts remain unchanged. No replacement binary, updated Truss compiler
cohort, hosted overall conformance success or public release is credited by
this packet.

After both repaired selected-source full-suite variants pass, create a new
source freeze. Rebuild the Mac wheel on the same macOS ARM64 host into paths
keyed by that freeze so the previous `a21` wheel and `86c` receipts cannot be
overwritten. The existing
release workflow pins Rust 1.90.0 and maturin 1.9.6 and builds
`crates/weft-python/Cargo.toml` with `--release --locked`; a safe local
reproduction should use a dedicated target directory and a fresh output path:

```sh
SOURCE_FREEZE=$(git rev-parse HEAD) # run only after committing the qualified freeze
FREEZE8=${SOURCE_FREEZE:0:8}
export CARGO_TARGET_DIR="/private/tmp/weft-arras-051-final-target-${FREEZE8}"
export CARGO_INCREMENTAL=0
WHEEL_OUT="/private/tmp/weft-arras-051-final-macos-${FREEZE8}/dist"
MAC_OUT="/private/tmp/weft-arras-051-final-macos-${FREEZE8}"
mkdir -p "$WHEEL_OUT"
maturin build --manifest-path crates/weft-python/Cargo.toml --release --locked \
  --out "$WHEEL_OUT"
WHEEL=$(find "$WHEEL_OUT" -maxdepth 1 -name 'weft_sql-0.4.51-*.whl' -print -quit)
test -n "$WHEEL"
python3 -m venv "$MAC_OUT/venv"
"$MAC_OUT/venv/bin/python" -m pip install --no-deps "$WHEEL"
"$MAC_OUT/venv/bin/python" scripts/release/verify-wheel-packaging.py \
  --wheel "$WHEEL" --version 0.4.51 --output "$MAC_OUT/packaging.json"
```

The separate target and output roots are new for this freeze; do not reuse the
old `/private/tmp/weft-arras-051-final-wheel-build.log` or packaging directory.
The packaging check verifies every wheel `RECORD` digest, package
metadata/ABI/notices, the installed module against the archive module, and
installed `weft/__init__.py` against the archive. Record the wheel SHA-256 and
embedded native-module SHA-256 from `packaging.json`; then require Truss's
exact installed-consumer checks to use that same wheel and source before
adoption. Keep the old Mac artifacts intact. Rebuild Linux only from the
new freeze through the source-bound packaging workflow, then update Truss's
active selected source and Mac/Linux cohort identities from those actual
artifacts. Re-run the exact installed Truss and release gates against the new
tuple. This plan records required work; it does not claim those commands or
gates have run.
