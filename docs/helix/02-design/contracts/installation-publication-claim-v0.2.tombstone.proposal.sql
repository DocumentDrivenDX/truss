-- Private feasibility candidate; not an adopted layout or AuthorityLease issuer.
-- Retain settled original identities permanently for this installed profile.
-- No deletion, reset, token reuse, expiration or auto-repair. Not a migration.
CREATE TABLE truss.policy_publication_claim (
 operation_identity_bytes bytea PRIMARY KEY CHECK (octet_length(operation_identity_bytes) > 0),
 installation_identity_bytes bytea NOT NULL CHECK (octet_length(installation_identity_bytes) > 0),
 policy_profile_bytes bytea NOT NULL CHECK (octet_length(policy_profile_bytes) > 0),
 generation bigint NOT NULL CHECK (generation > 0),
 settled boolean NOT NULL DEFAULT false
);
REVOKE ALL ON truss.policy_publication_claim FROM PUBLIC;
