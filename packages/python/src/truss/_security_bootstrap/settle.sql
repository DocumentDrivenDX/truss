-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Tombstone profile0.2: retain original exact identity/profile/generation.
-- Repeated settlement returns zero; original uncertainty requires reconciliation.
-- Only original admitted recovery/publication owner after all protected release
-- has completed or was conclusively withheld. Never use timeout/probe as closure.
-- Acquire original schema-head then guard SHARE; confirm actual UPDATE 1/commit.
UPDATE truss.policy_publication_claim SET settled=true
WHERE NOT settled AND operation_identity_bytes=$1::bytea AND installation_identity_bytes=$2::bytea
 AND policy_profile_bytes=$3::bytea AND generation=$4::bigint
RETURNING pg_catalog.encode(operation_identity_bytes,'hex');
