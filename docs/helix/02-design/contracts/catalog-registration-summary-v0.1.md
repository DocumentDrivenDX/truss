# Public Python registration summary — candidate

The native71 / SDK0.0.39 registration summary is published. The next update
unifies every public preparation entrypoint under a source-only format. This document describes the unreleased native72 candidate;
publication and complete workload qualification remain pending.
This supplements [CONTRACT-003](CONTRACT-003-catalog-revision.md).

## Preparation and source retention

`prepare_catalog` and `ReferenceAssembly.prepare_catalog` validate the original
UMF0.7/0.8 document and collect its storage declarations. They retain the exact
original bytes and the caller's independent document revision. An absent Field
`name` binds the Truss property to that Field's stable `id`; it does not add a
name to the UMF source. Duplicate resulting property names refuse.

`PreparedAcceptance.report_evidence_bytes` remains available for compatibility.
Its ordinary-registration content is UTF-8 JSON:

```json
{
  "interfaceVersion": "truss-registration-preparation/2.0",
  "documents": [{
    "documentId": "example",
    "contentSha256": "<original document SHA256>",
    "validation": {"valid": true, "complete": true, "diagnostics": []}
  }]
}
```

The document order matches the original input. Validation objects and their
complete diagnostics come from the pinned UMF document validator; the example
shows one possible result, not required completeness or empty diagnostics.
Unknown extension/action content stays in the original document. Ordinary
registration does not construct per-operation inspector transcripts, duplicated
assertion artifacts, or an exhaustive assertion-enforcement inventory.
`prepare_acceptance`, `prepare_core08_acceptance`, `prepare_catalog` and the
assembly convenience method use the same implementation and summary. Their
existing signatures and caller-selected configuration remain supported; none
constructs an inspector transcript. Historical stored report formats remain
readable and replayable without regenerating their original preparation data.

## Accepted report

New ordinary registrations use `truss-catalog-registration-report/0.6`.
The receipt holds registration, installation, actor, revision, request, origin,
release and source-digest identities. It references the original document and
validator results in `schema_doc`; it contains no source base64, declaration
snapshots, or repeated allocated-definition inventories. Current catalog APIs
return usable normalized definitions. Historical stored reports retain their
original format and exact bytes.

The source format is `truss-registration-summary/2.0`. It records UMF version
and selected capability memberships, the producing runtime release, document
hashes and validation status, and `validationLocation: schema_doc.validation`.
Full validator diagnostics remain with that document, once.

The original document is stored once in `schema_doc`. A modern registration
request uses `truss-acceptance-input/0.2.0` with artifact identities and SHA256
references. Its stored `document_bytes` and `declaration_bytes` are empty;
compatibility views derive from the archived original source on demand.
`PreparedAcceptance` likewise retains the original bytes once, one validation
result, and the descriptor. The compatibility declaration/archive properties
are derived when accessed. Original core0.7 sources do not acquire an implicit
migration receipt or duplicate core0.8 target document.

The immutable definition index stores coordinates and pins for efficient
mutation lookup. Original fragments are read from `schema_doc` on explicit
request, never stored again in this index. New definitions do not create
redundant insertion snapshots in `schema_change`. Changes to existing definitions
still preserve exact before/after history, including historical interpretation.
Legacy stored insertion snapshots are preserved.

## Retry and errors

Registration request identity binds the exact descriptor, original archived
source and validation, and asserted origin, plus installation, actor and request
key. Original source whitespace remains significant. Derived declarations do
not create a second identity or storage home. Derived report-preparation bytes are excluded. Changing from an
older report producer to the summary producer therefore preserves original
report replay and unchanged-document detection. Stored reports retain their
original format and exact bytes; retries do not relabel or rewrite them.

An unsupported storage definition returns catalog code `unsupported_profile`;
invalid input returns `invalid_input`. A local catalog refusal is an execution
obligation with no retry, rather than an invalid-transaction diagnosis.
Preparation failures are raised before database calls. Byte, tree-depth,
member-count, node-count and ordinary deadline limits remain; per-character
work accounting is removed.

## Resource math and qualification

The unchanged many-types workload contains1000 records,12000 properties,
2000 keys and1000 relationships in a2,528,638-byte document. The native72
candidate preparation retains approximately2.7MB including its validator
result. A local PostgreSQL18.6 registration used approximately12MB across
source, normalized definitions, pin index, request and report, including native
indexes, TOAST and page allocation. This is a measured example, not a memory
limit or a claim about every1000-type schema.

The existing16MiB complete planned-catalog bound remains after removing
insertion snapshots; the unchanged1000-type schema now fits. Source documents
remain bounded at4MiB each, the catalog at65536 definitions and512 documents,
and the complete ingress at16MiB. Ordinary operation parameter limits remain
4MiB; the catalog-only ingress permits16MiB. SQL deadlines remain10seconds
per statement and30seconds per operation. V8 retains its512MiB hard heap
limit. Peak process RSS includes engine/runtime and transient parsing allocations
and must be reported separately from retained payload and database storage.

Local preparation, real-schema registration/replay, populated native71 upgrade
and all11 stress-schema registration checks have passed individually. Complete
load/read/update/reopen workload qualification, cross-platform CI and release
publication are still pending; schema registration alone does not qualify those.

## Compact catalog views

The candidate uses view profile0.4 and wire `truss-catalog-view/0.2.0`, defined
by [the schema](catalog-view-v0.2.schema.json) and
[TypeScript binding](bindings/truss-catalog-view-v0.2.d.ts). It sends ordered
dependency pins and source-fragment hashes rather than repeating full references
and base64 fragments. The extraction profile appears once per view. Provenance
still identifies the exact archive, digest and pointer. Native definition pins
and their recipes remain unchanged.

Python entries retain one shared source string per archive and source offsets.
`entry.definition.bytes_base64` derives exact compatibility bytes when accessed;
it is not retained per entry. `view.original_bytes` is likewise derived when
requested. The unchanged1000-type case produces a12,456,454-byte complete view
of16000 definitions, within the existing16MiB cap, and keeps one source string.
The old0.1 wire schema remains available for historical consumers.

Receipt0.6 stores only effect counts for rebinding and key backfill. Their
complete history remains in its existing native homes. Authorized
`accepted_document_in_transaction` reads return `validation_bytes` for the
original UMF validator diagnostics; those diagnostics are not copied into each
receipt. Source-reference receipts cannot resolve their original bytes through
the standalone historical report resolver; use the authorized source API.
