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

## First populated route selection and acceptance matrix

M1 is not a version-number exercise. Select an actual supported source bundle and
an actual required target change before authoring the recipe. Pin both complete
inventories and original artifacts; identify the product requirement that requires
physical migration rather than ordinary catalog acceptance. A second installation
of unchanged DDL does not satisfy the populated upgrade requirement.

The review-only source-epoch0.16 composition cannot be promoted to an admitted
source just to obtain a passing route: all four original operation admission
families reissue an ordinal after savepoint rollback. See the
[issuer integration handoff](operation-ordinal-issuer-handoff.md). Repairing that
composition is prerequisite installation work. If a deployed historical source
actually contains the defect, its upgrade needs a separately admitted recovery
route with explicit defective-source preconditions; it cannot inherit normal
source verification. No such deployed-source claim or recovery route is selected.

The recipe's independent preservation fixture must cover every populated family
below. Record explicit independently expected originals before migration and compare
the same originals after commit; counts or regenerated digests alone are insufficient.

| Populated source family | Required target observation | Refusal/failure control |
| --- | --- | --- |
| Document-qualified catalog, definitions and accepted reports | Complete document/module/element identities, original accepted bytes and report correspondence | Same names across two documents remain distinct; missing source member refuses before effects |
| Objects, keys and exact scalar/property values | Full keys and absence/null/value distinctions; exact large integer, decimal and timestamp carriers | No JavaScript rounding, key merging or coercion; byte-modified source refuses |
| Relationship occurrences and ordering | Original occurrence identities, endpoints, relationship types and declared ordering semantics | Existing same-endpoint uniqueness limitations are explicit; no deduplication or unsupported parallel occurrence qualification |
| Journal, transaction receipts and feed positions | Original records and externally retained receipt/feed interpretation across the selected epoch transition | Do not reconstruct original bytes, recycle identities or treat xid visibility alone as proof of commit |
| Installation, configuration and source epochs | Original predecessor identity and selected registered target transition, including configuration generation/modes | Stale original source/configuration refuses once; no inferred route or silent epoch rewrite |
| Unresolved attempts and recovery custody | Original attempt identity/evidence remains resolvable with its actual outcome | Refuse migration when original recovery/exclusion policy cannot preserve unresolved custody; never replay attempts |
| Roles, grants, guards and security dependencies | Complete selected inventory and independently verified mandatory integrity/authorization behavior | Missing routines or wrong grants cannot publish readiness even when table/column projection matches |

Run the same selected populated fixture through success, late recipe failure,
lost COMMIT acknowledgement and confirmed commit with failed readiness verification.
For late failure, prove source preservation and absence of target publication from
an independent connection after settlement. For uncertain/committed outcomes,
retain the original recovery identity; a fresh process must reconcile without
executing a recipe again. The existing binding supplies the result distinctions.
These controls are required acceptance evidence, not current passing tests.

## Rust compiler embedding alignment

The [frozen Python extension receipt](evidence/design-audit/weft-python-f05f2df-component.json)
replaces the older5856c73 compiler pin for this focused component qualification.
It uses the same f05f2df committed source archive and qualified build feature as
the current Truss TypeScript/CLI integration. `scripts/build-weft-python.py`
archives the committed source, verifies the original archive hash and builds
the original PyO3 extension with locked offline dependencies; it adds no Python
SQL compiler. The installed macOS arm64 ABI3 wheel delegates `weft.compile_json`
directly to Rust and has no declared Python runtime dependencies.

In a fresh Python3.11 environment outside the checkout, the loaded extension
matches the exact wheel payload. Count, bounded grouped count, unbounded-group
refusal, unsupported-profile refusal and missing-version refusal have independently
declared outcomes and full parsed-response correspondence with the same pinned
CLI. Five invalid transport inputs refuse, and the test-only configuration export
is absent. Original owner-output equality is compiler correspondence, not an
independent native semantic oracle. Historical broader owner corpus evidence
remains tied to its older build; it is not relabeled by these five cases.

