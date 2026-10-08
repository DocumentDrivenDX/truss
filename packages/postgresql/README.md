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

`verifyExactArtifacts(artifacts, {maxArtifacts,maxSingleBytes,maxTotalBytes})`
is the first CONTRACT-003 ingress primitive. It snapshots bounded exact artifact
carriers before asynchronous Web Crypto SHA-256 verification. Canonical base64,
exact digest, scalar identity, own data fields and full input/byte limits are
required. It returns frozen original carriers without parsing/converting JSON;
unknown UMF content and numeric spelling stay byte-exact. Unknown carrier fields,
accessors, corrupt digests and noncanonical base64 refuse. No profile name or
verified digest establishes provenance, UMF validity/completeness, dependency order,
semantic support, native catalog acceptance, authorization or generated IDs.
No SQL is issued. The observed Bun/public-package check uses the four original
Ashlar v1/v2/v3/unknown UMF examples and independent Bun/Web Crypto hashes. Browser
build passes; actual browser execution of this new primitive remains unverified.

`bun scripts/check-umf-semantic-ingress.ts <pinned-UMF-checkout> <Ashlar-examples>`
builds the actual clean fac1497a UMF readDocument/validateDocument producer and
runs original v1/v2/v3/unknown example artifacts through it after integrity ingress.
All four observed results are valid=true, complete=false. Full original diagnostics
are retained: experimental core warnings, v2 unknown nullability, and the unknown
example's preserved assertion. CONTRACT-003 requires completeness of separately selected semantic checks;
aggregate validateDocument.complete is not the writable-readiness rule. No qualified
semantic-check composition has been supplied, so writable acceptance remains
unavailable. This evidence does not introduce a
qualified validator service or accept native IDs; suppressing warnings would not
establish completeness. The exact supported acceptance/profile composition remains
a required dependency. The browser-target producer is observed under Bun only.

Real Chromium 153.0.8010.12 executes the actual built Truss ingress and identical
pinned UMF producer on all four original examples. Original bytes and complete
validity/completeness/diagnostics match Bun. Corrupt digests, shared byte overflow
and noncanonical base64 refuse; unknown assertion stays preserved and Node globals
are absent. `check-umf-browser-ingress.ts` records exact bundle hashes. This verifies
browser execution for the exercised subset, not selected semantic-check admission,
qualified isolation/termination/resource accounting or native catalog readiness.

The semantic probe now also emits a source-qualified interpretation/check inventory
using actual UMF inspectCoreNullability/Cardinality/Facets/Keys/Relationships results.
Twenty-six full original inspection results across the four examples are anchored
to exact artifact hashes/pointers; raw original inputs and unknown diagnostics are
retained. Real Chromium reproduces every Bun operation result. Required-check
producer, native binding and support-profile slots are explicitly unresolved;
inspectors carry unverified provenance and cannot supply complete value validation,
original author authority or native acceptance. This implements the inventory
prerequisite requested by the Truss profile review without a Truss semantic validator.
