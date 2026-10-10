# Private native row-image candidate

`codec.sql` preserves all native state/node/scalar user-column binary cells through
PostgreSQL `record_send`, retaining each type OID, explicit NULL and full payload.
The domain prefix selects the row kind and candidate framing version. The scalar's
native numeric datum, original numeric token, temporal instant, original temporal
text and source bytes remain independent cells. No generic JSON or display-string
conversion supplies the image.

The original column validator checks full ordered membership, native types,
nullability, typmods, collation, dropped/array fields and inheritance. Five private
INVOKER routines have PUBLIC EXECUTE revoked. They are data codecs: constructed
composites or matching profile labels do not authenticate an original trigger,
prestate, candidate, installation, subject or operation. Complete deployed routine/
builtin/cast/codec dependency and private role/ACL/DDL closure remain required.

The exact complete frame length is checked before whole-record serialization.
Native text/bytea lengths, fixed-width payload sizes and the original numeric binary
length supply the preflight; serialized output must match that length exactly.
Numeric length measurement still serializes that numeric cell. This candidate does
not qualify pre-materialization/native detoast/numeric-send/record-send/copy/allocator/
deadline bounds. The original admission profile must establish those independently before
using these images for protected effects. An 8-MiB returned image does not mean its
containing retained operation/touch row or all copies fit a resource budget.

Native binary representation is a version-qualified codec, not a portable canonical
UMF value. Reuse UMF/Weft's owner semantics for interpreting original definitions
and logical values; retain these native bytes for native correspondence only. Full
row-image fidelity does not qualify family/association meaning or any of the seven
semantic routine bodies. No installer, ordinary caller grant or public API is added.
