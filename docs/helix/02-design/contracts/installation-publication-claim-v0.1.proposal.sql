-- Private feasibility candidate; not an adopted layout or AuthorityLease issuer.
-- A committed claim survives coordinator disconnect. No expiration/auto-repair.
CREATE TABLE truss.policy_publication_claim (
 operation_identity_bytes bytea PRIMARY KEY CHECK (octet_length(operation_identity_bytes) > 0),
 installation_identity_bytes bytea NOT NULL CHECK (octet_length(installation_identity_bytes) > 0),
 policy_profile_bytes bytea NOT NULL CHECK (octet_length(policy_profile_bytes) > 0),
 generation bigint NOT NULL CHECK (generation > 0)
);
REVOKE ALL ON truss.policy_publication_claim FROM PUBLIC;
