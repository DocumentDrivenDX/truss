# Python installation and migration implementation handoff

This handoff applies the owner's Truss-maintained Python and shipped-migration
requirements to CONTRACT-007, CONTRACT-008, CONTRACT-012 and the existing
[administrative binding](../02-design/contracts/bindings/truss-layout-migration-v0.1.proposal.d.ts).
It selects Python composition conventions; it does not qualify an executor or
substitute for the complete populated M1 source/target route.

## Package and entrypoints

Fresh installation is a separate `truss.installation` tooling projection with
`install_fresh` and `reconcile_installation`, mapping the existing bootstrap
binding. It requires its original qualified candidate and bootstrap-attempt
context; an installed migration request cannot create a fresh namespace. Both
tooling projections are constructed inertly from the same admitted original
assembly/services. Construction performs no namespace query, starts no transaction
and issues no attempt. The current Python package implements neither projection.

Continue the experimental `truss-toolkit` distribution already containing the
local runtime. Implement a `truss.migrations` module with `status`, `verify`,
`apply` and `reconcile` on an explicitly constructed migration tooling instance.
Preserve the existing binding's complete request/result variants and exact
artifact/profile fields. No Python-specific migration ledger or version-derived
SQL is introduced. The package must deliver registered original manifest,
recipes, source/target inventories, verifier inputs and compatibility profiles,
or retain an explicit separately delivered artifact admission contract.

Use frozen Python dataclasses for admitted pins, exact artifact references and
result variants. Retain original immutable bytes independently of decoded fields;
never reconstruct original request/recipe/receipt bytes from dataclass JSON.
Wire interchange retains the existing field names and interface versions rather
than assigning a new wire protocol to Python naming conventions. Wrong types,
unknown fields, altered originals and incomplete variants refuse before native
submission under the existing bounded admission profile. A dictionary containing
an administrative profile name cannot grant authority.

Do not expose `apply_sql`, arbitrary recipe callbacks or `commit_by_id`. The
existing pure TypeScript planner is declared-metadata preparation only. A Python
planner must use a shared language-neutral corpus and preserve that scope; it
cannot infer installed status or synthesize routes from intermediate versions.
`no_steps` still requires current full installation verification.

## Connection and transaction ownership

The host supplies an actual PostgreSQL administrative connection and the original
qualified driver/services. Truss does not provision a pool or substitute another
connection. Application embedding uses the caller's actual transaction and does
not commit it; migration apply is a separate administrative operation that owns
one dedicated transaction for the entire registered route. Refuse a connection
already in a caller transaction before effects. The host must close its connection
before the owned local server context exits.

Driver admission must establish actual transaction status, exclusive use,
original receive/account/cancellation bounds and settlement correlation on that
same connection. Stock-driver convenience properties are insufficient evidence
for the existing original producer port. The pg8000 experiments remain candidates,
not a supported-driver selection. The local runtime's connection URI does not
supply administrative credentials, original authority or a qualified driver.

Inspect/verify preserve their registered read-only cut. Apply retains original
request and attempt recovery custody durably before effects, resolves the exact
registered recipe bytes, obtains the security-owned exclusions, verifies the
source, executes ordered steps, verifies independent target/preservation
expectations and publishes receipt/archive/marker atomically. The security owner
provides admission, current-context freshness and publication drain; Python must
consume that composition rather than implement a second resolver.

## Settlement and exceptions

Map native outcomes to the existing result variants, including `commit_unknown`,
`recovery_required` and `committed_unverified`. The bootstrap binding now includes
the confirmed-commit/unverified-readiness variant too: retain original commit and
attempt evidence with a recovery reference, exposing no ready marker or complete
committed inventory. Authorization-unavailable recovery retains the evidence in
the trusted registry while returning the opaque observation-unavailable branch.
Do not translate these outcomes into a generic
retryable exception. Pre-effect refusal returns once. No automatic apply retry,
callback replay or recipe resubmission follows a socket error or deadline.

A confirmed commit survives later verification or framework failure. Unknown
cleanup retains the original recovery reference and quarantines connection use
according to the qualified driver protocol. Reconcile looks up that same original
attempt read-only and never calls apply. Missing/unavailable observation cannot
prove rollback. Preserve all original evidence when returning any uncertain
variant; an exception without recovery custody cannot replace it.

