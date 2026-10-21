# Hohfeld performance evidence — 2026-10-21

These are scoped local macOS ARM64 results, Python3.11.17, PostgreSQL18.6,
pgserver-pg18 18.6.1, psycopg3.3.6 and mini-racer0.14.1. Ordinary reads and
the final native suites use the exact Weft0.4.49 artifact identified by Weft's
`local-macos-0.4.49.json`. Earlier intermediate samples explicitly use0.4.48.
The public release qualification and artifact pins are separate delivery gates.

## Request coverage

| Request | Delivery and evidence |
| --- | --- |
| T1 | Access-aware unchanged reader catalog, retained from0.0.44; native schema-cache/reader controls and measured three-statement hit |
| T2 | Conditional native query binding; unchanged response omits source/binding; every hit checks current person and full dependency scope; schema-cache controls cover changed pins/limits and revoked readers |
| T3 | One immutable runtime verification per process; three pure tests include corruption retry, concurrency and caller-mutation isolation; microbenchmark receipt is not an E2E claim |
| T4 | `statement-budgets.json` and native budget test include every Cursor.execute and driver wait, including raw data query; host setup/adoption/settlement and server-internal statements explicitly excluded |
| T5 | Combined catalog/source/digest/query API in one adopted read-only transaction, with final catalog/authority checks; compiled-query native test. Existing Hohfeld adapter adoption remains a host change; no unmodified-adapter adoption claim |
| T6 | Immutable runtime verification removed from every apply; current three-effect apply measured three submits; original conformance, settlement and journal checks retained |
| T7 | Independent rootless object chunks use one native group writer;16-record native test proves one attempt,16 operation indices, original source bytes and16 journals; parity/audit and failure-injection tests cover fallbacks and no retries |
| T8 | Already available owned-group bound requalified at153/3,072 with refusal at3,073, including condition preview |
| W1 | Bounded exact compiler-result reuse; four pure controls and native revoked-reader regression. Value-independent templates are not provided |
| W2 | Documented current wildcard-added names, explicit alias/projection workaround, no selected EXCLUDE/REPLACE date; real compiler collision and distinct-alias native controls |
| W3 | Documented ABI1.1 complete source bounds by shape and plan-inspection guidance; selective LIMIT/count/page native controls refuse before output reduction |
| R16.4 | Element-specific registration refusal after original UMF validation; unnamed UMF remains valid; original native retry and no-catalog-effects control |

## Receipts and reproduction

`truss-hp-final-pure.log`:57 tests, including immutable/compile caches,
preparation/relational/DDD/report support, exact module cohorts and malicious wheel
controls. `truss-hp-final-compiled.log`:16 native compiled-query/budget/capacity
tests. `truss-hp-final-preconditions.log`:15 native group/preview controls.
`truss-hp-final-disclosure.log`:five explicitly enabled native disclosure cases.
`truss-hp-final-parity-audit.log`:eight parity/owned/audit tests and actual
32/64/128 three-trial plus1,024-record measurements. `truss-hp-final-native-import.log` records the final22-case import/parity/audit
campaign, including the unselected legacy profile whole-input refusal. The added
rollback-validator case passed separately. `truss-hp-installed-final.log` records
10 controls from the exact installed local wheel; `local-installed-wheel.json`
proves all429 runtime payloads match source. Separate current-query and
admission/import logs record their precise selected modules and test counts.
`truss-hp-final-boundary-controls.json` records18 controls and source hashes;
the actual module checker reports1,646 imports.

Run maintained modules using the installed compiler and current package source:

```sh
PYTHONPATH=packages/python/src:packages/python/tests python scripts/run-python-test-module.py test_compiled_query_native test_hohfeld_statement_budgets_native test_schema_cache_native test_batched_import_native test_batched_import_parity_native test_owned_import_native test_mutation_group_audit_native test_owned_group_audit_native test_group_preconditions_native test_group_preview_native
TRUSS_DISCLOSURE_NATIVE_QUALIFICATION=1 PYTHONPATH=packages/python/src:packages/python/tests python scripts/run-python-test-module.py test_current_disclosure_runtime_native.CurrentDisclosureRuntimeNativeTests
python scripts/check-module-boundaries.py
python scripts/check-module-boundaries-controls.py
python scripts/build-owned-runtime.py --check
```

The Hohfeld source is commit03d004053f0d88cb693b46a7efce345198b28305
(`adopt-truss-0-0-44`), extracted into an isolated snapshot. Run its
`tests/bench_latency.py --throwaway --runs 100 --warmup 10 --no-cold --no-create --statements --json REPORT`.
The two original-adopter JSON reports retain all100-run observations, nearest-rank
percentiles, machine load, waits and actual phase statements. Their matching
source-hash receipts identify the exploratory Truss source bytes exactly; they
are not claimed as clean published-wheel qualification. No live user data or
active adoption checkout was modified.

## Limits and review dispositions

The20ms singleton/100ms action targets are not all established. Original-adapter
catalog/data transactions and noisy machine load remain visible, not normalized
away. Combined API availability alone is not host adoption. The read source bound,
related-key bound and explicit value-sensitive cache keys remain intentional.

Broader `test_catalog_runtime_native` includes nine pre-existing stale assertions
in four module-access test methods expecting outer `Error` instead of typed
`Ok(ModuleAccessBatchRefused)`. The same failures reproduced against unmodified
HEAD; they are not credited as passing here. Maintained release selections and
focused live-authority controls remain required. Whole-repository discovery is
not claimed. Failure from two mistyped exploratory import module selectors was
corrected with the maintained parity/audit modules; that failed invocation is
not counted as a passing campaign.

Final review confirmed that the complete import input already rejects a
non-selected legacy payload profile before native mutation. An exploratory test
initially expected a per-record rejection; its failed assertion was corrected to
the actual whole-input22023 refusal, retained prior caller work and zero effects.
The redundant speculative SQL check was removed; runtime SQL/manifest bytes are
unchanged by this final review control. The corrected full22-case campaign passed.

The unchanged conditional reader-catalog hit in `statement-budgets.json` took
1.98ms for the measured warm local call at load9.37, using three public driver
statements/waits (one native observation plus the operation guard). This is a
single observation on the51-record fixture, not a percentile or managed-host
latency promise. Fresh public Weft0.4.49 macOS/Linux wheels match their published
checksums and all four explicit Truss cohort pins. See
`weft049-public-verification.json` for the release/packaging/compiler source
identities and exact qualified workflow runs.

`truss-hp-registration-adoption-native.log` records30 later registration/domain-
pack/commerce/declarative/evolution controls. `truss-hp-set-based-dml-proof.log`
records the independent physical-DML observation:16 imports produce one INSERT
each into object, journal and runtime_owned_operation (16 rows each), with
original per-record source/provenance retained. Test-owned transition-table
triggers count the actual server statements; no business implementation is mocked.
