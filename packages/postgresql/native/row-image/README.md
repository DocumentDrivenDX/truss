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

The existing-string replacement helper selects UTF-8 JSON string source tokens.
After actual retained-image size checks, it independently decodes OLD and NEW
source and compares each decoded string with its native text under C equality.
It preserves the exact source spelling, including whitespace and escapes. The
other row-image codecs continue to preserve opaque source cells without selecting
this interpretation.

`existing-string-scope.sql` supplies the pending writer's selected object/property
collection: the complete owner/type/property-owner/property tuple must identify
one state, whose entire node/payload membership must be one parentless declared
string root. The writer checks this scope before capture and independently after
all effects. Caller-held owner/catalog exclusions and complete integrity visibility
remain prerequisites; an RLS-visible subset cannot establish completeness. Image
length bounds do not qualify aggregate scan work, detoast, allocation or deadlines.
This selected singleton implementation supplies no general recursive definition,
facet/history validation, readiness, seal, accepted authority or public mutation.

`forest.sql` adds `row_image_forest_original(original_scope bytea) RETURNS void`,
a private read-only physical forest check over the existing retained-image scope.
The original decoder bounds UTF8 JSON to 8 MiB and at most 1,024 images, validates
complete native cell framing and rejects duplicate identities. The forest body
requires declared roots, same-state parents, exclusive child slots and permitted
parent kinds, full-byte map/record identities, contiguous sequence ordinals and
scalar payload parity. An iterative bounded traversal checks every retained node,
including disconnected cycles. Array/index and child scans have bounded quadratic
work; no linear-work or full native resource qualification is claimed.

Native tests compare identical original codec bytes with Python's physical tree
validator, including empty/scalar/null forests, nested containers, multiple states,
a deep chain at the exact image ceiling, and malformed parent/slot/payload cases.
An administrative fixture installs an actual disconnected cycle, successfully
checks native foreign keys immediately, requires both validators to refuse, and
verifies exact original-image restoration after savepoint rollback. It removes
row observers transaction-locally to isolate this check from unfinished admission;
this is not a protected writer route.

Empty input proves an empty retained physical forest only. RF02 complete-scope
integrity and visibility, original current authority, logical definition/member
semantics, native scalar codecs, candidate reconstruction, seals and deferred
commit closure remain separate. This component performs no writes, issues no
proof token and enables no public Python capability. PUBLIC execution is revoked.

`numeric-witness.sql` implements the private NX02–NX05 mathematical component:
`numeric_witness_original(text)` and `numeric_equal_original(text,text)`. The
explicit candidate grammar is JSON numeric token syntax; it does not admit an
original UMF Field or source codec. Each complete UTF8 token is bounded to 65,536
bytes. Full grammar and signed-bigint exponent parsing run before zero handling,
including arbitrary token-bounded leading exponent zeros. Checked normalization
adds the net trailing-zero/fraction adjustment once. Mantissa digits are never
cast to native numeric and exponents never cause power-of-ten expansion.

The ephemeral witness contains mathematical sign, full coefficient digits and
signed exponent. Mathematical zero does not overwrite retained negative-zero,
scale or exponent spelling. Equality decodes both original operands itself and
uses C-collated coefficient equality. PUBLIC execution is revoked; no caller
witness can confer admission. Native tests execute eleven authored witnesses and
seven pairs, malformed complete tokens, both signed exponent endpoints, zero and
normalized exponent overflow, exact byte limit, and independent original-spelling
custody in an administrative temporary table.

This does not replace the registered UMF exact-number APIs, admit source facets,
qualify native representability or shared allocation/work charging, register a
Weft comparator, complete RF05, seal an operation or enable a public Python API.
Million-exponent witnesses are mathematical cases, not PostgreSQL storage claims.
