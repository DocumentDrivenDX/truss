---
ddx:
  id: truss.journal-horizon-initialization-custody
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: CONTRACT-008
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: CONTRACT-011
      kind: informed_by
  schemas:
    - id: truss.journal-horizon-initialization-custody
      version: "0.1"
      title: Native journal horizon initialization custody
      path: docs/helix/02-design/contracts/journal-horizon-initialization-custody-0.1.schema.json
      schemaFormat: json-schema
---

# Journal horizon initialization custody

## Purpose

Fresh native0.76 admission MUST recognize authentic calendar-dependent journal
partition bounds without changing the initializer or admitting arbitrary bounds.
This contract governs private installation custody and administrative verification.
Its profile is `truss-journal-horizon-initialization/0.1`. It establishes no
execution evidence or migration route by itself.

## Scope and boundaries

The selected package is0.0.56, native0.76, PostgreSQL18.6. Initialization zones
are exactly `UTC` and `America/New_York`; unsupported zones refuse before DDL.
The existing `groups.sql` source unit, including both `clock_timestamp()` calls,
MUST execute once, byte-identically and in its original relative order. Its
required SHA-256 is
`8d213c5b1243b2839c1ca6a465a709f20b5e03048da184bd58dea87d04ec95dc`.
Do not
set its clock, timezone or bounds to make a fixture pass. The wrapper may split
DDL submissions at this source-unit boundary, without splitting/parsing its SQL.

New private custody storage, bounded read-only observations around that unit,
and transactional persistence are permitted baseline changes. They require a new
exact native manifest digest and fresh installed observations. Native0.75,
published0.0.54 and retired source evidence remain unchanged. Populated0.0.54
installation/migration attempts MUST refuse before effects; no witness backfill,
startup migration, historical admission or current-date repair is introduced.

## Trust boundary

The trusted installing host, guarded installation callback, PostgreSQL backend,
qualified server clock/timezone rules, private NOLOGIN owner and approved managed
platform administrators are inside the existing administrative trust boundary.
The caller's ordinary registrar/writer/reader/audit/feed roles are outside it.
Only trusted installation code can supply the private writer; public APIs accept
no witness, anchor, zone override or caller-supplied capability.

A database/OS administrator or compromised installing host can rewrite SQL,
custody and clock together. This profile does not claim tamper resistance against
that administrator. A digest proves byte consistency, not a signature or clock
attestation. Clock monotonicity within the bracket and stable session timezone
are trusted platform assumptions. Detected clock reversal, unsupported timezone,
window overflow or inconsistent bounds MUST refuse; never retry internally.
A change to timezone rules that changes retained derivation MUST refuse pending
explicit qualified recovery, rather than reinterpret an existing installation.

## Normative surface

The schema companion owns the closed witness shape. The private relation is
`truss.runtime_initialization_custody`: exactly one row per installation with
`installation_id uuid PRIMARY KEY`, `witness_bytes bytea NOT NULL` bounded to
16KiB, and stored/generated SHA-256 integrity over those exact bytes. Its foreign
key identifies the original `catalog_runtime_installation.installation_id`.
Private owner, table/type/column/default ACLs, immutability trigger and any helper
routine definitions are part of the exact native baseline. Ordinary roles and
PUBLIC have no table write/read or mutation-helper authority. Existing managed
platform trust is not expanded; supported policy combinations retain complete
ordinary effective-rights checks. No broad managed-role exception is added here.

The row's payload uses the existing migration canonical JSON codec, with no float
or timestamp coercion. Reject duplicate JSON keys, extra fields, noncanonical
bytes and a digest inconsistent with those exact bytes. Schema integer fields require exact integers, not Boolean
values; all digests are lowercase64hex. The witness includes:

- Exact installation UUID, database OID, original private owner OID, backend PID
  and native transaction ID; these bind one guarded installation context.
- Native manifest digest, exact unchanged `groups.sql` digest and qualified
  `_initialization_custody.py` producer digest. The latter is pinned by the
  new baseline policy, not supplied by an ordinary caller.
- Actual initialization timezone, UTC clock endpoints, complete derived candidate
  endpoint pairs, and the original complete canonical-UTC relation inventory row.
  Its original partition-bound text at index7 remains literal evidence.

