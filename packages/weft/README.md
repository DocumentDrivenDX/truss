# Experimental Truss query host for Weft

`createQueryEngine(compiler, binding, host?)` compiles Weft SQL against exact original UMF modules and a trusted owner-supplied binding. `compile` retains the original response and immutable plan; `execute` admits only plans issued by that engine. Parameters use Weft's named `{family,value}` exact text transport. No compiler, SQL rewriting or semantic validator is duplicated in Truss.

The portable package has no host I/O. An initialized Weft WASM compiler can implement its `Compiler` interface. The separate Bun package loads the exact pinned Rust executable using build evidence. Host registration supplies every original obligation handler, one authorized affine read context, exact decoder, and context verification before checks and before result release. Unknown obligations or parameter meaning refuse before context acquisition. Missing native host refuses explicitly. Hosts must additionally qualify original resource/transport/cancellation and authority obligations; callback interfaces alone do not prove them.

This is a new experimental convenience API, not a claim that CONTRACT-007's complete `executeInTransaction` facade or the protected Truss engine is implemented. The selected compiler profile currently qualifies a fixture layout, not reference layout 0.12. The upstream fixture in tests is explicitly synthetic. No fixture IDs are accepted catalog IDs and no storage installation/readiness is performed.

## Reproduce

Build only committed upstream source, excluding another chat's edits:

```sh
python3 scripts/build-weft-source.py /path/to/weft /empty/build/directory /path/to/weft-toolchain
TRUSS_WEFT_BUILD=/empty/build/directory bun test tests/weft
TRUSS_TSC=/path/to/tsc bun scripts/typecheck-weft.ts
```

The build uses locked offline dependencies and `truss-postgresql-qualified`, never `--all-features`. It records source archive, lockfile and executable hashes. Tests use the actual compiler and independently exercise host refusal/order; the in-memory host test is not native qualification. Packages are private/unreleased. Native execution against the current owner layout requires an admitted matching binding/profile and complete real catalog/context/authorization/decoder/transport producers.


`bun run build` emits browser-compatible JavaScript and declarations. Browser and native component checks are in `scripts/check-weft-browser.ts` and `scripts/check-weft-native.ts`. The native check requires a fresh isolated test database; it installs the review-only repaired source and never provisions an existing production database. The repair producer uses UMF to edit/export the native model. Retained receipts state the narrower qualification boundaries.


`serializeStorageBinding` serializes a trusted owner-produced composition, verifies every embedded original artifact hash and requires a positive catalog revision. It retains supplied native/home/key/relationship definitions and never allocates IDs or infers bindings. Byte integrity and a positive revision do not establish authenticity: the host must obtain the composition from actual admitted catalog/installation custody. Rust remains responsible for binding semantics, and native host admission still verifies current original context. The serializer is not an acceptance service.
