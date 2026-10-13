# Scalar array/map feature tranche — 2026-10-13

Implements one-level UMF core0.7/0.8 array/map Fields with explicit required
singular scalar item definitions, source-qualified retained item pins, original
fragments and declaration authority. Public create/update/import/read/history
and PropertyEquals use exact scalar carriers. Maps have unique exact keys and
canonical C ordering; sequence order/duplicates and absent/null/empty survive.
No owned/nested records, optional item slots or item rebinding claim.

Runtime0.43-candidate retains layout0.16; matching Weft0.4.8/backend0.4.13
preserves earlier exact runtime selections. Container-bearing selected catalogs
explicitly refuse compiled queries instead of omitting logical fields.

Astra Ultra reviewed the plan and implementation. Corrected original-payload
parse ordering, outer publication item authority, original executed-revision
receipt dependencies and hidden receipt visibility refusal. Request-free imports
use immutable original creation evidence, never today's catalog as fallback.
Original .42 manifest archived byte-exactly for additive upgrade.

Focused installed-wheel tests cover original UMF0.7/0.8 acceptance, create,
map equality/no-op, precision and duplicate-key refusal, import, durable replay,
read-only reads, retained history, null/empty/absence, rollback and item-module
access revocation. Additive .42→.43 and scalar numeric query checks are run
alongside these workflows: five tests passed in103.814 seconds on the installed
Truss0.0.6.dev0 and Weft0.4.8 wheels. Module boundaries passed932 imports.
Native release smoke and actual public assets will be
recorded separately. Managed Aurora/Lakebase and full corpus remain unqualified.

Final source rerun: two container workflows passed19.053 seconds. Existing
basic typed-key/traversal/facet-evolution release checks: six passed52.957 seconds.
Focused mypy checks passed three modules. Commitcab9e4dc merged concurrent
security main updates in9aedd8f3 and pushed main.