This wheel is a local development build, not a published consumer dependency or
a `truss-toolkit` query API. Its PostgreSQL fixture target remains17.9; neither
this build nor its feature name qualifies the default pgserver16.2 database.
Original Truss binding/obligation admission, current-person read context, exact
result decoding, bounded execution and package delivery remain required. Weft0.3
and positional output are not adopted by rebuilding this frozen0.2 interface.

The source-component `truss.weft.CompilerBoundary` now consumes that original
in-process `compile_json` callable synchronously. It accepts immutable complete
owner request bytes, verifies original binding/model hashes before invocation,
admits only compile0.2/SQL0.2 and returned backend0.2/context correspondence,
retains original response bytes and freezes nested artifact views. JSON metadata
integers stay Python-exact and decimals use Decimal; parameter values must remain
ordered text. Duplicate members, invalid Unicode, excessive nesting, changed
pins, non-text parameters and positional output in the old profile refuse.

Five independent unittest methods cover immutable exact carriers, pre-compiler
input refusal, changed/new artifacts, single invocation on failures, reentrancy
and disposal withholding publication. The pinned wheel/CLI checker additionally
passes its five cases through this boundary: compiled artifacts retain exact
response bytes, blocked profiles/queries refuse, and absent versions refuse before
invocation. That checker loads the boundary from source, not a newly built Truss
wheel; its receipt records this distinction. The original extension still matches
its separately installed wheel payload. No execute method, native permit, alternate
SQL compiler or Weft0.3 adoption is introduced. The full Python engine, original
obligation services, native decoder and complete installed distribution remain
required delivery work.

The subsequent [installed compiler wheel receipt](evidence/design-audit/python-weft-wheel-component.json)
closes the source-only packaging gap for this component. A new truss-toolkit
0.0.1.dev0 wheel, built with setuptools79.0.1, was installed with --no-index
--no-deps into the fresh Python3.11 environment already containing only the frozen
Weft wheel and packaging tools. Outside the checkout and without PYTHONPATH,
the boundary resolves inside that environment. All nine delivered Python module
payloads equal both the original wheel and current source; no module is omitted.
The five actual compiler/CLI cases, five invalid native transport controls and
five boundary unittest methods pass with that installed Truss package.

This is the base compiler-component distribution only. The native Weft wheel
remains separately delivered, and the conditional local extra is not installed
in this environment. No clean local-extra resolution, pgserver lifecycle rerun,
full engine API, database execution or original recipe/profile delivery is
established by these packaging checks. Historical source-only and older component
receipts retain their original scope and pins.

## Private query execution coordination

`truss._query_execution.QueryCoordinator` implements the synchronous ordering
boundary corresponding to the existing TypeScript host/handler/scope protocol.
It captures original compiler and host callbacks at construction and keeps a
private weak identity registry of its own frozen plans. Foreign/copied plans
refuse. Complete original host obligations are checked for admitted meaning
before acquiring a read context. Unsupported owners or unknown handlers refuse
without a connection acquisition. Brands or compiler SQL do not issue authority.

Inside the same original context, run context verification, every registered
obligation check, one data query, exact text/null shape admission, the original
decoder and publication context verification. Freeze complete results and return
only after context cleanup exits successfully. Disposal is rechecked through
publication, including after cleanup. Unknown cleanup, context drift, decoder
failure, suppressed incomplete host failure or reentrant native invocation
publishes no result. No transaction commit, connection substitution or automatic
query retry is introduced. Native ownership and settlement stay with the host.

Seven independent unittest methods cover those ordering/fault schedules, nested
immutability, exact large integer text, numeric/invalid-Unicode decoder refusal,
callback capture and disposal during both checks and context exit. They use
synthetic host callbacks and compiler responses, not authenticated native
observations. This module is private source implementation, absent from the
earlier nine-module wheel receipt and not exported as a ready query engine.
Original bounded producer/transaction custody, current-person authorization,
full obligation grammar, owner-qualified decoder, actual native execution and
installed distribution qualification remain required before public activation.

