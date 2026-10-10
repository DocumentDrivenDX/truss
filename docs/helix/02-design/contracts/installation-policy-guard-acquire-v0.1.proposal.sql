-- Private candidate for compatible read/write or qualified coordinator scopes.
-- Not an ordinary read-only data-transaction query. Original admission/lock
-- order/actor/resource custody must precede dispatch.
SELECT g.singleton::pg_catalog.text AS singleton,
 pg_catalog.encode(g.installation_identity_bytes,'hex') AS installation_identity_bytes_hex,
 pg_catalog.encode(g.policy_profile_bytes,'hex') AS policy_profile_bytes_hex,
 g.generation::pg_catalog.text AS generation
FROM truss.policy_generation_guard AS g
WHERE g.singleton = 1
FOR SHARE OF g;
-- Preserve zero/extra/error/unknown observations as refusal/recovery; do not
-- repair the row or release authority from caller-supplied generation bytes.
