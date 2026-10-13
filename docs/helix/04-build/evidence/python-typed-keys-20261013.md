# Public typed business keys — 2026-10-13

The next runtime0.40 candidate connects UMF's original0.7/0.8 tuple producers to
public rootless scalar object creation, key updates, lookup, imports and
KeyAbsent preconditions. Admitted key families are string, integer (including
signed64), decimal18/4, Boolean and binary. Existing string callers remain valid;
typed lookup uses existing TextValue/BooleanValue carriers. Timestamp/float
identity is undefined upstream and is refused.

Native byte-to-cell checks follow UMF's original UMFK1 grammar against actual
accepted property families/facets. Decimal spellings1.2300/1.23000 share a tuple;
raw stored values and request fingerprints keep their original tokens. Actual
object rows and buffered logical lookup results are both checked. Immediate and
deferred finalization, import identity/provenance and preconditions use the same
comparison. Original string namespace/transport recipes remain byte-identical,
so reservations and old memberships remain reachable.

Mutation and import-key profiles are versioned. Exact historical committed
requests replay before current-profile admission; a historical profile cannot
create a new group on a miss. Legacy import encoding profiles are allowed only
with exact pins and all-string components. Upgrade0.39→0.40 preserves routine
custody, reports, receipts and source history; new private helpers receive owner
ACLs and the existing final ACL check refuses unwanted default grants.

Basic installed tests cover original0.7/0.8 composite keys, duplicate mathematical
decimal equality, key update/reservation, read-only lookup, failed preconditions,
import create/retry/skip and original committed replay. Astra's missing-profile
NULL-safety and create-key refusal-order findings have regression assertions.
The populated upgrade seeds the actual publishedv0.0.2 package, then continues
writes and replays its old mutation profile. Matching Weft0.4.5/backend0.4.10
preserves existing numeric queries; query pages and relationship-key projections
remain string-only and are a separate feature tranche.

Final five-test installed run passed46.698s after native family/domain
prevalidation for create, key conditions and imports. Existing native22023
refusals stay typed group failures or contained per-record import rejections;
Bun/host failures keep their separate handling. Astra Ultra approved the plan
and completed source after these concrete fixes. Public consumer typing and
Python module boundaries pass. These are basic functionality/real defect checks,
not full corpus, performance or protected-engine qualification.
