-- Fresh private candidate, not layout adoption or automatic initialization.
-- Verified bootstrap supplies original exact installation/profile and capacity.
-- Complete native parity must include this home and exclude uncontrolled writes.
CREATE TABLE truss.policy_publication_capacity (
 singleton smallint PRIMARY KEY CHECK(singleton=1),
 installation_identity_bytes bytea NOT NULL CHECK(octet_length(installation_identity_bytes)>0),
 policy_profile_bytes bytea NOT NULL CHECK(octet_length(policy_profile_bytes)>0),
 max_retained integer NOT NULL CHECK(max_retained BETWEEN 1 AND 1048576)
);
REVOKE ALL ON truss.policy_publication_capacity FROM PUBLIC;
-- Profile changes require original guard UPDATE and complete protected transition.
