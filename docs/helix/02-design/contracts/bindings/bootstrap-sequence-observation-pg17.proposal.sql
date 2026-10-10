-- Raw PG17 sequence configuration, not live counter/reset/commit evidence.
-- $1 exact admitted namespace; retain missing configuration through LEFT JOIN.
SELECT c.oid::text AS sequence_oid, n.nspname AS sequence_schema,
       c.relname AS sequence_name, c.relpersistence::text AS persistence,
       s.seqrelid::text AS configuration_oid,
       s.seqtypid::text AS type_oid,
       s.seqstart::text AS start_value, s.seqincrement::text AS increment,
       s.seqmin::text AS minimum, s.seqmax::text AS maximum,
       s.seqcache::text AS cache_size, s.seqcycle AS cycles,
       pg_catalog.to_jsonb(s)::pg_catalog.text AS original_configuration_row_json,
       pg_catalog.to_jsonb(c)::pg_catalog.text AS original_relation_row_json
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
LEFT JOIN pg_catalog.pg_sequence AS s ON s.seqrelid = c.oid
WHERE n.nspname = $1::pg_catalog.text AND c.relkind = 'S'
ORDER BY c.oid;
-- Independent raw relation enumeration retains every other/unknown relation kind.
-- Resolve type/owner/ACL/dependencies separately; never call nextval for collection.
