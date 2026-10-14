# Public registration-owned alternate-key backfill report

Native62 registration can add non-primary keys over existing required singular
string, integer, decimal, boolean or binary fields. Existing key definitions and
numbers remain unchanged; new owner-local numbers follow the retained maximum.
Existing/primary-key changes and newly rebound key components remain unsupported.

Acceptance requires affected-module writer authority and complete current
object-property read authority to collect candidates. It obtains original UMF
tuple receipts from locked exact candidates,
recomputes them before effects, and refuses duplicates by document/module/Record/
Key with `key.duplicate` and the number of participating objects. It performs no
automatic retry. Pure key backfill leaves object version, revision, timestamps
and record mutation history unchanged. Unrelated value rebinding still advances
its affected objects normally.

Registrations owning key effects use `truss-catalog-registration-report/0.4`,
`keyBackfillProfile: truss-catalog-key-backfill/0.1`, and ordered `keyBackfills`.
Each entry has string `objectId`, `typeId`, `objectVersion`, and an `effects` array.
Effects retain string key identity/number, original definition pin, canonical
namespace/tuple transport, original owner receipt, membership/reservation IDs,
bucket generations and original context/reservation bytes. All integers remain
exact decimal strings. Existing rebind fields remain when that registration
also owns value effects. Original earlier reports keep their own format/bytes.

Acceptance, original-report reads and replay require current read authority over
original owners and key components. Registrar authority alone cannot disclose
key values. These effects survive later object updates/deletion through immutable
registration storage and the original report. The caller settles the complete
transaction; pending results do not confirm durability.