`clockBeforeUtc` and `clockAfterUtc` are finite native microsecond instants in
`YYYY-MM-DDTHH:MM:SS.ffffffZ`, positive Gregorian years1..9999. Reject rather than
round noncanonical/unrepresentable values. Derived endpoints must fit the same
range. Obtain these values through exact PostgreSQL expressions; Python wall time,
`transaction_timestamp()`, genesis time and installation-marker time are not
substitutes. Resource timeouts/deadlines remain independently enforced.

### Capture and publication

Under existing installer exclusion and the same guarded cursor/transaction:

1. Perform all existing source/cohort/administrator/existing-schema checks before
   custody work. Observe the actual session zone and backend/transaction identity.
2. Immediately before submitting the original `groups.sql` unit, read native
   `clock_timestamp()` as `clockBeforeUtc`. Execute that unit once, unchanged.
3. Immediately after it returns, read native `clock_timestamp()` as
   `clockAfterUtc` and re-observe zone/backend/transaction. Require the same
   identity/zone, `0 <= after-before <= 300000000` microseconds, and at most one
   local calendar-month boundary. A native transaction-ID assignment for custody
   is permitted; no independent transaction, COMMIT or second installer exists.
4. Derive the complete finite candidate set from that window as below. Observe
   the actual relation row only after initialization, using the existing UTC
   inventory observer; restore every caller setting it temporarily changes.
5. Check the actual bound against that independent candidate set. Finish original
   DDL/grants/ownership checks, bind the actual installation UUID, then insert
   the witness once through the private installer path. Publish installation and
   custody atomically. Verify complete final definitions, ACLs and witness before
   returning pending installation. Do not capture by verifying against an
   already frozen literal calendar inventory.

Pre-DDL failures use the existing `InstallRefused(code="incompatible")` route.
A post-DDL custody failure MUST raise a private containment exception: map it to
that refusal only after the existing host reports confirmed contained rollback
and no cleanup error. Unknown rollback/commit, deadline and cleanup failures retain
existing Error/recovery custody. Never return a successful refusal with DDL left
inside a live caller transaction. Caller work preceding the operation survives
only where the existing savepoint contract guarantees it.

### Window-derived bounds, including two reads

Let `a` and `b` be the retained endpoints and `Z` the retained initialization
zone. Derive using native PostgreSQL18.6 date/interval semantics in `Z`, then
render under the existing UTC native-bound deparse profile. Use no current clock.
The initializer assigns lower then upper with independent clock reads. Therefore
admit exactly pairs for which there exist `a <= tL <= tU <= b` and:

```
L = date_trunc('month', tL) - interval '1 month'
U = date_trunc('month', tU) + interval '13 months'
```

Enumerate months intersecting `[a,b]` in `Z`, not months inferred from observed
bounds. A same-month window yields exactly one pair. A window crossing the one
allowed boundary yields old/old, old/new and new/new pairs; new/old is forbidden.
Deduplicate and sort by exact lower then upper instants. Compute month arithmetic
in `Z`, including each endpoint's actual DST offset; fixed-day/month durations or
applying today's UTC offset are forbidden. Each candidate's native serialized
bound must equal the observed literal at index7. Native recomputation is trusted
only after its exact qualified SQL/profile is verified; never execute bound text
as SQL or invent a permissive timestamp parser.

The native derivation helper MUST reconstitute finite exact parameters using
round-trip-checked PostgreSQL values; it may temporarily select retained `Z`
inside the administrative read transaction, but must restore prior settings.
Store both endpoint instants before rendering candidate bound text in UTC.
Native bound rendering must match the existing canonical inventory observer,
including quoted endpoints; compare whole bound strings, not a broad regex.
No library-local calendar or timestamp-value codec replaces PostgreSQL.

The protected witness records the complete candidate set, even though exactly
one pair produced the original row. This does not claim either internal clock
read was directly observed. It proves bounded compatibility with their genuine
execution window under the stated trust assumptions.

### Future verification, backup and preservation

