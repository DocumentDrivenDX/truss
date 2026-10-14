# Registration-owned rebinding source checkpoint — 2026-10-14

US-008 remains unfinished: existing public writes retain unknown values, but
catalog evolution refuses the matching retained names. Astra reviewed the next
implementation: new optional non-key scalar/flat properties first, followed by
required properties/key backfills and broader recursive values. This does not
narrow the complete feature goal.

`catalog-rebind.sql` adds an unintegrated registration-owned transition and three
native helpers. The transition captures original registration identity, actor,
writer transaction, before/after objects, keys, exact journal rows and effects.
Planned-basis rendering retains the existing original-definition pin recipe.
The mutation helper preserves unmatched retained entries, validates each moved
value/destination, increments each affected object once, emits complete per-move
presence/definition facts and a metadata witness/group digest, and checks the
combined object-value bound before persistence.

Astra source review corrected abbreviated rebind facts, extra closed-envelope
members and the moved-value byte-bound omission. Original registration custody
stays in the protected transition/report association. An isolated public-host
installation on PostgreSQL18.6 compiles the table and three function definitions.
The first smoke attempt omitted BEGIN; the corrected host-owned transaction
setup passes. This is source compilation only, not mutation or admission proof.

Required next integration: capture columns/FK/native DDL through UMF; add the
catalog compatibility/effect/report branch; validate genuine registration-owned
transitions in object/journal closure; extend history and complete-entity query
attribution; preserve create/import provenance; add the native59 upgrade and
basic public accept/read/report/history/query/feed workflow. Occupied destinations,
including null, and existing rename/required/key guards remain protected.

The source is not loaded by `_release`, is absent from the current manifest and
has no public callable export. No enabled/released rebinding support is claimed.
Truss23/Weft24 publication is independently confirmed by successful release
workflows38492829110/38492277370.

## UMF storage capture

`scripts/capture-catalog-rebind-storage.ts` now retains the exact storage prefix
in the UMF PostgreSQL adapter and regenerates it with the owner SQL exporter.
Saved-model reload/export equality and deterministic `--check` pass. The core
projection contains all twelve transition columns and the actual referenced
registration/schema-revision primary-key columns. The integer revision FK is a
core Relationship; the UUID registration FK retains its original native
declaration and column/Record correspondence through core references, since
portable UUID key equality is not defined by UMF core. UUID, xid8, oid and JSONB
columns retain their native declarations without invented scalar semantics.
Core validation is valid but incomplete, as expected for retained native meaning.

The generated owner-export DDL, followed by the original helper suffix, compiles
on an isolated public-host Truss23 installation using PostgreSQL18.6. Native
inspection confirms twelve columns and both foreign keys, with registration's
DEFERRABLE INITIALLY DEFERRED timing preserved. All three helper definitions
compile. This remains storage/source evidence: registration, mutation, report,
history and query rebinding are not enabled by this capture.

## Native60 integration candidate

The candidate now loads the owner-export storage and the helper suffix, applies
registration-owned effects before report/head publication, and connects shared
object/journal closure, creation delegation, graph validation, complete history,
entity attribution and committed feed delivery. Reports with effects select0.3
and expose original exact event wrappers; old report regeneration stays unchanged.
Current report disclosure covers all original data dependencies; history/query
checks cover only the selected object's original dependencies. The pure report
serializer still supports metadata-only catalog verification.

Astra's corrections cover same-transaction creation closure, native version guards,
pre/post candidate and report authority, immediate UPDATE readback, scoped readers
and psycopg's literal-percent escaping. Native tests found and corrected the
complete-wrapper journal NULL old_value requirement and UTC journal comparison.
Seven basic final-wheel cases pass45.785s on PG18: UMF0.7/0.8 workflows include
create/register/read/history/query/feed/replay, invalid candidate refusal and one
host-owned create/register transaction; populated native59 upgrade/rollback also
passes. Candidate wheel v9 SHA25674205f73a74f65c03909dd2abd2ab101a770583b1a8bf9b44b48d4ca63a0c8a0,
matching Weft0.4.25/backend30. Python1031-import and Weft11-package boundary checks
pass; workspace Rust checking passes. A broad exploratory mypy invocation reports
existing dependency-stub and implementation typing gaps and is not a successful
package typing claim. Publication and the broader feature goal remain pending.

Final authority correction rechecks every selected object's current-transaction rebind before latest-image selection, so an ordinary later update/delete cannot suppress original registration/writer/reader obligations. Astra confirms the exact diff. Final v10 wheel SHA2566fc5fa25406d1096819c29895fc7d5e98db6e64ff6deaa9720bcbf486fbda1b6 passes the same seven cases52.592s, now including create→rebind→ordinary update→commit at version3. Module boundaries remain1031 imports.
