# Public registration-owned rebinding report

Truss native60 adds `truss-catalog-registration-report/0.3` only to registrations
that own rebinding effects. Other registrations preserve their existing report
format. The full original report remains in `CatalogRegistration.report_bytes`
and `CatalogReport.original_bytes`; retry returns those same bytes.

The existing report fields remain present. New fields are `rebindProfile`, with
value `truss-native-catalog-rebind/0.1`, and `rebinds`, ordered by type/object ID.
Each entry contains string `objectId`, `typeId`, `beforeVersion`, `afterVersion`,
plus `effects` and `events`. Each effect contains string `propertyId`, exact
`originalName`, original `definitionPin`, and the exact typed `value` cell.
Each event is the original `truss-journal-exact-bytes/0.2.0-proposal` wrapper:
`component: "event"`, canonical `bytesBase64`, and `sha256`. Decoded bytes retain
the complete rebind presence/definition facts or complete metadata witness and
the ordered history-group digest. No physical bigint JSON fields are exposed.

The inventory comes from immutable transitions keyed by registration ID. It is
independent of current objects and remains readable after mutation or deletion
when current original-owner/property/item read authority permits disclosure.
Registrar authority alone cannot disclose this data. Acceptance, original
report reads, replay and unchanged requests check current disclosure authority.
Whole reports require all original dependencies; a single object's history and
query attribution require that object's original dependencies.

The supported transition moves valid retained cells into new absent-allowed,
non-key scalar/flat-container fields, preserves unmatched values, and increments
each affected object once in the registration transaction. Invalid values refuse
by qualified field and count with rule `property.rebind_value`. Existing rename,
required-field and key guards remain. Required/key backfill and recursive
rebinding are separate unfinished work. Original source references in report0.3
use the same report-local resolution as report0.2.
