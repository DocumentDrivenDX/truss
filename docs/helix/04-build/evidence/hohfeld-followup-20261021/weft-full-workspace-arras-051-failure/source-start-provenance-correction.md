# Selected Weft candidate source-start provenance correction — 2026-10-22

This separate note clarifies the starting checkout state for the preserved
candidate attempt in `original-candidate.log`. It supplements the earlier
packet's simplified `selectedSourceRevision` field; it does not alter or replace
that receipt, either original full-suite log, or the captured test patch.

The candidate command began with Git `HEAD` at
`874e0f67255be297ee321024e8f6d180c668f951` and four uncommitted B-001 paths:

| Path | Resulting Git blob in `e43b7a8c` and `84bde6e6` |
| --- | --- |
| `spikes/b001/README.md` | `184d7d605faa20cded36e5ca43b30b8d7cb096e9` |
| `spikes/b001/check_native.py` | `fb1e16d8f8f042eaee53f8196f61d3403cf634c8` |
| `spikes/b001/core/tests/boundary.rs` | `4b6c0ca42f400204c0c8736dc6beb1cb3966ee6b` |
| `spikes/b001/fixtures/cases-umf070.json` | `6da3729cb533ca8075f9fe7ed43164b945c8145a` |

The exact four-path working-tree patch captured for that run is preserved as
`source-start-b001.patch` (SHA-256
`f278a687caebb0b00b76a8888694a1fd22eecb82b24e3f7a49d47b57770f1461`). Its
three modified-file target blob IDs match the later `e43b7a8c` commit; the
added UMF 0.7 fixture has SHA-256
`5d13b1d0d77074193e678321406f57a9ce34e49cd413649f0f7f7210262c6306`, matching
the committed file. The four paths in `e43b7a8c` are byte-identical to those
in `84bde6e6`.

During the still-running candidate invocation, the dirty B-001 changes were
committed as `e43b7a8c68d870a88cba15349b63884dd64d578f`. `HEAD` then advanced
to `84bde6e6f1ebe406cf01f4b344c977739dbe0180`; that subsequent commit changed
only `.github/scripts/configure_ubuntu_apt_sources.py` and the two workflow
files. A Git comparison confirms there is no difference between `e43b7a8c`
and `84bde6e6` in `Cargo.toml`, `Cargo.lock`, `crates`, `spec`, `vendor`,
`.cargo`, Rust toolchain declarations, or `docs/helix/02-design/contracts`.
The invocation's source-start identity is therefore `874e0f67` plus the four
captured B-001 paths, not a checkout that began at `84bde6e6`. Its candidate
result remains failed as recorded in the original log (SHA-256
`826d66f5c9baa2f7fe88ba685d34d8b5f30326ae99da8084a3820f33e593dbe3`).

This clarification makes no new suite-pass, binary, freeze, cohort, or release
claim. The later full-suite qualification at `56d5507c` and source freeze at
`55715373` remain separately evidenced.
