-- Unexecuted PG17 sequence rights; unique original role/object oid[] pairs <=256.
-- Equal nonnull one-dimensional input arrays and exact class/kind admission required.
WITH pairs AS (
 SELECT f.role_oid,f.object_oid
 FROM ROWS FROM (pg_catalog.unnest($1::pg_catalog.oid[]),
                 pg_catalog.unnest($2::pg_catalog.oid[])) AS f(role_oid,object_oid)
)
SELECT r.oid::pg_catalog.text AS role_oid,
       o.oid::pg_catalog.text AS object_oid,
       pg_catalog.has_sequence_privilege(r.oid,o.oid,'USAGE') AS has_usage,
       pg_catalog.has_sequence_privilege(r.oid,o.oid,'USAGE WITH GRANT OPTION') AS can_grant_usage,
       pg_catalog.has_sequence_privilege(r.oid,o.oid,'SELECT') AS has_select,
       pg_catalog.has_sequence_privilege(r.oid,o.oid,'SELECT WITH GRANT OPTION') AS can_grant_select,
       pg_catalog.has_sequence_privilege(r.oid,o.oid,'UPDATE') AS has_update,
       pg_catalog.has_sequence_privilege(r.oid,o.oid,'UPDATE WITH GRANT OPTION') AS can_grant_update
FROM pairs AS f
JOIN pg_catalog.pg_roles AS r ON r.oid = f.role_oid
JOIN pg_catalog.pg_class AS o ON o.oid = f.object_oid
WHERE o.relkind = 'S'
ORDER BY r.oid,o.oid;
