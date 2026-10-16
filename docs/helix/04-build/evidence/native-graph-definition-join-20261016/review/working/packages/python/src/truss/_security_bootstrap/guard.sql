-- CONTRACT-005 optional installation-wide current-authority guard.
-- Not adopted or included in layout 0.9. No automatic repair/initialization.
CREATE TABLE truss.policy_generation_guard (
 singleton smallint PRIMARY KEY CHECK (singleton = 1),
 installation_identity_bytes bytea NOT NULL CHECK (octet_length(installation_identity_bytes) > 0),
 policy_profile_bytes bytea NOT NULL CHECK (octet_length(policy_profile_bytes) > 0),
 generation bigint NOT NULL CHECK (generation > 0)
);
-- Protected bootstrap inserts (1, exact original installation/profile bytes, 1).
-- Ordinary roles receive no direct DML. Native lock/actor/snapshot/profile,
-- full effective authority/dependency and resource admission remain required.
