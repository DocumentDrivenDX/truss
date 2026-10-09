# Conformance runtime implementation handoff

Status: existing contracts and carrier proposals are authored; runtime services
remain unimplemented. `packages/tooling/src` contains the layout migration planner
and a private alias-substitution candidate helper. The conformance constructors and runner/assessor
lifecycle currently exist as declarations and type witnesses, not executable
services. Governed inputs are CONTRACT-004/007/011, US/TD/STP-027/028, the case
grammar and operation registry proposals. Reuse those APIs; no second runner,
qualification authority or public transaction-by-ID service is needed.

The [combined schema receipt](evidence/design-audit/schema-inventory-runtime-handoff-2026-10-09.json)
records strict registration, reference resolution and compilation of all 155
top-level contract schemas, including the case argument and operation registry
descriptors added for this handoff. It reports zero errors. This verifies schema
composition only; it does not implement the runner, establish observer independence
or qualify an operation against PostgreSQL or another implementation.

## Implementation sequence and independent exits

C5 has a reusable private `conformance-alias-substitution.ts` component over
already admitted bounded JSON/namespace/binding/scope projections. Seventeen
synthetic controls now exercise that implementation, and strict TypeScript
passes. It preserves literal data and exact integer text, uses only registered
slots, refuses invalid/forward/rolled-back/unknown or wrong-generation bindings
and returns a copied candidate input. It does not admit native issuer, visibility,
resource accounting or complete public-wire semantics. C5 still requires those
original runner procedures and independent native invariant comparison before
normalization; no public conformance factory or capability is activated.

C1 must consume the [private original-service construction port](../02-design/contracts/conformance-original-service-port.proposal.md).
Public method shapes and matching profile metadata do not prove original
registered service/build/function custody. Preserve the existing factory API
and host qualification authority; copied services or unavailable original
startup registration refuse before constructing a projection.

| Slice | Concrete implementation output | Required exit |
| --- | --- | --- |
| C1 original composition and inert binding | Implement existing createConformanceRunTooling/createConformanceEvidenceTooling projections over original host runner/assessor; capture immutable exact configuration and method/profile correspondence | Missing services, unknown required profiles, changed pin or empty approved manifests refuse construction; no artifact resolution, native acquisition or execution occurs at import/construction |
| C2 prepareRun and recovery custody | Admit original manifest/input inventory/environment reference/procedure/resource composition, full case/fixture/expectation/alias/registry artifact bytes and complete reservation before issuing the original prepared handle | Cross-artifact and original digest/parser/schema/method/observer independence admission pass; invalid input and cancellation before claim have zero native effects; copied handles/recovery strings cannot mint prepared authority |
| C3 original run claim and setup | Claim the original preparation at most once, acquire only its admitted isolated environment, verify actual native tuple, perform registered setup and compare full independent starting inventory | Native drift/unsupported capabilities record complete honest not-run inventory; failed/interrupted acquisition retains original recovery and cleanup evidence; setup mismatch cannot become replacement fixtures or skipped correctness |
| C4 registered operation and observation | Dispatch exact method arguments through existing capability/executor procedures, preserve business versus execution result layers, observe all normative surfaces at original transaction boundaries | No arbitrary SQL/import/callback from case content; unknown methods/profiles and invalid scope generations refuse before dependent effects; savepoint/callback return never proves commit; absent observer leaves the case unverified |
| C5 identity construction and comparison | Bind only original eligible typed result/setup occurrences, resolve aliases in exact registered input slots, validate the complete unchanged public wire and compare native invariants before normalization | Literal data stays exact; forward/rebound/unknown/rolled-back bindings, substituted namespace/profile and wrong endpoint/order/multiplicity fail; exact large IDs never pass through host-number conversion |
| C6 evidence settlement and assess | Preserve every required case and actual result/state/journal/report/performance verdict, original partial progress, termination and cleanup; emit immutable receipt and invoke separately bound assessor | A recorded run is not automatically qualified; omitted/not-run/interrupted cases, unavailable observers, malformed evidence and altered original pins cannot produce qualified; later reruns receive distinct evidence identities |
| C7 independent interchange | Run TypeScript writer/Python reader and Python writer/TypeScript reader against each direction's actual committed database state using the original writer's bindings | Readers inspect the same original state; no fixture replacement, shared writer serialization oracle or agreement-only correctness; Python ownership decision and independent packed-consumer/native evidence remain explicit gates |

Administrative and lifecycle/configuration operations belong to the same
complete required registry where selected. The twenty-two capability return
carriers do not establish that broader inventory. Keep pending traversal and
catalog-concurrency choices as original profile gates; the harness cannot pick
their behavior from an implementation's favorable result. The Python package
ownership decision does not prevent constructing language-neutral packets, but
it prevents claiming the supported Python delivery route settled.

## Original lifecycle and containment

Keep prepareRun, run, abandonPreparedRun and reconcileRun under their existing
issuer/custody contract. Preparation does not acquire native resources. Run
cannot accept a replacement request or remint a preparation after an unknown
claim. Abandonment closes only still-prepared work; it cannot free a claimed
native operation. Reconciliation observes the original run and returns its
actual prepared/abandoned/recorded/interrupted state without replaying cases.
Separate case result, execution outcome, native termination and evidence-store
settlement. Unknown native work or cleanup retains custody across caller loss,
deadline and disposal; cancellation delivery alone never establishes rollback.

Resolve scope and cancellation references through original trusted harness
registration, not JSON-shaped handles. Security-read, subject/principal,
verified-application and publication procedures remain under their owners.
The latest security working-source review is component input only; host method
shape and matching profile strings cannot confer native authority. Reserve the
complete parser/copy/constructed-input/observer/archive and recovery budget
under the existing selected resource contract, including simultaneous copies;
do not infer a heap bound from individual schema maxima.

## Red-first execution packet

Before C3 native work, assemble one immutable independent case packet for each
required operation/boundary family plus the selected full corpus manifest.
Include forbidden overload results, wrong input/result profile, changed native
tuple, copied prepared handle, duplicate run claim, setup mismatch, missing
observer, false committed boundary, rejected-result alias, forward alias,
rolled-back scope, wrong current authority, omitted case, malformed receipt
and interrupted cleanup. Preserve deliberately failing fixtures and raw
observations. An independent implementer must review the packet without
importing writer helpers and record contract ambiguities before qualification.

The current shape/link/arithmetic/substitution scripts are reproducible design
witnesses for C1/C2/C4/C5/C6 constraints. They are not host services or proof of
native scope, authority, observer independence, resource containment or C7
interchange. Do not replace any native exit above with their green output.
Package exports, original runtime/driver/target tuples and actual runner
commands are selected and pinned during implementation; no command pointing
to absent harness files is a current executable success claim.
