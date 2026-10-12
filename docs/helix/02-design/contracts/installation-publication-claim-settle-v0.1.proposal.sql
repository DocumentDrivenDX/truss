-- Only original admitted recovery/publication owner after all protected release
-- has completed or was conclusively withheld. Never use timeout/probe as closure.
-- Acquire original schema-head then guard SHARE; confirm actual DELETE 1/commit.
DELETE FROM truss.policy_publication_claim
WHERE operation_identity_bytes=$1::bytea AND installation_identity_bytes=$2::bytea
 AND policy_profile_bytes=$3::bytea AND generation=$4::bigint
RETURNING pg_catalog.encode(operation_identity_bytes,'hex');
