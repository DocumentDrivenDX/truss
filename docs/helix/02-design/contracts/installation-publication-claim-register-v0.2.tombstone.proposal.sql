-- Tombstone profile0.2 only; settled identities remain PK members.
-- Duplicate original bytes refuse23505; no upsert or replacement claim.
-- Original admitted operation token/identity/profile/generation, not caller proof.
-- Acquire original schema-head then guard SHARE first. Commit claim before any
-- protected disclosure, confirm original commit, retain unresolved custody on loss.
INSERT INTO truss.policy_publication_claim
 (operation_identity_bytes, installation_identity_bytes, policy_profile_bytes, generation)
SELECT $1::bytea, installation_identity_bytes, policy_profile_bytes, generation
FROM truss.policy_generation_guard
WHERE singleton=1 AND installation_identity_bytes=$2::bytea
 AND policy_profile_bytes=$3::bytea AND generation=$4::bigint
RETURNING pg_catalog.encode(operation_identity_bytes,'hex');
