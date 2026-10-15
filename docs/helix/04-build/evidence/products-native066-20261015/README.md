# Original Products model against a fresh native66 binding

The original native-person source packet is UMF commit
`ed6766987cd403fb513a82d49102596f6e727235`,
`docs/helix/04-build/evidence/security/preparation-sources-20261015/input.json`,
SHA-256 `4ef6a9faf4c8e098f43a1949bc425145570f6e7616f22af9dabbe773c00d9e19`.
Top-level Artifact digests and the nested request model digest were checked.
`original-model.json` retains the
exact request model bytes, digest/revision
`b7f8ad91d22eeae35d9c7a966090d9120a2f436c84e29a6ba56d5979a6b712b5`.
The action remains `sales.set-name`, invocation `umf.actions.tx/1`.

A disposable PG18.6 store publicly installs Truss, accepts that exact original
model and exports a genuine native66 query binding using a module reader.
`native-query-bundle.json` and `native-binding.json` are actual returned bytes.
The historical packet's disposable-store binding is never selected. There are
no seed rows, SCRAM/Subject admission, policy installation, seal or effects.
The receipt's authority/securityReady flags remain false.

The published Weft0.4.30 mutation compiler compiles the original request but
refuses this fresh binding during registration with
`WFT-MUTATION-TRUSS-CURRENT: Original current model/binding/evidence required`.
At exact source `50464e03edc9db6dd1ea566f2e110b2aa4e6164f`,
`crates/weft-postgresql/src/truss_mutation.rs` admits only native0.65 in its
initial registration check. Native66 query support does not establish native66
mutation-selection support. This finding was sent to the Weft owner for an
additive registration, preserving the original native65/c0/98ee cohort.

`probe.py` reproduces the scoped observation with a new output directory. Its
portable argument handling was added after the recorded run. It requires the
published macOS arm64 Weft0.4.30 binary and checks its exact extension hash; use
the project Python environment, Truss source on PYTHONPATH, psycopg3.3.6 and
pgserver-pg18 18.6.1. Example from the Truss checkout:

```sh
PYTHONPATH=packages/python/src:/path/to/published-weft-install python docs/helix/04-build/evidence/products-native066-20261015/probe.py /path/to/umf /new/output --bun bun
```

Fresh store identities are expected to differ. This is compiler compatibility
evidence, not a working native bulk API or a browser/local-store profile.

## Source fix and native workflow

Weft commit `e389d60` adds native66 registration through the unchanged full
binding validator, retaining native65 and its original lowering obligations.
Its [retained evidence](https://github.com/DocumentDrivenDX/weft/tree/e389d60/docs/helix/04-build/evidence/truss066-mutation-20261015)
includes a basic Rust test, Python bridge checks and a fresh PostgreSQL18.6
workflow: original Products acceptance and public seeds, native population
preflights/selection, then public Truss update and readback. The selected product
changes to `Foo`; the other remains unchanged. Astra Ultra reviewed the source
and evidence. The bridge hash is
`3d1f9363cae5c8a8949d33ff1303446a2ef5e0d042ae6510106096f92c183c0f`.
This is an unpublished local dev build, requiring a later wheel release; it does
not change the published0.4.30 refusal above. The administrative selector remains
an excluded test assessor, with protected selection, authorization, sealed bulk
execution and browser support still unfinished.
