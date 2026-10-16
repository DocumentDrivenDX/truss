# Public Python registration summary — candidate

Unreleased native69 / SDK0.0.36 development interface. Database workflows and
Astra review remain pending; this document does not claim release readiness.
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
  "interfaceVersion": "truss-registration-preparation/1.0",
  "documents": [{
    "documentId": "example",
    "contentSha256": "<original document SHA256>",
    "sourceValidation": {"valid": true, "complete": true, "diagnostics": []},
    "targetValidation": {"valid": true, "complete": true, "diagnostics": []}
  }]
}
```

The document order matches the original input. Validation objects and their
complete diagnostics come from the pinned UMF document validator; the example
shows one possible result, not required completeness or empty diagnostics.
Unknown extension/action content stays in the original document. Ordinary
registration does not construct per-operation inspector transcripts, duplicated
assertion artifacts, or an exhaustive assertion-enforcement inventory.
Low-level retained preparation component APIs preserve their earlier formats.

## Accepted report

New ordinary registrations use `truss-catalog-registration-report/0.5`.
Existing top-level registration, actor, revision, origin, accepted-input and
allocated-ID fields retain their meaning. `source` has exactly these fields:

| Field | Value |
| --- | --- |
| `sourceFormat` | `truss-registration-summary/1.0` |
| `umf` | Original UMF version, interpretation and selected-subset memberships |
| `documentValidations` | The preparation summary's ordered `documents` array |

`umf[].supportedSubset` carries the current native catalog capability definition
and its digest. The retained `AcceptanceInput.supportProfile` remains a legacy
preparation selector; the older experimental subset text is not substituted for
the release's actual storage capability in the summary report.

Original document bytes remain in `acceptedInput.documents[].artifact` and the
accepted-document read API. Consumers do not reconstruct documents from
inspection evidence. Existing report-local source references also resolve
against report0.5 through `resolve_catalog_report_source`.

Optional `runtimeFacetEnforcement`, `rebindProfile`/`rebinds`, and
`keyBackfillProfile`/`keyBackfills` retain their existing meanings. Their
presence does not replace the report0.5 format version. Atomic native effects,
compatibility refusals and current disclosure authority remain required.

## Retry and errors

Registration request identity retains the original acceptance-input, archived
source/declaration and asserted-origin bytes, plus installation, actor and
request key. Derived report-preparation bytes are excluded. Changing from an
older report producer to the summary producer therefore preserves original
report replay and unchanged-document detection. Stored reports retain their
original format and exact bytes; retries do not relabel or rewrite them.

An unsupported storage definition returns catalog code `unsupported_profile`;
invalid input returns `invalid_input`. A local catalog refusal is an execution
obligation with no retry, rather than an invalid-transaction diagnosis.
Preparation failures are raised before database calls. Byte, tree-depth,
member-count, node-count and ordinary deadline limits remain; per-character
work accounting is removed.

## Remaining validation

The original pizza, northwind and catalog documents pass local preparation and
storage-support checks with approximately4–6KiB summaries. The500KB source
preparation regression also passes. Actual register/create/read/update/reopen,
predecessor-report retry and matching-wheel query runs remain pending. These
local results establish neither native persistence nor release qualification.
