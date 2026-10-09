# Direct lookup contract walkthrough — missing object

Status: author review of a concrete case design, not the independent
implementer walkthrough required by US-027/028 and not an executed corpus
case. Inputs are the current direct-read, execution and history declarations,
CONTRACT-004/007/011, and the conformance case grammar. This example exercises
the actual `DirectReadCapability.lookup(transaction, request)` method; it
does not introduce a new read API.

## Starting state and input

Admit one real installed composition, accepted object type and public direct
read capability. Freeze the type's actual `typeId`, `definitionPin` and
qualified owner `{documentId,moduleId}`, the active catalog revision, exact
layout/read pins and authorized scope identity. Independently observe a
selected object ID absent from the complete qualified lookup namespace under
the admitted original cut. Do not assume absence from a large number, allocator
gap, empty caller result or a role-filtered prefix. No concurrent fixture
writer is admitted between this observation and the held test transaction.

The input artifact carries the existing `DirectLookupRequest` object:

```text
context:
  catalogRevision: actual admitted revision
  layoutProfile: exact installed layout pin
  readProfile: exact registered direct-read pin
  authorizedScopeIdentity: actual admitted scope
  consistency: {kind: live}
selection:
  operation: object_id
  type: {typeId, definitionPin, owner: {documentId, moduleId}}
  id: independently established absent object ID
```

These are explanatory field descriptions, not substituted runtime values or a
JSON fixture. `DirectLookupRequest` has no interfaceVersion member. The setup
artifact owns the actual state, context and transaction registration; the
input step references its original adopted scope. The runner resolves any
permitted case references before constructing this unchanged public wire.
This missing ID is literal test selection, not a new allocated result alias.

## Required outcomes and boundaries

Inside the original live adopted transaction, require the entire lookup result
`{status: 'ok', value: {outcome: 'not_found'}}`. The inner not_found is a business
result; an outer execution error or inner unavailable/invalid is a failure of
this case. No record member is permitted. Lookup does not commit or roll back
the adopted host transaction. Observe its result at the pending boundary, then
have the trusted harness confirm termination independently before committed
state expectations. Savepoint release is insufficient termination evidence.

If a separately registered case wraps lookup in `Executor.withTransaction`,
its outer result is instead the execution outcome containing
`{value: lookupOutcome, durability: 'committed'}`. Compare both layers and the
original termination evidence; do not flatten one into the other or promote a
callback's not_found to proof of commit. That owned variant is a distinct
registered procedure, not an adapter-selected fallback for this adopted case.

The state expectation compares the complete selected canonical and applicable
derived/reservation/request inventory against its independently captured
starting state. The journal expectation requires no additional events from
this lookup, preserving the original starting journal rather than requiring
the whole database journal to be empty. The report expectation requires no
new acceptance/import/enforcement report from this read, while preserving
existing immutable reports. All four normative sections remain present;
absence of a new report is an explicit observation, not an omitted section.

## Refusals and remaining implementation outputs

Independent controls must change the selected type pin, return an outer error,
add a forbidden record to not_found, alter a canonical row, emit a journal
event, mutate an existing report, flatten owned/adopted result layers, and
label callback return committed without host termination. Every control must
fail its applicable normative comparator; equal final counts are insufficient.

The existing request/result carriers are `direct-lookup-request-v0.1.schema.json`
and `direct-lookup-result-v0.1.schema.json`, with shared cursor, exact-value,
history and direct-page dependencies. Reuse them; no new request/result wire is
needed. The proposal `direct-lookup-execution-outcome-v0.1.proposal.schema.json`
composes the existing outer Outcome and inner result plus execution-failure
schema. It adds no public field and does not qualify termination.

Closing this case requires exact registration of those existing schemas and
the outer composition, registered setup/transaction and observer procedures,
actual immutable fixture and expected bytes, complete identity paths where
applicable, and native no-write/termination witnesses. The current envelope
schemas cannot fill those semantic artifacts. A contract-only implementer must
review the complete packet without importing writer implementation helpers,
record remaining ambiguities and then implement the selected adapter. This
author walkthrough exposes that handoff; it does not discharge independence
or native qualification.
