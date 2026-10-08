# Experimental inert assembly

This first runtime package implements `createReferenceAssembly` construction,
configuration snapshotting and disposal. It supports only the pinned
`INERT_ASSEMBLY_PROFILE`. No native capability is implemented: selectors return
`unavailable`, and a configured readiness observation returns `unverified`.

Importing or constructing the package does not inspect a database, invoke an
executor/recovery registry, parse UMF, install a layout or close host resources.
Registry profile/retention metadata must be own data properties; accessors refuse
without invoking them. Caller configuration cannot change the held snapshot.
Native source/model/codec/authority qualification remains required in later work.

The source uses the existing governing bindings as one canonical declaration
source. Build emits their exact transitive declaration closure under `dist`,
without author-machine paths. Packed consumers use only this package's public
root; future adapters/tooling must import the same public transaction type rather
than copying its nominal brand. The clean packed consumer checks that canonical
brand use compiles and an independently copied brand is rejected.

This is a private package candidate, not a published dependency, native runtime,
Truss installation or finished Ashlar integration. Bun 1.4.2 and TypeScript 7.0.2
are checked. Node, actual browser loading and native PostgreSQL support are not
claimed from the ESM ES2022 build.

From the repository root with installed dependencies:

```sh
bun test tests/inert-assembly.test.ts
bun scripts/build.ts
bun scripts/check-packed.ts
```

For the inspected local compiler, pass
`--tsc /Users/erik/Projects/umf/node_modules/typescript/bin/tsc` to both scripts.
That path is an explicit development command; emitted files contain no such path.
