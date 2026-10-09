# Python installation and migration implementation handoff

This handoff applies the owner's Truss-maintained Python and shipped-migration
requirements to CONTRACT-007, CONTRACT-008, CONTRACT-012 and the existing
[administrative binding](../02-design/contracts/bindings/truss-layout-migration-v0.1.proposal.d.ts).
It selects Python composition conventions; it does not qualify an executor or
substitute for the complete populated M1 source/target route.

## Package and entrypoints

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
`recovery_required` and `committed_unverified`. Do not translate them into a generic
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
