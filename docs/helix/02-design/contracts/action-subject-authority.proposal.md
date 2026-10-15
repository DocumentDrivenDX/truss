# Shared native action Subject and role authority

Candidate dependency of US-049-AC2/AC5 and CONTRACT-013, under CONTRACT-005.
Subject enrollment and stock SCRAM login components now have scoped native
evidence below; no complete admitted action provider or delegation is claimed.
This provider is shared by direct action admission
and preparation; worker delegation adds separate obligations.

## Meaning and ownership

The existing `catalog_subject_map` binds a login to a stored ontology Staff key.
It retains that meaning. A Staff entity is not automatically an authenticated
human, and a native LOGIN is not automatically a human either. The deployment's
qualified authentication provider enrolls the association between a native role
OID and an opaque external Subject identity, with an explicit human/service kind.
Truss verifies native connection custody and protected enrollment; it does not
create accounts or infer authentication from supplied actor text.

Use two installation-owned, persistent, private homes:

- `action_subject_binding`: installation identity, native LOGIN role OID,
  external identity bytes and exact kind (`human` or `service`). One binding per
  installation/native role. Identity bytes are nonempty, bounded and compared
  exactly; they are neither a display name nor an ontology key.
- `action_role_binding`: installation identity, original registered action
  namespace identity, exact authorization profile ID/version, exact declared
  role ID, and explicitly enrolled native role OID. The full semantic key is
  unique. Do not infer that an action role string names a PostgreSQL role.

The action namespace comes from the original protected registry and its owner
semantics. Its exact codec must be handed off before DDL is generated; a new
preparation-only namespace convention is forbidden. Role IDs obey CONTRACT-901's
256 UTF-16-unit limit and exact comparison, not a PostgreSQL identifier limit.
Empty roles and unknown profiles refuse. Enrollment resolves OIDs in the same
trusted native installation transaction; a claimed OID or role spelling from a
request cannot create an association. Native role deletion/recreation requires
explicit re-enrollment; administrative provenance and OID-reuse exclusion must
be qualified rather than treating an OID as an eternal identity.

## Original admission procedure

1. Capture the actual authenticated native connecting role/database/backend
   incarnation. No SET ROLE, service substitution, or request-supplied human.
2. Hold source/registry and both protected mapping cuts in the shared lock order,
   then the original role/policy exclusions. Both mapping homes join the data
   transaction's held exclusion inventory through original seal COMMIT; existing
   three-table authority cuts do not cover them automatically.
3. Fresh RC authority reads exactly one original subject association and checks
   current ordinary role flags and issuer/administrative reachability. Require
   kind `human` for `person-required`; a service association refuses this direct
   profile. Missing enrollment refuses even when module access succeeds.
4. Resolve original current action metadata and exact namespace/profile/roles
   from protected source. Resolve each declared role through protected enrollment;
   unknown mapping refuses, never silently drops an interpretation obligation.
   Compute native current membership closure for the captured human. At least
   one declared role must match. Preserve separate module/field/ontology checks.
5. Bind the original human identity, action namespace/revision, complete owner
   scope and mapping/source basis into the same complete native permit. Recheck
   before seal and original completion under retained exclusions. No result
   object, JSON, actor string or copied mapping is authority.

Actual authentication-provider provenance is a premise that native membership
cannot prove. Shared provider registration must name its admitted authentication
profile and custody. An arbitrary administrator-created association is not by
itself evidence that an external person authenticated this invocation.

## Acceptance-linked native qualification

