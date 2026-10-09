---
ddx:
  id: truss.pooler-overhead-experiment
  type: test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-032
      kind: informed_by
    - id: STP-032
      kind: informed_by
    - id: TP-001
      kind: informed_by
---

# Prepared versus unprepared point-read experiment

Status: proposed workload and measurement procedure, not a registered native
experiment. The mean-versus-p95 selection is pending owner response. The
existing US-032-AC3 bound remains 0.05 ms extra cost at 1,000 types. This
proposal neither changes that bound nor supplies pooler qualification.

## Workload and paired boundary

Use exactly 1,000 accepted object types, each with one required string property
and one committed object carrying a distinct independently expected string.
The fixture artifact records actual accepted type/property/object identities,
exact UMF/model bytes and complete expected object values. No edges or optional
indexes are introduced by the workload. The separately selected installation,
policy, journal and baseline physical index/statistics inventories remain
complete and identical between modes. Setup is excluded from measured time.

Each pair reads the same object through the same registered public direct-read
method, using the same authenticated role, visibility, transaction ownership,
result codec and complete validated result. Only the admitted preparation mode
differs. Both modes use the same exact transaction-mode pooler/driver/server
profile. A direct-server baseline cannot establish pooler incremental cost.
If that pooler profile cannot qualify prepared execution, this paired
experiment is unavailable; do not substitute another topology. A distinct
experiment may assess that topology under an explicitly different claim.

Freeze the complete public call boundary before running: API entry to complete
validated result decoding/assembly, including transaction work that the
selected call owns. Do not measure one mode outside a transaction or omit its
preparation/protocol work. Query plan, parameters, statement preparation
lifetime and backend rotation policy are registered artifacts, not inferred
from a cached statement name. Record backend identities and actual preparation
mode separately without credentials.

## Samples and proposed decision rule

Warm up with 200 pairs using the first 200 fixture objects in fixture order.
Record these samples separately. Then run three repetitions, each with exactly
1,000 pairs visiting every fixture object once in fixture order. Within each
repetition alternate prepared-first and unprepared-first; invert the initial
order in the second repetition. No parallel readers are introduced. Freeze
cache/reset behavior before setup; apply the same procedure to both modes and
retain it in evidence. Never reset caches or refresh statistics in response to
a disappointing measured sample.

Record every elapsed duration as an exact nonnegative integer nanosecond
string. For pair i, compute signed delta `unprepared_i - prepared_i` using
exact integer arithmetic. The proposed statistic is the arithmetic mean of
all 1,000 deltas for each repetition, with no rounding before comparison.
The 0.05 ms bound equals 50,000 ns, so compare the signed delta sum against
50,000,000 ns for each repetition. Negative differences remain negative and
are reported; do not clamp them or take absolute values. All three repetitions
must meet the selected rule. Raw mode distributions and p95 may be informative
but cannot replace the selected criterion. An owner-selected p95 rule requires
a revised preregistered procedure before execution.

Any wrong value, incomplete result, error, timeout, missing pair or interrupted
run prevents a performance pass. Preserve the partial original run and cleanup
evidence; a later rerun gets a distinct identity. Results cannot be removed as
outliers or reclassified as warm-up. The independently expected values are
checked for both modes, so paired agreement alone is insufficient correctness.

## Registration and implementation exit

Before native work, pin exact fixture/procedure bytes, chosen statistic,
implementation/adapter/pooler/server/runtime and hardware configuration,
installation/layout/model/value/policy/journal profiles, complete native index
and statistics inventory, authenticated writer and independent observer,
monotonic clock source, cache/preparation/rotation settings, resources and
cleanup/recovery procedures. Any unresolved pin prevents registration; this
document is not permission to fill one from a current default during a run.

Implement independent assessor controls for a sum exactly at the bound, one ns
over it, a negative sum, a missing sample, a mismatched object result, duplicate
pair identity, changed mode profile, swapped units and a failed repetition
hidden by a favorable aggregate across repetitions. Native controls must
verify actual prepared/unprepared behavior and backend boundaries through the
selected pooler. Arithmetic fixtures cannot qualify native mode execution.

The next outputs are owner statistic selection, immutable fixture and complete
environment/procedure registration, red assessor controls and the actual
paired native schedule. US-032-AC1/AC2 still require their complete correctness
corpus independently; this point-read workload cannot substitute for it.

Run `bun docs/helix/04-build/evidence/design-audit/check-pooler-overhead-arithmetic.ts`
for twelve independent synthetic proposed-mean witnesses. They include exact
boundary and one-nanosecond failures, negative deltas, wrong shared results,
missing/duplicate samples, changed modes/units and failure hidden by combining
repetitions. The unsafe-number fixture uses durations 2^53 and 2^53+1 and
places their exact one-nanosecond difference at the decisive bound; converting
them to JavaScript numbers would produce the wrong verdict. These are
mathematical design checks, not measured samples, statistic adoption or native
pooler/mode/resource qualification. The production assessor remains unfinished.
