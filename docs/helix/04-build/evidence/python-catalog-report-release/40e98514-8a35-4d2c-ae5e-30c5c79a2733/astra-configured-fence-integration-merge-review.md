# Configured archive fence — merged-source review

Disposition: **no scoped implementation blocker found** in merge `19f1a223`, which preserves the fence component `20432c24` and incoming main `9fc23a75`. Review is read-only; no implementation edits, native tests, or producers were run. Saved SMT formulas were independently replayed.

Both installed-fence checks, the original archive cut, and the before/after release and resource comparisons remain. The incoming change adds a final configured graph/metadata recollection and original-operation comparison after the additional collectors, before returning the provisional packet. Its new native test changes installation metadata after the original core stage, requires the exact final-cut `55000` diagnostic, rolls back catalog effects, and preserves earlier host work. This directly tests the metadata mismatch branch; it does not independently erase every operation-comparison conjunct.

The original body/settings, same-length hash controls, SETOF signature refusal, NULL/default-ACL refusal, twenty-one pre-effect drift cases, and actual-stage same-writer archive fence remain intact. The incoming borrowed-host implementation is preserved, and the ordinary boundary construction retains its default path. The current native component runs are not a new qualification of the borrowed-host API or its semantics.

## Current retained evidence

These packets replace the pre-merge 274-input packets for current-source correspondence; the earlier packets remain historical. The current closure has **276 inputs**, adding `_borrowed_host.py` and `_native_attachment.py`, with no removed inputs. Seven prior inputs changed: `host.py`, `_native_pg8000.py`, `__init__.py`, `configured-stage.sql`, the configured release test, the native runner, and the boundary checker.

| Final packet | Result |
|---|---|
| `40e98514-8a35-4d2c-ae5e-30c5c79a2733` | 23 release/configured + 14 dispatch + 15 incoming tests pass: **52** |
| `b75402b0-cae1-4d56-8f49-f8e8820e0e3a` | Paired verifier omission: **22** intended non-refusals; 23 methods + 14 dispatch |
| `aef34088-2853-4f8b-8320-348731644781` | Hash-only omission: **2** intended non-refusals; 23 + 14 |
| `97de4b9a-6e91-4b86-be76-109f0fcf208d` | Resource digest omission: **1** intended non-refusal; 23 + 14 |
| `3b64709a-7ce2-4183-9916-62ed096fc7c1` | Archive lock omission: **4** intended non-refusals; 12 raw release + 14 dispatch |
| `18787d50-2a41-4dcc-b29d-56fd407ba7e2` | Standalone fence predicate disabled: **10** intended non-refusals across 8 methods; no configured dispatch/auxiliary groups |

The positive receipt SHA-256 is `681a336e4098f0b1ebad2e3b0ff80d16e23288c775befa7bab0abf24e4d782a6`. The retained logs contain only the specified assertion failures in negative variants, with no incidental errors. The boundary logs report **520 imports**. Exact source ZIPs, current source hashes, executed SQL variants, native binary pins, test identities, and owned cleanup are recorded in the separate merged native audit.

Formal packet `aa5ccaac-36f8-4067-9d1a-3be1a8f40a3b` has four matching current source preimages and **seven independently replayed formulas: four UNSAT, three SAT**. All formulas are byte-identical to the earlier algebra; only the native-runner source pin changed. Independent reconstruction and SAT-witness checks pass. The formal pins do not include the new installed verifier or configured wrapper; this remains a conditional opaque-state transition model, not implementation refinement. In particular, rollback loss is stipulated as `alive=false`, not derived from a savepoint stack.

## Limits

This checkpoint supports the selected original fence correspondence and tested native archive-write exclusion, including the added final metadata observation. It does not authenticate the verifier, owner, role reachability, language implementation, or declared resources; establish continuously held source/configuration/DDL/authority custody; prevent privileged source ABA; or cover final host disclosure. Other source/configuration lock waits, whole allocation/CPU/deTOAST limits, installed-body correspondence, complete accepted-report authority, public installer readiness, and backend acceptance remain open. No accepted-case promotion follows from this review.

Retained review artifacts:

- `/private/tmp/astra-configured-fence-integration-merge-native-audit.json`
- `/private/tmp/astra-configured-fence-integration-merge-formal-replay.json`

All pre-merge review/audit files are preserved separately.
