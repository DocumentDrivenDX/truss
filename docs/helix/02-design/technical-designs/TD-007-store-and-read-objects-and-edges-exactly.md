---
ddx:
  id: TD-007
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-007
      kind: informed_by
    - id: SD-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# TD-007: Store and read objects and edges exactly

## Selected decision handoff — 2026-10-07

Planned numeric facade controls NAPI-01–04: safe integer number and larger bigint round-trip exactly; reject unsafe integer number before effects; under decimal(3,1), admit exact decimal number 12.5 but reject the actual binary value of number 0.1; preserve decimalToken 1.00 and large/nested tokens across browser, JSON transport and native readback. Explicit number conversion must reject precision loss and preserve the original token separately. Planned ID controls PID-01–03: pending IDs link records only in the same live adopted transaction; rollback leaves no committed graph identity; no durable external publication occurs before confirmed outer commit, and unknown commit waits for recovery rather than reallocation. Cases are not_run.


**User Story:** [[US-007]]. **Feature:** FEAT-002. **Parent:** [[SD-002]].

## Scope

Build the catalog-driven exact value codec and fixed object/edge storage transport. No per-type tables or implicit driver conversions. The story includes shared identifier allocation, not edge lifecycle/cardinality rules covered by other stories. Exact numeric token preservation and the hybrid numeric API are selected; exact source/native codec profiles remain to be composed.

## Technical Approach

Inherit SD-002's lossless text boundary. Core receives typed values and a pinned catalog; the adapter passes explicit typed parameters and raw text/null result cells under CONTRACT-007. Avoid a generic host JSON parser for numeric tokens. Read object maps with an exact recursive parser that preserves presence before converting each value according to its catalog meaning.

US-007-AC1 spans pure codec and actual PostgreSQL roundtrip. Binary uses canonical base64; timestamps retain authored offset text rather than native driver Date conversion. Arbitrary-precision arithmetic handles numeric validation. AC2 uses map membership plus explicit JSON null; SQL null and absent field are not interchangeable. AC3 checks nested strings as well as top-level properties before persistence and reports the governing rule. AC4 obtains identifiers exclusively from the shared native sequence; rolled-back reservations leave gaps and deleted identifiers are never recycled.

## Numeric convenience implementation boundary

