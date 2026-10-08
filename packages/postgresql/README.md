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

The newer existing UMF source 16c35e8d exposes validateCoreFieldValue for core 0.8.
`check-umf-field-values.ts` uses its actual explicit verified 0.7→0.8 upgrade and
rollback APIs, retaining original source bytes/receipts without changing examples.
Four actual present string values in local-string-source.jsonl receive valid=true,
complete=true results; required null and wrong scalar-family probes refuse, while
v3's explicit absent-allowed caption accepts null. Bun and real Chromium agree on
all original operation results. Legacy 0.7 direct value checks refuse. This supplies
one actual upstream producer, not whole-record/availability/key/relationship or
native binding support. A present-value result for v2's unknown availability or the
unknown document assertion does not qualify those unresolved meanings. Fixture
property mappings are local development IDs, not accepted Truss catalog identities.

UMF branch codex/core-record-value-check at c45c72a2 adds the reusable
validateCoreRecordValues operation under CONTRACT-049. It composes actual Field
checks with logical membership/presence, preserving original incomplete document
results separately. `check-umf-record-values.ts` consumes that exact clean source
and verified explicit upgrades: all three actual create/replace records in the
local source receive valid/complete logical results in Bun and real Chromium.
Unknown v2 availability/document assertion remain incomplete; dataset keys and
relationships require separate context. Delete remains a source operation. No
native accepted IDs, automatic defaults, writable catalog profile or source ACK
is supplied by these results. The UMF branch is pushed separately, not merged.

## Private native catalog components

The internal SQL under `native/` is exercised independently of the public inert
assembly. It is not an installer or a granted application API. The isolated
harness currently selects the UMF-generated qualified-property layout 0.15;
Weft's separately tested query fixture registration retains its original layout.
The harness installs actual ALWAYS generation observers and a deferred commit
barrier. Unfinalized operations and forged finalized flags both refuse COMMIT
with SQLSTATE 55000 because the complete runtime finalizer is unfinished.
Rollback/savepoint containment is part of the expected successful test result.

From the repository root, build the original owner bundles from a local UMF Git
repository containing the required commits and installed build dependencies:

```sh
bun scripts/build-umf-runtime.ts /path/to/umf record
bun scripts/build-umf-runtime.ts /path/to/umf values
```

Each command prints its separate temporary bundle directory. Record uses
c45c72a2a8a3c4fba61c40c5927dd9091acf8cc3; values uses
9e4bed3efe922c11e4b5a888ba6854de14f1b29f. The builder archives committed source
and records source/bundle hashes and build dependencies. Current-core Field/key
checks do not promote the older Record producer to current-core qualification.
Keep both original manifests; do not substitute a sibling working tree bundle.

Use a fresh disposable PostgreSQL 17.9 instance on the harness's fixed loopback
port. The layout creates its own schema and genesis rows, so reruns need a fresh
instance. These commands use synthetic fixtures only:

```sh
docker run --rm -d --name truss-runtime-admission \
  -e POSTGRES_HOST_AUTH_METHOD=trust \
  -e 'POSTGRES_INITDB_ARGS=--locale=C --encoding=UTF8' \
  -p 127.0.0.1:15434:5432 postgres:17.9
docker exec truss-runtime-admission pg_isready -h 127.0.0.1
```

Wait for readiness, then supply the exact directories printed by the two builds:

```sh
TRUSS_UMF_PRODUCER=/path/to/record-bundle \
TRUSS_UMF_VALUE_PRODUCER=/path/to/values-bundle \
TRUSS_OPERATION_TEST_URL=postgres://postgres@127.0.0.1:15434/postgres \
  bun scripts/check-operation-admission.ts
docker stop truss-runtime-admission
```

The harness writes `docs/helix/04-build/evidence/runtime-operation-admission.json`,
pinning layout/native body/owner bundle hashes and original observed checks.
A green run proves those component checks only. It covers original operation
custody/exclusion, archive-backed catalog staging and identity classification,
qualified cross-module Fields/ordered keys, generation events, key buckets,
prestate snapshots and rollback. It does not establish complete current-data
validation, whole-set matching, reactivation, immutable reports, journal/feed/ACK,
effective-role installation, resource/deadline enforcement or public runtime
readiness. Internal allocated IDs remain transaction-local. Keep this evidence
separate from compiler fixture results and from production installation claims.