| Witness | Required outcome | Criterion |
| --- | --- | --- |
| Module writer without subject enrollment | Refuse person-required | US-049-AC2 |
| Enrolled service with module/action memberships | Refuse direct human profile | US-049-AC2 |
| Enrolled human with module membership, no exact action role | Deny | US-049-AC2 |
| Explicit `bulk-editor` mapping plus current native membership | Permit only with original authentication/source/permit custody | US-049-AC2/AC5 |
| Case-different, unknown profile, unmapped role, foreign action namespace | Refuse; no inferred role-name mapping | US-049-AC1/AC5 |
| Revocation committed before authority admission while RR sees old grant | Deny from fresh original authority | US-049-AC2 |
| Mapping/role mutation after admission | Block through actual original COMMIT or invalidate before publication | US-049-AC2/AC5 |
| Dropped/recreated principal, forged actor, changed backend or issuer membership | Refuse | US-049-AC2/AC4 |
| Worker supplies original human identity without protected delegation | Refuse; direct preparation cannot qualify worker profile | US-049-AC2 |

All witnesses remain required, not passed. Registry namespace codec, admitted
authentication provider, native homes/installer/helper closure, role lifecycle,
mapping lock ordering and actual bridge consumption are open implementation gates.

## Implemented component boundary

`_action_subject_installation.bootstrap_action_subjects_in_transaction` creates
the private installation-FK-bound Subject home and exact explicit native LOGIN
associations under a trusted quiescent direct administrator. Caller owns COMMIT;
existing homes require migration. Native evidence verifies explicit human/service
kinds, original readback, ordinary caller SELECT/DML refusal and no silent
rebinding. It returns `security_ready=false`; enrollment does not authenticate an
invocation. The native opaque identity bytes remain independent of Staff keys.

[SCRAM evidence](../../04-build/evidence/security-scram-preparation-login-20261014/receipt.json)
qualifies the separate Unix-socket credential exchange component.
[Subject enrollment evidence](../../04-build/evidence/security-action-subject-installation-20261014/receipt.json)
does not qualify protected current observation, role deletion/reuse, mapping cuts,
full helper/DDL closure, action-role bindings or native permit consumption. These
remain required before any action or preparation admission claim.

`_action_role_installation.bootstrap_action_roles_in_transaction` now consumes
the original `ActionRegistration` ticket's retained family/known role obligations,
requires a complete explicit mapping to ordinary NOLOGIN native roles, and stores
the original revision pin separately. Store identity bytes are retained separately
from installation and family. The historical enrollment evidence below used
explicit diagnostic configuration only. The current private enrollment API
requires an original committed `ActionStoreObservation`; it compares the held
immutable native store row, receipt, exact identity fields, installation and
committed issuer before creating role mappings. Raw configuration bytes and
pending/fenced or forged contexts refuse. Current diagnostic role observation
uses the normal RC native store verifier and its operational source cuts.

The private fresh producer checks complete full-byte family/role uniqueness.
A surrogate native key and **nonunique** digest routing avoid oversized B-tree
keys and hash-as-identity assumptions. This is not a database-wide uniqueness
theorem for arbitrary administrative DML: no later native mutation API is admitted.
Qualified migrations/updates, full semantic-key enforcement and mapping writer
closure remain open. Missing, unknown, duplicate or partial declared-role maps
refuse; enrollment itself never evaluates current membership or grants access.

[Native role/enrollment evidence](../../04-build/evidence/security-action-role-installation-20261014/receipt.json)
also retains Astra's addressed pre-pin type-shadowing and missing schema-USAGE
findings, with actual hostile-domain/path-restoration and fresh-service controls.


[Issued-store integration evidence](../../04-build/evidence/security-issued-store-roles-20261014/receipt.json)
replays the actual original source/store producer and complete role-observation
schedule. Initial role DDL remains a trusted quiescent administrative operation:
it cannot hold an operational source epoch SHARE cut that correctly forbids
routine DDL. It therefore uses separate immutable committed-store comparison;
this is not current-source or authority admission. The initial failed composition
and its repair are retained. All observation outputs remain
`security_ready=false`; authenticated human, native guard/anchor, full source
closure and protected selector/finalizer obligations remain open. Guard epochs
remain separate from replay identity. No historical Astra approval is extended
to this new integration and no backend acceptance case is promoted.