Consume the existing pinned UMF numeric producer and Truss registration described in [the current numeric handoff](../contracts/core-numeric-number-view.proposal.md#current-umf-numeric-producer-adoption-handoff--2026-10-08). UMF owns admitJavascriptNumber, exactDecimal, integerFromBigInt, integerToBigInt and numericToNumberLossless; do not implement a second converter or validator in Truss. ADR-006’s binary64 rational procedure remains an independent expectation/oracle, not duplicate production work. The adapter preserves original exact carriers, admits the selected Field context separately and qualifies error translation and conservative precharged producer bounds before an operation-bounded call. Owner constructor names and API capture are available; complete wrapper/resource/native qualification remains unfinished.

Reads retain exact token carriers by default. Explicit number conversion consumes the owner’s lossless view and is checked against independently authored exact-rational expectations; retain original spelling separately. The current owner producer refuses signed-zero number views while retaining signed-zero exact decimal tokens, so that view remains unavailable rather than locally special-cased. Safe integer-number admission remains stricter than mere binary64 representability for integer input. Field/source/native and finite resource profiles still govern all conversion paths.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/values/parse.ts` | Exact recursive parsing and token diagnostics | US-007-AC1, US-007-AC3 |
| `packages/core/src/values/codec.ts` | Catalog-directed encoding/decoding, presence and family validation | US-007-AC1, US-007-AC2, US-007-AC3 |
| `packages/core/src/values/numeric-correspondence.ts` | CONTRACT-010 NX01–NX06 bounded mathematical witnesses after original grammar/facet admission; lexical custody stays separate | US-007-AC1 |
| `packages/postgresql/src/storage/values.ts` | Parameterized fixed-row writes and raw-text map reads | US-007-AC1, US-007-AC2 |
| `packages/postgresql/src/storage/identity.ts` | Shared sequence reservations without caller-chosen IDs | US-007-AC4 |
| `tests/values/codec.test.ts`, `tests/values/native.test.ts`, `tests/values/browser.test.ts` | Exact corpus, real persistence and pure browser portability | All criteria |

These are new implementation components. Keep browser tests independent of Bun/Node-only APIs; database integration remains outside core.

## API/Interface Design

CONTRACT-001 governs storage representation and sequence identity; CONTRACT-004 governs mutation/report behavior; CONTRACT-007 governs exact executor transport and transaction ownership. Shared public value schemas and the final lexical-preservation carrier must be settled there before publication. Weft's decoder consumes the qualified Truss profile, not an independently guessed JSON representation.

## Data Model Changes

Existing property maps and shared sequence remain the baseline. A lexical receipt or alternative numeric carrier, if selected, is a versioned contract/layout change and cannot be hidden in this story's implementation. Structured nonidentity records remain value containment; keyed records and owned relationships require explicit UMF bindings rather than inference from a record-valued field.

## Integration Points

Catalog supplies recursive logical type and physical binding. Codec refusal is explicit for selected unsupported types; unknown retained content follows its separate retention contract. Storage executes within the catalog pin and host transaction context. Exact driver configuration is mandatory on every connection, including adopted caller connections. If the executor cannot provide raw text for required cells, refuse the adapter profile rather than trust rounded output.

## Security

Authentication and connection ownership belong to the host. Enforce the acting role/context before reads/writes. Parameterize values and identifiers through validated templates. Bound recursive depth/size through the exact selected versioned value/resource profiles before accepting untrusted inputs. Existing read/row-home/collector resource proposals are candidate inputs, not an adopted complete codec profile; select their original units/producers and composition without silently inventing or widening limits. Reports identify rule/path without unnecessary value disclosure.

## Performance

Measure encode/decode cost by bytes and nesting, and database roundtrip by the qualified corpus. Cache compiled codecs by full catalog/profile identity. Do not trade exactness for native double parsing. Broad scale claims depend on ADR-002 V1/V2 and PRD benchmarks, not this story's correctness pass.

## Testing

STP-007 owns all four primary allocations. Independent fixtures include 9007199254740993, signed limits, decimal trailing zeroes/exponent spellings, equivalent instants with distinct offsets, binary bytes, empty/nested containers, absent and null. Native observations inspect stored text and decoded results separately. Concurrent object/edge creates use independent clients; deletion and rollback cases prove nonreuse. Browser tests run the same codec output package.

## Migration and Rollback

Initial storage uses fresh bootstrap only. Failed writes leave no canonical rows or journal effects; sequence gaps are permitted. Never repair exactness by rewriting existing values without an explicit migration. A carrier change requires old/new decoding qualification and a reviewed version transition. Preserve previous fixtures and profiles for comparison.

## Implementation Sequence

1. Select the full original logical/native/home/codec/resource tuple and apply accepted ADR-006 exact carrier direction and FR-15 provisional precommit ID rules. Row-home numeric_token is an authored candidate; it does not silently accept the props lexical ADR or prove durability.
2. Add independent exactness/presence/U+0000/native identity cases and the NX witness/refusal corpus. Original facet and native representability expectations must be separate from mathematical/lexical equality.
3. Implement bounded exact parsing and pure NX comparison with source bytes retained; validate the complete original token/exponent/facets before zero normalization. Run pure browser/Bun cases through the same portable output.
4. Implement raw native descriptor/text/parameter transport, actual stored source/token/value correspondence and complete row/recursive finalization under selected original context/resource custody. Register/qualify native parsing/facet/correspondence producers before reporting database enforcement.
5. Exercise caller-owned connections, selected adapter/timing/cancellation/containment cases and native identity/concurrency controls. Publish scoped receipts for storage/readback; key, order, predicate and aggregate capability qualification remains separately declared under CR03.

## Risks and Gates

JSONB preserves numeric value but is not a general original-token archive. CONTRACT-001's authored lexical promise therefore requires a concrete carrier/receipt decision before AC1 can pass for the full corpus. Unsupported native scalar widths, float special values, nested presence and unknown values require explicit profile decisions. Driver convenience decoding can irreversibly lose precision before core receives a value. No native roundtrip claim follows from pure codec or parser tests.

### Journal-stage cleanup integration

For a selected journal child-store profile, CONTRACT-001's original stage cohort/snapshot/pending-result and paired observation/DELETE sources participate in RT01–RT06 retention. Whole-operation closure preserves exact original values and allocator/recovery dependencies: child rows cannot be independently evicted, split to fit resources or used as commit proof. Independently admit full original parent/stage membership and current eligibility, reobserve under exclusions, compare complete returned snapshots, prove child/parent absence and publish pending capacity/effect evidence atomically. Existing operation/touch cleanup wires remain a separate profile. STP-007's stage-cleanup supplements below specify native race/rollback/uncertainty controls; installer/routines/resource/privilege/descriptor profile selection and actual native runs remain open.


## Formal Specification: capacity reservation transfer

Affected slice: native operation/touch custody capacity under CONTRACT-001 and
CONTRACT-009, supporting US-007-AC1/AC2's complete atomic storage and exact
readback. Truss owns this transfer protocol; UMF owns metadata semantics and the
security owner supplies current authority. Chosen level is precise specification
plus bounded executable transition analysis, pending native implementation
correspondence. This extends the existing formal-methods concern; it does not
strengthen a model-only result into a protected-engine support claim.

The state contains the complete abstract retained-row inventory and its observed
row/byte counters, one active reservation's immutable initial and remaining
budgets, original rollback inventory, issued-attempt count, cumulative application
work and unknown-containment quarantine. Start with one previously retained unit
row and no reservation. Reserve atomically enters prepared custody before registry
insertion; registration consumes one row/byte unit and enters active custody.
New touch/growth consumes remaining budget; shrink changes retained bytes without
refunding spent growth. Finalization clears only remaining capacity. Confirmed
rollback restores the original native inventory but leaves issued ordinals and
spent work unchanged. Unknown containment permits no new work. Host commit is
allowed only after reservation clearance. Original full operation/guard validation
is an assumption at these abstract transitions, not an algorithm supplied here.

| Property | Required invariant and authority |
| --- | --- |
| CR-01 retained parity | Observed retained counters equal the complete inventory, including prior finalized custody; CONTRACT-001 persistent parity/RT and US-007-AC1/AC2. |
| CR-02 capacity conservation | Nonnegative retained plus remaining reservation never exceeds original row/byte caps; CONTRACT-001 capacity admission. |
| CR-03 cleared slot | Cleared custody has no remaining/initial/consumption/snapshot state; empty slot is not complete commit authority; CONTRACT-001 OC and capacity protocol. |
| CR-04 no spend refund | Remaining equals immutable initial budget minus consumed positive deltas; shrink cannot recharge the operation; CONTRACT-001 accounting and CONTRACT-009 original operation budgets. |
| CR-05 work monotonic | Local rollback cannot refund cumulative application work; CONTRACT-007/009 original enclosing account. |
| CR-06 ordinal monotonic | Rolled-back attempts retain issued ordinal gaps; ADR-008 and original issuer custody. |
| CR-07 unknown quarantine | Unresolved containment cannot resume ordinary work; CONTRACT-007 recovery. |

The [Python finite model](../../04-build/evidence/design-audit/capacity_reservation_model.py)
exhaustively explores three retained/reserved rows, five byte units, two issued
attempts and twelve application-work steps. Units abstract original exact byte
lengths; complete semantic identity, per-row codec/native overhead, issuer/security,
lock order and atomic native effects are assumptions outside this graph. Separate
containment remains possible after the application budget is spent; this model
proves no real cancellation/containment deadline. No fairness or liveness guarantee
is claimed. Reachable commit and recovery witnesses establish non-vacuity only.

The current receipt records2386 states/4770 transitions and seven negative
controls violating their intended properties. Its recovery witness includes
registered B effects before B rollback with finalized A surviving. The earlier
model/receipt are retained as initial evidence; their B witness stopped before
registry insertion and cannot supply that stronger recovery example. There is no
reviewed correspondence to enforcing native procedures yet. The reservation SQL
CHECKs and34 native schema observations cover structural shape only. Implement
and independently map original reserve/consume/finalize/rollback/commit procedures
and enabled guards, then replay concrete witnesses/fault controls before claiming
native enforcement. The full45-story/167-criterion scope remains unchanged.
