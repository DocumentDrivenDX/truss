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
