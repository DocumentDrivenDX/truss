-- Private observation only. Drain original registration scopes with schema-head
-- SHARE then original guard UPDATE; use a fresh READ COMMITTED statement.
-- Expected original token/bytes/generation and producer/cut custody are separate.
SELECT pg_catalog.encode(operation_identity_bytes,'hex') AS operation_identity_bytes_hex,
 pg_catalog.encode(installation_identity_bytes,'hex') AS installation_identity_bytes_hex,
 pg_catalog.encode(policy_profile_bytes,'hex') AS policy_profile_bytes_hex,
 generation::pg_catalog.text AS generation,settled::pg_catalog.text AS settled
FROM truss.policy_publication_claim
WHERE operation_identity_bytes OPERATOR(pg_catalog.=) $1::bytea;
-- Zero rows mean not observed, never an authenticated noncommit/abort.
