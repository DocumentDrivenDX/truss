---
ddx:
  id: EVIDENCE-NATIVE-LAYOUT-CAPTURE
  type: evidence
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: CONTRACT-008
      kind: informed_by
    - id: US-045
      kind: informed_by
---

# Native UMF layout capture experiment

On 2026-10-05 the existing Truss layout and optional module-isolation SQL were imported into UMF's native PostgreSQL representation, serialized/read through UMF JSON, and regenerated twice. Both source archives remained exact and repeated regenerated SQL matched. This demonstrates a design path; it is not installation qualification or a completed US-045 test suite.

## Inputs and runtime

Truss baseline: worktree `6d87fce53d04b876ec8ca37fb5eab0a949f1d320`, unchanged `storage-layout.sql` and `module-isolation.sql`. The SQL header still calls itself 0.1 while its installed schema marker is 0.2; reconcile that metadata before qualification.

Runtime source: `/Users/erik/Projects/umf`, observed after the run at `16c35e8d943769ccfa7bb57d16785aa7159abe65`; relevant entry/runtime files were clean. Native backend is `@libpg-query/parser@17.6.10`, PostgreSQL-17.4-derived, distinct from a tested live-server version. The physical representation uses core envelope `0.1.0`; Truss application schemas' `0.7.0` pin is a different profile. Source digests below were captured after the run and are provenance, not an immutable-run attestation.

| Runtime input | SHA-256 |
| --- | --- |
| `src/adapters/postgresql/index.ts` | `7baa071d95e5f9863a4ce2bf892d87fb27cab9d8605ba4cf8887016d14ca17b4` |
| `native/postgresql/runtime.ts` | `a88fea4cf15c9c3c3f0ad1f0a36d8f5de42a42ce8ea9712499f609beee3ea751` |
| `src/index.ts` | `f540f085e29bcea2c685ab271957ec1159892a54ed51e0a6ee238974fd744349` |
| `package.json` | `692f5d5c8537d04ac4bf7b079199e28a83edeacfc8291c8dcb6bb1395f7759de` |

## Outputs

- [Fixed layout model](../../02-design/models/truss-layout-0.2.umf.json), [generated SQL](../../02-design/models/truss-layout-0.2.generated.sql), [generation checks/digests](../../02-design/models/truss-layout-0.2.generation.json).
- [Optional isolation model](../../02-design/models/truss-module-isolation-0.2.umf.json), [generated SQL](../../02-design/models/truss-module-isolation-0.2.generated.sql), [generation checks/digests](../../02-design/models/truss-module-isolation-0.2.generation.json).
- [Exact script executed](native-layout-capture/reproduce.ts). It names the inspected local input/runtime paths; reproduce in that environment or deliberately repin them and retain new evidence.

The command was `bun /private/tmp/truss-layout-model.ts`, exit 0. The retained script is byte-identical to that input. It verifies source archive, UMF JSON roundtrip, deterministic export and the UMF export guard. No database, browser or independent parser was executed here.

## Remaining evidence

Complete inventory accounting, native generated/baseline catalog comparison, PostgreSQL 16/17 behavior, function-body validation, schema-name adaptation, edited-model cases and browser qualification remain required. The checked SQL is still the authority. A future breaking layout/model revision must regenerate both components with new versioned receipts rather than silently replacing this candidate.