A new profile key `initializationPolicies` may contain exactly one closed policy
for surface `relations`, identity `["journal_runtime_horizon"]`, boundIndex7,
custody relation/profile/schema digest, initializer/producer digests, the two
zones and maximum window300000000. Select it only for the exact new0.76 native
manifest. The policy has exactly these keys: `profile`, `surface`, `identity`,
`boundIndex`, `custodyRelation`, `witnessProfile`, `witnessSchemaSha256`,
`initializerSha256`, `installerSha256`, `qualifiedTimeZones`, `maxWindowMicros`.
`profile` is `truss-journal-horizon-admission/0.1`; `witnessProfile` is the
contract profile above; `qualifiedTimeZones` is exactly
`["America/New_York","UTC"]`; `maxWindowMicros` is the string `"300000000"`.
`witnessSchemaSha256` is `4e5cd88be2eff7152f744053323103dc758f9e3922cee780e5653ae64fc112c4`.
Initializer digest is the unchanged unit pin above; installer digest must be the
actual qualified helper bytes, filled from genuine source before captures. No
placeholder policy is executable. Duplicate policy identities/unknown keys refuse.

Existing `initializationAlternatives` and historical profiles retain
their exact finite-row meaning; do not reinterpret them globally.

First verify every static native definition/ACL, including custody storage and
its read/write boundary, with only this relation's bound field deferred. Then
read exactly one protected witness using direct qualified catalog/table reads.
Validate schema, digest, source/context identities, finite window and independently
re-derived complete candidate set. Require all other cells of the horizon row to
match the exact baseline and require its entire actual row to equal the stored
original row. The current observer timezone is immaterial and must be restored.
Backend PID and writerXid are historical installation provenance, not a demand
that later verification reuse that process/transaction. Live installation UUID,
database OID and original owner binding must match; timestamps/candidates remain
from the historical bracket. Enforce writerXid as positive native uint64, with
no JSON float, signed, overflow or Boolean coercion.
Missing, malformed, cross-installation, substituted or non-derivable custody
refuses. A self-hashed caller JSON file is never sufficient authority.

`matches_inventory` alone MUST NOT admit a policy from a timestamp-shaped string:
it needs the verified private custody context. Reconnect/status/backup later use
stored initialization endpoints; no freshness expiration based on the current
month is imposed. Existing journal horizon expiry remains real: this contract
never extends, replaces or auto-maintains the finite partition.

Backup includes original witness bytes/digest and original bound row. Future
qualified migrations must preserve both exactly, even when application release
identity advances; no migration route is enabled here. Preserve the original
installation manifest identity separately from any later active target. A restore
with changed database/owner identity needs the existing explicitly qualified
restore/remapping procedure; do not synthesize fresh installation custody from
the restored bounds or silently remap identifiers. In its absence, refuse.

## Error semantics

Missing/stale/corrupt custody, invalid window/zone, changed timezone derivation,
bound mismatch, additional relation changes or ACL drift close readiness. There
is no repair, fallback to finite calendar rows, clock override or automatic retry.
Administrative verifier failure leaves inventory/data unchanged. Later native
shutdown and capture cleanup follow existing confirmed-stop requirements.

## Examples

A UTC November window wholly within that month derives October1 through
December1 of the following year. A December window derives November1 through
January1 of the year after next. These are different genuine initializations of
the same native code, not equivalent literal inventories.

For a UTC window spanning November30/December1, the old/new pair derives
October1 through January1 of the year after next. It is valid for the two reads;
a single assumed month anchor would incorrectly reject it. A new/old pair is not
admitted. These examples specify derivation tests, not historical native captures.

## Schema basis and evidence limits

CONTRACT-008 bootstrap meaning and the retained
`truss-runtime-migrations-0.1.umf.json` model distinguish exact native source,
original inventory and immutable receipt bytes. That model uses UMF0.10.0 and
`umf.postgresql`0.1.0 to retain PostgreSQL meaning; it is not rewritten.
The witness is a Truss-private native-administration evidence carrier. JSON
Schema2020-12 expresses its closed transport shape; PostgreSQL owns timestamp,
timezone, partition and privilege semantics. No new UMF FieldView, Weft compiler
or public temporal value meaning is defined. The JSON schema cannot establish
native authority, ordered execution, real time or successful qualification.

Primary semantics: [PostgreSQL18 date/time operations](https://www.postgresql.org/docs/18/functions-datetime.html)
and [PL/pgSQL declaration defaults](https://www.postgresql.org/docs/18/plpgsql-declarations.html).
The [build plan](../../04-build/journal-horizon-custody-plan.md) and STP-045
sequence source/native controls and genuine two-zone captures.
