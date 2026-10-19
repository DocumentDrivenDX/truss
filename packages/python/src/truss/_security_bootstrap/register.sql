-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Capacity is sourced from the protected original native profile, never $5.
-- Required order: schema-head SHARE, installation guard SHARE, claim table
-- capacity lock; fresh READ COMMITTED statement after acquisition. All profile
-- writes require guard UPDATE. Verify complete native profile/callable parity.
INSERT INTO truss.policy_publication_claim
 (operation_identity_bytes,installation_identity_bytes,policy_profile_bytes,generation)
SELECT $1::bytea,g.installation_identity_bytes,g.policy_profile_bytes,g.generation
FROM truss.policy_generation_guard g
JOIN truss.policy_publication_capacity c
 ON c.singleton OPERATOR(pg_catalog.=) g.singleton
 AND c.installation_identity_bytes OPERATOR(pg_catalog.=) g.installation_identity_bytes
 AND c.policy_profile_bytes OPERATOR(pg_catalog.=) g.policy_profile_bytes
WHERE g.singleton OPERATOR(pg_catalog.=) 1
 AND g.installation_identity_bytes OPERATOR(pg_catalog.=) $2::bytea
 AND g.policy_profile_bytes OPERATOR(pg_catalog.=) $3::bytea
 AND g.generation OPERATOR(pg_catalog.=) $4::bigint
 AND pg_catalog.octet_length($1::bytea) BETWEEN 1 AND 2048
 AND (SELECT pg_catalog.count(*) FROM
  (SELECT 1 FROM truss.policy_publication_claim LIMIT c.max_retained) retained)
  OPERATOR(pg_catalog.<) c.max_retained
RETURNING pg_catalog.encode(operation_identity_bytes,'hex');
-- Exactly one confirmed INSERT/commit before disclosure. Zero/malformed/unknown
-- refuses or retains original recovery custody. Never repair profile on admission.
