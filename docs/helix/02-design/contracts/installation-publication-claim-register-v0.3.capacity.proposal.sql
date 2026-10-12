-- Private tombstone capacity candidate. $5 is original verified profile capacity,
-- not a public caller option. Local subset: integer1..1048576 retained identities,
-- original operation bytes1..2048. These are implementation bounds, not semantics.
-- Acquire schema-head SHARE, guard SHARE, capacity table lock first; fresh
-- READ COMMITTED statement after lock acquisition. Commit before disclosure.
-- All registration sources must be covered; uncapped0.2 is incompatible.
INSERT INTO truss.policy_publication_claim
 (operation_identity_bytes,installation_identity_bytes,policy_profile_bytes,generation)
SELECT $1::bytea,installation_identity_bytes,policy_profile_bytes,generation
FROM truss.policy_generation_guard
WHERE singleton=1 AND installation_identity_bytes=$2::bytea
 AND policy_profile_bytes=$3::bytea AND generation=$4::bigint
 AND octet_length($1::bytea) BETWEEN 1 AND 2048
 AND CASE WHEN $5::integer BETWEEN 1 AND 1048576 THEN
  (SELECT count(*) FROM (SELECT 1 FROM truss.policy_publication_claim LIMIT $5::integer) retained)
   < $5::integer
 ELSE false END
RETURNING pg_catalog.encode(operation_identity_bytes,'hex');
-- Zero rows refuses original admission, including exhaustion. No delete, upsert,
-- automatic profile change, retry with a new token or disclosure on refusal.
