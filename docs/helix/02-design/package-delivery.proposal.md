# Embeddable package delivery design

Architecture and ADR-001 govern this proposal. Workspace paths are internal locations, not published package names. The repository currently has no root package.json or implementation workspace. This document specifies the B-014 build outputs rather than claiming packages exist.

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

All schedules are planned. B-014 can implement build/export and inert consumer checks independently of pending allocation policy; native PD-04 still requires the complete original deployment and installation tuple. Package construction does not qualify missing routines or Weft binding adoption.
