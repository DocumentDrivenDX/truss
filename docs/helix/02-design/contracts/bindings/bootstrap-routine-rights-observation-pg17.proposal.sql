-- Unexecuted PG17 routine rights; unique original role/object oid[] pairs <=256.
-- Equal nonnull one-dimensional input arrays and exact class/kind admission required.
WITH pairs AS (
 SELECT f.role_oid,f.object_oid
 FROM ROWS FROM (pg_catalog.unnest($1::pg_catalog.oid[]),
                 pg_catalog.unnest($2::pg_catalog.oid[])) AS f(role_oid,object_oid)
)
SELECT r.oid::pg_catalog.text AS role_oid,
       o.oid::pg_catalog.text AS object_oid,
       pg_catalog.has_function_privilege(r.oid,o.oid,'EXECUTE') AS has_execute,
       pg_catalog.has_function_privilege(r.oid,o.oid,'EXECUTE WITH GRANT OPTION') AS can_grant_execute
FROM pairs AS f
JOIN pg_catalog.pg_roles AS r ON r.oid = f.role_oid
JOIN pg_catalog.pg_proc AS o ON o.oid = f.object_oid
ORDER BY r.oid,o.oid;
