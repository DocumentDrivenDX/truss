---
ddx:
  id: truss.native-source-observation.design
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.native-source-binding.design
      kind: informed_by
    - id: CONTRACT-013
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
---

# Native source observation

This isolated implementation spike extends the incomplete native-binding design,
not the current consumer registration. Baseline is Truss59360445. CONTRACT-013's
structural0.1 packet remains frozen and rejects the proposed0.2 inventory; it must
not be weakened or implicitly migrated. This proposal needs independent review.

## Required observation

Use the original stock psycopg host operation and borrowed native cursor. Retain
exact accepted-request and complete runtime manifest bytes. Acquire original
accepted-catalog source table SHARE cuts and the three current native homes
`edge`, `object`, `object_key_bucket`; verify the original source cut. Require
PostgreSQL18.6, READ COMMITTED, read/write transaction. Original accepted-catalog
assessment verifies durable registration sources/reports and installed release.
Keep a second exact native assessment from fresh original JSONB text rows under
the same source cuts. Do not pass fractional JSON through Python binary floats.
Original authored documents and unknown content remain unchanged; PostgreSQL's
canonical JSONB output is a native observation, not the original authored bytes.

Observe actual system identifier/database OID/name, schema OID/name/owner and
installed runtime identity. Missing privilege for pg_control_system is a refusal,
not permission to invent a system identifier. For each selected home record
actual relation OID, namespace, owner, kind/persistence/RLS/inheritance, every
positive user attnum/name/typeOID/typmod/collation/flags/default expression and
all relation constraints with native identity, definition and flags. Column
expression data explicitly distinguishes `none`, `default` and `generated`;
pg_attrdef source for a generated column MUST NOT be labeled as a default. Names are
locators; neither equal names nor reusable OIDs establish continuity or permission.
Permanent unfiltered noninherited owner tables are the selected physical subset.
Dropped columns refuse. No row-home store is inferred from its declaration.

Native SQL deparsers provide native default/constraint observations; no adapter
parses or executes those expressions. Metadata is not comparator/codec equivalence.
Existing source/routine/role/DDL authority guards remain required separately.

## Versioned data surface

Inventory `truss.native-source.inventory/0.2-candidate` includes explicit schema
owner, relation namespace/flags, complete selected-home coverage, defaults and
constraints. Assessment is `truss.accepted-catalog-assessment/0.2-candidate` with
raw strict-scanned native row fragments; the original0.1 verifier's bytes remain
retained separately and are not used as exact fractional inventory. Report
`truss.native-source.observation/0.2-candidate` references all four original sources
and has complete/authority/securityReady=false, nativeAdmission=required. It is
data, not a native witness or permission. Field/Key/edge/codec mapping, actual
source continuity, held authenticated authority and closing release remain open.
No JSON reconstruction imports a native authority capability.

## Capacity and failure

The four binding-original byte surfaces each1..4,000,000 bytes. The additional
legacy verifier diagnostic is separate, bounded by its original16MiB maximum. The original verifier
keeps its independent16MiB retained budget; the new bound is not a peak-memory
claim or a pre-materialization wire bound. Stock driver/host deadlines apply.
Original owner JSON scanner limits apply independently to each JSON source:
512-character numeric tokens;4096 members/items per container; depth128;
1,000,000 visited nodes; duplicate keys, invalid Unicode and nonfinite values
refuse. Accepted modules1..256. Native catalog arrays at most4096 rows each;
selected homes exactly3; positive user columns1..1600 per home; constraints at
most4096 per home. Budget default/constraint text before fetching detail rows,
verify complete census and final encoded aggregate bytes. Unsupported capacity
refuses the whole result, with no truncation or inferred absence.

The observer does not commit/rollback or restore a failed caller transaction.
Its host must contain failure and restore state. Successful search_path is
restored. Relation SHARE cuts remain to caller settlement; they do not establish
schema/database/routine/ACL exclusion or absence of same-transaction/ABA changes.

## Required tests

Pure tests must expose the legacy fractional-number round trip and prove exact
raw-fragment preservation, malformed/duplicate/Unicode/capacity refusal, canonical
native identity/flag forms and data-only report behavior. Native tests must use
owned disposable PostgreSQL resources and actual original host/cursor: observe
an accepted model, original manifest and all selected homes; independent queries
must match OIDs/attnums/defaults/constraints; external writers/DDL must conflict
with held relation cuts. Native RLS/owner/inheritance/column changes must refuse
or change the explicit observation, never preserve a stale matching descriptor.
Verify savepoint restoration and owned fixture cleanup. Original0.1 consumer
cohort/registration is unchanged. Neither these tests nor pure metadata qualify
NSB-T03/T15/T16 or any shared backend case completely. Shared158/34 scope remains
45implemented/113missing, with all original132 requirements retained.

## Scoped execution checkpoint

Six supplied-row tests pass, including the isolated legacy JSON float round-trip
counterexample. This is not proof that a currently admitted native facet can
reach that old path; current numeric facet examples use integer precision/scale.
The new exact assessment avoids depending on that numeric representation. No
legacy assessor, registration or public consumer is modified.

Four original-host native tests pass on59360445/PostgreSQL18.6: actual accepted
source/release and selected metadata correspondence, six external DML/DDL lock
refusals, wrong-source refusal, RLS-home refusal and changed/restored column
metadata. Exact restoration can reproduce identical data without proving
continuity; the report remains authority=false. Initial test callback arity
failed before observation, making initial negative assertions non-evidence;
corrected callbacks and explicit positive preconditions pass4tests/8.602s.

The first actual inventory retained generated=s but mislabeled its pg_attrdef
source as defaultExpression. R1 remains frozen; R2 uses explicit expression
kind/source and refuses inconsistent generated/missing-source metadata. Native
independent expectations now cover all32 columns’ nullability/identity and all
default/generated expressions, including both stored key-bucket sha256 columns.
This corrects native metadata meaning without adding an expression interpreter.

Astra identified two further R1 qualifications: runtime manifest bytes bypassed
the declared scanner/4MB cap, and the505 selected source pins omitted imported
test_preparation plus its capacity fixture. R2 scans/bounds the manifest before
release use and adds an actual-source-path negative test. The new native archive
includes the complete test tree and contract-binding fixtures, checks imported
project Python closure after execution, and retains R3 as selected-endpoint
evidence. These are source/capacity repairs, not native authority admission.