The synchronous coordinator now refuses coroutine/async-generator host functions
at construction and detects awaitable results from wrapped callbacks. Original
context and obligation checks must return None after completing or raise; a
Boolean return cannot stand in for completed verification. An unawaited coroutine
is closed without executing it and never permits the next native query. Async
services need a separately integrated execution path, not implicit event-loop or
thread creation. Nine unittest methods now pass with warnings treated as errors,
including wrapped async checks, nonvoid checks and async context verification;
their independent event traces contain no data query after such refusal.

Context entry/exit now uses the same explicit synchronous completion boundary.
Async lifecycle methods refuse before entry; a wrapped exit returning an awaitable
withholds the buffered result and never runs implicit asynchronous cleanup. Original
host cleanup/recovery custody remains unresolved until its own qualified protocol
settles it. Eleven source unittest methods pass with warnings as errors, including
both lifecycle controls. This closes the host-language publication bypass only;
it does not prove native cleanup or release resources on behalf of the host.

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


## Current coordinator wheel delivery

The [ten-module delivery receipt](evidence/design-audit/python-weft-coordinator-wheel-component.json)
now covers the current package including the private query coordinator, superseding
source-only delivery status for that component. A new Python3.11 environment outside
the checkout installs only the built Truss base wheel and frozen original Weft
wheel, with no dependency resolution or local extra. Every delivered Python module
matches its installed payload and current source. Five Rust compiler outcomes and
five invalid transport refusals retain their existing component scope.

The [installed coordinator controls](evidence/design-audit/python-coordinator-installed-controls.json)
run all eleven synthetic-host tests against that exact installed coordinator,
including asynchronous check/cleanup rejection, disposal, reentrancy, drift,
unknown obligations and suppressed host failure. The earlier nine-module wheel
receipt remains historical. This delivery includes no installer or migration
implementation and proves no original security/driver authority, native execution,
clean local-extra resolution, or complete committed engine interchange.


The subsequent [current-wheel local-extra receipt](evidence/design-audit/python-current-wheel-local-extra.json)
closes the clean declared local-extra resolution gap for macOS arm64/Python3.11.
Pip resolves the wheel's pinned pgserver0.1.4, fasteners0.20, platformdirs4.12.4
and psutil7.2.2 using published cached wheels in the same initially fresh environment.
The complete existing34-test Python component suite passes against the installed
ten-module wheel outside the checkout, with warnings treated as errors. Four tests
exercise actual PostgreSQL16.2 lifecycle, retained commit/restart, cross-process
custody refusal, independent servers and explicit cleanup-failure recovery.
Other tests retain their pure/synthetic component scope. Earlier base-wheel
receipts intentionally describe the environment before this extra installation.
This is no cross-platform/process-crash, full installation, migration-execution
or protected-engine qualification.


## Committed preservation and DISTINCT alignment

The [upstream source review](evidence/design-audit/upstream-preservation-distinct-review.json)
pins UMFb51c300d and Weft9fbbbab separately from Truss's adopted compilerf05f2df.
UMF's document preservation guidance selects TableSpec Python for source-document
loading and BagIt transfer of originals/history, with scoped PREMIS/PROV metadata.
Those acquisition artifacts do not supply Truss transaction settlement, migration
receipts, original issuer authority or fresh-process database reconciliation.
Reuse retained immutable source bytes through admitted consumer inputs; do not
replace Truss recovery custody with a loader handoff or checksum.

Weft's new0.3 DISTINCT subset applies to complete projected tuples of required
non-null scalar Strings under exact UTF8_BINARY semantics. Ordering requires an
exact projected Field/scan occurrence and lowers through projected carrier aliases.
Numeric, optional/tagged, aggregate, computed, structured and page-profile DISTINCT
remain refused in this subset. It is a Spark candidate, not a Truss PostgreSQL
qualification: original PostgreSQL native/qualified profile source bytes are
unchanged. Keep the adopted0.2 compiler refusal until an exact owner-admitted
PostgreSQL composition is selected and qualified. DISTINCT must never repair the
native parallel-edge limitation by silently deduplicating relationship inputs;
source guards and original occurrence identities remain independently required.
