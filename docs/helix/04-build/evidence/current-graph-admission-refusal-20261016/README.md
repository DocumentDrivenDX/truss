# Current Graph public admission refusal — 2026-10-16

The existing explicit Graph compiler cohort now checks the real reserved ordinary
caller transaction's complete source/data cut after its Subject helper and before
any Graph/fact collection or staging. Verification observes native backend PID,
virtual transaction, current database, actual truss relation OIDs, granted ShareLocks,
and persistent ordinary tables without RLS/inheritance. It acquires no missing locks,
issues no reusable permit, and ignores unrelated extra locks.

Complete cuts still return `QueryRefused(execution_obligation)` before collection:
current authority through public handoff is not yet qualified. A separately issued
epoch token is not a required architecture. A native-lock authority profile may
qualify after routine/schema/ACL/role/dependency stability, ABA, authenticated caller
custody and the private-settlement-to-public-handoff interval are proven. Existing
source-epoch/protection refusals remain in place. Scalar and old presence cohort
selection is unchanged. This is improved public refusal, not authorized Graph SQL.

The installed wheel built on Truss main `dc948aeb` passed three real PG18.6 cases
in 11.076 seconds: complete caller cuts reach the distinct authority refusal;
matching partial helper/registration refuses the missing physical cuts; settled
caller refuses with `stale_context`. The complete case also rejects another real
backend using the first caller's transaction identity. All cases assert no fact or
Graph collector, no evaluation/staging, no public rows and no staging temp table.
Fixture/server cleanup completed. The earlier run expected a host error for the
settled case; its actual safe `stale_context` refusal was correct and the assertion
was corrected before the final run. Two public API tests and 1,581-import boundary
check also pass. Exact build/consumer pins are in `pins.json`; built wheels stay
outside main. The earlier Subject-cut native proof establishes the 25 positive
relation cuts and writer blocking through caller rollback.

Release CI's existing installed current-policy step now includes the Subject-cut
regression. The three Graph cases remain an explicit manual check against the
reviewed local cohort; stable compiler CI does not install that cohort or claim
hosted Graph qualification. No default compiler repin, new job or broad campaign
was added.

Local caller authentication is the existing fixture mechanism, not SCRAM evidence.
No full B-008 case promotion, role/DDL writer closure, malicious-owner containment,
continuous authority, Graph release or Databricks enforcement is claimed. Completed
Astra Ultra review is required before root integrates this frozen increment.
