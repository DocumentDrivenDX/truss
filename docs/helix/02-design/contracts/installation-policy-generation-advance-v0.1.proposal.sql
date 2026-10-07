-- Private post-parity effect source. Parameters originate in the admitted
-- exclusive guard/installation/authority resolver, not public caller evidence.
UPDATE truss.policy_generation_guard
SET generation = generation + 1
WHERE singleton = 1
  AND installation_identity_bytes = $1::bytea
  AND policy_profile_bytes = $2::bytea
  AND generation = $3::bigint
  AND generation < 9223372036854775807
RETURNING singleton::pg_catalog.text AS singleton,
  pg_catalog.encode(installation_identity_bytes,'hex') AS installation_identity_bytes_hex,
  pg_catalog.encode(policy_profile_bytes,'hex') AS policy_profile_bytes_hex,
  generation::pg_catalog.text AS generation;
-- Require actual UPDATE 1 and exactly one complete returned row, generation
-- prior+1 and unchanged original identity/profile. Zero/extra/malformed output
-- refuses original containment; no upsert, reset or automatic retry.
-- This source supplies no lock, actor capture, fresh observation or grant proof.