## Implementation and qualification order

1. Select the complete installed bundle on the local16.2 profile, including all
   routine/grant/initializer obligations. Current structural checks do not satisfy
   this step. Define one complete populated M1 source/target route and independent
   preservation expectations, retaining historical receipt/feed/epoch semantics.
2. Implement original status/verify inspection and verifier on the selected
   driver, proving no writes and refusing incomplete source observations. Package
   these original inputs; test byte-modified or missing delivered artifacts.
3. Bind original administrative admission, installed-target recovery registry and
   driver settlement services. Wrong service/profile, changed request, unavailable
   recovery custody and caller-owned transaction must refuse before effects.
4. Implement apply under the exact M1 route. Exercise real first-step effects then
   late-step failure, complete rollback and no target publication. Independently
   verify objects, keys, edges, exact values, reports, journal, receipts, feed
   positions and unresolved recovery state.
5. Implement settlement and fresh-process reconcile using actual lost acknowledgement
   and post-commit verification failure. Prove that reconcile repeats no recipes,
   confirmed commits survive framework rollback, and unavailable lookup keeps
   readiness closed.
6. Qualify a built Python distribution outside the checkout with only its declared
   dependencies and delivered route artifacts. Prove fresh bootstrap separation,
   unsupported-route refusal, no upgrade on startup and ordinary UMF model changes
   without DDL. Run corresponding TypeScript/Python committed interchange on the
   same selected source/target/security/driver tuple.

Aurora and Lakebase remain separate advertised-target qualifications. The current
pgserver/Python lifecycle wheel is useful local infrastructure, not evidence that
any stage above is implemented. No traversal API decision or pool performance
benchmark gates this sequence.

## Shared planner corpus before the Python port

`tests/fixtures/layout-migration-planning.json` now supplies sixteen independent
expected results for the existing declared-metadata planner, exercised by
`tests/layout-migration-corpus.test.ts`. It retains original input JSON text,
including duplicate-member and numeric-node refusals, rather than passing only
already-decoded objects. Full expected source/target pins, recipe order and
procedure artifacts are compared for successful plans. Explicit route absence,
ambiguous routes, changed source pins, nontransactional steps and malformed
unselected routes refuse; large version components remain exact.

The Python port consumes this same corpus and preserves the existing decoder's
finite byte/depth/node/member/work bounds, Unicode rules and numeric-free closed
wire. These sixteen cases are a baseline, not exhaustive decoder qualification.
Neither these fixture manifests nor
a passing metadata plan are delivered original migration artifacts, installed
observations, administrative authority or a selected populated M1 route.

The private Python `_acceptance_json` component now implements numeric-free
wire decoding with the same logical limits and duplicate-key work accounting
as the existing TypeScript decoder. It scans iteratively and uses Python's
JSON decoder only for individually validated string tokens. UTF-16 key lengths
are used for shared work charges, including supplementary Unicode characters.
Original `acceptance-outer-json-expected.proposal.json` vectors and the original
capacity fixture pass, along with exact depth/container/node boundaries and
byte/work refusals. These are source-component checks, not built-wheel, host
heap, shared operation-account or administrative admission qualification.
The planner's frozen result variants are implemented as described below;
administrative execution remains unfinished.

The experimental `truss.migration_planning.plan_layout_migration` now implements
the existing declared-route planner in Python. Frozen pin/artifact/procedure/result
dataclasses and tuple step sequences retain exact hashes, original declared order
and integer-exact version comparisons. Immutable bytes are required; mutable
buffers refuse. Both implementations pass the expanded sixteen-case shared corpus,
including a complete explicitly declared downgrade. Python also checks direct
target/resource/type refusals and frozen nested results. These source tests do not
qualify a built distribution, migration execution or original installed observation
producer. The separate `truss.migrations` administrative tooling remains unfinished;
this module exposes no database connection, apply, startup upgrade or retry.

The [built-wheel component receipt](evidence/design-audit/python-migration-planning-wheel-component.json)
records five passing unittest methods outside the checkout, including all sixteen
shared planner cases and eighteen original wire cases. Both module origins resolve
to the separately installed wheel. Installation used --no-deps in an existing
private environment; it does not qualify clean dependency resolution or delivered
original recipes. Independent corpus inputs remain external test expectations.
