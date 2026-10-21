# E2–E8 installed-wheel qualification

Local macOS ARM64 evidence for Truss 0.0.44, Python 3.11.17, PostgreSQL/libpq
18.6, pgserver-pg18 18.6.1, psycopg 3.3.6, Weft 0.4.48 and mini-racer 0.14.1.
The isolated environment carries umf_access dev4; no additional SDK qualification
is inferred. All tests import `/private/tmp/truss-release44-installed/truss`, not
checkout runtime files. No application database or persistent dev host was reset.

Runtime manifest SHA-256:
`9f6aab31802e9bebcd886f735ba9fe0bb405e69d3501a32f36cee8827b544d00`.
The [package receipt](local-package.json) binds all 428 exact runtime files in
source/wheel/sdist and all 436 wheel RECORD members. Local archive hashes identify
this local build; hosted and public builds have separate receipts.

## Verification

| Gate | Actual result | Receipt |
| --- | --- | --- |
| New batch/catalog/DDD/preview/lifecycle/install/grant/audit APIs and wire controls | 74 passed, zero skips | [native](native.log) |
| Final review controls: actual READ ONLY preview and cross-module edge/owned cascade audit | 2 passed | [controls](review-controls.log) |
| Existing import, conditions, receipt lifecycle, catalog evolution, action transport and generated client/native action | 70 passed, zero skips; explicit frozen UMF source/Bun opt-in selected | [regressions](regressions.log) |
| Managed fused/nonfused guards and psycopg fault/cleanup/cancellation controls | 44 passed | [host](host-guard.log) |
| Original Hohfeld catalog/Northwind/Pizza register/seed/list/open/write/facts and graph import | 21 passed; Python-only PATH | [examples](consumer-examples.log) |
| Original corpus13 | 63 passed, nine declared limits, seven replica-only exclusions | [corpus](consumer-corpus.json) |
| Python boundaries | 1,636 edges and all 18 allowed/refusal controls | [controls](boundary-controls.json) |
| Typed public consumers, mypy 1.15.0 | Positive consumers pass; exact negative cases have 10 and 10 expected errors | [typing](typing.log) |

Hohfeld is frozen at `fed2c116db5dcdf2ac3b12b71bbfdddc35d03f6c`; the original
checkout is read-only and all consumer runtime work uses its `/private/tmp`
archive. The corpus verifier witnesses that one old Unsupported registration
limit now fails because its business case succeeds, removes only that obsolete
limit in memory, and runs the original assertions. It does not weaken assertions
or claim the nine remaining limitations are implemented. Original test selection
initially deselected all marked tests; explicit `-m truss` selected the 21 tests.
A host command initially named a nonexistent class; the complete corrected module
selection passes. These are selection corrections, not runtime passes or skips.

## Statement budgets

[Original consumer statement traces](consumer-statements.json) retain actual
rendered SQL without bind parameters, using the original `bench_latency.Ops` over
one warm kept person connection. Three samples of each operation have identical
counts. Setup/warmup/cleanup are excluded; per-operation transaction setup and
settlement are included and separated below. Implicit BEGIN and protocol messages
are not Cursor.execute calls. The original psycopg wait-call counter is a proxy,
not measured network packet/round-trip evidence.

| Original workflow | Cursor.execute | Driver rollback | Driver commit | All submissions |
| --- | ---: | ---: | ---: | ---: |
| Singleton read by key including facts | 29 | 2 | 0 | 31 |
| Single-object RenameUseCase update | 31 | 1 | 1 | 33 |
| Describe/type enumeration | 27 | 3 | 0 | 30 |

The read's 29 execute calls include six host setup, five SAVEPOINT, five RELEASE,
four adoption/observer and nine payload/other calls. The update includes six
host setup, eight SAVEPOINT, eight RELEASE, two adoption/observer and seven
payload/other calls, across two transactions. This unchanged adapter still calls
the unconditional catalog routes; it does not automatically use the new validator.
A simple guarded managed function, including a conditional catalog observation,
uses three statements in an already adopted transaction; adoption separately uses
three. Do not generalize that budget to a complete compiled entity query.

The [native parity/performance samples](batch-parity-performance.json) compare
32/64/128 legacy versus batched inputs over three trials, then 1,024 batched
records. At 128, legacy builder512 + executor1162 =1674 client statements versus
batched builder3 + executor6 =9, excluding context acquisition/settlement equally.
The 1,024-record route uses3 +27. These counts include final report authorization.
Records still use individual native containment and enforcement server-side.
The measured local elapsed reduction is modest, not a tenfold gain; this evidence
qualifies no TCP latency, p95 target, allocator quota or universal write budget.
Backend/client RSS samples are observations, not complete memory accounting.

## Delivery status

Independent source review and the complete request disposition are recorded in
[review](review.md). The [Linux candidate run](https://github.com/DocumentDrivenDX/truss/actions/runs/39538360360)
passed, including the 76 final new API/review controls and original public workload.
Its 40 unittest invocations report 494 executions: 493 passed and one optional
generated-client preflight unit skipped because its source/Bun opt-in was absent.
That opt-in unit and generated native action ran in the separate local 70-test
selection. The whole hosted run is not called zero-skip. Separate stress,
large-capacity and diagnostic collection were not selected.

[PR21](https://github.com/DocumentDrivenDX/truss/pull/21) merged as
`5834509d641a2961b1871d00cb1fd59962c5f086`; tag `v0.0.44` points there. Candidate
implementation `4a442f33`, review follow-up `3a5bf974` and the merge have identical
runtime and test bytes; the intervening delta is review documentation only.
The downloaded Linux candidate package matches all 428 runtime files and 772
tracked sdist package files, with eight explicit backend metadata files.
[Candidate status](linux-candidate.json), [compressed original log](linux-candidate.log.gz)
and [delivery mapping](delivery.json) retain those distinct identities.

[Tagged Linux CI](https://github.com/DocumentDrivenDX/truss/actions/runs/39540319279)
and [fresh public verification](public-release.json) passed. All ten public assets
(nine checksummed assets plus SHA256SUMS),436 RECORD members,428 runtime files,
package metadata, source-build contents and every release pin match the qualified
release source. Publication time is 2026-10-21T04:11:26Z. The reviewed
[public verifier](verify-public-release.py) performs unauthenticated public API
and artifact downloads, resolves the public tag, and calls its sibling
[integrity verifier](verify-release-integrity.py) for complete checksums,
archives, metadata, entry points, source, pins and published contracts/ABI.
[Verifier controls](public-verifier-controls.json) reject representative duplicate,
unsafe and symlink archive members. Historical releases/receipts remain unchanged.
