# Embeddable package delivery design

Architecture and ADR-001 govern this proposal. Workspace paths are internal locations, not published package names. An experimental root workspace and inert PostgreSQL assembly now exist; see [the scoped build evidence](../04-build/evidence/inert-assembly/README.md). Native adapters, core value/catalog implementation, tooling and full B-014 delivery remain unfinished. This document specifies their required outputs rather than claiming native packages or support exist.

## Build and export boundaries

Each executable package emits ESM ES2022 JavaScript plus matching declarations into its own dist directory. Its root export maps types to `./dist/index.d.ts` and import to `./dist/index.js`. Publish only compiled files and explicitly inventoried data; consumers must not resolve workspace TypeScript or private source paths. CommonJS and Node support require separate selection/evidence. Do not claim them from ESM or Bun success.

| Workspace | Root executable export responsibility | Runtime dependency boundary |
| --- | --- | --- |
| packages/core | Admitted exact-value/profile/catalog planning APIs, defined by governing core bindings before export | Selected browser-compatible UMF APIs; no filesystem, credentials, driver, compiler initialization or host globals |
| packages/postgresql | createReferenceAssembly and its declared types/capability facades | Core plus abstract executor/host service interfaces; no runtime adapter or tooling import |
| packages/adapter-bun | Selected Bun executor/adoption bridge, after driver profile selection | PostgreSQL/core and explicit Bun runtime; no administrative startup |
| packages/adapter-pg | Separately qualified Node/pg executor bridge | PostgreSQL/core and selected driver; provisional until its own support evidence |
| packages/tooling | createRetentionTooling, createFeedLifecycleTooling, createReceiptLifecycleTooling and explicitly selected physical-job setup | Explicit supplied assembly/host services; native actions occur only on invoked capability methods |
| packages/conformance | createConformanceEvidenceTooling/createConformanceRunTooling and corpus loading | Explicit runner/assessor/adapter injection; no production core dependency |

Names above come from existing draft bindings; no adapter constructor name or missing core API is invented. Tooling and conformance expose separate data subpaths only after exact filenames/versions/digests are selected. Avoid a monolithic root barrel that pulls all drivers, native models and corpus into browser consumers. A package may share type-only interfaces while its emitted runtime graph remains separate.

Build validates exports against the owning declarations and fails if a public declaration references a private file, absolute author machine path, missing type/data export or an incompatible profile. Published dependencies use exact reviewed package/API versions; workspace paths in current source experiments are not distributable dependency pins. Preserve original UMF source/profile and Weft artifact compatibility in explicit host configuration rather than an implicit latest dependency.

## Dependency and declaration ownership (proposed)

Build the selected UMF dependency first, then core, then PostgreSQL, then the selected adapters/tooling, then conformance harnesses and the packed reference consumer. Conformance fixture data can be built independently. This is a dependency order, not permission to exercise a native capability before its installation/profile gates close.

The PostgreSQL package owns the public executor and assembly declarations, including `Executor<HostTransaction>`, `TransactionHandle`, `SavepointHandle`, `Statement`, `StatementResult`, `Outcome` and the existing `ReferenceAssembly` family. Adapters implement that public executor surface; they retain concrete driver/host-transaction types in their own declarations. Tooling imports the public assembly/transaction types rather than copying the draft declarations. Existing bindings remain contract sources until their selected public export manifest is authored; their relative filenames are not published subpaths.

`TransactionHandle` and `SavepointHandle` currently have unique-symbol brands in [the execution binding](contracts/bindings/truss-execution-v0.1.d.ts). Preserve one canonical public declaration identity for these brands across assembly, adapter and tooling consumers. A copied structurally similar declaration is incompatible and must not be repaired with a cast. The package manifest records the selected compatible PostgreSQL package version for each consumer; conflicting installed copies cannot silently exchange transaction handles. This rule does not authorize using a handle after its owning transaction/assembly lifetime or across executor instances.

Core owns pure value/catalog/profile data and computation. It does not import PostgreSQL transaction/assembly declarations, even through a type-only back edge. If a future pure core export needs an outcome carrier presently co-located in the execution binding, explicitly move or factor that carrier with preserved contract meaning and review the public declaration graph; do not duplicate nominal types or make core depend on the whole executor surface. No additional shared package is selected by this proposal.

| Importer | Permitted selected package edges | Refused edges |
| --- | --- | --- |
| Core | Existing browser-compatible UMF API | PostgreSQL, adapters, tooling, conformance, Weft/runtime compiler |
| PostgreSQL | Core; public abstract host services supplied as values | Adapter implementation, tooling, conformance or compiler initialization |
| Adapter | PostgreSQL public executor/types; core where required; selected runtime driver | Tooling/conformance startup, private assembly internals |
| Tooling | PostgreSQL/core public surfaces and explicitly selected tooling dependencies | Adapter construction or installation as an import side effect |
| Conformance library | Public data/profile types and injected runner/assessor services | Concrete native adapter loaded by the generic library entry point |
| Reference or native harness | Public selected packages and explicit host-owned Weft composition | Workspace/private implementation paths or undocumented native handles |

Published package metadata declares all runtime dependencies; type-only dependencies must also resolve from an empty packed consumer. Tree shaking is not evidence of a permitted dependency graph: inspect emitted imports, dynamic imports, declarations and exported data closure independently. Optional native/compiler functionality must be composed by the host through its admitted interface rather than hidden behind an import-time global singleton. A missing optional service produces the existing configured unsupported/readiness outcome when requested, with no fallback connection or compiler initialization.

PD-07 supplements PD-01/05: compile a clean consumer that passes an adapter-created transaction handle to the public assembly/tooling interfaces, and reject an independently copied brand or incompatible package-version handle. Retain the resolved package/declaration graph. PD-08 supplements PD-02/03: inject a forbidden reverse edge and an import-time driver/compiler action separately; each must fail its respective graph/inertness check even if bundling could remove the code. These schedules are planned, not passing package evidence.

