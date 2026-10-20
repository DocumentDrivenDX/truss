# Embedder E0/E1 execution evidence

Scope: local macOS ARM64, Python 3.11.17, PostgreSQL 18.6 from
`pgserver-pg18==18.6.1`, psycopg 3.3.6 and Weft 0.4.48. Changes are unreleased.
The final wheel's exact source/wheel/installed correspondence is recorded in
`final-wheel.json`: 412 runtime files, SHA-256
`4f05ffd83be69733ee6601c17e6340f9816b3d767f333e8e67e2c7cc2bbcd6d6`.
Its distribution version remains 0.0.41; it is a development build, not the
published 0.0.41 wheel. The changed native manifest digest distinguishes it
from the original installation. No upgrade or publication was performed.

## Baseline and observed changes

The baseline wheel was built from the untouched source at execution entry,
retained separately outside the checkout, and loaded through an isolated target
directory. `baseline_probe.py` reproduces the 153-condition refusal, index-zero
second-create collision and raw non-member `42501`. Original unnamed Field and
fully unnamed stable-ID query workflows pass. Source review and native evidence
therefore supersede the proposed blanket nameless registration refusal.

`e0-measured-measurements.json` and `e1-measured-measurements.json` capture
actual client SQL through a test-only subclass of the stock psycopg Cursor.
Both wheels issue three statements for group context, reader catalog and a
point object read, and four for the isolated one-update apply. These calls run
inside an already adopted caller transaction. Setup, BEGIN/COMMIT, complete
Hohfeld workflows, network round trips and server-internal work are excluded.
One sample per call does not establish a latency distribution or speedup.

## Attempt history

Every attempt retains its log and receipt; failed runs remain failed.

- `e0-baseline`: sandbox could not access pgserver's existing process-lock
  directory; zero tests ran. The subsequent native runs used the authorized
  external lock and fresh owned fixtures.
- `e0-baseline-native`: four controls passed; the fifth used the wrong expected
  existing Python tag (`invalid_input` instead of `invalid`). The assertion was
  corrected without changing baseline runtime bytes.
- `e0-baseline-confirmed`: the corrected 153-condition assertion passed; the
  measurement harness addressed the Cursor at the wrong module path. The
  test-only harness was corrected to subclass `psycopg.Cursor`.
- `e0-measured`: the corrected measurement passed against unchanged baseline.
- `e1-source-native`: 31 controls ran. The 153/3,072/3,073 cases, collision
  ordinals, reservations, failure precedence and original unnamed queries
  passed. Three expectations/setup cases failed: executable retired-profile
  assumption, old raw-error expectation and read-only host adoption. Runtime
  source changed during this exploratory run; its receipt explicitly records
  that fact and is not final-source qualification.
- `e1-measured`: first candidate installed wheel measurement passed with unchanged inputs; this measurement predates the metadata memo.
- `e1-installed-final`: first candidate ran 65 controls in 974.996 seconds.
  63 passed. The 3,072-condition fixture hit the unchanged deadline; the legacy
  component fixture had a synthetic-wrapper ACL/cleanup failure. Inputs remained
  unchanged. This failed receipt is retained.
- `e1-installed-corrective`: the corrected synthetic legacy component passed;
  the isolated 3,072 case still hit the deadline. No timeout was widened.
- `e1-opt1-ceiling`: two installed-wheel fixtures passed in 32.790 seconds,
  including 3,072 conditions, one-over-limit refusal and malformed targets.
  All runtime/test inputs remained unchanged. The optimization is a one-entry
  exact-full-target type-metadata memo local to each inventory invocation.
  It preserves all four inventory passes and every per-condition authority check;
  it caches neither authority nor condition truth.
- `e1-opt1-regression`: all 65 selected controls passed in 453.869 seconds
  (455.686 seconds including the gate producer). Runtime and all test inputs
  remained unchanged. The exact tested preconditions source is retained in
  `opt1-regression-test_group_preconditions_native.txt`.
- `e1-opt1-mixed-final`: two controls passed in 28.879 seconds (30.522 seconds
  including the gate producer), with unchanged inputs. The additional full
  3,072-condition workload alternates A/B identities and combines existence and
  two property equalities, proving metadata hits/misses and current prestate
  evaluation within the unchanged deadlines. The corrected invalid object-ID
  case uses a unique condition ID so duplicate-ID rejection cannot mask it.
  Together these scoped runs qualify the final source/wheel subset; they do not
  establish all possible 3,072-condition key/relationship workloads.

`opt1-static-gates.json` records the generated-runtime check, 1,526-edge Python
boundary check, 18 mutation controls and installed-wheel positive/exact-negative
consumer type checks. Retained boundary-control producer, checker and complete
Python-source pins were rechecked against final source. `cohort.json` records
libpq 18.6, dependency versions and unchanged deadlines. `final-verification.json`
binds final source/runtime/test snapshots and governing frontmatter checks.

`run_gate.py` records commands, selected package roots, test hashes, runtime
hashes, unchanged-input checks, dependency versions and original output. It uses
the existing `run-python-test-module.py` cleanup runner and original isolated
LocalPostgres class fixtures. Tests create and remove their own temporary
clusters; no application database or shared TCP listener is used. These are
focused fixtures, not full engine, platform, managed-service or deployment
qualification.

## Review and continuation

Luna agents implemented and analyzed the bounded changes. Sol authored the
Truss contract/design/test-plan amendments and reviewed changed source, native
ordinal trust, authority-result mapping, generated owner SQL, malformed input,
rollback evidence and backward-compatible outer error tags.

E2 analysis found an explicit design boundary: legacy imports preserve
per-record rejection/progress and engine-owned per-record settlement, while
existing owned imports are atomic. Replacing the former with a single owned
group would change behavior. Next work must preserve the selected semantics and
qualify batching at the existing count before a separately bounded 1,024-record
profile; E1 makes no import throughput or larger-import claim.