## Reference application ownership

Allocate examples/reference-bun as a clean consumer of packed public packages. It supplies configuration, credentials, pools, authentication, selected native profiles, recovery registry and optional verifier/worker/tooling services. It imports no private implementation module. Construction is synchronous/inert; readiness observation and installation/tooling are separate explicit calls. A host can omit replay, feed workers or compiled reads when selecting independent capabilities, without silently downgrading a requested capability.

The example demonstrates engine-owned and adopted transaction paths, sentinel writes, exact original results, disposal/quarantine and recovery. It never closes caller pools or commits adopted transactions. Compiler registration/compilation is explicit orchestration using Weft's public owner bridge; Truss's assembly cannot substitute a private SQL parser or initialize compiler globals. Unsupported selections refuse through the original configured boundary.

## Independent packed-consumer acceptance

PD-01: pack each selected package, install into an empty directory outside the workspace and load only documented exports. Fail for missing emitted files/types, private/absolute source references or undeclared dependencies.

PD-02: load core in real Chromium with independent exact-value fixtures; inspect transitive runtime imports and declarations for Bun/Node/driver/native/compiler dependencies. Import must perform no network/filesystem/connection work.

PD-03: import PostgreSQL package and construct valid/invalid assemblies with a counting abstract executor. Import/construction and inert selection make zero executor calls; readiness alone invokes its explicit observation path.

PD-04: load selected Bun adapter/reference example from packed artifacts, with actual native profiles. Exercise adoption, sentinel rollback, cancellation, lost acknowledgment and disposal without hidden caller transaction/pool control. Native evidence is separate from package load success.

PD-05: compile a consumer's declared types for every selected export/data subpath. Unselected Node/CommonJS and incompatible binding/profile requests remain explicit unsupported scopes, not inferred compatibility.

PD-06: retain original package/build/dependency/configuration/corpus hashes per run; modify one packed artifact or profile after admission and require mismatch refusal. A passing workspace import is not packed-consumer evidence.

All schedules are planned. B-014 can implement build/export and inert consumer checks under the selected provisional-ID policy; native PD-04 still requires the complete original deployment and installation tuple. Package construction does not qualify missing routines or Weft binding adoption.


Configuration capture is implemented under CONTRACT-007's assembly boundary before PD-03 can pass. Include STP-030 CC-01–04 in the packed construction consumer: exact nested-data capture, accessor refusal, stable original service-reference selection and separate continuing custody checks. The package does not serialize/freeze injected host services or expose the caller's mutable configuration as its captured state.


## Authored registration export closure

The PostgreSQL package owns createReferenceAssembly, registerOperationArbitration, registerCatalogTransform and registerTraversalStageService as driver-neutral assembly/protocol integration. Tooling owns explicit bootstrap, physical optimization/job, key migration, receipt observation/lifecycle, retention and versioned feed registration/facade exports. Conformance owns the two conformance factories. This assigns all eighteen currently authored `export declare function` surfaces to an implementation owner; it does not invent a core factory, adapter constructor, published package identifier or final data subpath.

PD-01/05 compares the selected runtime/type export inventory with these governing declarations, preserving nominal registration/transaction brands through one canonical public identity. A package build cannot omit a required authored export merely because a reference scenario does not call it. Selection/version compatibility and support qualification remain explicit; historical/unselected feed variants must retain their version scope rather than be merged by renaming. Registration exports remain inert and assembly-scoped; the host supplies executable services and a registry does not grant native readiness or disclosure authority. No PostgreSQL runtime import of tooling is introduced to reach an administrative registration.


Core owns the selected draft ExactIntegerToken, ExactDecimalToken, ExactNumericToken, NumericInput, NumericReadValue, LosslessNumericNumberView and NumericInputOrigin declarations from ADR-006. Their emitted declarations have no PostgreSQL/executor/driver dependency. Preserve the UMF-compatible wrapper fields and exact-token read default; constructor/admission implementation still reuses pinned UMF semantics and the selected bounded domain algorithm. These are type exports, not new runtime functions or qualified numeric support.


## Selected draft core data entry

The [core data declaration entry](contracts/bindings/truss-core-data-v0.1.d.ts) explicitly exports foundational profile/artifact/canonical-tree, exact value/presence/identity, numeric convenience carrier, ordered group input/reference and exact group result types from their canonical owning declarations. All exports are type-only; it exposes no executor/transaction/savepoint handles, host recovery service or runtime factory. Do not replace this explicit list with export-star over every contract file, which could leak protocol/host responsibilities or silently add exports when a draft changes.

This is the selected initial pure-data export entry for B-004/B-014, with no published package name or runtime support claim. Emit its declaration closure through the public core package; PostgreSQL/tooling consumers use those canonical data types instead of copying them. Execution nominal brands remain owned by the PostgreSQL entry. Additional core callable/domain APIs still require explicit design and independent admission evidence; a data barrel does not supply numeric conversion or catalog planning.

The [compile-only consumer](contracts/bindings/truss-core-data-v0.1.typecheck.ts) resolves the selected data exports and refuses importing Executor/TransactionHandle through core. The full existing declaration witness set compiles together. This proves declaration membership/consistency only; PD-01/02/05 must independently verify packed runtime/declaration closures and actual Chromium imports once implementation exists.


Core's selected first numeric callable is admitNumericInput, governed by ADR-006 and its draft admission declaration. Its runtime export is separate from the type-only data entry and performs no native/host I/O. PD-01/02/05 must resolve its original packaged UMF/profile dependencies and execute independent public conversion/refusal fixtures; declaration compilation does not qualify the implementation.
